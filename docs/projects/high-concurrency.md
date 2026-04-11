---
layout: default
title: 高并发系统设计：核心思路与实践 ⭐⭐⭐
---
# 高并发系统设计：核心思路与实践 ⭐⭐⭐

## 🎯 面试题：如何设计一个高并发系统？

> 高并发系统设计是面试最高频的系统设计题，没有之一。无论是阿里、字节、腾讯还是美团，但凡面高级工程师及以上岗位，几乎必问高并发相关问题。本质考察的是：对系统全链路的理解深度、问题拆解能力、以及在流量洪峰面前的架构决策能力。

---

## 一、高并发核心指标

### 1.1 关键性能指标详解

```
高并发系统的核心指标体系：

┌─────────────────────────────────────────────────────────────┐
│                      核心指标体系                              │
├─────────────────────────────────────────────────────────────┤
│  QPS (Queries Per Second)                                   │
│    └─ 每秒请求数，衡量系统吞吐能力的基准指标                    │
│                                                             │
│  TPS (Transactions Per Second)                              │
│    └─ 每秒事务数，一个事务可能包含多个请求                     │
│                                                             │
│  并发数 (Concurrent Users)                                   │
│    └─ 同时在线的用户数，与 QPS 非线性相关                      │
│                                                             │
│  响应时间 (Response Time)                                    │
│    └─ p50/p95/p99/p999 分布                                  │
│                                                             │
│  错误率 (Error Rate)                                         │
│    └─ 5xx/4xx 占比、超时率                                   │
│                                                             │
│  资源利用率                                                  │
│    └─ CPU/内存/磁盘 IO/网络 IO                               │
└─────────────────────────────────────────────────────────────┘
```

**QPS vs TPS 的区别：**

```java
// QPS：每秒钟请求数
// 一个页面请求可能包含 10 个接口
// 10000 QPS 的页面 = 100000 QPS 的后端接口

// TPS：每秒钟事务数
// 一个事务 = 一次完整的业务操作
// 例如：一次下单 = 1 TPS（内部可能调用 5 个接口）
```

### 1.2 响应时间的分位数

```
分位数的含义：

100 个请求的响应时间从小到大排序：
  p50 = 第 50 个请求的响应时间（中位数）
  p95 = 第 95 个请求的响应时间
  p99 = 第 99 个请求的响应时间
  p999 = 第 999 个请求的响应时间

为什么关注 p99/p999？
  - p50 只能反映一半用户的体验
  - p99 反映的是"那 1% 的用户可能正在骂你"
  - 电商大促时，p999 才是生命线

典型目标：
  - p50 < 200ms（优秀）
  - p95 < 500ms（良好）
  - p99 < 1s（及格）
  - p999 < 2s（高并发场景可接受）
```

### 1.3 并发数的计算

```java
// 并发数估算公式
// 并发数 = QPS × 平均响应时间（秒）

// 示例：
// QPS = 10000，平均响应时间 = 100ms
// 并发数 = 10000 × 0.1 = 1000 个并发请求

// 线程数估算
// 最佳线程数 = CPU 核心数 × 期望 CPU 利用率 × (1 + 等待时间/处理时间)
// IO 密集型：最佳线程数 = CPU 核心数 × 2 ~ 3
// CPU 密集型：最佳线程数 = CPU 核心数 + 1
```

---

## 二、分层架构设计

### 2.1 高并发系统分层架构

```
用户请求的完整链路：

┌─────────────────────────────────────────────────────────────────────┐
│                           用户层                                      │
│   (浏览器 / App / 小程序)                                             │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CDN 层                                        │
│   └─ 静态资源缓存（JS/CSS/图片/视频）                                  │
│   └─ 就近接入（全国 CDN 节点）                                         │
│   └─ 边缘计算（简单逻辑下沉）                                          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         接入层                                        │
│   └─ DNS 解析（智能调度）                                             │
│   └─ 负载均衡（Nginx / LVS / SLB）                                   │
│   └─ SSL 卸载                                                        │
│   └─ 请求限流（令牌桶 / 漏桶）                                         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         网关层                                        │
│   └─ 统一鉴权（Token 验证）                                            │
│   └─ 路由转发（微服务网关）                                            │
│   └─ 请求染色（TraceId 透传）                                         │
│   └─ 熔断降级（Sentinel / Hystrix）                                  │
│   └─ 风控拦截（黑名单 / 频率限制）                                      │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        应用层                                         │
│   └─ 业务逻辑处理                                                     │
│   └─ 服务编排（Spring Cloud / Dubbo）                                 │
│   └─ 线程池并行调用                                                   │
│   └─ 本地缓存（Caffeine / Guava Cache）                              │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        缓存层                                         │
│   └─ 多级缓存（本地 → Redis → CDN）                                   │
│   └─ 热点数据探测                                                     │
│   └─ 缓存预热                                                        │
│   └─ 缓存淘汰策略                                                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据层                                         │
│   └─ 读写分离（主从复制）                                              │
│   └─ 分库分表（水平/垂直分片）                                         │
│   └─ 连接池优化（HikariCP / Druid）                                   │
│   └─ SQL 优化（索引 / 执行计划）                                       │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      基础设施层                                        │
│   └─ 容器化部署（Docker / K8s）                                       │
│   └─ 服务网格（Istio）                                                │
│   └─ 日志 / 监控 / 告警                                               │
│   └─ 弹性伸缩（Auto Scaling）                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 每层防护的目标

```
分层防护的核心思想：层层过滤，把流量挡在靠近用户的那一层

层级         拦截目标                    防护手段
─────────────────────────────────────────────────────────
CDN 层       静态资源请求                 浏览器缓存、CDN 缓存
接入层       非法请求、CC 攻击             IP 限流、验证码
网关层       恶意调用、业务攻击             鉴权、风控、熔断
应用层       业务层流量                    线程池隔离、接口限流
缓存层       数据库访问                    多级缓存、热点探测
数据层       持久化写入                    读写分离、分库分表

目标：每层过滤掉 80% 的流量，数据库只承受 1% 的压力
```

---

## 三、流量防护体系

### 3.1 限流算法

#### 令牌桶算法

```
令牌桶的核心思想：以固定速率向桶中添加令牌，请求来时取令牌，桶满则丢弃

┌────────────────────────────────────────┐
│           令牌桶示意图                  │
│                                        │
│      ┌──────────────────────┐         │
│      │   令牌生成器          │         │
│      │   (每秒 N 个令牌)     │         │
│      └─────────┬────────────┘         │
│                │                        │
│                ▼                        │
│      ┌──────────────────────┐         │
│      │       桶              │         │
│      │         令牌          │         │
│      │   令牌令牌 令牌        │         │
│      │    令牌令牌            │         │
│      │   桶容量 = M           │         │
│      └─────────┬────────────┘         │
│                │                        │
│                ▼  取令牌                │
│      ┌──────────────────────┐         │
│      │    请求通过           │         │
│      └──────────────────────┘         │
└────────────────────────────────────────┘

