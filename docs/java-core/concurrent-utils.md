---
layout: default
title: Java 并发工具类详解：CountDownLatch、CyclicBarrier、Semaphore ⭐⭐⭐
---

# Java 并发工具类详解：CountDownLatch、CyclicBarrier、Semaphore ⭐⭐⭐

## 面试题概览

> 以下三个工具类是 Java 并发编程中最核心的同步辅助类，几乎是面试必问内容。面试官通常会从原理、使用场景、源码实现等多个维度进行考察，务必做到原理清晰、代码熟练。

---

## 一、AQS 回顾

在深入讲解三大并发工具类之前，我们先简要回顾一下 AQS（AbstractQueuedSynchronizer）的核心概念，因为 **CountDownLatch 和 Semaphore 都基于 AQS 实现**，理解 AQS 是掌握它们的基石。

### 1.1 AQS 是什么？

AQS 是 Java 并发包（JUC）的核心框架，提供了一种实现阻塞锁和其他同步器（Synchronizer）的通用框架。它使用一个 **volatile 的 int 类型的 state 变量**来表示同步状态，并维护了一个 **FIFO 双向队列**来管理等待线程。

### 1.2 AQS 的两种模式

AQS 支持两种同步模式：

- **独占模式（Exclusive）**：同一时刻只有一个线程能获取同步状态。例如 `ReentrantLock`。
- **共享模式（Shared）**：同一时刻可以有多个线程同时获取同步状态。例如 `CountDownLatch`、`Semaphore`、`CyclicBarrier`（底层使用 ReentrantLock + Condition，虽然不是直接继承 AQS 但语义上属于共享）。

### 1.3 AQS 核心方法

```java
// 独占模式获取
public final void acquire(int arg);
// 独占模式释放
public final boolean release(int arg);

// 共享模式获取
public final void acquireShared(int arg);
// 共享模式释放
public final boolean releaseShared(int arg);
```

子类需要覆写的方法：

```java
// 独占模式：尝试获取锁
protected boolean tryAcquire(int arg);

// 独占模式：尝试释放锁
protected boolean tryRelease(int arg);

// 共享模式：尝试获取共享锁，返回负数表示失败
protected int tryAcquireShared(int arg);

// 共享模式：尝试释放共享锁
protected boolean tryReleaseShared(int arg);

// 判断当前线程是否持有独占锁
protected boolean isHeldExclusively();
```

### 1.4 等待队列结构

AQS 内部维护了一个 CLH 队列的变体——一个双向 FIFO 队列：

```java
static final class Node {
    // 共享模式标记
    static final Node SHARED = new Node();
    // 独占模式标记
    static final Node EXCLUSIVE = null;

    // 等待状态
    volatile int waitStatus;
    static final int CANCELLED = 1;    // 线程已取消
    static final int SIGNAL = -1;       // 后继节点需要被唤醒
    static final int CONDITION = -2;    // 线程在条件队列中等待
    static final int PROPAGATE = -3;    // 共享模式状态传播

    volatile Node prev;   // 前驱节点
    volatile Node next;   // 后继节点
    volatile Thread thread; // 当前节点绑定的线程
}
```

### 1.5 AQS 与三大工具类的关系

| 工具类 | 基于 AQS | 模式 |
|--------|----------|------|
| CountDownLatch | ✅ | 共享模式 |
| Semaphore | ✅ | 共享模式 |
| CyclicBarrier | ❌（基于 ReentrantLock + Condition） | N/A |
| Exchanger | ❌（基于 CAS） | N/A |
| Phaser | ❌（自己实现同步逻辑） | N/A |

---

## 二、CountDownLatch

### 2.1 概念与使用场景

**CountDownLatch**（倒计时门闩）是一种同步辅助类，允许一个或多个线程等待一组其他线程完成操作后再继续执行。

**核心思想**：通过一个**计数器**实现，计数器的初始值为线程的数量。每当一个线程完成了自己的任务后，调用 `countDown()` 将计数器的值减 1。当计数器值变为 0 时，那些在 `await()` 上等待的线程就会被唤醒，继续执行后续任务。

**典型使用场景**：

