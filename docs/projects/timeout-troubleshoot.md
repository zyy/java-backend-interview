# 接口超时排查实战

> 从超时到优化：接口性能问题全链路排查指南

## 🎯 面试重点

- 超时问题分类与根因分析
- 全链路调用追踪技术
- 数据库与中间件性能分析
- 超时预防与优化策略

## 📖 超时问题分类

### 1. 超时现象定义

```java
/**
 * 超时问题类型
 */
public class TimeoutProblemType {
    
    // 1. 连接超时（Connection Timeout）
    /*
     * 现象：TCP连接建立失败
     * 默认值：通常10-30秒
     * 原因：网络不通、服务宕机、防火墙限制
     */
    
    // 2. 读取超时（Read Timeout）
    /*
     * 现象：连接已建立，但等待响应超时
     * 默认值：通常30-60秒
     * 原因：服务处理慢、网络延迟、数据量大
     */
    
    // 3. 写入超时（Write Timeout）
    /*
     * 现象：发送请求数据超时
     * 默认值：通常30秒
     * 原因：网络拥堵、接收方处理慢
     */
    
    // 4. 全局超时（Global Timeout）
    /*
     * 现象：整个操作超时
     * 实现：业务层面设置的超时时间
     * 原因：复杂业务流程耗时过长
     */
    
    // 5. 链式超时（Cascading Timeout）
    /*
     * 现象：A服务超时导致B服务超时，连锁反应
     * 原因：服务依赖过深，超时传播
     */
}
```

### 2. 超时影响范围

```java
/**
 * 超时影响级别
 */
public class TimeoutImpactLevel {
    
    // 1. 用户影响
    public class UserImpact {
        /*
         * 直接体验：页面加载慢，操作无响应
         * 用户流失：等待时间超过8秒，70%用户离开
         * 信任损失：频繁超时降低用户信任
         */
    }
    
    // 2. 系统影响
    public class SystemImpact {
        /*
         * 资源占用：超时请求不释放连接，占用线程
         * 雪崩效应：单个服务超时引发连锁反应
         * 数据不一致：超时后重试可能导致重复操作
         */
    }
    
    // 3. 业务影响
    public class BusinessImpact {
        /*
         * 交易失败：支付、下单等关键业务失败
         * 数据丢失：超时后数据未持久化
         * 资损风险：超时重试可能导致重复扣款
         */
    }
}
```

## 📖 排查工具链

### 1. 网络层排查工具

```bash
# 1. ping - 网络连通性测试
ping api.example.com
# 关注：丢包率、延迟时间

# 2. traceroute - 路由跟踪
traceroute api.example.com
# 或使用mtr（更强大）
mtr -r -c 10 api.example.com
# 发现网络瓶颈节点

# 3. tcpping - TCP端口连通性
# 需要安装tcpping
tcpping -p 8080 api.example.com
# 测试TCP连接建立时间

# 4. curl - HTTP请求测试
curl -o /dev/null -s -w "\
时间统计:\n\
---------------\n\
DNS解析: %{time_namelookup}s\n\
TCP连接: %{time_connect}s\n\
TLS握手: %{time_appconnect}s\n\
发送请求: %{time_pretransfer}s\n\
服务器处理: %{time_starttransfer}s\n\
总时间: %{time_total}s\n\
" https://api.example.com/v1/users

# 5. netstat - 网络连接状态
netstat -an | grep TIME_WAIT | wc -l  # TIME_WAIT连接数
netstat -an | grep ESTABLISHED | wc -l  # 活跃连接数

# 6. tcpdump - 网络抓包
tcpdump -i eth0 host api.example.com and port 8080 -w capture.pcap
# 使用Wireshark分析抓包文件
```

### 2. 系统层排查工具

