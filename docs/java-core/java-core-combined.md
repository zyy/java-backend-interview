# Java 核心基础（合并版）

> Java 基础是后端面试的重中之重，务必扎实掌握
> 本文档合并了所有 Java 核心基础相关主题，便于统一维护

## 📋 内容大纲

## 1. 基础语法 ⭐

### 1.1 数据类型与包装类
**内容概要：**
- 基本数据类型：byte、short、int、long、float、double、char、boolean
- 包装类：Byte、Short、Integer、Long、Float、Double、Character、Boolean
- 自动装箱与拆箱
- 缓存机制：IntegerCache（-128~127）
- 类型转换与精度丢失

**面试要点：**
- 为什么要有包装类？
- 自动装箱拆箱的原理
- Integer 缓存机制及注意事项
- 基本类型与包装类型的性能差异

### 1.2 String、StringBuilder、StringBuffer
> 详细内容请参考原文档：[string.md](./string.md)

**核心区别：**
- **String**：不可变字符序列，线程安全
- **StringBuilder**：可变字符序列，非线程安全，性能高
- **StringBuffer**：可变字符序列，线程安全，性能较低

**面试高频题：**
1. String 为什么不可变？
2. 字符串常量池原理
3. StringBuilder 和 StringBuffer 的选择
4. 字符串拼接的性能优化

### 1.3 equals 与 hashCode
**equals() 方法：**
- 用于比较对象内容是否相等
- 默认实现比较对象引用（==）
- 需要重写以实现逻辑相等

**hashCode() 方法：**
- 返回对象的哈希码值
- 用于哈希表（HashMap、HashSet）中快速定位
- equals() 相等的对象，hashCode() 必须相等

**重写规范：**
1. 一致性：多次调用 hashCode() 应返回相同值
2. 等价性：equals() 相等则 hashCode() 必须相等
3. 不等价性：equals() 不等时 hashCode() 最好不等（减少哈希冲突）

### 1.4 泛型机制
**泛型的作用：**
1. 类型安全：编译时检查类型错误
2. 代码复用：一套代码处理多种类型
3. 消除强制类型转换

**类型擦除：**
- Java 泛型是编译期特性
- 运行时类型信息被擦除
- 无法获取泛型的具体类型

**通配符：**
- `<?>`：无界通配符
- `<? extends T>`：上界通配符（生产者）
- `<? super T>`：下界通配符（消费者）

**面试要点：**
- 类型擦除的原理及影响
- PECS 原则（Producer Extends, Consumer Super）
- 泛型与反射的冲突

### 1.5 注解与反射
**注解（Annotation）：**
- 元数据，为代码添加信息
- 内置注解：@Override、@Deprecated、@SuppressWarnings
- 元注解：@Target、@Retention、@Documented、@Inherited

**反射（Reflection）：**
- 运行时获取类信息并操作
- 核心类：Class、Field、Method、Constructor
- 应用：框架、动态代理、序列化

**性能考虑：**
- 反射调用比直接调用慢
- 可通过缓存 Class 对象、Method 对象优化

## 2. 集合框架 ⭐⭐

### 2.1 ArrayList vs LinkedList
> 详细内容请参考原文档：[list.md](./list.md)

**数据结构：**
- **ArrayList**：动态数组，支持随机访问
- **LinkedList**：双向链表，支持快速插入删除

**性能对比：**
| 操作 | ArrayList | LinkedList |
|------|-----------|------------|
| 随机访问 | O(1) | O(n) |
| 头部插入 | O(n) | O(1) |
| 尾部插入 | O(1) | O(1) |
| 中间插入 | O(n) | O(1)（定位+插入） |
| 内存占用 | 较小（连续内存） | 较大（节点开销） |

### 2.2 HashMap 原理详解
> 详细内容请参考原文档：[hashmap.md](./hashmap.md)

**核心要点：**
- 数据结构：数组 + 链表 + 红黑树（JDK 1.8+）
- 哈希冲突解决：拉链法
- 扩容机制：容量翻倍，重新哈希
- 线程安全：非线程安全，使用 ConcurrentHashMap

### 2.3 ConcurrentHashMap
> 详细内容请参考原文档：[concurrent-hashmap.md](./concurrent-hashmap.md)

**线程安全实现：**
- JDK 1.7：分段锁（Segment）
- JDK 1.8：CAS + synchronized（锁粒度更细）

**性能优势：**
- 读操作完全无锁（volatile）
- 写操作锁粒度小（单个桶）
- 扩容时支持并发操作

### 2.4 其他集合类对比
**Set 接口实现：**
- **HashSet**：基于 HashMap，无序
- **TreeSet**：基于 TreeMap，有序
- **LinkedHashSet**：保持插入顺序

**Queue 接口实现：**
- **LinkedList**：双向队列
- **ArrayDeque**：数组实现的双端队列
- **PriorityQueue**：优先级队列（堆实现）

**Map 接口实现：**
- **TreeMap**：红黑树，键有序
- **LinkedHashMap**：保持插入顺序或访问顺序
- **WeakHashMap**：弱引用键，适合缓存

## 3. 并发编程 ⭐⭐⭐

### 3.1 线程池核心参数详解
> 详细内容请参考原文档：[thread-pool.md](./thread-pool.md)