1. **主线程等待子线程完成**：启动多个子线程执行任务，主线程调用 `await()` 等待所有子线程完成后汇总结果。
2. **服务启动时预热**：等待多个依赖服务（或缓存）加载完成后再对外提供服务。
3. **多线程计算结果合并**：开启 N 个线程并行计算，主线程汇总结果。
4. **接口依赖并行化**：多个外部接口互不依赖，可以并行调用，使用 CountDownLatch 等待所有结果返回。

### 2.2 核心 API

```java
// 创建计数器，count 为计数器的初始值
public CountDownLatch(int count);

// 等待计数器归零。如果计数器值已经为 0，立即返回；
// 否则阻塞当前线程直到计数器归零或线程被中断。
public void await() throws InterruptedException;

// 带超时时间的等待
public boolean await(long timeout, TimeUnit unit) throws InterruptedException;

// 使计数器减 1。如果计数器值已经为 0，则没有任何效果。
public void countDown();
```

### 2.3 原理：AQS 共享模式

`CountDownLatch` 内部通过一个 **Sync 内部类**继承了 AQS，并使用 AQS 的**共享模式**来实现。

```java
// CountDownLatch 源码（基于 JDK 8）
private static final class Sync extends AbstractQueuedSynchronizer {
    private final int count;

    Sync(int count) {
        this.count = count;
        // 设置初始状态值
        setState(count);
    }

    // 共享模式获取：尝试获取锁（这里表示等待计数器归零）
    // 返回值 >= 0 表示成功
    protected int tryAcquireShared(int args) {
        // 当 state == 0 时返回 1（成功），否则返回 -1（失败，进入等待队列）
        return getState() == 0 ? 1 : -1;
    }

    // 共享模式释放：计数器减 1，如果减到 0 则唤醒等待队列中的节点
    protected boolean tryReleaseShared(int args) {
        // 循环CAS，保证原子性
        for (;;) {
            int c = getState();
            if (c == 0) {
                // 已经是 0 了，不能再减，返回 false（不应该发生）
                return false;
            }
            int nextc = c - 1;
            if (compareAndSetState(c, nextc)) {
                // 只有减到 0 才返回 true，触发唤醒逻辑
                return nextc == 0;
            }
        }
    }
}
```

**工作流程**：

1. 创建 `CountDownLatch(count)` 时，AQS 的 state 被初始化为 `count`。
2. 线程调用 `await()` 时，AQS 会调用 `tryAcquireShared(arg)`。如果 `state == 0`，返回 1，立即返回；否则返回 -1，当前线程被封装成 Node 加入等待队列并阻塞。
3. 其他线程调用 `countDown()` 时，AQS 调用 `tryReleaseShared(arg)`。将 `state` 减 1，如果 `state` 变为 0，则调用 `doReleaseShared()` **唤醒等待队列中的头节点的后继节点**。
4. 被唤醒的线程重新尝试 `tryAcquireShared`，发现 `state == 0`，于是成功返回，`await()` 方法解除阻塞。

### 2.4 完整代码示例

#### 示例一：主线程等待子线程完成

```java
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class CountDownLatchDemo1 {

    public static void main(String[] args) throws InterruptedException {
        int threadCount = 5;
        CountDownLatch latch = new CountDownLatch(threadCount);

        ExecutorService executor = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final int threadNum = i + 1;
            executor.submit(() -> {
                try {
                    System.out.println("线程 " + threadNum + " 开始执行任务...");
                    // 模拟工作
                    Thread.sleep((long) (Math.random() * 2000));
                    System.out.println("线程 " + threadNum + " 完成任务！");
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    // 计数器减 1，必须放在 finally 中确保一定执行
                    latch.countDown();
                }
            });
        }

        System.out.println("主线程等待子线程执行完成...");
        // 等待所有子线程完成
        latch.await();
        System.out.println("所有子线程执行完毕，主线程继续执行！");

        executor.shutdown();
    }
}
```

**运行结果示例**：
```
主线程等待子线程执行完成...
线程 1 开始执行任务...
线程 3 开始执行任务...
线程 2 开始执行任务...
线程 4 开始执行任务...
线程 5 开始执行任务...
线程 4 完成任务！
线程 2 完成任务！
线程 3 完成任务！
线程 1 完成任务！
线程 5 完成任务！
所有子线程执行完毕，主线程继续执行！
```

#### 示例二：带超时等待的多线程任务

