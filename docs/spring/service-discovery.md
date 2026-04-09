---
layout: default
title: Spring Cloud 服务注册与发现机制
---

# Spring Cloud 服务注册与发现机制

## 一、服务注册与发现的背景与架构

在传统的单体应用中，所有模块都在同一个进程内，通过直接方法调用进行通信。但随着业务规模增长，单体应用逐渐暴露出一系列问题：代码膨胀难以维护、单点故障影响全局、扩容不够灵活、技术栈更新困难。于是微服务架构应运而生——将大系统拆分为多个独立部署、独立运行的服务进程，每个服务专注于完成某一类业务能力。

然而，微服务拆分带来了一个新的核心问题：**服务之间如何相互发现和通信？** 在传统架构中，服务 A 调用服务 B，只需要知道 B 的 IP 地址和端口。但在微服务架构中，服务的实例数量是动态变化的——服务实例可能随时新增（水平扩容）、下线（缩容或故障）、或迁移（重新部署）。手动维护一份 IP 地址列表既不现实，也极易出错。

服务注册与发现（Service Discovery）机制正是为解决这一问题而设计。其核心思想是：**引入一个中心化的注册中心（Registry），所有服务实例在启动时主动向注册中心注册自己的地址信息（IP、端口、健康状态等），消费者通过注册中心获取目标服务的实例列表，再发起调用**。当服务实例发生变化时，注册中心主动通知订阅者，整个过程无需人工干预。

这套架构中包含三个关键角色：

- **服务注册者（Provider）**：服务实例向注册中心注册，提供自己的地址信息
- **服务发现者（Consumer）**：服务消费者从注册中心获取服务实例列表，并发起 RPC 调用
- **注册中心（Registry）**：维护服务实例列表，提供健康检查和故障检测，实时推送变更通知

从通信模式上看，服务发现分为**客户端发现**（如 Eureka、Ribbon）和**服务端发现**（如 Consul + Nginx / Kubernetes Service）两种。Spring Cloud 默认采用客户端发现模式，由服务消费者自行从注册中心获取实例列表并实现负载均衡。

## 二、Eureka 原理详解

Eureka 是 Netflix 开源的服务注册与发现组件，后被 Spring Cloud 整合为 Spring Cloud Netflix 模块，成为 Spring Cloud 微服务体系中最经典的服务发现方案。Eureka 采用 **AP 优先** 的设计理念，在可用性和一致性之间选择了可用性——即使注册中心部分节点宕机，只要还有节点存活，服务发现依然可用。

### 2.1 服务注册

当一个 Spring Boot 应用引入了 `spring-cloud-starter-netflix-eureka-client` 依赖并配置了相关参数后，应用在启动时会自动向 Eureka Server 发起注册请求，将自己的应用名称（spring.application.name）、IP、端口、健康检查地址等信息注册到 Eureka Server。

```yaml
# application.yml
spring:
  application:
    name: order-service  # 全局唯一的服务名称
eureka:
  instance:
    hostname: order-service.example.com
    port: 8080
    # 心跳间隔，默认30秒
    lease-renewal-interval-in-seconds: 30
    # 续约到期时间，默认90秒（3次心跳未响应则剔除）
    lease-expiration-duration-in-seconds: 90
    # 注册时使用IP地址而非主机名
    prefer-ip-address: true
  client:
    # 是否注册到Eureka Server
    register-with-eureka: true
    # 是否从Eureka Server获取注册表
    fetch-registry: true
    # Eureka Server地址（多个节点用逗号分隔）
    service-url:
      defaultZone: http://eureka-server-1:8761/eureka/,http://eureka-server-2:8761/eureka/
```

服务实例注册的 HTTP 请求地址为 `POST /eureka/apps/{appName}`，请求体中包含实例的详细信息。Eureka Server 收到注册请求后，会将其存储在内存注册表中，同时异步地将注册信息同步到其他对等节点（Peer Nodes）。

### 2.2 服务续约

