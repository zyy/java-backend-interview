# CPU 100% 问题排查实战

> 从报警到解决：CPU爆满问题全链路排查指南

## 🎯 面试重点

- CPU问题定位工具链
- 常见CPU问题场景分析
- 线程堆栈分析与解读
- 性能问题根治方案

## 📖 问题现象与分类

### 1. CPU 100% 现象识别

```bash
# 现象1：整体CPU使用率100%
top - 14:30:01 up 30 days,  1:15,  1 user,  load average: 10.25, 8.76, 7.34
%Cpu(s): 100.0 us,  0.0 sy,  0.0 ni,  0.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st

# 现象2：单个进程CPU使用率异常高
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 1234 java      20   0   12.3g   8.2g   1.2g R 450.0  25.8  100:30.15 java

# 现象3：系统负载高但CPU使用率不高
# 通常表示IO等待或锁竞争
load average: 15.00, 12.50, 10.00  # 1分钟平均负载15
%Cpu(s):  30.0 us,  10.0 sy,  0.0 ni,  10.0 id,  50.0 wa,  0.0 hi,  0.0 si,  0.0 st
# wa（IO等待）高达50%
```

### 2. CPU问题分类

```java
/**
 * CPU问题类型
 */
public enum CPUProblemType {
    
    USER_CPU_HIGH(100, 0),      // 用户态CPU高（代码问题）
    SYSTEM_CPU_HIGH(0, 100),    // 内核态CPU高（系统调用频繁）
    IO_WAIT_HIGH(0, 0, 50),     // IO等待高（磁盘/网络）
    LOAD_HIGH_BUT_CPU_LOW,      // 负载高但CPU低（锁竞争/上下文切换）
    SINGLE_THREAD_CPU_HIGH,     // 单线程CPU高（死循环/密集计算）
    MULTI_THREAD_CPU_HIGH,      // 多线程CPU高（线程池配置不当）
    PERIODIC_CPU_SPIKE          // 周期性CPU尖刺（定时任务/GC）
}
```

## 📖 排查工具链

### 1. 系统层面工具

```bash
# 1. top - 系统资源概览
top -c                    # 显示完整命令
top -H -p <pid>           # 查看指定进程的线程
top -b -n 1 > top.log     # 输出到文件

# 2. vmstat - 虚拟内存统计
vmstat 1 10               # 每秒采样1次，共10次
# 关键列：
# r：等待运行的进程数（>CPU核数表示有进程等待）
# us：用户态CPU时间百分比
# sy：内核态CPU时间百分比
# id：空闲CPU百分比
# wa：等待IO的CPU时间百分比
# cs：上下文切换次数（过高表示线程切换频繁）

# 3. mpstat - 多核CPU统计
mpstat -P ALL 1           # 查看每个CPU核心的使用率
# 发现CPU使用不均衡问题

# 4. pidstat - 进程资源统计
pidstat -u -p <pid> 1 10  # 查看进程CPU使用
pidstat -w -p <pid> 1 10  # 查看进程上下文切换
pidstat -d -p <pid> 1 10  # 查看进程IO

# 5. sar - 系统活动报告
sar -u 1 10               # CPU使用率
sar -q 1 10               # 系统负载
sar -w 1 10               # 上下文切换
# sar需要安装sysstat，适合历史数据分析

# 6. perf - 性能分析神器
perf top                  # 实时查看函数CPU占用
perf record -g -p <pid>   # 记录性能数据
perf report               # 生成报告
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg
```

### 2. JVM层面工具

```bash
# 1. jps - Java进程查看
jps -lvm                  # 查看所有Java进程及参数

# 2. jstack - 线程堆栈分析
jstack <pid> > thread_dump.txt            # 导出线程堆栈
jstack -l <pid> > thread_dump_locks.txt   # 包含锁信息

# 3. jstat - JVM统计监控
jstat -gcutil <pid> 1000 10               # GC统计
jstat -gccause <pid> 1000 10              # GC原因

# 4. jmap - 内存分析
jmap -heap <pid>                          # 堆内存摘要
jmap -histo:live <pid> | head -20         # 存活对象统计

# 5. arthas - 在线诊断工具
# 安装：java -jar arthas-boot.jar
dashboard                                # 实时仪表板
thread -n 3                              # 最忙的3个线程
profiler start                           # 开始CPU采样
profiler stop                            # 停止并生成火焰图
```