```bash
# 1. top - 系统资源监控
top -c
# 关注：CPU使用率、负载、内存使用

# 2. vmstat - 系统性能统计
vmstat 1 10
# 关注：r（等待运行的进程数）、wa（IO等待）、cs（上下文切换）

# 3. iostat - 磁盘IO统计
iostat -x 1 10
# 关注：%util（设备使用率）、await（平均等待时间）

# 4. sar - 系统活动报告
sar -u 1 10      # CPU使用率
sar -q 1 10      # 系统负载
sar -b 1 10      # IO统计
sar -n DEV 1 10  # 网络统计

# 5. ss - Socket统计
ss -tnlp         # 查看所有TCP连接
ss -s            # Socket统计摘要
```

### 3. 应用层排查工具

```bash
# 1. APM工具（SkyWalking、Pinpoint、Zipkin）
# 全链路追踪，定位慢方法

# 2. Java诊断工具（Arthas）
# 安装：java -jar arthas-boot.jar
dashboard       # 实时仪表板
trace           # 方法调用追踪
watch           # 方法参数/返回值监控
profiler        # 生成火焰图

# 3. JVM工具
jstack <pid> > thread_dump.txt  # 线程堆栈分析
jstat -gc <pid> 1000 10         # GC监控
jmap -heap <pid>                # 堆内存分析

# 4. 日志分析
# 查看应用日志，定位错误
grep -n "TimeoutException\|Read timed out\|Connection timed out" app.log
# 查看慢查询日志
grep "Query took" app.log | sort -k5 -nr | head -20
```

### 4. 数据库层排查工具

```sql
-- 1. 查看当前连接
SHOW PROCESSLIST;
-- 关注：State列（Sending data、Copying to tmp table等）
-- Time列（执行时间）

-- 2. 查看锁信息
SHOW ENGINE INNODB STATUS\G;
-- 在输出中查找 "LATEST DETECTED DEADLOCK" 和 "TRANSACTIONS"

-- 3. 查看慢查询
-- 先确认慢查询日志是否开启
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 查看慢查询日志
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 4. 查看表状态
SHOW TABLE STATUS LIKE 'orders';
-- 关注：Data_length、Index_length、Rows

-- 5. 分析SQL执行计划
EXPLAIN SELECT * FROM orders WHERE user_id = 1001;
-- 或使用更详细的格式
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE user_id = 1001;

-- 6. 性能监控
-- 使用performance_schema
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;
```

## 📖 常见超时场景

### 场景1：数据库查询超时

```sql
-- 问题现象：接口响应慢，数据库查询超时

-- 1. 查看慢查询日志
-- 发现以下慢查询：
# Query_time: 12.345678  Lock_time: 0.000123 Rows_sent: 10  Rows_examined: 1000000
SELECT * FROM orders 
WHERE user_id = 1001 
  AND status = 'PAID'
  AND created_at BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY created_at DESC;

-- 2. 分析执行计划
EXPLAIN SELECT * FROM orders WHERE ...;
-- 输出：type=ALL，表示全表扫描，扫描100万行

-- 3. 问题分析：
-- 缺少合适索引，导致全表扫描
-- 查询条件包含范围查询，索引使用受限

-- 4. 解决方案：
-- 方案1：添加复合索引
ALTER TABLE orders ADD INDEX idx_user_status_time (user_id, status, created_at);

-- 方案2：优化查询条件
-- 如果只需要最近数据，缩小时间范围
SELECT * FROM orders 
WHERE user_id = 1001 
  AND status = 'PAID'
  AND created_at >= '2023-10-01'  -- 只查最近3个月
ORDER BY created_at DESC;

-- 方案3：分页查询优化
-- 使用覆盖索引 + 子查询
SELECT * FROM orders 
WHERE id >= (
    SELECT id FROM orders 
    WHERE user_id = 1001 AND status = 'PAID'
    ORDER BY created_at DESC 
    LIMIT 1000000, 1
)
ORDER BY id LIMIT 20;
```

### 场景2：外部API调用超时

