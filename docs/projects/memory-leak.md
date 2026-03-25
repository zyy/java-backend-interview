---
layout: default
title: 内存泄漏排查实战
---
# 内存泄漏排查实战

> 从缓慢死亡到精准定位：内存泄漏全链路排查指南

## 🎯 面试重点

- 内存泄漏原理与常见场景
- 内存分析工具链使用
- 堆转储文件分析与解读
- 内存泄漏预防与监控

## 📖 内存泄漏原理

### 1. Java内存管理基础

```java
/**
 * Java内存回收机制
 */
public class MemoryManagement {
    
    // GC Roots 对象
    /*
     * 1. 虚拟机栈中引用的对象
     * 2. 方法区中类静态属性引用的对象
     * 3. 方法区中常量引用的对象
     * 4. 本地方法栈中JNI引用的对象
     * 5. Java虚拟机内部的引用
     * 6. 被同步锁持有的对象
     */
    
    // 可达性分析算法
    /*
     * GC Roots -> 对象A -> 对象B -> 对象C
     * 从GC Roots开始，标记所有可达对象
     * 不可达对象将被回收
     */
    
    // 内存泄漏定义
    /*
     * 对象已经不再使用，但因为某些原因仍然被GC Roots引用
     * 导致无法被垃圾回收器回收
     * 最终导致内存耗尽，OOM
     */
}
```

### 2. 内存泄漏 vs 内存溢出

```java
/**
 * 内存泄漏与内存溢出的区别
 */
public class MemoryLeakVsOOM {
    
    // 内存泄漏（Memory Leak）
    /*
     * 特征：内存缓慢增长，最终耗尽
     * 原因：代码缺陷，对象无法被回收
     * 现象：应用运行时间越长，内存使用越高
     * 解决：修复代码，释放无用对象引用
     */
    
    // 内存溢出（Out of Memory）
    /*
     * 特征：内存突然耗尽
     * 原因：内存配置不足，或一次性申请过大内存
     * 现象：应用突然崩溃，抛出OOM异常
     * 解决：增加内存，或优化内存使用
     */
    
    // 关系
    /*
     * 内存泄漏是内存溢出的常见原因
     * 但内存溢出不一定由内存泄漏引起
     * 也可能是合理的内存使用超过了配置
     */
}
```

## 📖 常见内存泄漏场景

### 1. 静态集合类泄漏

```java
/**
 * 最常见的泄漏场景：静态集合
 */
public class StaticCollectionLeak {
    
    // ❌ 错误示例：静态集合无限增长
    private static final Map<String, Object> CACHE = new HashMap<>();
    
    public void addToCache(String key, Object value) {
        CACHE.put(key, value);  // 永远不会被移除
    }
    
    public Object getFromCache(String key) {
        return CACHE.get(key);
    }
    
    // 问题：随着时间推移，CACHE会无限增长
    // 即使某些数据不再需要，也无法被GC回收
    
    // ✅ 解决方案1：使用WeakHashMap
    private static final Map<String, Object> WEAK_CACHE = new WeakHashMap<>();
    // 当key没有强引用时，entry会被自动移除
    
    // ✅ 解决方案2：使用LRU缓存
    private static final Map<String, Object> LRU_CACHE = 
        Collections.synchronizedMap(new LinkedHashMap<String, Object>(100, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry eldest) {
                return size() > 1000;  // 限制大小
            }
        });
    
    // ✅ 解决方案3：使用带过期时间的缓存（如Caffeine）
    private Cache<String, Object> caffeineCache = Caffeine.newBuilder()
        .maximumSize(1000)
        .expireAfterWrite(10, TimeUnit.MINUTES)
        .recordStats()
        .build();
}
```

### 2. 监听器与回调泄漏