### 3. 应用层面工具

```bash
# 1. 应用日志分析
grep -n "ERROR\|WARN\|Exception" app.log | tail -100
tail -f app.log | grep -A 10 -B 10 "high cpu"

# 2. 业务指标监控
# 查看QPS、响应时间、错误率等业务指标
# 确认是否业务流量突增导致

# 3. APM工具（SkyWalking、Pinpoint等）
# 查看调用链，定位慢方法
# 查看数据库慢查询
```

## 📖 常见场景与排查

### 场景1：死循环

```bash
# 现象：单个线程CPU 100%
# 排查步骤：

# 1. top找到高CPU进程和线程
top -H -p <pid>
# 发现线程12345占用100% CPU

# 2. 线程ID转为十六进制
printf "%x\n" 12345  # 输出：3039

# 3. jstack分析线程堆栈
jstack <pid> | grep -A 20 -B 5 "nid=0x3039"

# 输出示例：
"Thread-1" #10 prio=5 os_prio=0 tid=0x00007f8b1c0e8000 nid=0x3039 runnable [0x00007f8b0b7f1000]
   java.lang.Thread.State: RUNNABLE
        at com.example.BadService.infiniteLoop(BadService.java:25)
        at com.example.BadService.lambda$start$0(BadService.java:18)
        at com.example.BadService$$Lambda$1/1078694789.run(Unknown Source)
        at java.lang.Thread.run(Thread.java:748)

# 4. 定位代码
public class BadService {
    public void infiniteLoop() {
        while (true) {           // ❌ 死循环
            // 做一些计算
            int result = 1 + 1;
        }
    }
}

# 解决方案：
# 1. 添加循环终止条件
# 2. 添加Thread.sleep避免空转
# 3. 使用中断机制
```

### 场景2：频繁GC

```bash
# 现象：周期性CPU尖刺，伴随频繁GC
# 排查步骤：

# 1. jstat查看GC情况
jstat -gcutil <pid> 1000
# 输出：
  S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGCT     GCT
  0.00  96.88  25.25  87.50  94.82  92.19   3220   63.451    12    3.240   66.691

# 关注：YGC（Young GC次数）增长快，FGC（Full GC次数）也在增长

# 2. 查看GC日志（如果配置了）
# -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/tmp/gc.log

# 3. 分析内存使用
jmap -histo:live <pid> | head -20
# 发现大量相同类型的对象

# 4. 定位代码
public class CacheService {
    private static final List<byte[]> CACHE = new ArrayList<>();
    
    public void addToCache(byte[] data) {
        CACHE.add(data);  // ❌ 内存泄漏，无限增长
    }
}

# 解决方案：
# 1. 修复内存泄漏
# 2. 调整JVM参数（增大堆内存，调整GC策略）
# 3. 使用合适的缓存策略（LRU、带过期时间）
```

### 场景3：锁竞争

```bash
# 现象：CPU使用率不高但负载高，大量线程处于BLOCKED状态
# 排查步骤：

# 1. jstack查看线程状态
jstack <pid> | grep "java.lang.Thread.State" | sort | uniq -c
# 输出：
   50  java.lang.Thread.State: RUNNABLE
   30  java.lang.Thread.State: BLOCKED (on object monitor)
   20  java.lang.Thread.State: WAITING (on object monitor)

# 2. 查看BLOCKED线程详情
jstack <pid> | grep -B 5 -A 10 "BLOCKED"

# 3. 定位锁竞争代码
public class OrderService {
    private static final Object globalLock = new Object();  // ❌ 全局锁
    
    public void processOrder(Order order) {
        synchronized (globalLock) {  // 所有订单竞争同一把锁
            // 处理订单，耗时操作
            Thread.sleep(100);
        }
    }
}

# 解决方案：
# 1. 减小锁粒度（使用细粒度锁）
# 2. 使用读写锁（ReentrantReadWriteLock）
# 3. 使用无锁数据结构（ConcurrentHashMap）
# 4. 使用乐观锁（CAS操作）
```

### 场景4：正则表达式灾难