特点：
  - 允许一定程度的突发流量（桶内有令牌）
  - 令牌桶满时新令牌被丢弃，不影响已存在的令牌
  - 适合限流场景：允许瞬时高峰，但限制总量
```

```java
// Java 实现令牌桶（Guava RateLimiter）
public class TokenBucketRateLimiter {

    // 每秒产生 100 个令牌，桶容量 200
    private final RateLimiter rateLimiter = RateLimiter.create(100, 200);

    public boolean tryAcquire() {
        // 尝试获取一个令牌，非阻塞立即返回
        return rateLimiter.tryAcquire();
    }

    public boolean tryAcquireWithTimeout(long timeout, TimeUnit unit) {
        // 等待最多 timeout 时间获取令牌
        return rateLimiter.tryAcquire(timeout, unit);
    }

    // 在 Controller 中使用
    @GetMapping("/api/resource")
    public ResponseEntity<?> getResource() {
        if (!rateLimiter.tryAcquire()) {
            return ResponseEntity.status(429)
                .body("请求过于频繁，请稍后再试");
        }
        // 业务逻辑
        return ResponseEntity.ok(resourceService.get());
    }
}
```

#### 漏桶算法

```
漏桶的核心思想：请求像水一样进入漏桶，以固定速率漏出，超出容量则拒绝

┌────────────────────────────────────────┐
│           漏桶示意图                    │
│                                        │
│      ┌──────────────────────┐         │
│      │       入水            │         │
│      │    请求请求请求       │         │
│      └─────────┬────────────┘         │
│                │                        │
│                ▼                        │
│      ┌──────────────────────┐         │
│      │       桶              │         │
│      │    请求请求            │         │
│      │   桶容量 = M           │         │
│      └─────────┬────────────┘         │
│                │                        │
│                ▼  固定速率漏出           │
│      ┌──────────────────────┐         │
│      │    请求通过           │         │
│      └──────────────────────┘         │
└────────────────────────────────────────┘

特点：
  - 无论请求多少，流出速率恒定
  - 严格平整流量，不允许突发
  - 适合下游保护场景：下游处理能力固定，不允许瞬时冲击
```

#### 令牌桶 vs 漏桶

```
对比维度          令牌桶                    漏桶
─────────────────────────────────────────────────────────
允许突发          是（桶内有令牌）           否（严格均匀）
实现复杂度        中等                      简单
适用场景          限流（保护自己）           削峰（保护下游）
算法特性          配额消费                  队列排队

实际选择：
  - 保护自己的接口：令牌桶（允许用户快速响应）
  - 保护下游 MQ/数据库：漏桶（严格控制消费速率）
```

### 3.2 Sentinel 限流实战

```java
// Sentinel 限流配置
@Configuration
public class SentinelConfig {

    // 自定义流控规则
    @PostConstruct
    public void initFlowRules() {
        List<FlowRule> rules = new ArrayList<>();

        // 秒杀接口：每秒 100 次
        FlowRule seckillRule = new FlowRule("/api/seckill/do");
        seckillRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        seckillRule.setCount(100);
        seckillRule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT);
        seckillRule.setMaxQueueingTimeMs(500);  // 排队等待时间
        rules.add(seckillRule);

        // 普通接口：每秒 1000 次
        FlowRule normalRule = new FlowRule("/api/normal");
        normalRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        normalRule.setCount(1000);
        rules.add(normalRule);

        FlowRuleManager.loadRules(rules);
    }
}

// 在 Service 中使用
@Service
public class OrderService {

    @SentinelResource(value = "createOrder", blockHandler = "handleBlock")
    public Result<Order> createOrder(OrderRequest request) {
        // 正常业务逻辑
        return Result.success(orderMapper.insert(request));
    }

    // 限流降级处理
    public Result<Order> handleBlock(BlockException e) {
        return Result.error("系统繁忙，请稍后再试");
    }
}
```

### 3.3 熔断降级

```
熔断器的工作原理：

        ┌────────────────────────────────────────┐
        │              熔断器状态机               │
        │                                         │
        │      ┌─────────┐   失败率过高   ┌──────────┐
        │      │  Closed │ ──────────────→│  Open   │
        │      │  正常   │                 │  熔断中  │
        │      │  请求   │                 │  直接   │
        │      └─────────┘                 │  拒绝   │
        │            │                      └────┬─────┘
        │            │                           │
        │            │  探测成功                  │
        │            │                           │
        │            ▼                      半开状态│
        │      ┌─────────┐ ◀────────────────┐     │
        │      │  Half   │ ────────────────│─────┘
        │      │  Open   │   探测请求通过   │
        │      └─────────┘                 │
        └────────────────────────────────────────┘

熔断策略：
  - 慢调用比例：响应时间 > 阈值 的请求占比
  - 异常比例：异常请求占总请求的比例
  - 异常数：单位时间内异常请求数
```

```java
// Sentinel 熔断配置
@PostConstruct
public void initDegradeRules() {
    List<DegradeRule> rules = new ArrayList<>();

    // 慢调用熔断：响应时间 > 1s 的请求占比 50% 时熔断 10 秒
    DegradeRule slowRule = new DegradeRule("createOrder");
    slowRule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType());
    slowRule.setCount(0.5);  // 50% 失败率
    slowRule.setSlowRatioThreshold(1000);  // 响应时间 > 1s 视为慢调用
    slowRule.setMinRequestAmount(10);  // 最小请求数
    slowRule.setStatIntervalMs(10000);  // 统计时间窗口 10 秒
    slowRule.setTimeWindow(10);  // 熔断持续时间 10 秒
    rules.add(slowRule);

    DegradeRuleManager.loadRules(rules);
}
```

### 3.4 隔离策略

```
隔离的核心思想：不把鸡蛋放在一个篮子里

┌─────────────────────────────────────────────────────────────┐
│                    隔离策略分类                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  线程池隔离                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │ 线程池1 │ │ 线程池2 │ │ 线程池3 │                       │
│  │  5 线程 │ │ 10 线程 │ │ 20 线程 │                       │
│  └────┬────┘ └────┬────┘ └────┬────┘                       │
│       │          │          │                              │
│       ▼          ▼          ▼                              │
│   订单服务    支付服务    库存服务                          │
│                                                              │
│  信号量隔离                                                 │
│  ┌─────────┐ ┌─────────┐                                 │
│  │ 信号量1 │ │ 信号量2 │  ← 不创建线程，用计数器限流       │
│  │  100   │ │  200   │                                   │
│  └─────────┘ └─────────┘                                 │
│                                                              │
│  进程隔离                                                   │
│  ┌─────────┐ ┌─────────┐                                 │
│  │ 进程1   │ │ 进程2   │  ← 不同服务部署在不同机器         │
│  │ 秒杀服务 │ │  普通服务│                                  │
│  └─────────┘ └─────────┘                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 线程池隔离实战
@Configuration
public class ThreadPoolConfig {

