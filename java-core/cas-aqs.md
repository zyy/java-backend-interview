# CAS 与 AQS 原理详解 ⭐⭐⭐

## 面试题：说说 CAS 和 AQS 的原理

### 核心回答

**CAS（Compare And Swap）**是一种无锁原子操作，通过比较内存值和预期值来决定是否更新。**AQS（AbstractQueuedSynchronizer）**是 Java 并发包的基石，提供了实现锁和同步器的框架。

---

## 一、CAS 原理

### 什么是 CAS？

CAS 包含三个操作数：
- **V**：内存地址的值
- **A**：预期值
- **B**：新值

**操作逻辑**：当且仅当 V == A 时，将 V 更新为 B，否则不做任何操作。

```java
// 伪代码
boolean compareAndSwap(V, A, B) {
    if (V == A) {
        V = B;
        return true;
    }
    return false;
}
```

### CAS 的硬件支持

CAS 是 CPU 的原子指令（x86 的 `cmpxchg` 指令），保证了操作的原子性。

```java
// Unsafe 类中的 CAS 方法
public final native boolean compareAndSwapInt(Object o, long offset, 
                                               int expected, int x);
```

### AtomicInteger 源码分析

```java
public class AtomicInteger extends Number implements java.io.Serializable {
    private volatile int value;  // volatile 保证可见性
    
    private static final Unsafe unsafe = Unsafe.getUnsafe();
    private static final long valueOffset;
    
    static {
        try {
            valueOffset = unsafe.objectFieldOffset(
                AtomicInteger.class.getDeclaredField("value"));
        } catch (Exception ex) { throw new Error(ex); }
    }
    
    // CAS 自增
    public final int incrementAndGet() {
        return unsafe.getAndAddInt(this, valueOffset, 1) + 1;
    }
    
    // Unsafe 中的实现
    public final int getAndAddInt(Object o, long offset, int delta) {
        int v;
        do {
            v = getIntVolatile(o, offset);  // 获取当前值
        } while (!compareAndSwapInt(o, offset, v, v + delta));  // CAS 更新
        return v;
    }
}
```

### CAS 的问题

#### 1. ABA 问题

**问题描述**：
- 线程 1：读取值为 A
- 线程 2：将 A 改为 B，再改回 A
- 线程 1：CAS 成功，但实际上值已经被修改过

**解决方案**：使用版本号（AtomicStampedReference）

```java
AtomicStampedReference<Integer> ref = 
    new AtomicStampedReference<>(100, 0);

// 更新时需要比较值和版本号
ref.compareAndSet(100, 200, 0, 1);
```

#### 2. 自旋开销

CAS 失败会不断重试，CPU 开销大。

**优化**：
- 自适应自旋：根据历史成功率调整重试次数
- 退避策略：失败后短暂休眠

#### 3. 只能保证单个变量的原子性

对于多个变量的复合操作，需要使用 synchronized 或 AtomicReference。

---

## 二、AQS 原理

### AQS 概述

AQS（AbstractQueuedSynchronizer）是 Java 并发包的核心框架，提供了：
- 同步状态的管理（state）
- 线程的排队和阻塞
- 线程的唤醒机制

**基于 AQS 实现的类**：
- ReentrantLock
- ReentrantReadWriteLock
- CountDownLatch
- Semaphore
- CyclicBarrier

### AQS 核心结构

```java
public abstract class AbstractQueuedSynchronizer 
    extends AbstractOwnableSynchronizer {
    
    // 同步状态
    private volatile int state;
    
    // 等待队列头节点
    private transient volatile Node head;
    
    // 等待队列尾节点
    private transient volatile Node tail;
    
    // 独占线程
    private transient Thread exclusiveOwnerThread;
}

// 队列节点
static final class Node {
    // 共享模式
    static final Node SHARED = new Node();
    
    // 独占模式
    static final Node EXCLUSIVE = null;
    
    // 等待状态
    volatile int waitStatus;
    static final int CANCELLED =  1;   // 取消
    static final int SIGNAL    = -1;   // 后继节点需要唤醒
    static final int CONDITION = -2;   // 在条件队列中
    static final int PROPAGATE = -3;   // 共享模式传播
    
    volatile Node prev;       // 前驱节点
    volatile Node next;       // 后继节点
    volatile Thread thread;   // 绑定的线程
}
```

### 独占模式获取锁（acquire）

```java
public final void acquire(int arg) {
    // 1. 尝试获取锁
    if (!tryAcquire(arg) &&
        // 2. 获取失败，加入等待队列
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        // 3. 如果被中断，恢复中断状态
        selfInterrupt();
}

// 加入等待队列
private Node addWaiter(Node mode) {
    Node node = new Node(Thread.currentThread(), mode);
    
    Node pred = tail;
    if (pred != null) {
        node.prev = pred;
        // CAS 设置尾节点
        if (compareAndSetTail(pred, node)) {
            pred.next = node;
            return node;
        }
    }
    // 队列为空或 CAS 失败，进入完整入队流程
    enq(node);
    return node;
}

// 在队列中等待获取锁
final boolean acquireQueued(final Node node, int arg) {
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            
            // 前驱是头节点，尝试获取锁
            if (p == head && tryAcquire(arg)) {
                setHead(node);  // 获取成功，成为头节点
                p.next = null;  // 帮助 GC
                failed = false;
                return interrupted;
            }
            
            // 判断是否需要阻塞
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}
```

### 独占模式释放锁（release）

