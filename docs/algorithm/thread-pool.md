---
layout: default
title: 线程池与异步任务高频面试题 ⭐⭐⭐
---

# 线程池与异步任务高频面试题 ⭐⭐⭐

## 🎯 面试核心

线程池和异步任务是 Java 并发编程的核心内容，也是面试的高频考点。掌握线程池的原理、参数配置、拒绝策略，以及 CompletableFuture 的使用，是成为高级 Java 开发者的必备技能。

---

## 一、线程池核心参数

### 1. 七大参数详解

```java
public ThreadPoolExecutor(
    int corePoolSize,          // 核心线程数
    int maximumPoolSize,       // 最大线程数
    long keepAliveTime,         // 空闲线程存活时间
    TimeUnit unit,             // 时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,         // 线程工厂
    RejectedExecutionHandler handler     // 拒绝策略
)
```

### 2. 参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| **corePoolSize** | 核心线程数，即使空闲也不回收 | 4 |
| **maximumPoolSize** | 最大线程数，包括核心线程 | 8 |
| **keepAliveTime** | 空闲线程的存活时间 | 60 |
| **unit** | 时间单位 | TimeUnit.SECONDS |
| **workQueue** | 任务队列 | new LinkedBlockingQueue<>(100) |
| **threadFactory** | 线程工厂，创建新线程 | Executors.defaultThreadFactory() |
| **handler** | 拒绝策略 | new ThreadPoolExecutor.AbortPolicy() |

### 3. 线程池工作流程图解

```
                    ┌─────────────────────────────────────┐
                    │         新任务提交                  │
                    └─────────────┬───────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  核心线程数 < corePoolSize？ │
                    └────────────┬────────────┘
                       是        │        否
                       │         │         │
                       ▼         │         ▼
              ┌──────────────┐   │   ┌─────────────────┐
              │ 创建新线程    │   │   │  队列已满？      │
              │ 执行任务      │   │   └───────┬─────────┘
              └──────────────┘   │      是   │    否
                                 │      │    │
                                 │      ▼    │
                                 │ ┌──────────────┐
                                 │ │ 最大线程数 <  │
                                 │ │ maximumPoolSize？│
                                 │ └───────┬─────────┘
                                 │    是   │    否
                                 │    │    │
                                 │    ▼    │
                                 │ ┌──────────────┐
                                 │ │ 创建新线程    │
                                 │ │ 执行任务      │
                                 │ └──────────────┘
                                 │    │
                                 │    │
                                 ▼    ▼
                    ┌─────────────────────────┐
                    │      执行拒绝策略        │
                    └─────────────────────────┘
```

---

## 二、线程池工作流程详解

### 核心流程

```
1. 提交任务
   ↓
2. 检查线程池中运行的线程数 < corePoolSize？
   ├── 是 → 创建新线程执行任务
   └── 否 → 3
   ↓
3. 任务队列未满？
   ├── 是 → 任务加入队列，等待执行
   └── 否 → 4
   ↓
4. 线程池中运行的线程数 < maximumPoolSize？
   ├── 是 → 创建新线程执行任务
   └── 否 → 5
   ↓
5. 执行拒绝策略
```

### 拒绝时机

```
时机 1：任务队列已满（LinkedBlockingQueue 满了）
时机 2：线程池已关闭（shutdown）
时机 3：线程池已停止（shutdownNow）
时机 4：线程池达到最大容量且队列满
```

---

## 三、四种内置拒绝策略

### 1. AbortPolicy（默认）

```java
/**
 * 抛出 RejectedExecutionException 异常
 * 任务被拒绝，调用者可以捕获异常处理
 */
public static class AbortPolicy implements RejectedExecutionHandler {
    public void rejectedExecution(Runnable r, ThreadPoolExecutor e) {
        throw new RejectedExecutionException(
            "Task " + r.toString() +
            " rejected from " +
            e.toString()
        );
    }
}
```

### 2. CallerRunsPolicy

```java
/**
 * 由调用线程执行任务
 * 优点：缓解提交压力，让调用者自己执行
 * 缺点：可能影响调用者的性能
 */
public static class CallerRunsPolicy implements RejectedExecutionHandler {
    public void rejectedExecution(Runnable r, ThreadPoolExecutor e) {
        if (!e.isShutdown()) {
            r.run();  // 调用者线程执行
        }
    }
}
```

### 3. DiscardPolicy

```java
/**
 * 直接丢弃任务，不抛出异常
 * 缺点：任务被静默丢弃，不知道发生了什么
 */
public static class DiscardPolicy implements RejectedExecutionHandler {
    public void rejectedExecution(Runnable r, ThreadPoolExecutor e) {
        // 什么都不做
    }
}
```

