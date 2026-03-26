---
layout: default
title: Java 内存模型（JMM）与 happens-before 详解 ⭐⭐⭐
---
# Java 内存模型（JMM）与 happens-before 详解 ⭐⭐⭐

## 面试题：什么是 Java 内存模型？happens-before 规则是什么？

### 核心回答

Java 内存模型（Java Memory Model，简称 **JMM**）是一种规范，定义了 JVM 如何与计算机内存（RAM）交互，规定了线程之间共享变量的**可见性**、**有序性**和**原子性**。

**happens-before** 是 JMM 中最核心的概念，它定义了跨线程操作的偏序关系：如果操作 A happens-before 操作 B，那么 A 的执行结果对 B 可见，且 A 的执行顺序在 B 之前。

### 本章结构

```
1. JMM 抽象结构：主内存 vs 工作内存
2. 内存可见性问题：缓存不一致的根源
3. 三大特性：原子性、可见性、有序性
4. happens-before 规则（8 条）详解
5. 重排序：编译器/CPU 重排与内存屏障
6. volatile 的内存语义
7. synchronized 的内存语义
8. final 域的内存语义
9. 高频面试题
```

---

## 一、JMM 抽象结构：主内存 vs 工作内存

### 1.1 什么是 JMM？

JMM（Java Memory Model）是 Java 虚拟机（JVM）规范的一部分，定义了 Java 线程与主内存之间的抽象关系。

> **为什么需要 JMM？**
>
> Java 代码运行在 JVM 上，而 JVM 运行在操作系统之上，最终跑在 CPU 上。CPU 有多级缓存（寄存器、L1/L2/L3 缓存），操作系统有进程内存空间。这些复杂的硬件结构导致线程间共享变量的访问变得不可预测。JMM 就是为了**屏蔽底层硬件差异**，给 Java 程序员一个统一的内存模型。

### 1.2 JMM 抽象模型

```
┌──────────────────────────────────────────────────────────┐
│                         JVM 进程                         │
│                                                          │
│   ┌─────────────┐                      ┌─────────────┐  │
│   │  Thread A   │                      │  Thread B   │  │
│   │ ┌─────────┐ │                      │ ┌─────────┐ │  │
│   │ │工作内存A│ │                      │ │工作内存B│ │  │
│   │ │(缓存)   │ │                      │ │(缓存)   │ │  │
│   │ └────┬────┘ │                      │ └────┬────┘ │  │
│   │      │      │                      │      │      │  │
│   └──────┼──────┘                      └──────┼──────┘  │
│          │                                    │          │
└──────────┼────────────────────────────────────┼──────────┘
           │            JMM 抽象               │
           │  ←──── load/store 抽象操作 ────→ │
           │                                    │
    ┌──────┴────────────────────────────────────┴──────┐
    │                    主内存                         │
    │         (物理 RAM / 堆内存区域)                   │
    │                                                   │
    │   ┌─────────┐  ┌─────────┐  ┌─────────┐          │
    │   │变量 x   │  │变量 y   │  │对象 obj │          │
    │   └─────────┘  └─────────┘  └─────────┘          │
    └───────────────────────────────────────────────────┘
```

**关键概念：**

| 概念 | 说明 |
|------|------|
| **主内存（Main Memory）** | 所有线程共享的内存区域，对应物理 RAM 或 JVM 堆内存 |
| **工作内存（Working Memory）** | 每个线程私有的内存区域，保存该线程使用到的变量的副本（相当于 CPU 缓存） |
| **load 操作** | 将主内存变量读取到工作内存 |
| **store 操作** | 将工作内存变量写回主内存 |
| **read 操作** | 工作内存中读取变量（供 use 使用） |
| **write 操作** | 工作内存中写入变量（供 assign 赋值） |

### 1.3 线程与内存的交互流程

```java
// Java 代码
int x = 10;  // 线程对变量的写操作

// 实际在 JMM 中的执行流程（简化版）：
// 1. assign：线程在工作内存中给变量 x 赋值 10
// 2. store：将 x = 10 从工作内存写入主内存
// 3. write：将主内存中的 x 值标记为已更新

// 其他线程读取 x 的流程：
// 1. read：从主内存读取最新的 x 值
// 2. load：将 x 值加载到工作内存
// 3. use：线程使用工作内存中的 x 值
```