    // 订单服务线程池
    @Bean("orderExecutor")
    public Executor orderExecutor() {
        return new ThreadPoolExecutor(
            10,  // 核心线程
            50,  // 最大线程
            60,  // 空闲存活时间
            TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),  // 队列容量
            new ThreadFactoryBuilder().setNamePrefix("order-").build(),
            new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略：调用方执行
        );
    }

    // 消息通知线程池
    @Bean("notifyExecutor")
    public Executor notifyExecutor() {
        return new ThreadPoolExecutor(
            5, 20, 60, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(5000),
            new ThreadFactoryBuilder().setNamePrefix("notify-").build(),
            new ThreadPoolExecutor.DiscardPolicy()
        );
    }
}

// 使用
@Service
public class OrderService {

    @Autowired
    @Qualifier("orderExecutor")
    private Executor executor;

    public void createOrderAsync(Order order) {
        executor.execute(() -> {
            orderMapper.insert(order);
            // 后续逻辑
        });
    }
}
```

---

## 四、缓存为王

### 4.1 多级缓存架构

```
高并发系统的缓存层级：

┌─────────────────────────────────────────────────────────────────┐
│                        多级缓存架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L1: 浏览器缓存                                                 │
│     - 静态资源：JS/CSS/图片                                      │
│     - 策略：Cache-Control / Etag                                 │
│     - 命中率：通常 60-80%                                        │
│                                                                  │
│  L2: CDN 缓存                                                   │
│     - 边缘节点缓存                                               │
│     - 静态页面/接口响应                                          │
│     - 命中率：通常 40-60%                                        │
│                                                                  │
│  L3: Nginx 缓存                                                 │
│     - OpenResty / Lua 缓存                                       │
│     - 热点数据                                                   │
│     - 命中率：通常 30-50%                                        │
│                                                                  │
│  L4: 本地缓存                                                   │
│     - Caffeine / Guava Cache                                    │
│     - JVM 进程内缓存                                             │
│     - 命中率：通常 20-40%                                        │
│                                                                  │
│  L5: 分布式缓存                                                 │
│     - Redis / Memcached                                         │
│     - 跨进程共享                                                 │
│     - 命中率：通常 10-30%（视业务而定）                            │
│                                                                  │
│  L6: 数据库                                                     │
│     - 最终数据来源                                               │
│     - 只读场景尽量绕过                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

关键认知：
  - 缓存不是银弹，命中率才是核心
  - 层级越多，缓存成本越高，一致性越难保证
  - 根据业务特性选择合适的缓存层级组合
```

### 4.2 缓存策略详解

```java
// 多级缓存实现
@Service
public class ProductCacheService {

    // L1: 本地缓存（Caffeine）
    private final Cache<String, ProductVO> localCache = Caffeine.newBuilder()
        .maximumSize(10000)
        .expireAfterWrite(1, TimeUnit.MINUTES)
        .build();

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private ProductMapper productMapper;

    public ProductVO getProduct(Long productId) {
        String cacheKey = "product:" + productId;

        // L1: 查本地缓存
        ProductVO result = localCache.getIfPresent(cacheKey);
        if (result != null) {
            return result;
        }

        // L2: 查 Redis
        String redisValue = redisTemplate.opsForValue().get(cacheKey);
        if (redisValue != null) {
            result = JSON.parseObject(redisValue, ProductVO.class);
            localCache.put(cacheKey, result);  // 回填本地缓存
            return result;
        }

        // L3: 查数据库
        result = productMapper.selectById(productId);
        if (result != null) {
            // 回填 Redis
            redisTemplate.opsForValue().set(cacheKey,
                JSON.toJSONString(result),
                10, TimeUnit.MINUTES);
            // 回填本地缓存
            localCache.put(cacheKey, result);
        }

        return result;
    }

