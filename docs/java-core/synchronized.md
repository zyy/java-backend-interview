---
layout: default
title: synchronized 与锁升级原理 ⭐⭐⭐
---
# synchronized 与锁升级原理 ⭐⭐⭐

## 面试题：synchronized 的锁升级过程是怎样的？

### 核心回答

JDK 1.6 之前，synchronized 是**重量级锁**，直接调用操作系统互斥量（Mutex Lock），性能较差。JDK 1.6 引入了**锁升级机制**，根据竞争情况从无锁逐步升级到重量级锁，大幅提升了性能。

### 锁的四种状态

```
无锁 → 偏向锁 → 轻量级锁 → 重量级锁
（只能升级，不能降级，偏向锁可以撤销）
```

### Java 对象头结构

synchronized 锁信息存储在对象头（Mark Word）中：

```
对象头（64 位 JVM）：
|----------------------------------------------------------------------------------------|
|                                    Mark Word (64 bits)                                 |
|----------------------------------------------------------------------------------------|
| 锁状态   | 25 bit (unused) | 31 bit (hashCode) | 1 bit (unused) | 4 bit (分代年龄) | 1 bit (偏向锁位) | 2 bit (锁标志位) |
|----------------------------------------------------------------------------------------|
| 无锁     | 0               | hashCode          | 0              | 分代年龄         | 0                | 01               |
| 偏向锁   | 线程ID(54bit)   | Epoch(2bit)       | 分代年龄(4bit) | 1                | 01               |
| 轻量级锁 | 指向栈中锁记录的指针 (64 bit)                                              | 00               |
| 重量级锁 | 指向互斥量（Monitor）的指针 (64 bit)                                       | 10               |
| GC标记   | 空                                                                         | 11               |
|----------------------------------------------------------------------------------------|
```

### 锁升级过程详解

#### 1. 无锁状态

```java
// 对象刚创建时，处于无锁状态
Object obj = new Object();
// Mark Word：hashCode + 分代年龄 + 0（非偏向）+ 01（无锁）
```

#### 2. 偏向锁（Biased Locking）

**适用场景**：只有一个线程访问同步块

**原理**：
- 第一次获取锁时，将线程 ID 写入对象头
- 后续同一线程进入，只需检查线程 ID，无需 CAS

```java
// 偏向锁获取流程
if (Mark Word 是偏向模式) {
    if (线程 ID 是当前线程) {
        // 直接执行同步块，无需任何同步操作
    } else {
        // CAS 替换线程 ID
        if (CAS 成功) {
            // 获取偏向锁成功
        } else {
            // 撤销偏向锁，升级为轻量级锁
        }
    }
}
```

**优点**：
- 无竞争时，同步操作几乎零开销
- 适合单线程反复进入同步块的场景

**偏向锁撤销**：
- 当其他线程尝试获取锁时，需要撤销偏向锁
- 撤销需要等待全局安全点（STW），有一定开销

#### 3. 轻量级锁（Lightweight Locking）

**适用场景**：多个线程交替执行（无激烈竞争）

**原理**：
- 线程在栈帧中创建 Lock Record（锁记录）
- 使用 CAS 将对象头的 Mark Word 替换为指向 Lock Record 的指针
- 失败则自旋等待

```java
// 轻量级锁获取流程
// 1. 在当前线程栈帧中创建 Lock Record
Lock Record lr = new Lock Record();
lr.displaced_header = obj.markWord;

// 2. CAS 将对象头指向 Lock Record
if (CAS(obj.markWord, lr.displaced_header, lr)) {
    // 获取轻量级锁成功
} else {
    // 自旋等待
    for (int i = 0; i < 自旋次数; i++) {
        if (CAS(...)) return;
    }
    // 自旋失败，升级为重量级锁
}
```

**自旋优化**：
- **自适应自旋**：根据历史成功率动态调整自旋次数
- 如果之前成功过，增加自旋次数
- 如果之前失败过，减少自旋次数

#### 4. 重量级锁（Heavyweight Locking）

**适用场景**：多个线程激烈竞争

**原理**：
- 使用操作系统互斥量（Mutex）
- 线程阻塞和唤醒需要用户态/内核态切换
- 开销最大，但最稳定

```
Monitor（监视器）结构：
|------------------------------------------------|
|  Owner：持有锁的线程                            |
|  EntryList：等待获取锁的阻塞线程队列             |
|  WaitSet：调用 wait() 后等待的线程队列           |
|  Recursions：重入次数                           |
|------------------------------------------------|
```

### 锁升级流程图

```
线程 A 访问同步块
        ↓
    对象是否偏向？
        ↓ 否
    无锁 → CAS 获取偏向锁
        ↓ 是
    检查线程 ID
        ↓ 是（同一线程）
    直接执行（偏向锁）
        ↓ 否（不同线程）
    撤销偏向锁 → 升级为轻量级锁
        ↓
    CAS 获取轻量级锁
        ↓ 成功
    执行同步块
        ↓ 失败（有其他线程竞争）
    自旋等待
        ↓ 自旋成功
    获取轻量级锁
        ↓ 自旋失败
    升级为重量级锁 → 线程阻塞
```

### 代码示例