```java
/**
 * 外部API调用超时问题
 */
public class ExternalAPITimeout {
    
    // ❌ 错误示例：默认超时时间过长
    public User getUserFromExternal(Long userId) {
        RestTemplate restTemplate = new RestTemplate();
        // 默认超时时间：无限等待！
        String url = "https://external-api.com/users/" + userId;
        return restTemplate.getForObject(url, User.class);
    }
    
    // ❌ 错误示例：未设置合理的超时时间
    public User getUserWithTimeout() {
        RestTemplate restTemplate = new RestTemplate();
        
        // 设置连接超时和读取超时
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);    // 5秒连接超时
        factory.setReadTimeout(30000);      // 30秒读取超时（太长！）
        
        restTemplate.setRequestFactory(factory);
        
        String url = "https://external-api.com/users/123";
        return restTemplate.getForObject(url, User.class);
    }
    
    // ✅ 解决方案1：合理设置超时时间
    public User getUserWithProperTimeout() {
        RestTemplate restTemplate = new RestTemplate();
        
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(3000);    // 3秒连接超时
        factory.setReadTimeout(5000);       // 5秒读取超时
        
        restTemplate.setRequestFactory(factory);
        
        String url = "https://external-api.com/users/123";
        try {
            return restTemplate.getForObject(url, User.class);
        } catch (ResourceAccessException e) {
            // 超时异常处理
            log.error("调用外部API超时", e);
            return getFallbackUser();  // 降级策略
        }
    }
    
    // ✅ 解决方案2：使用断路器模式（Hystrix/Resilience4j）
    @CircuitBreaker(name = "externalApi", fallbackMethod = "fallbackUser")
    public User getUserWithCircuitBreaker(Long userId) {
        String url = "https://external-api.com/users/" + userId;
        return restTemplate.getForObject(url, User.class);
    }
    
    public User fallbackUser(Long userId, Throwable t) {
        log.error("调用外部API失败，使用降级数据", t);
        return new User(userId, "默认用户");
    }
    
    // ✅ 解决方案3：异步调用 + 超时控制
    public CompletableFuture<User> getUserAsync(Long userId) {
        return CompletableFuture.supplyAsync(() -> {
            String url = "https://external-api.com/users/" + userId;
            return restTemplate.getForObject(url, User.class);
        }).orTimeout(5, TimeUnit.SECONDS)  // 5秒超时
          .exceptionally(ex -> {
              log.error("获取用户信息超时", ex);
              return getFallbackUser();
          });
    }
}
```

### 场景3：线程池耗尽超时

```java
/**
 * 线程池配置不当导致的超时
 */
public class ThreadPoolTimeout {
    
    // ❌ 错误示例：线程池配置不当
    @Configuration
    public class ThreadPoolConfig {
        @Bean
        public ExecutorService taskExecutor() {
            // 线程池太小，队列无限大
            return new ThreadPoolExecutor(
                5,      // 核心线程数（太小）
                10,     // 最大线程数（太小）
                60L, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(),  // 无界队列（危险！）
                new ThreadPoolExecutor.AbortPolicy()  // 拒绝策略：直接抛出异常
            );
        }
    }
    
    @Service
    public class OrderService {
        @Autowired
        private ExecutorService executor;
        
        public void processBatchOrders(List<Order> orders) {
            List<Future> futures = new ArrayList<>();
            for (Order order : orders) {
                // 提交任务到线程池
                futures.add(executor.submit(() -> processOrder(order)));
            }
            
            // 等待所有任务完成
            for (Future future : futures) {
                try {
                    future.get(10, TimeUnit.SECONDS);  // 10秒超时
                } catch (TimeoutException e) {
                    // 任务执行超时
                    log.error("订单处理超时", e);
                }
            }
        }
        
        private void processOrder(Order order) {
            // 复杂处理逻辑，可能耗时
            Thread.sleep(5000);  // 模拟耗时操作
        }
    }
    
    // 问题分析：
    // 1. 线程池核心线程数太小
    // 2. 使用无界队列，任务积压
    // 3. 大量任务等待，最终超时
    
    // ✅ 解决方案：合理配置线程池
    @Bean
    public ExecutorService fixedThreadPool() {
        int corePoolSize = Runtime.getRuntime().availableProcessors() * 2;
        int maxPoolSize = corePoolSize * 2;
        
        return new ThreadPoolExecutor(
            corePoolSize,
            maxPoolSize,
            60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),  // 有界队列
            new NamedThreadFactory("order-processor"),
            new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略：调用者运行
        );
    }
    
    // ✅ 解决方案：使用CompletableFuture超时控制
    public void processOrdersWithTimeout(List<Order> orders) {
        List<CompletableFuture<Void>> futures = orders.stream()
            .map(order -> CompletableFuture.runAsync(() -> processOrder(order), executor)
                .orTimeout(3, TimeUnit.SECONDS)  // 每个任务3秒超时
                .exceptionally(ex -> {
                    log.error("处理订单失败: " + order.getId(), ex);
                    return null;
                })
            )
            .collect(Collectors.toList());
        
        // 等待所有任务完成（带超时）
        try {
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                .get(30, TimeUnit.SECONDS);  // 整体30秒超时
        } catch (TimeoutException e) {
            log.error("批量处理订单超时", e);
            // 取消未完成的任务
            futures.forEach(future -> future.cancel(true));
        }
    }
}
```

