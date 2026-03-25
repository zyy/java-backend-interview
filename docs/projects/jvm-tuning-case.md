# JVM调优实战案例

> 从OOM到高性能：JVM调优实战全记录

## 🎯 面试重点

- JVM内存模型与垃圾回收原理
- 常见JVM问题诊断与解决
- 线上性能问题排查流程
- JVM参数调优实战

## 📖 内存溢出（OOM）案例

### 案例1：堆内存溢出（Heap OOM）

```bash
# 错误日志
java.lang.OutOfMemoryError: Java heap space
Dumping heap to /tmp/heapdump.hprof ...
Heap dump file created

# 问题分析
1. 使用jmap分析堆转储文件
jhat /tmp/heapdump.hprof  # 启动分析服务
# 或使用MAT（Memory Analyzer Tool）图形化分析

2. 发现大对象
发现一个HashMap占用了80%的堆内存，存储了100万条缓存数据

3. 代码定位
public class CacheService {
    private static final Map<String, Object> CACHE = new HashMap<>();
    
    public void cacheData(String key, Object value) {
        CACHE.put(key, value);  // 无限增长，无过期机制
    }
}

# 解决方案
1. 使用LRU缓存（LinkedHashMap）
private static final Map<String, Object> CACHE = 
    Collections.synchronizedMap(new LinkedHashMap<String, Object>(1000, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry eldest) {
            return size() > 1000;  // 限制大小
        }
    });

2. 使用Caffeine缓存（带过期时间）
private Cache<String, Object> cache = Caffeine.newBuilder()
    .maximumSize(1000)
    .expireAfterWrite(10, TimeUnit.MINUTES)
    .recordStats()
    .build();

3. 调整JVM参数
-Xmx4g -Xms4g  # 增加堆内存
-XX:+HeapDumpOnOutOfMemoryError  # OOM时生成堆转储
-XX:HeapDumpPath=/tmp/heapdump.hprof
```

### 案例2：元空间溢出（Metaspace OOM）

```bash
# 错误日志
java.lang.OutOfMemoryError: Metaspace

# 问题分析
1. 动态生成大量类
使用CGLIB动态代理，每次请求生成新代理类
使用Groovy脚本引擎，动态编译执行脚本

2. 使用jstat查看元空间使用
jstat -gc <pid> 1000 10
# 关注：M（Metaspace）使用量

3. 代码定位
public class GroovyService {
    public Object execute(String script) {
        GroovyShell shell = new GroovyShell();
        return shell.evaluate(script);  // 每次执行都编译新类
    }
}

# 解决方案
1. 使用类缓存
private static final Map<String, Class> CLASS_CACHE = new ConcurrentHashMap<>();

public Object execute(String script) {
    Class clazz = CLASS_CACHE.computeIfAbsent(script, k -> {
        GroovyClassLoader loader = new GroovyClassLoader();
        return loader.parseClass(script);
    });
    return clazz.newInstance();
}

2. 限制动态类生成
- 使用静态代理替代动态代理
- 预编译脚本，运行时只执行

3. 调整JVM参数
-XX:MetaspaceSize=256m      # 初始元空间大小
-XX:MaxMetaspaceSize=512m    # 最大元空间大小
-XX:+UseCompressedClassPointers  # 压缩类指针
```

### 案例3：直接内存溢出（Direct Memory OOM）

```bash
# 错误日志
java.lang.OutOfMemoryError: Direct buffer memory

# 问题分析
1. 使用ByteBuffer.allocateDirect()分配直接内存
2. Netty使用直接内存作为ByteBuf
3. 直接内存不受堆内存限制，但受物理内存限制

4. 使用Native Memory Tracking监控
-XX:NativeMemoryTracking=detail
jcmd <pid> VM.native_memory detail

# 代码定位
public class DirectMemoryService {
    public void processFile(String path) {
        // 每次处理都分配新的直接缓冲区
        ByteBuffer buffer = ByteBuffer.allocateDirect(1024 * 1024);  // 1MB
        // ... 处理逻辑
        // 忘记释放（需要等待GC）
    }
}

# 解决方案
1. 使用池化的直接缓冲区
private static final ByteBufferPool BUFFER_POOL = new ByteBufferPool(10, 1024 * 1024);

public void processFile(String path) {
    ByteBuffer buffer = BUFFER_POOL.borrowBuffer();
    try {
        // ... 处理逻辑
    } finally {
        BUFFER_POOL.returnBuffer(buffer);
    }
}

2. Netty配置优化
// 使用池化的ByteBufAllocator
ByteBufAllocator allocator = PooledByteBufAllocator.DEFAULT;

// 调整直接内存参数
-Dio.netty.maxDirectMemory=0  # 使用堆内存
# 或限制直接内存大小
-XX:MaxDirectMemorySize=1g

3. 及时释放资源
// 手动释放直接内存
((DirectBuffer) buffer).cleaner().clean();
```