```java
/**
 * 监听器未正确移除导致的泄漏
 */
public class ListenerLeak {
    
    // ❌ 错误示例：监听器未移除
    public class EventSource {
        private List<EventListener> listeners = new ArrayList<>();
        
        public void addListener(EventListener listener) {
            listeners.add(listener);
        }
        
        // 缺少removeListener方法！
    }
    
    public class EventListener {
        private EventSource source;
        
        public EventListener(EventSource source) {
            this.source = source;
            source.addListener(this);  // 注册自己
        }
        
        // 当EventListener不再使用时，仍然被EventSource引用
        // 形成循环引用：EventSource -> listeners -> EventListener -> EventSource
    }
    
    // ✅ 解决方案：正确管理监听器生命周期
    public class FixedEventSource {
        private List<EventListener> listeners = new ArrayList<>();
        
        public void addListener(EventListener listener) {
            listeners.add(listener);
        }
        
        public void removeListener(EventListener listener) {
            listeners.remove(listener);
        }
        
        // 或者使用弱引用
        private List<WeakReference<EventListener>> weakListeners = new ArrayList<>();
        
        public void addWeakListener(EventListener listener) {
            weakListeners.add(new WeakReference<>(listener));
        }
    }
    
    public class FixedEventListener {
        private EventSource source;
        
        public FixedEventListener(EventSource source) {
            this.source = source;
            source.addListener(this);
        }
        
        public void destroy() {
            // 明确移除监听器
            source.removeListener(this);
            this.source = null;  // 断开引用
        }
    }
}
```

### 3. ThreadLocal泄漏

```java
/**
 * ThreadLocal使用不当导致的泄漏
 */
public class ThreadLocalLeak {
    
    // ❌ 错误示例：使用static ThreadLocal且不清理
    private static final ThreadLocal<SimpleDateFormat> DATE_FORMAT =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));
    
    public String formatDate(Date date) {
        return DATE_FORMAT.get().format(date);  // 每次调用都会创建SimpleDateFormat
    }
    
    // 问题：线程池中的线程会复用
    // ThreadLocal中的SimpleDateFormat会一直存在，直到线程销毁
    
    // ✅ 解决方案1：使用后清理
    public String formatDateWithCleanup(Date date) {
        try {
            return DATE_FORMAT.get().format(date);
        } finally {
            // 重要：使用后清理
            DATE_FORMAT.remove();
        }
    }
    
    // ✅ 解决方案2：使用FastDateFormat（线程安全）
    private static final FastDateFormat FAST_DATE_FORMAT = 
        FastDateFormat.getInstance("yyyy-MM-dd");
    
    public String formatDateFast(Date date) {
        return FAST_DATE_FORMAT.format(date);  // 线程安全，无需ThreadLocal
    }
    
    // ✅ 解决方案3：使用DateTimeFormatter（Java 8+）
    private static final DateTimeFormatter FORMATTER = 
        DateTimeFormatter.ofPattern("yyyy-MM-dd");
    
    public String formatDateJava8(LocalDate date) {
        return date.format(FORMATTER);  // 线程安全
    }
}
```

### 4. 内部类持有外部类引用

```java
/**
 * 匿名内部类/非静态内部类泄漏
 */
public class InnerClassLeak {
    
    // ❌ 错误示例：Handler持有Activity引用（Android常见）
    public class Activity {
        private Handler handler = new Handler() {
            @Override
            public void handleMessage(Message msg) {
                // 隐式持有Activity实例
                updateUI();
            }
        };
        
        // 发送延迟消息
        public void scheduleTask() {
            handler.sendEmptyMessageDelayed(0, 60000);  // 60秒后执行
        }
        
        // Activity销毁时
        public void onDestroy() {
            // 如果没有移除消息，Handler仍然持有Activity引用
            // 导致Activity无法被回收
        }
    }
    
    // ✅ 解决方案1：使用静态内部类 + 弱引用
    public class FixedActivity {
        private static class SafeHandler extends Handler {
            private final WeakReference<FixedActivity> activityRef;
            
            public SafeHandler(FixedActivity activity) {
                this.activityRef = new WeakReference<>(activity);
            }
            
            @Override
            public void handleMessage(Message msg) {
                FixedActivity activity = activityRef.get();
                if (activity != null) {
                    activity.updateUI();
                }
            }
        }
        
        private final Handler handler = new SafeHandler(this);
        
        public void onDestroy() {
            handler.removeCallbacksAndMessages(null);  // 清理所有消息
        }
    }
    
    // ✅ 解决方案2：使用静态方法
    public class BetterActivity {
        private static void handleMessageStatic(Message msg, BetterActivity activity) {
            // 静态方法不持有实例引用
            if (activity != null) {
                activity.updateUI();
            }
        }
        
        private Handler handler = new Handler() {
            @Override
            public void handleMessage(Message msg) {
                handleMessageStatic(msg, BetterActivity.this);
            }
        };
    }
}
```

