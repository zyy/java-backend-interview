# JVM 原理（合并版）

> JVM 是区分初级和高级 Java 开发者的关键知识点
> 本文档合并了所有 JVM 相关主题，便于统一维护

## 📋 内容大纲

## 1. JVM 内存模型 ⭐⭐

### 1.1 运行时数据区
**程序计数器（PC Register）：**
- 线程私有，指向当前执行指令地址
- 唯一不会发生 OOM 的区域

**Java 虚拟机栈（Java Virtual Machine Stacks）：**
- 线程私有，存储栈帧（Stack Frame）
- 局部变量表、操作数栈、动态链接、方法出口
- 异常：StackOverflowError（栈深度超限）、OutOfMemoryError（无法扩展）

**本地方法栈（Native Method Stack）：**
- 为 Native 方法服务
- 与虚拟机栈类似，可能由虚拟机实现合并

**Java 堆（Java Heap）：**
- 线程共享，存储对象实例
- GC 主要区域，分代收集
- 异常：OutOfMemoryError（堆内存不足）

**方法区（Method Area）：**
- 线程共享，存储类信息、常量、静态变量
- HotSpot 实现：永久代（JDK 1.7 前）、元空间（JDK 1.8+）
- 异常：OutOfMemoryError（元空间不足）

**运行时常量池（Runtime Constant Pool）：**
- 方法区的一部分，存储字面量和符号引用

### 1.2 对象内存布局
**对象头（Header）：**
- Mark Word：哈希码、GC 分代年龄、锁状态等（32/64 bit)
- Klass Pointer：指向类元数据的指针（压缩后 32 bit）
- 数组长度（仅数组对象）

**实例数据（Instance Data）：**
- 对象真正存储的有效数据
- 字段排列顺序受分配策略影响

**对齐填充（Padding）：**
- 保证对象大小为 8 字节的整数倍

**内存布局示例：**
```
+----------------------+
|      Mark Word       |  // 8 bytes (64-bit)
+----------------------+
|   Klass Pointer      |  // 4 bytes (compressed)
+----------------------+
|   instance data 1    |
|   instance data 2    |
|         ...          |
+----------------------+
|    alignment padding |  // 填充到 8 字节倍数
+----------------------+
```

### 1.3 内存分配策略
**对象优先在 Eden 区分配：**
- 大多数对象生命周期很短
- Eden 区内存不足时触发 Minor GC

**大对象直接进入老年代：**
- 避免在 Eden 区和 Survivor 区大量复制
- 阈值通过 `-XX:PretenureSizeThreshold` 设置

**长期存活对象进入老年代：**
- 对象年龄计数器，每熬过一次 Minor GC 年龄加 1
- 阈值通过 `-XX:MaxTenuringThreshold` 设置（默认 15）

**动态对象年龄判定：**
- 如果 Survivor 区中相同年龄所有对象大小总和 > Survivor 空间一半
- 年龄 >= 该年龄的对象直接进入老年代

**空间分配担保：**
- Minor GC 前检查老年代最大可用连续空间是否大于新生代所有对象总空间
- 如果成立，Minor GC 安全
- 否则检查是否允许担保失败（`-XX:HandlePromotionFailure`）

## 2. 垃圾回收 ⭐⭐⭐

### 2.1 垃圾回收算法详解
> 详细内容请参考原文档：[gc-algorithms.md](./gc-algorithms.md)

**标记-清除（Mark-Sweep）：**
- 过程：标记存活对象 → 清除未标记对象
- 缺点：内存碎片，效率问题

**复制（Copying）：**
- 过程：内存分为两块，存活对象复制到另一块
- 优点：无碎片，简单高效
- 缺点：内存利用率低（只能使用一半）

**标记-整理（Mark-Compact）：**
- 过程：标记存活对象 → 向一端移动 → 清理边界外内存
- 优点：无碎片，内存连续
- 缺点：移动对象开销大

**分代收集（Generational Collection）：**
- 依据：对象生命周期不同
- 年轻代：复制算法（Eden + 2个 Survivor）
- 老年代：标记-清除或标记-整理

### 2.2 G1、ZGC、Shenandoah（现代 GC）
**G1（Garbage First）：**
- 区域化内存布局，优先回收价值最大区域
- 可预测的停顿时间模型
- 适用：大内存（6GB+），停顿时间敏感