```java
import java.util.concurrent.*;

public class CountDownLatchTimeoutDemo {

    public static void main(String[] args) throws Exception {
        int taskCount = 3;
        CountDownLatch latch = new CountDownLatch(taskCount);

        ExecutorService executor = Executors.newFixedThreadPool(taskCount);

        for (int i = 0; i < taskCount; i++) {
            executor.submit(() -> {
                try {
                    // 模拟任务
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    latch.countDown();
                }
            });
        }

        // 最多等待 5 秒
        boolean completed = latch.await(5, TimeUnit.SECONDS);
        if (completed) {
            System.out.println("所有任务在 5 秒内完成！");
        } else {
            System.out.println("等待超时，还有任务未完成！");
        }

        executor.shutdown();
    }
}
```

#### 示例三：模拟游戏加载

```java
import java.util.concurrent.*;

public class GameLoadingDemo {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("游戏启动中...");

        CountDownLatch latch = new CountDownLatch(3);

        // 加载声音资源
        new Thread(() -> {
            try {
                Thread.sleep(2000);
                System.out.println("✅ 声音资源加载完成");
            } catch (InterruptedException e) {
                e.printStackTrace();
            } finally {
                latch.countDown();
            }
        }, "声音线程").start();

        // 加载图像资源
        new Thread(() -> {
            try {
                Thread.sleep(3000);
                System.out.println("✅ 图像资源加载完成");
            } catch (InterruptedException e) {
                e.printStackTrace();
            } finally {
                latch.countDown();
            }
        }, "图像线程").start();

        // 加载网络资源
        new Thread(() -> {
            try {
                Thread.sleep(1000);
                System.out.println("✅ 网络资源加载完成");
            } catch (InterruptedException e) {
                e.printStackTrace();
            } finally {
                latch.countDown();
            }
        }, "网络线程").start();

        latch.await();
        System.out.println("🎮 所有资源加载完毕，游戏开始！");
    }
}
```

---

## 三、CyclicBarrier

### 3.1 概念与使用场景

**CyclicBarrier**（循环栅栏）是一种同步辅助类，允许一组线程相互等待，直到所有线程都到达某个屏障点之后，所有线程才会被释放并继续执行。

与 CountDownLatch 的关键区别：
- **CountDownLatch**：计数器只能减，不能重置，一旦减到 0 就不可复用。
- **CyclicBarrier**：计数器到 0 后会自动重置（循环），可以反复使用。

**典型使用场景**：

1. **多线程计算任务分阶段汇总**：例如第一阶段所有线程并行计算，第二阶段汇总结果，第三阶段再并行计算……每阶段都需要等待所有线程完成。
2. **多路数据加载完成后合并**：例如同时加载文件数据、数据库数据、缓存数据，全部加载完成后再进行数据合并处理。
3. **压力测试中的并发请求控制**：模拟 N 个用户同时发起请求。
4. **并行排序算法**：如归并排序中，将数组分段后各线程排序，然后合并。

### 3.2 核心 API

```java
// 创建屏障，参与线程数为 parties
public CyclicBarrier(int parties);

// 创建屏障，指定 barrierAction（当所有线程到达屏障后，由最后一个到达的线程执行该回调）
public CyclicBarrier(int parties, Runnable barrierAction);

// 等待所有线程到达屏障。如果当前线程不是最后一个到达的，则阻塞。
// 返回值是到达的序号（int），用于区分是第几个到达的
public int await() throws InterruptedException, BrokenBarrierException;

// 带超时的等待
public int await(long timeout, TimeUnit unit);

// 重置屏障到初始状态
public void reset();

// 查询当前有多少个线程在等待
public int getNumberWaiting();

// 查询屏障是否处于 broken 状态
public boolean isBroken();
```

### 3.3 原理：ReentrantLock + Condition

`CyclicBarrier` **不是基于 AQS** 实现的，而是直接使用了 **`ReentrantLock` + `Condition`** 来实现。