### 1.4 为什么需要工作内存？

工作内存的存在是为了**提高性能**：

- **速度差异**：CPU 访问寄存器和 L1 缓存的速度比访问 RAM 快 100-1000 倍
- **减少冲突**：每个线程有独立的工作内存，避免频繁访问主内存造成总线竞争
- **线程隔离**：工作内存是线程私有的，提供了基本的线程隔离

**但这也带来了问题：** 一个线程修改了变量，什么时候才能被其他线程看到？

---

## 二、内存可见性问题：缓存不一致的根源

### 2.1 可见性问题的本质

**可见性（Visibility）**：一个线程对共享变量的修改，何时对其他线程可见。

```java
public class VisibilityProblem {
    private boolean flag = false;

    // 线程 A：写入者
    public void writer() {
        flag = true;  // 修改 flag
        System.out.println("Writer finished");
    }

    // 线程 B：读取者
    public void reader() {
        while (!flag) {  // 一直循环
            // 线程 B 可能永远看不到 flag = true
        }
        System.out.println("Reader sees flag = true");
    }
}
```

**为什么线程 B 可能看不到 flag 的更新？**

```
时间线：
                 线程 A                    线程 B
                  │                         │
    flag = false  │                         │
    (主内存)       │                         │
                  │                         │
    flag = true   │                         │
    (写回主内存?)   │                         │
                  │                         │
    CPU缓存A更新   │                         │
    但 CPU缓存B    │── read flag ───────────→│ 读到旧值 false！
                  │   (从CPU缓存B读)         │ 循环继续！
                  │                         │
```

### 2.2 硬件层面的缓存一致性

现代 CPU 通常使用 **MESI 缓存一致性协议**来保证缓存一致性：

```
MESI 四种状态：

┌─────────┬────────────────────────────────────────┐
│ 状态     │ 含义                                    │
├─────────┼────────────────────────────────────────┤
│ M (Modified) │ 已修改：该行数据被当前处理器修改，  │
│             │ 与主内存不一致，且是唯一有效副本      │
├─────────┼────────────────────────────────────────┤
│ E (Exclusive)│ 独占：该行数据只存在于当前处理器缓存 │
│             │ 中，且与主内存一致                    │
├─────────┼────────────────────────────────────────┤
│ S (Shared)   │ 共享：该行数据在多个处理器缓存中都   │
│             │ 有副本，且与主内存一致                │
├─────────┼────────────────────────────────────────┤
│ I (Invalid)  │ 无效：该行数据在当前缓存中无效，    │
│             │ 需要从主内存或其他缓存重新加载        │
└─────────┴────────────────────────────────────────┘

状态转换：
- Modified  → 被其他缓存 read → 总线 flush，主内存更新 → Shared
- Exclusive → 其他缓存 write  → Invalid
- Shared    → 其他缓存 write  → Invalid
- Invalid   → cache miss      → 从主内存或总线读取 → Shared/Exclusive
```

### 2.3 为什么 MESI 不够？还需要 volatile？

虽然 MESI 能保证**缓存一致性**，但它不能保证**操作顺序**：

```java
// 线程 A
x = 1;          // Store 1
flag = true;   // Store 2

// 线程 B
if (flag) {    // Load flag
    System.out.println(x);  // Load x
}
```

即使 MESI 保证 x 和 flag 的值最终一致，**CPU 和编译器可能重排序指令**，导致线程 B 可能看到 `flag = true` 但 `x = 0`。

这就是 **可见性 + 有序性** 的双重问题。

### 2.4 内存可见性问题的常见场景

#### 场景 1：循环无法退出

```java
public class BusyLoop {
    private static boolean done = false;

    public static void main(String[] args) throws InterruptedException {
        // 线程 1：修改 done
        new Thread(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) {}
            done = true;
        }).start();

        // 线程 2：等待 done
        while (!done) {
            // 理论上应该退出，但可能永远循环！
        }
        System.out.println("Done!");
    }
}
```

