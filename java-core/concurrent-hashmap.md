# ConcurrentHashMap 原理详解 ⭐⭐⭐

## 面试题：ConcurrentHashMap 是如何保证线程安全的？

### 核心回答

ConcurrentHashMap 是 Java 并发包中提供的线程安全哈希表，相比 Hashtable 和 Collections.synchronizedMap()，它采用了更细粒度的锁机制，实现了更高的并发性能。

### JDK 1.7 vs JDK 1.8 对比

| 特性 | JDK 1.7 | JDK 1.8 |
|------|---------|---------|
| **数据结构** | Segment 数组 + HashEntry 数组 + 链表 | Node 数组 + 链表 + 红黑树 |
| **锁机制** | 分段锁（Segment 继承 ReentrantLock） | CAS + synchronized（锁单个 Node） |
| **锁粒度** | 段级别（默认 16 段） | 节点级别 |
| **并发度** | 固定 16（Segment 数量） | 理论上无上限 |
| **哈希冲突** | 链表 | 链表 + 红黑树（长度≥8） |
| **size 计算** | 分段统计后累加 | 基于 CounterCell 数组 |

### JDK 1.8 核心结构

```java
// 核心字段
 transient volatile Node<K,V>[] table;  // 哈希桶数组
 
 // Node 节点定义
 static class Node<K,V> implements Map.Entry<K,V> {
     final int hash;
     final K key;
     volatile V val;        // volatile 保证可见性
     volatile Node<K,V> next;
 }
 
 // 特殊节点：ForwardingNode（扩容时使用）
 static final class ForwardingNode<K,V> extends Node<K,V> {
     final Node<K,V>[] nextTable;
 }
 
 // 特殊节点：TreeBin（红黑树根节点）
 static final class TreeBin<K,V> extends Node<K,V> {
     TreeNode<K,V> root;
 }
```

### 核心参数

```java
// 默认初始容量
private static final int DEFAULT_CAPACITY = 16;

// 默认并发级别（JDK 1.7 使用，1.8 仅用于兼容）
private static final int DEFAULT_CONCURRENCY_LEVEL = 16;

// 负载因子
private static final float LOAD_FACTOR = 0.75f;

// 链表转红黑树阈值
static final int TREEIFY_THRESHOLD = 8;

// 红黑树转链表阈值
static final int UNTREEIFY_THRESHOLD = 6;

// 最小树化容量（table 长度达到 64 才允许转红黑树）
static final int MIN_TREEIFY_CAPACITY = 64;

// 扩容时单线程最小迁移量
private static final int MIN_TRANSFER_STRIDE = 16;
```

### put() 方法执行流程

```java
final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode());  // 计算哈希值
    int binCount = 0;
    
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        
        // 1. table 未初始化，先初始化
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();
        
        // 2. 目标位置为空，CAS 直接插入
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;
        }
        
        // 3. 发现 ForwardingNode，说明正在扩容，协助扩容
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
        
        // 4. 发生哈希冲突，需要加锁处理
        else {
            V oldVal = null;
            synchronized (f) {  // 只锁当前桶的头节点
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {  // 链表
                        binCount = 1;
                        for (Node<K,V> e = f;; ++binCount) {
                            K ek;
                            // 找到相同 key，更新值
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                oldVal = e.val;
                                if (!onlyIfAbsent)
                                    e.val = value;
                                break;
                            }
                            Node<K,V> pred = e;
                            // 到链表尾部，插入新节点
                            if ((e = e.next) == null) {
                                pred.next = new Node<K,V>(hash, key, value, null);
                                break;
                            }
                        }
                    }
                    else if (f instanceof TreeBin) {  // 红黑树
                        Node<K,V> p;
                        binCount = 2;
                        if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key, value)) != null) {
                            oldVal = p.val;
                            if (!onlyIfAbsent)
                                p.val = value;
                        }
                    }
                }
            }
            
            // 检查是否需要树化
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    
    addCount(1L, binCount);  // 更新元素个数
    return null;
}
```

### 线程安全机制

#### 1. CAS 操作（无锁化）

```java
// 使用 Unsafe 进行 CAS 操作
static final <K,V> boolean casTabAt(Node<K,V>[] tab, int i,
                                    Node<K,V> c, Node<K,V> v) {
    return U.compareAndSwapObject(tab, ((long)i << ASHIFT) + ABASE, c, v);
}
```

**CAS 使用场景**：
- 初始化 table
- 桶位为空时插入节点
- 更新元素个数（CounterCell）

#### 2. synchronized 细粒度锁

```java
// 只锁住链表/红黑树的头节点
synchronized (f) {
    // 处理链表或红黑树
}
```

**为什么用 synchronized 而不是 ReentrantLock？**

JDK 1.8 对 synchronized 进行了优化：
- 锁升级机制（无锁 → 偏向锁 → 轻量级锁 → 重量级锁）
- 在锁竞争不激烈时，synchronized 性能更好
- 代码更简洁

#### 3. volatile 保证可见性

```java
// table 使用 volatile 修饰
transient volatile Node<K,V>[] table;

// Node 的 val 和 next 使用 volatile 修饰
volatile V val;
volatile Node<K,V> next;
```

### 扩容机制（多线程协作）

