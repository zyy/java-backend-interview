# JVM 垃圾回收算法详解 ⭐⭐⭐

## 面试题：说说 JVM 的垃圾回收算法

### 核心回答

JVM 垃圾回收主要包括**标记阶段**和**回收阶段**，常见算法有：标记-清除、复制算法、标记-整理算法，以及分代收集算法。

### 对象存活判断

#### 1. 引用计数算法

```java
// 给对象添加一个引用计数器
// 每被引用一次，计数器 +1
// 引用失效时，计数器 -1
// 计数器为 0 时，可回收

// 问题：无法解决循环引用
Object a = new Object();  // a:1
Object b = new Object();  // b:1
a.ref = b;  // b:2
b.ref = a;  // a:2
// a 和 b 互相引用，但已无外部引用
// 引用计数不为 0，无法回收
```

**缺点**：无法处理循环引用，Python 曾使用，现已改为可达性分析

#### 2. 可达性分析算法（GC Roots）

```
GC Roots 包括：
1. 栈中的局部变量引用的对象
2. 方法区中类静态属性引用的对象
3. 方法区中常量引用的对象
4. 本地方法栈中 JNI 引用的对象
5. JVM 内部引用（Class对象、异常对象等）
6. 所有被同步锁（synchronized）持有的对象
```

**工作原理**：
```
从 GC Roots 出发，沿着引用链向下搜索
 reachable objects（可达对象）
   ↓
不可达的对象 = 垃圾
```

### 三种基础垃圾回收算法

#### 1. 标记-清除算法（Mark-Sweep）

```java
// 步骤1：标记
遍历所有对象，标记存活对象

// 步骤2：清除
遍历堆内存，回收未标记对象

// 问题：
// 1. 效率问题：标记和清除效率都不高
// 2. 空间问题：产生大量内存碎片
```

```
标记-清除示意图：

标记前：[obj][obj][obj][obj][obj][obj]
         ↓ 标记存活对象
标记后：[   ][obj][   ][obj][   ][obj]
         ↓ 清除
结果：   [obj][   ][obj][   ][obj]
         ↓
      碎片化内存
```

#### 2. 复制算法（Copying）

```java
// 原理：将内存分成两块
// 每次只使用一块
// 回收时，将存活对象复制到另一块
// 清除原块

// 优点：无碎片、高效
// 缺点：浪费一半内存
```

```
复制算法示意图：

内存分为 From 和 To 两半：
From: [obj][obj][  ][  ]  →  存活对象复制到 To
To:   [   ][   ][obj][obj]  →  交换 From 和 To
```

**应用**：Minor GC（年轻代）
- Eden 区（80%）
- Survivor From（10%）
- Survivor To（10%）

```
年轻代内存布局：

┌────────────────────────────────────┐
│               Eden                  │  80%
├─────────────┬──────────────────────┤
│  Survivor   │     Survivor        │
│    From      │      To            │
│   10%       │     10%            │
└─────────────┴──────────────────────┘

Minor GC 流程：
1. Eden 区存活对象 → Survivor To
2. Survivor From 存活对象 → Survivor To（年龄+1）
3. Survivor From 和 Survivor To 交换
```

#### 3. 标记-整理算法（Mark-Compact）

```java
// 步骤1：标记存活对象
// 步骤2：整理 - 将存活对象向一端移动
// 步骤3：清除边界外的对象
```

```
标记-整理示意图：

整理前：[   ][obj][   ][obj][   ][obj][   ]
         ↓
整理后：[obj][obj][obj][   ][   ][   ][   ]
         ↓
      清除边界外的对象
```

**应用**：Full GC（老年代）

### 分代收集算法

```
年轻代（Young Generation）：
- 对象朝生夕灭
- 采用复制算法
- Minor GC 频繁

老年代（Old/Tenured Generation）：
- 对象存活时间长
- 采用标记-清除/标记-整理算法
- Full GC 较少

永久代（PermGen JDK7-）→ 元空间（Metaspace JDK8+）：
- 存储类信息、常量
- 元空间使用本地内存
```

### 垃圾收集器

#### 1. Serial 收集器

```bash
-XX:+UseSerialGC
```

**特点**：
- 单线程收集
- 进行垃圾收集时，必须暂停所有用户线程（Stop The World）
- 简单高效，Client 模式默认

#### 2. Parallel 收集器

```bash
-XX:+UseParallelGC  # 新生代
-XX:+UseParallelOldGC  # 老年代
```

**特点**：
- 多线程并行收集
- 吞吐量优先
- JDK 8 默认

**参数**：
```bash
-XX:MaxGCPauseMillis=100  # 最大停顿时间
-XX:GCTimeRatio=19        # 吞吐量目标
```

#### 3. CMS 收集器（Concurrent Mark Sweep）