#### 场景 2：对象逃逸

```java
public class ObjectEscape {
    private int value = 0;
    private static ObjectEscape instance;

    public static void create() {
        instance = new ObjectEscape();  // 逸出！
        instance.value = 42;
    }
}
// 如果指令重排序，可能导致其他线程看到 value = 0 的半初始化对象
```

#### 场景 3：双重检查锁定的陷阱

```java
public class DCL {
    private static DCL instance;

    public static DCL getInstance() {
        if (instance == null) {          // 线程 B 可能跳过此处
            synchronized (DCL.class) {
                if (instance == null) {
                    instance = new DCL(); // 可能返回未初始化完成的对象
                }
            }
        }
        return instance;
    }
}
```

---

## 三、三大特性：原子性、可见性、有序性

JMM 围绕三个核心特性展开，这三个特性正是多线程编程中最容易出错的地方。

### 3.1 原子性（Atomicity）

**定义**：一个操作或多个操作要么全部执行，要么全部不执行，执行过程不会被任何因素打断。

```java
// 原子操作
x = 1;           // 基本类型赋值
y = obj.field;   // 引用赋值

// 非原子操作
x++;             // 实际是：read → increment → write
obj.field = 1;   // 如果 obj 引用发生改变，不安全
i = i + 1;       // 复合操作
```

**JMM 对原子性的保证：**

| 操作 | 原子性保证 | 说明 |
|------|-----------|------|
| 基本类型的读写 | ✓ JMM 保证 | `read`、`write`、`assign`、`load`、`store`、`putfield`、`getfield` 等 |
| `synchronized` 修饰的方法/块 | ✓ JVM 保证 | 互斥访问 |
| `java.util.concurrent.atomic` 包 | ✓ CAS 保证 | 原子变量类 |
| 普通字段的读写 | ✗ 可能被拆分 | `long`、`double` 在 32 位 JVM 中可能非原子 |

**注意：`long` 和 `double` 的原子性**

```java
public class LongDoubleDemo {
    // 在 32 位 JVM 中，下面的操作可能非原子：
    private long value;    // 可能读到高 32 位和低 32 位不一致的值
    private double d;      // 同理

    // 解决方案 1：加 synchronized
    private synchronized void setValue(long v) { value = v; }
    private synchronized long getValue() { return value; }

    // 解决方案 2：使用 volatile（Java 1.5+ 保证原子性）
    private volatile long value2;
}
```

> **Java 1.5+ 对 `volatile long/double` 的保证**：JMM 将 `volatile long` 和 `volatile double` 的读写操作规定为原子操作。

### 3.2 可见性（Visibility）

**定义**：当一个线程修改了共享变量的值，其他线程能立即看到这个修改。

```
可见性问题演示：

┌─────────────────────────────────────────────────────────┐
│  线程 A 工作内存          主内存           线程 B 工作内存  │
│                                                         │
│  ┌──────────────┐      ┌──────────────┐   ┌────────────┐│
│  │  x = 1       │      │   x = 0       │   │  (无缓存)  ││
│  │  (修改)      │ ───→ │  (更新为 1)   │   │            ││
│  └──────────────┘      └──────────────┘   └────────────┘│
│                                                         │
│        刷新延迟：其他线程可能继续读取旧值 x = 0           │
└─────────────────────────────────────────────────────────┘

解决可见性问题的方式：
1. volatile：保证写操作后立即刷新到主内存，读操作直接读主内存
2. synchronized：unlock 前必须 flush 到主内存
3. final：构造方法结束后 final 域对其他线程可见（需正确构造）
```

### 3.3 有序性（Ordering）

**定义**：程序执行的顺序按照代码的先后顺序执行，但在编译器和 CPU 优化下，可能发生指令重排序。

```java
int a = 0;
boolean flag = false;

// 线程 A
a = 1;         // 操作 1
flag = true;   // 操作 2

// 线程 B
if (flag) {    // 操作 3
    // 这里一定能读到 a = 1 吗？
    System.out.println(a);  // 操作 4
}
```

如果发生重排序：

