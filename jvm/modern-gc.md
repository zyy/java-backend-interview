# G1、ZGC、Shenandoah

> 现代垃圾回收器

## 🎯 面试重点

- 各现代回收器的特点
- G1 的区域概念和回收流程
- ZGC 的染色指针技术

## 📖 G1 收集器

### G1 特点

```java
/**
 * G1 (Garbage First) 收集器
 * 
 * 特点：
 * 1. 区域（Region）概念
 * 2. 复制 + 标记-整理
 * 3. 可预测停顿时间
 * 4. 优先回收垃圾最多的区域
 * 5. JDK 9+ 默认收集器
 */
public class G1Features {
    // 启动参数
    /*
     * -XX:+UseG1GC                    // 启用 G1
     * -XX:MaxGCPauseMillis=200        // 最大停顿时间目标
     * -XX:G1HeapRegionSize=n          // Region 大小（1MB-32MB）
     * -XX:InitiatingHeapOccupancyPercent=45  // 触发 Mixed GC 阈值
     */
}
```

### G1 区域

```java
/**
 * G1 区域概念
 * 
 * G1 将堆划分为多个大小相等的 Region（区域）
 * 每个 Region 可以是 Eden、Survivor、Old、HUMOUS（大对象）
 * 
 * ┌─────────────────────────────────────────────────┐
 * │                   堆内存                          │
 * │  ┌──────┬──────┬──────┬──────┬──────┬──────┐   │
 * │  │ E    │ E    │ S    │ O    │ O    │ H    │   │
 * │  ├──────┴──────┴──────┴──────┴──────┴──────┤   │
 * │  │ E    │ E    │ O    │ O    │ H    │ E    │   │
 * │  ├──────┴──────┴──────┴──────┴──────┴──────┤   │
 * │  │ S    │ O    │ O    │ E    │ E    │ S    │   │
 * └──────────────────────────────────────────────┘   │
 * 
 * Region 大小：1MB - 32MB（通过 -XX:G1HeapRegionSize 设置）
 * 大对象（HUMOUS）：超过 Region 一半的对象
 */
public class G1Regions {}
```

### G1 回收流程

```java
/**
 * G1 回收流程：
 * 
 * 1. Young GC（年轻代收集）
 *    - 收集所有年轻代 Region
 *    - 复制到 Survivor Region
 *    - STW（Stop The World）
 * 
 * 2. Mixed GC（混合收集）
 *    - 收集所有年轻代 + 部分老年代
 *    - 多次 Young GC 后触发
 *    - STW
 * 
 * 3. Full GC（完整收集）
 *    - 串行/并行 Full GC
 *    - 发生条件：内存不足时
 */
public class G1CollectionProcess {
    // Young GC 流程
    /*
     * 1. 根扫描
     * 2. 更新 RSet
     * 3. 复制存活对象到 Survivor
     * 4. 处理引用
     */
    
    // 触发 Mixed GC 条件
    /*
     * G1MixedGCLiveThresholdPercent (默认 85%)
     * G1HeapWastePercent (默认 5%)
     * G1ReservePercent (默认 10%)
     */
}
```

### RSet 和 Card Table

```java
/**
 * RSet（Remembered Set）
 * 
 * 作用：记录其他 Region 对本 Region 的引用
 * 目的：避免全堆扫描，快速找到存活对象
 * 
 * 每个 Region 有一个 RSet
 * RSet 使用 Card Table 实现
 */
public class RSetExample {
    // Card Table
    /*
     * 每个 Card 512字节
     * 如果一个对象引用了其他 Region 的对象，对应 Card 标记为 dirty
     * 
     *     Region 1                    Region 2
     *  ┌────────────┐            ┌────────────┐
     *  │ Card Table  │     引用   │            │
     *  │ [ ][ ][DIRTY]│ ────────→│            │
     *  └────────────┘            └────────────┘
     */
}
```

## 📖 ZGC 收集器

### ZGC 特点

```java
/**
 * ZGC (Z Garbage Collector)
 * 
 * 特点：
 * 1. 并发收集（几乎全部并发）
 * 2. 染色指针（Colored Pointers）
 * 3. 读屏障（Load Barrier）
 * 4. 不分代（或者说动态分代）
 * 5. 停顿时间不超过 10ms
 * 6. 支持 TB 级堆内存
 */
public class ZGCFeatures {
    // 启动参数
    /*
     * -XX:+UseZGC                    // 启用 ZGC
     * -XX:ConcGCThreads=auto        // 并发 GC 线程数
     * -XX:ParallelGCThreads=auto    // 并行 GC 线程数
     * -XX:ZHeapSize=n               // 堆大小
     */
}
```

### 染色指针

