---
layout: default
title: Spring Cloud 负载均衡详解：Ribbon 与 OpenFeign ⭐⭐⭐
---
# Spring Cloud 负载均衡详解：Ribbon 与 OpenFeign ⭐⭐⭐

## 面试题：什么是负载均衡？Spring Cloud 如何实现负载均衡？

### 核心回答

负载均衡是将请求分发到多个服务实例的技术，分为服务端负载均衡（Nginx、F5）和客户端负载均衡（Ribbon）。Spring Cloud 通过 Ribbon 实现客户端负载均衡，OpenFeign 在 Ribbon 基础上提供了声明式 HTTP 客户端，使得服务调用更加简洁。

## 一、负载均衡基础

### 1.1 负载均衡分类

```
┌─────────────────────────────────────────────────────────────┐
│                   负载均衡分类                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  服务端负载均衡：                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    负载均衡器                         │   │
│  │                 (Nginx/F5/HAProxy)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│              │              │              │                │
│              ▼              ▼              ▼                │
│         服务实例1       服务实例2       服务实例3            │
│                                                             │
│  特点：                                                     │
│  ├── 集中式，独立部署                                       │
│  ├── 请求先到负载均衡器，再分发                              │
│  └── 需要维护负载均衡器高可用                                │
│                                                             │
│  客户端负载均衡：                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     客户端                           │   │
│  │              (内置负载均衡逻辑)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│              │              │              │                │
│              ▼              ▼              ▼                │
│         服务实例1       服务实例2       服务实例3            │
│                                                             │
│  特点：                                                     │
│  ├── 分布式，每个客户端都有负载均衡能力                      │
│  ├── 客户端直接选择服务实例                                  │
│  └── 无需独立的负载均衡器                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 服务端 vs 客户端负载均衡

| 特性 | 服务端负载均衡 | 客户端负载均衡 |
|------|---------------|---------------|
| 部署位置 | 独立服务器 | 客户端内部 |
| 代表产品 | Nginx、F5、HAProxy | Ribbon、Spring Cloud LoadBalancer |
| 请求路径 | 客户端 → LB → 服务 | 客户端 → 服务 |
| 性能 | 多一跳，稍慢 | 直连，更快 |
| 高可用 | 需要保证 LB 高可用 | 无需额外保证 |
| 运维成本 | 较高 | 较低 |
| 适用场景 | 外部流量入口 | 内部服务调用 |

### 1.3 负载均衡算法

```
┌─────────────────────────────────────────────────────────────┐
│                   常见负载均衡算法                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 轮询（Round Robin）                                      │
│     ├── 按顺序依次分配请求                                   │
│     └── A → B → C → A → B → C                              │
│                                                             │
│  2. 随机（Random）                                          │
│     ├── 随机选择一个实例                                     │
│     └── 适合请求量大的场景                                   │
│                                                             │
│  3. 加权轮询（Weighted Round Robin）                        │
│     ├── 根据权重分配请求                                     │
│     └── 权重高的实例获得更多请求                             │
│                                                             │
│  4. 加权随机（Weighted Random）                             │
│     ├── 随机 + 权重                                         │
│     └── 概率与权重成正比                                     │
│                                                             │
│  5. 最少连接（Least Connections）                           │
│     ├── 选择当前连接数最少的实例                            │
│     └── 适合长连接场景                                       │
│                                                             │
│  6. 一致性哈希（Consistent Hash）                           │
│     ├── 根据请求特征（如 IP、用户 ID）计算哈希               │
│     └── 相同特征的请求总是路由到同一实例                     │
│                                                             │
│  7. 响应时间加权（Weighted Response Time）                  │
│     ├── 根据响应时间动态调整权重                            │
│     └── 响应快的实例获得更多请求                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 二、Ribbon 核心组件

### 2.1 Ribbon 简介

Ribbon 是 Netflix 开源的客户端负载均衡组件，主要功能：

- 服务发现：从注册中心获取服务实例列表
- 负载均衡：根据策略选择服务实例
- 故障处理：重试、超时处理

### 2.2 Ribbon 核心组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Ribbon 核心组件架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  ILoadBalancer                       │   │
│  │                  (负载均衡器)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│              │                              │               │
│              ▼                              ▼               │
│  ┌───────────────────┐          ┌───────────────────┐      │
│  │    ServerList     │          │      IRule        │      │
│  │   (服务列表)       │          │   (负载均衡策略)   │      │
│  └───────────────────┘          └───────────────────┘      │
│              │                              │               │
│              ▼                              ▼               │
│  ┌───────────────────┐          ┌───────────────────┐      │
│  │ ServerListFilter  │          │    IPing          │      │
│  │  (服务列表过滤)    │          │   (健康检查)       │      │
│  └───────────────────┘          └───────────────────┘      │
│                                                             │
│  组件说明：                                                  │
│  ├── ILoadBalancer：负载均衡器入口，协调各组件               │
│  ├── ServerList：获取服务实例列表                           │
│  ├── ServerListFilter：过滤服务实例                         │
│  ├── IRule：负载均衡策略，选择实例                          │
│  └── IPing：健康检查，剔除不可用实例                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 ILoadBalancer（负载均衡器）