服务实例注册成功后，并非永久有效。为了应对服务实例临时下线（重启、部署）而非真正永久下线的情况，Eureka 引入了**心跳续约（Renew）**机制。客户端每间隔 `lease-renewal-interval-in-seconds`（默认 30 秒）向 Eureka Server 发送一次心跳请求 `PUT /eureka/apps/{appName}/{instanceId}`，类似于在说"我还活着"。如果 Eureka Server 在 `lease-expiration-duration-in-seconds`（默认 90 秒）内没有收到某个实例的心跳，就认为该实例已下线，从注册表中将其剔除。

```java
// 心跳续约的核心逻辑（Eureka Client 内部实现）
@Scheduled(initialDelay = 30000, fixedDelay = 30000)
public void renew() {
    for (InstanceInfo instance : instanceRegistry.getApplications()) {
        try {
            // 发送心跳：PUT /eureka/apps/{appName}/{instanceId}
            EurekaHttpResponse<InstanceInfo> response = 
                discoveryClient.sendHeartBeat(instance.getAppName(), instance.getId(), null, "UP");
            if (response.getStatusCode() == 404) {
                // 404说明实例不在注册表中，需要重新注册
                register();
            }
        } catch (Exception e) {
            logger.error("心跳失败，将触发重新注册", e);
            register();
        }
    }
}
```

### 2.3 服务下线与剔除

**主动下线**：当服务实例正常关闭时（如接收到 SIGTERM 信号），Spring Cloud 的 `EurekaAutoServiceRegistration` 会自动向 Eureka Server 发送 DELETE 请求 `DELETE /eureka/apps/{appName}/{instanceId}`，通知注册中心该实例即将下线。注册中心收到下线请求后，会立即将该实例从注册表中移除，并同步通知所有订阅者。

**故障剔除**：如果服务实例因崩溃或网络故障而无法发送主动下线请求，Eureka Server 依赖后台的**自我保护模式**（Self-Preservation）和**定时扫描剔除**双重机制来处理这种情况。Server 每 60 秒扫描注册表，对超过阈值时间未续约的实例执行剔除。需要特别注意的是，当 Eureka Server 在 15 分钟内收到的续约次数低于期望阈值（85%）时，会进入自我保护模式——在此期间，Eureka Server **停止剔除任何**服务实例，即使实例心跳超时。

```yaml
eureka:
  server:
    # 是否启用自我保护机制（生产环境建议开启）
    enable-self-preservation: true
    # 续约百分比阈值，低于此值时触发自我保护
    renewal-percent-threshold: 0.85
    # 剔除间隔，默认60秒
    eviction-interval-timer-in-ms: 60000
    # 响应缓存更新间隔
    response-cache-update-interval-ms: 30000
```

## 三、Eureka 两级缓存机制

Eureka Server 的性能很大程度上取决于其注册表查询的响应速度。为了在高并发场景下减少内存注册表的访问压力，Eureka Server 实现了**两级缓存（ReadOnlyCacheMap + ReadWriteCacheMap）**来异步刷新注册表数据，这是理解 Eureka 高级特性的关键。

### 3.1 三层数据结构

Eureka Server 内部维护了三层数据结构：

- **Registry（实际注册表）**：内存中的 `ConcurrentHashMap<服务名, Map<实例ID, InstanceInfo>>`，所有服务注册、续约、下线操作都直接作用在这层。读写操作本身已经是无锁并发安全的。
- **ReadWriteCacheMap（二级缓存）**：Guava Cache，基于 `ConcurrentHashMap` 的包装，支持 TTL 过期（默认 180 秒）和容量限制。读写分离，当 Registry 变更时，会异步地写入 ReadWriteCacheMap。
- **ReadOnlyCacheMap（一级缓存）**：只读的内存缓存，默认每 30 秒从 ReadWriteCacheMap 同步一次最新数据。

### 3.2 三层之间的数据流动