## 📖 GC性能问题案例

### 案例1：频繁Full GC

```bash
# 症状：应用周期性卡顿，每次持续几秒到几十秒
# GC日志分析
[Full GC (Allocation Failure) 
[PSYoungGen: 0K->0K(153600K)] 
[ParOldGen: 419430K->419430K(419430K)] 419430K->419430K(573030K), 
[Metaspace: 32767K->32767K(1081344K)], 
0.1234567 secs] 
[Times: user=0.12 sys=0.00, real=0.12 secs]

# 问题分析
1. 老年代空间不足，频繁Full GC
2. 使用jstat监控GC
jstat -gc <pid> 1000

# 输出：
 S0C    S1C    S0U    S1U      EC       EU        OC         OU       MC     MU    CCSC   CCSU   YGC     YGCT    FGC    FGCT     GCT   
5120.0 5120.0  0.0    0.0   41984.0  41984.0   1048576.0  1048576.0  4864.0 4688.7 512.0  481.2     10    0.050   5      0.500    0.550

# 关注：OU（老年代使用）接近OC（老年代容量），FGC（Full GC次数）频繁

# 代码定位
public class DataProcessor {
    public void process(List<Data> dataList) {
        List<Result> results = new ArrayList<>();
        for (Data data : dataList) {
            // 处理每个数据，产生大量中间对象
            Result result = processSingle(data);
            results.add(result);
        }
        // results对象太大，进入老年代
    }
}

# 解决方案
1. 优化对象创建
- 使用对象池复用对象
- 减少大对象创建
- 使用基本类型替代包装类型

2. 调整堆内存比例
# 增大新生代比例
-Xmn2g  # 新生代2G（堆总大小4G）
# 或调整比例
-XX:NewRatio=2  # 老年代:新生代=2:1

3. 调整Survivor区比例
-XX:SurvivorRatio=8  # Eden:Survivor=8:1:1

4. 使用G1GC替代Parallel GC
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200  # 目标暂停时间
-XX:G1HeapRegionSize=4m   # Region大小
```

### 案例2：Young GC时间过长

```bash
# 症状：Young GC每次耗时几百毫秒，影响接口响应
# GC日志分析
[GC (Allocation Failure) 
[PSYoungGen: 419430K->52428K(458752K)] 419430K->52428K(1507328K), 
0.234567 secs] 
[Times: user=0.23 sys=0.00, real=0.23 secs]

# Young GC耗时234ms，太长！

# 问题分析
1. 新生代对象太多，存活对象多
2. 使用jmap查看对象分布
jmap -histo:live <pid> | head -20

# 发现大量相同的临时对象

# 代码定位
public class StringProcessor {
    public String process(String input) {
        // 频繁创建StringBuilder
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            sb.append(processChar(input.charAt(i)));  // 每次循环创建新String
        }
        return sb.toString();
    }
}

# 解决方案
1. 重用StringBuilder
private static final ThreadLocal<StringBuilder> STRING_BUILDER = 
    ThreadLocal.withInitial(() -> new StringBuilder(1024));

public String process(String input) {
    StringBuilder sb = STRING_BUILDER.get();
    sb.setLength(0);  // 清空重用
    
    for (int i = 0; i < 1000; i++) {
        sb.append(processChar(input.charAt(i)));
    }
    return sb.toString();
}

2. 调整新生代大小
# 增大新生代，减少GC频率
-Xmn2g  # 原来是1g

3. 使用G1GC优化Young GC
-XX:+UseG1GC
-XX:G1NewSizePercent=5    # 新生代最小比例
-XX:G1MaxNewSizePercent=60 # 新生代最大比例
```

### 案例3：CMS GC并发模式失败

