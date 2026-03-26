---
layout: default
title: Spring Cloud 熔断器详解：Sentinel 与 Resilience4j ⭐⭐⭐
---
# Spring Cloud 熔断器详解：Sentinel 与 Resilience4j ⭐⭐⭐

## 面试题：什么是熔断器？如何实现熔断降级？

### 核心回答

熔断器是一种保护机制，当下游服务出现故障时，自动切断请求，防止故障蔓延。熔断器通过状态机实现 Closed（关闭）、Open（打开）、Half Open（半开）三种状态的转换，结合限流、降级策略，保障系统的高可用。

## 一、熔断器原理

### 1.1 为什么需要熔断器？

```
┌─────────────────────────────────────────────────────────────┐
│                     雪崩效应                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  正常情况：                                                   │
│                                                             │
│  服务 A → 服务 B → 服务 C                                    │
│    ↓        ↓        ↓                                      │
│   10ms    20ms     15ms                                     │
│                                                             │
│  服务 C 故障：                                               │
│                                                             │
│  服务 A → 服务 B → 服务 C（故障）                             │
│    ↓        ↓        ↓                                      │
│  等待...  等待...   超时                                     │
│    ↓        ↓                                               │
│  线程阻塞  线程阻塞                                          │
│    ↓        ↓                                               │
│  资源耗尽  资源耗尽                                          │
│    ↓                                                        │
│  整个系统崩溃！                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    熔断器保护                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  服务 A → 服务 B → [熔断器] → 服务 C                          │
│                      ↓                                      │
│                检测到故障                                    │
│                      ↓                                      │
│                 打开熔断                                     │
│                      ↓                                      │
│            快速返回降级响应                                  │
│                      ↓                                      │
│             保护系统稳定                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 熔断器三状态模型

```
┌─────────────────────────────────────────────────────────────┐
│                   熔断器状态机                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                     请求成功                                 │
│           ┌────────────────────────────┐                   │
│           │                            │                   │
│           ▼                            │                   │
│   ┌───────────────┐                    │                   │
│   │               │                    │                   │
│   │    Closed     │                    │                   │
│   │   (关闭状态)   │                    │                   │
│   │               │                    │                   │
│   │  所有请求正常  │                    │                   │
│   │  通过执行      │                    │                   │
│   │               │                    │                   │
│   └───────┬───────┘                    │                   │
│           │                            │                   │
│           │ 失败率 > 阈值              │                   │
│           │ (如 50%)                   │                   │
│           ▼                            │                   │
│   ┌───────────────┐                    │                   │
│   │               │                    │                   │
│   │     Open      │                    │                   │
│   │   (打开状态)   │                    │                   │
│   │               │                    │                   │
│   │  所有请求直接  │                    │                   │
│   │  返回降级响应  │                    │                   │
│   │               │                    │                   │
│   └───────┬───────┘                    │                   │
│           │                            │                   │
│           │ 等待时间到                  │                   │
│           │ (如 30秒)                  │                   │
│           ▼                            │                   │
│   ┌───────────────┐                    │                   │
│   │               │                    │                   │
│   │  Half Open    │                    │                   │
│   │  (半开状态)    │                    │                   │
│   │               │                    │                   │
│   │  放行部分请求  │────────────────────┘                   │
│   │  探测服务恢复  │                                        │
│   │               │  探测失败                              │
│   └───────────────┘─────────────────────────┐              │
│                                             │              │
│                                             ▼              │
│                                        返回 Open           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 熔断器核心参数

