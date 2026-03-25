# volatile 原理与内存屏障 ⭐⭐⭐

## 面试题：volatile 的作用和原理是什么？

### 核心回答

volatile 是 Java 中的轻量级同步机制，保证变量的**可见性**和**有序性**，但不保证**原子性**。

### volatile 的三大特性

| 特性 | 说明 | 实现机制 |
|------|------|---------|
| **可见性** | 一个线程修改，其他线程立即可见 | 内存屏障 + 缓存一致性协议 |
| **有序性** | 禁止指令重排序 | 内存屏障 |
| **原子性** | ❌ 不保证 | 需要配合 synchronized 或 CAS |

### 可见性原理

#### Java 内存模型（JMM）

```
┌─────────────┐         ┌─────────────┐
│   Thread A  │         │   Thread B  │
│  ┌───────┐  │         │  ┌───────┐  │
│  │ 本地  │  │         │  │ 本地  │  │
│  │ 内存A │  │         │  │ 内存B │  │
│  └───┬───┘  │         │  └───┬───┘  │
│      │      │         │      │      │
└──────┼──────┘         └──────┼──────┘
       │                       │
       └───────────┬───────────┘
                   │
            ┌──────┴──────┐
            │   主内存     │
            │  (共享变量)  │
            └─────────────┘
```

**问题**：线程修改变量后，其他线程可能看不到最新值

**volatile 解决**：
- **写操作**：立即刷新到主内存
- **读操作**：直接从主内存读取

```java
// volatile 写操作
volatile int x = 0;

Thread A:
x = 1;  // 1. 修改本地内存 2. 立即刷新到主内存

Thread B:
int y = x;  // 直接从主内存读取最新值
```

### 内存屏障（Memory Barrier）

内存屏障是一种 CPU 指令，用于确保指令的执行顺序。

#### 四种内存屏障

| 屏障类型 | 说明 | 作用 |
|---------|------|------|
| **LoadLoad** | 读-读屏障 | 禁止读-读重排序 |
| **StoreStore** | 写-写屏障 | 禁止写-写重排序 |
| **LoadStore** | 读-写屏障 | 禁止读-写重排序 |
| **StoreLoad** | 写-读屏障 | 禁止写-读重排序（全能屏障）|

#### volatile 的内存屏障插入策略

```java
// volatile 写操作
instance = new Singleton();  // volatile 变量

// 实际执行：
// StoreStore 屏障（防止普通写和 volatile 写重排序）
// volatile 写
// StoreLoad 屏障（防止 volatile 写和后续 volatile 读/写重排序）
```

```java
// volatile 读操作
if (instance != null) {  // volatile 变量

// 实际执行：
// LoadLoad 屏障（防止 volatile 读和普通读重排序）
// LoadStore 屏障（防止 volatile 读和普通写重排序）
// volatile 读
```

### 经典应用场景

#### 1. 状态标志位

```java
public class TaskRunner {
    private volatile boolean running = true;
    
    public void stop() {
        running = false;  // 所有线程立即可见
    }
    
    public void run() {
        while (running) {  // 读取最新状态
            // 执行任务
        }
    }
}
```

#### 2. 双重检查锁定（DCL）

```java
public class Singleton {
    private volatile static Singleton instance;
    
    public static Singleton getInstance() {
        if (instance == null) {                    // 第1次检查
            synchronized (Singleton.class) {
                if (instance == null) {            // 第2次检查
                    instance = new Singleton();    // volatile 禁止重排序
                }
            }
        }
        return instance;
    }
}
```

**为什么需要 volatile？**

```java
// instance = new Singleton() 实际分三步：
// 1. 分配内存空间
// 2. 初始化对象
// 3. 将引用指向内存地址

// 如果没有 volatile，可能重排序为 1-3-2：
// 其他线程可能拿到未完全初始化的对象！
```

#### 3. 读写锁的读操作

```java
public class Counter {
    private volatile long value;
    
    public void increment() {
        // 写操作需要同步
        synchronized (this) {
            value++;
        }
    }
    
    public long get() {
        // 读操作无需同步，volatile 保证可见性
        return value;
    }
}
```

### volatile 不保证原子性