    // 缓存更新：双删策略
    public void updateProduct(ProductVO product) {
        String cacheKey = "product:" + product.getId();

        // 1. 先删除缓存
        localCache.invalidate(cacheKey);
        redisTemplate.delete(cacheKey);

        // 2. 更新数据库
        productMapper.updateById(product);

        // 3. 延迟删除（应对并发：其他线程可能刚读到旧数据）
        new Thread(() -> {
            try {
                Thread.sleep(500);
                redisTemplate.delete(cacheKey);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }).start();
    }
}
```

### 4.3 缓存命中率分析

```
缓存命中率的计算与优化：

┌─────────────────────────────────────────────────────────────┐
│                     缓存命中分析                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  缓存命中率 = 命中次数 / 总请求次数                           │
│                                                              │
│  典型场景的命中率：                                           │
│  ┌─────────────────┬────────────┬────────────┐              │
│  │ 业务场景        │ 缓存命中率  │ 说明       │              │
│  ├─────────────────┼────────────┼────────────┤              │
│  │ 热点商品详情    │ 95%+       │ 1% 的商    │              │
│  │                 │            │ 品贡献 99% │              │
│  │                 │            │ 的访问     │              │
│  │ 用户画像        │ 80-90%     │ 用户行为   │              │
│  │                 │            │ 相对稳定   │              │
│  │ 列表页         │ 30-50%     │ 分页参数   │              │
│  │                 │            │ 多样       │              │
│  │ 实时数据       │ 10-20%     │ 数据变化   │              │
│  │                 │            │ 频繁       │              │
│  └─────────────────┴────────────┴────────────┘              │
│                                                              │
│  命中率低的常见原因：                                          │
│  1. 缓存 key 设计不合理（太多参数组合）                        │
│  2. 缓存过期时间太短                                           │
│  3. 缓存容量太小导致频繁淘汰                                   │
│  4. 热点数据不均匀（存在热点 key）                              │
│  5. 缓存穿透（大量不存在的数据请求）                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 缓存预热

```java
// 缓存预热实现
@Service
public class CachePreheatService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private ProductMapper productMapper;

    /**
     * 定时预热：每天凌晨 3 点预热热点商品
     */
    @Scheduled(cron = "0 0 3 * * ?")
    public void preheatHotProducts() {
        log.info("开始缓存预热...");

        // 1. 获取热点商品列表（根据历史访问数据）
        List<Long> hotProductIds = getHotProductIds();

        // 2. 批量查询并写入缓存
        for (Long productId : hotProductIds) {
            try {
                ProductVO product = productMapper.selectById(productId);
                if (product != null) {
                    String cacheKey = "product:" + productId;
                    redisTemplate.opsForValue().set(
                        cacheKey,
                        JSON.toJSONString(product),
                        1, TimeUnit.HOURS
                    );
                }
            } catch (Exception e) {
                log.error("缓存预热失败: productId={}", productId, e);
            }
        }

        log.info("缓存预热完成，共预热 {} 个商品", hotProductIds.size());
    }

    /**
     * 主动预热：秒杀活动开始前 5 分钟预热
     */
    @PostConstruct
    public void preheatSeckillProducts() {
        // 从配置中心读取秒杀商品 ID 列表
        List<Long> seckillProductIds = seckillProductConfig.getProductIds();

        for (Long productId : seckillProductIds) {
            // 预热库存
            ProductStock stock = stockMapper.selectByProductId(productId);
            String stockKey = "seckill:stock:" + productId;
            redisTemplate.opsForValue().set(stockKey, String.valueOf(stock.getStock()));
        }
    }

    private List<Long> getHotProductIds() {
        // 从 Redis 获取最近 7 天访问 Top 1000 的商品
        Set<String> topProducts = redisTemplate.opsForZSet()
            .reverseRange("product:access:rank", 0, 999);
        return topProducts.stream()
            .map(Long::parseLong)
            .collect(Collectors.toList());
    }
}
```

### 4.5 缓存问题与应对

```
缓存三大经典问题：

┌─────────────────────────────────────────────────────────────┐
│  1. 缓存穿透                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │   请求 → 缓存(无) → 数据库(无) → 返回空             │   │
│  │                                                     │   │
│  │   问题：恶意请求查询不存在的数据，打穿数据库         │   │
│  │                                                     │   │
│  │   解决方案：                                        │   │
│  │   - 布隆过滤器（推荐）                              │   │
│  │   - 缓存空值（短 TTL）                              │   │
│  │   - 参数校验 + 风控                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  2. 缓存击穿                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │   热点 key 过期瞬间 → 并发请求全部打向数据库         │   │
│  │                                                     │   │
│  │   解决方案：                                        │   │
│  │   - 互斥锁（分布式锁）                              │   │
│  │   - 逻辑过期（不过期，用后台异步更新）               │   │
│  │   - 永不过期（热点数据）                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  3. 缓存雪崩                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │   大量缓存同时过期 → 请求全部打向数据库              │   │
│  │                                                     │   │
│  │   解决方案：                                        │   │
│  │   - 随机过期时间（ TTL + random）                   │   │
│  │   - 持久化（Redis 集群 + 哨兵）                     │   │
│  │   - 多级缓存 + 熔断降级                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 缓存击穿：互斥锁方案
public ProductVO getProductWithLock(Long productId) {
    String cacheKey = "product:" + productId;

    // 1. 先查缓存
    String value = redisTemplate.opsForValue().get(cacheKey);
    if (value != null) {
        return JSON.parseObject(value, ProductVO.class);
    }

    // 2. 获取分布式锁
    String lockKey = "lock:product:" + productId;
    Boolean acquired = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);

    if (Boolean.TRUE.equals(acquired)) {
        try {
            // 双重检查
            value = redisTemplate.opsForValue().get(cacheKey);
            if (value != null) {
                return JSON.parseObject(value, ProductVO.class);
            }

            // 查数据库
            ProductVO product = productMapper.selectById(productId);
            if (product != null) {
                redisTemplate.opsForValue().set(cacheKey,
                    JSON.toJSONString(product),
                    30, TimeUnit.MINUTES);
            } else {
                // 缓存空值，防止穿透
                redisTemplate.opsForValue().set(cacheKey,
                    "NULL", 60, TimeUnit.SECONDS);
            }
            return product;
        } finally {
            redisTemplate.delete(lockKey);
        }
    } else {
        // 没拿到锁，短暂等待后重试
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return getProductWithLock(productId);
    }
}
```

---

## 五、异步化与MQ

### 5.1 异步化的价值

```
同步 vs 异步：

同步调用：
  用户请求 → 服务A → 服务B → 服务C → 返回
  耗时 = T(A) + T(B) + T(C)

异步调用：
  用户请求 → 服务A → 写 MQ → 立即返回
  耗时 = T(A) + T(写MQ)

适用场景：
  - 非核心链路：消息通知、日志记录、数据统计
  - 耗时操作：批量处理、第三方调用
  - 削峰填谷：秒杀下单、优惠券发放

核心价值：
  1. 提升吞吐量：不受下游耗时影响
  2. 削峰填谷：MQ 缓冲洪峰，平滑处理
  3. 解耦微服务：上下游不直接依赖
  4. 最终一致性：允许短暂延迟
```

### 5.2 MQ 削峰实战

```java
// 秒杀场景：MQ 削峰
@Service
public class SeckillService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private RocketMQTemplate mqTemplate;

    /**
     * 秒杀接口：Redis 预减库存 + MQ 异步下单
     */
    public Result<String> seckill(SeckillRequest request) {
        Long skuId = request.getSkuId();
        Long userId = request.getUserId();

        // 1. Lua 脚本原子扣减库存
        String stockKey = "seckill:stock:" + skuId;
        Long remainStock = redisTemplate.execute(
            new DefaultRedisScript<>(
                "local stock = redis.call('GET', KEYS[1]) " +
                "if stock == false or tonumber(stock) < 1 then return -1 end " +
                "redis.call('DECR', KEYS[1]) " +
                "return redis.call('GET', KEYS[1])",
                Long.class
            ),
            List.of(stockKey)
        );

        if (remainStock == null || remainStock < 0) {
            return Result.error("已售罄");
        }

        // 2. 发送 MQ 消息（异步下单）
        SeckillMessage message = new SeckillMessage(skuId, userId);
        mqTemplate.asyncSend("seckill-order-topic", message, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("秒杀消息发送成功: {}", sendResult.getMsgId());
            }

            @Override
            public void onException(Throwable e) {
                // 消息发送失败，回补库存
                log.error("消息发送失败，回补库存: skuId={}", skuId, e);
                redisTemplate.opsForValue().increment(stockKey);
            }
        });

        // 3. 立即返回
        return Result.success("抢购成功，请前往订单页面确认");
    }
}
```

### 5.3 线程池并行化

```java
// CompletableFuture 并行调用多个服务
@Service
public class OrderDetailService {

    @Autowired
    private UserService userService;

    @Autowired
    private ProductService productService;

    @Autowired
    private AddressService addressService;

    public OrderDetailVO getOrderDetail(Long orderId) {
        long startTime = System.currentTimeMillis();

        // 1. 串行调用（总耗时 = A + B + C + D）
        // Order order = orderMapper.selectById(orderId);
        // User user = userService.getUser(order.getUserId());
        // Product product = productService.getProduct(order.getProductId());
        // Address address = addressService.getAddress(order.getAddressId());

        // 2. CompletableFuture 并行调用（总耗时 ≈ max(A, B, C)）
        CompletableFuture<Order> orderFuture = CompletableFuture.supplyAsync(
            () -> orderMapper.selectById(orderId)
        );

        CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(
            () -> userService.getUserByOrderId(orderId)
        );

        CompletableFuture<Product> productFuture = CompletableFuture.supplyAsync(
            () -> productService.getProductByOrderId(orderId)
        );

        CompletableFuture<Address> addressFuture = CompletableFuture.supplyAsync(
            () -> addressService.getAddressByOrderId(orderId)
        );

        // 3. 等待所有结果
        CompletableFuture<Void> allOf = CompletableFuture.allOf(
            orderFuture, userFuture, productFuture, addressFuture
        );

        try {
            allOf.join();  // 阻塞等待
        } catch (Exception e) {
            // 处理异常
            throw new RuntimeException("获取订单详情失败", e);
        }

        // 4. 组装结果
        OrderDetailVO detail = new OrderDetailVO();
        detail.setOrder(orderFuture.get());
        detail.setUser(userFuture.get());
        detail.setProduct(productFuture.get());
        detail.setAddress(addressFuture.get());

        log.info("订单详情查询耗时: {}ms", System.currentTimeMillis() - startTime);
        return detail;
    }
}
```

### 5.4 MQ 消息可靠性

```
MQ 消息可靠性的核心原则：

┌─────────────────────────────────────────────────────────────┐
│                   消息可靠性的三个环节                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 生产可靠（不丢消息）                                       │
│     - 同步发送 + 确认回调                                     │
│     - 事务消息（RocketMQ）                                   │
│     - 消息持久化                                              │
│                                                              │
│  2. 存储可靠（不丢消息）                                       │
│     - 主从复制                                                │
│     - 刷盘策略（同步刷盘）                                    │
│     - 集群部署                                                │
│                                                              │
│  3. 消费可靠（不丢消息）                                       │
│     - 手动 ACK                                               │
│     - 消息幂等                                                │
│     - 失败重试                                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 消费者：手动 ACK + 幂等处理
@Service
@Slf4j
public class OrderConsumer {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @RocketMQMessageListener(
        topic = "seckill-order-topic",
        consumerGroup = "seckill-consumer-group",
        consumeThreadMax = 10
    )
    public void consume(SeckillMessage message, Acknowledgment ack) {
        String dedupKey = "dedup:order:" + message.getSkuId() + ":" + message.getUserId();

        try {
            // 1. 幂等检查
            Boolean success = redisTemplate.opsForValue()
                .setIfAbsent(dedupKey, "1", 1, TimeUnit.HOURS);

            if (!Boolean.TRUE.equals(success)) {
                log.info("消息已处理，跳过: {}", message);
                ack.acknowledge();
                return;
            }

            // 2. 业务处理
            createOrder(message);

            // 3. 手动 ACK
            ack.acknowledge();
            log.info("订单创建成功: {}", message);

        } catch (Exception e) {
            log.error("订单创建失败，不 ACK 会重试: {}", message, e);
            throw e;  // 抛出异常，MQ 会自动重试
        }
    }
}
```

---

## 六、数据库优化

### 6.1 读写分离

```
读写分离架构：

┌─────────────────────────────────────────────────────────────┐
│                      读写分离架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌──────────────┐                         │
│                    │   应用服务    │                         │
│                    └──────┬───────┘                         │
│                           │                                  │
│              ┌────────────┴────────────┐                    │
│              │                         │                     │
│              ▼                         ▼                     │
│      ┌──────────────┐         ┌──────────────┐            │
│      │   写库（主）  │         │   读库（从）  │            │
│      │  Master      │ ◄───────│  Slave       │            │
│      │  QPS: 1000   │  同步   │  QPS: 5000   │            │
│      └──────┬───────┘         └──────────────┘            │
│             │                                             │
│             │  binlog 异步复制                              │
│             └─────────────────────────────────►            │
│                                                              │
│  读写策略：                                                  │
│  - 写操作：强制走主库                                        │
│  - 读操作：强制走从库（或根据一致性要求选择）                   │
│  - 延迟问题：金融类业务强制读主库                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// Spring Boot 读写分离配置
@Configuration
public class DataSourceConfig {

    @Bean
    public DataSource dataSource(
            @Value("${spring.datasource.master.url}") String masterUrl,
            @Value("${spring.datasource.slave.url}") String slaveUrl) {

        Map<Object, Object> targetDataSources = new HashMap<>();

        // 主库
        HikariDataSource masterDs = new HikariDataSource();
        masterDs.setJdbcUrl(masterUrl);
        targetDataSources.put("master", masterDs);

        // 从库
        HikariDataSource slaveDs = new HikariDataSource();
        slaveDs.setJdbcUrl(slaveUrl);
        targetDataSources.put("slave", slaveDs);

        // 路由数据源
        RoutingDataSource routingDs = new RoutingDataSource();
        routingDs.setTargetDataSources(targetDataSources);
        routingDs.setDefaultTargetDataSource(masterDs);

        return routingDs;
    }
}

// 切换数据源
public class RoutingDataSource extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        // 读操作走从库，写操作走主库
        boolean isReadOnly = TransactionSynchronizationManager.isCurrentTransactionReadOnly();
        return isReadOnly ? "slave" : "master";
    }
}

// 使用：在 Service 中控制读写
@Service
public class UserService {

    @Transactional(readOnly = true)  // 走从库
    public User getUserById(Long id) {
        return userMapper.selectById(id);
    }

    @Transactional(readOnly = false)  // 走主库
    public void createUser(User user) {
        userMapper.insert(user);
    }
}
```

### 6.2 分库分表

```
分库分表策略：

┌─────────────────────────────────────────────────────────────┐
│                    分库分表策略                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  垂直分库：按业务模块拆分                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                     │
│  │ 用户库   │ │ 订单库   │ │ 商品库   │                     │
│  └─────────┘ └─────────┘ └─────────┘                     │
│                                                              │
│  垂直分表：按字段冷热拆分                                     │
│  ┌─────────────┬─────────────┐                             │
│  │ user_basic  │ user_detail │                             │
│  │ (id,name)   │ (addr,desc) │  ← 冷数据                    │
│  └─────────────┴─────────────┘                             │
│                                                              │
│  水平分片：按数据量拆分                                       │
│  ┌──────────┬──────────┬──────────┐                       │
│  │ order_0  │ order_1  │ order_2  │                       │
│  │ userId%3 │ userId%3 │ userId%3 │                       │
│  │   = 0    │   = 1    │   = 2    │                       │
│  └──────────┴──────────┴──────────┘                       │
│                                                              │
│  分片键选择原则：                                             │
│  1. 尽量选择查询最频繁的字段                                  │
│  2. 避免跨分片查询                                           │
│  3. 均匀分布（避免热点）                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// ShardingSphere 分片配置
@Configuration
public class ShardingSphereConfig {

    @Bean
    public DataSource dataSource() throws SQLException {
        ShardingSphereDataSourceFactory.createDataSource(
            createDataSourceMap(),
            createRuleConfiguration(),
            createProps()
        );
    }

    private ShardingRuleConfiguration createRuleConfiguration() {
        ShardingRuleConfiguration config = new ShardingRuleConfiguration();

        // 订单表分片：按 user_id 分片到 4 个库，每库 4 张表
        TableRuleConfiguration orderTable = new TableRuleConfiguration("t_order", "ds$->{0..3}.t_order_$->{0..3}");
        orderTable.setDatabaseShardingStrategy(
            new StandardShardingStrategyConfiguration("user_id", "databaseShardingAlgorithm")
        );
        orderTable.setTableShardingStrategy(
            new StandardShardingStrategyConfiguration("user_id", "tableShardingAlgorithm")
        );

        config.getTableRuleConfigs().add(orderTable);
        return config;
    }

    private Map<String, DataSource> createDataSourceMap() {
        // 配置 4 个数据源
        Map<String, DataSource> map = new HashMap<>();
        for (int i = 0; i < 4; i++) {
            map.put("ds" + i, createDataSource(i));
        }
        return map;
    }
}
```

### 6.3 连接池优化

```java
// HikariCP 连接池优化配置
@Configuration
public class HikariCPConfig {

    @Bean
    public DataSource dataSource() {
        HikariConfig config = new HikariConfig();

        // 核心配置
        config.setJdbcUrl("jdbc:mysql://localhost:3306/db");
        config.setUsername("root");
        config.setPassword("password");
        config.setDriverClassName("com.mysql.cj.jdbc.Driver");

        // 连接池大小
        config.setMaximumPoolSize(20);    // 最大连接数
        config.setMinimumIdle(5);         // 最小空闲连接

        // 空闲连接存活时间
        config.setIdleTimeout(300000);     // 5 分钟

        // 连接最大存活时间
        config.setMaxLifetime(1800000);    // 30 分钟

        // 连接超时
        config.setConnectionTimeout(10000); // 10 秒

        // 慢查询日志
        config.setLeakDetectionThreshold(60000); // 60 秒未归还视为泄漏

        // PreparedStatement 缓存
        config.setPreparedStatementCacheSize(250);
        config.addDataSourceProperty("cachePrepStmts", "true");

        return new HikariDataSource(config);
    }
}

// 监控连接池指标
@Bean
public MeterBinder HikariCPMetrics(HikariDataSource dataSource) {
    return registry -> {
        HikariConfigMXBean bean = dataSource.getHikariConfigMXBean();
        Gauge.builder("hikari.connections.active", bean, HikariConfigMXBean::getActiveConnections)
            .register(registry);
        Gauge.builder("hikari.connections.idle", bean, HikariConfigMXBean::getIdleConnections)
            .register(registry);
        Gauge.builder("hikari.connections.waiting", bean, HikariConfigMXBean::getThreadsAwaitingConnection)
            .register(registry);
    };
}
```

---

## 七、水平扩展

### 7.1 无状态设计

```
无状态服务设计原则：

┌─────────────────────────────────────────────────────────────┐
│                   无状态 vs 有状态                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  有状态服务：                                                 │
│    - 用户的 Session 存储在服务器内存                          │
│    - 每次请求必须路由到同一台服务器                           │
│    - 扩缩容麻烦，需要 Session 复制                           │
│                                                              │
│  无状态服务：                                                 │
│    - Session 存储在 Redis / JWT Token                        │
│    - 请求可以路由到任意服务器                                 │
│    - 轻松扩缩容                                              │
│                                                              │
│  无状态化改造要点：                                            │
│  1. 移除本地缓存（用分布式缓存）                              │
│  2. 移除本地 Session（用 Redis）                             │
│  3. 文件存储外置（用 OSS / NAS）                             │
│  4. 定时任务不走集群（用 XXL-Job）                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 无状态服务改造示例
// ❌ 有状态：本地缓存用户信息
@Service
public class OldUserService {
    private Map<Long, User> localCache = new ConcurrentHashMap<>();  // 有状态

    public User getUser(Long userId) {
        return localCache.computeIfAbsent(userId, id -> userMapper.selectById(id));
    }
}

// ✅ 无状态：使用 Redis 分布式缓存
@Service
public class NewUserService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    public User getUser(Long userId) {
        String key = "user:" + userId;
        String value = redisTemplate.opsForValue().get(key);
        if (value != null) {
            return JSON.parseObject(value, User.class);
        }
        User user = userMapper.selectById(userId);
        redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
        return user;
    }
}
```

### 7.2 服务发现

```
服务发现架构：

┌─────────────────────────────────────────────────────────────┐
│                    服务发现架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │  服务A v1   │    │  服务A v2   │    │  服务A v3   │   │
│   │ 192.168.1.1 │    │ 192.168.1.2 │    │ 192.168.1.3 │   │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   │
│          │                  │                  │           │
│          └────────────────┬┴─────────────────┘           │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   注册中心       │                       │
│                  │ (Nacos/Zookeeper│                       │
│                  │   Consul/Eureka)│                       │
│                  └────────┬────────┘                       │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   消费者        │                       │
│                  │  服务发现 + 负载 │                      │
│                  └─────────────────┘                       │
│                                                              │
│  注册中心核心功能：                                           │
│  - 服务注册：心跳检测、自动剔除                               │
│  - 服务发现：动态感知服务变更                                 │
│  - 负载均衡：多种策略（轮询/随机/权重）                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 自动扩缩容

```yaml
# Kubernetes HPA 自动扩缩容配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
  minReplicas: 3           # 最小 3 个 Pod
  maxReplicas: 50          # 最大 50 个 Pod
  metrics:
    # CPU 使用率 > 70% 时扩容
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    # 内存使用率 > 80% 时扩容
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30   # 扩容冷却 30 秒
      policies:
        - type: Percent
          value: 100                   # 每次最多扩容 100%
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300  # 缩容冷却 5 分钟
```

---

## 八、热点数据问题

### 8.1 热点 key 探测

```
热点数据问题：

┌─────────────────────────────────────────────────────────────┐
│                    热点数据问题                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  什么是热点数据？                                             │
│  - 某条数据的访问量远高于其他数据                             │
│  - 例如：秒杀商品、明星结婚官宣、热门新闻                       │
│                                                              │
│  热点数据的危害：                                             │
│  - 单机 Redis 无法承受（热点 key 独享 CPU）                  │
│  - 热点 key 所在节点成为瓶颈                                 │
│  - 可能导致集群雪崩                                          │
│                                                              │
│  热点探测方案：                                               │
│  1. 客户端统计：本地累加 + 定时上报                          │
│  2. 代理层统计：Twemproxy / Codis 统计                      │
│  3. 服务端统计：Redis 4.0+ 的 MONITOR 命令（生产慎用）       │
│  4. 独立探测系统：京东 / 阿里有专门的热点探测服务              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 热点 key 探测实现
@Service
public class HotKeyDetector {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // 本地窗口计数器
    private final Map<String, AtomicLong> localCounter = new ConcurrentHashMap<>();

