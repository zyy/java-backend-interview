# 服务注册与发现

> 微服务架构的核心组件

## 🎯 面试重点

- 服务注册与发现的工作原理
- Eureka vs Zookeeper/Nacos 的区别
- 注册中心的核心功能

## 📖 服务注册与发现原理

### 核心概念

```java
/**
 * 服务注册与发现包含三个角色：
 * 
 * 1. 服务提供者（Provider）
 *    - 启动时向注册中心注册自己的服务
 *    - 运行时定期发送心跳续约
 *    - 停止时向注册中心注销
 * 
 * 2. 注册中心（Registry）
 *    - 保存服务提供者列表
 *    - 接收心跳监测服务健康状态
 *    - 服务消费者查询服务列表
 * 
 * 3. 服务消费者（Consumer）
 *    - 从注册中心获取服务提供者列表
 *    - 通过负载均衡调用服务
 */
public class ServiceDiscovery {
    /*
     * 工作流程：
     * 
     *   Provider              Registry              Consumer
     *     │                     │                     │
     *     │──注册服务──────────→│                     │
     *     │──心跳──────────────→│                     │
     *     │                     │←──查询服务───────────│
     *     │                     │──服务列表──────────→│
     *     │←─────调用───────────│                     │
     */
}
```

### 服务注册

```java
/**
 * 服务注册流程
 */
public class ServiceRegistration {
    // 1. 应用启动时注册
    // Spring Cloud: @EnableDiscoveryClient
    // 服务自动注册到 Eureka Server
    
    // 2. 注册信息包括
    /*
     * {
     *   "app": "ORDER-SERVICE",
     *   "instanceId": "localhost:8080",
     *   "host": "localhost",
     *   "port": 8080,
     *   "status": "UP",
     *   "metadata": {...}
     * }
     */
    
    // 3. 定期续约
    // Eureka: 默认 30 秒续约一次
    // 90 秒未续约则剔除服务
}
```

### 服务发现

```java
/**
 * 服务发现流程
 */
public class ServiceDiscovery {
    // 方式1：客户端发现（Eureka）
    // 客户端从注册中心获取服务列表，自己做负载均衡
    
    // 方式2：服务端发现（Nginx/Kubernetes）
    // 请求先到网关，网关查询注册中心并路由
    
    // Ribbon 负载均衡策略
    /*
     * - RoundRobinRule：轮询
     * - RandomRule：随机
     * - WeightedResponseTimeRule：响应时间加权
     * - BestAvailableRule：选择最空闲
     * - AvailabilityFilteringRule：过滤故障实例
     */
}
```

## 📖 主流注册中心对比

### Eureka

```java
/**
 * Eureka 工作原理
 */
public class Eureka {
    /*
     * 架构：
     * 
     *   Eureka Server          Eureka Client
     *   (注册中心)              (服务提供者/消费者)
     *       ↑                      ↑
     *       │─←──Register──←─────│  注册
     *       │─←──Renew──←────────│  心跳
     *       │─←──Fetch Registry←─│  获取服务列表
     *       │─←──Cancel──←───────│  注销
     * 
     * 特性：
     * - AP 模型（优先可用性）
     * - 自我保护机制（防止网络分区误删）
     * - 客户端负责健康检查
     */
    
    // 配置示例（application.yml）
    /*
     * eureka:
     *   client:
     *     register-with-eureka: true
     *     fetch-registry: true
     *     service-url:
     *       defaultZone: http://localhost:8761/eureka/
     *   instance:
     *     lease-renewal-interval-in-seconds: 30
     *     lease-expiration-duration-in-seconds: 90
     */
}
```

### Nacos

```java
/**
 * Nacos 工作原理
 */
public class Nacos {
    /*
     * Nacos = 服务注册 + 配置管理
     * 
     * 支持：
     * - CP + AP 模式切换
     * - 临时实例（AP）和持久实例（CP）
     * - 命名空间隔离
     * - 集群选举（支持 AP 或 CP）
     * 
     * 对比 Eureka：
     * | 特性      | Eureka     | Nacos      |
     * |-----------|------------|------------|
     * | 一致性模型| AP         | CP + AP    |
     * | 选举机制  | 无         | 有         |
     * | 配置管理  | 无         | 有         |
     * | 多语言    | Java       | 多语言     |
     */
    
    // 配置示例
    /*
     * spring:
     *   cloud:
     *     nacos:
     *       discovery:
     *         server-addr: 127.0.0.1:8848
     *         namespace: dev
     *         group: DEFAULT_GROUP
     */
}
```

### Zookeeper

```java
/**
 * Zookeeper 作为注册中心
 */
public class Zookeeper {
    /*
     * 特性：
     * - CP 模型（强一致性）
     * - Leader 选举
     * - 临时节点（服务下线自动删除）
     * 
     * 缺点：
     * - 选举期间不可用
     * - 服务数量多时性能下降
     * 
     * 适用场景：
     * - 配置管理
     * - 分布式协调
     * - 不适合作为服务注册中心（CP 牺牲可用性）
     */
}
```

### 对比总结

```java
/**
 * 注册中心对比
 */
public class RegistryComparison {
    /*
     * | 特性        | Eureka     | Nacos      | Zookeeper  |
     * |-------------|------------|------------|------------|
     * | 一致性模型   | AP         | AP + CP    | CP         |
     * | 可用性       | 高         | 高         | 低（选举） |
     * | 功能丰富度   | 一般       | 丰富       | 一般       |
     * | 维护活跃度   | 低（停止维护）| 高        | 高         |
     * | 推荐选择     | 兼容旧系统  | 新项目首选 | 特定场景   |
     */
}
```

## 📖 核心面试题

### Q1: Eureka 自我保护机制？

**答：** 
当 Eureka Server 在短时间内丢失过多客户端心跳时，会进入自我保护模式，不再剔除服务，防止网络分区导致误删。表现为`EMERGENCY: EUREKA MAY BE INCORRECTLY CLAIMING INSTANCES ARE UP WHEN THEY'RE NOT.`

### Q2: Eureka 和 Nacos 的区别？

**答：**
- 一致性：Eureka 是 AP，Nacos 同时支持 AP 和 CP
- 功能：Nacos 支持配置管理，Eureka 不支持
- 模型：Nacos 支持临时/持久实例，Eureka 只有临时
- 维护：Eureka 已停止维护，Nacos 活跃

### Q3: 服务注册中心选型考虑因素？

**答：**
- 一致性要求（AP vs CP）
- 集群规模和性能
- 功能需求（是否需要配置管理）
- 维护活跃度
- 多语言支持需求

---

**⭐ 重点：服务注册与发现是微服务架构的基础，理解各注册中心的区别和适用场景**