```java
public interface ILoadBalancer {
    
    // 添加服务实例
    void addServers(List<Server> newServers);
    
    // 选择服务实例
    Server chooseServer(Object key);
    
    // 标记服务下线
    void markServerDown(Server server);
    
    // 获取可用的服务列表
    List<Server> getReachableServers();
    
    // 获取所有服务列表
    List<Server> getAllServers();
}
```

```java
// BaseLoadBalancer 实现
public class BaseLoadBalancer extends AbstractLoadBalancer {
    
    // 所有服务实例
    protected volatile List<Server> allServerList;
    
    // 可用服务实例
    protected volatile List<Server> upServerList;
    
    // 负载均衡策略
    protected IRule rule;
    
    // 健康检查
    protected IPing ping;
    
    @Override
    public Server chooseServer(Object key) {
        if (rule == null) {
            return null;
        }
        return rule.choose(key);
    }
}
```

### 2.4 ServerList（服务列表）

```java
public interface ServerList<T extends Server> {
    
    // 获取初始服务列表
    public List<T> getInitialListOfServers();
    
    // 获取更新的服务列表
    public List<T> getUpdatedListOfServers();
}
```

```java
// 基于 Eureka 的实现
public class DiscoveryEnabledNIWSServerList extends AbstractServerList<DiscoveryEnabledServer> {
    
    @Override
    public List<DiscoveryEnabledServer> getInitialListOfServers() {
        return fetchServersBasedOnConfiguration();
    }
    
    @Override
    public List<DiscoveryEnabledServer> getUpdatedListOfServers() {
        return fetchServersBasedOnConfiguration();
    }
    
    private List<DiscoveryEnabledServer> fetchServersBasedOnConfiguration() {
        // 从 Eureka 获取服务实例列表
        List<DiscoveryEnabledServer> result = new ArrayList<>();
        List<ServiceInstance> instances = discoveryClient.getInstances(serviceId);
        for (ServiceInstance instance : instances) {
            result.add(new DiscoveryEnabledServer(instance, false));
        }
        return result;
    }
}
```

### 2.5 ServerListFilter（服务列表过滤）

```java
public interface ServerListFilter<T extends Server> {
    
    // 过滤服务列表
    public List<T> getFilteredListOfServers(List<T> servers);
}
```

```java
// ZoneAffinityServerListFilter：同区域优先
public class ZoneAffinityServerListFilter<T extends Server> extends AbstractServerListFilter<T> {
    
    @Override
    public List<T> getFilteredListOfServers(List<T> servers) {
        // 获取当前实例所在区域
        String currentZone = zone;
        
        // 过滤同区域的实例
        List<T> filtered = servers.stream()
            .filter(server -> currentZone.equals(server.getZone()))
            .collect(Collectors.toList());
        
        // 如果同区域实例数量过少，返回全部实例
        if (filtered.size() < threshold) {
            return servers;
        }
        
        return filtered;
    }
}
```

### 2.6 IRule（负载均衡策略）

```java
public interface IRule {
    
    // 选择服务实例
    public Server choose(Object key);
    
    // 设置负载均衡器
    public void setLoadBalancer(ILoadBalancer lb);
    
    // 获取负载均衡器
    public ILoadBalancer getLoadBalancer();
}
```

### 2.7 七种负载均衡策略详解

#### 2.7.1 RoundRobinRule（轮询）

```java
public class RoundRobinRule extends AbstractLoadBalancerRule {
    
    private AtomicInteger nextServerCyclicCounter;
    
    @Override
    public Server choose(Object key) {
        ILoadBalancer lb = getLoadBalancer();
        if (lb == null) {
            return null;
        }
        
        Server server = null;
        int count = 0;
        while (server == null && count++ < 10) {
            List<Server> reachableServers = lb.getReachableServers();
            List<Server> allServers = lb.getAllServers();
            
            int upCount = reachableServers.size();
            int serverCount = allServers.size();
            
            if (upCount == 0 || serverCount == 0) {
                return null;
            }
            
            // 计算下一个索引
            int nextServerIndex = incrementAndGetModulo(serverCount);
            server = allServers.get(nextServerIndex);
        }
        
        return server;
    }
    
    private int incrementAndGetModulo(int modulo) {
        for (;;) {
            int current = nextServerCyclicCounter.get();
            int next = (current + 1) % modulo;
            if (nextServerCyclicCounter.compareAndSet(current, next)) {
                return next;
            }
        }
    }
}
```