```bash
# 现象：处理特定输入时CPU突然飙升
# 排查步骤：

# 1. arthas监控方法执行时间
watch com.example.TextProcessor process '{params, returnObj, throwExp}' -x 3

# 2. 发现特定输入导致方法执行时间极长

# 3. 定位代码
public class TextProcessor {
    public boolean validate(String input) {
        // ❌ 灾难性回溯的正则表达式
        return input.matches("(a+)+b");
        // 输入：aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!
        // 会导致指数级时间增长
    }
}

# 解决方案：
# 1. 优化正则表达式，避免回溯
# 2. 限制输入长度
# 3. 使用更简单的字符串匹配
# 4. 设置超时时间
```

### 场景5：数学计算密集

```bash
# 现象：CPU持续高位，但业务量不大
# 排查步骤：

# 1. perf top查看热点函数
perf top -p <pid>

# 2. 发现数学计算函数占用高CPU

# 3. 定位代码
public class Calculator {
    public BigDecimal calculatePi(int precision) {
        // ❌ 高精度计算，CPU密集
        BigDecimal pi = BigDecimal.ZERO;
        for (int i = 0; i < 1000000; i++) {
            // 复杂的数学计算
            pi = pi.add(calculateTerm(i));
        }
        return pi;
    }
}

# 解决方案：
# 1. 算法优化（使用更高效的算法）
# 2. 结果缓存（相同输入直接返回缓存结果）
# 3. 异步计算（不阻塞主线程）
# 4. 使用本地库（如JNI调用C++数学库）
```

## 📖 实战排查案例

### 案例1：电商大促期间CPU 100%

```bash
# 问题描述：
# 双11大促期间，订单服务CPU突然飙升至100%
# 接口响应时间从50ms上升至5s+
# 错误率从0.01%上升至5%

# 排查步骤：
# 1. 快速止血：扩容实例，增加机器
# 2. top查看：发现Java进程CPU 450%
# 3. top -H查看：多个线程CPU都很高
# 4. jstack分析：发现大量线程在同一个方法

# 线程堆栈片段：
"http-nio-8080-exec-1" #31 daemon prio=5 os_prio=0 tid=0x00007f8b1c0e8000 nid=0x3039 runnable [0x00007f8b0b7f1000]
   java.lang.Thread.State: RUNNABLE
        at java.util.regex.Pattern$GroupHead.match(Pattern.java:4668)
        at java.util.regex.Pattern$Loop.match(Pattern.java:4795)
        at java.util.regex.Pattern$GroupTail.match(Pattern.java:4727)
        at java.util.regex.Pattern$BranchConn.match(Pattern.java:4578)
        at java.util.regex.Pattern$CharProperty.match(Pattern.java:3777)
        at java.util.regex.Pattern$Branch.match(Pattern.java:4606)
        at java.util.regex.Pattern$GroupHead.match(Pattern.java:4668)
        at java.util.regex.Pattern.match(Pattern.java:1134)
        at java.util.regex.Matcher.find(Matcher.java:1248)
        at com.example.OrderService.validateOrderNo(OrderService.java:123)

# 5. 定位代码：
public class OrderService {
    private static final Pattern ORDER_NO_PATTERN = 
        Pattern.compile("^\\d{4}-\\d{2}-\\d{2}-[A-Z]{3}-\\d{6}$");
    
    public boolean validateOrderNo(String orderNo) {
        // 大促期间订单号格式错误的数据增多
        // 错误订单号： "2023-11-11-XXX-123" （XXX不是三个大写字母）
        return ORDER_NO_PATTERN.matcher(orderNo).matches();  // ❌ 正则回溯
    }
}

# 6. 解决方案：
# 短期：修改正则，避免回溯 ^\\d{4}-\\d{2}-\\d{2}-[A-Z]{3}-\\d{6}$
# 改为分段验证，避免复杂正则
public boolean validateOrderNoFixed(String orderNo) {
    if (orderNo == null || orderNo.length() != 20) return false;
    // 分段验证
    if (!orderNo.substring(0, 4).matches("\\d{4}")) return false;
    if (!orderNo.substring(5, 7).matches("\\d{2}")) return false;
    // ... 其他段验证
    return true;
}

# 长期：添加输入校验，异常订单直接拒绝
# 添加限流，保护核心服务
```