```
┌─────────────────────────────────────────────────────────────┐
│                    熔断器核心参数                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  统计窗口参数：                                               │
│  ├── slidingWindowSize：滑动窗口大小（请求数/时间）          │
│  ├── minimumNumberOfCalls：最小调用次数                      │
│  └── failureRateThreshold：失败率阈值（如 50%）             │
│                                                             │
│  状态转换参数：                                               │
│  ├── waitDurationInOpenState：Open 状态等待时间             │
│  ├── permittedNumberOfCallsInHalfOpenState：半开状态允许请求数│
│  └── slowCallDurationThreshold：慢调用时间阈值              │
│                                                             │
│  降级参数：                                                   │
│  ├── fallbackMethod：降级方法                               │
│  └── fallbackResult：降级返回值                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 二、Sentinel 详解

### 2.1 Sentinel 简介

Sentinel 是阿里巴巴开源的流量控制和熔断降级组件，具有以下特点：

- 丰富的应用场景：流量控制、熔断降级、系统负载保护
- 完善的实时监控：控制台实时查看监控数据
- 广泛的开源生态：Spring Cloud、Dubbo、gRPC
- 完善的 SPI 扩展点：自定义规则、数据源

### 2.2 Sentinel 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                   Sentinel 核心概念                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  资源 (Resource)：                                           │
│  ├── 可以是方法、代码块、接口                                 │
│  └── Sentinel 保护的基本单位                                 │
│                                                             │
│  规则 (Rule)：                                               │
│  ├── 流控规则：FlowRule                                     │
│  ├── 降级规则：DegradeRule                                  │
│  ├── 系统规则：SystemRule                                   │
│  ├── 热点规则：ParamFlowRule                                │
│  └── 授权规则：AuthorityRule                                │
│                                                             │
│  Entry：                                                     │
│  ├── 资源访问的入口                                         │
│  └── SphU.entry("resourceName")                             │
│                                                             │
│  Context：                                                   │
│  ├── 上下文环境                                              │
│  └── 每次资源调用创建一个 Context                            │
│                                                             │
│  ProcessorSlot：                                             │
│  ├── 责任链模式的处理槽                                      │
│  ├── NodeSelectorSlot：选择节点                              │
│  ├── ClusterBuilderSlot：构建集群节点                       │
│  ├── FlowSlot：流控检查                                     │
│  ├── DegradeSlot：熔断检查                                  │
│  └── StatisticSlot：统计数据                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 滑动时间窗口算法

```
┌─────────────────────────────────────────────────────────────┐
│                  滑动时间窗口算法                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  时间轴：                                                    │
│  ──────────────────────────────────────────────→            │
│                                                             │
│  窗口大小：1秒，分为 2 个样本窗口                             │
│                                                             │
│  ┌────────────────┬────────────────┐                       │
│  │  Window 0      │  Window 1      │                       │
│  │  (0-500ms)     │  (500-1000ms)  │                       │
│  │  请求数: 10    │  请求数: 15    │                       │
│  └────────────────┴────────────────┘                       │
│        ↑              ↑                                     │
│        │              │                                     │
│       当前时间 (750ms)                                       │
│                                                             │
│  当前窗口统计：                                              │
│  Window 0 已过期，Window 1 是当前窗口                        │
│  统计结果：15 (当前) + 10 (重置前的旧数据)                    │
│                                                             │
│  窗口滑动：                                                  │
│  时间流逝，窗口向右滑动，旧窗口数据被重置                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Sentinel 规则详解

#### 2.4.1 流控规则（FlowRule）

```java
// 流控规则配置
FlowRule rule = new FlowRule();
rule.setResource("getUser");              // 资源名
rule.setGrade(RuleConstant.FLOW_GRADE_QPS); // 限流阈值类型
rule.setCount(100);                       // 阈值：100 QPS
rule.setStrategy(RuleConstant.STRATEGY_DIRECT); // 流控策略
rule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT); // 流控效果
FlowRuleManager.loadRules(Collections.singletonList(rule));
```

```yaml
# Spring Cloud Alibaba 配置
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
      datasource:
        flow:
          nacos:
            server-addr: localhost:8848
            data-id: sentinel-flow-rules
            rule-type: flow
```

**流控策略**：

| 策略 | 说明 |
|------|------|
| DIRECT | 直接拒绝（默认） |
| ASSOCIATE | 关联限流（关联资源达到阈值时限流） |
| CHAIN | 链路限流（只记录从入口资源进来的流量） |

**流控效果**：