```bash
-XX:+UseConcMarkSweepGC
```

**收集过程**：
```
1. 初始标记（Initial Mark）
   - 标记 GC Roots 直接关联的对象
   - Stop The World，但很快

2. 并发标记（Concurrent Mark）
   - 标记所有存活对象
   - 与用户线程并发执行

3. 重新标记（Remark）
   - 修正并发标记期间变动的对象
   - Stop The World

4. 并发清除（Concurrent Sweep）
   - 清除垃圾对象
   - 与用户线程并发执行
```

**优缺点**：
- **优点**：并发收集、低停顿
- **缺点**：CPU 敏感、浮动垃圾、内存碎片

#### 4. G1 收集器（Garbage First）

```bash
-XX:+UseG1GC
```

**特点**：
- 面向服务端应用
- 将堆分成多个大小相等的 Region
- 优先回收价值最大的 Region
- 可预测停顿时间

**Region 布局**：
```
┌─────────────────────────────────────────────┐
│  Eden  │ Survivor │    Old     │   Humongous │
│  Region│  Region  │   Region   │   Region    │
└─────────────────────────────────────────────┘

Humongous Region：存储大于 Region 50% 的大对象
```

**收集过程**：
```
1. Young Collection（年轻代收集）
   - Eden 区和 Survivor 区回收
   - Stop The World

2. Mixed Collection（混合收集）
   - 选择价值最大的 Old Region
   - 同时收集年轻代和部分老年代
   - Stop The World

3. 并发标记周期（Concurrent Marking）
   - 追踪所有存活对象
```

#### 5. ZGC 和 Shenandoah

```bash
-XX:+UseZGC      # ZGC（JDK 11+）
-XX:+UseShenandoahGC  # Shenandoah（JDK 12+）
```

**特点**：
- 低延迟（< 10ms）
- 并发收集
- 不分代（ZGC）或部分分代（Shenandoah）

**ZGC 核心技术**：
- 染色指针（Colored Pointers）
- 读屏障（Load Barrier）
- 并发重定位

### 垃圾收集器对比

| 收集器 | 作用区域 | 算法 | 线程 | 停顿时间 | JDK 版本 |
|--------|---------|------|------|---------|---------|
| Serial | 年轻代 | 复制 | 单 | 较长 | 所有版本 |
| ParNew | 年轻代 | 复制 | 多 | 较长 | JDK 1.4+ |
| Parallel Scavenge | 年轻代 | 复制 | 多 | 较长 | JDK 1.4+ |
| Serial Old | 老年代 | 标记-整理 | 单 | 较长 | 所有版本 |
| Parallel Old | 老年代 | 标记-整理 | 多 | 较长 | JDK 1.6+ |
| CMS | 老年代 | 标记-清除 | 多 | 较短 | JDK 1.5+ |
| G1 | 全部 | 标记-整理 | 多 | 可预测 | JDK 9+ |
| ZGC | 全部 | 标记-整理 | 多 | <10ms | JDK 11+ |

### 高频面试题

**Q1: 为什么年轻代用复制算法，老年代用标记整理？**

```
年轻代：对象存活率低，复制操作少，效率高
- 98% 对象朝生夕灭
- 复制少量存活对象比整理大量碎片更划算

老年代：对象存活率高，复制成本高
- 对象存活时间长
- 采用标记-整理，避免内存碎片
```

**Q2: 什么是 Stop The World？**

```
JVM 在进行垃圾回收时，需要暂停所有用户线程
直到 GC 完成才能恢复

影响：
- 短暂停顿（<100ms）用户感知不强
- 长停顿（>1s）会导致系统卡顿

优化：
- 减少 GC 频率
- 使用并发收集器
```

**Q3: Minor GC 和 Full GC 的区别？**

| 类型 | 触发条件 | 回收区域 | 停顿时间 |
|------|---------|---------|---------|
| Minor GC | Eden 满 | 年轻代 | 短 |
| Full GC | 老年代满/空间分配担保失败 | 全部 | 长 |

**Q4: 对象何时进入老年代？**

```java
// 1. 年龄达到阈值（默认 15）
// 对象在 Survivor 区每经历一次 Minor GC，年龄 +1
// age >= MaxTenuringThreshold 时进入老年代

// 2. 大对象直接进入老年代
// -XX:PretenureSizeThreshold=1M

// 3. 动态年龄判断
// Survivor 区相同年龄对象总和 > Survivor 区一半
// 年龄 >= 该年龄的对象进入老年代
```

---

**参考链接：**
- [JVM垃圾回收算法详解-CSDN](https://blog.csdn.net/wstever/article/details/135476987)
- [JVM常见面试题(四):垃圾回收-博客园](https://www.cnblogs.com/qhhfRA/p/18566615)
