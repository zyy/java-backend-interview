---
layout: default
title: 线程池核心参数详解 ⭐⭐⭐
---
# 线程池核心参数详解 ⭐⭐⭐

## 面试题：讲讲线程池有哪些核心参数？

### 核心回答

Java 线程池通过 `ThreadPoolExecutor` 类实现，包含 **7 个核心参数**，合理配置这些参数是高性能并发编程的关键。

### 七大核心参数

```java
public ThreadPoolExecutor(
    int corePoolSize,           // 核心线程数
    int maximumPoolSize,        // 最大线程数
    long keepAliveTime,         // 空闲线程存活时间
    TimeUnit unit,              // 时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,        // 线程工厂
    RejectedExecutionHandler handler    // 拒绝策略
)
```

### 参数详解

#### 1. corePoolSize（核心线程数）

**定义**：线程池中始终保持存活的线程数量，即使空闲也不会被销毁。

**特点**：
- 线程池初始化时不会立即创建核心线程
- 有任务提交时，如果当前线程数 < corePoolSize，会创建新线程
- 直到线程数达到 corePoolSize，新任务才会进入队列

**配置建议**：
```
CPU 密集型任务：N + 1（N 为 CPU 核心数）
IO 密集型任务：2N 或更大
混合型任务：根据实际情况测试调整
```

#### 2. maximumPoolSize（最大线程数）

**定义**：线程池中允许存在的最大线程数量。

**触发条件**：
- 当任务队列已满
- 当前线程数 < maximumPoolSize
- 会创建非核心线程来处理任务

**注意**：
- 如果设置过大，可能导致系统资源耗尽
- 建议根据系统资源和任务特性设置上限

#### 3. keepAliveTime（线程空闲时间）

**定义**：非核心线程在空闲状态下的最大存活时间。

**说明**：
- 仅对非核心线程有效（线程数 > corePoolSize 时）
- 超过此时间，空闲线程会被销毁
- 可通过 `allowCoreThreadTimeOut(true)` 让核心线程也受限制

#### 4. unit（时间单位）

**定义**：keepAliveTime 的时间单位。

**常用值**：
- `TimeUnit.SECONDS` - 秒
- `TimeUnit.MILLISECONDS` - 毫秒

#### 5. workQueue（任务队列）

**定义**：用于存放等待执行任务的阻塞队列。

**常用队列类型**：

| 队列类型 | 特点 | 适用场景 |
|---------|------|---------|
| `ArrayBlockingQueue` | 有界队列，基于数组 | 需要限制队列大小，防止 OOM |
| `LinkedBlockingQueue` | 无界队列（默认容量 Integer.MAX_VALUE） | 任务量波动大，内存充足 |
| `SynchronousQueue` | 不存储元素，直接提交 | 任务执行快，需要直接传递 |
| `PriorityBlockingQueue` | 优先级队列 | 任务有优先级区分 |

**选择建议**：
- **有界队列**：防止任务无限堆积导致 OOM
- **无界队列**：配合合理的拒绝策略使用

#### 6. threadFactory（线程工厂）

**定义**：用于创建新线程的工厂类。

**作用**：
- 自定义线程名称（便于问题排查）
- 设置线程优先级
- 设置守护线程属性

```java
ThreadFactory namedThreadFactory = new ThreadFactoryBuilder()
    .setNameFormat("pool-%d")
    .setDaemon(false)
    .build();
```

#### 7. handler（拒绝策略）

**定义**：当线程池和队列都满时，处理新任务的策略。

**JDK 内置策略**：

| 策略 | 行为 |
|------|------|
| `AbortPolicy`（默认） | 直接抛出 RejectedExecutionException |
| `CallerRunsPolicy` | 由调用线程（提交任务的线程）执行 |
| `DiscardPolicy` | 静默丢弃任务 |
| `DiscardOldestPolicy` | 丢弃队列中最老的任务，重试提交 |

**自定义拒绝策略**：
```java
RejectedExecutionHandler customHandler = (r, executor) -> {
    // 记录日志
    log.warn("Task rejected: {}", r);
    // 持久化到数据库，后续补偿执行
    saveToDb(r);
};
```

### 线程池执行流程

```
提交任务
    ↓
当前线程数 < corePoolSize ?
    ↓ 是
创建核心线程执行任务
    ↓ 否
任务队列是否已满 ?
    ↓ 否
加入任务队列等待执行
    ↓ 是
当前线程数 < maximumPoolSize ?
    ↓ 是
创建非核心线程执行任务
    ↓ 否
执行拒绝策略
```

### 线程池状态

```java
// 线程池的 5 种状态
private static final int RUNNING    = -1 << COUNT_BITS;  // 接收新任务，处理队列任务
private static final int SHUTDOWN   =  0 << COUNT_BITS;  // 不接收新任务，处理队列任务
private static final int STOP       =  1 << COUNT_BITS;  // 不接收新任务，不处理队列任务
private static final int TIDYING    =  2 << COUNT_BITS;  // 所有任务终止，执行 terminated()
private static final int TERMINATED =  3 << COUNT_BITS;  // terminated() 执行完成
```

### 线程池配置示例

```java
// CPU 密集型任务线程池
ThreadPoolExecutor cpuExecutor = new ThreadPoolExecutor(
    4,                      // corePoolSize = CPU核心数 + 1
    8,                      // maximumPoolSize
    60L, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(100),
    new ThreadFactoryBuilder().setNameFormat("cpu-pool-%d").build(),
    new ThreadPoolExecutor.CallerRunsPolicy()
);

// IO 密集型任务线程池
ThreadPoolExecutor ioExecutor = new ThreadPoolExecutor(
    8,                      // corePoolSize = CPU核心数 * 2
    16,                     // maximumPoolSize
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder().setNameFormat("io-pool-%d").build(),
    new ThreadPoolExecutor.DiscardPolicy()
);
```

### 高频面试题

**Q1: 为什么使用线程池？**
- 减少线程创建/销毁的开销
- 控制并发线程数量
- 便于线程管理和监控
- 提高响应速度

**Q2: corePoolSize = 0 时线程池如何工作？**
- 提交任务时，任务直接进入队列
- 队列满后，创建线程执行任务
- 适用于任务执行不频繁的场景

**Q3: 如何合理配置线程池参数？**
1. 分析任务是 CPU 密集型还是 IO 密集型
2. 根据任务类型设置 corePoolSize
3. 根据系统资源设置 maximumPoolSize
4. 根据任务量波动选择队列类型
5. 根据业务重要性选择拒绝策略

**Q4: submit() 和 execute() 的区别？**
- `execute()`：提交 Runnable 任务，无返回值
- `submit()`：提交 Runnable/Callable 任务，返回 Future

### 最佳实践

1. **使用有界队列**：防止任务无限堆积
2. **自定义线程名称**：便于问题排查
3. **监控线程池状态**：通过 `getActiveCount()`、`getQueue().size()` 等
4. **优雅关闭**：先调用 `shutdown()`，等待任务完成后再关闭

```java
// 优雅关闭线程池
executor.shutdown();
try {
    if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
        executor.shutdownNow();
    }
} catch (InterruptedException e) {
    executor.shutdownNow();
}
```

---

**参考链接：**
- [Java线程池核心参数详解-CSDN](https://blog.csdn.net/qq_61302385/article/details/147209145)
- [线程池核心参数详解-掘金](https://juejin.cn/post/7498997224401518611)