```java
// CyclicBarrier 核心结构（基于 JDK 8）
public class CyclicBarrier {
    // 屏障开启需要的线程数量
    private final int parties;
    // 最后一个到达线程要执行的回调
    private final Runnable barrierCommand;

    // 保护屏障修改的锁
    private final ReentrantLock lock = new ReentrantLock();
    // 条件变量：线程在此等待直到所有线程到达
    private final Condition trip = lock.newCondition();

    // 当前_generation：每次 reset() 都会创建新的 generation
    private static class Generation {
        boolean broken = false;
    }
    private Generation generation = new Generation();

    // 剩余需要到达的线程数，初始值为 parties
    private int count;

    public CyclicBarrier(int parties, Runnable barrierAction) {
        this.parties = parties;
        this.count = parties;
        this.barrierCommand = barrierAction;
    }

    // 等待方法
    public int await() throws InterruptedException, BrokenBarrierException {
        try {
            return dowait(false, 0L);
        } catch (TimeoutException toe) {
            throw new Error(toe); // 不应该发生
        }
    }

    private int dowait(boolean timed, long nanos) throws InterruptedException,
            BrokenBarrierException, TimeoutException {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            Generation g = generation;

            // 检查屏障是否已被破坏
            if (g.broken)
                throw new BrokenBarrierException();

            // 检查是否被中断
            if (Thread.interrupted()) {
                breakBarrier();
                throw new InterruptedException();
            }

            int index = --count;
            // 如果不是最后一个到达的线程
            if (index != 0) {
                // 等待
                if (!timed)
                    trip.await();
                else if (nanos > 0)
                    nanos = trip.awaitNanos(nanos);

                // 被唤醒后检查屏障状态
                if (g.broken || generation != g)
                    return index;

                // 如果超时，则破坏屏障
                throw new TimeoutException();
            }

            // 最后一个到达的线程，执行以下逻辑
            // 1. 执行 barrierAction 回调
            Runnable command = barrierCommand;
            if (command != null) {
                command.run();
            }
            // 2. 唤醒所有等待的线程
            nextGeneration();
            return 0;

        } finally {
            lock.unlock();
        }
    }

    // 推进到下一代（重置计数器 + 唤醒所有等待线程）
    private void nextGeneration() {
        trip.signalAll();  // 唤醒所有等待的线程
        count = parties;   // 重置计数器
        generation = new Generation(); // 创建新的 generation
    }

    // 破坏屏障
    private void breakBarrier() {
        generation.broken = true;
        count = parties;
        trip.signalAll();
    }

    // 重置屏障
    public void reset() {
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            breakBarrier();    // 破坏当前代
            nextGeneration();   // 开启新一代（自动重置）
        } finally {
            lock.unlock();
        }
    }
}
```

**工作流程**：

1. 线程调用 `await()` 后，先获取锁（`lock.lock()`），将 `count` 减 1。
2. 如果 `index != 0`（还有线程未到达），则调用 `trip.await()` 释放锁并阻塞，当前线程进入 Condition 的等待队列。
3. 如果 `index == 0`（自己是最后一个到达的线程）：
   - 执行 `barrierAction` 回调（如果有）。
   - 调用 `nextGeneration()`——通过 `trip.signalAll()` 唤醒所有等待的线程，重置 `count = parties`，创建新的 `Generation` 对象。
4. 被唤醒的线程重新竞争锁，然后 `dowait` 方法返回，`await()` 解除阻塞。

### 3.4 barrierAction 回调

`barrierAction` 是 `CyclicBarrier` 的一个非常实用的特性。当最后一个线程到达屏障点时，会由**最后一个到达的线程**负责执行这个回调。这意味着可以用它来做一些汇总工作。

```java
import java.util.concurrent.*;
import java.util.*;

public class CyclicBarrierWithAction {

    public static void main(String[] args) {
        int partyCount = 4;

        // 回调：当所有线程到达后执行（通常用于汇总）
        Runnable barrierAction = () -> {
            System.out.println("🏁 所有线程已到达，汇总结果阶段开始...");
        };

        CyclicBarrier barrier = new CyclicBarrier(partyCount, barrierAction);

        List<Thread> threads = new ArrayList<>();

        for (int i = 0; i < partyCount; i++) {
            final int threadId = i + 1;
            Thread t = new Thread(() -> {
                try {
                    System.out.println("线程 " + threadId + " 正在执行第一阶段任务...");
                    Thread.sleep((long) (Math.random() * 1000));

                    System.out.println("线程 " + threadId + " 到达屏障点，等待其他线程...");
                    barrier.await();  // 等待第一阶段完成

                    // 第一阶段汇总结束后，所有线程继续执行第二阶段
                    System.out.println("线程 " + threadId + " 开始执行第二阶段任务...");
                    Thread.sleep((long) (Math.random() * 500));

                    System.out.println("线程 " + threadId + " 到达第二个屏障点...");
                    barrier.await();  // 等待第二阶段完成

                    System.out.println("线程 " + threadId + " 全部完成！");
                } catch (InterruptedException | BrokenBarrierException e) {
                    e.printStackTrace();
                }
            }, "Worker-" + threadId);
            threads.add(t);
            t.start();
        }

        // 等待所有线程结束
        threads.forEach(t -> {
            try {
                t.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        });

        System.out.println("所有工作线程均已完成！");
    }
}
```