```bash
# 症状：CMS GC退化为Serial Old GC，导致长时间STW
# GC日志分析
[GC (CMS Initial Mark) ...]
[GC (CMS Final Remark) ...]
[Full GC (Allocation Failure)  # 并发模式失败！
... 耗时5秒 ...]

# 问题分析
1. 老年代碎片化严重
2. 晋升阈值设置不合理
3. 内存分配过快，CMS回收跟不上

# 代码定位
public class MemoryIntensiveService {
    public void process() {
        // 分配大量中等大小的对象（几十KB）
        for (int i = 0; i < 100000; i++) {
            byte[] buffer = new byte[32 * 1024];  // 32KB
            // 使用后立即丢弃
        }
        // 这些对象可能直接进入老年代（-XX:PretenureSizeThreshold）
    }
}

# 解决方案
1. 使用G1GC替代CMS
# G1GC更适合处理内存碎片
-XX:+UseG1GC
-XX:+UseStringDeduplication  # 字符串去重

2. 调整晋升阈值
# 降低对象直接进入老年代的阈值
-XX:PretenureSizeThreshold=1M  # 1MB以上对象直接进入老年代

3. 增加老年代空间
# 增大堆内存，增加老年代比例
-Xmx8g -Xms8g
-XX:NewRatio=3  # 老年代:新生代=3:1

4. 调整CMS参数
-XX:CMSInitiatingOccupancyFraction=75  # 老年代使用75%时启动CMS
-XX:+UseCMSInitiatingOccupancyOnly
-XX:+CMSClassUnloadingEnabled  # 启用类卸载
```

## 📖 CPU性能问题案例

### 案例1：CPU 100%问题

```bash
# 症状：服务器CPU使用率100%，应用响应慢

# 排查步骤
1. 使用top找到高CPU进程
top -c

2. 找到高CPU线程
top -H -p <pid>
# 记录线程ID（十进制）

3. 将线程ID转为十六进制
printf "%x\n" <thread_id>

4. 使用jstack分析线程栈
jstack <pid> > thread_dump.txt
# 在thread_dump.txt中搜索十六进制线程ID

# 常见原因
1. 死循环
while (true) {
    // 业务逻辑
}

2. 频繁GC
# 查看GC日志

3. 锁竞争激烈
# 大量线程在等待锁

# 代码定位
public class OrderService {
    private final Object lock = new Object();
    
    public void processOrder(Order order) {
        synchronized (lock) {  // 全局锁，竞争激烈
            // 处理订单，耗时操作
            Thread.sleep(100);
        }
    }
}

# 解决方案
1. 减少锁粒度
private final Map<Long, Object> orderLocks = new ConcurrentHashMap<>();

public void processOrder(Order order) {
    Object lock = orderLocks.computeIfAbsent(order.getId(), k -> new Object());
    synchronized (lock) {  // 订单级锁
        // 处理订单
    }
}

2. 使用无锁数据结构
private final ConcurrentHashMap<Long, Order> orderMap = new ConcurrentHashMap<>();

public void processOrder(Order order) {
    orderMap.compute(order.getId(), (k, v) -> {
        // 无锁处理
        return processOrderInternal(order);
    });
}

3. 使用读写锁
private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();

public void readOperation() {
    lock.readLock().lock();
    try {
        // 读操作
    } finally {
        lock.readLock().unlock();
    }
}

public void writeOperation() {
    lock.writeLock().lock();
    try {
        // 写操作
    } finally {
        lock.writeLock().unlock();
    }
}
```

### 案例2：上下文切换过多

```bash
# 症状：CPU使用率不高，但系统负载高，性能差

# 排查步骤
1. 查看上下文切换次数
vmstat 1
# 关注cs（context switch）列

2. 使用pidstat查看进程上下文切换
pidstat -w -p <pid> 1

3. 使用jstack分析线程状态
# 大量线程处于RUNNABLE但实际在等待锁

# 代码定位
public class ThreadPoolService {
    // 线程池配置过大
    private ExecutorService executor = Executors.newFixedThreadPool(1000);
    
    public void process(List<Task> tasks) {
        List<Future> futures = new ArrayList<>();
        for (Task task : tasks) {
            futures.add(executor.submit(() -> {
                synchronized (sharedResource) {  // 竞争共享资源
                    return task.process();
                }
            }));
        }
        // 等待所有任务完成
    }
}

# 解决方案
1. 合理配置线程池
# 根据任务类型配置线程池
# CPU密集型：核心数 + 1
# IO密集型：核心数 * 2
private ExecutorService executor = new ThreadPoolExecutor(
    8,      // 核心线程数
    16,     // 最大线程数
    60,     // 空闲时间
    TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),  // 任务队列
    new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略
);

2. 减少锁竞争
# 使用ConcurrentHashMap替代synchronized Map
# 使用Atomic类替代synchronized
# 使用ThreadLocal避免共享

3. 使用异步非阻塞IO
# 使用Netty、WebFlux等异步框架
# 减少线程数量
```

