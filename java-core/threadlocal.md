# ThreadLocal 原理与内存泄漏 ⭐⭐⭐

## 面试题：ThreadLocal 为什么会内存泄漏？如何解决？

### 核心回答

ThreadLocal 为每个线程提供独立的变量副本，实现线程隔离。但如果使用不当，可能导致内存泄漏，主要原因是 ThreadLocalMap 中的 Entry 使用弱引用作为 key，而 value 是强引用。

### ThreadLocal 结构

```
┌─────────────────────────────────────────────────────────────┐
│                         Thread                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              threadLocals (ThreadLocalMap)           │   │
│  │  ┌─────────────────────────────────────────────────┐ │   │
│  │  │  Entry[] table                                  │ │   │
│  │  │  ┌─────────────────────────────────────────┐   │ │   │
│  │  │  │ Entry[0]: WeakReference<ThreadLocal>    │   │ │   │
│  │  │  │            ↓ (弱引用，GC 可回收)          │   │ │   │
│  │  │  │         ThreadLocal @0x1234             │   │ │   │
│  │  │  │            ↓                            │   │ │   │
│  │  │  │         value = "UserData" (强引用)      │   │ │   │
│  │  │  └─────────────────────────────────────────┘   │ │   │
│  │  └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心源码

```java
// Thread 类中的 ThreadLocalMap
public class Thread implements Runnable {
    ThreadLocal.ThreadLocalMap threadLocals = null;
}

// ThreadLocal 的 set 方法
public void set(T value) {
    Thread t = Thread.currentThread();
    ThreadLocalMap map = getMap(t);  // 获取当前线程的 ThreadLocalMap
    if (map != null)
        map.set(this, value);  // 以 ThreadLocal 为 key，value 为值
    else
        createMap(t, value);
}

// ThreadLocalMap 定义
static class ThreadLocalMap {
    // Entry 继承 WeakReference，key 是弱引用
    static class Entry extends WeakReference<ThreadLocal<?>> {
        Object value;  // value 是强引用！
        
        Entry(ThreadLocal<?> k, Object v) {
            super(k);    // key 是弱引用
            value = v;   // value 是强引用
        }
    }
    
    private Entry[] table;
    private int size = 0;
}
```

### 内存泄漏原因

#### 场景分析

```java
public class MemoryLeakDemo {
    // 线程池中的线程是复用的
    private ExecutorService executor = Executors.newFixedThreadPool(5);
    
    public void process() {
        executor.submit(() -> {
            ThreadLocal<User> userLocal = new ThreadLocal<>();
            userLocal.set(new User("张三"));  // 大对象
            
            // 业务逻辑...
            
            // 忘记调用 remove()！
            // userLocal.remove();
        });
    }
}
```

#### 泄漏过程

```
1. ThreadLocal 变量被置为 null
   threadLocal = null;

2. GC 发生时
   - ThreadLocal 只有弱引用，被回收
   - Entry.key 变为 null
   - 但 Entry.value 仍是强引用，无法回收！

3. 线程池场景下
   - 线程不会销毁
   - ThreadLocalMap 一直存在
   - value 永远无法被回收
   - 内存泄漏！
```

```
泄漏示意图：

Before GC:
Thread → ThreadLocalMap → Entry[] → Entry 
                                        ↓
                                    ┌──────────┐
                                    │ key      │──→ ThreadLocal (强引用)
                                    │ value    │──→ User对象 (强引用)
                                    └──────────┘

After GC (threadLocal = null):
Thread → ThreadLocalMap → Entry[] → Entry
                                        ↓
                                    ┌──────────┐
                                    │ key = null│  (ThreadLocal 被回收)
                                    │ value    │──→ User对象 (强引用，无法回收！)
                                    └──────────┘
```

### 为什么 key 要设计为弱引用？

```java
// 如果 key 是强引用
ThreadLocal tl = new ThreadLocal();
tl.set(value);
tl = null;  // 即使置为 null，ThreadLocalMap 仍持有强引用
            // ThreadLocal 永远无法回收！

// key 是弱引用
ThreadLocal tl = new ThreadLocal();
tl.set(value);
tl = null;  // ThreadLocalMap 持有弱引用
            // GC 时 ThreadLocal 可回收
            // 虽然 value 可能泄漏，但 ThreadLocal 本身不会泄漏