    // 滑动窗口：统计最近 1 秒的请求数
    public void recordAccess(String key) {
        // 本地计数
        localCounter.computeIfAbsent(key, k -> new AtomicLong(0))
            .incrementAndGet();

        // 定时上报（每 100ms）
        reportHotKeys();
    }

    @Scheduled(fixedRate = 100)
    public void reportHotKeys() {
        if (localCounter.isEmpty()) return;

        Map<String, Long> snapshot = new HashMap<>();
        localCounter.forEach((key, counter) -> {
            long count = counter.getAndSet(0);
            if (count > 0) {
                snapshot.put(key, count);
            }
        });

        if (!snapshot.isEmpty()) {
            // 上报到 Redis 聚合
            String hashKey = "hotkey:counter:" + LocalDateTime.now().format(
                DateTimeFormatter.ofPattern("yyyyMMddHHmmss")
            );
            redisTemplate.opsForHash().putAll(hashKey, snapshot);
            redisTemplate.expire(hashKey, 1, TimeUnit.HOURS);
        }
    }

    // 获取热点 key
    public Set<String> getHotKeys(int topN) {
        Set<String> hotKeys = new HashSet<>();
        // 聚合所有窗口的计数
        // 取 Top N
        return hotKeys;
    }
}
```

### 8.2 热点数据分散

```
热点分散策略：

┌─────────────────────────────────────────────────────────────┐
│                    热点分散方案                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  方案一：热点 key 加后缀分散                                  │
│    原始 key:  seckill:stock:1001                            │
│    分散后:    seckill:stock:1001_0                          │
│                seckill:stock:1001_1                         │
│                seckill:stock:1001_2                         │
│                seckill:stock:1001_3                         │
│                                                              │
│  方案二：本地缓存 + 分布式锁                                  │
│    - 热点数据优先读本地缓存                                   │
│    - 本地缓存miss时加分布式锁只允许一个请求去加载              │
│                                                              │
│  方案三：读写分离                                            │
│    - 热点 key 单独部署到高性能机器                           │
│    - 读写分离，读操作走多个从节点                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// 热点 key 分散实现
@Service
public class HotKeyService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // 热点 key 分片数量
    private static final int HOT_KEY_SHARDS = 4;