### 案例2：定时任务导致CPU周期性尖刺

```bash
# 问题描述：
# 每天凌晨2点，系统CPU出现周期性尖刺
# 持续时间约30分钟，影响用户体验

# 排查步骤：
# 1. 查看监控图表，确认周期性规律
# 2. 查看定时任务配置，发现凌晨2点有数据统计任务
# 3. arthas监控方法执行

# 4. 定位代码：
@Component
public class DailyStatTask {
    @Scheduled(cron = "0 0 2 * * ?")  // 每天凌晨2点执行
    public void generateDailyReport() {
        // 全表扫描，复杂计算
        List<Order> allOrders = orderRepository.findAll();  // ❌ 百万级数据
        Map<Long, BigDecimal> userStats = new HashMap<>();
        
        for (Order order : allOrders) {
            // 复杂统计计算，CPU密集
            BigDecimal amount = userStats.getOrDefault(order.getUserId(), BigDecimal.ZERO);
            userStats.put(order.getUserId(), amount.add(order.getAmount()));
        }
    }
}

# 5. 解决方案：
# 方案1：分批次处理
public void generateDailyReportBatch() {
    int page = 0;
    int size = 1000;
    List<Order> orders;
    
    do {
        orders = orderRepository.findPage(page, size);
        processBatch(orders);
        page++;
    } while (!orders.isEmpty());
}

# 方案2：使用数据库聚合
public void generateDailyReportSql() {
    // 使用SQL直接统计，减少数据传输和Java计算
    String sql = "SELECT user_id, SUM(amount) FROM orders " +
                 "WHERE created_at >= ? AND created_at < ? " +
                 "GROUP BY user_id";
    // 执行SQL，直接获取结果
}

# 方案3：调整执行时间
# 改到业务低峰期执行，如凌晨4点
# 或周末执行
```

### 案例3：线程池配置不当

```bash
# 问题描述：
# 系统上线新功能后，CPU使用率从30%升至80%
# 接口响应时间变长，但QPS没有明显增长

# 排查步骤：
# 1. top查看：CPU主要在user态，说明是应用代码
# 2. jstack查看：大量线程处于RUNNABLE状态
# 3. 查看线程池配置

# 4. 定位代码：
@Configuration
public class ThreadPoolConfig {
    @Bean
    public ExecutorService taskExecutor() {
        // ❌ 线程池配置过大
        return Executors.newFixedThreadPool(200);  // 线程太多！
    }
}

@Service
public class ImageProcessService {
    @Autowired
    private ExecutorService executor;
    
    public void processImages(List<Image> images) {
        List<Future> futures = new ArrayList<>();
        for (Image image : images) {
            futures.add(executor.submit(() -> {
                // CPU密集的图像处理
                return processImage(image);
            }));
        }
        // 等待所有任务完成
    }
}

# 5. 问题分析：
# 200个线程并发执行CPU密集型任务
# 超出CPU核心数（假设32核），导致大量上下文切换
# 线程竞争CPU，实际效率下降

# 6. 解决方案：
# 合理配置线程池大小
# CPU密集型任务：核心数 + 1
# IO密集型任务：核心数 × 2
@Bean
public ExecutorService taskExecutor() {
    int corePoolSize = Runtime.getRuntime().availableProcessors() + 1;
    return new ThreadPoolExecutor(
        corePoolSize,      // 核心线程数
        corePoolSize * 2,  // 最大线程数
        60L, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(1000),
        new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略：调用者运行
    );
}
```

## 📖 预防与优化

### 1. 代码层面预防