```

**设计权衡**：
- 弱引用：ThreadLocal 本身可回收，但 value 可能泄漏
- 强引用：ThreadLocal 和 value 都泄漏

### 解决方案

#### 1. 及时调用 remove()

```java
public void process() {
    ThreadLocal<User> userLocal = new ThreadLocal<>();
    try {
        userLocal.set(new User("张三"));
        // 业务逻辑...
    } finally {
        userLocal.remove();  // 必须调用！
    }
}
```

#### 2. 使用 try-finally 模式

```java
public class SafeThreadLocal<T> {
    private final ThreadLocal<T> threadLocal = new ThreadLocal<>();
    
    public void execute(Supplier<T> supplier, Consumer<T> consumer) {
        T value = supplier.get();
        threadLocal.set(value);
        try {
            consumer.accept(value);
        } finally {
            threadLocal.remove();
        }
    }
}
```

#### 3. 使用 InheritableThreadLocal 注意传递

```java
// 父子线程传递 ThreadLocal
public class ParentChildDemo {
    // 子线程可以获取父线程的值
    private static InheritableThreadLocal<String> inheritableLocal = 
        new InheritableThreadLocal<>();
    
    public static void main(String[] args) {
        inheritableLocal.set("父线程的值");
        
        new Thread(() -> {
            System.out.println(inheritableLocal.get());  // 输出：父线程的值
        }).start();
    }
}
```

**注意**：线程池中使用 InheritableThreadLocal 也有问题，需要使用 TransmittableThreadLocal。

### ThreadLocalMap 的清理机制

#### 1. 探测式清理（expungeStaleEntry）

```java
// 清理指定位置的失效 Entry
private int expungeStaleEntry(int staleSlot) {
    Entry[] tab = table;
    int len = tab.length;
    
    // 清理当前位置
    tab[staleSlot].value = null;
    tab[staleSlot] = null;
    size--;
    
    // 继续向后扫描，直到遇到 null
    Entry e;
    int i;
    for (i = nextIndex(staleSlot, len);
         (e = tab[i]) != null;
         i = nextIndex(i, len)) {
        ThreadLocal<?> k = e.get();
        if (k == null) {  // key 被回收
            e.value = null;
            tab[i] = null;
            size--;
        } else {
            // 重新哈希
            int h = k.threadLocalHashCode & (len - 1);
            if (h != i) {
                tab[i] = null;
                while (tab[h] != null)
                    h = nextIndex(h, len);
                tab[h] = e;
            }
        }
    }
    return i;
}
```

#### 2. 启发式清理（cleanSomeSlots）

```java
// 启发式扫描，清理失效 Entry
private boolean cleanSomeSlots(int i, int n) {
    boolean removed = false;
    Entry[] tab = table;
    int len = tab.length;
    do {
        i = nextIndex(i, len);
        Entry e = tab[i];
        if (e != null && e.get() == null) {
            n = len;
            removed = true;
            i = expungeStaleEntry(i);
        }
    } while ((n >>>= 1) != 0);
    return removed;
}
```

**触发时机**：
- set() 方法：发现 key 为 null 时触发
- get() 方法：发现 key 为 null 时触发
- remove() 方法：主动触发

### 使用场景

#### 1. 用户上下文传递

```java
public class UserContext {
    private static final ThreadLocal<User> currentUser = new ThreadLocal<>();
    
    public static void set(User user) {
        currentUser.set(user);
    }
    
    public static User get() {
        return currentUser.get();
    }
    
    public static void clear() {
        currentUser.remove();
    }
}

// 拦截器中设置
public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, 
                            HttpServletResponse response, 
                            Object handler) {
        User user = authenticate(request);
        UserContext.set(user);
        return true;
    }
    
    @Override
    public void afterCompletion(HttpServletRequest request,
                                HttpServletResponse response,
                                Object handler, Exception ex) {
        UserContext.clear();  // 必须清理！
    }
}
```

#### 2. 数据库连接管理

```java
public class ConnectionManager {
    private static final ThreadLocal<Connection> connectionHolder = 
        new ThreadLocal<>();
    
    public static Connection getConnection() {
        Connection conn = connectionHolder.get();
        if (conn == null) {
            conn = DataSource.getConnection();
            connectionHolder.set(conn);
        }
        return conn;
    }
    
