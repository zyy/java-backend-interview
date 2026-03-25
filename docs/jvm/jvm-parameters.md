---
layout: default
title: JVM 参数配置
---
# JVM 参数配置

> JVM 调优参数详解

## 🎯 面试重点

- 常用 JVM 参数
- 参数设置原则
- 生产配置示例

## 📖 堆内存参数

```bash
# 堆大小
-Xms4g              # 初始堆大小
-Xmx4g              # 最大堆大小
# 建议：Xms = Xmx，避免动态扩容

# 年轻代
-Xmn2g              # 年轻代大小
-XX:NewRatio=2      # 新生代:老年代 = 1:2
-XX:SurvivorRatio=8 # Eden:Survivor = 8:1

# 元空间
-XX:MetaspaceSize=256m      # 初始元空间大小
-XX:MaxMetaspaceSize=512m   # 最大元空间大小

# 直接内存
-XX:MaxDirectMemorySize=1g  # 最大直接内存
```

## 📖 GC 参数

### Serial GC

```bash
-XX:+UseSerialGC
# 单线程 GC，适合客户端
```

### Parallel GC

```bash
-XX:+UseParallelGC           # 年轻代使用 Parallel
-XX:+UseParallelOldGC        # 老年代使用 Parallel
-XX:ParallelGCThreads=4      # GC 线程数
-XX:MaxGCPauseMillis=200     # 最大停顿时间目标
-XX:GCTimeRatio=99           # 吞吐量目标
```

### CMS GC

```bash
-XX:+UseConcMarkSweepGC      # 使用 CMS
-XX:+UseCMSInitiatingOccupancyOnly
-XX:CMSInitiatingOccupancyFraction=70  # 老年代 70% 触发
-XX:+CMSScavengeBeforeRemark  # Remark 前做一次 Young GC
-XX:+CMSParallelRemarkEnabled # 并行 Remark
```

### G1 GC

```bash
-XX:+UseG1GC                 # 使用 G1
-XX:MaxGCPauseMillis=200     # 最大停顿时间
-XX:G1HeapRegionSize=8m      # Region 大小
-XX:InitiatingHeapOccupancyPercent=45  # 触发阈值
-XX:G1ReservePercent=10      # 保留空间
```

### ZGC

```bash
-XX:+UseZGC                  # 使用 ZGC
-XX:ConcGCThreads=4          # 并发 GC 线程
-XX:ZAllocationSpikeTolerance=5  # 分配尖峰容忍度
```

## 📖 GC 日志参数

```bash
# JDK 8
-XX:+PrintGCDetails
-XX:+PrintGCDateStamps
-XX:+PrintGCTimeStamps
-XX:+PrintGCApplicationStoppedTime
-Xloggc:/path/to/gc.log

# JDK 9+
-Xlog:gc*:file=/path/to/gc.log:time,tags:filecount=5,filesize=100m
```

## 📖 OOM 处理参数

```bash
# OOM 时导出堆转储
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/path/to/dump

# OOM 时执行脚本
-XX:OnOutOfMemoryError="/path/to/script.sh"
```

## 📖 其他常用参数

```bash
# 线程栈大小
-Xss1m

# 大对象直接进入老年代
-XX:PretenureSizeThreshold=1m

# 晋升年龄阈值
-XX:MaxTenuringThreshold=15

# 禁用偏向锁
-XX:-UseBiasedLocking

# 字符串去重（G1）
-XX:+UseStringDeduplication

# 压缩指针
-XX:+UseCompressedOops
-XX:+UseCompressedClassPointers
```

## 📖 生产配置示例

### 4C8G 服务器

```bash
# Web 应用
-Xms4g -Xmx4g
-Xmn1g
-XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-Xlog:gc*:file=/var/log/gc.log:time,tags
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heap.hprof
```

### 8C16G 服务器

```bash
# 服务端应用
-Xms12g -Xmx12g
-Xmn4g
-XX:MetaspaceSize=512m -XX:MaxMetaspaceSize=1g
-XX:+UseG1GC
-XX:MaxGCPauseMillis=100
-XX:G1HeapRegionSize=16m
-XX:InitiatingHeapOccupancyPercent=40
```

### 大数据应用

```bash
# 内存敏感型
-Xms32g -Xmx32g
-XX:+UseZGC
-XX:ConcGCThreads=8
-XX:ZCollectionInterval=5
```

## 📖 面试真题

### Q1: 常用的 JVM 参数？

**答：**
- `-Xms/-Xmx`：堆大小
- `-Xmn`：年轻代大小
- `-XX:+UseG1GC`：使用 G1
- `-XX:MaxGCPauseMillis`：停顿时间目标
- `-Xlog:gc*`：GC 日志

### Q2: 如何设置堆大小？

**答：**
- 初始堆和最大堆设置为相同值
- 堆大小一般不超过物理内存的 50%
- 需要考虑元空间、直接内存、栈等开销

### Q3: 如何选择垃圾收集器？

**答：**
- 单核/客户端：Serial
- 多核/吞吐优先：Parallel
- 低延迟：G1
- 超低延迟（JDK 11+）：ZGC

---

**⭐ 重点：JVM 参数配置是性能调优的基础**