**特点**：
- 按顺序依次选择实例
- 使用 CAS 保证线程安全
- 默认策略

#### 2.7.2 RandomRule（随机）

```java
public class RandomRule extends AbstractLoadBalancerRule {
    
    private Random random;
    
    @Override
    public Server choose(Object key) {
        ILoadBalancer lb = getLoadBalancer();
        if (lb == null) {
            return null;
        }
        
        Server server = null;
        while (server == null) {
            List<Server> upList = lb.getReachableServers();
            List<Server> allList = lb.getAllServers();
            
            int serverCount = allList.size();
            int upCount = upList.size();
            
            if (upCount == 0) {
                return null;
            }
            
            // 随机选择一个实例
            int index = random.nextInt(serverCount);
            server = upList.get(index);
        }
        
        return server;
    }
}
```

**特点**：
- 随机选择实例
- 适合请求量大的场景
- 实现简单

#### 2.7.3 WeightedResponseTimeRule（响应时间加权）

```java
public class WeightedResponseTimeRule extends RoundRobinRule {
    
    private DynamicServerWeightLoadBalancer weightCalculator;
    
    @Override
    public Server choose(Object key) {
        // 获取权重列表
        List<Double> weights = weightCalculator.getWeights();
        List<Server> servers = getLoadBalancer().getAllServers();
        
        // 根据权重选择实例
        // 响应时间越短，权重越高
        double totalWeight = weights.stream().mapToDouble(Double::doubleValue).sum();
        double randomWeight = Math.random() * totalWeight;
        
        double currentWeight = 0;
        for (int i = 0; i < servers.size(); i++) {
            currentWeight += weights.get(i);
            if (randomWeight <= currentWeight) {
                return servers.get(i);
            }
        }
        
        return super.choose(key);
    }
    
    // 定时任务：计算权重
    class DynamicServerWeightLoadBalancer {
        void maintainWeights() {
            // 根据平均响应时间计算权重
            // 权重 = 总响应时间 - 当前实例响应时间
            // 响应时间越短，权重越高
        }
    }
}
```

**特点**：
- 根据响应时间动态调整权重
- 响应快的实例获得更多请求
- 自适应负载均衡

#### 2.7.4 BestAvailableRule（最低并发）

```java
public class BestAvailableRule extends ClientConfigEnabledRoundRobinRule {
    
    @Override
    public Server choose(Object key) {
        ILoadBalancer lb = getLoadBalancer();
        if (lb == null) {
            return null;
        }
        
        Server server = null;
        int minConcurrentConnections = Integer.MAX_VALUE;
        
        // 遍历所有实例，选择并发连接数最少的
        for (Server s : lb.getAllServers()) {
            ServerStats stats = loadBalancerStats.getSingleServerStat(s);
            int concurrentConnections = stats.getActiveRequestsCount();
            
            if (concurrentConnections < minConcurrentConnections) {
                minConcurrentConnections = concurrentConnections;
                server = s;
            }
        }
        
        return server;
    }
}
```

**特点**：
- 选择当前并发连接数最少的实例
- 适合长连接场景
- 避免某些实例过载

#### 2.7.5 AvailabilityFilteringRule（可用性过滤）

```java
public class AvailabilityFilteringRule extends PredicateBasedRule {
    
    @Override
    public AbstractServerPredicate getPredicate() {
        // 过滤条件：
        // 1. 实例是可用的
        // 2. 并发连接数不超过阈值
        return compositePredicate;
    }
    
    @Override
    public Server choose(Object key) {
        int count = 0;
        Server server = null;
        
        // 使用轮询，但只从可用实例中选择
        while (count++ < 10) {
            List<Server> servers = getPredicate().getEligibleServers(
                getLoadBalancer().getAllServers(), key);
            
            if (servers.isEmpty()) {
                break;
            }
            
            int index = (int) (count % servers.size());
            server = servers.get(index);
            
            if (server != null && server.isAlive()) {
                return server;
            }
        }
        
        return null;
    }
}
```

**特点**：
- 过滤掉不可用的实例
- 过滤掉并发连接数超限的实例
- 提高请求成功率

#### 2.7.6 ZoneAvoidanceRule（区域感知）

