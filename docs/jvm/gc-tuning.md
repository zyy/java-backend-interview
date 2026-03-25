---
layout: default
title: GC 调优实战
---
# GC 调优实战

> 实际生产环境的 GC 调优

## 🎯 面试重点

- 常见的 GC 问题
- 调优思路和参数
- 典型案例分析

## 📖 调优思路

### 调优目标

```java
/**
 * GC 调优目标：
 * 
 * 1. 吞吐量（Throughput）
 *    - 单位时间内处理的任务数
 *    - -XX:GCTimeRatio 设置
 * 
 * 2. 停顿时间（Latency）
 *    - 单次 GC 停顿时间
 *    - -XX:MaxGCPauseMillis 设置
 * 
 * 3. 内存占用（Footprint）
 *    - 堆内存大小
 *    - -Xmx, -Xms
 * 
 * 目标三角：无法同时达到最优，通常在吞吐量和停顿时间之间权衡
 */
public class TuningGoals {
    // 配置示例
    /*
     * 吞吐量优先：
     * -XX:+UseParallelGC
     * -XX:GCTimeRatio=19
     * -XX:MaxGCPauseMillis=1000
     * 
     * 停顿时间优先（G1）：
     * -XX:+UseG1GC
     * -XX:MaxGCPauseMillis=200
     * -XX:G1HeapRegionSize=8m
     */
}
```

### 调优步骤

```java
/**
 * GC 调优步骤：
 * 
 * 1. 了解应用特征
 *    - 对象分配率
 *    - 对象生命周期
 *    - 并发用户数
 *    - 数据量
 * 
 * 2. 收集 GC 日志
 *    - -XX:+PrintGCDetails
 *    - -XX:+PrintGCDateStamps
 *    - -Xloggc:gc.log
 * 
 * 3. 分析日志
 *    - GC 频率
 *    - 停顿时间
 *    - 内存使用情况
 * 
 * 4. 调整参数
 *    - 堆大小
 *    - 年轻代大小
 *    - GC 收集器
 * 
 * 5. 验证效果
 */
public class TuningSteps {}
```

## 📖 常见问题

### Full GC 频繁

```java
/**
 * Full GC 频繁的原因：
 * 
 * 1. 内存不足
 *    - 堆太小
 *    - 对象太多/太大
 * 
 * 2. 内存碎片
 *    - 标记-清除产生碎片
 *    - CMS 的 Concurrent Mode Failure
 * 
 * 3. 对象的晋升
 *    - survivor 区太小
 *    - 对象年龄太大
 * 
 * 4. Metaspace 不足
 *    - 类加载太多
 *    - -XX:MetaspaceSize 太小
 */
public class FullGCFrequent {
    // 解决方案
    /*
     * 1. 增大堆内存
     *    -Xmx4096m -Xms4096m
     * 
     * 2. 增大年轻代
     *    -XX:NewRatio=1  (年轻代:老年代=1:1)
     * 
     * 3. 增大 survivor 区
     *    -XX:SurvivorRatio=4
     * 
     * 4. 调整 CMS 触发阈值
     *    -XX:CMSInitiatingOccupancyFraction=70
     * 
     * 5. 切换到 G1
     *    -XX:+UseG1GC
     */
}
```

### GC 停顿时间长

```java
/**
 * GC 停顿时间长的原因：
 * 
 * 1. 年轻代太大
 *    - 复制算法时间过长
 * 
 * 2. 对象太多
 *    - 标记时间过长
 * 
 * 3. 收集器选择不当
 *    - 使用了 Serial GC
 * 
 * 4. 大对象直接进入老年代
 *    - -XX:PretenureSizeThreshold 太小
 */
public class LongPauseTime {
    // 解决方案
    /*
     * 1. 减小年轻代
     *    -XX:NewSize=256m -XX:MaxNewSize=256m
     * 
     * 2. 使用 G1
     *    -XX:+UseG1GC
     *    -XX:MaxGCPauseMillis=200
     * 
     * 3. 使用 ZGC
     *    -XX:+UseZGC
     * 
     * 4. 优化对象分配
     *    - 对象池化
     *    - 避免分配大对象
     */
}
```

### 内存泄漏