    /**
     * 读取：随机分散到不同分片
     */
    public String getHotValue(String key) {
        int shard = ThreadLocalRandom.current().nextInt(HOT_KEY_SHARDS);
        String shardedKey = key + "_" + shard;
        return redisTemplate.opsForValue().get(shardedKey);
    }

    /**
     * 写入：写入所有分片
     */
    public void setHotValue(String key, String value) {
        for (int i = 0; i < HOT_KEY_SHARDS; i++) {
            String shardedKey = key + "_" + i;
            redisTemplate.opsForValue().set(shardedKey, value);
        }
    }

    /**
     * 扣减：原子操作
     */
    public Long decrement(String key) {
        // 遍历所有分片，直到成功扣减
        for (int i = 0; i < HOT_KEY_SHARDS; i++) {
            String shardedKey = key + "_" + i;
            Long result = redisTemplate.opsForValue().decrement(shardedKey);
            if (result != null && result >= 0) {
                return result;
            }
            // 回滚
            redisTemplate.opsForValue().increment(shardedKey);
        }
        return -1L;
    }
}
```

---

## 九、减库存问题

### 9.1 Redis Lua 原子扣减

```lua
-- Lua 脚本：保证库存扣减原子性
-- 防止并发场景下的超卖问题

-- KEYS[1]: 库存 key，如 seckill:stock:1001
-- ARGV[1]: 要扣减的数量，如 1