```java
public class ZoneAvoidanceRule extends PredicateBasedRule {
    
    @Override
    public AbstractServerPredicate getPredicate() {
        // 组合判断：
        // 1. 区域可用性
        // 2. 实例可用性
        return compositePredicate;
    }
    
    @Override
    public Server choose(Object key) {
        // 1. 计算各区域的可用性分数
        // 2. 选择最优区域
        // 3. 在最优区域内轮询选择实例
        return getPredicate().chooseRoundRobinAfterFiltering(
            getLoadBalancer().getAllServers(), key);
    }
}
```

**特点**：
- 优先选择同区域实例
- 考虑区域整体可用性
- 避免跨区域调用延迟

#### 2.7.7 RetryRule（重试）

```java
public class RetryRule extends AbstractLoadBalancerRule {
    
    private IRule subRule;
    private long maxRetryMillis;
    
    @Override
    public Server choose(Object key) {
        long startTime = System.currentTimeMillis();
        Server server = null;
        
        while (server == null && 
               (System.currentTimeMillis() - startTime) < maxRetryMillis) {
            
            // 使用子策略选择实例
            server = subRule.choose(key);
            
            if (server == null) {
                try {
                    Thread.sleep(100);  // 短暂等待后重试
                } catch (InterruptedException e) {
                    break;
                }
            }
        }
        
        return server;
    }
}
```

**特点**：
- 在指定时间内重试
- 可以包装其他策略
- 提高选择成功率

### 2.8 IPing（健康检查）

```java
public interface IPing {
    
    // 检查实例是否存活
    public boolean isAlive(Server server);
}
```

```java
// DummyPing：不检查，默认存活
public class DummyPing implements IPing {
    @Override
    public boolean isAlive(Server server) {
        return true;
    }
}

// PingUrl：HTTP 检查
public class PingUrl implements IPing {
    
    private String expectedContent;
    
    @Override
    public boolean isAlive(Server server) {
        String url = "http://" + server.getHostPort() + "/";
        
        try {
            HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(3000);
            
            int code = conn.getResponseCode();
            if (code == 200) {
                return true;
            }
        } catch (Exception e) {
            return false;
        }
        
        return false;
    }
}
```

### 2.9 Ribbon 配置

```yaml
# application.yml
user-service:
  ribbon:
    # 负载均衡策略
    NFLoadBalancerRuleClassName: com.netflix.loadbalancer.RandomRule
    
    # 服务列表刷新间隔
    ServerListRefreshInterval: 30000
    
    # 连接超时
    ConnectTimeout: 3000
    
    # 读取超时
    ReadTimeout: 5000
    
    # 最大重试次数
    MaxAutoRetries: 1
    
    # 切换实例重试次数
    MaxAutoRetriesNextServer: 1
    
    # 是否对所有操作重试
    OkToRetryOnAllOperations: false
```

```java
// Java 配置
@Configuration
public class RibbonConfig {
    
    @Bean
    public IRule ribbonRule() {
        // 随机策略
        return new RandomRule();
    }
    
    @Bean
    public IPing ribbonPing() {
        // URL 检查
        return new PingUrl();
    }
}
```

## 三、Ribbon 执行流程

### 3.1 完整执行流程图

```
┌────────────────────────────────────────────────────────────────────┐
│                    Ribbon 执行流程图                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  HTTP Request                                                      │
│  GET http://user-service/api/user/1                               │
│      ↓                                                             │
│  LoadBalancerInterceptor                                           │
│  ├── 拦截 RestTemplate 请求                                        │
│  └── 提取服务名：user-service                                      │
│      ↓                                                             │
│  RibbonLoadBalancerClient                                          │
│  ├── 获取 ILoadBalancer                                           │
│  │   └── SpringClientFactory.getInstance(serviceId)               │
│  ├── 执行 choose() 选择实例                                        │
│  │   └── IRule.choose(key)                                        │
│      ↓                                                             │
│  【选择实例详细流程】                                                │
│                                                                    │
│  1. ServerList.getUpdatedListOfServers()                           │
│     └── 从注册中心获取服务实例列表                                  │
│        [Instance1, Instance2, Instance3]                           │
│      ↓                                                             │
│  2. ServerListFilter.getFilteredListOfServers()                    │
│     └── 过滤服务实例                                               │
│        [Instance1, Instance2]                                      │
│      ↓                                                             │
│  3. IPing.isAlive()                                                │
│     └── 健康检查                                                   │
│        [Instance1(✓), Instance2(✓)]                                │
│      ↓                                                             │
│  4. IRule.choose()                                                 │
│     └── 根据策略选择实例                                           │
│        → Instance1                                                 │
│      ↓                                                             │
│  【返回选择结果】                                                    │
│                                                                    │
│  RibbonLoadBalancerClient                                          │
│  ├── 构建实际 URL                                                  │
│  │   http://user-service/api/user/1                               │
│  │   → http://192.168.1.1:8080/api/user/1                         │
│  └── 发送请求                                                      │
│      ↓                                                             │
│  HTTP Response                                                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 源码分析

#### LoadBalancerInterceptor

```java
public class LoadBalancerInterceptor implements ClientHttpRequestInterceptor {
    