### 3.5 CyclicBarrier vs CountDownLatch 区别

| 对比维度 | CountDownLatch | CyclicBarrier |
|----------|----------------|---------------|
| **计数方向** | 只减不增 | 只减，到 0 自动重置（可循环） |
| **是否可复用** | 一次性，计数到 0 后不可再用 | 可复用，通过 `reset()` 重置 |
| **等待方向** | 主线程等待子线程 | 子线程之间相互等待 |
| **底层实现** | AQS 共享模式 | ReentrantLock + Condition |
| **计数器归零后的行为** | 唤醒所有等待线程 | 最后一个到达的线程执行 `barrierAction` 后唤醒其他线程 |
| **典型场景** | 主线程等待子线程完成 | 多线程分阶段协作 |
| **异常处理** | 不可被中断（除非显式抛出） | 任何一个线程中断都会破坏屏障（`BrokenBarrierException`） |
| **reset()** | 无此方法 | 有，可以主动重置 |

### 3.6 完整代码示例

```java
import java.util.concurrent.*;
import java.util.*;

public class CyclicBarrierCompleteDemo {

    // 模拟数据处理任务
    private static final int TASK_COUNT = 3;
    // 存放各线程处理结果的集合
    private static final List<String> results = Collections.synchronizedList(new ArrayList<>());

    public static void main(String[] args) throws InterruptedException {
        ExecutorService executor = Executors.newFixedThreadPool(TASK_COUNT);

        // 第一阶段屏障
        CyclicBarrier barrier1 = new CyclicBarrier(TASK_COUNT, () -> {
            System.out.println("【汇总】第一阶段完成，汇总结果：" + results);
        });

        // 第二阶段屏障
        CyclicBarrier barrier2 = new CyclicBarrier(TASK_COUNT, () -> {
            System.out.println("【汇总】第二阶段完成，最终结果汇总！");
        });

        for (int i = 0; i < TASK_COUNT; i++) {
            final int taskId = i + 1;
            executor.submit(() -> {
                try {
                    // ===== 第一阶段：并行处理 =====
                    String data = "Task-" + taskId + "-Data-" + UUID.randomUUID().toString().substring(0, 4);
                    System.out.println("任务 " + taskId + " 处理了数据: " + data);
                    results.add(data);

                    // 等待其他任务也处理完
                    barrier1.await();

                    // ===== 第二阶段：处理汇总结果 =====
                    System.out.println("任务 " + taskId + " 收到第一阶段汇总，继续处理...");
                    Thread.sleep(500);
                    String processed = "Processed-" + taskId;
                    results.add(processed);

                    // 等待所有任务第二阶段完成
                    barrier2.await();

                    System.out.println("任务 " + taskId + " 全部完成！");
                } catch (InterruptedException | BrokenBarrierException e) {
                    e.printStackTrace();
                }
            });
        }

        Thread.sleep(10000); // 等待足够长的时间
        executor.shutdown();
    }
}
```

---

## 四、Semaphore

### 4.1 概念与使用场景

**Semaphore**（信号量）是一种计数信号量，用于控制同时访问某个特定资源的线程数量。

**核心思想**：`Semaphore` 维护了一组**许可（permits）**。线程通过 `acquire()` 方法获取许可，如果没有可用许可则阻塞；通过 `release()` 方法释放许可，归还信号量。

**典型使用场景**：

1. **限流（流量控制）**：限制对某个资源（如数据库连接池、线程池、接口并发数）的访问数量。
2. **资源池管理**：如连接池、对象池，限制同时使用的资源数量。
3. **多线程并发控制**：控制同时运行的线程数量，避免资源耗尽。
4. **读写限流**：限制同时读取资源的线程数（虽然更推荐使用 ReadWriteLock）。