### 5. 连接未关闭

```java
/**
 * 资源未关闭导致的泄漏
 */
public class ResourceLeak {
    
    // ❌ 错误示例：各种连接未关闭
    public void readFile(String path) {
        try {
            FileInputStream fis = new FileInputStream(path);
            // 使用fis...
            // ❌ 忘记关闭！
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    
    public void queryDatabase() {
        Connection conn = null;
        Statement stmt = null;
        ResultSet rs = null;
        
        try {
            conn = dataSource.getConnection();
            stmt = conn.createStatement();
            rs = stmt.executeQuery("SELECT * FROM users");
            // 处理结果...
            
            // ❌ 在异常时可能不会执行关闭代码
            rs.close();
            stmt.close();
            conn.close();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
    
    // ✅ 解决方案1：使用try-with-resources（Java 7+）
    public void readFileSafe(String path) {
        try (FileInputStream fis = new FileInputStream(path);
             InputStreamReader isr = new InputStreamReader(fis);
             BufferedReader br = new BufferedReader(isr)) {
            
            String line;
            while ((line = br.readLine()) != null) {
                // 处理每一行
            }
            // 自动关闭所有资源
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    
    // ✅ 解决方案2：使用模板方法模式
    public class JdbcTemplate {
        public <T> T execute(ConnectionCallback<T> action) {
            Connection conn = null;
            try {
                conn = dataSource.getConnection();
                return action.doInConnection(conn);
            } catch (SQLException e) {
                throw new RuntimeException(e);
            } finally {
                closeConnection(conn);
            }
        }
        
        private void closeConnection(Connection conn) {
            if (conn != null) {
                try {
                    conn.close();
                } catch (SQLException e) {
                    // 记录日志，但不抛出异常
                    log.error("关闭连接失败", e);
                }
            }
        }
    }
}
```

## 📖 排查工具链

### 1. 监控工具

```bash
# 1. jstat - JVM统计监控
jstat -gcutil <pid> 1000 10  # 每秒采样，共10次
# 输出：
#  S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGC    FGCT     GCT
#  0.00  96.88  25.25  87.50  94.82  92.19   3220   63.451    12    3.240   66.691
# 关注：O（老年代使用率）持续增长，说明可能有内存泄漏

# 2. jmap - 内存分析
jmap -heap <pid>                # 堆内存摘要
jmap -histo <pid> | head -20    # 对象统计（直方图）
jmap -histo:live <pid> | head -20  # 存活对象统计
jmap -dump:live,format=b,file=heap.hprof <pid>  # 导出堆转储

# 3. VisualVM / JConsole - 图形化监控
# 实时查看内存使用趋势、GC活动、线程状态等
# 可以生成堆转储，进行内存分析

# 4. Eclipse MAT（Memory Analyzer Tool） - 堆转储分析
# 功能强大，可以：
# - 查找最大的对象
# - 分析支配树（Dominator Tree）
# - 查找内存泄漏嫌疑
# - 分析GC Roots路径
```

### 2. 堆转储分析实战

```bash
# 生成堆转储
# 方式1：jmap命令
jmap -dump:live,format=b,file=heap.hprof <pid>

# 方式2：JVM参数（OOM时自动生成）
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/heapdump.hprof

# 方式3：通过JMX
jcmd <pid> GC.heap_dump /tmp/heapdump.hprof

# 分析堆转储
# 1. 使用jhat（Java内置，功能简单）
jhat heap.hprof
# 访问 http://localhost:7000

# 2. 使用Eclipse MAT（推荐）
# 下载：https://www.eclipse.org/mat/
# 打开heap.hprof文件

# 3. 使用VisualVM
# 文件 -> 装入 -> 选择heap.hprof

# 4. 使用命令行工具（快速分析）
jmap -histo heap.hprof | head -50
```