```java
// 服务注册 → 写入Registry → 失效ReadWriteCacheMap → 异步刷新
public void register(InstanceInfo registrant, int leaseDuration, boolean isReplication) {
    // 1. 直接写入Registry（ConcurrentHashMap，无锁并发安全）
    Map<String, InstanceInfo> gMap = registry.get(registrant.getAppName());
    gMap.put(registrant.getId(), registrant);
    
    // 2. 失效ReadWriteCacheMap（只增加一个失效标记，不立即重建）
    invalidateState(registrant.getAppName());
    
    // 3. 立即同步到Peer节点（如果是主节点）
    if (!isReplication) {
        replicateToPeers(ActionType.ADD, registrant.getAppName(), registrant);
    }
}

// 服务查询 → 读取ReadOnlyCacheMap → 读不到则穿透到ReadWriteCacheMap
public Applications getApplicationsDerialized() {
    // 1. 先读一级缓存ReadOnlyCacheMap
    Applications apps = readOnlyCacheMap.get(key);
    if (apps != null) return apps; // 命中一级缓存，直接返回
    
    // 2. 一级缓存未命中，读取二级缓存ReadWriteCacheMap
    apps = readWriteCacheMap.get(key);
    if (apps != null) {
        readOnlyCacheMap.put(key, apps); // 写回一级缓存
        return apps;
    }
    
    // 3. 二级缓存也未命中，加锁查Registry并重建缓存
    synchronized (lock) {
        apps = readWriteCacheMap.get(key);
        if (apps == null) {
            apps = registry.getApplications();
            readWriteCacheMap.put(key, apps);
            readOnlyCacheMap.put(key, apps);
        }
    }
    return apps;
}
```

### 3.3 缓存机制的影响与调优

两级缓存带来的一个工程影响是：**客户端感知到服务变更存在最多 30 秒的延迟**。这是因为注册表的变更虽然会立即写入 Registry 并失效 ReadWriteCacheMap，但 ReadOnlyCacheMap 的刷新是定时任务驱动的，存在最长 30 秒的窗口期。

对于某些对注册表实时性要求极高的场景，可以通过调参来优化：设置 `response-cache-update-interval-ms=10000` 将一级缓存刷新间隔从 30 秒降低到 10 秒，但代价是 Eureka Server 本身会承受更高的 CPU 和 GC 压力。在实际生产环境中，通常建议保持默认配置，因为对于服务发现场景，30 秒的延迟是可以接受的，而 Eureka 的设计哲学本身就是 AP 而非 CP。

## 四、Consul 原理：Raft 协议与健康检查

HashiCorp Consul 是另一个功能强大的服务发现组件，与 Eureka 不同，Consul 默认采用 **CP 模式**（一致性优先），基于 Raft 共识算法保证数据一致性，同时支持更丰富的健康检查机制和 DNS/HTTP/GRPC 多种查询接口。

### 4.1 Raft 共识算法

Consul 集群中的所有节点分为 **Leader** 和 **Follower** 两种角色，数据写入遵循 Raft 协议的日志复制机制：

- **写请求**：客户端的写请求首先路由到 Leader，Leader 将请求作为日志条目写入本地日志，然后**并行**向所有 Follower 发送日志复制请求
- **提交条件**：只有当集群中**超过半数（≥N/2+1）**的节点（包括 Leader 自身）成功写入该日志条目后，Leader 才会将这条日志应用到状态机并返回成功给客户端
- **Leader 选举**：如果 Follower 在 election timeout（默认 150-300ms 随机值）内没有收到 Leader 的心跳，就会发起选举。获得超过半数投票的节点成为新的 Leader

```json
// Consul Server 端配置
{
  "server": true,
  "bootstrap_expect": 3,  // 期望3个Server节点，构建一个可用集群至少需要3个
  "data_dir": "/var/lib/consul",
  "ui_config": { "enabled": true },
  "addresses": { "http": "0.0.0.0" },
  "ports": {
    "dns": 8600,        // DNS端口
    "http": 8500,       // HTTP API端口
    "grpc": 8502        // gRPC端口
  },
  "raft_protocol": 3
}
```

Consul 的 Raft 协议确保了数据的一致性，但代价是 Leader 故障时需要重新选举，在选举期间（通常几百毫秒到几秒）集群无法处理写请求。如果 Consul 集群中的 Server 节点数为 3，最多允许 1 台宕机而不影响可用性；如果为 5，则最多允许 2 台宕机。