| 效果 | 说明 |
|------|------|
| DEFAULT | 直接拒绝，抛出 FlowException |
| WARM_UP | 预热模式，从阈值/3 逐渐增加到阈值 |
| RATE_LIMITER | 匀速排队，请求在队列中等待 |
| WARM_UP_RATE_LIMITER | 预热 + 匀速排队 |

#### 2.4.2 降级规则（DegradeRule）

```java
// 降级规则配置
DegradeRule rule = new DegradeRule("getUser");
rule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType()); // 熔断策略
rule.setCount(0.5);                 // 阈值：50% 错误率
rule.setTimeWindow(30);             // 熔断时长：30秒
rule.setMinRequestAmount(10);       // 最小请求数
rule.setStatIntervalMs(10000);      // 统计时长：10秒
DegradeRuleManager.loadRules(Collections.singletonList(rule));
```

**熔断策略**：

| 策略 | 说明 | 阈值 |
|------|------|------|
| ERROR_RATIO | 错误比例 | 0.0 - 1.0 |
| ERROR_COUNT | 错误数 | 整数 |
| SLOW_REQUEST_RATIO | 慢调用比例 | 0.0 - 1.0 |

#### 2.4.3 系统规则（SystemRule）

```java
// 系统规则配置
SystemRule rule = new SystemRule();
rule.setHighestSystemLoad(3.0);     // 系统 Load 阈值
rule.setHighestCpuUsage(0.8);       // CPU 使用率阈值
rule.setAvgRt(1000);                // 平均响应时间阈值
rule.setMaxThread(500);             // 最大并发线程数
rule.setQps(1000);                  // 系统 QPS 阈值
SystemRuleManager.loadRules(Collections.singletonList(rule));
```

#### 2.4.4 热点规则（ParamFlowRule）

```java
// 热点参数限流
ParamFlowRule rule = new ParamFlowRule();
rule.setResource("getUser");
rule.setCount(10);                  // 每秒最多 10 次
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setParamIdx(0);                // 第一个参数

// 特定参数例外
ParamFlowItem item = new ParamFlowItem();
item.setObject("VIP_USER");
item.setCount(100);                 // VIP 用户 100 次
rule.setParamFlowItemList(Collections.singletonList(item));

ParamFlowRuleManager.loadRules(Collections.singletonList(rule));
```

```java
// 使用示例
@GetMapping("/user/{id}")
@SentinelResource(value = "getUser", blockHandler = "handleBlock")
public User getUser(@PathVariable String id) {
    return userService.findById(id);
}

// 热点参数限流：对 id 参数限流
// 普通 id：10 QPS
// VIP_USER：100 QPS
```

#### 2.4.5 授权规则（AuthorityRule）

```java
// 授权规则配置
AuthorityRule rule = new AuthorityRule();
rule.setResource("protectedApi");
rule.setStrategy(RuleConstant.AUTHORITY_WHITE); // 白名单模式
rule.setLimitApp("appA,appB");       // 允许的应用
AuthorityRuleManager.loadRules(Collections.singletonList(rule));
```

### 2.5 Sentinel 注解使用

```java
@RestController
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/user/{id}")
    @SentinelResource(
        value = "getUser",                    // 资源名
        blockHandler = "getUserBlockHandler", // 限流降级处理
        blockHandlerClass = UserBlockHandler.class, // 限流处理类
        fallback = "getUserFallback",         // 异常降级处理
        fallbackClass = UserFallback.class,   // 降级处理类
        exceptionsToIgnore = {IllegalArgumentException.class} // 忽略的异常
    )
    public Result<User> getUser(@PathVariable Long id) {
        return Result.success(userService.findById(id));
    }
    
    // 限流/熔断降级方法（必须与原方法参数一致 + BlockException）
    public Result<User> getUserBlockHandler(Long id, BlockException ex) {
        return Result.error("系统繁忙，请稍后再试");
    }
    
    // 异常降级方法（必须与原方法参数一致 + Throwable）
    public Result<User> getUserFallback(Long id, Throwable ex) {
        return Result.error("服务异常: " + ex.getMessage());
    }
}
```