### 4. DiscardOldestPolicy

```java
/**
 * 丢弃队列中最老的任务，然后重试执行新任务
 * 缺点：可能丢弃重要任务
 */
public static class DiscardOldestPolicy implements RejectedExecutionHandler {
    public void rejectedExecution(Runnable r, ThreadPoolExecutor e) {
        if (!e.isShutdown()) {
            e.getQueue().poll();  // 丢弃最老的任务
            e.execute(r);         // 重试执行新任务
        }
    }
}
```

### 自定义拒绝策略

```java
/**
 * 自定义拒绝策略：记录日志 + 降级处理
 */
public class CustomRejectedExecutionHandler implements RejectedExecutionHandler {
    private static final Logger logger = Logger.getLogger(
        CustomRejectedExecutionHandler.class.getName()
    );
    
    @Override
    public void rejectedExecution(Runnable r, ThreadPoolExecutor executor) {
        // 记录日志
        logger.warning("Task rejected: " + r.toString());
        
        // 降级处理：将任务写入本地文件或数据库
        try {
            saveToLocalFile(r);
        } catch (Exception e) {
            logger.severe("Failed to save rejected task: " + e.getMessage());
        }
    }
    
    private void saveToLocalFile(Runnable r) {
        // 保存到本地文件，后续处理
    }
}
```

---

## 四、线程池状态转换

### 五种状态

```java
// 线程池状态存储在 ctl 字段的高 3 位
private static final int COUNT_BITS = Integer.SIZE - 3;  // 29
private static final int CAPACITY   = (1 << COUNT_BITS) - 1;  // 2^29 - 1

// 五种状态（按值从小到大）
private static final int RUNNING    = -1 << COUNT_BITS;  // 接受新任务，执行队列中的任务
private static final int SHUTDOWN   =  0 << COUNT_BITS;  // 不接受新任务，但执行队列中的任务
private static final int STOP       =  1 << COUNT_BITS;  // 不接受新任务，不执行队列中的任务
private static final int TIDYING    =  2 << COUNT_BITS;  // 所有任务终止，terminated() 即将执行
private static final int TERMINATED  =  3 << COUNT_BITS;  // terminated() 已执行完成
```

### 状态转换图

```
RUNNING ──────► SHUTDOWN ──────► TIDYING ──────► TERMINATED
  │                │                │               │
  │                │                │               │
  │   调用 shutdown()│  调用 shutdown()│  任务全部执行完 │  terminated()
  │                │    队列空了      │    回调        │   执行完成
  │                │                │               │
  ▼                ▼                ▼               ▼
RUNNING       SHUTDOWN         TIDYING        TERMINATED
                    │
                    │
                    ▼
               ┌──────────┐
               │   STOP   │
               └──────────┘
                    ▲
                    │
调用 shutdownNow()  │
                    │
                    ▼
              不接受新任务
              不执行队列任务
```

### 状态详解

| 状态 | 值 | 说明 | 接受新任务 | 执行队列任务 |
|------|-----|------|-----------|------------|
| **RUNNING** | -1 | 运行中 | ✅ | ✅ |
| **SHUTDOWN** | 0 | 关闭中 | ❌ | ✅ |
| **STOP** | 1 | 已停止 | ❌ | ❌ |
| **TIDYING** | 2 | 整理中 | ❌ | ❌ |
| **TERMINATED** | 3 | 已终止 | ❌ | ❌ |

---

## 五、线程池选择建议

### 1. CPU 密集型 vs IO 密集型

```
CPU 密集型：
- 特点：任务主要是计算，CPU 占用高，很少等待
- 示例：视频编码、图片处理、数学计算
- 建议：corePoolSize = CPU 核心数 + 1
  （因为计算任务会占满 CPU，多一个线程用于处理调度）

IO 密集型：
- 特点：任务主要是 IO 等待，CPU 占用低
- 示例：数据库查询、网络请求、文件读写
- 建议：corePoolSize = CPU 核心数 × 2 或更多
  （因为 IO 等待时 CPU 空闲，可以处理更多任务）
```

### 2. 经验公式

```java
/**
 * 线程数计算公式
 * 
 * N_cpu = CPU 核心数
 * W_io = 等待时间（Wait）
 * C_cpu = 计算时间（Compute）
 * 
 * 最佳线程数 = N_cpu × (1 + W_io / C_cpu)
 */
public class ThreadPoolSizeCalculator {
    
    public static void main(String[] args) {
        // 获取 CPU 核心数
        int cpuCores = Runtime.getRuntime().availableProcessors();
        System.out.println("CPU cores: " + cpuCores);
        
        // IO 密集型（假设 IO 时间是计算时间的 4 倍）
        double ioRatio = 4.0;
        int ioThreads = (int) (cpuCores * (1 + ioRatio));
        System.out.println("IO密集型线程数建议: " + ioThreads);
        
        // CPU 密集型
        int cpuThreads = cpuCores + 1;
        System.out.println("CPU密集型线程数建议: " + cpuThreads);
    }
}
```