### 3. MAT分析技巧

```java
/**
 * Eclipse MAT 常用分析功能
 */
public class MATAnalysis {
    
    // 1. 泄漏嫌疑报告（Leak Suspects）
    /*
     * MAT会自动分析可能的泄漏点
     * 显示最大的对象和保留集（Retained Set）
     */
    
    // 2. 直方图（Histogram）
    /*
     * 按类统计对象数量和内存占用
     * 重点关注：
     * - char[]（字符串内部）
     * - byte[]
     * - HashMap$Node
     * - 自定义业务对象
     */
    
    // 3. 支配树（Dominator Tree）
    /*
     * 显示对象的支配关系
     * 如果一个对象支配了大量内存，可能是泄漏点
     */
    
    // 4. 路径到GC Roots（Path to GC Roots）
    /*
     * 查看对象到GC Roots的引用路径
     * 理解为什么对象无法被回收
     * 排除弱引用、软引用等
     */
    
    // 5. OQL（Object Query Language）
    /*
     * 类似SQL的查询语言，查询堆中的对象
     * 示例：
     * SELECT * FROM java.util.HashMap
     * SELECT toString(s) FROM java.lang.String s WHERE s.count > 1000
     */
}
```

## 📖 实战排查案例

### 案例1：缓存服务内存泄漏

```bash
# 问题描述：
# 缓存服务运行一周后，内存使用从2G增长到8G（堆内存8G）
# Full GC频繁，应用响应变慢

# 排查步骤：
# 1. jstat监控发现老年代使用率持续增长
jstat -gcutil 1234 1000

# 输出：
Time   S0   S1    E     O      M     CCS    YGC   YGCT  FGC  FGCT   GCT
14:30  0.0 100.0 25.6  85.4   94.2  91.8   450   12.3   8    4.2   16.5
14:31  0.0 100.0 30.1  86.2   94.2  91.8   451   12.4   8    4.2   16.6
14:32  0.0 100.0 35.4  87.1   94.2  91.8   452   12.5   8    4.2   16.7
# O（老年代）持续增长，从85.4% -> 86.2% -> 87.1%

# 2. 生成堆转储
jmap -dump:live,format=b,file=cache_heap.hprof 1234

# 3. MAT分析
# 打开cache_heap.hprof，查看泄漏嫌疑报告

# 4. 发现可疑对象
Leak Suspects
Problem Suspect 1
The thread java.lang.Thread @ 0x7c006020 main keeps local variables with total size 1,234,567,890 bytes (45.67%) in memory.

Details:
- java.util.HashMap @ 0x7d001234 - 800 MB
  -> table array of java.util.HashMap$Node[1048576] @ 0x7d001240 - 800 MB
  -> ... many entries ...

# 5. 查看HashMap内容
# 在支配树中找到这个HashMap，查看内容
# 发现是全局的UserCache，存储了所有用户数据

# 6. 定位代码
public class UserCacheService {
    private static final Map<Long, User> USER_CACHE = new HashMap<>();
    
    public User getUser(Long userId) {
        return USER_CACHE.computeIfAbsent(userId, id -> {
            // 从数据库加载
            User user = userDao.findById(id);
            return user;
        });
    }
    
    // ❌ 问题：没有缓存淘汰策略
    // 随着用户量增长，缓存无限扩大
}

# 7. 解决方案
# 方案1：添加缓存淘汰策略
private static final Map<Long, User> USER_CACHE = 
    Collections.synchronizedMap(new LinkedHashMap<Long, User>(10000, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry eldest) {
            return size() > 10000;  // 最多缓存1万用户
        }
    });

# 方案2：使用Caffeine缓存
private Cache<Long, User> userCache = Caffeine.newBuilder()
    .maximumSize(10000)
    .expireAfterAccess(1, TimeUnit.HOURS)
    .recordStats()
    .build();

# 方案3：按业务拆分缓存
# 活跃用户缓存时间长，非活跃用户缓存时间短
```

### 案例2：线程池内存泄漏