### 2.6 Sentinel 控制台

```bash
# 启动 Sentinel Dashboard
java -Dserver.port=8080 -Dcsp.sentinel.dashboard.server=localhost:8080 -Dproject.name=sentinel-dashboard -jar sentinel-dashboard.jar
```

```yaml
# 应用配置
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080  # 控制台地址
        port: 8719                 # 与控制台通信的端口
      eager: true                  # 应用启动时立即初始化
      datasource:
        flow:
          nacos:
            server-addr: localhost:8848
            data-id: ${spring.application.name}-flow-rules
            group-id: SENTINEL_GROUP
            rule-type: flow
```

### 2.7 Sentinel 集成 Spring Cloud

```xml
<!-- 依赖 -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  application:
    name: user-service
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
        port: 8719
      eager: true
      datasource:
        flow:
          nacos:
            server-addr: localhost:8848
            data-id: ${spring.application.name}-flow-rules
            rule-type: flow
        degrade:
          nacos:
            server-addr: localhost:8848
            data-id: ${spring.application.name}-degrade-rules
            rule-type: degrade

# OpenFeign 集成 Sentinel
feign:
  sentinel:
    enabled: true
```

```java
// OpenFeign 降级配置
@FeignClient(name = "order-service", fallbackFactory = OrderServiceFallbackFactory.class)
public interface OrderServiceClient {
    
    @GetMapping("/order/{userId}")
    Result<List<Order>> getOrders(@PathVariable Long userId);
}

@Component
public class OrderServiceFallbackFactory implements FallbackFactory<OrderServiceClient> {
    
    @Override
    public OrderServiceClient create(Throwable cause) {
        return new OrderServiceClient() {
            @Override
            public Result<List<Order>> getOrders(Long userId) {
                return Result.error("订单服务不可用，请稍后再试");
            }
        };
    }
}
```

### 2.8 Sentinel 核心源码

```java
// SphU.entry() 核心流程
public static Entry entry(String name) throws BlockException {
    return Env.sph.entry(name, EntryType.OUT, 1, OBJECTS0);
}

// CtSph.entry()
public Entry entry(String name, EntryType type, int count, Object... args) throws BlockException {
    // 创建资源包装器
    StringResourceWrapper resource = new StringResourceWrapper(name, type);
    return entry(resource, count, args);
}

// 核心处理链
private Entry entryWithPriority(ResourceWrapper resourceWrapper, int count, boolean prioritized, Object... args) throws BlockException {
    // 创建 Context
    Context context = ContextUtil.getContext();
    
    // 创建 ProcessorSlotChain
    ProcessorSlot<Object> chain = lookProcessChain(resourceWrapper);
    
    // 创建 Entry
    Entry e = new CtEntry(resourceWrapper, chain, context);
    
    // 执行处理链
    chain.entry(context, resourceWrapper, null, count, prioritized, args);
    
    return e;
}

// ProcessorSlotChain 结构
public class DefaultProcessorSlotChain extends ProcessorSlotChain {
    
    AbstractLinkedProcessorSlot<?> first = new AbstractLinkedProcessorSlot<Object>() {};
    AbstractLinkedProcessorSlot<?> end = first;
    
    @Override
    public void entry(Context context, ResourceWrapper resourceWrapper, Object param, int count, boolean prioritized, Object... args) throws Throwable {
        // 依次执行各个 Slot
        first.transformEntry(context, resourceWrapper, param, count, prioritized, args);
    }
}

// Slot 执行顺序
// NodeSelectorSlot → ClusterBuilderSlot → LogSlot → StatisticSlot → 
// AuthoritySlot → SystemSlot → FlowSlot → DegradeSlot
```

## 三、Resilience4j 详解

### 3.1 Resilience4j 简介

Resilience4j 是一个轻量级的容错库，灵感来自 Netflix Hystrix，但设计更加轻量和模块化。

**核心模块**：

