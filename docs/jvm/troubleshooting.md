---
layout: default
title: JVM 线上问题排查
---
# JVM 线上问题排查

> 生产环境问题定位

## 🎯 面试重点

- CPU 飙高排查
- OOM 排查
- 死锁排查

## 📖 CPU 100% 排查

### 排查步骤

```bash
# 1. 找到 Java 进程
jps -l
# 或
ps -ef | grep java

# 2. 查看占用 CPU 高的线程
top -H -p <pid>

# 3. 将线程 ID 转为 16 进制
printf '%x' <tid>
# 例如：printf '%x' 12345  -> 3039

# 4. 查看线程栈
jstack <pid> | grep <hex_tid> -A 30

# 5. 分析代码定位问题
```

### 常见原因

```
1. 死循环
   - while(true) 无退出条件
   - 自旋锁问题

2. 正则回溯
   - 复杂正则表达式导致回溯

3. 密集计算
   - 算法复杂度过高
   - 大数据量处理

4. GC 频繁
   - Full GC 导致 CPU 飙高
```

## 📖 OOM 排查

### 排查步骤

```bash
# 1. 查看内存使用
jstat -gc <pid> 1000

# 2. 导出堆转储
jmap -dump:format=b,file=heap.hprof <pid>

# 或添加 JVM 参数自动 dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/path/to/dump

# 3. 使用 MAT 或 VisualVM 分析
```

### 常见 OOM 类型

```
1. Java heap space
   - 对象太多，堆不够
   - 内存泄漏
   
   解决：增大堆内存、排查泄漏

2. Metaspace
   - 类加载太多
   - 动态代理生成类
   
   解决：增大 Metaspace、排查类加载

3. GC overhead limit exceeded
   - GC 时间占比过高
   
   解决：增大堆内存、优化代码

4. Direct buffer memory
   - NIO 直接内存溢出
   
   解决：增大 -XX:MaxDirectMemorySize

5. StackOverflowError
   - 方法调用栈太深
   - 递归没有终止
   
   解决：增大栈大小、修复递归
```

## 📖 死锁排查

### 排查步骤

```bash
# 1. 打印线程栈
jstack <pid> > thread.txt

# 2. 搜索死锁信息
grep -A 10 "Found one Java-level deadlock" thread.txt

# 或直接使用
jstack -l <pid> | grep -A 20 "deadlock"
```

### 死锁示例

```java
// 典型死锁
Thread 1: lock(A) -> 等待 lock(B)
Thread 2: lock(B) -> 等待 lock(A)
```

### 解决方案

```
1. 统一加锁顺序
2. 使用 tryLock 超时
3. 使用 Lock 的 lockInterruptibly
4. 减小锁粒度
```

## 📖 内存泄漏排查

### 排查步骤

```
1. 多次 GC 后内存不释放
   jstat -gcutil <pid> 1000

2. 对比多次 heap dump
   jmap -histo:live <pid> | head 20

3. 使用 MAT 分析
   - Dominator Tree
   - Leak Suspects Report
```

### 常见泄漏场景

```java
// 1. 静态集合
static List<Object> list = new ArrayList<>();
list.add(obj);  // 永远不释放

// 2. ThreadLocal 未清理
threadLocal.set(obj);
// 忘记 remove()

// 3. 监听器未注销
listener.register(this);
// 忘记 unregister()

// 4. 缓存未过期
cache.put(key, value);
// 没有过期策略
```

## 📖 面试真题

### Q1: 线上服务响应慢如何排查？

**答：**
1. 查看系统资源：top、vmstat
2. 查看 JVM：jstat -gc
3. 查看线程状态：jstack
4. 查看是否有死锁
5. 使用 Arthas trace 追踪慢方法

### Q2: 如何排查内存泄漏？

**答：**
1. 多次 GC 后内存持续增长
2. 导出 heap dump
3. 使用 MAT 分析泄漏对象
4. 追踪对象引用链
5. 定位代码修复

---

**⭐ 重点：问题排查能力是高级工程师必备技能**