```bash
# 问题描述：
# 任务调度服务，每天内存增长2%，一个月后OOM
# 重启后恢复正常，然后再次缓慢增长

# 排查步骤：
# 1. 生成堆转储分析
# 使用MAT分析，发现大量ThreadLocal对象

# 2. 查看ThreadLocal内容
# 发现是SimpleDateFormat对象

# 3. 定位代码
public class DateUtils {
    private static final ThreadLocal<SimpleDateFormat> DATE_FORMATTER =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
    
    public static String format(Date date) {
        return DATE_FORMATTER.get().format(date);
    }
    
    // ❌ 问题：线程池中的线程会复用
    // ThreadLocal中的SimpleDateFormat会一直存在
}

# 4. 验证猜想
# 查看线程池配置
@Bean
public ExecutorService taskExecutor() {
    return Executors.newFixedThreadPool(50);  // 固定线程池
}

# 固定线程池中的线程不会销毁
# ThreadLocal会一直存在，直到线程销毁（也就是应用重启）

# 5. 解决方案
# 方案1：使用后清理ThreadLocal
public static String formatWithCleanup(Date date) {
    try {
        return DATE_FORMATTER.get().format(date);
    } finally {
        DATE_FORMATTER.remove();  // 使用后清理
    }
}

# 方案2：使用线程安全的DateTimeFormatter（Java 8+）
private static final DateTimeFormatter FORMATTER = 
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

public static String formatJava8(LocalDateTime dateTime) {
    return dateTime.format(FORMATTER);  // 线程安全
}

# 方案3：每个任务创建新的SimpleDateFormat
# 虽然创建对象有开销，但避免了泄漏
public static String formatNew(Date date) {
    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
    return sdf.format(date);  // 每次创建新的
}
```

### 案例3：第三方库内存泄漏

```bash
# 问题描述：
# 引入新的JSON解析库后，内存缓慢增长
# 怀疑第三方库有内存泄漏

# 排查步骤：
# 1. 使用jmap直方图对比
# 正常状态
jmap -histo:live <pid> | grep com.alibaba.fastjson

# 运行一段时间后
jmap -histo:live <pid> | grep com.alibaba.fastjson
# 发现fastjson相关对象数量持续增长

# 2. 生成堆转储，使用MAT分析
# 查看fastjson对象的GC Roots路径

# 3. 发现是JSONPath缓存
# fastjson的JSONPath会缓存编译结果
# 但缓存没有大小限制

# 4. 查看fastjson源码
public class JSONPath {
    private static final ConcurrentHashMap<String, JSONPath> pathCache 
        = new ConcurrentHashMap<>();
    
    // 缓存所有编译过的JSONPath
    // 没有淘汰机制
}

# 5. 解决方案
# 方案1：升级fastjson版本（新版本可能已修复）
# 方案2：使用其他JSON库（如Jackson、Gson）
# 方案3：手动清理缓存（如果支持）
JSONPath.clearCache();

# 方案4：限制使用JSONPath
# 避免在循环或高频接口中使用
```

## 📖 预防与最佳实践

### 1. 代码规范

```java
/**
 * 内存安全编码规范
 */
public class MemorySafeCode {
    
    // 1. 集合使用规范
    public class CollectionSafe {
        // 避免使用静态集合
        // 如必须使用，添加大小限制
        private static final int MAX_CACHE_SIZE = 10000;
        private static final Map<String, Object> SAFE_CACHE = 
            Collections.synchronizedMap(new LinkedHashMap<String, Object>(
                MAX_CACHE_SIZE, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry eldest) {
                    return size() > MAX_CACHE_SIZE;
                }
            });
    }
    
    // 2. 资源关闭规范
    public class ResourceSafe {
        // 使用try-with-resources
        public void readFile(String path) {
            try (BufferedReader br = Files.newBufferedReader(Paths.get(path))) {
                String line;
                while ((line = br.readLine()) != null) {
                    processLine(line);
                }
            } catch (IOException e) {
                log.error("读取文件失败", e);
            }
        }
        
        // 自定义资源实现AutoCloseable
        public class DatabaseConnection implements AutoCloseable {
            private Connection conn;
            
            public DatabaseConnection() throws SQLException {
                this.conn = dataSource.getConnection();
            }
            
            @Override
            public void close() {
                if (conn != null) {
                    try {
                        conn.close();
                    } catch (SQLException e) {
                        log.error("关闭数据库连接失败", e);
                    }
                }
            }
        }
    }
    
    // 3. ThreadLocal使用规范
    public class ThreadLocalSafe {
        // 使用static final修饰
        private static final ThreadLocal<SimpleDateFormat> DATE_FORMAT =
            ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));
        
        // 使用后必须清理
        public String formatDate(Date date) {
            try {
                return DATE_FORMAT.get().format(date);
            } finally {
                DATE_FORMAT.remove();  // 重要！
            }
        }
        
        // 或者使用线程安全的替代方案
        private static final DateTimeFormatter FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");
    }
    
    // 4. 监听器与回调规范
    public class ListenerSafe {
        // 使用弱引用
        private List<WeakReference<EventListener>> listeners = new ArrayList<>();
        
        public void addListener(EventListener listener) {
            listeners.add(new WeakReference<>(listener));
        }
        
        // 定期清理失效的弱引用
        public void cleanupListeners() {
            listeners.removeIf(ref -> ref.get() == null);
        }
    }
}
```