| 模块 | 功能 |
|------|------|
| CircuitBreaker | 熔断器 |
| RateLimiter | 限流器 |
| Retry | 重试 |
| Bulkhead | 舱壁隔离 |
| Cache | 缓存 |
| Timelimiter | 超时控制 |

### 3.2 Resilience4j 熔断器

#### 3.2.1 配置方式

```yaml
# application.yml
resilience4j:
  circuitbreaker:
    configs:
      default:
        slidingWindowType: COUNT_BASED        # 滑动窗口类型
        slidingWindowSize: 10                 # 滑动窗口大小
        minimumNumberOfCalls: 5               # 最小调用次数
        failureRateThreshold: 50              # 失败率阈值
        waitDurationInOpenState: 10s          # Open 状态等待时间
        permittedNumberOfCallsInHalfOpenState: 3  # 半开状态允许请求数
        slowCallDurationThreshold: 2s         # 慢调用时间阈值
        slowCallRateThreshold: 50             # 慢调用率阈值
        automaticTransitionFromOpenToHalfOpenEnabled: true  # 自动转半开
    instances:
      userService:
        baseConfig: default
      orderService:
        slidingWindowSize: 20
        failureRateThreshold: 30
```

#### 3.2.2 注解使用

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    // 熔断器
    @CircuitBreaker(name = "userService", fallbackMethod = "getUserFallback")
    public User getUser(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException("用户不存在"));
    }
    
    // 降级方法（参数需与原方法一致 + Exception）
    private User getUserFallback(Long id, Exception ex) {
        log.warn("获取用户失败，使用降级数据: {}", id);
        return User.builder()
            .id(id)
            .name("默认用户")
            .build();
    }
}
```

#### 3.2.3 编程式使用

```java
@Service
public class UserService {
    
    private final CircuitBreaker circuitBreaker;
    
    public UserService(CircuitBreakerRegistry registry) {
        this.circuitBreaker = registry.circuitBreaker("userService");
    }
    
    public User getUser(Long id) {
        return circuitBreaker.executeSupplier(() -> {
            return userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("用户不存在"));
        });
    }
    
    // 带降级的调用
    public User getUserWithFallback(Long id) {
        Supplier<User> supplier = CircuitBreaker.decorateSupplier(
            circuitBreaker, 
            () -> userRepository.findById(id).orElse(null)
        );
        
        return Try.ofSupplier(supplier)
            .recover(throwable -> User.builder().id(id).name("默认用户").build())
            .get();
    }
}
```

### 3.3 Resilience4j 限流器

```yaml
# application.yml
resilience4j:
  ratelimiter:
    configs:
      default:
        limitForPeriod: 10            # 每个周期允许的请求数
        limitRefreshPeriod: 1s        # 刷新周期
        timeoutDuration: 0            # 等待获取许可的超时时间
    instances:
      userService:
        baseConfig: default
```

```java
@Service
public class UserService {
    
    // 限流器
    @RateLimiter(name = "userService", fallbackMethod = "rateLimitFallback")
    public User getUser(Long id) {
        return userRepository.findById(id).orElse(null);
    }
    
    private User rateLimitFallback(Long id, RequestNotPermitted ex) {
        throw new RuntimeException("请求过于频繁，请稍后再试");
    }
}
```

### 3.4 Resilience4j 重试

```yaml
# application.yml
resilience4j:
  retry:
    configs:
      default:
        maxAttempts: 3                # 最大尝试次数（包括首次）
        waitDuration: 500ms           # 重试等待时间
        exponentialBackoffMultiplier: 2  # 指数退避因子
        retryExceptions:              # 触发重试的异常
          - java.io.IOException
          - java.net.SocketTimeoutException
        ignoreExceptions:             # 不重试的异常
          - java.lang.IllegalArgumentException
    instances:
      userService:
        baseConfig: default
```

```java
@Service
public class UserService {
    
    @Retry(name = "userService", fallbackMethod = "getUserFallback")
    public User getUser(Long id) {
        return callRemoteService(id);
    }
    