```java
public class LockUpgradeDemo {
    
    // 演示偏向锁
    public static void biasedLock() {
        Object lock = new Object();
        
        // 第一次获取锁，升级为偏向锁
        synchronized (lock) {
            // 偏向线程 A
        }
        
        // 同一线程再次获取，无需同步操作
        synchronized (lock) {
            // 直接执行
        }
    }
    
    // 演示轻量级锁
    public static void lightweightLock() throws InterruptedException {
        Object lock = new Object();
        
        Thread t1 = new Thread(() -> {
            synchronized (lock) {
                // 线程 A 获取偏向锁
            }
        });
        
        Thread t2 = new Thread(() -> {
            synchronized (lock) {
                // 线程 B 竞争，升级为轻量级锁
            }
        });
        
        t1.start();
        t1.join();  // 确保 t1 先执行完
        t2.start();
    }
    
    // 演示重量级锁
    public static void heavyweightLock() {
        Object lock = new Object();
        
        // 多个线程同时竞争
        for (int i = 0; i < 10; i++) {
            new Thread(() -> {
                synchronized (lock) {
                    // 激烈竞争，升级为重量级锁
                    try {
                        Thread.sleep(100);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }).start();
        }
    }
}
```

### 锁优化技术

#### 1. 锁消除（Lock Elimination）

```java
// JIT 编译器优化：检测到不可能存在竞争，消除锁
public void method() {
    Object lock = new Object();  // 局部变量，不可能逃逸
    synchronized (lock) {        // 锁会被消除
        // do something
    }
}
```

#### 2. 锁粗化（Lock Coarsening）

```java
// 优化前：频繁的加锁解锁
for (int i = 0; i < 100; i++) {
    synchronized (lock) {
        // do something
    }
}

// 优化后：扩大锁范围，减少加锁次数
synchronized (lock) {
    for (int i = 0; i < 100; i++) {
        // do something
    }
}
```

### 查看锁状态（JVM 参数）

```bash
# 查看对象头信息
java -jar jol-cli.jar internals java.util.HashMap

# JVM 参数控制锁行为
-XX:+UseBiasedLocking      # 启用偏向锁（默认开启）
-XX:-UseBiasedLocking      # 禁用偏向锁
-XX:BiasedLockingStartupDelay=0  # 启动立即启用偏向锁（默认延迟 4 秒）
```

### 高频面试题

**Q1: 为什么 JDK 15 要禁用偏向锁？**

JDK 15 默认禁用了偏向锁，原因：
1. **收益减少**：现代应用多线程竞争激烈，偏向锁撤销开销大
2. **复杂性**：偏向锁增加了代码复杂性和维护成本
3. **替代方案**：轻量级锁优化已经足够好

**Q2: synchronized 和 ReentrantLock 的区别？**

| 特性 | synchronized | ReentrantLock |
|------|-------------|---------------|
| 实现 | JVM 层（字节码） | API 层（Java 代码） |
| 锁获取 | 自动获取/释放 | 手动 lock/unlock |
| 可中断 | 不支持 | 支持 lockInterruptibly() |
| 超时获取 | 不支持 | 支持 tryLock(timeout) |
| 公平锁 | 非公平 | 支持公平/非公平 |
| 条件变量 | 一个（wait/notify） | 多个（Condition） |
| 性能 | JDK 6+ 优化后接近 | 与 synchronized 接近 |

**Q3: 为什么 wait()/notify() 必须在 synchronized 块内调用？**

1. **防止竞态条件**：确保在检查条件和等待之间不会有其他线程修改条件
2. **Monitor 关联**：wait()/notify() 依赖 Monitor，必须先获取锁
3. **语义完整性**：保证原子性操作

```java
// 正确用法
synchronized (lock) {
    while (!condition) {
        lock.wait();  // 释放锁，进入等待队列
    }
    // 执行业务逻辑
}

// 错误用法：会抛出 IllegalMonitorStateException
if (!condition) {
    lock.wait();  // 未获取锁就调用 wait
}
```

**Q4: 什么是锁的 happens-before 关系？**

```java
// 解锁 happens-before 加锁
// 即：线程 A 解锁后，线程 B 加锁时能看到线程 A 的所有修改

Thread A:
synchronized (lock) {
    x = 1;  // A 的操作
}

Thread B:
synchronized (lock) {
    // 这里一定能看到 x = 1
    System.out.println(x);
}
```

### 最佳实践

```java
// 1. 减少锁持有时间
public void method() {
    // 非同步操作
    prepare();
    
    synchronized (lock) {
        // 只同步必要的代码
        criticalSection();
    }
    
    // 非同步操作
    cleanup();
}

// 2. 降低锁粒度
// 不好的做法：一个大锁
public class BigLock {
    private final Object lock = new Object();
    private int count1;
    private int count2;
    
    public void inc1() {
        synchronized (lock) { count1++; }
    }
    
    public void inc2() {
        synchronized (lock) { count2++; }
    }
}

// 好的做法：细粒度锁
public class FineLock {
    private final Object lock1 = new Object();
    private final Object lock2 = new Object();
    private int count1;
    private int count2;
    
    public void inc1() {
        synchronized (lock1) { count1++; }
    }
    
    public void inc2() {
        synchronized (lock2) { count2++; }
    }
}

// 3. 避免嵌套锁（防止死锁）
// 不好的做法
synchronized (lockA) {
    synchronized (lockB) {  // 可能死锁
        // ...
    }
}

// 好的做法：统一获取顺序
Object first = lockA.hashCode() < lockB.hashCode() ? lockA : lockB;
Object second = lockA.hashCode() < lockB.hashCode() ? lockB : lockA;
synchronized (first) {
    synchronized (second) {
        // ...
    }
}
```

---

**参考链接：**
- [synchronized锁升级的原理-CSDN](https://blog.csdn.net/u012151345/article/details/139246964)
- [Java面试题之synchronized关键字原理-阿里云](https://developer.aliyun.com/article/1167811)