    private LoadBalancerClient loadBalancer;
    
    @Override
    public ClientHttpResponse intercept(HttpRequest request, 
                                        byte[] body, 
                                        ClientHttpRequestExecution execution) throws IOException {
        
        URI originalUri = request.getURI();
        String serviceName = originalUri.getHost();
        
        // 负载均衡选择实例并执行请求
        return loadBalancer.execute(serviceName, 
            new LoadBalancerRequest<ClientHttpResponse>() {
                @Override
                public ClientHttpResponse apply(ServiceInstance instance) throws Exception {
                    // 构建实际 URL
                    URI uri = loadBalancer.reconstructURI(instance, originalUri);
                    HttpRequest newRequest = new HttpRequestAdapter(request, uri);
                    return execution.execute(newRequest, body);
                }
            });
    }
}
```

#### RibbonLoadBalancerClient

```java
public class RibbonLoadBalancerClient implements LoadBalancerClient {
    
    @Override
    public <T> T execute(String serviceId, LoadBalancerRequest<T> request) throws IOException {
        // 获取负载均衡器
        ILoadBalancer loadBalancer = getLoadBalancer(serviceId);
        
        // 选择服务实例
        Server server = getServer(loadBalancer);
        if (server == null) {
            throw new IllegalStateException("No instances available for " + serviceId);
        }
        
        // 包装为 RibbonServer
        RibbonServer ribbonServer = new RibbonServer(serviceId, server);
        
        // 执行请求
        return execute(serviceId, ribbonServer, request);
    }
    
    protected Server getServer(ILoadBalancer loadBalancer) {
        if (loadBalancer == null) {
            return null;
        }
        // 调用负载均衡策略选择实例
        return loadBalancer.chooseServer("default");
    }
}
```

### 3.3 @LoadBalanced 注解原理

```java
@Target({ ElementType.FIELD, ElementType.PARAMETER, ElementType.METHOD })
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@Qualifier
public @interface LoadBalanced {
}
```

```java
// LoadBalancerAutoConfiguration
@Configuration
@ConditionalOnClass(RestTemplate.class)
@ConditionalOnBean(LoadBalancerClient.class)
@EnableConfigurationProperties(LoadBalancerProperties.class)
public class LoadBalancerAutoConfiguration {
    
    @LoadBalanced
    @Autowired(required = false)
    private List<RestTemplate> restTemplates = Collections.emptyList();
    
    @Bean
    public LoadBalancerInterceptor loadBalancerInterceptor(
            LoadBalancerClient loadBalancerClient,
            LoadBalancerProperties properties) {
        return new LoadBalancerInterceptor(loadBalancerClient, properties);
    }
    
    @Bean
    public RestTemplateCustomizer restTemplateCustomizer(
            final LoadBalancerInterceptor loadBalancerInterceptor) {
        return restTemplate -> {
            // 为所有 @LoadBalanced 标注的 RestTemplate 添加拦截器
            List<ClientHttpRequestInterceptor> list = new ArrayList<>(
                restTemplate.getInterceptors());
            list.add(loadBalancerInterceptor);
            restTemplate.setInterceptors(list);
        };
    }
}
```

## 四、OpenFeign 详解

### 4.1 OpenFeign 简介

OpenFeign 是一个声明式 HTTP 客户端，通过注解定义 HTTP 请求，简化了服务调用代码。

**特点**：
- 声明式调用：使用注解定义接口
- 整合 Ribbon：自动负载均衡
- 整合 Sentinel：熔断降级
- 支持 Spring MVC 注解

### 4.2 OpenFeign 使用

```xml
<!-- 依赖 -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

```java
// 启动类
@SpringBootApplication
@EnableFeignClients
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

```java
// Feign 客户端定义
@FeignClient(name = "user-service", path = "/api/user")
public interface UserClient {
    
    @GetMapping("/{id}")
    Result<User> getUser(@PathVariable("id") Long id);
    
    @GetMapping
    Result<List<User>> listUsers(@RequestParam("page") Integer page,
                                 @RequestParam("size") Integer size);
    
    @PostMapping
    Result<User> createUser(@RequestBody UserDTO userDTO);
    
    @PutMapping("/{id}")
    Result<User> updateUser(@PathVariable("id") Long id, 
                           @RequestBody UserDTO userDTO);
    