### 场景4：锁竞争超时

```java
/**
 * 锁竞争导致的超时
 */
public class LockContentionTimeout {
    
    // ❌ 错误示例：全局锁竞争
    public class InventoryService {
        private static final Object globalLock = new Object();
        
        public boolean deductInventory(Long productId, Integer quantity) {
            synchronized (globalLock) {  // 全局锁，所有商品竞争同一把锁
                // 检查库存
                Inventory inventory = inventoryDao.get(productId);
                if (inventory.getStock() < quantity) {
                    return false;
                }
                
                // 扣减库存（耗时操作）
                inventory.setStock(inventory.getStock() - quantity);
                inventoryDao.update(inventory);
                
                // 记录日志等操作
                logService.logDeduction(productId, quantity);
                
                return true;
            }
        }
    }
    
    // 问题：高并发时大量线程等待全局锁，导致超时
    
    // ✅ 解决方案1：减小锁粒度（按商品ID加锁）
    public class InventoryServiceOptimized {
        private final Map<Long, Object> productLocks = new ConcurrentHashMap<>();
        
        public boolean deductInventory(Long productId, Integer quantity) {
            // 获取商品级别的锁
            Object lock = productLocks.computeIfAbsent(productId, k -> new Object());
            
            synchronized (lock) {
                // 库存检查与扣减
                return doDeductInventory(productId, quantity);
            }
        }
    }
    
    // ✅ 解决方案2：使用数据库乐观锁
    public class InventoryServiceOptimistic {
        public boolean deductInventoryWithVersion(Long productId, Integer quantity) {
            // 使用版本号控制并发
            int retryCount = 0;
            while (retryCount < 3) {  // 重试3次
                Inventory inventory = inventoryDao.get(productId);
                
                if (inventory.getStock() < quantity) {
                    return false;
                }
                
                // 使用版本号更新
                int rows = inventoryDao.updateWithVersion(
                    productId, 
                    inventory.getStock() - quantity,
                    inventory.getVersion()
                );
                
                if (rows > 0) {
                    return true;  // 更新成功
                }
                
                retryCount++;
                try {
                    Thread.sleep(50);  // 短暂等待后重试
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
            
            return false;  // 重试多次后失败
        }
    }
    
    // ✅ 解决方案3：使用分布式锁（Redis）设置超时
    public class InventoryServiceDistributed {
        private static final String LOCK_PREFIX = "inventory:lock:";
        
        public boolean deductInventoryWithRedisLock(Long productId, Integer quantity) {
            String lockKey = LOCK_PREFIX + productId;
            String requestId = UUID.randomUUID().toString();
            
            try {
                // 尝试获取锁，设置5秒超时
                boolean locked = redisTemplate.opsForValue()
                    .setIfAbsent(lockKey, requestId, 5, TimeUnit.SECONDS);
                
                if (!locked) {
                    // 获取锁失败，可能被其他线程持有
                    log.warn("获取库存锁失败，productId: {}", productId);
                    return false;
                }
                
                // 执行库存扣减
                return doDeductInventory(productId, quantity);
                
            } finally {
                // 释放锁（使用Lua脚本保证原子性）
                String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                               "return redis.call('del', KEYS[1]) " +
                               "else return 0 end";
                
                redisTemplate.execute(
                    new DefaultRedisScript<>(script, Long.class),
                    Collections.singletonList(lockKey),
                    requestId
                );
            }
        }
    }
}
```