### 3. 常用线程池配置

```java
/**
 * CPU 密集型配置
 * 线程数 = CPU 核心数 + 1
 */
ThreadPoolExecutor cpuExecutor = new ThreadPoolExecutor(
    8, 8, 0L, TimeUnit.MILLISECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder().setNameFormat("cpu-pool-%d").build(),
    new ThreadPoolExecutor.AbortPolicy()
);

/**
 * IO 密集型配置
 * 线程数 = CPU 核心数 × 2
 */
ThreadPoolExecutor ioExecutor = new ThreadPoolExecutor(
    16, 16, 60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder().setNameFormat("io-pool-%d").build(),
    new ThreadPoolExecutor.AbortPolicy()
);

/**
 * 混合型配置
 * 线程数动态计算
 */
int corePoolSize = Runtime.getRuntime().availableProcessors() * 2;
int maxPoolSize = corePoolSize * 2;
```

---

## 六、ForkJoinPool

### 核心思想

```
ForkJoinPool 用于分治思想的问题：
1. Fork：将大任务拆分成小任务
2. Join：合并小任务的结果

特点：
- 工作窃取（Work Stealing）：空闲线程从其他线程队列中偷任务
- 适合递归任务：树形结构、归并排序等
```

### RecursiveTask 示例

```java
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveTask;

/**
 * 使用 ForkJoinPool 计算数组和
 */
public class ForkJoinSum extends RecursiveTask<Long> {
    private static final int THRESHOLD = 10000;  // 拆分阈值
    private long[] array;
    private int start;
    private int end;
    
    public ForkJoinSum(long[] array, int start, int end) {
        this.array = array;
        this.start = start;
        this.end = end;
    }
    
    @Override
    protected Long compute() {
        int length = end - start;
        
        if (length <= THRESHOLD) {
            // 小任务，直接计算
            return computeDirectly();
        } else {
            // 大任务，拆分成两个小任务
            int mid = start + length / 2;
            
            ForkJoinSum left = new ForkJoinSum(array, start, mid);
            ForkJoinSum right = new ForkJoinSum(array, mid, end);
            
            // Fork 两个子任务
            left.fork();
            right.fork();
            
            // Join 两个子任务的结果
            return left.join() + right.join();
        }
    }
    
    private long computeDirectly() {
        long sum = 0;
        for (int i = start; i < end; i++) {
            sum += array[i];
        }
        return sum;
    }
    
    public static void main(String[] args) {
        long[] array = new long[1000000];
        for (int i = 0; i < array.length; i++) {
            array[i] = i + 1;
        }
        
        ForkJoinPool pool = ForkJoinPool.commonPool();
        long result = pool.invoke(new ForkJoinSum(array, 0, array.length));
        System.out.println("Sum: " + result);
    }
}
```

### ForkJoinPool vs 普通线程池

| 特性 | ForkJoinPool | 普通线程池 |
|------|-------------|-----------|
| 任务类型 | 递归任务 | 普通任务 |
| 工作窃取 | ✅ 支持 | ❌ 不支持 |
| 适用场景 | 分治问题 | 独立任务 |
| 吞吐量 | 更高 | 一般 |

---

## 七、CompletableFuture

### 核心概念

```
CompletableFuture 是 Java 8 引入的异步编程利器：

1. 异步执行：不需要手动管理线程
2. 链式调用：支持 thenApply、thenCompose、thenCombine 等
3. 组合操作：支持 allOf、anyOf 等
4. 异常处理：支持 exceptionally、handle 等
```

### 1. 基本用法

```java
/**
 * 创建 CompletableFuture
 */
public class CompletableFutureDemo {
    
    public static void main(String[] args) throws Exception {
        // 方法 1：supplyAsync - 有返回值
        CompletableFuture<String> future1 = CompletableFuture.supplyAsync(() -> {
            return "Hello";
        });
        
        // 方法 2：runAsync - 无返回值
        CompletableFuture<Void> future2 = CompletableFuture.runAsync(() -> {
            System.out.println("Running async task");
        });
        
        // 获取结果
        String result = future1.get();
        System.out.println(result);
        
        future2.get();
    }
}
```

### 2. thenApply - 转换结果