### 2. 监控与告警

```yaml
# 内存泄漏监控配置
monitoring:
  # JVM内存监控
  jvm_memory:
    - name: heap_usage
      query: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} * 100
      threshold: 80  # 堆使用超过80%告警
      duration: 5m
    
    - name: old_gen_usage
      query: jvm_memory_pool_used_bytes{pool="Tenured Gen"} / jvm_memory_pool_max_bytes{pool="Tenured Gen"} * 100
      threshold: 85  # 老年代使用超过85%告警
      duration: 10m
    
    - name: metaspace_usage
      query: jvm_memory_pool_used_bytes{pool="Metaspace"} / jvm_memory_pool_max_bytes{pool="Metaspace"} * 100
      threshold: 90  # 元空间使用超过90%告警
  
  # GC监控
  gc:
    - name: full_gc_frequency
      query: increase(jvm_gc_collection_seconds_count{gc="G1 Old Generation"}[5m])
      threshold: 2  # 5分钟内Full GC超过2次告警
    
    - name: gc_pause_time
      query: rate(jvm_gc_collection_seconds_sum[5m])
      threshold: 0.5  # 每秒GC暂停超过0.5秒告警
  
  # 业务监控
  business:
    - name: cache_size
      query: application_cache_size
      threshold: 10000  # 缓存大小超过1万告警
    
    - name: active_connections
      query: database_active_connections
      threshold: 100  # 数据库活跃连接超过100告警
```

### 3. 定期健康检查

```java
/**
 * 内存健康检查框架
 */
public class MemoryHealthCheck {
    
    // 1. 内存使用趋势分析
    public class MemoryTrendAnalyzer {
        public void analyzeTrend() {
            // 获取最近24小时内存使用数据
            List<MemoryUsage> usages = getMemoryUsageHistory(24);
            
            // 分析趋势
            double growthRate = calculateGrowthRate(usages);
            if (growthRate > 5.0) {  // 每小时增长超过5%
                alert("内存泄漏嫌疑：内存持续增长");
                suggestHeapDump();
            }
        }
    }
    
    // 2. 堆转储定期分析
    public class ScheduledHeapDump {
        @Scheduled(cron = "0 0 4 * * ?")  // 每天凌晨4点
        public void dailyHeapAnalysis() {
            // 生成堆转储
            String dumpFile = generateHeapDump();
            
            // 分析堆转储
            HeapAnalysisResult result = analyzeHeapDump(dumpFile);
            
            // 检查可疑点
            if (result.hasSuspiciousObjects()) {
                alert("发现可疑内存对象: " + result.getTopSuspects());
            }
            
            // 清理旧堆转储文件
            cleanupOldDumps();
        }
    }
    
    // 3. 对象数量监控
    public class ObjectCountMonitor {
        public void monitorObjectCounts() {
            // 使用JMX监控关键类的对象数量
            Map<String, Long> objectCounts = getObjectCountsByClass();
            
            // 检查异常增长
            for (Map.Entry<String, Long> entry : objectCounts.entrySet()) {
                String className = entry.getKey();
                Long count = entry.getValue();
                
                Long lastCount = lastCounts.get(className);
                if (lastCount != null) {
                    double growth = (count - lastCount) * 100.0 / lastCount;
                    if (growth > 50.0) {  // 增长超过50%
                        alert(className + " 对象数量异常增长: " + growth + "%");
                    }
                }
                
                lastCounts.put(className, count);
            }
        }
    }
}
```