```java
// 线程 A 可能被重排为：
flag = true;   // 先执行
a = 1;         // 后执行

// 线程 B 执行时：
// flag = true → 进入 if → a 可能还是 0！（没来得及被 A 赋值）
```

**三种重排序类型：**

| 重排序类型 | 主体 | 说明 |
|-----------|------|------|
| **编译器重排序** | JVM 编译器 | 调整无依赖关系的语句顺序 |
| **CPU 重排序** | 处理器 | 指令流水线、记忆单元重排 |
| **内存重排序** | CPU 缓存 | 存储/加载操作顺序与程序顺序不同 |

### 3.4 三大特性的相互关系

```
                    ┌─────────────────┐
                    │   Java 内存模型   │
                    │      (JMM)       │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │   原子性     │   │   可见性     │   │   有序性     │
   │             │   │             │   │             │
   │ x = 1       │   │ volatile    │   │ volatile    │
   │ synchronized│   │ synchronized│   │ synchronized│
   │ CAS         │   │ final       │   │ volatile    │
   └─────────────┘   └─────────────┘   └─────────────┘
```

**synchronized** 是唯一能同时保证原子性、可见性和有序性的方式，但性能开销较大。

**volatile** 能保证可见性和有序性，但不保证原子性。

---

## 四、happens-before 规则（8 条）详解

### 4.1 什么是 happens-before？

**happens-before**（先行发生原则）是 JMM 中定义的两个操作之间的偏序关系，是判断数据是否存在竞争、线程是否安全的重要依据。

> **关键理解**：如果操作 A happens-before 操作 B，那么：
> 1. A 的执行结果对 B 可见
> 2. A 的执行顺序在 B 之前
> 3. **但不是说 A 必须在 B 之前执行**，而是说 JMM 保证 A 的效果对 B 可见

**形式化定义：**

```
在 JMM 中，如果操作 A happens-before 操作 B，那么：
- JMM 将允许重排序（如果重排序后执行结果一致）
- JMM 将禁止重排序（如果重排序会改变执行结果）

简言之：happens-before 规定了哪些重排序是合法的，哪些是非法的。
```

### 4.2 八条核心规则

#### 规则一：程序顺序规则（Program Order Rule）

> **同一个线程中，按照程序代码的书写顺序，前面的操作 happens-before 后面的操作。**

```java
int a = 1;      // 1. happens-before 2.
int b = 2;      // 2. happens-before 3.
int c = a + b;  // 3.

Thread A:
x = 1;          // ① happens-before ②
y = 2;          // ② happens-before ③
z = x + y;      // ③

// 注意：这里说的是单个线程内的有序性
// 编译器/CPU 可以重排 ① ② ③，只要重排后结果一致
```

#### 规则二：监视器锁规则（Monitor Lock Rule）

> **同一个锁的 unlock 操作 happens-before 后续对这个锁的 lock 操作。**

```java
synchronized (lock) {
    // 临界区代码
    x = 100;    // 线程 A 在临界区内修改
}               // unlock

// ... 其他线程 ...

synchronized (lock) {
    // 线程 B 进入临界区
    int val = x;  // 一定能读到线程 A 修改后的值 100
}
```

**等价于：**

```java
// 线程 A
lock.lock();         // 获取锁
x = 100;              // 修改共享变量
lock.unlock();        // 释放锁  happens-before

// 线程 B
lock.lock();          // 获取锁  happens-before
int val = x;          // 一定能看到 x = 100
lock.unlock();
```

#### 规则三：volatile 变量规则（Volatile Variable Rule）

> **对 volatile 变量的写操作 happens-before 后续对该变量的读操作。**

```java
volatile int x = 0;

// 线程 A
x = 1;           // 写 volatile

// 线程 B
int y = x;       // 读 volatile

// 线程 B 一定能看到 x = 1
// 线程 A 在写 x 之前的所有操作对线程 B 都可见
```

这是 volatile 保证可见性的核心依据。

#### 规则四：线程启动规则（Thread Start Rule）

> **Thread.start() 调用 happens-before 被启动线程中的任何操作。**