```java
public class VolatileTest {
    private volatile int count = 0;
    
    public void increment() {
        count++;  // 非原子操作！
    }
    
    public static void main(String[] args) throws InterruptedException {
        VolatileTest test = new VolatileTest();
        
        // 10 个线程各执行 1000 次 increment
        for (int i = 0; i < 10; i++) {
            new Thread(() -> {
                for (int j = 0; j < 1000; j++) {
                    test.increment();
                }
            }).start();
        }
        
        Thread.sleep(3000);
        System.out.println(test.count);  // 结果可能小于 10000！
    }
}
```

**原因**：`count++` 实际上是三个操作：
1. 读取 count 值
2. 加 1
3. 写回 count

volatile 不能保证这三步的原子性。

**解决方案**：

```java
// 方案1：synchronized
public synchronized void increment() {
    count++;
}

// 方案2：AtomicInteger
private AtomicInteger count = new AtomicInteger(0);
public void increment() {
    count.incrementAndGet();  // CAS 保证原子性
}

// 方案3：LongAdder（高并发推荐）
private LongAdder count = new LongAdder();
public void increment() {
    count.increment();
}
```

### volatile vs synchronized

| 特性 | volatile | synchronized |
|------|---------|--------------|
| 可见性 | ✓ | ✓ |
| 原子性 | ✗ | ✓ |
| 有序性 | ✓ | ✓ |
| 阻塞 | 不会阻塞线程 | 会阻塞线程 |
| 适用场景 | 单一变量的读写 | 复合操作 |
| 性能 | 轻量级 | 重量级 |

### happens-before 规则

volatile 变量的读写操作满足 happens-before 关系：

```java
// volatile 写 happens-before volatile 读

Thread A:
volatile int x = 1;  // 写操作

Thread B:
int y = x;  // 读操作，一定能看到 x = 1

// 同时，Thread A 在写之前的所有操作对 Thread B 可见
```

### CPU 缓存一致性协议（MESI）

volatile 的可见性实现依赖于 CPU 的缓存一致性协议：

```
MESI 四种状态：
- M（Modified）：已修改，数据被修改，与主内存不一致
- E（Exclusive）：独占，数据只在当前缓存，与主内存一致
- S（Shared）：共享，数据在多个缓存中，与主内存一致
- I（Invalid）：无效，数据已失效，需要重新加载

volatile 写：将数据状态变为 M，并刷新到主内存
volatile 读：如果状态为 I，从主内存重新加载
```

### 高频面试题

**Q1: volatile 能保证线程安全吗？**

- **单一操作**：volatile 变量的读写是线程安全的
- **复合操作**：如 `i++` 不是线程安全的，需要 synchronized 或 Atomic 类

**Q2: 为什么 volatile 能解决 DCL 的单例问题？**

```java
// 禁止了以下重排序：
// 1. 分配内存
// 2. 初始化对象  ← 这两步不能重排序
// 3. 引用赋值      ←

// 如果没有 volatile：
// 线程 A 执行：1-3-2（重排序后）
// 线程 B 看到 instance 不为 null，但对象未初始化完成！
```

**Q3: volatile 和 Atomic 类的区别？**

```java
// volatile：保证可见性和有序性
private volatile int count;

// AtomicInteger：保证原子性
private AtomicInteger count = new AtomicInteger(0);

// 复合操作需要 Atomic
public void addAndGet(int delta) {
    count.addAndGet(delta);  // 原子操作
}
```

**Q4: 什么场景不适合用 volatile？**

1. **需要原子性的场景**：如计数器递增
2. **复杂的状态判断**：
```java
// 错误用法
volatile int a = 0;
volatile int b = 0;

// 无法保证 a 和 b 的一致性
if (a == b) {  // 可能读到不一致的值
    // ...
}
```

### 最佳实践

```java
// 1. 使用 volatile 作为状态标志
private volatile boolean stopped = false;

public void stop() {
    stopped = true;
}

public void doWork() {
    while (!stopped) {
        // 工作
    }
}

// 2. 配合 synchronized 使用
private volatile int value;

public synchronized void increment() {
    value++;
}

public int get() {
    return value;  // 无需同步，volatile 保证可见性
}

// 3. 使用 Atomic 类替代 volatile（需要原子性时）
private AtomicInteger counter = new AtomicInteger(0);

public void increment() {
    counter.incrementAndGet();
}
```

---

**参考链接：**
- [深入理解volatile与synchronized](https://so.html5.qq.com/page/real/search_news?docid=70000021_41368735b3454852)
- [volatile关键字最全原理剖析-SegmentFault](https://segmentfault.com/a/1190000045398760)