### 4.2 核心 API

```java
// 创建信号量，permits 为许可数量
public Semaphore(int permits);

// 创建信号量，fair 指定是否为公平模式
public Semaphore(int permits, boolean fair);

// 获取 1 个许可，阻塞直到可用
public void acquire() throws InterruptedException;

// 获取多个许可
public void acquire(int permits) throws InterruptedException;

// 尝试获取许可（非阻塞）
public boolean tryAcquire();

// 尝试获取许可，带超时
public boolean tryAcquire(long timeout, TimeUnit unit);

// 释放 1 个许可
public void release();

// 释放多个许可
public void release(int permits);

// 查询当前可用的许可数量
public int availablePermits();

// 查询是否有线程在等待获取许可
public final boolean hasQueuedThreads();
```

### 4.3 原理：AQS 共享模式

`Semaphore` 内部有两个实现类：`NonfairSync`（非公平）和 `FairSync`（公平），都继承自 `Sync`，而 `Sync` 继承自 `AQS`。

```java
// Semaphore 源码（基于 JDK 8）

public class Semaphore implements java.io.Serializable {
    
    private final Sync sync;

    // 非公平模式
    static final class NonfairSync extends Sync {
        NonfairSync(int permits) {
            super(permits);
        }
        protected int tryAcquireShared(int acquires) {
            return nonfairTryAcquireShared(acquires);
        }
    }

    // 公平模式
    static final class FairSync extends Sync {
        FairSync(int permits) {
            super(permits);
        }
        protected int tryAcquireShared(int acquires) {
            for (;;) {
                // 公平模式：先检查等待队列中是否有更早等待的线程
                if (hasQueuedPredecessors())
                    return -1;
                int available = getState();
                int acquired = available - acquires;
                if (acquired < 0 || compareAndSetState(available, acquired))
                    return acquired;
            }
        }
    }

    // Sync 是 AQS 的子类
    abstract static class Sync extends AbstractQueuedSynchronizer {
        private final int permits;

        Sync(int permits) {
            this.permits = permits;
            setState(permits);
        }

        // 非公平模式的核心逻辑
        final int nonfairTryAcquireShared(int acquires) {
            for (;;) {
                int available = getState();
                int remaining = available - acquires;
                if (remaining < 0 ||
                    compareAndSetState(available, remaining))
                    return remaining;
            }
        }

        // 释放许可
        protected final boolean tryReleaseShared(int releases) {
            for (;;) {
                int current = getState();
                int next = current + releases;
                if (next < current) // overflow
                    throw new Error("Maximum permit count exceeded");
                if (compareAndSetState(current, next))
                    return true;
            }
        }
    }
}
```

**工作流程**：

1. 创建 `Semaphore(permits)` 时，AQS 的 state 被初始化为 `permits`（许可数量）。
2. 线程调用 `acquire()` 时，AQS 调用 `tryAcquireShared(arg)`。
   - `tryAcquireShared` 返回**负数**表示获取失败，线程被加入等待队列并阻塞。
   - 返回**非负数**表示获取成功，方法返回。
3. 线程调用 `release()` 时，AQS 调用 `tryReleaseShared(arg)`，将 `state` 增加，唤醒等待队列中的节点。

### 4.4 公平 vs 非公平

- **非公平模式（默认）**：`tryAcquire` 直接通过 CAS 抢锁，不检查等待队列。因此可能存在"插队"现象——新来的线程可能比等待队列中的老线程先获取到许可。
- **公平模式**：`tryAcquire` 先调用 `hasQueuedPredecessors()` 检查等待队列中是否有更早等待的线程。如果有，则乖乖排队，不会插队。

```java
// 公平模式示例
Semaphore fairSemaphore = new Semaphore(3, true);  // 公平

// 非公平模式示例
Semaphore unfairSemaphore = new Semaphore(3, false); // 非公平（默认）
```

**选择建议**：
- 如果对**吞吐量**要求高，使用**非公平模式**（默认），因为减少了很多不必要的排队开销。
- 如果对**公平性**有要求（如避免线程饥饿），使用**公平模式**。

### 4.5 完整代码示例

#### 示例一：实现连接池（限流）