## 📖 实战调优参数

### 1. 电商应用调优参数

```bash
# 电商应用特点：高并发、大内存、低延迟
# JVM参数配置
-Xmx8g -Xms8g                     # 堆内存8G
-Xmn4g                            # 新生代4G
-XX:MetaspaceSize=256m            # 元空间256M
-XX:MaxMetaspaceSize=512m         # 最大元空间512M
-XX:+UseG1GC                      # 使用G1垃圾回收器
-XX:MaxGCPauseMillis=200          # 目标暂停时间200ms
-XX:ParallelGCThreads=8           # 并行GC线程数（CPU核心数）
-XX:ConcGCThreads=4               # 并发GC线程数（CPU核心数/4）
-XX:InitiatingHeapOccupancyPercent=45  # 触发Mixed GC的堆占用率
-XX:G1HeapRegionSize=4m           # Region大小4M
-XX:+UseStringDeduplication       # 字符串去重
-XX:StringDeduplicationAgeThreshold=3  # 字符串去重年龄阈值
-XX:+PrintGCDetails               # 打印GC详情
-XX:+PrintGCDateStamps            # 打印GC时间戳
-XX:+PrintGCTimeStamps            # 打印GC时间戳
-Xloggc:/tmp/gc.log               # GC日志文件
-XX:+UseGCLogFileRotation         # GC日志轮转
-XX:NumberOfGCLogFiles=5          # 保留5个日志文件
-XX:GCLogFileSize=20M             # 每个日志文件20M
-XX:+HeapDumpOnOutOfMemoryError   # OOM时生成堆转储
-XX:HeapDumpPath=/tmp/heapdump.hprof  # 堆转储路径
-XX:ErrorFile=/tmp/hs_err_pid%p.log   # 错误日志
```

### 2. 大数据处理调优参数

```bash
# 大数据应用特点：大内存、大量计算、长时间运行
# JVM参数配置
-Xmx32g -Xms32g                    # 堆内存32G
-Xmn16g                            # 新生代16G
-XX:SurvivorRatio=8                # Eden:Survivor=8:1:1
-XX:MaxTenuringThreshold=15        # 对象晋升年龄阈值
-XX:PretenureSizeThreshold=1M      # 大对象直接进入老年代阈值
-XX:+UseConcMarkSweepGC            # 使用CMS（或G1GC）
-XX:CMSInitiatingOccupancyFraction=75  # CMS触发阈值
-XX:+UseCMSInitiatingOccupancyOnly     # 仅使用阈值触发CMS
-XX:+ExplicitGCInvokesConcurrent   # System.gc()触发并发GC
-XX:+CMSScavengeBeforeRemark       # CMS重新标记前执行Young GC
-XX:ParallelCMSThreads=8           # CMS并行线程数
-XX:ConcGCThreads=4                # CMS并发线程数
-XX:+CMSParallelRemarkEnabled      # 并行重新标记
-XX:+CMSClassUnloadingEnabled      # 启用类卸载
-XX:CMSFullGCsBeforeCompaction=0   # Full GC后压缩
-XX:+UseCompressedOops             # 压缩普通对象指针
-XX:+UseCompressedClassPointers    # 压缩类指针
-XX:ReservedCodeCacheSize=256m     # 代码缓存256M
```

### 3. 微服务应用调优参数