```java
/**
 * 内存泄漏排查
 * 
 * 常见泄漏点：
 * 1. 静态集合（HashMap, ArrayList）
 * 2. ThreadLocal
 * 3. 缓存
 * 4. 监听器/回调
 * 5. 内部类持有外部类引用
 */
public class MemoryLeak {
    // 排查工具
    /*
     * 1. jmap -histo:live pid
     *    - 列出堆中对象
     * 
     * 2. jmap -dump:format=b,file=heap.hprof pid
     *    - 导出堆 dump
     * 
     * 3. MAT (Memory Analyzer Tool)
     *    - 分析 dump 文件
     *    - 查找泄漏对象
     * 
     * 4. jstat -gcutil pid 1000
     *    - 监控 GC 情况
     */
}
```

## 📖 调优参数

### 堆内存参数

```java
/**
 * 堆内存参数
 */
public class HeapParameters {
    // 基本参数
    /*
     * -Xms4096m          初始堆大小
     * -Xmx4096m          最大堆大小
     * -Xmn256m           年轻代大小
     * -XX:NewRatio=2     年轻代:老年代=1:2
     * -XX:SurvivorRatio=8  Eden:Survivor=8:1
     */
    
    // 元空间参数
    /*
     * -XX:MetaspaceSize=256m  元空间初始大小
     * -XX:MaxMetaspaceSize=1g 元空间最大
     */
    
    // 例子
    /*
     * 4核8G服务器 Tomcat 配置：
     * -Xms4096m -Xmx4096m
     * -XX:MetaspaceSize=256m
     * -XX:MaxMetaspaceSize=512m
     */
}
```

### GC 收集器参数

```java
/**
 * GC 收集器参数
 */
public class GCParameters {
    // Parallel GC
    /*
     * -XX:+UseParallelGC
     * -XX:ParallelGCThreads=4
     * -XX:MaxGCPauseMillis=100
     * -XX:GCTimeRatio=19
     */
    
    // CMS
    /*
     * -XX:+UseConcMarkSweepGC
     * -XX:CMSInitiatingOccupancyFraction=80
     * -XX:+UseCMSInitiatingOccupancyOnly
     * -XX:+CMSScavengeBeforeRemark
     */
    
    // G1
    /*
     * -XX:+UseG1GC
     * -XX:MaxGCPauseMillis=200
     * -XX:G1HeapRegionSize=8m
     * -XX:InitiatingHeapOccupancyPercent=45
     */
    
    // ZGC
    /*
     * -XX:+UseZGC
     * -XX:ConcGCThreads=4
     */
}
```

## 📖 调优案例

### 案例1：堆外内存溢出

```java
/**
 * 案例：NIO 导致堆外内存溢出
 * 
 * 现象：Java 进程 OOM，但堆内存还有空间
 * 原因：NIO 直接内存（DirectByteBuffer）超出限制
 */
public class DirectMemoryCase {
    // 排查
    /*
     * 1. jstat -gc 显示堆正常
     * 2. jmap -heap 显示无异常
     * 3. dmesg | grep "Out of memory" 发现 NPE
     * 
     * 解决：
     * -XX:MaxDirectMemorySize=1g  // 增加限制
     * 或检查代码中 DirectByteBuffer 释放
     */
}
```

### 案例2：Metaspace 溢出

```java
/**
 * 案例：Metaspace 溢出
 * 
 * 现象：Full GC 后 old 区内存占用高，Metaspace 使用率 100%
 * 原因：大量动态类生成（JBoss、CGLib、动态代理）
 */
public class MetaspaceCase {
    // 排查
    /*
     * 1. jstat -gc 显示 Metaspace 已满
     * 2. jmap -clstats 查看类加载器
     * 
     * 解决：
     * -XX:MetaspaceSize=256m
     * -XX:MaxMetaspaceSize=1g
     * -XX:+UseStringDeduplication  // 字符串去重
     */
}
```

## 📖 面试真题

### Q1: 如何排查 OOM？

**答：**
1. 添加 -XX:+HeapDumpOnOutOfMemoryError 参数，OOM 时自动 dump
2. 使用 jmap -dump 手动导出
3. 使用 MAT 分析 dump 文件，查找大对象和内存泄漏
4. 分析代码中的对象创建和引用

### Q2: G1 调优参数？

**答：**
- -XX:MaxGCPauseMillis=200：设置停顿时间目标
- -XX:G1HeapRegionSize=8m：Region 大小
- -XX:InitiatingHeapOccupancyPercent=45：触发 Mixed GC 阈值
- -XX:G1ReservePercent=10：保留内存比例

---

**⭐ 重点：GC 调优是生产环境必备技能，需要结合具体场景分析**