    @DeleteMapping("/{id}")
    Result<Void> deleteUser(@PathVariable("id") Long id);
}
```

```java
// 使用 Feign 客户端
@Service
public class OrderService {
    
    @Autowired
    private UserClient userClient;
    
    public Order createOrder(Long userId, OrderDTO orderDTO) {
        // 调用用户服务
        Result<User> userResult = userClient.getUser(userId);
        if (!userResult.isSuccess()) {
            throw new RuntimeException("用户不存在");
        }
        
        User user = userResult.getData();
        
        // 创建订单...
        Order order = new Order();
        order.setUserId(user.getId());
        order.setUserName(user.getName());
        
        return orderRepository.save(order);
    }
}
```

### 4.3 Feign 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                   Feign 核心组件                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Feign.Builder                                              │
│  ├── 构建 Feign 客户端                                      │
│  └── 配置各个组件                                           │
│                                                             │
│  Contract                                                   │
│  ├── 解析接口注解                                           │
│  └── SpringMvcContract：支持 Spring MVC 注解               │
│                                                             │
│  Encoder                                                    │
│  ├── 编码请求体                                             │
│  └── SpringEncoder：支持 JSON 序列化                        │
│                                                             │
│  Decoder                                                    │
│  ├── 解码响应体                                             │
│  └── SpringDecoder：支持 JSON 反序列化                      │
│                                                             │
│  Client                                                     │
│  ├── 执行 HTTP 请求                                         │
│  ├── Default：HttpURLConnection                             │
│  └── LoadBalancerFeignClient：集成 Ribbon                   │
│                                                             │
│  RequestInterceptor                                         │
│  ├── 请求拦截器                                             │
│  └── 添加统一 Header、认证信息                              │
│                                                             │
│  Logger                                                     │
│  ├── 日志记录                                               │
│  └── Slf4jLogger                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Feign 执行流程

```
┌────────────────────────────────────────────────────────────────────┐
│                    Feign 执行流程图                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  userClient.getUser(1L)                                            │
│      ↓                                                             │
│  ReflectiveFeign.FeignInvocationHandler.invoke()                   │
│  ├── JDK 动态代理                                                  │
│  └── 拦截方法调用                                                  │
│      ↓                                                             │
│  SynchronousMethodHandler.invoke()                                 │
│  ├── 构建 RequestTemplate                                          │
│  │   ├── 解析 @GetMapping                                         │
│  │   ├── 解析 @PathVariable                                       │
│  │   └── 构建请求 URL 和参数                                      │
│      ↓                                                             │
│  RequestInterceptor.apply()                                        │
│  ├── 添加请求头                                                    │
│  ├── 添加认证信息                                                  │
│  └── 修改请求参数                                                  │
│      ↓                                                             │
│  Encoder.encode()                                                  │
│  └── 序列化请求体（POST/PUT）                                      │
│      ↓                                                             │
│  LoadBalancerFeignClient.execute()                                 │
│  ├── 解析服务名                                                    │
│  ├── Ribbon 选择实例                                               │
│  └── 发送 HTTP 请求                                                │
│      ↓                                                             │
│  HTTP 响应                                                         │
│      ↓                                                             │
│  Decoder.decode()                                                  │
│  └── 反序列化响应体                                                │
│      ↓                                                             │
│  返回结果 Result<User>                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.5 Feign 配置

```yaml
# application.yml
feign:
  client:
    config:
      default:
        # 连接超时
        connectTimeout: 5000
        # 读取超时
        readTimeout: 5000
        # 日志级别
        loggerLevel: FULL
      
      user-service:
        connectTimeout: 3000
        readTimeout: 10000
  
  # GZIP 压缩
  compression:
    request:
      enabled: true
      mime-types: application/json
      min-request-size: 2048
    response:
      enabled: true
  
  # Sentinel 集成
  sentinel:
    enabled: true
  
  # HTTP 客户端
  httpclient:
    enabled: true
    max-connections: 200
    max-connections-per-route: 50
```

### 4.6 Feign 日志配置

```java
@Configuration
public class FeignConfig {
    
    @Bean
    public Logger.Level feignLoggerLevel() {
        // 日志级别
        // NONE：无日志
        // BASIC：请求方法、URL、响应状态码、执行时间
        // HEADERS：BASIC + 请求/响应头
        // FULL：HEADERS + 请求/响应体
        return Logger.Level.FULL;
    }
}
```

```yaml
# 为特定 Feign 客户端配置日志级别
logging:
  level:
    com.example.client.UserClient: DEBUG
```

### 4.7 Feign 请求拦截器