```java
/**
 * CPU问题代码规范
 */
public class CPUSafeCode {
    
    // 1. 避免死循环
    public void safeLoop() {
        // 设置明确的终止条件
        int maxIterations = 1000;
        for (int i = 0; i < maxIterations; i++) {
            // 业务逻辑
        }
        
        // 或者使用超时控制
        long startTime = System.currentTimeMillis();
        while (condition) {
            if (System.currentTimeMillis() - startTime > 5000) {
                throw new TimeoutException("操作超时");
            }
            // 业务逻辑
        }
    }
    
    // 2. 合理使用正则表达式
    public class RegexSafety {
        // 避免灾难性回溯
        private static final Pattern SAFE_PATTERN = Pattern.compile("^\\w{1,50}$");
        
        // 设置超时（Java 9+）
        public boolean safeMatch(String input) {
            Matcher matcher = SAFE_PATTERN.matcher(input);
            try {
                return matcher.find(100);  // 100ms超时
            } catch (Exception e) {
                return false;
            }
        }
    }
    
    // 3. 优化算法复杂度
    public class AlgorithmOptimization {
        // 使用高效算法
        public int findMax(int[] array) {
            // O(n) 替代 O(n²)
            int max = Integer.MIN_VALUE;
            for (int num : array) {
                if (num > max) max = num;
            }
            return max;
        }
        
        // 使用缓存避免重复计算
        private Map<Integer, BigInteger> factorialCache = new ConcurrentHashMap<>();
        
        public BigInteger factorial(int n) {
            return factorialCache.computeIfAbsent(n, k -> {
                if (n <= 1) return BigInteger.ONE;
                return factorial(n - 1).multiply(BigInteger.valueOf(n));
            });
        }
    }
    
    // 4. 合理使用线程池
    public class ThreadPoolBestPractice {
        private ExecutorService executor = new ThreadPoolExecutor(
            Runtime.getRuntime().availableProcessors(),  // 核心线程数
            Runtime.getRuntime().availableProcessors() * 2,  // 最大线程数
            60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),
            new NamedThreadFactory("cpu-intensive"),
            new ThreadPoolExecutor.CallerRunsPolicy()  // 饱和策略
        );
        
        // 监控线程池状态
        public void monitorThreadPool() {
            ThreadPoolExecutor tpe = (ThreadPoolExecutor) executor;
            log.info("Active threads: {}", tpe.getActiveCount());
            log.info("Queue size: {}", tpe.getQueue().size());
            log.info("Completed tasks: {}", tpe.getCompletedTaskCount());
        }
    }
}
```

### 2. 监控预警体系

```yaml
# 监控配置示例
monitoring:
  # CPU相关监控
  cpu:
    # 系统CPU
    - name: system_cpu_usage
      query: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
      threshold: 80  # 告警阈值80%
      duration: 5m   # 持续5分钟触发
    
    # 进程CPU
    - name: process_cpu_usage
      query: rate(process_cpu_seconds_total[5m]) * 100
      threshold: 90
    
    # 单核CPU
    - name: single_core_cpu
      query: 100 - (avg by (cpu, instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
      threshold: 95  # 单核95%告警
    
    # 系统负载
    - name: system_load
      query: node_load1
      threshold: cpu_cores * 2  # 负载超过核心数2倍
    
    # 上下文切换
    - name: context_switches
      query: rate(node_context_switches_total[5m])
      threshold: 10000  # 每秒1万次
  
  # JVM监控
  jvm:
    # GC暂停时间
    - name: gc_pause_time
      query: rate(jvm_gc_pause_seconds_sum[5m])
      threshold: 0.5  # 每秒GC暂停0.5秒
    
    # 线程数
    - name: thread_count
      query: jvm_threads_live_threads
      threshold: 500
  
  # 应用监控
  application:
    # 接口响应时间
    - name: api_response_time_p99
      query: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
      threshold: 1.0  # P99超过1秒
    
    # 慢查询
    - name: slow_sql_count
      query: rate(mysql_slow_queries_total[5m])
      threshold: 10  # 每秒10个慢查询
```

### 3. 应急预案