    private User getUserFallback(Long id, Exception ex) {
        return User.builder().id(id).name("默认用户").build();
    }
}
```

### 3.5 Resilience4j 舱壁隔离

```yaml
# application.yml
resilience4j:
  bulkhead:
    configs:
      default:
        maxConcurrentCalls: 25        # 最大并发数
        maxWaitDuration: 0            # 等待获取许可的时间
    instances:
      userService:
        baseConfig: default

  # 信号量隔离
  thread-pool-bulkhead:
    configs:
      default:
        maxThreadPoolSize: 10         # 最大线程数
        coreThreadPoolSize: 5         # 核心线程数
        queueCapacity: 20             # 队列容量
        keepAliveDuration: 20s        # 空闲线程存活时间
```

```java
@Service
public class UserService {
    
    // 舱壁隔离
    @Bulkhead(name = "userService", fallbackMethod = "bulkheadFallback")
    public User getUser(Long id) {
        return userRepository.findById(id).orElse(null);
    }
    
    private User bulkheadFallback(Long id, BulkheadFullException ex) {
        throw new RuntimeException("系统繁忙，请稍后再试");
    }
    
    // 线程池隔离
    @Bulkhead(name = "userService", type = Bulkhead.Type.THREADPOOL)
    public CompletableFuture<User> getUserAsync(Long id) {
        return CompletableFuture.supplyAsync(() -> 
            userRepository.findById(id).orElse(null)
        );
    }
}
```

### 3.6 组合使用

```java
@Service
public class UserService {
    
    // 组合多个容错机制
    @CircuitBreaker(name = "userService", fallbackMethod = "fallback")
    @RateLimiter(name = "userService")
    @Retry(name = "userService")
    @Bulkhead(name = "userService")
    @TimeLimiter(name = "userService")
    public CompletableFuture<User> getUser(Long id) {
        return CompletableFuture.supplyAsync(() -> 
            userRepository.findById(id).orElse(null)
        );
    }
    
    private CompletableFuture<User> fallback(Long id, Exception ex) {
        return CompletableFuture.completedFuture(
            User.builder().id(id).name("默认用户").build()
        );
    }
}
```

```yaml
# 完整配置
resilience4j:
  timelimiter:
    configs:
      default:
        timeoutDuration: 2s           # 超时时间
        cancelRunningFuture: true     # 超时是否取消运行中的 Future
    instances:
      userService:
        baseConfig: default
```

### 3.7 Resilience4j 监控

```java
@Configuration
public class Resilience4jConfig {
    
    @Bean
    public CircuitBreaker circuitBreaker(CircuitBreakerRegistry registry) {
        CircuitBreaker circuitBreaker = registry.circuitBreaker("userService");
        
        // 注册事件监听器
        circuitBreaker.getEventPublisher()
            .onSuccess(event -> log.info("调用成功: {}", event))
            .onError(event -> log.error("调用失败: {}", event))
            .onStateTransition(event -> log.info("状态转换: {}", event))
            .onSlowCall(event -> log.warn("慢调用: {}", event));
        
        return circuitBreaker;
    }
}
```

```yaml
# Actuator 配置
management:
  endpoints:
    web:
      exposure:
        include: health,circuitbreakers,circuitbreakerevents
  endpoint:
    health:
      show-details: always
  health:
    circuitbreakers:
      enabled: true
```

## 四、Sentinel vs Hystrix vs Resilience4j 对比

### 4.1 功能对比

```
┌─────────────────────────────────────────────────────────────┐
│              三种熔断器功能对比                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┬──────────┬───────────┬─────────────┐  │
│  │     功能         │ Hystrix  │ Sentinel  │ Resilience4j│  │
│  ├─────────────────┼──────────┼───────────┼─────────────┤  │
│  │ 熔断器          │    ✅    │    ✅     │     ✅      │  │
│  │ 限流            │    ❌    │    ✅     │     ✅      │  │
│  │ 热点参数限流     │    ❌    │    ✅     │     ❌      │  │
│  │ 系统自适应保护   │    ❌    │    ✅     │     ❌      │  │
│  │ 重试            │    ❌    │    ❌     │     ✅      │  │
│  │ 舱壁隔离        │    ✅    │    ✅     │     ✅      │  │
│  │ 控制台          │    ✅    │    ✅     │     ❌      │  │
│  │ 实时监控        │    ✅    │    ✅     │     ✅      │  │
│  │ 动态配置        │    ✅    │    ✅     │     ✅      │  │
│  │ Spring Cloud集成│    ✅    │    ✅     │     ✅      │  │
│  │ 维护状态        │  停止维护 │   活跃    │     活跃    │  │
│  └─────────────────┴──────────┴───────────┴─────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 性能对比