```java
@Configuration
public class FeignConfig {
    
    @Bean
    public RequestInterceptor authInterceptor() {
        return template -> {
            // 从当前上下文获取 Token
            String token = SecurityContextHolder.getContext()
                .getAuthentication()
                .getCredentials()
                .toString();
            
            // 添加认证头
            template.header("Authorization", "Bearer " + token);
        };
    }
    
    @Bean
    public RequestInterceptor traceInterceptor() {
        return template -> {
            // 添加链路追踪 ID
            String traceId = MDC.get("traceId");
            if (StringUtils.hasText(traceId)) {
                template.header("X-Trace-Id", traceId);
            }
        };
    }
}
```

### 4.8 Feign 降级配置

```java
@FeignClient(name = "user-service", 
             fallback = UserClientFallback.class)
public interface UserClient {
    
    @GetMapping("/{id}")
    Result<User> getUser(@PathVariable("id") Long id);
}

@Component
public class UserClientFallback implements UserClient {
    
    @Override
    public Result<User> getUser(Long id) {
        return Result.error("用户服务不可用");
    }
}
```

```java
// 使用 FallbackFactory 获取异常信息
@FeignClient(name = "user-service", 
             fallbackFactory = UserClientFallbackFactory.class)
public interface UserClient {
    
    @GetMapping("/{id}")
    Result<User> getUser(@PathVariable("id") Long id);
}

@Component
public class UserClientFallbackFactory implements FallbackFactory<UserClient> {
    
    @Override
    public UserClient create(Throwable cause) {
        return new UserClient() {
            @Override
            public Result<User> getUser(Long id) {
                log.error("调用用户服务失败", cause);
                
                if (cause instanceof FeignException.NotFound) {
                    return Result.error("用户不存在");
                }
                if (cause instanceof FeignException.ServiceUnavailable) {
                    return Result.error("用户服务不可用");
                }
                
                return Result.error("用户服务调用失败: " + cause.getMessage());
            }
        };
    }
}
```

### 4.9 Feign 性能优化

#### 4.9.1 使用连接池

```xml
<!-- 替换默认的 HttpURLConnection -->
<dependency>
    <groupId>io.github.openfeign</groupId>
    <artifactId>feign-httpclient</artifactId>
</dependency>
```

```yaml
feign:
  httpclient:
    enabled: true
    max-connections: 200          # 最大连接数
    max-connections-per-route: 50 # 每个路由的最大连接数
    connection-timeout: 5000      # 连接超时
    connection-timer-repeat: 3000 # 连接定时器重复间隔
```

#### 4.9.2 GZIP 压缩

```yaml
feign:
  compression:
    request:
      enabled: true
      mime-types: application/json,application/xml
      min-request-size: 2048      # 最小压缩大小
    response:
      enabled: true
```

#### 4.9.3 超时配置

```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 5000      # 连接超时 5s
        readTimeout: 10000        # 读取超时 10s
```

### 4.10 自定义 Feign 配置

```java
@FeignClient(name = "user-service", 
             configuration = UserFeignConfig.class,
             fallbackFactory = UserClientFallbackFactory.class)
public interface UserClient {
    // ...
}

public class UserFeignConfig {
    
    @Bean
    public Encoder encoder() {
        return new SpringEncoder(new SpringEncoderDelegate(messageConverters));
    }
    
    @Bean
    public Decoder decoder() {
        return new SpringDecoder(messageConverters);
    }
    
    @Bean
    public Contract contract() {
        return new SpringMvcContract();
    }
    
    @Bean
    public Logger.Level loggerLevel() {
        return Logger.Level.FULL;
    }
    
    @Bean
    public RequestInterceptor authInterceptor() {
        return template -> {
            // 自定义拦截逻辑
        };
    }
}
```

## 五、Spring Cloud LoadBalancer（Ribbon 替代方案）

### 5.1 背景

Ribbon 已进入维护模式，Spring Cloud 提供了新的负载均衡组件：Spring Cloud LoadBalancer。

### 5.2 添加依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-loadbalancer</artifactId>
</dependency>
```

### 5.3 配置负载均衡策略

```java
@Configuration
public class LoadBalancerConfig {
    
    @Bean
    public ReactorServiceInstanceLoadBalancer randomLoadBalancer(
            Environment environment, 
            LoadBalancerClientFactory factory) {
        String serviceId = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
        return new RandomLoadBalancer(
            factory.getLazyProvider(serviceId, ServiceInstanceListSupplier.class), 
            serviceId);
    }
}
```

```java
// 自定义负载均衡策略
public class CustomLoadBalancer implements ReactorServiceInstanceLoadBalancer {
    
    private final ServiceInstanceListSupplier serviceInstanceListSupplier;
    
    public CustomLoadBalancer(ServiceInstanceListSupplier supplier) {
        this.serviceInstanceListSupplier = supplier;
    }
    