```java
public final boolean release(int arg) {
    // 1. 尝试释放锁
    if (tryRelease(arg)) {
        Node h = head;
        // 2. 唤醒后继节点
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);
        return true;
    }
    return false;
}

// 唤醒后继节点
private void unparkSuccessor(Node node) {
    int ws = node.waitStatus;
    if (ws < 0)
        compareAndSetWaitStatus(node, ws, 0);
    
    Node s = node.next;
    if (s == null || s.waitStatus > 0) {
        s = null;
        // 从尾部向前找有效的后继节点
        for (Node t = tail; t != null && t != node; t = t.prev)
            if (t.waitStatus <= 0)
                s = t;
    }
    if (s != null)
        LockSupport.unpark(s.thread);
}
```

### 共享模式

```java
// 共享模式获取
public final void acquireShared(int arg) {
    if (tryAcquireShared(arg) < 0)
        doAcquireShared(arg);
}

// 共享模式释放
public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {
        doReleaseShared();  // 唤醒多个后继节点
        return true;
    }
    return false;
}
```

### AQS 的模板方法模式

子类只需实现特定方法：

```java
// 独占模式需要实现的方法
protected boolean tryAcquire(int arg);      // 获取锁
protected boolean tryRelease(int arg);      // 释放锁

// 共享模式需要实现的方法
protected int tryAcquireShared(int arg);    // 获取共享锁
protected boolean tryReleaseShared(int arg); // 释放共享锁

// 判断是否是独占线程
protected boolean isHeldExclusively();
```

### ReentrantLock 实现示例

```java
public class ReentrantLock implements Lock, java.io.Serializable {
    
    private final Sync sync;
    
    // 同步器实现
    abstract static class Sync extends AbstractQueuedSynchronizer {
        
        // 非公平锁获取
        final boolean nonfairTryAcquire(int acquires) {
            final Thread current = Thread.currentThread();
            int c = getState();
            
            if (c == 0) {
                // 直接 CAS 尝试获取
                if (compareAndSetState(0, acquires)) {
                    setExclusiveOwnerThread(current);
                    return true;
                }
            }
            else if (current == getExclusiveOwnerThread()) {
                // 重入
                int nextc = c + acquires;
                if (nextc < 0)
                    throw new Error("Maximum lock count exceeded");
                setState(nextc);
                return true;
            }
            return false;
        }
        
        // 释放锁
        protected final boolean tryRelease(int releases) {
            int c = getState() - releases;
            if (Thread.currentThread() != getExclusiveOwnerThread())
                throw new IllegalMonitorStateException();
            boolean free = false;
            if (c == 0) {
                free = true;
                setExclusiveOwnerThread(null);
            }
            setState(c);
            return free;
        }
    }
}
```

### 高频面试题

**Q1: CAS 和 synchronized 的区别？**

| 特性 | CAS | synchronized |
|------|-----|--------------|
| 实现 | 硬件原子指令 | JVM 监视器锁 |
| 阻塞 | 非阻塞（自旋） | 阻塞 |
| 开销 | 低（无上下文切换） | 高（可能涉及内核态） |
| 适用场景 | 低竞争、短操作 | 高竞争、长操作 |
| 问题 | ABA、自旋开销 | 线程切换开销 |

**Q2: AQS 为什么使用双向链表？**

1. **方便取消节点**：需要找到前驱节点修改 next 指针
2. **支持从尾部向前遍历**：unparkSuccessor 方法需要
3. **方便插入**：在尾部插入时需要修改前驱的 next

**Q3: AQS 如何保证可见性？**

```java
// 使用 volatile 修饰关键字段
private volatile int state;
private transient volatile Node head;
private transient volatile Node tail;

// 使用 CAS 操作保证原子性
compareAndSetState(expected, update);
compareAndSetTail(pred, node);
```

**Q4: 公平锁和非公平锁的区别？**

```java
// 公平锁：先检查队列是否有等待线程
protected final boolean tryAcquire(int acquires) {
    final Thread current = Thread.currentThread();
    int c = getState();
    if (c == 0) {
        // 关键区别：先检查队列是否为空
        if (!hasQueuedPredecessors() &&
            compareAndSetState(0, acquires)) {
            setExclusiveOwnerThread(current);
            return true;
        }
    }
    // ...
}

// 非公平锁：直接 CAS 尝试获取
final boolean nonfairTryAcquire(int acquires) {
    final Thread current = Thread.currentThread();
    int c = getState();
    if (c == 0) {
        // 直接 CAS，不检查队列
        if (compareAndSetState(0, acquires)) {
            setExclusiveOwnerThread(current);
            return true;
        }
    }
    // ...
}
```

**Q5: 什么是 CLH 队列？**

CLH（Craig, Landin, and Hagersten）是一种基于链表的可扩展、高性能公平锁。

AQS 借鉴了 CLH 的思想：
- 使用双向链表组织等待线程
- 每个节点自旋检查前驱节点的状态
- 前驱释放锁时唤醒后继

### 最佳实践

```java
// 1. 低竞争场景使用 Atomic 类
private AtomicInteger counter = new AtomicInteger(0);

// 2. 高竞争场景使用 LongAdder
private LongAdder longAdder = new LongAdder();

// 3. 自定义同步器继承 AQS
public class CustomLock extends AbstractQueuedSynchronizer {
    @Override
    protected boolean tryAcquire(int arg) {
        if (compareAndSetState(0, 1)) {
            setExclusiveOwnerThread(Thread.currentThread());
            return true;
        }
        return false;
    }
    
    @Override
    protected boolean tryRelease(int arg) {
        setExclusiveOwnerThread(null);
        setState(0);
        return true;
    }
}
```

---

**参考链接：**
- [Java面试题之AQS-CSDN](https://blog.csdn.net/yunkongbian2616/article/details/140843963)
- [AQS抽象队列同步器及工作原理解析-脚本之家](https://www.jb51.net/article/242201.htm)