### 4.2 健康检查机制

Consul 支持多种健康检查方式，这是其相较于 Eureka 的显著优势：

```json
// 定义HTTP健康检查：每10秒检查一次 /health 端点
{
  "check": {
    "id": "order-service-health",
    "name": "Order Service Health",
    "http": "http://localhost:8080/actuator/health",
    "interval": "10s",
    "timeout": "5s",
    "deregister_critical_service_after": "30s"
  }
}
```

```yaml
# Spring Boot + Consul 健康检查配置
spring:
  cloud:
    consul:
      host: consul-server
      port: 8500
      discovery:
        service-name: ${spring.application.name}
        lease-renewal-interval: 10s
        lease-duration: 30s
        health-check-path: /actuator/health
        health-check-interval: 10s
```

Consul 支持的健康检查类型包括：

- **HTTP 检查**：定期发送 HTTP GET 请求，检查响应状态码（2xx 为健康）
- **TCP 检查**：定期尝试建立 TCP 连接，连接成功则健康
- **TTL 检查**：服务定期向 Consul 上报自己的健康状态，超过 TTL 未上报则标记为不健康
- **Script + Interval**：执行自定义脚本，根据返回码判断健康状态
- **Docker 检查**：通过 Docker API 检查容器健康状态
- **GRPC 检查**：检查 gRPC 服务的健康状态（支持 gRPC 标准的健康检查协议）

## 五、Nacos：CP/AP 双模式与实例类型

Nacos（Naming and Configuration Service）是阿里巴巴开源的更新一代服务注册与发现组件，目前已成为 Spring Cloud Alibaba 的核心组件。Nacos 最大的特点是**同时支持 CP 和 AP 两种模式**，并支持临时实例和持久实例两种注册方式，可以根据业务场景灵活选择。

### 5.1 CP 模式与 AP 模式

Nacos 的集群一致性基于 **Raft 协议**（CP）和 **Distro 协议**（AP）两种实现：

**CP 模式（一致性优先）**：基于 Raft 共识算法，适用于对数据一致性要求极高的场景，如配置管理、分布式锁、注册中心选主等。Leader 节点故障时会进行 Leader 选举，在选举期间（约几秒）服务注册和发现会有短暂不可用。

**AP 模式（可用性优先）**：基于 Distro 协议，每个节点都是对等的，服务注册时会先写入本地，然后异步同步到其他节点。适合服务发现场景，任何节点宕机都不影响集群的注册发现能力——即使网络分区，不同分区的节点依然可以各自注册自己的服务实例。

```yaml
# Nacos 服务端配置
nacos:
  core:
    protocol:
      mode: prefer_ap  # 默认AP模式，可切换为cp
  # Raft配置（CP模式生效）
  raft:
    apply-to: leader
    wait-for-leader: true
    wait-for-leader-timeout: 5000
    election-timeout: 5000
    snapshot-interval: 3600
```

### 5.2 临时实例与持久实例

Nacos 支持两种实例注册类型，这是其区别于其他注册中心的独特设计：

**临时实例（ephemeral=true）**：默认类型，服务实例通过心跳维持注册关系。如果心跳超时（默认 15 秒内未续约），Nacos 会主动将该实例从注册表中移除。临时实例不持久化到磁盘，Nacos 重启后数据丢失，适用于服务发现场景。

**持久实例（ephemeral=false）**：实例注册后永久存在于注册表中，不依赖心跳续约。持久实例宕机后不会被自动剔除（除非主动注销），Nacos 重启后依然可以从磁盘恢复数据。适用于需要保留服务元数据的场景，如基础服务（数据库、缓存）地址信息不希望因临时故障而被移除的情况。

```java
// Nacos实例注册：指定临时实例或持久实例
@Configuration
public class NacosInstanceConfig {

    @Bean
    public NacosDiscoveryProperties discoveryProperties() {
        NacosDiscoveryProperties props = new NacosDiscoveryProperties();
        // false = 持久实例，true = 临时实例（默认）
        props.setEphemeral(false); // 持久实例，不依赖心跳
        return props;
    }
}

// 通过API注册持久实例
// curl -X PUT 'http://nacos-server:8848/nacos/v1/ns/instance'
//   ?serviceName=order-service&ip=192.168.1.10&port=8080&ephemeral=false
```