```java
Thread B = new Thread(() -> {
    // 这里能读到 done = false 吗？
    while (!done) { }
    System.out.println("Done!");
});

done = true;         // 线程 A
B.start();           // happens-before

// 线程 B 启动后，一定能看到 done = true
```

#### 规则五：线程终止规则（Thread Termination Rule）

> **线程中的所有操作 happens-before 其他线程检测到该线程终止。**

```java
Thread B = new Thread(() -> {
    x = 100;
    y = 200;
});

B.start();
B.join();  // 等待 B 终止

// 在主线程中：
// B 线程的所有操作对主线程可见
// 一定能读到 x = 100, y = 200
```

**等价于：**

```java
// 线程 A（主线程）
B.start();          // 启动线程 B

// ... 其他代码 ...

B.join();          // 等待 B 终止
// 此时，B 线程的所有操作已完成
// B 线程对 x, y 的修改对主线程可见
System.out.println(x);  // 输出 100
System.out.println(y);  // 输出 200
```

#### 规则六：线程中断规则（Thread Interruption Rule）

> **对 Thread.interrupt() 的调用 happens-before 被中断线程检测到中断事件（抛出 InterruptedException 或调用 isInterrupted()）。**

```java
Thread B = new Thread(() -> {
    while (!Thread.currentThread().isInterrupted()) {
        // 业务逻辑
    }
});

B.interrupt();  // 主线程调用

// B 线程中，isInterrupted() 返回 true
// 或抛出 InterruptedException
```

#### 规则七：对象终结规则（Finalizer Rule）

> **一个对象的构造函数中的操作 happens-before 它的 finalize() 方法的开始。**

```java
public class MyObject {
    private int value = 10;  // 在构造方法中赋值

    @Override
    protected void finalize() throws Throwable {
        // 这里一定能读到 value = 10
        System.out.println(value);
    }
}

// 原因：构造函数结束 happens-before finalize() 开始
// 但注意：finalize() 的执行时机不确定，只是保证可见性
```

#### 规则八：传递性规则（Transitivity）

> **如果 A happens-before B，且 B happens-before C，那么 A happens-before C。**

```java
// 示例
int a = 1;           // 1. happens-before 2.
volatile int b = 2;  // 2. happens-before 3.
int c = a + b;       // 3.

// 传递性：1. happens-before 3.
// 所以 c 一定能读到 a = 1, b = 2
```

### 4.3 happens-before 与时间调度的关系

```
┌─────────────────────────────────────────────────────────┐
│                   happens-before 不是时间顺序            │
│                                                         │
│   线程 A            happens-before           线程 B      │
│   write x ──────────────→───────────── read x          │
│                                                         │
│   A 在 write 之前的所有操作，B 都可能看到                   │
│   但 B 可能在 A 的 write 之前 就执行了 read（读取旧值）     │
│   只是后来被通知/刷新后，B 才看到新值                      │
└─────────────────────────────────────────────────────────┘
```

### 4.4 happens-before 综合示例

```java
public class HBExample {
    private int x = 0;
    private volatile boolean flag = false;

    public void write() {
        x = 42;           // 1.
        flag = true;      // 2. volatile 写
    }

    public void read() {
        if (flag) {       // 3. volatile 读
            // 根据 volatile 规则：2. happens-before 3.
            // 根据程序顺序规则：1. happens-before 2.
            // 根据传递性：1. happens-before 3.
            // 所以这里一定能看到 x = 42
            System.out.println(x);  // 输出 42
        }
    }
}
```

---

## 五、重排序：编译器重排、CPU 重排、内存屏障

### 5.1 什么是重排序？

重排序（Reordering）是编译器和 CPU 为了优化程序性能，对指令执行顺序进行调整的行为。

```
源代码                     实际执行可能（重排序后）
─────────────────────     ──────────────────────
a = 1;                     b = 2;        // 重排
b = 2;            →        a = 1;        // 重排
c = a + b;                 c = a + b;    // 保持（依赖于 a, b）
```

**为什么可以重排序？**

- **as-if-serial 语义**：在不改变单线程执行结果的前提下，任何重排序都是允许的
- **数据依赖关系**：只有没有数据依赖关系的指令才能重排序

**数据依赖关系的类型：**