local stock = redis.call('GET', KEYS[1])

-- 库存不存在
if stock == false then
    return -1
end

stock = tonumber(stock)
local deduct = tonumber(ARGV[1])

-- 库存不足
if stock < deduct then
    return 0
end

-- 扣减库存
stock = stock - deduct
redis.call('SET', KEYS[1], stock)

-- 返回剩余库存
return stock
```

```java
// Java 调用 Lua 扣减库存
@Service
public class StockService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    private static final String DEDUCT_STOCK_LUA =
        "local stock = redis.call('GET', KEYS[1]) " +
        "if stock == false then return -1 end " +
        "stock = tonumber(stock) " +
        "local deduct = tonumber(ARGV[1]) " +
        "if stock < deduct then return 0 end " +
        "stock = stock - deduct " +
        "redis.call('SET', KEYS[1], stock) " +
        "return stock";

    /**
     * 扣减库存
     * @return >0 扣减成功，返回剩余库存；0 库存不足；-1 商品不存在
     */
    public Long deductStock(String key, int count) {
        DefaultRedisScript<Long> script = new DefaultRedisScript<>(DEDUCT_STOCK_LUA, Long.class);
        Long result = stringRedisTemplate.execute(script, List.of(key), String.valueOf(count));
        return result;
    }
}
```

### 9.2 乐观锁兜底

```java
// MySQL 乐观锁兜底
@Service
public class StockDbService {

    @Autowired
    private StockMapper stockMapper;

    /**
     * 乐观锁扣减库存
     * SQL: UPDATE stock SET stock = stock - #{count}, version = version + 1
     *      WHERE sku_id = #{skuId} AND stock >= #{count} AND version = #{version}
     */
    public boolean deductStockWithOptimisticLock(Long skuId, int count) {
        // 1. 查询当前库存
        Stock stock = stockMapper.selectBySkuId(skuId);
        if (stock == null || stock.getStock() < count) {
            return false;
        }

        // 2. 乐观锁更新
        int affected = stockMapper.deductWithVersion(skuId, count, stock.getVersion());

        if (affected == 0) {
            // 乐观锁冲突，重试
            log.warn("库存扣减冲突，重试: skuId={}", skuId);
            return deductStockWithOptimisticLock(skuId, count);
        }

        return true;
    }
}
```

```xml
<!-- StockMapper.xml -->
<update id="deductWithVersion">
    UPDATE stock
    SET stock = stock - #{count},
        version = version + 1,
        updated_at = NOW()
    WHERE sku_id = #{skuId}
      AND stock >= #{count}
      AND version = #{version}
</update>
```

---

## 十、压测与监控

### 10.1 本地压测工具

```
压测工具对比：

┌─────────────────────────────────────────────────────────────┐
│                    压测工具对比                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  JMeter                                                     │
│  - 优点：功能强大，图形界面，支持复杂场景                      │
│  - 缺点：重量级，资源消耗大                                   │
│  - 适用：完整链路压测、复杂业务场景                           │
│                                                              │
│  wrk / wrk2                                                 │
│  - 优点：轻量级，高性能，C 语言实现                          │
│  - 缺点：功能单一，不支持复杂场景                             │
│  - 适用：接口性能基准测试                                     │
│                                                              │
│  ab (Apache Bench)                                          │
│  - 优点：简单易用，Apache 项目自带                           │
│  - 缺点：功能有限，不支持持续压测                             │
│  - 适用：快速单接口压测                                       │
│                                                              │
│  vegeta                                                     │
│  - 优点：Go 语言，可编程，输出丰富                           │
│  - 缺点：学习曲线较陡                                         │
│  - 适用：Gopher 的选择                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# wrk 压测示例
# 200 个并发，持续压测 30 秒
wrk -t4 -c200 -d30s --latency http://localhost:8080/api/products

# 结果分析：
# Running 30s test @ http://localhost:8080/api/products
#   4 threads and 200 connections
#   Thread Stats   Avg      Stdev     Max   +/-Stdev
#     Latency    45.32ms   12.45ms 198.00ms   87.00%
#     Req/Sec     4.52k   234.89    5.12k   70.00%
#   Latency Distribution
#      50%   44.00ms
#      75%   52.00ms
#      90%   60.00ms
#      99%   98.00ms
#   135623 requests in 30.01s, 45.23MB read
#   Socket errors: connect 0, read 0, write 0, timeout 5
#   Non-2xx or 3xx responses: 12
# Requests/sec:   4518.23
# Transfer/sec:      1.51MB
```

```java
// JMeter Java Request 实现自定义压测
public class SeckillSampler implements JavaSamplerClient {

