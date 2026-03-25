# JVM 监控工具

> JVM 问题排查利器

## 🎯 面试重点

- 常用监控命令
- 分析工具使用

## 📖 命令行工具

### jps

```bash
# 查看所有 Java 进程
jps -l

# 输出主类全名
jps -lvm
```

### jstat

```bash
# 查看类加载统计
jstat -class pid

# 查看 GC 统计
jstat -gc pid 1000 10  # 每秒输出，共 10 次

# 查看 GC 原因
jstat -gccause pid

# 输出每列含义
# EC: Eden 区容量
# EU: Eden 区已用
# OC: Old 区容量
# OU: Old 区已用
# YGC: Young GC 次数
# YGCT: Young GC 总时间
# FGC: Full GC 次数
# FGCT: Full GC 总时间
```

### jmap

```bash
# 查看堆内存使用
jmap -heap pid

# 查看对象统计
jmap -histo pid | head 20

# 导出堆转储
jmap -dump:format=b,file=heap.hprof pid

# 查看等待回收的对象
jmap -finalizerinfo pid
```

### jstack

```bash
# 打印线程栈
jstack pid

# 检测死锁
jstack -l pid | grep "Found one Java-level deadlock"

# 输出到文件
jstack pid > thread.txt
```

### jinfo

```bash
# 查看 JVM 参数
jinfo -flags pid

# 查看某个参数
jinfo -flag MaxHeapSize pid

# 动态修改参数
jinfo -flag +PrintGCDetails pid
```

## 📖 可视化工具

### JConsole

```
# 启动
jconsole

# 功能
- 内存监控
- 线程监控
- 类加载监控
- MBean 管理
```

### VisualVM

```
# 启动
jvisualvm

# 功能
- 内存分析
- CPU 分析
- 线程分析
- 堆转储分析
- 插件扩展
```

### JMC (Java Mission Control)

```
# 启动
jmc

# 功能
- 低开销监控
- 飞行记录器
- 内存泄漏检测
- 性能分析
```

### Arthas（阿里开源）

```bash
# 启动
java -jar arthas-boot.jar

# 常用命令
dashboard      # 仪表盘
thread         # 线程信息
heapdump       # 堆转储
jad            # 反编译代码
watch          # 方法监控
trace          # 方法调用链追踪
stack          # 方法调用栈
```

## 📖 面试真题

### Q1: 如何查看线上 JVM 内存使用？

**答：** 
- `jstat -gc pid` 快速查看 GC 情况
- `jmap -heap pid` 查看堆内存详情
- JConsole/VisualVM 可视化监控

### Q2: 线上 CPU 100% 如何排查？

**答：**
1. `top -H -p pid` 找到占用 CPU 高的线程
2. 将线程 ID 转为 16 进制：`printf '%x' tid`
3. `jstack pid | grep hex` 找到对应线程栈
4. 分析代码定位问题

---

**⭐ 重点：监控工具是排查问题的基础**