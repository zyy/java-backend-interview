---
layout: default
title: 内存分配策略
---
# 内存分配策略

> 对象如何在堆内存中分配

## 🎯 面试重点

- 对象分配的流程
- 内存分配方式（指针碰撞/空闲列表）
- 内存分配是否线程安全

## 📖 对象分配流程

### 分配步骤

```java
/**
 * 对象分配流程：
 * 
 * 1. 检查类是否加载
 *    - 检查常量池中是否有类的符号引用
 *    - 检查类是否已加载、解析、初始化
 * 
 * 2. 分配内存
 *    - 计算对象所需内存大小
 *    - 从堆中分配内存
 * 
 * 3. 初始化零值
 *    - 将实例数据区初始化为零值
 *    - 保证字段可以不赋值直接使用
 * 
 * 4. 设置对象头
 *    - 设置 Mark Word
 *    - 设置 Klass Pointer
 *    - 设置数组长度（数组）
 * 
 * 5. 执行 <init>
 *    - 调用构造函数
 *    - 执行代码块和字段赋值
 */
public class ObjectAllocationProcess {
    // 可用内存计算
    /*
     * objectSize = 对象头 + 实例数据 + 对齐填充
     * 
     * 对象头 = Mark Word(8) + Klass Pointer(4/8) + 数组长度(4,仅数组)
     * 实例数据 = 所有字段的内存占用之和
     * 对齐填充 = 8 的倍数
     */
}
```

### 内存分配方式

```java
/**
 * 内存分配有两种方式：
 */
public class AllocationMethods {
    // 1. 指针碰撞（Bump the Pointer）
    /*
     * 适用：内存规整（没有碎片）
     * 原理：使用一个指针，分配内存时移动指针
     * 
     *     ┌───────────────────────┐
     *     │ 已分配  │ ← 指针位置   │
     *     ├───────────────────────┤
     *     │    未分配             │
     *     └───────────────────────┘
     * 
     * 使用：Serial、ParNew 等使用标记-整理的收集器
     */
    
    // 2. 空闲列表（Free List）
    /*
     * 适用：内存不规整（存在碎片）
     * 原理：维护一个列表，记录可用内存块
     * 
     *     ┌────┬────┬────┬────┐
     *     │ A  │ B  │ C  │ D  │
     *     │ 20 │ 10 │ 30 │ 15 │
     *     └──┴────┴────┴────┘
     * 
     * 使用：CMS 等使用标记-清除的收集器
     */
}
```

### 线程安全问题

```java
/**
 * 内存分配的线程安全问题
 * 
 * 问题：多个线程同时分配内存，可能导致指针覆盖
 * 
 * 解决方案：
 */
public class ThreadSafeAllocation {
    // 1. CAS + 失败重试
    /*
     * 乐观锁思路
     * 
     * class Allocation {
     *     private static final AtomicInteger offset = new AtomicInteger(0);
     *     
     *     public void allocate(int size) {
     *         while (true) {
     *             int current = offset.get();
     *             int next = current + size;
     *             if (offset.compareAndSet(current, next)) {
     *                 return current;
     *             }
     *         }
     *     }
     * }
     */
    
    // 2. TLAB（Thread Local Allocation Buffer）
    /*
     * 为每个线程分配一小块内存（TLAB）
     * 线程在自己的 TLAB 中分配，不需要同步
     * 
     * 配置：-XX:+UseTLAB
     * 默认：TLAB 大小 = Eden 区 / 线程数
     * 
     *     ┌─────────────────────────────────────┐
     *     │  Thread 1 TLAB  │  Thread 2 TLAB    │
     *     │   [私有区域]    │    [私有区域]     │
     *     └─────────────────────────────────────┘
     */
}
```

## 📖 对象分配策略

### 对象年龄（Age）

```java
/**
 * 对象年龄（Age）
 * 
 * 对象在 Survivor 区每熬过一次 Minor GC，年龄 +1
 * 默认 age 达到 15（-XX:MaxTenuringThreshold）晋升老年代
 * 
 * 晋升阈值可以通过 -XX:MaxTenuringThreshold 设置
 */
public class AgeDemo {
    // 年龄配置
    /*
     * -XX:MaxTenuringThreshold=15  // 默认 15
     * -XX:SurvivorRatio=8          // Eden/Survivor = 8
     * -XX:+AlwaysTenure           // 立即晋升（不使用 Survivor）
     */
}
```

### 晋升老年代的时机

```java
/**
 * 对象晋升老年代的时机：
 */
public class PromoteToOld {
    // 1. 年龄达到阈值
    /*
     * age >= -XX:MaxTenuringThreshold
     * 默认 15 次 Minor GC
     */
    
    // 2. 动态年龄判断
    /*
     * Survivor 区中，年龄 >= n 的对象总和 > Survivor 区的一半
     * 则 >= n 的对象全部晋升老年代
     * 
     * 目的：避免年龄太小的对象频繁晋升
     */
    
    // 3. 大对象直接进入老年代
    /*
     * -XX:PretenureSizeThreshold=1024 (字节)
     * 
     * 超过该阈值的对象直接在老年代分配
     * 避免在 Eden 区产生大量复制
     */
    
    // 4. 空间分配担保
    /*
     * Minor GC 前，检查老年代最大可用连续空间
     * 如果不够，触发 Full GC
     */
}
```

### 分配担保

```java
/**
 * 空间分配担保
 * 
 * 原理：
 * 1. Minor GC 前，检查老年代最大可用连续空间
 * 2. 如果 > 历次 Minor GC 晋升老年代对象平均值，可以进行 Minor GC
 * 3. 否则进行 Full GC
 */
public class AllocationGuarantee {
    // 配置
    /*
     * -XX:HandlePromotionFailure=true
     * 
     * JDK 7+ 后：
     * 只要老年代最大可用连续空间 > 新生代对象总空间
     * 就可以进行 Minor GC，否则 Full GC
     */
}
```

## 📖 面试真题

### Q1: 什么情况下对象会进入老年代？

**答：**
1. 年龄达到阈值（默认 15 岁）
2. 动态年龄判断，Survivor 区同龄对象超过一半
3. 大对象（超过 -XX:PretenureSizeThreshold）
4. Survivor 区空间不够

### Q2: 什么是 TLAB？

**答：** Thread Local Allocation Buffer，线程本地分配缓冲区。每个线程在 Eden 区分配一小块内存，对象在 TLAB 中分配不需要同步，提高分配效率。

### Q3: 对象分配在堆还是栈？

**答：** 
- 对象本身分配在堆中（new Object）
- 引用变量在栈中（Object obj）
- 逃逸分析后，可能进行栈上分配（标量替换）

---

**⭐ 重点：理解对象分配流程和内存分配方式，这是理解 GC 的基础**