    @Override
    public SampleResult runTest(JavaSamplerContext context) {
        SampleResult result = new SampleResult();
        result.sampleStart();

        try {
            // 执行秒杀请求
            HttpResponse response = HttpUtil.post(
                "http://localhost:8080/api/seckill/do",
                JsonUtil.toJson(new SeckillRequest(skuId, userId))
            );

            result.setResponseCode(response.getStatusCode() + "");
            result.setResponseData(response.getBody(), "utf-8");

            if (response.getStatusCode() == 200) {
                result.setSuccessful(true);
            } else {
                result.setSuccessful(false);
            }
        } catch (Exception e) {
            result.setSuccessful(false);
            result.setResponseMessage(e.getMessage());
        } finally {
            result.sampleEnd();
        }

        return result;
    }
}
```

### 10.2 监控告警体系

```
监控四大黄金指标：

┌─────────────────────────────────────────────────────────────┐
│                   监控四大黄金指标                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 延迟 (Latency)                                           │
│     - 接口响应时间分布                                        │
│     - p50/p95/p99/p999                                      │
│     - 告警：p99 > 2s                                         │
│                                                              │
│  2. 流量 (Traffic)                                           │
│     - QPS / TPS                                              │
│     - 并发连接数                                             │
│     - 告警：QPS 突增 50%                                     │
│                                                              │
│  3. 错误 (Errors)                                            │
│     - 5xx 错误率                                             │
│     - 超时率                                                  │
│     - 告警：错误率 > 1%                                       │
│                                                              │
│  4. 饱和度 (Saturation)                                      │
│     - CPU / 内存利用率                                       │
│     - 磁盘 IO / 网络 IO                                      │
│     - 线程池队列满                                            │
│     - 告警：CPU > 80%                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```java
// Prometheus + Micrometer 监控指标
@Service
public class MetricsService {

    private final MeterRegistry registry;

    // 计数器：QPS
    private final Counter requestCounter = Counter.builder("http.requests.total")
        .tag("uri", "/api/products")
        .register(registry);

    // 计时器：延迟分布
    private final Timer requestTimer = Timer.builder("http.requests.latency")
        .tag("uri", "/api/products")
        .register(registry);

    // 仪表盘：当前并发
    private final Gauge concurrentRequests = Gauge.builder("http.requests.concurrent")
        .register(registry);

    // Histogram：响应时间分布
    private final DistributionSummary responseSize = DistributionSummary.builder("http.response.size")
        .register(registry);

    public void recordRequest(HttpServletRequest request, long duration) {
        // 记录 QPS
        requestCounter.increment();

        // 记录延迟
        requestTimer.record(duration, TimeUnit.MILLISECONDS);

        // 记录响应大小
        responseSize.record(response.getContentLength());
    }
}
```

```yaml
# Prometheus 告警规则
groups:
  - name: high-concurrency-alerts
    rules:
      # 高延迟告警
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_requests_latency_seconds_bucket[5m])) > 2
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High latency detected"
          description: "p99 latency is {{ $value }}s"

      # 高错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "5xx error rate is {{ $value }}%"

      # CPU 告警
      - alert: HighCPU
        expr: rate(process_cpu_seconds_total[1m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
```

---

## 十一、高频面试题

**Q1: 高并发系统的核心设计思想是什么？**
> 高并发系统的核心是**分层防护、层层过滤**。把流量挡在离用户最近的那一层，数据库只承受 1% 的压力。具体手段：CDN 扛静态资源、Nginx 限流、网关层熔断降级、应用层多级缓存、数据库读写分离 + 分库分表。每一层都有明确的目标：CDN 扛 60% 静态请求、Nginx 再扛 20% 恶意请求、应用层缓存扛 15% 热点读、数据库只承受 5% 的写。

**Q2: 如何衡量一个系统的并发能力？**
> 核心指标有四个：① **QPS**：每秒请求数，衡量吞吐；② **响应时间分布**：p50/p95/p99/p999，关注长尾延迟；③ **并发数**：同时处理的请求数，与 QPS 和响应时间相关；④ **错误率**：5xx 占比、超时率。计算公式：并发数 = QPS × 平均响应时间。最佳线程数 = CPU 核心数 × 期望利用率 × (1 + 等待时间/处理时间)。

**Q3: 限流算法有哪些？令牌桶和漏桶的区别是什么？**
> 限流算法有计数器、滑动窗口、令牌桶、漏桶四种。**令牌桶**允许一定程度的突发流量（桶内有令牌），适合保护自己的接口；**漏桶**以固定速率漏出，不允许突发，适合保护下游 MQ/数据库。简单记：令牌桶 = 配额消费，漏桶 = 队列排队。

**Q4: 缓存穿透、击穿、雪崩的区别是什么？**
> 三个问题的区别：① **缓存穿透**：查询不存在的数据，直接打穿到数据库，解决方案是布隆过滤器 + 缓存空值；② **缓存击穿**：热点 key 过期瞬间，大量并发同时打穿到数据库，解决方案是互斥锁 + 逻辑过期；③ **缓存雪崩**：大量缓存同时过期，解决方案是随机 TTL + 持久化 + 多级缓存。

**Q5: 如何保证 Redis 和数据库的数据一致性？**
> 没有完美的方案，只有权衡：① **旁路缓存**：更新数据库后删除缓存，适合读多写少场景；② **双写**：更新数据库后同时写缓存，适合一致性要求高的场景，但有并发问题；③ **延迟双删**：更新数据库后删缓存，延迟 500ms 再删一次，应对并发读旧值。无论哪种方案都无法 100% 保证一致，只能降低不一致的时间窗口。

**Q6: MQ 消息可靠性如何保证？**
> 消息可靠性需要保证三个环节：① **生产端**：同步发送 + SendCallback 确认，RocketMQ 可用事务消息；② **存储端**：主从复制 + 同步刷盘；③ **消费端**：手动 ACK + 消息幂等（用 Redis 做去重）。任何环节出问题都可能丢消息，生产环境必须全链路保障。

**Q7: 如何设计一个抗住 100 万 QPS 的系统？**
> 这是一个综合题，考察全链路能力。回答思路：① **CDN + 就近接入**：扛静态资源和第一波流量；② **Nginx 限流**：令牌桶，限制到 10 万 QPS；③ **网关层**：熔断降级 + 鉴权 + 风控；④ **应用层**：多级缓存（本地 + Redis），热点数据预热，限流 + 隔离；⑤ **MQ 削峰**：异步处理非核心链路；⑥ **数据库**：读写分离 + 分库分表 + 乐观锁；⑦ **弹性扩缩容**：K8s HPA 自动扩容；⑧ **监控告警**：全链路监控 + 异常告警。

---

**参考链接：**
- [秒杀系统设计详解](https://tech.meituan.com/2019/11/28/meituan-seckill.html)
- [高并发系统设计 40 问](https://juejin.cn/book/6844733800300150280)
- [Sentinel 官方文档](https://sentinelguard.io/zh-cn/)