**ThreadPoolExecutor 参数：**
1. corePoolSize：核心线程数
2. maximumPoolSize：最大线程数
3. keepAliveTime：空闲线程存活时间
4. unit：时间单位
5. workQueue：工作队列
6. threadFactory：线程工厂
7. handler：拒绝策略

**拒绝策略：**
- AbortPolicy：抛出异常（默认）
- CallerRunsPolicy：调用者线程执行
- DiscardPolicy：直接丢弃
- DiscardOldestPolicy：丢弃最老任务

### 3.2 synchronized 与锁升级
> 详细内容请参考原文档：[synchronized.md](./synchronized.md)

**锁升级过程：**
1. 无锁状态
2. 偏向锁：减少同一线程获取锁的开销
3. 轻量级锁：CAS 自旋，避免线程阻塞
4. 重量级锁：真正的互斥锁，线程阻塞

**锁优化：**
- 锁消除：JIT 编译器优化
- 锁粗化：减少锁的获取释放次数
- 适应性自旋：根据历史成功率调整自旋次数

### 3.3 volatile 与内存屏障
> 详细内容请参考原文档：[volatile.md](./volatile.md)

**volatile 特性：**
1. 可见性：保证修改立即同步到主内存
2. 有序性：禁止指令重排序
3. 不保证原子性：复合操作仍需同步

**内存屏障：**
- LoadLoad：禁止读操作重排序
- StoreStore：禁止写操作重排序
- LoadStore：禁止读后写重排序
- StoreLoad：禁止写后读重排序（全能屏障）

### 3.4 CAS 与 AQS 原理
> 详细内容请参考原文档：[cas-aqs.md](./cas-aqs.md)

**CAS（Compare And Swap）：**
- 原子操作：比较并交换
- 实现：Unsafe 类提供 native 方法
- 问题：ABA 问题（通过版本号解决）

**AQS（AbstractQueuedSynchronizer）：**
- 同步器框架：ReentrantLock、CountDownLatch 等基础
- 核心：状态 state + FIFO 队列
- 实现：模板方法模式

### 3.5 ThreadLocal 原理与内存泄漏
> 详细内容请参考原文档：[threadlocal.md](./threadlocal.md)

**原理：**
- 每个线程有自己的 ThreadLocalMap
- key 为 ThreadLocal 的弱引用
- value 为存储的值（强引用）

**内存泄漏：**
- 原因：ThreadLocal 被回收，但 value 仍被强引用
- 解决：使用完后调用 remove() 方法

## 4. IO/NIO ⭐⭐

### 4.1 BIO、NIO、AIO 区别
> 详细内容请参考原文档：[io-models.md](./io-models.md)

**BIO（Blocking IO）：**
- 同步阻塞：每个连接一个线程
- 优点：简单直观
- 缺点：线程开销大，并发能力有限

**NIO（Non-blocking IO）：**
- 同步非阻塞：多路复用器（Selector）
- 核心组件：Channel、Buffer、Selector
- 优点：单线程处理多连接，高并发

**AIO（Asynchronous IO）：**
- 异步非阻塞：回调机制
- 优点：真正的异步，不阻塞线程
- 缺点：编程复杂，系统支持有限

### 4.2 Netty 基础
**核心组件：**
1. Channel：网络连接抽象
2. EventLoop：事件循环，处理 I/O
3. ChannelHandler：业务逻辑处理
4. ByteBuf：高效字节容器

**线程模型：**
- Reactor 模式
- 单线程、多线程、主从多线程模型

**编解码器：**
- 解决 TCP 粘包/拆包问题
- 常用：LengthFieldBasedFrameDecoder

## 🎯 面试高频题汇总

1. **HashMap 的 put 流程是怎样的？**
   - 计算哈希值 → 定位桶 → 处理冲突 → 检查扩容

2. **ConcurrentHashMap 如何保证线程安全？**
   - JDK 1.8：CAS + synchronized（锁单个桶）

3. **线程池的核心参数有哪些？如何合理配置？**
   - CPU 密集型：corePoolSize = CPU 核心数
   - IO 密集型：corePoolSize = CPU 核心数 × 2

4. **String、StringBuilder、StringBuffer 的区别？**
   - 可变性、线程安全性、性能

5. **synchronized 的锁升级过程？**
   - 无锁 → 偏向锁 → 轻量级锁 → 重量级锁

6. **volatile 能保证原子性吗？为什么？**
   - 不能，只保证可见性和有序性

7. **ArrayList 和 LinkedList 的区别？**
   - 数组 vs 链表，随机访问 vs 插入删除

8. **ThreadLocal 为什么会内存泄漏？如何解决？**
   - 弱引用 key 被回收，强引用 value 残留
   - 使用后调用 remove()

9. **CAS 和 AQS 的原理？**
   - CAS：比较并交换，乐观锁
   - AQS：同步器框架，CLH 队列

10. **BIO、NIO、AIO 的区别？**
    - 阻塞 vs 非阻塞 vs 异步

## 📚 延伸阅读

- [Java 官方文档](https://docs.oracle.com/javase/8/docs/)
- [深入理解 Java 虚拟机](https://book.douban.com/subject/34907497/)
- 《Java 并发编程实战》
- 《Effective Java》

---

**文档维护说明：**
- 本文档合并了 Java 核心基础所有主题
- 原独立文档可逐步迁移至此
- 后期只维护此合并文档，避免重复和冲突
- 索引文件需更新为指向此文档的对应章节