## 📖 全链路追踪

### 1. 分布式追踪原理

```java
/**
 * 分布式追踪核心概念
 */
public class DistributedTracing {
    
    // Trace：一次完整的请求链路
    /*
     * 包含多个Span
     * 有唯一的Trace ID
     * 跨越多个服务
     */
    
    // Span：单个操作单元
    /*
     * 包含：开始时间、结束时间、操作名称
     * 可以嵌套（父子关系）
     * 携带标签（Tags）和日志（Logs）
     */
    
    // 追踪上下文传播
    /*
     * Trace ID和Span ID需要在服务间传递
     * 通常通过HTTP Header传递
     * 如：X-B3-TraceId、X-B3-SpanId
     */
    
    // 采样率（Sampling）
    /*
     * 生产环境通常不追踪所有请求
     * 通过采样率控制追踪数据量
     * 如：10%的请求被追踪
     */
}
```

### 2. SkyWalking实战配置

```yaml
# application.yml
spring:
  application:
    name: order-service
  
  # SkyWalking配置
  cloud:
    skywalking:
      enabled: true
      # 采集器地址
      collector:
        backend-service: ${SW_AGENT_COLLECTOR_BACKEND_SERVICES:127.0.0.1:11800}
      # 代理配置
      agent:
        service_name: ${SW_AGENT_NAME:order-service}
        # 采样率（0.0-1.0）
        sample_n_per_3_secs: ${SW_AGENT_SAMPLE:1}
        # 忽略特定路径
        ignore_suffix: ${SW_AGENT_IGNORE_SUFFIX:.jpg,.jpeg,.png,.gif,.css,.js}
        # 日志收集
        log:
          grpc:
            reporter:
              enabled: ${SW_LOGGING_GRPC_REPORTER_ENABLED:true}

# 日志MDC配置（关联Trace ID）
logging:
  pattern:
    level: "%5p [${spring.application.name:},%X{traceId:-},%X{spanId:-}]"
```

### 3. 自定义追踪

```java
/**
 * 自定义业务追踪
 */
@Aspect
@Component
@Slf4j
public class BusinessTraceAspect {
    
    @Around("@annotation(businessTrace)")
    public Object traceBusinessMethod(ProceedingJoinPoint joinPoint, 
                                      BusinessTrace businessTrace) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        String businessKey = businessTrace.value();
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 执行原方法
            Object result = joinPoint.proceed();
            
            long costTime = System.currentTimeMillis() - startTime;
            
            // 记录成功追踪
            log.info("业务追踪成功 - {}: {}, 耗时: {}ms", 
                     businessKey, methodName, costTime);
            
            // 如果耗时超过阈值，记录警告
            if (costTime > businessTrace.timeoutThreshold()) {
                log.warn("业务方法执行超时 - {}: {}, 耗时: {}ms (阈值: {}ms)",
                         businessKey, methodName, costTime, businessTrace.timeoutThreshold());
                
                // 发送告警
                alertService.sendTimeoutAlert(businessKey, methodName, costTime);
            }
            
            return result;
            
        } catch (Exception e) {
            long costTime = System.currentTimeMillis() - startTime;
            
            // 记录失败追踪
            log.error("业务追踪失败 - {}: {}, 耗时: {}ms, 异常: {}", 
                      businessKey, methodName, costTime, e.getMessage(), e);
            
            throw e;
        }
    }
}

// 自定义注解
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface BusinessTrace {
    String value();  // 业务标识
    long timeoutThreshold() default 1000;  // 超时阈值（ms）
}

// 使用示例
@Service
public class OrderService {
    
    @BusinessTrace(value = "创建订单", timeoutThreshold = 3000)
    public Order createOrder(OrderRequest request) {
        // 业务逻辑
        return order;
    }
}
```