    public static void close() {
        Connection conn = connectionHolder.get();
        if (conn != null) {
            try {
                conn.close();
            } catch (SQLException e) {
                e.printStackTrace();
            }
            connectionHolder.remove();
        }
    }
}
```

#### 3. SimpleDateFormat 线程安全

```java
public class DateUtil {
    // SimpleDateFormat 不是线程安全的
    private static final ThreadLocal<SimpleDateFormat> dateFormatHolder =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
    
    public static String format(Date date) {
        return dateFormatHolder.get().format(date);
    }
}
```

### 高频面试题

**Q1: ThreadLocal 和 synchronized 的区别？**

| 特性 | ThreadLocal | synchronized |
|------|-------------|--------------|
| 作用 | 线程隔离 | 线程同步 |
| 数据 | 每个线程独立副本 | 共享数据 |
| 竞争 | 无竞争 | 有竞争 |
| 适用场景 | 线程上下文传递 | 临界区保护 |

**Q2: ThreadLocalMap 的哈希冲突怎么解决？**

```java
// 开放寻址法（线性探测）
private void set(ThreadLocal<?> key, Object value) {
    Entry[] tab = table;
    int len = tab.length;
    int i = key.threadLocalHashCode & (len - 1);
    
    // 线性探测
    for (Entry e = tab[i]; e != null; e = tab[i = nextIndex(i, len)]) {
        ThreadLocal<?> k = e.get();
        if (k == key) {
            e.value = value;
            return;
        }
        if (k == null) {
            replaceStaleEntry(key, value, i);
            return;
        }
    }
    tab[i] = new Entry(key, value);
}
```

**Q3: 父子线程如何共享 ThreadLocal？**

```java
// 使用 InheritableThreadLocal
private static InheritableThreadLocal<String> local = 
    new InheritableThreadLocal<>();

// 原理：Thread.init() 方法中复制父线程的 inheritableThreadLocals
if (inheritThreadLocals && parent.inheritableThreadLocals != null)
    this.inheritableThreadLocals =
        ThreadLocal.createInheritedMap(parent.inheritableThreadLocals);
```

**Q4: 线程池中使用 ThreadLocal 有什么问题？**

```java
// 问题：线程复用导致数据混乱
ExecutorService pool = Executors.newFixedThreadPool(2);
ThreadLocal<Integer> local = new ThreadLocal<>();

pool.submit(() -> {
    local.set(1);
    // 线程使用完归还线程池，但没有清理 ThreadLocal
});

pool.submit(() -> {
    // 同一个线程，可能读到之前设置的值！
    System.out.println(local.get());  // 可能输出 1！
});
```

**解决方案**：
```java
// 1. 每次使用完清理
pool.submit(() -> {
    try {
        local.set(1);
        // 业务逻辑
    } finally {
        local.remove();
    }
});

// 2. 使用 TransmittableThreadLocal（阿里开源）
TransmittableThreadLocal<String> ttl = new TransmittableThreadLocal<>();
ExecutorService ttlPool = TtlExecutors.getTtlExecutorService(pool);
```

### 最佳实践

```java
// 1. 使用 static final 修饰
private static final ThreadLocal<User> userHolder = new ThreadLocal<>();

// 2. 必须配合 try-finally 使用
public void process() {
    userHolder.set(getUser());
    try {
        // 业务逻辑
    } finally {
        userHolder.remove();
    }
}

// 3. 使用 Java 8 的 withInitial
private static final ThreadLocal<SimpleDateFormat> sdf = 
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

// 4. 定期清理（Spring 的 RequestContextFilter）
public class CleanupFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, 
                        ServletResponse response, 
                        FilterChain chain) throws IOException, ServletException {
        try {
            chain.doFilter(request, response);
        } finally {
            // 清理所有 ThreadLocal
            UserContext.clear();
            TransactionContext.clear();
        }
    }
}
```

---

**参考链接：**
- [ThreadLocal 原理与内存泄漏-掘金](https://juejin.cn/post/7498658013932716041)
- [ThreadLocal 内存泄露是怎么回事-图灵课堂](https://www.tulingxueyuan.cn/tlzx/javamst/6288.html)