```bash
# 微服务特点：内存较小、快速启动、弹性伸缩
# JVM参数配置
-Xmx1g -Xms1g                      # 堆内存1G
-Xmn512m                           # 新生代512M
-XX:MetaspaceSize=128m             # 元空间128M
-XX:MaxMetaspaceSize=256m          # 最大元空间256M
-XX:+UseSerialGC                   # 使用Serial GC（单核小内存）
# 或使用G1GC小堆优化
-XX:+UseG1GC                       # 使用G1GC
-XX:G1HeapRegionSize=1m            # Region大小1M
-XX:MaxGCPauseMillis=100           # 目标暂停时间100ms
-XX:G1NewSizePercent=5             # 新生代最小比例5%
-XX:G1MaxNewSizePercent=60         # 新生代最大比例60%
-XX:InitiatingHeapOccupancyPercent=45  # IHOP 45%
-XX:ConcGCThreads=1                # 并发GC线程数1
-XX:ParallelGCThreads=2            # 并行GC线程数2
-XX:+UseStringDeduplication        # 字符串去重
-XX:StringDeduplicationAgeThreshold=3  # 字符串去重年龄阈值
-XX:+OptimizeStringConcat          # 优化字符串拼接
-XX:+UseTLAB                       # 使用线程本地分配缓冲
-XX:TLABSize=64k                   # TLAB大小64K
-XX:+ResizeTLAB                    # 允许调整TLAB大小
-XX:+AlwaysPreTouch                # 启动时预分配内存
-XX:+UseContainerSupport           # 容器支持
-XX:InitialRAMPercentage=50.0      # 初始内存百分比
-XX:MaxRAMPercentage=75.0          # 最大内存百分比
-XX:MinRAMPercentage=25.0          # 最小内存百分比
```

## 📖 监控与诊断工具

### 1. Arthas（阿尔萨斯）实战

```bash
# 安装Arthas
curl -O https://arthas.aliyun.com/arthas-boot.jar
java -jar arthas-boot.jar

# 常用命令
# 1. 查看JVM信息
dashboard  # 仪表板，实时查看JVM状态
jvm        # JVM信息

# 2. 线程分析
thread     # 查看所有线程
thread -n 3  # 查看最忙的3个线程
thread -b    # 查看死锁
thread <tid> # 查看指定线程

# 3. 类/方法监控
watch com.example.UserService getUser '{params, returnObj, throwExp}' -x 3
trace com.example.OrderService createOrder
monitor -c 5 com.example.UserService login  # 每5秒统计一次

# 4. 反编译代码
jad com.example.UserService

# 5. 修改运行时代码（热修复）
redefine /tmp/UserService.class

# 6. 方法调用追踪
stack com.example.UserService getUser

# 7. 火焰图生成
profiler start  # 开始采样
profiler stop   # 停止并生成火焰图
```

### 2. 线上问题排查流程

```java
/**
 * 线上JVM问题排查 checklist
 */
public class JVMTroubleshootingChecklist {
    
    // 1. 问题现象分类
    public enum ProblemType {
        OOM,              // 内存溢出
        HIGH_CPU,         // CPU使用率高
        HIGH_MEMORY,      // 内存使用率高
        SLOW_RESPONSE,    // 响应慢
        FREQUENT_GC,      // 频繁GC
        DEADLOCK,         // 死锁
    }
    
    // 2. 排查工具准备
    public class Tools {
        // 必须安装的工具
        String[] requiredTools = {
            "jps",      // 查看Java进程
            "jstack",   // 线程栈分析
            "jmap",     // 内存分析
            "jstat",    // JVM统计信息
            "jinfo",    // JVM配置信息
            "arthas",   // 在线诊断
            "vmstat",   // 系统性能
            "top"       // 进程监控
        };
        
        // 可选工具
        String[] optionalTools = {
            "MAT",           // 内存分析工具
            "GCViewer",      // GC日志分析
            "VisualVM",      // 可视化监控
            "YourKit",       // 商业性能分析
            "JProfiler"      // 商业性能分析
        };
    }
    
    // 3. 排查步骤
    public class Steps {
        /*
        1. 确认现象：收集错误日志、监控指标、用户反馈
        2. 定位进程：使用top、jps找到问题进程
        3. 资源分析：查看CPU、内存、IO、网络使用情况
        4. JVM分析：使用jstat、jmap、jstack分析JVM状态
        5. 线程分析：使用thread dump分析线程状态
        6. 内存分析：分析堆转储文件（如果已生成）
        7. 代码定位：结合日志和代码，定位问题根源
        8. 解决方案：实施优化措施
        9. 验证效果：监控优化后的效果
        10. 总结沉淀：记录问题原因和解决方案
        */
    }
}
```