```java
/**
 * 染色指针（Colored Pointers）
 * 
 * 原理：在对象的 64 位指针上使用几位作为标记位
 * 
 * 标记位含义（64位）：
 * 00000000 00000000 00000000 00000000 00000000 00000000 00000000 0000 0 0 0 0
 *                                                                          ↑ 颜色位
 * 
 * 颜色：
 * 0：正常对象
 * 1：重映射（Relocated）
 * 2：待回收（Marked0）
 * 4：已标记（Marked1）
 * 8：已初始化（Finalizable）
 */
public class ColoredPointers {
    // 优点
    /*
     * 1. 不需要额外的元数据空间
     * 2. 可以在运行时知道对象状态
     * 3. 不需要Barrier修改对象头
     * 
     * 限制：43 位寻址空间（8TB）
     */
}
```

### ZGC 回收流程

```java
/**
 * ZGC 回收阶段：
 * 
 * 1. 停顿标记（STW）
 *    - 标记 GC Roots
 *    - 停顿时间 < 1ms
 * 
 * 2. 并发标记
 *    - 遍历对象图
 *    - 标记所有存活对象
 *    - 不停顿
 * 
 * 3. 重新标记（STW）
 *    - 处理并发期间的变化
 *    - 停顿时间 < 1ms
 * 
 * 4. 并发重分配
 *    - 复制存活对象到新 Region
 *    - 更新指针
 *    - 不停顿
 * 
 * 5. 并发引用处理
 *    - 更新引用
 *    - 不停顿
 */
public class ZGCPhases {}
```

## 📖 Shenandoah 收集器

### Shenandoah 特点

```java
/**
 * Shenandoah 收集器
 * 
 * 特点：
 * 1. 并发回收（与应用并发）
 * 2. 转发指针（Brooks Pointer）
 * 3. 不分代（实验性分代）
 * 4. 与 G1 类似，使用 Region
 * 5. 停顿时间可控
 * 
 * 与 ZGC 对比：
 * - ZGC：染色指针，需要特定 JDK 版本
 * - Shenandoah：转发指针，OpenJDK 特有
 */
public class ShenandoahFeatures {
    // 启动参数
    /*
     * -XX:+UseShenandoahGC
     * -XX:ShenandoahGCHeuristics=adaptive
     * 
     * Heuristics：
     * - adaptive：自适应
     * - static：静态
     * - compact：压缩优先
     * - aggressive：激进
     */
}
```

### 转发指针

```java
/**
 * 转发指针（Brooks Pointer）
 * 
 * 在对象头部添加一个指针
 * 正常对象：指针指向自己
 * 移动后：指针指向新位置
 * 
 * 读写时检查指针：
 * - 读取：通过指针找到最新对象
 * - 写入：更新指针
 */
public class BrooksPointer {
    // 读屏障
    /*
     * Object getObjectField(Field f) {
     *     Object o = f.get(this);
     *     // 读屏障检查
     *     if (o == FORWARDING_PTR) {
     *         o = o.getForwardee();
     *     }
     *     return o;
     * }
     */
}
```

## 📖 对比总结

```java
/**
 * 现代 GC 对比
 */
public class GCComparison {
    /*
     * | 特性        | G1           | ZGC           | Shenandoah    |
     * |-------------|--------------|---------------|---------------|
     * | 分代        | 分代         | 不分代        | 不分代（实验）|
     * | 内存结构    | Region       | Region        | Region        |
     * | 并发程度    | 部分并发     | 全部并发       | 全部并发      |
     * | 停顿时间    | 可控         | <10ms         | <10ms         |
     * | 最大堆      | -            | 8TB           | -             |
     * | 原理        | RSet         | 染色指针      | 转发指针      |
     * | JDK 版本    | 9+ 默认      | 11+           | 8+            |
     * | 生产可用    | 是           | 是(11+)       | 是            |
     */
}
```

## 📖 面试真题

### Q1: G1 和 CMS 的区别？

**答：**
- G1 使用 Region 内存布局，CMS 使用 old 区的卡表
- G1 可以设置停顿时间目标，CMS 不行
- G1 使用复制+整理，CMS 使用标记+清除（会产生碎片）
- G1 会产生 Mixed GC，CMS 不会

### Q2: ZGC 为什么快？

**答：**
- 染色指针：在指针上标记，不需要额外空间，不需要改变对象头
- 并发重分配：大部分阶段与应用并发
- 读屏障优化：轻微开销换取并发安全

### Q3: G1 的 Region 大小如何设置？

**答：**
- 默认根据堆大小动态计算（1MB-32MB）
- 建议：不要太小（增加 RSet 开销），不要太大（GC 回收时间长）
- 公式：-XX:G1HeapRegionSize=8M（推荐 2 的幂次）

---

**⭐ 重点：现代回收器是 JDK 升级的重点，G1 必须掌握，ZGC 是未来趋势**