| 关系类型 | 示例 | 能否重排 |
|---------|------|---------|
| 写后读 | `a = 1; b = a;` | ✗ |
| 读后写 | `b = a; a = 2;` | ✗ |
| 写后写 | `a = 1; a = 2;` | ✗ |
| 读后读 | `b = a; c = a;` | ✓ |
| 写后写（无依赖） | `a = 1; b = 2;` | ✓ |

### 5.2 三种重排序类型

#### 类型一：编译器重排序

```
源代码：
x = obj.getX();    // 读取
y = x + 1;         // 计算
obj.setX(y);       // 写入

// 编译器优化后（假设 CPU 延迟高）：
// 可能先执行其他不相关的操作，再执行 setX
// 只要结果一致，编译器可以自由重排
```

**编译器的重排序受 as-if-serial 约束，不能改变单线程程序的结果。**

#### 类型二：CPU 重排序（指令级并行）

现代 CPU 使用**超标量流水线**和**乱序执行**来并行执行指令：

```
原始指令序列：
1. LOAD  x, [addr1]    // 加载 x（内存访问，慢）
2. ADD   y, x, 1       // 计算 y（快）
3. STORE [addr2], y    // 存储 y

CPU 执行：
- 指令 1 发出后需要等待内存返回（可能 100+ 周期）
- 期间，CPU 可以先执行 2
- 指令 2 完成后，指令 3 可以执行
- 即使 1 还在等待，结果仍然正确（因为 2 不依赖 1 的结果）
```

#### 类型三：内存重排序（Memory Reordering）

这是最隐蔽的重排序，发生在 CPU 缓存层面：

```
源代码：
Store A = 1;      // 写 A
Store B = 2;      // 写 B

内存实际执行顺序：
- CPU A 执行后，数据可能还在 Store Buffer 中
- 尚未刷新到主内存
- 其他 CPU 核心可能先看到 B 的更新，再看到 A 的更新

这称为 Store Buffer Forwarding 或 Memory Reordering
```

### 5.3 内存屏障（Memory Barrier）

内存屏障（Memory Barrier，也称 Memory Fence）是 CPU 提供的指令，用于禁止特定类型的重排序。

#### 四种内存屏障

| 屏障类型 | 作用 | 防止的重排序 |
|---------|------|------------|
| **LoadLoad** | 屏障前的读操作先于屏障后的读操作 | 防止 Load1 和 Load2 重排序 |
| **StoreStore** | 屏障前的写操作先于屏障后的写操作 | 防止 Store1 和 Store2 重排序 |
| **LoadStore** | 屏障前的读操作先于屏障后的写操作 | 防止 Load 和 Store 重排序 |
| **StoreLoad** | 屏障前的写操作先于屏障后的读操作 | 防止 Store 和 Load 重排序 |

#### 内存屏障在 volatile 中的应用

```java
volatile int x = 0;

// 线程 A 写 x = 1：
// 1. StoreStore 屏障（确保之前的普通写都已刷新到主内存）
// 2. volatile 写（x = 1，写入主内存，同时 invalid 其他 CPU 缓存）
// 3. StoreLoad 屏障（确保写对后续的读可见）
// 底层：Lock 前缀指令（x86）或 DMB（ARM）

// 线程 B 读 x：
// 1. LoadLoad 屏障（确保后续普通读不会先执行）
// 2. LoadStore 屏障（确保不会和后续写重排）
// 3. volatile 读（从主内存读取最新值）
// 底层：内存屏障指令或缓存一致性协议保证
```

#### x86 架构的内存屏障特性

| 屏障类型 | x86 实现 | 说明 |
|---------|---------|------|
| StoreStore | CPU 自动保证 | x86 Store 顺序较强 |
| LoadLoad | CPU 自动保证 | x86 Load 顺序较强 |
| StoreLoad | `mfence` / `lock` | **需要显式屏障**，这是性能开销最大的 |
| LoadStore | CPU 自动保证 | x86 保证 |

**为什么 x86 的 StoreLoad 需要特殊处理？**