## 📖 面试真题

### Q1: 如何排查线上JVM内存溢出问题？

**答：**
1. **查看错误日志**：确认OOM类型（Java heap space、Metaspace等）
2. **分析堆转储**：如果配置了-XX:+HeapDumpOnOutOfMemoryError，使用MAT或jhat分析
3. **检查监控指标**：查看内存使用趋势，确定是突然增长还是缓慢增长
4. **代码分析**：结合堆转储中的大对象，定位相关代码
5. **常见原因**：
   - 内存泄漏（如静态集合无限增长）
   - 大对象创建（如大数组、大字符串）
   - 不合理的内存配置（如堆内存太小）
6. **解决方案**：
   - 修复内存泄漏代码
   - 增加堆内存大小
   - 使用缓存时设置上限和过期时间

### Q2: 如何分析GC日志？

**答：**
1. **开启GC日志**：使用-XX:+PrintGCDetails等参数
2. **关键指标**：
   - GC类型：Young GC vs Full GC
   - 耗时：关注real time（实际暂停时间）
   - 内存变化：GC前后各区域使用量
   - 频率：GC发生频率
3. **分析工具**：
   - 使用GCViewer可视化分析
   - 使用gceasy在线分析
   - 手动分析关注Full GC频率和耗时
4. **优化目标**：
   - 减少Full GC频率
   - 降低GC暂停时间
   - 提高吞吐量

### Q3: 如何选择垃圾回收器？

**答：**
根据应用特点选择：
1. **Serial GC**：单核小内存（几百MB），嵌入式系统
2. **Parallel GC（吞吐量优先）**：多核，追求高吞吐，可接受较长暂停
3. **CMS GC（低延迟）**：多核，追求低暂停，老年代并发收集
4. **G1 GC（平衡型）**：大堆（4G+），平衡吞吐和暂停，JDK9+默认
5. **ZGC**：超大堆（TB级），极低暂停（<10ms），JDK15+生产可用
6. **Shenandoah**：类似ZGC，RedHat开发，低暂停

**选择建议**：
- 小堆（<4G）：Parallel GC或G1
- 中大堆（4G-32G）：G1
- 超大堆（>32G）：ZGC或Shenandoah
- 实时性要求高：ZGC、Shenandoah

### Q4: 如何设置合理的JVM参数？

**答：**
1. **堆内存**：
   - 初始堆（-Xms）和最大堆（-Xmx）设置相同值，避免动态调整
   - 堆大小 = 活跃数据量 × 2 ~ 3倍
   - 留出20%内存给操作系统和其他进程

2. **新生代**：
   - 新生代大小 = 堆大小 × 1/3 ~ 1/2
   - 使用-XX:NewRatio或-Xmn指定

3. **元空间**：
   - 初始值：-XX:MetaspaceSize=256m
   - 最大值：-XX:MaxMetaspaceSize=512m

4. **垃圾回收器**：
   - 根据应用特点选择合适的GC
   - 设置合理的暂停时间目标

5. **监控参数**：
   - 开启GC日志、堆转储、错误日志
   - 方便问题排查

### Q5: 如何预防JVM性能问题？

**答：**
1. **监控预警**：
   - 建立完善的监控体系（CPU、内存、GC、线程等）
   - 设置合理的告警阈值

2. **容量规划**：
   - 根据业务量预估内存需求
   - 定期进行容量评估和扩容

3. **代码规范**：
   - 避免内存泄漏（如静态集合、未关闭的资源）
   - 合理使用缓存（设置大小限制和过期时间）
   - 减少大对象创建

4. **压测验证**：
   - 定期进行压力测试，验证系统承载能力
   - 通过压测发现性能瓶颈

5. **定期优化**：
   - 定期分析GC日志，优化JVM参数
   - 定期检查代码中的性能问题

## 📚 延伸阅读

- [深入理解Java虚拟机](https://book.douban.com/subject/34907497/)
- [Java性能权威指南](https://book.douban.com/subject/26740520/)
- [Arthas官方文档](https://arthas.aliyun.com/doc/)
- [G1垃圾回收器调优](https://www.oracle.com/technical-resources/articles/java/g1gc.html)

---

**⭐ 重点：JVM调优需要结合监控数据、日志分析和代码审查，是一个持续优化和迭代的过程**