## 📖 超时优化策略

### 1. 超时配置最佳实践

```yaml
# 超时配置示例
timeout:
  # HTTP客户端超时
  http:
    connect: 3000    # 连接超时3秒
    read: 10000      # 读取超时10秒
    write: 5000      # 写入超时5秒
    
  # 数据库超时
  database:
    connect: 5000           # 连接超时5秒
    socket: 30000           # Socket超时30秒
    transaction: 60000      # 事务超时60秒
    
  # Redis超时
  redis:
    connect: 2000           # 连接超时2秒
    socket: 5000            # Socket超时5秒
    command: 3000           # 命令执行超时3秒
    
  # 消息队列超时
  mq:
    send: 5000              # 发送消息超时5秒
    receive: 10000          # 接收消息超时10秒
    
  # 业务超时
  business:
    create_order: 5000      # 创建订单5秒
    process_payment: 10000  # 处理支付10秒
    generate_report: 30000  # 生成报告30秒
```

### 2. 降级与熔断策略

```java
/**
 * 降级熔断配置
 */
@Configuration
public class ResilienceConfig {
    
    @Bean
    public CircuitBreakerConfig circuitBreakerConfig() {
        return CircuitBreakerConfig.custom()
            .failureRateThreshold(50)          // 失败率阈值50%
            .slowCallRateThreshold(50)         // 慢调用率阈值50%
            .slowCallDurationThreshold(Duration.ofSeconds(2))  // 慢调用阈值2秒
            .waitDurationInOpenState(Duration.ofSeconds(60))   // 开启状态等待60秒
            .permittedNumberOfCallsInHalfOpenState(10)         // 半开状态允许10个调用
            .minimumNumberOfCalls(100)         // 最小调用数100
            .slidingWindowType(SlidingWindowType.COUNT_BASED)  // 基于计数的滑动窗口
            .slidingWindowSize(100)            // 滑动窗口大小100
            .recordExceptions(TimeoutException.class, IOException.class)  // 记录哪些异常
            .build();
    }
    
    @Bean
    public TimeLimiterConfig timeLimiterConfig() {
        return TimeLimiterConfig.custom()
            .timeoutDuration(Duration.ofSeconds(5))  // 超时时间5秒
            .cancelRunningFuture(true)               // 取消正在执行的Future
            .build();
    }
    
    @Bean
    public BulkheadConfig bulkheadConfig() {
        return BulkheadConfig.custom()
            .maxConcurrentCalls(10)           // 最大并发调用10
            .maxWaitDuration(Duration.ofMillis(500))  // 最大等待时间500ms
            .build();
    }
}

// 使用示例
@Service
public class ExternalService {
    
    @CircuitBreaker(name = "externalApi", fallbackMethod = "fallback")
    @TimeLimiter(name = "externalApi")
    @Bulkhead(name = "externalApi")
    public CompletableFuture<String> callExternalApi() {
        return CompletableFuture.supplyAsync(() -> {
            // 调用外部API
            return restTemplate.getForObject("https://api.example.com", String.class);
        });
    }
    
    public CompletableFuture<String> fallback(Throwable t) {
        return CompletableFuture.completedFuture("Fallback response");
    }
}
```

### 3. 异步化改造