## 📖 面试真题

### Q1: 如何判断应用是否存在内存泄漏？

**答：**
1. **监控指标**：老年代内存使用率持续增长，不随GC下降
2. **GC日志**：Full GC频率增加，但每次回收的内存越来越少
3. **应用表现**：运行时间越长，内存使用越高，最终OOM
4. **重启验证**：重启后内存恢复正常，然后再次缓慢增长
5. **工具验证**：使用jstat监控，或生成堆转储分析

### Q2: 如何使用MAT分析内存泄漏？

**答：**
1. **生成堆转储**：使用jmap或JVM参数生成heapdump.hprof
2. **打开MAT**：使用Eclipse Memory Analyzer打开堆转储文件
3. **查看泄漏报告**：查看Leak Suspects报告，MAT会自动分析可疑点
4. **分析直方图**：查看占用内存最多的对象类型
5. **查看支配树**：找到支配大量内存的对象
6. **分析GC Roots路径**：查看对象为什么无法被回收
7. **对比堆转储**：生成不同时间点的堆转储，对比对象增长情况

### Q3: ThreadLocal为什么会引起内存泄漏？如何避免？

**答：**
**泄漏原因：**
1. ThreadLocal使用static修饰，生命周期与类相同
2. 线程池中的线程会复用，ThreadLocal会一直存在
3. ThreadLocal的Entry是弱引用，但value是强引用
4. 如果ThreadLocal不再使用，但线程仍然存活，value无法被回收

**避免方法：**
1. **使用后清理**：调用ThreadLocal.remove()
2. **使用try-finally保证清理**
3. **使用线程安全的替代品**：如DateTimeFormatter（Java 8+）
4. **使用自定义ThreadLocal子类**：重写initialValue()，返回可回收对象
5. **避免在线程池中使用ThreadLocal**：如果必须使用，确保清理

### Q4: 如何排查第三方库引起的内存泄漏？

**答：**
1. **隔离测试**：单独测试可疑的第三方库
2. **版本对比**：升级/降级版本，观察内存变化
3. **堆转储分析**：分析堆转储中第三方库的对象
4. **源码审查**：查看第三方库源码，寻找可能的泄漏点
5. **替代方案**：尝试使用其他同类库
6. **监控告警**：监控第三方库的内存使用
7. **社区反馈**：查看GitHub issues，是否有类似问题

### Q5: 线上系统内存泄漏，如何紧急处理？

**答：**
**紧急处理：**
1. **扩容**：增加实例数量，分担压力
2. **重启**：重启有问题实例，快速恢复
3. **降级**：关闭非核心功能，减少内存使用
4. **限流**：限制流量，防止问题扩散

**排查定位：**
1. **生成堆转储**：在重启前生成堆转储
2. **保存日志**：保存GC日志、应用日志
3. **监控分析**：分析监控数据，定位问题时间点
4. **代码审查**：审查最近上线的代码变更

**根治方案：**
1. **修复代码**：根据堆转储分析结果修复泄漏点
2. **增加监控**：增加内存泄漏监控告警
3. **压测验证**：修复后压测验证
4. **复盘总结**：总结问题原因，完善流程

## 📚 延伸阅读

- [Eclipse MAT官方文档](https://www.eclipse.org/mat/documentation/)
- [Java性能权威指南](https://book.douban.com/subject/26740520/)
- [Understanding and Solving Memory Leaks in Java](https://dzone.com/articles/understanding-and-solving-memory-leaks-in-java)
- [Plumbr内存泄漏检测](https://plumbr.io/java-memory-leak)

---

**⭐ 重点：内存泄漏排查需要结合监控、工具分析和代码审查，建立从预防、检测到修复的完整闭环**