### 5.3 Nacos 与 Spring Cloud 集成

```yaml
# application.yml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: nacos-server:8848
        namespace: prod
        group: DEFAULT_GROUP
        # 临时实例（默认true），CP模式需要设置为false
        ephemeral: false
      username: nacos
      password: nacos
```

Nacos 还支持命名空间（Namespace）和分组（Group）来实现服务隔离逻辑隔离，类似于 Eureka 的 Availability Zone 概念，但更加灵活。通过命名空间可以实现不同环境（dev/staging/prod）的服务隔离，通过分组可以实现业务线或团队的逻辑隔离。

## 六、Ribbon 客户端负载均衡

Spring Cloud Netflix 的 Ribbon 是客户端负载均衡（Client-Side Load Balancing）的实现。与服务端负载均衡（如 Nginx）不同，Ribbon 运行在服务消费者的进程内，在发起远程调用之前就已经从注册中心获取了服务实例列表，再根据负载均衡策略选择一个具体的实例发起请求。

### 6.1 Ribbon 的工作原理

Ribbon 与 Eureka 的集成流程如下：

1. Spring Cloud 自动配置 `DiscoveryEnableNIWSServerList` 和 `NIWSDiscoveryPing`，使 Ribbon 从 Eureka 获取服务实例列表
2. Ribbon 定期（默认每30秒）从 Eureka 拉取注册表缓存到本地
3. 当发起服务调用时，`ZoneAwareLoadBalancer` 根据负载均衡策略从候选实例中选择一个
4. 请求直接发送到选中的实例 IP:Port

```yaml
# Ribbon 配置
<clientName>:
  ribbon:
    # 服务列表获取策略
    NFLoadBalancerRuleClassName: com.netflix.loadbalancer.RandomRule
    # 服务列表刷新间隔
    ServerListRefreshInterval: 30000
    # 同区域优先策略
    EnableZoneAffinity: true
    # 最大重试次数
    MaxAutoRetries: 2
    # 同一实例最大重试次数
    MaxAutoRetriesNextServer: 1
    # 是否所有HTTP方法都启用重试
    OkToRetryOnAllOperations: false
```

Ribbon 内置了多种负载均衡策略：

| 策略类 | 策略名称 | 说明 |
|-------|---------|------|
| RoundRobinRule | 轮询策略 | 依次选择每个实例，默认策略 |
| RandomRule | 随机策略 | 随机选择一个实例 |
| WeightedResponseTimeRule | 加权响应时间策略 | 响应时间越短的实例被选中的概率越高 |
| BestAvailableRule | 最低并发策略 | 选择并发数最低的实例 |
| AvailabilityFilteringRule | 可用性过滤策略 | 过滤掉连接失败或熔断中的实例 |
| ZoneAvoidanceRule | 区域权衡策略 | 综合考虑区域和实例可用性（默认） |

### 6.2 自定义负载均衡策略

在 Spring Boot 3.x + Spring Cloud 2022.0 之后的版本中，Netflix Ribbon 已进入维护模式，Spring Cloud 推荐使用 **Spring Cloud LoadBalancer** 作为替代。但如果仍在使用 Ribbon，可以通过实现 `IRule` 接口来自定义负载均衡策略：

```java
// 自定义灰度发布负载均衡策略
public class GrayReleaseRule extends AbstractLoadBalancerRule {

    @Autowired
    private GrayReleaseService grayService;

    @Override
    public Server choose(Object key) {
        ILoadBalancer balancer = getLoadBalancer();
        List<Server> servers = balancer.getReachableServers();
        
        // 过滤掉不符合灰度规则的实例
        List<Server> eligibleServers = servers.stream()
            .filter(server -> grayService.isEligible(server.getHost(), key))
            .collect(Collectors.toList());
        
        if (eligibleServers.isEmpty()) {
            // 灰度实例不可用时，回退到全部可用实例
            return chooseRandomly(servers);
        }
        
        return chooseRandomly(eligibleServers);
    }
}
```