```java
/**
 * thenApply：转换结果类型
 */
public class ThenApplyDemo {
    public static void main(String[] args) throws Exception {
        CompletableFuture<Integer> future = CompletableFuture
            .supplyAsync(() -> "123")          // String
            .thenApply(Integer::parseInt)      // 转换为 Integer
            .thenApply(x -> x * 2);           // 乘以 2
        
        System.out.println(future.get());  // 246
    }
}
```

### 3. thenCompose - 扁平化

```java
/**
 * thenCompose：用于返回另一个 CompletableFuture 的情况
 */
public class ThenComposeDemo {
    
    public CompletableFuture<User> getUserById(long id) {
        return CompletableFuture.supplyAsync(() -> {
            return new User(id, "User" + id);
        });
    }
    
    public CompletableFuture<String> getUserName(long id) {
        return CompletableFuture
            .supplyAsync(() -> id)
            .thenCompose(this::getUserById)  // 返回 CompletableFuture
            .thenApply(User::getName);
    }
    
    public static void main(String[] args) throws Exception {
        ThenComposeDemo demo = new ThenComposeDemo();
        String name = demo.getUserName(1L).get();
        System.out.println(name);  // User1
    }
}

class User {
    private long id;
    private String name;
    
    public User(long id, String name) {
        this.id = id;
        this.name = name;
    }
    
    public long getId() { return id; }
    public String getName() { return name; }
}
```

### 4. thenCombine - 组合两个结果

```java
/**
 * thenCombine：组合两个独立的 CompletableFuture
 */
public class ThenCombineDemo {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> future1 = CompletableFuture
            .supplyAsync(() -> "Hello");
        
        CompletableFuture<String> future2 = CompletableFuture
            .supplyAsync(() -> "World");
        
        // 组合两个结果
        String result = future1
            .thenCombine(future2, (s1, s2) -> s1 + " " + s2)
            .get();
        
        System.out.println(result);  // Hello World
    }
}
```

### 5. 异常处理

```java
/**
 * 异常处理
 */
public class ExceptionHandleDemo {
    public static void main(String[] args) throws Exception {
        // exceptionally：捕获异常并返回默认值
        String result1 = CompletableFuture
            .supplyAsync(() -> {
                if (true) throw new RuntimeException("Error!");
                return "Success";
            })
            .exceptionally(ex -> "Default value: " + ex.getMessage())
            .get();
        
        System.out.println(result1);  // Default value: Error!
        
        // handle：无论如何都执行，可以修改结果
        String result2 = CompletableFuture
            .supplyAsync(() -> {
                if (true) throw new RuntimeException("Error!");
                return "Success";
            })
            .handle((result, ex) -> {
                if (ex != null) {
                    return "Handled: " + ex.getMessage();
                }
                return result;
            })
            .get();
        
        System.out.println(result2);  // Handled: Error!
    }
}
```

### 6. 等待多个任务完成

```java
/**
 * 等待多个任务完成
 */
public class WaitMultipleDemo {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> f1 = CompletableFuture
            .supplyAsync(() -> "Task 1");
        CompletableFuture<String> f2 = CompletableFuture
            .supplyAsync(() -> "Task 2");
        CompletableFuture<String> f3 = CompletableFuture
            .supplyAsync(() -> "Task 3");
        
        // 等待所有任务完成
        CompletableFuture.allOf(f1, f2, f3).get();
        
        System.out.println("All tasks completed!");
        
        // 等待任意一个任务完成
        CompletableFuture.anyOf(f1, f2, f3).get();
        
        System.out.println("At least one task completed!");
    }
}
```

---

## 八、高频面试题总结

| 题目 | 难度 | 关键点 | 时间复杂度 |
|------|------|--------|-----------|
| 线程池参数 | ⭐ | 七大参数、工作流程 | - |
| 拒绝策略 | ⭐⭐ | 四种策略、自定义 | - |
| 线程池状态 | ⭐⭐ | 五种状态转换 | - |
| CPU vs IO 密集型 | ⭐⭐ | 线程数计算 | - |
| ForkJoinPool | ⭐⭐ | 分治思想、工作窃取 | O(N log N) |
| CompletableFuture | ⭐⭐⭐ | 异步编排、链式调用 | - |

---

## 九、面试建议

1. **理解原理**：线程池的工作流程是核心，要能画图解释
2. **参数配置**：根据业务场景选择合适的线程数
3. **拒绝策略**：了解四种策略的适用场景，能自定义
4. **状态转换**：掌握五种状态的含义和转换条件
5. **CompletableFuture**：熟练使用 thenApply、thenCompose、thenCombine
6. **实际应用**：结合项目经验，如订单处理、异步日志等
7. **扩展思考**：线程池监控、动态调整、队列选择等