| 特性 | Hystrix | Sentinel | Resilience4j |
|------|---------|---------|--------------|
| 实现语言 | Java | Java | Java |
| 隔离策略 | 线程池/信号量 | 信号量 | 信号量/线程池 |
| 熔断策略 | 异常比例 | 异常比例/慢调用 | 异常比例/慢调用 |
| 限流算法 | 无 | 滑动窗口/令牌桶 | 令牌桶 |
| 性能开销 | 较高 | 低 | 低 |
| 内存占用 | 较高 | 低 | 低 |

### 4.3 选型建议

```
┌─────────────────────────────────────────────────────────────┐
│                     选型建议                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  选择 Sentinel：                                             │
│  ├── 需要完善的控制台和可视化监控                            │
│  ├── 需要热点参数限流                                       │
│  ├── 需要系统自适应保护                                     │
│  ├── 已有 Spring Cloud Alibaba 生态                         │
│  └── 需要丰富的限流场景                                     │
│                                                             │
│  选择 Resilience4j：                                         │
│  ├── 需要轻量级解决方案                                     │
│  ├── 需要重试功能                                           │
│  ├── 需要模块化组合使用                                     │
│  ├── 已有 Spring Cloud 生态（非 Alibaba）                   │
│  └── 不需要控制台                                           │
│                                                             │
│  不推荐 Hystrix：                                            │
│  └── 已停止维护，建议迁移到 Sentinel 或 Resilience4j        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 五、熔断降级在 Spring Cloud 中的集成

### 5.1 Gateway + Sentinel

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-alibaba-sentinel-gateway</artifactId>
</dependency>
```

```yaml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
```

### 5.2 OpenFeign + Sentinel

```yaml
feign:
  sentinel:
    enabled: true
```

```java
@FeignClient(name = "user-service", fallback = UserServiceFallback.class)
public interface UserServiceClient {
    
    @GetMapping("/user/{id}")
    User getUser(@PathVariable Long id);
}

@Component
public class UserServiceFallback implements UserServiceClient {
    
    @Override
    public User getUser(Long id) {
        return User.builder().id(id).name("默认用户").build();
    }
}
```

### 5.3 RestTemplate + Sentinel

```java
@Configuration
public class RestTemplateConfig {
    
    @Bean
    @LoadBalanced
    @SentinelRestTemplate(
        blockHandler = "handleBlock",
        blockHandlerClass = SentinelExceptionHandler.class,
        fallback = "handleFallback",
        fallbackClass = SentinelExceptionHandler.class
    )
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

public class SentinelExceptionHandler {
    
    public static ResponseEntity<String> handleBlock(HttpRequest request, 
                                                     byte[] body, 
                                                     ClientHttpRequestExecution execution, 
                                                     BlockException ex) {
        return ResponseEntity.status(429).body("请求被限流");
    }
    
    public static ResponseEntity<String> handleFallback(HttpRequest request, 
                                                        byte[] body, 
                                                        ClientHttpRequestExecution execution, 
                                                        Throwable ex) {
        return ResponseEntity.status(500).body("服务降级");
    }
}
```

## 📖 高频面试题

### Q1: 熔断器的三种状态是如何转换的？

**答：**

#### 1. Closed（关闭）状态
- 正常状态，所有请求正常通过
- 统计请求的成功/失败率
- 当失败率超过阈值时，转换为 Open 状态

#### 2. Open（打开）状态
- 熔断状态，所有请求直接返回降级响应
- 不执行实际业务逻辑
- 等待时间结束后，转换为 Half Open 状态