```java
/**
 * 同步接口异步化改造
 */
public class AsyncTransformation {
    
    // 改造前：同步阻塞接口
    @GetMapping("/orders/{id}")
    public OrderDTO getOrderDetail(@PathVariable Long id) {
        // 同步调用，可能阻塞
        Order order = orderService.getOrder(id);           // 数据库查询
        User user = userService.getUser(order.getUserId()); // 用户服务调用
        List<Product> products = productService.getProductsByOrder(id); // 产品服务调用
        
        return assemble(order, user, products);  // 组装DTO
    }
    
    // 问题：串行调用，总耗时 = t1 + t2 + t3
    
    // 改造后：异步并行
    @GetMapping("/orders/{id}/async")
    public CompletableFuture<OrderDTO> getOrderDetailAsync(@PathVariable Long id) {
        // 并行调用
        CompletableFuture<Order> orderFuture = 
            CompletableFuture.supplyAsync(() -> orderService.getOrder(id), executor);
        
        CompletableFuture<User> userFuture = orderFuture.thenCompose(order ->
            CompletableFuture.supplyAsync(() -> userService.getUser(order.getUserId()), executor)
        );
        
        CompletableFuture<List<Product>> productsFuture = 
            CompletableFuture.supplyAsync(() -> productService.getProductsByOrder(id), executor);
        
        // 合并结果
        return CompletableFuture.allOf(orderFuture, userFuture, productsFuture)
            .thenApply(v -> {
                try {
                    Order order = orderFuture.get();
                    User user = userFuture.get();
                    List<Product> products = productsFuture.get();
                    return assemble(order, user, products);
                } catch (Exception e) {
                    throw new CompletionException(e);
                }
            })
            .orTimeout(3000, TimeUnit.MILLISECONDS)  // 总体超时3秒
            .exceptionally(ex -> {
                log.error("获取订单详情失败", ex);
                return getFallbackOrderDetail(id);
            });
    }
    
    // 进一步优化：使用事件驱动
    public class OrderQueryHandler {
        
        @EventListener
        @Async
        public CompletableFuture<OrderDetailEvent> handleOrderQuery(OrderQueryEvent event) {
            // 异步处理查询
            return CompletableFuture.supplyAsync(() -> {
                OrderDetail detail = queryOrderDetail(event.getOrderId());
                return new OrderDetailEvent(detail);
            });
        }
        
        private OrderDetail queryOrderDetail(Long orderId) {
            // 并行查询
            // ...
            return detail;
        }
    }
}
```

## 📖 监控与告警

### 1. 超时监控指标

```yaml
# Prometheus监控配置
monitoring:
  timeout:
    # 接口响应时间
    - name: api_response_time
      query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
      threshold: 3.0  # P95响应时间超过3秒告警
    
    # 超时率
    - name: api_timeout_rate
      query: rate(http_request_timeouts_total[5m]) / rate(http_requests_total[5m]) * 100
      threshold: 5.0  # 超时率超过5%告警
    
    # 数据库查询时间
    - name: db_query_time
      query: histogram_quantile(0.99, rate(db_query_duration_seconds_bucket[5m]))
      threshold: 2.0  # P99查询时间超过2秒告警
    
    # 外部调用时间
    - name: external_api_time
      query: histogram_quantile(0.95, rate(external_api_duration_seconds_bucket[5m]))
      threshold: 5.0  # P95外部调用超过5秒告警
    
    # 队列等待时间
    - name: queue_wait_time
      query: histogram_quantile(0.95, rate(queue_wait_duration_seconds_bucket[5m]))
      threshold: 1.0  # P95队列等待超过1秒告警
```

### 2. 智能告警策略