## 七、心跳机制与故障检测

无论选择哪种服务注册与发现框架，心跳机制和故障检测都是保证服务列表准确性的核心能力。

### 7.1 心跳机制的类型

**服务端主动探测（Pull 模式）**：注册中心定期向服务实例发送健康检查请求。Consul 默认采用此模式，通过定期 HTTP GET 请求来检测实例是否存活。优点是注册中心掌握实例的真实健康状态，缺点是当实例数量庞大时探测本身会成为负担。

**客户端主动上报（Push 模式）**：服务实例主动向注册中心发送心跳。Eureka 和 Nacos 默认采用此模式。优点是探测开销与实例数量解耦，缺点是如果客户端心跳机制出现问题（如线程池耗尽），注册中心无法及时感知。

```java
// 心跳超时与剔除的关系
// Eureka 心跳配置
eureka:
  instance:
    lease-renewal-interval-in-seconds: 10  # 每10秒发送心跳
    lease-expiration-duration-in-seconds: 30  # 30秒未收到心跳则剔除

// 故障检测时间线：
// T+0: 实例正常运行，每10秒发送心跳
// T+25: 实例崩溃，停止发送心跳
// T+30: Eureka Server 判定超时，剔除实例
// T+35: 消费者下次刷新缓存，感知到实例下线
// 总延迟：最多35秒（15秒扫描 + 最多20秒ReadOnlyCacheMap刷新）
```

### 7.2 故障检测的工程考量

在生产环境中，心跳间隔和超时时间的设置需要在**检测速度**和**网络抖动容忍度**之间做权衡：

- 心跳间隔过短（如 5 秒）：故障检测快，但网络稍有抖动就会误判，导致大量实例被误剔除
- 心跳间隔过长（如 60 秒）：对网络抖动容忍度高，但故障检测延迟大，影响故障快速响应

业界通常采用的配置是心跳间隔为超时时间的 1/3（如 10s/30s），这样在实例真正宕机后，最坏情况下需要 3 个心跳周期才能被剔除，同时容忍偶尔 1-2 次心跳丢失而不触发剔除。

此外，注册中心的**自我保护模式**（Eureka）或**最小健康实例比例**（Nacos）是防止雪崩效应的关键机制——当大量服务实例同时不续约时，注册中心应当识别这可能是网络分区而非真实故障，从而暂停剔除操作，避免健康实例被误杀。

## 八、四大注册中心对比

| 特性 | Eureka | Zookeeper | Consul | Nacos |
|------|--------|-----------|--------|-------|
| 设计原则 | AP | CP | CP | CP/AP 双模式 |
| 一致性协议 | 无（对等复制） | ZAB | Raft | Raft/Distro |
| 健康检查 | 客户端心跳 | KeepAlive/TCP | HTTP/TCP/TTL/GRPC | TCP/HTTP/MySQL/GRPC |
| 临时实例 | 支持 | 不支持 | 支持 | 支持 |
| 持久实例 | 不支持 | 支持（ZK 节点持久） | 不支持 | 支持 |
| Spring Cloud 集成 | 原生 | 需要额外适配 | 需要额外适配 | 原生（Spring Cloud Alibaba） |
| 多数据中心 | 支持 | 需额外配置 | 原生支持 | 支持 |
| 配置管理 | 不支持 | 支持（ZK 支持但不推荐） | 支持 | 原生支持 |
| 运维复杂度 | 低 | 中 | 中 | 中 |
| 活跃度 | 已被 Netflix 归档维护 | Apache 顶级项目 | HashiCorp 商业支持 | 阿里维护，活跃度高 |

对于大多数 Spring Cloud 微服务项目，**Nacos 是目前最推荐的选择**，因为它同时提供了服务注册发现和配置管理两大核心能力，减少了组件数量和学习成本，且对 AP/AP 双模式的支持使其能适应更广泛的业务场景。对于已经稳定运行 Eureka 的存量系统，可以继续维护 Eureka，同时逐步探索 Nacos 的平滑迁移方案。