```
CPU A：                     CPU B：
Store A = 1                 
（写入 Store Buffer）       Load A  → 读到 0（旧值！）
                           // 此时 Store Buffer 中的 A 还未刷新到主内存
                           // Store Buffer 是 CPU 私有的
```

### 5.4 重排序对多线程的影响

```java
public class ReorderDemo {
    private int a = 0;
    private int b = 0;
    private int x = 0;
    private int y = 0;

    // 线程 A
    public void threadA() {
        a = 1;          // S1
        x = b;          // S2
    }

    // 线程 B
    public void threadB() {
        b = 1;          // S3
        y = a;          // S4
    }
}
```

**可能出现的执行结果：**

| 执行顺序 | x | y | 说明 |
|---------|---|---|------|
| S1 → S2 → S3 → S4 | 0 | 1 | 正常 |
| S3 → S4 → S1 → S2 | 1 | 0 | 正常 |
| S1 → S3 → S4 → S2 | 1 | 1 | 正常 |
| S1 → S2 → S4 → S3 | 0 | 0 | **不正常！** |

如果出现 x = 0 且 y = 0，说明发生了可见性问题。

---

## 六、volatile 的内存语义

### 6.1 volatile 的两大内存语义

1. **可见性**：写 volatile 后，所有线程立即可见
2. **有序性**：禁止指令重排序

### 6.2 volatile 的 happens-before 保证

```
                    happens-before
线程 A ───────────────────────────────→ 线程 B
  │                                          ▲
  │                                          │
write(volatile) ───────────────────→ read(volatile)
  │                                          │
  │                                          │
  │  线程 A 在写之前的所有操作                 │
  │  对线程 B 在读之后的所有操作可见           │
```

### 6.3 volatile 写-读的内存语义

```java
volatile int balance = 1000;

// 线程 A（生产者）：
balance = 2000;           // volatile 写
// 语义：
// 1. 将本地内存中的值刷新到主内存
// 2. 使其他 CPU 缓存中的副本失效
// 3. happens-before 所有后续的 volatile 读

// 线程 B（消费者）：
int current = balance;    // volatile 读
// 语义：
// 1. 使 CPU 缓存失效，从主内存重新读取
// 2. happens-before 所有后续的操作
```

### 6.4 volatile 在 DCL 中的作用

```java
public class Singleton {
    private static volatile Singleton instance;  // 关键！

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                    // 构造过程（简化）：
                    // 1. 分配内存
                    // 2. 调用构造方法
                    // 3. instance = 引用赋值
                    // volatile 禁止了 2 和 3 的重排序
                }
            }
        }
        return instance;
    }
}
```

**没有 volatile 的风险：**

```
分配内存 ──→ 引用赋值 ──→ 调用构造方法
                              ↑
                        重排序后可能先执行这里

线程 B 看到 instance != null
但此时对象可能还没完成构造！
```

### 6.5 volatile 数组的特殊性

```java
volatile int[] arr = new int[10];

// arr 是 volatile，但 arr[0] 不是！
// volatile 保证的是 arr 引用本身可见
// arr[i] 的访问需要额外同步

arr = new int[20];  // 整个数组引用可见

// 如果要 volatile 数组语义，需要：
volatile int[] arr2;
public synchronized void write() {
    arr2[0] = 1;  // 同步保证可见性
}
```

---

## 七、synchronized 的内存语义

### 7.1 synchronized 的两大内存语义

1. **原子性**：互斥访问，一次只有一个线程能进入
2. **可见性**：unlock 前必须 flush 到主内存

### 7.2 synchronized 的 happens-before 保证

```
线程 A                           线程 B
   │                                │
   │  synchronized (lock)           │
   │  ↓                             │
   │  ... 临界区代码 ...             │
   │  ↓                             │
   │  ... 对共享变量的修改 ...        │    happens-before
   │  ↓                             │  ←──────────────────
   │  synchronized (lock)            │
   │                                │
   │                         synchronized (lock)
   │                         ↓
   │                         ... 一定能读到共享变量的最新值 ...
```

### 7.3 synchronized 的底层实现