```java
import java.util.concurrent.*;
import java.sql.*;

public class ConnectionPoolDemo {

    // 模拟最大连接数为 3 的数据库连接池
    private static final int POOL_SIZE = 3;
    private static final Semaphore semaphore = new Semaphore(POOL_SIZE);

    // 模拟的数据库连接
    static class DbConnection {
        private final int id;
        DbConnection(int id) { this.id = id; }
        public int getId() { return id; }
    }

    // 从连接池获取连接
    public static DbConnection getConnection() throws InterruptedException {
        semaphore.acquire();  // 获取许可
        return new DbConnection((int) (Math.random() * 1000));
    }

    // 归还连接
    public static void releaseConnection() {
        semaphore.release();
    }

    public static void main(String[] args) {
        int threadCount = 10;  // 10 个线程竞争 3 个连接

        CountDownLatch latch = new CountDownLatch(threadCount);

        ExecutorService executor = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final int taskId = i + 1;
            executor.submit(() -> {
                try {
                    System.out.println("任务 " + taskId + " 等待获取数据库连接...");
                    long start = System.currentTimeMillis();

                    DbConnection conn = getConnection();

                    System.out.println("任务 " + taskId + " 获取到连接 [id=" + conn.getId() + 
                            "]，耗时 " + (System.currentTimeMillis() - start) + "ms");

                    // 模拟使用连接 1-3 秒
                    Thread.sleep((long) (Math.random() * 2000) + 1000);

                    System.out.println("任务 " + taskId + " 释放连接 [id=" + conn.getId() + "]");
                    releaseConnection();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    latch.countDown();
                }
            });
        }

        try {
            latch.await();
            System.out.println("所有任务执行完毕！");
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        executor.shutdown();
    }
}
```

#### 示例二：接口限流（模拟 QPS 控制）

```java
import java.util.concurrent.*;

public class ApiRateLimitDemo {

    // 每秒最多允许 5 个请求
    private static final int MAX_QPS = 5;
    private static final Semaphore semaphore = new Semaphore(MAX_QPS);

    // 模拟限流的 API 调用
    public static String callApi(String apiName) throws InterruptedException {
        semaphore.acquire();  // 获取许可
        try {
            // 模拟 API 调用耗时 200ms
            Thread.sleep(200);
            return apiName + " 调用成功";
        } finally {
            semaphore.release();  // 释放许可
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int requestCount = 20;  // 模拟 20 个并发请求

        ExecutorService executor = Executors.newFixedThreadPool(requestCount);
        CountDownLatch latch = new CountDownLatch(requestCount);

        long startTime = System.currentTimeMillis();

        for (int i = 0; i < requestCount; i++) {
            final int reqId = i + 1;
            executor.submit(() -> {
                try {
                    String result = callApi("API-" + reqId);
                    System.out.println(result);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    latch.countDown();
                }
            });
        }

        latch.await();
        long duration = System.currentTimeMillis() - startTime;

        System.out.println("\n========== 统计 ==========");
        System.out.println("总请求数: " + requestCount);
        System.out.println("限流 QPS: " + MAX_QPS);
        System.out.println("总耗时: " + duration + "ms");
        System.out.println("实际 QPS: " + (requestCount * 1000.0 / duration));

        executor.shutdown();
    }
}
```

#### 示例三：tryAcquire 非阻塞获取

```java
import java.util.concurrent.*;

public class TryAcquireDemo {

    private static final Semaphore semaphore = new Semaphore(2);

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            final int taskId = i + 1;
            new Thread(() -> {
                // 非阻塞尝试获取许可
                if (semaphore.tryAcquire()) {
                    System.out.println("任务 " + taskId + " 成功获取许可，立即执行！");
                    try {
                        Thread.sleep(2000);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    } finally {
                        semaphore.release();
                    }
                } else {
                    System.out.println("任务 " + taskId + " 获取许可失败（无可用许可），放弃执行");
                }
            }).start();
        }
    }
}
```

---

## 五、Exchanger（线程间数据交换）

### 5.1 概念与使用场景

**Exchanger** 用于在两个线程之间**交换数据**。当一个线程调用 `exchange()` 方法后，它会阻塞，直到另一个线程也调用了 `exchange()` 方法，此时两个线程的数据会被**互换**，双方各自收到对方之前传入的数据。

**典型使用场景**：