```java
/**
 * 智能告警策略
 */
public class SmartAlertStrategy {
    
    // 1. 基于基线告警
    public class BaselineAlert {
        /*
         * 建立正常情况下的性能基线
         * 如：平均响应时间、P95、P99等
         * 当指标偏离基线超过阈值时告警
         * 考虑时间因素（工作日/周末、白天/夜晚）
         */
    }
    
    // 2. 复合条件告警
    public class CompositeAlert {
        /*
         * 多个条件同时满足才告警
         * 如：超时率升高 AND 错误率升高
         * 避免单一指标波动导致的误报
         */
    }
    
    // 3. 趋势预测告警
    public class TrendAlert {
        /*
         * 基于历史数据预测未来趋势
         * 如：内存使用率持续增长，预测何时会OOM
         * 提前告警，防患于未然
         */
    }
    
    // 4. 根因关联告警
    public class RootCauseAlert {
        /*
         * 将相关告警关联起来
         * 如：数据库慢查询导致接口超时
         * 告警时提示可能的根因
         */
    }
}
```

## 📖 面试真题

### Q1: 接口超时如何快速定位问题？

**答：**
1. **查看监控指标**：响应时间、错误率、超时率
2. **分析调用链**：使用APM工具查看全链路，定位慢节点
3. **检查依赖服务**：数据库、缓存、外部API等依赖服务状态
4. **分析系统资源**：CPU、内存、磁盘IO、网络
5. **查看日志**：应用日志、慢查询日志、GC日志
6. **线程堆栈分析**：使用jstack分析线程状态
7. **网络排查**：使用ping、traceroute、tcpdump分析网络

### Q2: 数据库查询超时如何排查？

**答：**
1. **查看慢查询日志**：找到执行时间长的SQL
2. **分析执行计划**：使用EXPLAIN分析SQL执行计划
3. **检查索引使用**：是否使用合适索引，是否回表查询
4. **分析锁情况**：使用SHOW ENGINE INNODB STATUS查看锁信息
5. **检查连接数**：SHOW PROCESSLIST查看当前连接
6. **检查表状态**：表大小、碎片情况、统计信息是否准确
7. **硬件检查**：磁盘IO、CPU使用率、内存使用

### Q3: 如何设置合理的超时时间？

**答：**
1. **分层设置**：网络层、连接层、应用层分别设置
2. **参考SLA**：根据业务SLA要求设置
3. **逐步调优**：从较小值开始，逐步调整到合适值
4. **考虑依赖**：下游服务的超时时间要小于上游
5. **区分场景**：读操作和写操作设置不同的超时时间
6. **监控反馈**：根据实际监控数据调整超时时间
7. **设置重试**：超时后配合重试机制，但注意幂等性

### Q4: 如何避免超时导致的雪崩效应？

**答：**
1. **设置超时**：所有外部调用都必须设置超时时间
2. **使用熔断器**：当失败率超过阈值时自动熔断，避免连锁反应
3. **服务降级**：非核心功能降级，保证核心功能可用
4. **限流保护**：限制并发请求数，保护服务不被压垮
5. **异步处理**：耗时操作异步化，不阻塞主流程
6. **缓存优化**：使用缓存减少重复计算和外部调用
7. **快速失败**：尽早失败，避免资源长时间占用

### Q5: 全链路追踪在超时排查中的作用？

**答：**
1. **定位慢节点**：直观显示每个环节的耗时
2. **分析依赖关系**：显示服务调用链，找到瓶颈点
3. **关联日志**：通过Trace ID关联不同服务的日志
4. **性能分析**：统计每个服务的P95、P99响应时间
5. **根因分析**：结合业务日志，分析超时的根本原因
6. **容量规划**：基于调用链数据，合理规划服务容量
7. **优化验证**：优化后验证效果，对比优化前后的性能

## 📚 延伸阅读

- [微服务架构设计模式](https://book.douban.com/subject/33425123/)
- [SRE：Google运维解密](https://book.douban.com/subject/26875239/)
- [分布式系统：概念与设计](https://book.douban.com/subject/6082808/)
- [Resilience4j官方文档](https://resilience4j.readme.io/)

---

**⭐ 重点：超时问题排查需要系统化的方法论，结合监控、追踪、日志分析和性能优化，建立从预防、检测到恢复的完整体系**