```java
/**
 * CPU问题应急预案
 */
public class CPUEmergencyPlan {
    
    // 1. 快速诊断checklist
    public class QuickDiagnosis {
        public void diagnose() {
            // Step 1: 查看系统资源
            exec("top -b -n 1 | head -20");
            exec("vmstat 1 5");
            
            // Step 2: 找到问题进程
            exec("ps aux --sort=-%cpu | head -10");
            
            // Step 3: 如果是Java进程
            exec("jstack <pid> > /tmp/thread_dump_$(date +%s).txt");
            exec("jstat -gcutil <pid> 1000 10");
            
            // Step 4: 业务指标检查
            checkQPS();
            checkErrorRate();
            checkSlowQueries();
        }
    }
    
    // 2. 快速恢复措施
    public class QuickRecovery {
        // 措施1：重启实例（最粗暴但有效）
        public void restartInstance() {
            // 优雅关闭，保留现场
            dumpThreads();
            dumpHeap();
            // 然后重启
        }
        
        // 措施2：流量调度
        public void scheduleTraffic() {
            // 将流量切到健康实例
            // 使用负载均衡器或网关
        }
        
        // 措施3：降级/熔断
        public void degradeFeature() {
            // 关闭非核心功能
            // 返回缓存数据
            // 限流保护核心功能
        }
    }
    
    // 3. 根本解决方案
    public class RootCauseSolution {
        // 方案1：代码优化
        public void optimizeCode() {
            // 修复死循环
            // 优化算法
            // 减少锁竞争
        }
        
        // 方案2：配置优化
        public void optimizeConfig() {
            // 调整JVM参数
            // 调整线程池配置
            // 调整数据库连接池
        }
        
        // 方案3：架构优化
        public void optimizeArchitecture() {
            // 引入缓存
            // 异步处理
            // 服务拆分
        }
    }
}
```

## 📖 面试真题

### Q1: 如何快速定位CPU 100%问题？

**答：**
1. **系统层面**：使用top找到高CPU进程，top -H找到高CPU线程
2. **进程层面**：如果是Java进程，使用jstack分析线程堆栈
3. **线程分析**：将线程ID转为十六进制，在jstack输出中查找对应线程
4. **代码定位**：根据线程堆栈定位到具体代码行
5. **原因分析**：常见原因包括死循环、频繁GC、锁竞争、算法复杂等
6. **解决方案**：根据具体原因修复代码或调整配置

### Q2: 如何区分用户态CPU高和内核态CPU高？

**答：**
1. **查看top输出**：
   - us（用户态）：应用程序代码消耗的CPU
   - sy（内核态）：系统调用消耗的CPU
   
2. **用户态CPU高**：通常是应用代码问题，如死循环、复杂计算
3. **内核态CPU高**：通常是系统调用频繁，如大量IO、网络操作、锁竞争
4. **使用pidstat区分**：pidstat -u -t -p <pid> 可以查看线程级别的用户态和内核态CPU

### Q3: 如何排查死锁导致的CPU问题？

**答：**
1. **现象识别**：CPU使用率不高但负载高，大量线程BLOCKED
2. **jstack分析**：jstack <pid> | grep -A 10 -B 5 "BLOCKED"
3. **查找死锁**：jstack输出末尾会有死锁检测结果
4. **分析锁依赖**：查看哪些线程持有什么锁，等待什么锁
5. **代码修复**：
   - 保证锁的获取顺序一致
   - 使用tryLock设置超时
   - 减小锁粒度
   - 使用无锁数据结构

### Q4: 如何预防CPU问题？

**答：**
1. **代码规范**：避免死循环、优化算法、合理使用正则
2. **资源限制**：设置线程池大小、连接池大小、超时时间
3. **监控预警**：建立完善的监控体系，设置合理的告警阈值
4. **压测验证**：定期进行压力测试，发现性能瓶颈
5. **容量规划**：根据业务增长规划资源，提前扩容
6. **应急预案**：制定应急预案，快速响应问题

### Q5: CPU问题和内存问题如何关联分析？

**答：**
1. **频繁GC导致CPU高**：垃圾回收消耗CPU资源
2. **内存泄漏导致OOM**：最终可能引发频繁GC
3. **分析工具结合**：
   - jstat查看GC情况
   - jmap分析内存使用
   - jstack分析线程状态
4. **典型场景**：
   - 内存泄漏 → 频繁GC → CPU升高
   - 大对象创建 → Young GC频繁 → CPU周期性尖刺
   - 元空间不足 → Full GC → CPU短暂100%
5. **综合解决方案**：既要优化内存使用，也要调整GC策略

## 📚 延伸阅读

- [Linux性能优化实战](https://time.geekbang.org/column/intro/140)
- [Java性能权威指南](https://book.douban.com/subject/26740520/)
- [Brendan Gregg的性能分析博客](http://www.brendangregg.com/)
- [Oracle官方性能调优指南](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/performance-enhancements-7.html)

---

**⭐ 重点：CPU问题排查需要系统化的工具链和方法论，从现象到根因，从应急到预防，建立完整的性能保障体系**