```java
private final void transfer(Node<K,V>[] tab, Node<K,V>[] nextTab) {
    int n = tab.length, stride;
    
    // 1. 计算每个线程负责的迁移量
    if ((stride = (NCPU > 1) ? (n >>> 3) / NCPU : n) < MIN_TRANSFER_STRIDE)
        stride = MIN_TRANSFER_STRIDE;
    
    // 2. 初始化新 table
    if (nextTab == null) {
        try {
            Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n << 1];
            nextTab = nt;
        } catch (Throwable ex) {
            sizeCtl = Integer.MAX_VALUE;
            return;
        }
        nextTable = nextTab;
        transferIndex = n;
    }
    
    int nextn = nextTab.length;
    ForwardingNode<K,V> fwd = new ForwardingNode<K,V>(nextTab);
    boolean advance = true;
    boolean finishing = false;
    
    // 3. 多线程并行迁移
    for (int i = 0, bound = 0;;) {
        Node<K,V> f; int fh;
        
        // 分配迁移任务
        while (advance) {
            int nextIndex, nextBound;
            if (--i >= bound || finishing)
                advance = false;
            else if ((nextIndex = transferIndex) <= 0) {
                i = -1;
                advance = false;
            }
            else if (U.compareAndSwapInt(this, TRANSFERINDEX, nextIndex,
                      nextBound = (nextIndex > stride ? nextIndex - stride : 0))) {
                bound = nextBound;
                i = nextIndex - 1;
                advance = false;
            }
        }
        
        // 迁移完成
        if (i < 0 || i >= n || i + n >= nextn) {
            if (finishing) {
                nextTable = null;
                table = nextTab;
                sizeCtl = (n << 1) - (n >>> 1);  // 新阈值 = 新容量 * 0.75
                return;
            }
            // ...
        }
        
        // 迁移桶中的元素
        else if ((f = tabAt(tab, i)) == null)
            advance = casTabAt(tab, i, null, fwd);
        else if ((fh = f.hash) == MOVED)
            advance = true;
        else {
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    Node<K,V> ln, hn;
                    if (fh >= 0) {  // 链表迁移
                        // 将链表拆分成两部分
                        // 一部分在新 table 的原位置
                        // 另一部分在新 table 的原位置 + n
                    }
                    else if (f instanceof TreeBin) {  // 红黑树迁移
                        // ...
                    }
                }
            }
        }
    }
}
```

**扩容特点**：
1. **多线程协作**：多个线程可以同时参与扩容
2. **分段迁移**：每个线程负责一段数据的迁移
3. **渐进式**：查询时遇到 ForwardingNode 会协助扩容

### size() 方法实现

```java
public int size() {
    long n = sumCount();
    return ((n < 0L) ? 0 :
            (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE : (int)n);
}

// 使用 CounterCell 数组分散热点
@sun.misc.Contended static final class CounterCell {
    volatile long value;
    CounterCell(long x) { value = x; }
}

final long sumCount() {
    CounterCell[] as = counterCells; CounterCell a;
    long sum = baseCount;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                sum += a.value;
        }
    }
    return sum;
}
```

**优化思路**：
- 使用 CounterCell 数组分散 CAS 竞争
- 不同线程更新不同的 CounterCell
- 求和时累加 baseCount 和所有 CounterCell

### 高频面试题

**Q1: ConcurrentHashMap 为什么 key 和 value 不能为 null？**

```java
// ConcurrentHashMap 的 put 方法
if (key == null || value == null) throw new NullPointerException();
```

原因：
1. **避免歧义**：无法区分 "key 不存在" 和 "key 存在但 value 为 null"
2. **并发安全**：在多线程环境下，null 值可能导致判断错误

**对比 HashMap**：
- HashMap 允许 null key 和 null value（单线程环境，可以通过 containsKey 区分）

**Q2: ConcurrentHashMap 和 Hashtable 的区别？**

| 特性 | ConcurrentHashMap | Hashtable |
|------|-------------------|-----------|
| 锁机制 | 细粒度锁（桶级别） | 粗粒度锁（整个表） |
| 性能 | 高并发性能好 | 并发性能差 |
| null 支持 | 不支持 | 不支持 |
| 迭代器 | 弱一致性 | 快速失败 |
| 出现版本 | JDK 1.5 | JDK 1.0 |

**Q3: size() 方法是准确的吗？**

不是实时的准确值，是**弱一致性**的：
- size() 返回的是一个估计值
- 在计算过程中，其他线程可能正在修改 Map
- 如果需要精确值，需要加锁遍历（但性能差）

**Q4: get() 方法需要加锁吗？**

不需要，get() 是**完全无锁**的：
- 利用 volatile 保证可见性
- 利用 CAS 保证原子性

```java
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {
        if ((eh = e.hash) == h) {
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
        else if (eh < 0)  // 正在扩容或是红黑树
            return (p = e.find(h, key)) != null ? p.val : null;
        
        // 遍历链表
        while ((e = e.next) != null) {
            if (e.hash == h &&
                ((ek = e.key) == key || (ek != null && key.equals(ek))))
                return e.val;
        }
    }
    return null;
}
```

### 最佳实践

```java
// 1. 预估容量，避免频繁扩容
ConcurrentHashMap<String, Object> map = new ConcurrentHashMap<>(128);

// 2. 使用 computeIfAbsent 原子性计算
map.computeIfAbsent(key, k -> createValue(k));

// 3. 使用 putIfAbsent 实现幂等
map.putIfAbsent(key, value);

// 4. 批量操作时考虑使用 merge
map.merge(key, value, (oldVal, newVal) -> oldVal + newVal);
```

---

**参考链接：**
- [ConcurrentHashMap 底层实现原理-CSDN](https://blog.csdn.net/MANONGMN/article/details/134179402)
- [ConcurrentHashMap 1.7与1.8的核心差异解析-CSDN](https://blog.csdn.net/qq_58299462/article/details/146198956)