## 九、面试题

### 面试题 1：Eureka 自我保护模式是什么？生产环境如何配置？

Eureka 自我保护模式是 Eureka Server 防止连锁故障的一种保护机制。当 Server 在 15 分钟内收到的续约次数低于期望阈值（`renewalPercentThreshold`，默认 0.85）时，说明有大量服务实例可能同时失联。Server 会假设这是网络分区（如整个机房断网），而非真实的故障，因此停止剔除任何服务实例。

生产环境建议保持默认开启（`enable-self-preservation=true`），同时配置合理的实例续约比例。如果服务实例波动频繁（如频繁发布），可以适当调低阈值或缩短剔除扫描间隔，但代价是故障实例被剔除的延迟增加。

### 面试题 2：Eureka 两级缓存的作用是什么？会带来什么问题？

Eureka Server 的两级缓存（ReadOnlyCacheMap + ReadWriteCacheMap）是为了在高并发查询注册表时减少对底层 ConcurrentHashMap 的锁竞争，提升查询性能。ReadWriteCacheMap 异步接收 Registry 的变更，ReadOnlyCacheMap 定期从 ReadWriteCacheMap 同步数据。

带来的问题是：**服务实例变更后，消费者感知到变更存在最多 30 秒的延迟**（ReadOnlyCacheMap 默认刷新间隔）。这个延迟在大多数场景下是可接受的，但如果对服务变更实时性有更高要求（如紧急下线故障实例），可以通过调小 `response-cache-update-interval-ms` 参数来缩短延迟，但会增大 Server 的 CPU 负载。

### 面试题 3：Nacos 的 CP 和 AP 模式有什么区别？如何在两者之间切换？

CP 模式基于 Raft 共识算法，保证数据强一致性，但 Leader 故障时需要重新选举，在选举期间（约几秒）服务注册会有短暂不可用。AP 模式基于 Distro 协议，每个节点独立处理请求，任何节点宕机都不影响其他节点的可用性。

切换方式：在 Nacos Server 配置文件中设置 `nacos.core.protocol.mode=prefer_ap` 或 `nacos.core.protocol.mode=cp`。客户端也可以通过 HTTP API 动态切换查询模式。生产环境中，服务发现场景建议使用 AP 模式，分布式锁、配置管理等强一致性场景建议切换到 CP 模式。

### 面试题 4：Ribbon 的负载均衡策略有哪些？如何自定义？

Ribbon 内置了轮询、随机、加权响应时间、最低并发、可用性过滤、区域权衡等六种策略。默认是 ZoneAvoidanceRule，综合考虑区域和可用性。

自定义负载均衡策略需要实现 `IRule` 接口。例如实现灰度发布策略：注入 `GrayReleaseService` 获取灰度规则（如请求头中的用户标签与实例标签匹配），从候选实例中过滤出符合条件的实例后，再按某种策略选择。如果过滤后为空，回退到原始策略。从 Spring Cloud 2022.0 起，Netflix Ribbon 已进入维护模式，推荐迁移到 Spring Cloud LoadBalancer。

### 面试题 5：Zookeeper 和 Eureka 在服务发现上的核心区别是什么？

核心区别在于**CAP 取舍**：Zookeeper 选择了 CP（一致性优先），Eureka 选择了 AP（可用性优先）。

Zookeeper 的 Leader 节点故障时，Follower 需要重新选举新 Leader，在选举期间（约几十秒）整个集群无法处理写请求，服务注册和发现都会有影响。但数据一致性有保障，读取到的永远是最新数据。

Eureka 的设计哲学是"宁可保留过期数据，也不停止服务"。即使部分节点宕机，剩余节点依然可以接收服务注册和查询，只要最终所有对等节点数据同步一致即可。这种 AP 的设计在大型分布式系统中更能保证服务调用的可用性，但对读取到的数据一致性要求更高的场景（如需要选主）则不适用 Zookeeper 以外的方式。