**ZGC（Z Garbage Collector）：**
- 并发标记、并发转移、并发重定位
- 停顿时间不超过 10ms
- 适用：超大内存（TB 级），超低延迟

**Shenandoah：**
- 与 ZGC 类似，但实现不同
- 并发压缩，减少 Full GC
- OpenJDK 社区驱动

**对比：**
| 特性 | G1 | ZGC | Shenandoah |
|------|-----|-----|------------|
| 最大堆 | 不限制 | 4TB | 不限制 |
| 停顿目标 | 200ms | 10ms | 10ms |
| 并发压缩 | 部分 | 完全 | 完全 |
| JDK 版本 | 9+（生产） | 11+（生产） | 12+（生产） |

### 2.3 GC 调优实战
**调优目标：**
1. 降低停顿时间（Latency）
2. 提高吞吐量（Throughput）
3. 减少内存占用（Footprint）

**常见问题及解决：**
1. **频繁 Minor GC**：增加新生代大小（`-Xmn`）
2. **Full GC 频繁**：增加老年代大小，优化对象分配
3. **GC 停顿过长**：使用 G1/ZGC，调整 Region 大小
4. **内存泄漏**：分析堆转储，查找强引用链

**参数示例：**
```bash
# G1 调优示例
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:G1HeapRegionSize=4M
-XX:InitiatingHeapOccupancyPercent=45

# ZGC 调优示例  
-XX:+UseZGC
-XX:ConcGCThreads=4
-XX:ParallelGCThreads=8
```

## 3. 类加载机制 ⭐⭐

### 3.1 类加载过程
**加载（Loading）：**
- 获取类的二进制字节流
- 转换为方法区的运行时数据结构
- 生成 Class 对象作为访问入口

**验证（Verification）：**
- 文件格式验证：魔数、版本等
- 元数据验证：语义验证
- 字节码验证：逻辑验证
- 符号引用验证：解析阶段验证

**准备（Preparation）：**
- 为类变量分配内存并设置初始值（零值）
- static final 常量在此阶段赋值

**解析（Resolution）：**
- 将符号引用转换为直接引用
- 类或接口、字段、方法、方法类型等的解析

**初始化（Initialization）：**
- 执行类构造器 `<clinit>()` 方法
- 静态变量赋值和静态代码块执行
- 父类先于子类初始化

### 3.2 双亲委派模型
**类加载器层次：**
1. **启动类加载器（Bootstrap ClassLoader）**：加载 `jre/lib` 核心类
2. **扩展类加载器（Extension ClassLoader）**：加载 `jre/lib/ext` 扩展类
3. **应用程序类加载器（Application ClassLoader）**：加载 classpath 类
4. **自定义类加载器**：用户自定义

**委派过程：**
1. 收到加载请求，先委托父加载器
2. 父加载器无法完成，子加载器尝试
3. 避免重复加载，保证类唯一性

**优点：**
- 安全性：防止核心类被篡改
- 唯一性：避免类重复加载
- 效率：减少加载开销

### 3.3 打破双亲委派
**场景：**
1. **JDBC 驱动加载**：需要加载厂商实现类
2. **Tomcat 类加载**：Web 应用隔离
3. **OSGi 模块化**：动态加载卸载
4. **热部署**：不重启更新类

**实现方式：**
1. 重写 `loadClass()` 方法（不推荐）
2. 重写 `findClass()` 方法（推荐）
3. 线程上下文类加载器（Thread Context ClassLoader）

**线程上下文类加载器：**
- 通过 `Thread.setContextClassLoader()` 设置
- 通过 `Thread.getContextClassLoader()` 获取
- SPI 机制使用（如 JDBC、JNDI）

## 4. 性能监控与调优 ⭐⭐⭐

### 4.1 常用监控工具
**命令行工具：**
- `jps`：JVM 进程状态
- `jstat`：JVM 统计信息（GC、类加载等）
- `jinfo`：JVM 配置信息
- `jmap`：内存映像（堆转储）
- `jstack`：线程栈跟踪
- `jcmd`：多功能命令（JDK 7+）