#### 3. Half Open（半开）状态
- 放行部分请求探测服务恢复情况
- 如果探测成功，转换为 Closed 状态
- 如果探测失败，转换回 Open 状态

```
Closed --[失败率>阈值]--> Open --[等待时间到]--> Half Open
   ↑                                                      |
   |                                                      |
   +------------------[探测成功]---------------------------+
   |
   +------------------[探测失败]--------------------------> Open
```

### Q2: Sentinel 和 Resilience4j 的区别？

**答：**

| 特性 | Sentinel | Resilience4j |
|------|---------|--------------|
| 控制台 | 完善 | 无 |
| 热点参数限流 | 支持 | 不支持 |
| 系统自适应保护 | 支持 | 不支持 |
| 重试机制 | 不支持 | 支持 |
| 轻量级 | 一般 | 更轻量 |
| 学习曲线 | 较陡 | 较平缓 |
| 社区活跃度 | 高 | 高 |

**选择建议**：
- 需要 Web 控制台、热点参数限流 → Sentinel
- 需要轻量级、重试功能 → Resilience4j

### Q3: 如何实现服务降级？

**答：**

#### 1. Sentinel 方式
```java
@SentinelResource(value = "getUser", 
                  fallback = "getUserFallback")
public User getUser(Long id) {
    return userRepository.findById(id);
}

public User getUserFallback(Long id, Throwable ex) {
    return User.builder().id(id).name("默认用户").build();
}
```

#### 2. Resilience4j 方式
```java
@CircuitBreaker(name = "userService", 
                fallbackMethod = "getUserFallback")
public User getUser(Long id) {
    return userRepository.findById(id);
}

private User getUserFallback(Long id, Exception ex) {
    return User.builder().id(id).name("默认用户").build();
}
```

#### 3. OpenFeign 降级
```java
@FeignClient(name = "user-service", 
             fallback = UserServiceFallback.class)
public interface UserServiceClient { }

@Component
public class UserServiceFallback implements UserServiceClient {
    @Override
    public User getUser(Long id) {
        return User.builder().id(id).name("默认用户").build();
    }
}
```

### Q4: Sentinel 的滑动窗口算法原理？

**答：**

滑动窗口算法将时间划分为多个时间片（样本窗口），统计最近 N 个窗口内的请求数据。

#### 1. 窗口结构
- 窗口大小：如 1 秒
- 样本窗口：如 500ms，分为 2 个样本
- 数组存储：环形数组存储各样本窗口数据

#### 2. 统计过程
```
时间轴：──[Window0]──[Window1]──[Window2]──[Window3]──→

当前时间：Window2
统计窗口：Window0 + Window1（最近 2 个样本）

当时间进入 Window3：
统计窗口：Window1 + Window2
Window0 被重置，存储新数据
```

#### 3. 优势
- 时间精度高
- 内存占用小
- 统计实时性好

### Q5: 如何防止雪崩效应？

**答：**

#### 1. 熔断降级
- 使用 Sentinel/Resilience4j 实现熔断器
- 服务故障时快速失败
- 返回降级响应

#### 2. 限流
- QPS 限流：限制每秒请求数
- 并发限流：限制并发线程数
- 热点参数限流：限制热点数据访问

#### 3. 超时控制
- 设置合理的超时时间
- 避免无限等待

#### 4. 舱壁隔离
- 线程池隔离：每个服务使用独立线程池
- 信号量隔离：限制并发访问数

#### 5. 重试机制
- 合理配置重试次数
- 指数退避避免重试风暴

---

**参考链接：**
- [Sentinel 官方文档](https://sentinelguard.io/zh-cn/docs/introduction.html)
- [Resilience4j 官方文档](https://resilience4j.readme.io/)
- [Spring Cloud Alibaba Sentinel-掘金](https://juejin.cn/post/7232856790361280572)
- [熔断器模式详解-CSDN](https://blog.csdn.net/zhengwenbo/article/details/108531239)