    @Override
    public Mono<Response<ServiceInstance>> choose(Request request) {
        return serviceInstanceListSupplier.get()
            .next()
            .map(instances -> {
                // 自定义选择逻辑
                ServiceInstance instance = selectInstance(instances);
                return new DefaultResponse(instance);
            });
    }
    
    private ServiceInstance selectInstance(List<ServiceInstance> instances) {
        // 自定义算法
        // 如：加权、一致性哈希等
        return instances.get(0);
    }
}
```

## 📖 高频面试题

### Q1: Ribbon 的七种负载均衡策略分别适用于什么场景？

**答：**

| 策略 | 适用场景 |
|------|---------|
| RoundRobinRule | 服务器性能相近，请求均匀分布 |
| RandomRule | 请求量大时，随机分布足够均匀 |
| WeightedResponseTime | 服务器性能差异大，响应时间差距明显 |
| BestAvailableRule | 需要避免单实例过载 |
| AvailabilityFilteringRule | 需要剔除故障实例 |
| ZoneAvoidanceRule | 多区域部署，优先同区域调用 |
| RetryRule | 需要在选择失败时重试 |

### Q2: @LoadBalanced 注解的作用是什么？

**答：**

#### 1. 作用
- 标记 RestTemplate 使用负载均衡
- 为 RestTemplate 添加 LoadBalancerInterceptor

#### 2. 原理
```java
// 通过 @Qualifier 注解，收集所有 @LoadBalanced 标注的 RestTemplate
@LoadBalanced
@Autowired(required = false)
private List<RestTemplate> restTemplates = Collections.emptyList();

// 为每个 RestTemplate 添加拦截器
restTemplate.setInterceptors(Arrays.asList(loadBalancerInterceptor));
```

#### 3. 使用
```java
@Configuration
public class RestTemplateConfig {
    
    @Bean
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class UserService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    public User getUser(Long id) {
        // 使用服务名替代具体地址
        return restTemplate.getForObject(
            "http://user-service/api/user/" + id, 
            User.class);
    }
}
```

### Q3: Feign 如何实现负载均衡？

**答：**

Feign 默认集成 Ribbon 实现负载均衡：

```
Feign Client
    ↓
LoadBalancerFeignClient
    ↓
FeignLoadBalancer
    ↓
Ribbon (ILoadBalancer + IRule)
    ↓
选择服务实例
    ↓
发送请求
```

#### 配置方式
```yaml
user-service:
  ribbon:
    NFLoadBalancerRuleClassName: com.netflix.loadbalancer.RandomRule
    ConnectTimeout: 3000
    ReadTimeout: 5000
```

### Q4: Feign 和 RestTemplate 的区别？

**答：**

| 特性 | Feign | RestTemplate |
|------|-------|-------------|
| 使用方式 | 声明式接口 | 编程式调用 |
| 代码简洁度 | 高 | 低 |
| 负载均衡 | 内置 Ribbon | 需要 @LoadBalanced |
| 熔断降级 | 内置支持 | 需要额外配置 |
| 请求拦截 | RequestInterceptor | ClientHttpRequestInterceptor |
| 性能 | 稍低（代理开销） | 稍高 |
| 灵活性 | 较低 | 较高 |

**选择建议**：
- 微服务间调用：推荐 Feign
- 简单场景、外部服务调用：RestTemplate

### Q5: 如何优化 Feign 性能？

**答：**

#### 1. 使用连接池
```xml
<dependency>
    <groupId>io.github.openfeign</groupId>
    <artifactId>feign-httpclient</artifactId>
</dependency>
```

#### 2. 配置连接池参数
```yaml
feign:
  httpclient:
    enabled: true
    max-connections: 200
    max-connections-per-route: 50
```

#### 3. 开启 GZIP 压缩
```yaml
feign:
  compression:
    request:
      enabled: true
    response:
      enabled: true
```

#### 4. 设置合理的超时
```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 5000
        readTimeout: 10000
```

#### 5. 合理配置日志级别
```java
@Bean
public Logger.Level feignLoggerLevel() {
    return Logger.Level.BASIC;  // 生产环境使用 BASIC
}
```

---

**参考链接：**
- [Spring Cloud Ribbon 官方文档](https://cloud.spring.io/spring-cloud-netflix/reference/html/)
- [OpenFeign 官方文档](https://docs.spring.io/spring-cloud-openfeign/docs/current/reference/html/)
- [Ribbon 负载均衡策略详解-掘金](https://juejin.cn/post/7232856790361280573)
- [Feign 核心原理-CSDN](https://blog.csdn.net/zhengwenbo/article/details/108531239)