**可视化工具：**
- **JConsole**：基本监控
- **VisualVM**：功能全面（插件扩展）
- **JMC（Java Mission Control）**：商业级监控
- **Arthas**：阿里开源，在线诊断

**远程监控：**
- JMX（Java Management Extensions）
- 启用：`-Dcom.sun.management.jmxremote`
- 端口：`-Dcom.sun.management.jmxremote.port=9999`

### 4.2 线上问题排查
**CPU 飙升：**
1. `top` 找到 Java 进程和线程
2. `jstack` 获取线程栈
3. 分析线程状态（RUNNABLE、BLOCKED）
4. 常见原因：死循环、锁竞争、GC 频繁

**内存泄漏：**
1. `jmap -heap` 查看堆内存
2. `jmap -dump:format=b,file=heap.hprof` 导出堆转储
3. 使用 MAT（Memory Analyzer Tool）分析
4. 查找支配树、GC Roots 引用链

**OOM（OutOfMemoryError）：**
1. **Java heap space**：堆内存不足
2. **PermGen space / Metaspace**：元数据区不足
3. **Unable to create new native thread**：线程数超限
4. **GC overhead limit exceeded**：GC 效率过低

**死锁检测：**
1. `jstack` 查看线程状态
2. 查找 `BLOCKED` 状态和持有锁
3. 使用 VisualVM 死锁检测功能

### 4.3 JVM 参数配置
**堆内存参数：**
- `-Xms`：初始堆大小
- `-Xmx`：最大堆大小
- `-Xmn`：新生代大小
- `-XX:NewRatio`：新生代/老年代比例
- `-XX:SurvivorRatio`：Eden/Survivor 比例

**GC 参数：**
- `-XX:+UseSerialGC`：串行 GC
- `-XX:+UseParallelGC`：并行 GC（吞吐量优先）
- `-XX:+UseConcMarkSweepGC`：CMS GC（低停顿）
- `-XX:+UseG1GC`：G1 GC（平衡）
- `-XX:+UseZGC`：ZGC（超低延迟）

**监控参数：**
- `-XX:+HeapDumpOnOutOfMemoryError`：OOM 时自动堆转储
- `-XX:HeapDumpPath`：堆转储文件路径
- `-XX:+PrintGCDetails`：打印 GC 详情
- `-XX:+PrintGCDateStamps`：打印 GC 时间戳
- `-Xloggc:gc.log`：GC 日志文件

**其他重要参数：**
- `-XX:MaxMetaspaceSize`：元空间最大大小
- `-XX:MaxDirectMemorySize`：直接内存最大大小
- `-XX:+DisableExplicitGC`：禁用 System.gc()
- `-XX:+UseCompressedOops`：压缩普通对象指针

## 🎯 面试高频题汇总

1. **JVM 内存区域如何划分？各区域作用？**
   - 线程私有：程序计数器、虚拟机栈、本地方法栈
   - 线程共享：堆、方法区

2. **垃圾回收算法有哪些？各有什么优缺点？**
   - 标记-清除、复制、标记-整理、分代收集

3. **CMS 和 G1 的区别？**
   - CMS：标记-清除，低停顿，碎片问题
   - G1：区域化，可预测停顿，无碎片

4. **类加载的双亲委派模型是什么？**
   - 层次结构，自上而下委托，自下而上加载

5. **线上出现 OOM 如何排查？**
   - 查看错误类型 → 分析堆转储 → 定位泄漏点 → 优化代码

6. **对象内存布局是怎样的？**
   - 对象头（Mark Word + Klass Pointer）+ 实例数据 + 对齐填充

7. **如何打破双亲委派模型？**
   - 重写 loadClass/findClass，使用线程上下文类加载器

8. **JVM 调优经验？**
   - 根据应用特点选择 GC，合理设置堆大小，监控关键指标

## 📚 延伸阅读

- [JVM 规范](https://docs.oracle.com/javase/specs/jvms/se8/html/)
- [Java Performance](https://book.douban.com/subject/26740503/)
- 《深入理解 Java 虚拟机》
- 《Java 性能权威指南》

---

**文档维护说明：**
- 本文档合并了 JVM 所有主题
- 原独立文档可逐步迁移至此
- 后期只维护此合并文档，避免重复和冲突
- 索引文件需更新为指向此文档的对应章节