```java
synchronized (obj) {
    x = 100;
}

// 编译后生成字节码：
// monitorenter    // 获取锁
// x = 100;
// monitorexit     // 释放锁

// 底层实现：
// 1. Mark Word 中的锁状态改变
// 2. 轻量级锁：CAS 修改栈帧中的锁记录
// 3. 重量级锁：OS mutex，挂起线程
```

### 7.4 synchronized 的内存语义实现

```
synchronized (lock) {
    x = 100;
}

等价于：

// lock 前
acquire() {
    // 内存屏障（Acquire Barrier）
    // 防止临界区前的操作重排序到临界区内
}

// 临界区
x = 100;

// unlock 后
release() {
    // 内存屏障（Release Barrier）
    // 防止临界区内的操作重排序到临界区外
    // 强制刷新本地缓存到主内存
}
```

### 7.5 synchronized 与 volatile 的对比

| 特性 | synchronized | volatile |
|------|-------------|----------|
| **原子性** | ✓ 保证 | ✗ 不保证 |
| **可见性** | ✓ 保证 | ✓ 保证 |
| **有序性** | ✓ 保证 | ✓ 保证 |
| **阻塞** | ✓ 可能阻塞 | ✗ 不阻塞 |
| **性能** | 较重（OS 互斥） | 轻量级 |
| **可重入** | ✓ 支持 | 不适用 |
| **作用域** | 方法/代码块 | 变量 |

---

## 八、final 域的内存语义

### 8.1 final 域的特殊性

final 域在 Java 5 之后有了特殊的内存语义：**正确构造的对象，final 域的值对所有线程可见，无需同步。**

### 8.2 final 的写屏障（Write Barrier）

```java
public class FinalFieldDemo {
    final int x;           // final 域
    int y;                 // 普通域
    static FinalFieldDemo instance;

    public FinalFieldDemo() {
        x = 1;             // 1. 写入 final 域
        y = 2;             // 2. 写入普通域
    }

    public static void writer() {
        instance = new FinalFieldDemo();  // 构造 + 引用赋值
    }

    public static void reader() {
        FinalFieldDemo obj = instance;     // 读取引用
        // 此时 obj.x 一定等于 1（final 保证）
        // 但 obj.y 可能等于 0（未正确构造风险）
    }
}
```

### 8.3 为什么需要正确构造？

**对象逸出（Object Escape）问题：**

```java
public class EscapeDemo {
    final int value;
    static EscapeDemo instance;

    // 错误写法：在构造方法中逸出 this
    public EscapeDemo() {
        value = 100;
        instance = this;  // 逸出！其他线程可能看到未构造完成的对象
    }
}

// 正确写法：
public class SafeDemo {
    final int value;

    public SafeDemo(int v) {
        value = v;  // 先初始化所有域
        // 不要在构造方法中逸出 this
    }
}
```

### 8.4 final 的内存语义规则

```
final 域的写 happens-before：
1. 将 final 域写入主内存
2. 构造对象的引用写入主内存（不逸出）

final 域的读 happens-before：
1. 从主内存读取 final 域
2. 从主内存读取对象引用

保证：一旦构造函数完成（引用未逸出），
所有线程都能看到正确初始化的 final 域值。
```

### 8.5 final 与不可变对象

```java
// 不可变对象天然线程安全
public final class ImmutablePerson {
    private final String name;    // final
    private final int age;        // final

    public ImmutablePerson(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // 没有 setter，所有字段 final
    // 每次返回新的实例
}

// 使用：无需同步，可共享
ImmutablePerson p = new ImmutablePerson("Alice", 30);
```

---

## 九、高频面试题

### 面试题 1：什么是 happens-before？它和"先行发生"有什么区别？

**参考答案：**

happens-before 是 JMM 中定义的两个操作之间的偏序关系，它规定了：
1. 如果 A happens-before B，那么 A 的执行结果对 B 可见
2. JMM 禁止会导致这种可见性被破坏的重排序

**常见误解澄清：**

| 误解 | 正确理解 |
|------|---------|
| happens-before 是时间上的先后 | 它是 JMM 的偏序关系，与物理时间无关 |
| happens-before 要求 A 先执行 | 不要求，只要效果一致即可 |
| 同一线程中后写的变量对先写的可见 | 同一线程中，写后读可见