1. **生产者-消费者数据传递**：一个线程生产数据，另一个线程消费数据，两者交换缓冲区。
2. **遗传算法**：在两个线程间交换个体进行交叉操作。
3. **校对数据**：例如需要将两个线程的数据进行比对时，可以交换数据后验证。

### 5.2 核心 API

```java
// 创建一个 Exchanger
Exchanger<V> exchanger = new Exchanger<>();

// 阻塞等待另一个线程交换数据
V exchange(V x) throws InterruptedException;

// 带超时版本的交换
V exchange(V x, long timeout, TimeUnit unit) throws InterruptedException, TimeoutException;
```

### 5.3 代码示例

```java
import java.util.concurrent.*;

public class ExchangerDemo {

    public static void main(String[] args) {
        Exchanger<String> exchanger = new Exchanger<>();

        Thread producer = new Thread(() -> {
            try {
                String data = "【生产者】数据-ABC";
                System.out.println("生产者准备交换: " + data);
                String received = exchanger.exchange(data);
                System.out.println("生产者收到: " + received);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }, "Producer");

        Thread consumer = new Thread(() -> {
            try {
                Thread.sleep(1000); // 确保生产者先调用 exchange
                String data = "【消费者】数据-XYZ";
                System.out.println("消费者准备交换: " + data);
                String received = exchanger.exchange(data);
                System.out.println("消费者收到: " + received);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }, "Consumer");

        producer.start();
        consumer.start();
    }
}
```

**运行结果**：
```
生产者准备交换: 【生产者】数据-ABC
消费者准备交换: 【消费者】数据-XYZ
生产者收到: 【消费者】数据-XYZ
消费者收到: 【生产者】数据-ABC
```

**注意**：`Exchanger` 只能用于**两个线程之间**的数据交换，如果只有一个线程调用 `exchange()`，则会一直阻塞。

---

## 六、Phaser（增强版 CyclicBarrier）

### 6.1 概念与使用场景

**Phaser**（阶段同步器）是 Java 7 引入的同步辅助类，是 `CyclicBarrier` 和 `CountDownLatch` 的**增强版**。它提供了更灵活的阶段（phase）管理：

- **动态注册**：线程可以在运行时动态注册/取消注册，不需要在构造时指定数量。
- **多阶段同步**：支持任意数量的阶段，每个阶段完成后自动进入下一阶段。
- **单次使用或循环使用**：可以配置为在所有阶段完成后自动 deregister，或者重用。

**典型使用场景**：

1. **多阶段并发任务**：如一个任务分为初始化阶段、处理阶段、收尾阶段，每个阶段都需要所有线程到达后同步。
2. **动态并发控制**：线程数量在运行时动态变化。
3. **批量任务处理**：处理 N 个任务，每批之间需要同步。

### 6.2 核心 API

```java
// 创建 Phaser
Phaser phaser = new Phaser();

// 创建并注册 parties 个参与者
Phaser phaser = new Phaser(int parties);

// 创建 parent 的子 Phaser
Phaser phaser = new Phaser(Phaser parent);

// 注册一个参与者（非阻塞）
int register();

// 批量注册
int bulkRegister(int parties);

// 到达并等待其他参与者
int arriveAndAwaitAdvance();

// 到达并注销（离开 Phaser）
int arriveAndDeregister();

// 获取当前阶段号
int getPhase();

// 等待当前阶段完成
int awaitAdvance(int phase);

// 等待进入下一阶段（可中断）
int awaitAdvanceInterruptibly(int phase) throws InterruptedException;

// 等待进入下一阶段（带超时）
int awaitAdvanceInterruptibly(int phase, long timeout, TimeUnit unit) throws InterruptedException, TimeoutException;
```

### 6.3 代码示例

```java
import java.util.concurrent.*;

public class PhaserDemo {

    public static void main(String[] args) throws InterruptedException {
        Phaser phaser = new Phaser(3);  // 3 个参与者

        ExecutorService executor = Executors.newFixedThreadPool(3);

        for (int i = 0; i < 3; i++) {
            final int participantId = i + 1;
            executor.submit(() -> {
                try {
                    // ===== 阶段 0：初始化 =====
                    System.out.println("参与者 " + participantId + " 正在初始化...");
                    Thread.sleep((long) (Math.random() * 1000