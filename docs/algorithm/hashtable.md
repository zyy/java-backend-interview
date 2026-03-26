---
layout: default
title: 哈希表（HashMap/HashSet）核心原理 ⭐⭐⭐
---

# 哈希表（HashMap/HashSet）核心原理 ⭐⭐⭐

> HashMap 是 Java 最核心的集合之一，也是面试中问到频率最高的集合类，没有之一

## 🎯 面试重点速览

| 知识点 | JDK 7 | JDK 8+ |
|--------|-------|--------|
| 底层结构 | 数组 + 链表（头插法） | 数组 + 链表 + 红黑树（尾插法） |
| 并发安全 | 无，线程不安全 | 无，线程不安全 |
| 并发替代 | Hashtable / Collections.synchronizedMap | ConcurrentHashMap（CAS + synchronized） |
| 扩容方式 | 2 倍扩容 | 2 倍扩容 |
| 链表插入 | 头插法（并发下可能死循环） | 尾插法（避免死循环） |

---

## 一、HashMap 底层数据结构

### 1.1 JDK 7：数组 + 链表

```java
/**
 * JDK 7 的 HashMap 核心结构
 *
 * 由一个 Entry 数组（叫 table）组成
 * 每个位置（桶）存一条链表的头节点
 * 每个 Entry 包含 key、value、hash、next
 */
public class HashMap<K, V> {
    // HashMap 内部维护的数组，每个元素是一条链表
    transient Entry<K, V>[] table;

    /**
     * Entry 是链表节点
     * - key: 键
     * - value: 值
     * - hash: key 的 hash 值（避免重复计算）
     * - next: 指向下一个节点的指针
     */
    static class Entry<K, V> implements Map.Entry<K, V> {
        final K key;
        V value;
        int hash;      // key 的 hash 值，缓存起来避免重复计算
        Entry<K, V> next; // 链表下一节点

        Entry(int h, K k, V v, Entry<K, V> n) {
            value = v;
            next = n;
            key = k;
            hash = h;
        }
    }
}
```

**JDK 7 存储结构图示：**

```
table 数组（长度为 16）：

index:  0       1       2       3       ...     15
      ┌────┐   ┌────┐   ┌────┐   ┌────┐         ┌────┐
      │null│   │Entry│  │null│  │Entry│         │null│
      └────┘   │key=1│  └────┘  │key=5│         └────┘
               │next │           │next │
               │  ↓  │           │ null│
               │Entry│           └─────┘
               │key=3│
               │next │
               │ null│
               └─────┘

例：key="hello" → hash = 12345 → index = 12345 & (16-1) = 5
```

### 1.2 JDK 8+：数组 + 链表 + 红黑树

```java
/**
 * JDK 8 的 HashMap 核心结构
 *
 * 当链表长度超过阈值（默认 8）时，链表会转换为红黑树
 * 红黑树查询时间复杂度：O(log n)，链表查询时间复杂度：O(n)
 */
public class HashMap<K, V> {
    transient Node<K, V>[] table;

    /**
     * JDK 8 的链表节点（替代了 Entry）
     */
    static class Node<K, V> {
        final int hash;
        final K key;
        V value;
        Node<K, V> next; // 链表下一节点

        Node(int hash, K key, V value, Node<K, V> next) {
            this.hash = hash;
            this.key = key;
            this.value = value;
            this.next = next;
        }
    }

    /**
     * JDK 8 新增：红黑树节点
     */
    static final class TreeNode<K, V> extends LinkedHashMap.Entry<K, V> {
        TreeNode<K, V> parent;      // 父节点
        TreeNode<K, V> left;        // 左子树
        TreeNode<K, V> right;       // 右子树
        TreeNode<K, V> prev;        // 前一个节点（删除时使用）
        boolean red;                // 颜色标记

        TreeNode(int hash, K key, V val, Node<K, V> next) {
            super(hash, key, val, next);
        }
    }

    /**
     * 链表转红黑树的阈值
     * 当链表长度 >= 8 时，转化为红黑树
     */
    static final int TREEIFY_THRESHOLD = 8;

    /**
     * 红黑树退化为链表的阈值
     * 当红黑树节点数 <= 6 时，退化为链表
     * 注意：不是 7，而是 6！中间留了一个"缓冲带"避免频繁转换
     */
    static final int UNTREEIFY_THRESHOLD = 6;
}
```

**JDK 8 存储结构图示：**

```
table 数组：

  index 0        index 3          index 7（链表转红黑树）
  ┌──────┐     ┌──────┐         ┌──────┐
  │ null │     │ Node │         │ Tree │
  └──────┘     │next  │         │Root  │
               │  ↓   │         │ / \  │
               │ null │         │*   *  │
               └──────┘         │/ \   │
                                 └─────┘

链表长度 >= 8 → 红黑树（O(n) → O(log n)）
红黑树节点 <= 6 → 退化回链表
```

---

## 二、HashMap 的 hash() 方法：扰动函数

### 2.1 hash() 的演变

```java
/**
 * JDK 7 的 hash() 实现
 * 通过一系列位运算和乘法让 hash 值更分散
 */
static int hash(int h) {
    h ^= (h >>> 20) ^ (h >>> 12);
    return h ^ (h >>> 7) ^ (h >>> 4);
}

/**
 * JDK 8 直接用 key 的 hashCode()
 * 不再对 hash 值做额外扰动
 * 扰动逻辑移到了 putVal() 的 index 计算中
 */
static final int hash(Object key) {
    int h;
    // 扰动：h ^ (h >>> 16)，高 16 位和低 16 位异或
    // 混合高低位，减少碰撞
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```

### 2.2 为什么要用 h ^ (h >>> 16)？

```java
/**
 * 扰动函数的作用：
 *
 * 假设 table 数组长度 n = 16（二进制 1111）
 * 寻址公式：index = (n - 1) & hash
 *                        = 15 & hash
 *                        = 0b1111 & hash
 *
 * 问题：如果只用 key.hashCode() 的低 4 位
 *       那么 hash 值低 4 位决定位置，高位被忽略
 *       导致碰撞集中在某些桶上（低 4 位分布不均）
 *
 * 解决：让高位和低位异或，把高位信息"混"到低位去
 *
 * 示例：
 *   key1.hashCode() = 0b 00000000 00000000 10000000 00000000
 *                                         ^^^^^^^^ 高位有值
 *   直接用低 4 位 = 0b 0000，低位全是 0 ❌ 所有碰撞
 *
 *   扰动后 h ^ (h >>> 16):
 *   0b 00000000 10000000 00000000 10000000
 *   ^ 00000000 00000000 00000000 10000000
 *   = 0b 00000000 10000000 00000000 00000000
 *   这次低 4 位 = 0b 0000，高位信息被混合进来了 ✅
 */

public class HashDemo {
    public static void main(String[] args) {
        // 演示扰动效果
        int h = 0b10000000_00000000_00000000_00000000; // 高位有1

        System.out.println("原始 hash (hex): " + Integer.toHexString(h));
        System.out.println("低 4 位: " + (h & 0xF));          // 0 ❌ 总是0
        System.out.println("扰动后低 4 位: " + ((h ^ (h >>> 16)) & 0xF)); // 有值 ✅

        // 用 String 的 hashCode 演示
        String key1 = "abc";
        String key2 = "Abc";
        System.out.println("\nString hashCode 扰动对比：");
        System.out.println("abc  hashCode: " + key1.hashCode());
        System.out.println("abc  扰动后:   " + (key1.hashCode() ^ (key1.hashCode() >>> 16)));
        System.out.println("Abc  hashCode: " + key2.hashCode());
        System.out.println("Abc  扰动后:   " + (key2.hashCode() ^ (key2.hashCode() >>> 16)));
    }
}
```

### 2.3 扰动图解

```
假设 hashCode() 返回：0b 10010110 11001010 00000000 00000000
                          ↑ 高 16 位     ↑ 低 16 位

>>> 16 移位后：          0b 00000000 00000000 10010110 11001010

异或（^）：
  0b 10010110 11001010 00000000 00000000
  0b 00000000 00000000 10010110 11001010
  ──────────────────────────────────────
  0b 10010110 01011110 10010110 11001010
  ───────── ─────────
   混合后     混合后
   高 16 位   低 16 位（高位的特征被混进来了）

再 & (n-1) 取 index 时，低 16 位的"高质量"保证了分布均匀
```

---

## 三、寻址算法：为什么用位运算而不是取模？

### 3.1 两种方式对比

```java
/**
 * 取模方式（慢）：
 *   index = hash % n
 *   模运算在 CPU 上需要除法指令，耗时钟周期
 *
 * 位运算方式（快）：
 *   index = (n - 1) & hash
 *   当 n 是 2 的幂次时，两者等价
 *
 * 示例：n = 16 = 2⁴
 *   hash = 37 → 37 % 16 = 5  →  37 & (16-1) = 37 & 15 = 5 ✅
 *   hash = 53 → 53 % 16 = 5  →  53 & (16-1) = 53 & 15 = 5 ✅
 *
 * 为什么等价？
 *   n = 2^k 时，n - 1 = 2^k - 1 的二进制全是 1
 *   hash & (2^k - 1) 就是取 hash 的低 k 位，等价于 hash % 2^k
 */

public class IndexDemo {
    public static void main(String[] args) {
        int n = 16; // 容量必须是 2 的幂次

        for (int hash : new int[]{5, 21, 37, 53, 69, 85}) {
            int byMod = hash % n;
            int byAnd = (n - 1) & hash;
            System.out.printf("hash=%d → %%: %d, &: %d %s%n",
                hash, byMod, byAnd, byMod == byAnd ? "✅" : "❌");
        }
    }
}
```

### 3.2 容量必须是 2 的幂次的原因

```java
/**
 * HashMap 的容量（table 数组长度）为什么必须是 2 的幂次？
 *
 * 原因 1：保证 (n - 1) & hash 均匀分布
 *   n = 16 → n-1 = 15 = 0b1111（低 4 位全是 1）
 *   n = 15 → n-1 = 14 = 0b1110（第 4 位是 0）
 *   如果 hash 高位有值，落在第 4 位的永远取不到 → 分布不均
 *
 * 原因 2：保证扩容后 rehash 均匀再分布
 *   扩容为 2 倍时：oldCap = 16, newCap = 32
 *   oldCap 二进制：   0b10000
 *   oldCap - 1：      0b01111
 *   oldCap 二进制最高位为 1 → 新增的那位（第 5 位）是否为 1
 *   只取决于 hash 的第 5 位，和其他位无关 → 均匀分散
 */
public class CapacityDemo {
    static void explain() {
        // 扩容时 rehash 的规律
        int oldCap = 16;      // 0b10000
        int newCap = 32;      // 0b100000

        // oldCap 二进制最高位为 1 → 这个 bit 的值决定了新位置
        // 新位置 = 原位置 或 原位置 + oldCap
        // 第 5 位是 0 → 原位置
        // 第 5 位是 1 → 原位置 + oldCap
        // 这个 bit 相当于一个"天然的分组位"
    }
}
```

### 3.3 寻址公式图解

```
HashMap 寻址全流程：

  key = "hello"
       ↓
  key.hashCode() = 0b 10010110 01011110 10010110 11001010
       ↓  扰动：^ (>>> 16)
  hash =          0b 10010110 01011110 01100100 00000000
       ↓
  index = (table.length - 1) & hash
       ↓  table.length = 16, n-1 = 15 = 0b1111
  index = 只取 hash 的低 4 位
       ↓
  0b 0000 = 0 号桶 ✅

如果 table.length = 15（不是 2 的幂次）：
  n-1 = 14 = 0b1110（低 4 位不是全 1）
  hash 的第 4 位（值 8）永远不会被用到
  → 碰撞集中在 0~7 号桶，8~15 号桶永远为空 ❌
```

---

## 四、链表与红黑树的转换

### 4.1 为什么链表超过 8 才转红黑树？

```java
/**
 * TREEIFY_THRESHOLD = 8 的原因：
 *
 * HashMap 默认初始容量 16，负载因子 0.75
 * 所以默认扩容阈值 = 16 × 0.75 = 12
 *
 * 当某个桶的链表长度达到 8 时：
 * - 此时 table 总元素数很可能已经 >= 12，即将触发扩容
 * - 扩容后每个桶的平均链表长度会减半（16 → 8 时减半）
 * - 所以链表长度 8 是个临界点：可能不用转树，扩容就能解决
 *
 * 泊松分布概率分析（源码注释）：
 *   链表长度 = 0 的桶：0.606
 *   链表长度 = 1 的桶：0.368
 *   链表长度 = 2 的桶：0.112
 *   链表长度 = 3 的桶：0.023
 *   链表长度 = 4 的桶：0.003
 *   链表长度 = 5 的桶：0.0003
 *   链表长度 = 6 的桶：0.00004
 *   链表长度 = 7 的桶：几乎为 0 ❗
 *
 * 翻译成人话：链表长度达到 8 的概率极低（< 0.00006）
 * 所以正常使用时几乎不会触发树化
 * 如果真的触发了，说明哈希函数严重不均匀，需要检查 hashCode()
 *
 * 红黑树本身也有开销（旋转、染色），只有长度够长时 O(log n) 才比 O(n) 快
 * 8 = log₂(256)，256 是链表长度期望上限的 10 倍以上
 */
```

### 4.2 退化阈值为什么是 6 而不是 7？

```java
/**
 * 为什么不设为 UNTREEIFY_THRESHOLD = 7（对称）？
 *
 * 原因：避免在临界点（7 和 8 之间）频繁树化/退化
 *
 * 如果阈值为 8 和 7：
 *  - 链表长度 = 8 → 树化
 *  - 链表长度 = 7 → 退化回链表
 *  - 链表长度 = 8 → 再次树化
 *  → 疯狂震荡！临界点附近反复横跳
 *
 * JDK 8 设为 8 和 6：
 *  - 链表长度 = 8 → 树化
 *  - 链表长度 = 6 → 退化
 *  - 链表长度 = 7 → 保持红黑树（不会退化）
 *  - 链表长度 = 8 → 保持红黑树
 *  → 不会反复树化/退化，有缓冲带 ✅
 *
 * 只有当长度降到 <= 6 时才退化，为临界情况留了余地
 */
```

### 4.3 树化完整流程

```java
/**
 * JDK 8 链表转红黑树的核心代码
 */
final void treeifyBin(Node<K, V>[] tab, int hash) {
    int n, index;
    Node<K, V> e;

    // 条件 1：tab 不为空
    // 条件 2：tab 长度 < MIN_TREEIFY_CAPACITY(64) 时，优先扩容而不是树化
    if (tab == null || (n = tab.length) < MIN_TREEIFY_CAPACITY)
        resize(); // 扩容而不是树化！容量 < 64 时不轻易树化
    else if ((e = tab[index = (n - 1) & hash]) != null) {
        // 构建红黑树
        TreeNode<K, V> hd = null, tl = null;
        do {
            TreeNode<K, V> p = replacementTreeNode(e, null);
            if (tl == null)
                hd = p;
            else {
                p.prev = tl;
                tl.next = p;
            }
            tl = p;
        } while ((e = e.next) != null);

        // 将链表头替换为红黑树头
        if ((tab[index] = hd) != null)
            hd.treeify(); // 调用 TreeNode 的树化方法（构建红黑树结构）
    }
}
```

---

## 五、HashMap 扩容机制

### 5.1 扩容触发条件

```java
/**
 * 扩容触发的两个条件：
 * 1. 元素数量 > 阈值（capacity × loadFactor）
 * 2. 哈希桶上有链表，且数组太小需要树化（触发 resize()）
 *
 * 默认参数：
 *   initialCapacity = 16
 *   loadFactor = 0.75
 *   threshold = 16 × 0.75 = 12
 *
 * 当元素数量 > 12 时，触发扩容为 32
 * 新阈值 = 32 × 0.75 = 24
 */
public class HashMapResizeDemo {
    public static void main(String[] args) {
        // HashMap 构造函数参数
        HashMap<String, Integer> map = new HashMap<>(16, 0.75f);
        // table.length = 16, threshold = 12

        // put 13 个元素后触发扩容
        for (int i = 0; i < 13; i++) {
            map.put("key" + i, i);
            System.out.println("put key" + i + " → size=" + map.size()
                + " → table.length 仍然是 16"); // 触发 resize 前
        }
        // 第 13 个元素放入后，size = 13 > threshold(12) → 扩容！
    }
}
```

### 5.2 扩容时 rehash 的重新分配

```java
/**
 * JDK 8 扩容时的元素重新分配
 * 核心逻辑：不需要重新计算 hash，只需要看原 hash 的高位
 *
 * 原容量：oldCap = 16 = 0b10000（第 5 位为 1）
 * 新容量：newCap = 32 = 0b100000（第 6 位为 1）
 *
 * 原 hash：h = 0b xxxxx0 yyyyy  （只看第 5 位）
 *   第 5 位 = 0 → 新位置 = 原位置（index）
 *   第 5 位 = 1 → 新位置 = 原位置 + oldCap（index + 16）
 *
 * 这就是扩容后 rehash 不需要重新计算 hash 的原因！
 * 直接判断原 hash 的第 oldCap 位即可
 */
void resize() {
    Node<K, V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;

    if (oldCap > 0) {
        // 超过最大容量，不再扩容
        if (oldCap >= MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return;
        }
        // 容量翻倍，阈值也翻倍
        newCap = oldCap << 1;        // oldCap × 2
        newThr = oldThr << 1;        // threshold × 2
    }

    // 重新分配节点到新数组
    for (int j = 0; j < oldCap; ++j) {
        Node<K, V> e;
        if ((e = oldTab[j]) != null) {
            oldTab[j] = null; // 释放旧数组引用

            if (e.next == null) {
                // 只有一个节点，直接计算新位置
                newTab[e.hash & (newCap - 1)] = e;
            }
            else if (e instanceof TreeNode) {
                // 红黑树分裂
                ((TreeNode<K, V>) e).split(this, newTab, j, oldCap);
            }
            else {
                // 链表分裂（JDK 8 尾插法）
                Node<K, V> loHead = null, loTail = null; // 保持原位置
                Node<K, V> hiHead = null, hiTail = null; // 移到原位置+oldCap

                do {
                    // 关键：判断 e.hash 的第 oldCap 位是 0 还是 1
                    if ((e.hash & oldCap) == 0) {
                        // 第 oldCap 位 = 0 → 原位置不动
                        if (loTail == null) loHead = e;
                        else loTail.next = e;
                        loTail = e;
                    }
                    else {
                        // 第 oldCap 位 = 1 → 移到 +oldCap 位置
                        if (hiTail == null) hiHead = e;
                        else hiTail.next = e;
                        hiTail = e;
                    }
                } while ((e = e.next) != null);

                // 两条链表分别放到新数组对应位置
                if (loTail != null) {
                    loTail.next = null;
                    newTab[j] = loHead;
                }
                if (hiTail != null) {
                    hiTail.next = null;
                    newTab[j + oldCap] = hiHead;
                }
            }
        }
    }
}
```

### 5.3 扩容 rehash 图解

```
原容量 16，新容量 32：

  hash = 0b 10110 (二进制，低 5 位)
  oldCap = 16 = 0b10000
  hash & oldCap = 0b10110 & 0b10000 = 0b10000 = 16（非0）
  → 新位置 = 原位置 + 16 = j + oldCap

  hash = 0b 00110 (二进制，低 5 位)
  hash & oldCap = 0b00110 & 0b10000 = 0b00000 = 0
  → 新位置 = 原位置 = j

不需要重新计算 hash 值，直接判断 oldCap 位的值即可！✅
```

---

## 六、JDK 7 头插法 vs JDK 8 尾插法

### 6.1 为什么 JDK 7 用头插法？

```java
/**
 * JDK 7 put() 核心代码（简化）
 * 新元素插到链表头部，叫"头插法"
 */
void addEntry(int hash, K key, V value, int bucketIndex) {
    // 取出头节点的引用
    Entry<K, V> e = table[bucketIndex];

    // 新节点插到头部：newEntry.next = 旧头
    table[bucketIndex] = new Entry<>(hash, key, value, e);

    // 如果超过阈值，扩容
    if (size++ >= threshold)
        resize(2 * table.length);
}

/**
 * 头插法的链表结构（越晚插入的越靠前）：
 *
 * put("a") → table[3] = [a]
 * put("b") → table[3] = [b → a]
 * put("c") → table[3] = [c → b → a]
 *
 * 优点：最近访问/插入的元素在链表头部，查询时可能更快命中热点数据
 * 缺点：并发不安全（致命）
 */
```

### 6.2 JDK 7 头插法在并发下的死循环

```java
/**
 * JDK 7 并发 resize 时形成环形链表的经典场景：
 *
 * 单线程正常 resize（扩容前）：
 *
 *   扩容前 table：index=3 位置有条链表：e1 → e2 → null
 *   oldCap = 16, hash & oldCap 结果让 e1 和 e2 都落在新 index=3（假设如此）
 *
 *   扩容时用头插法：
 *   1. 取 e1：newTab[3] = e1
 *   2. 取 e2：e2.next = e1 → newTab[3] = e2 → e1 → null
 *   ✅ 正常反转链表
 *
 * 两个线程并发 resize（关键问题）：
 *
 *   线程 A 和 B 同时在 resize() 中遍历链表 e1 → e2 → null
 *   线程 A 先拿到了 e1 和 e2，但还没更新完 newTab
 *   线程 B 已经完成了 resize，但因头插法链表反转了
 *   此时 A 继续执行，链表结构已经被 B 改了
 *
 *   死循环场景（最经典）：
 *   原链表：e1 → e2 → null
 *
 *   线程 A：取 e1，e1.next = e2，线程 A 被挂起
 *   线程 B：正常完成 resize，链表变成 e2 → e1 → null
 *   线程 A 恢复：取 e2，此时 e2.next 在线程 B 改动后 = e1
 *   线程 A 将 e2 插入后：e2.next = e1，但 e1.next = e2
 *   → 形成环形链表！e1 ↔ e2 死循环
 *
 *   后续 get() 查找一个不存在的 key：
 *   遍历链表，陷入死循环 ❌ CPU 100%
 *
 * 根本原因：头插法在遍历过程中修改链表，导致顺序反转不可控
 */
```

### 6.3 JDK 8 尾插法如何解决

```java
/**
 * JDK 8 改用尾插法（遍历链表同时构建新链表，从尾部依次挂接）：
 *
 * 扩容时将原链表拆分为两条：
 *   loHead → loTail：hash & oldCap == 0 的节点，保持原位置
 *   hiHead → hiTail：hash & oldCap == 1 的节点，移动到 +oldCap 位置
 *
 * 尾插法的关键：
 *   不反转原链表的顺序，而是分别从 tail 依次挂接
 *   所以线程 A 和线程 B 并发时，不会形成环形链表
 *
 * JDK 8 尾插法逻辑（伪代码）：
 *
 *   loHead = loTail = null
 *   hiHead = hiTail = null
 *
 *   do {
 *       // 每次取一个节点，插到对应链表尾部
 *       if ((e.hash & oldCap) == 0) {
 *           if (loTail == null) loHead = e;
 *           else loTail.next = e;
 *           loTail = e;         // tail 后移
 *       } else {
 *           if (hiTail == null) hiHead = e;
 *           else hiTail.next = e;
 *           hiTail = e;
 *       }
 *   } while ((e = e.next) != null);
 *
 *   // 最后一次性挂到新数组（不是逐节点挂）
 *   if (loTail != null) {
 *       loTail.next = null;
 *       newTab[j] = loHead;      // loHead 指向原顺序第一个
 *   }
 *   if (hiTail != null) {
 *       hiTail.next = null;
 *       newTab[j + oldCap] = hiHead;
 *   }
 *
 * 尾插法不反转顺序，所以即使并发执行也不会形成环
 * 但 JDK 8 HashMap 仍然不是线程安全的！
 */
```

### 6.4 头插法 vs 尾插法总结

```
                    JDK 7 头插法                    JDK 8 尾插法
                ──────────────────              ──────────────────
插入方式          新节点插到链表头部                新节点插到链表尾部
扩容时            链表顺序反转                      链表顺序保持
并发问题          可能形成环形链表 → 死循环          不会形成环形链表
                 resize 时遍历 + 头插 → 顺序反转
                 两个线程并发 → 环 ❌               仍然线程不安全
                                                     但不会死循环 ✅
热点数据          头部是最新数据，查询快一点         顺序不变，最早的在前
```

---

## 七、ConcurrentHashMap 的演进

### 7.1 JDK 7 分段锁（Segment）

```java
/**
 * JDK 7 ConcurrentHashMap 的核心思想：
 * 把数据分成多个段（Segment），每个段各自加锁
 * 不同段的操作可以并行，提高并发度
 *
 * 结构：Segment 数组（默认 16） × 每个 Segment 内是 HashEntry 数组
 * 每个 Segment 继承 ReentrantLock，有自己的锁
 */
public class ConcurrentHashMapJDK7<K, V> {
    // 分段数组，默认 16 个段
    final Segment<K, V>[] segments;

    /**
     * Segment 继承 ReentrantLock
     * 每个 Segment 独立加锁，锁的粒度是单个 Segment
     */
    static final class Segment<K, V> extends ReentrantLock {
        transient volatile HashEntry<K, V>[] table;
        int count;       // Segment 内元素数量
    }

    /**
     * put() 流程：
     * 1. 根据 key 计算 hash，确定落在哪个 Segment
     * 2. 调用该 Segment 的 lock() 加锁
     * 3. 在该 Segment 内部进行 put（和普通 HashMap 一样）
     * 4. unlock() 解锁
     *
     * 并发度 = Segment 数量，默认 16
     * 即最多 16 个线程可以同时 put（不同 Segment）
     */
    public V put(K key, V value) {
        int hash = hash(key);
        int segIdx = (hash >>> 28) & (segments.length - 1);
        Segment<K, V> seg = segments[segIdx];

        seg.lock(); // 只锁这个 Segment，其他 Segment 不受影响
        try {
            // 在该 Segment 内操作
            // ... put 逻辑 ...
        } finally {
            seg.unlock();
        }
    }

    /**
     * get() 不用加锁！
     * 因为 volatile 保证可见性
     */
    public V get(Object key) {
        int hash = hash(key);
        Segment<K, V> seg = segments[(hash >>> 28) & (segments.length - 1)];
        return seg.table[hash & (tab.length - 1)].value; // volatile 读
    }
}

/**
 * JDK 7 分段锁图示：
 *
 * Segments[0]  ──→  HashEntry[]  ──→  链表（lock 锁住）
 * Segments[1]  ──→  HashEntry[]  ──→  链表（lock 锁住） ← 并发可访问
 * Segments[2]  ──→  HashEntry[]  ──→  链表（lock 锁住）
 * ...                                     ↑
 * Segments[15] ──→  HashEntry[]  ──→  链表（lock 锁住）
 *                                     不同段互不干扰，最多 16 并发
 */
```

### 7.2 JDK 8：CAS + synchronized（抛弃分段锁）

```java
/**
 * JDK 8 ConcurrentHashMap 的核心改进：
 * 去掉分段锁，改用 CAS + synchronized
 *
 * 锁的粒度细化到每个桶（Node）
 * synchronized 只在发生哈希冲突（链表或红黑树）时才加锁
 * 无冲突时用 CAS 无锁插入
 */
public class ConcurrentHashMapJDK8<K, V> {

    /**
     * put() 核心流程：
     *
     * 1. 计算 hash
     * 2. tabAt(cas) 拿到当前桶的头节点
     * 3. 如果桶为空：
     *      CAS 插入新节点（无锁）→ 成功则结束
     * 4. 如果桶不为空（发生冲突）：
     *      synchronized(桶头节点) 加锁
     *      链表遍历或红黑树插入
     * 5. 如果链表长度 > 8 → 树化
     * 6. 如果元素数量 > 阈值 → 扩容
     */

    /**
     * CAS 插入头节点（无锁路径）
     * tabAt: Unsafe 类直接读取 volatile 数组
     * casTabAt: CAS 更新数组指定位置
     */
    private final Node<K, V>[] table;

    V put(K key, V value, boolean onlyIfAbsent) {
        int hash = spread(key.hashCode());
        V oldValue = null;

        // 自旋
        for (Node<K, V>[] tab = this.table;;) {
            Node<K, V> f;
            int n, i, fh;

            // ① 数组还没初始化 → 初始化
            if (tab == null || (n = tab.length) == 0) {
                tab = initTable();
            }
            // ② 桶为空 → CAS 无锁插入（最快路径）
            else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
                Node<K, V> newNode = new Node<>(hash, key, value, null);
                if (casTabAt(tab, i, null, newNode)) {
                    break; // 插入成功，退出循环
                }
                // CAS 失败 → 说明其他线程已经插入了，继续循环
            }
            // ③ hash == MOVED → 正在扩容，协助扩容
            else if ((fh = f.hash) == MOVED) {
                tab = helpTransfer(tab, f);
            }
            // ④ 桶有数据 → synchronized 加锁，遍历链表/红黑树
            else {
                synchronized (f) { // f 是桶的头节点，锁住这个桶
                    // 再次检查（防止其他线程修改）
                    if (tabAt(tab, i) == f) {
                        // 链表遍历
                        if (fh >= 0) {
                            // ... 链表插入逻辑 ...
                        }
                        // 红黑树插入
                        else if (f instanceof TreeBin) {
                            // ... 红黑树插入逻辑 ...
                        }
                    }
                }
                // 插入/更新完成后检查是否需要树化
                if (binCount >= TREEIFY_THRESHOLD) {
                    treeifyBin(tab, i);
                }
                break;
            }
        }
        addCount(1L, binCount);
        return oldValue;
    }

    /**
     * JDK 8 vs JDK 7 对比：
     *
     *                JDK 7                        JDK 8
     *  锁机制      分段锁（Segment × 16）       CAS + synchronized
     *  锁粒度      段级别（粗粒度）             桶级别（细粒度）
     *  并发度      最多 16 线程并发写           远大于 16
     *  读操作      不用锁（volatile）          不用锁（volatile）
     *  扩容        单线程扩容                  多线程协作扩容
     *  内存占用    Segment 数组额外开销         更低（去掉 Segment）
     */
}
```

### 7.3 ConcurrentHashMap 扩容：多线程协作

```java
/**
 * JDK 8 ConcurrentHashMap 扩容机制：
 * 支持多线程协作扩容，而不是单线程扩容
 *
 * 核心思想：
 * 1. 一个线程发现需要扩容，创建新数组
 * 2. 其他线程看到正在扩容（hash == MOVED），会"协助"扩容
 * 3. 每个线程负责迁移一部分桶（stride = 16）
 * 4. 所有线程协作完成扩容
 *
 * 关键变量：
 *   transferIndex：当前待迁移的桶索引（从后往前分配）
 *   NextTable：新数组
 *   ForwardingNode：特殊节点，hash = MOVED，表示该桶正在迁移
 */

/**
 * ForwardingNode 作用：
 * 1. 标记该桶已经迁移完成
 * 2. get() 时会转发到新数组查询
 */
static final class ForwardingNode<K, V> extends Node<K, V> {
    final Node<K, V>[] nextTable;

    ForwardingNode(Node<K, V>[] tab) {
        super(MOVED, null, null, null);
        this.nextTable = tab;
    }
}
```

---

## 八、HashSet 底层实现

### 8.1 HashSet 就是 HashMap

```java
/**
 * HashSet 的实现非常简单：
 * 底层就是一个 HashMap
 * 用 HashMap 的 key 存储 HashSet 的元素
 * value 统一用同一个 dummy 对象（PRESENT）
 */
public class HashSet<E> extends AbstractSet<E>
        implements Set<E>, Cloneable, java.io.Serializable {

    // 底层就是一个 HashMap
    private transient HashMap<E, Object> map;

    // dummy value，所有 key 共享这个 value
    private static final Object PRESENT = new Object();

    /**
     * 构造函数：创建一个 HashMap
     */
    public HashSet() {
        map = new HashMap<>();
    }

    public HashSet(int initialCapacity) {
        map = new HashMap<>(initialCapacity);
    }

    public HashSet(int initialCapacity, float loadFactor) {
        map = new HashMap<>(initialCapacity, loadFactor);
    }

    /**
     * add() 就是调用 HashMap 的 put()
     * value 用 PRESENT
     * put() 返回旧值，如果 key 不存在返回 null
     * 所以 add() 返回 true 表示之前不存在
     */
    public boolean add(E e) {
        return map.put(e, PRESENT) == null;
    }

    /**
     * remove() 就是调用 HashMap 的 remove()
     */
    public boolean remove(Object o) {
        return map.remove(o) == PRESENT;
    }

    /**
     * contains() 就是调用 HashMap 的 containsKey()
     * O(1) 时间复杂度
     */
    public boolean contains(Object o) {
        return map.containsKey(o);
    }

    /**
     * size() 就是 HashMap 的 size()
     */
    public int size() {
        return map.size();
    }

    /**
     * clear() 就是 HashMap 的 clear()
     */
    public void clear() {
        map.clear();
    }

    /**
     * iterator() 就是 HashMap 的 keySet().iterator()
     */
    public Iterator<E> iterator() {
        return map.keySet().iterator();
    }
}
```

### 8.2 LinkedHashSet 和 TreeSet

```java
/**
 * LinkedHashSet：继承 HashSet，底层是 LinkedHashMap
 * 保持插入顺序或访问顺序
 */
public class LinkedHashSet<E> extends HashSet<E>
        implements Set<E>, Cloneable, java.io.Serializable {

    public LinkedHashSet() {
        super(16, .75f, true); // 调用 HashSet 的构造函数，创建 LinkedHashMap
    }
}

/**
 * TreeSet：底层是 TreeMap
 * 元素有序（自然排序或自定义比较器）
 */
public class TreeSet<E> extends AbstractSet<E>
        implements NavigableSet<E>, Cloneable, java.io.Serializable {

    private transient NavigableMap<E, Object> m;

    private static final Object PRESENT = new Object();

    public TreeSet() {
        this(new TreeMap<E, Object>()); // 底层是 TreeMap
    }

    public boolean add(E e) {
        return m.put(e, PRESENT) == null;
    }
}
```

---

## 九、Load Factor 0.75 的选择原因

### 9.1 时间和空间的权衡

```java
/**
 * loadFactor = 0.75 的原因：
 *
 * 1. 时间成本 vs 空间成本
 *
 *    负载因子越大（接近 1.0）：
 *      - 空间利用率高（桶填得满）
 *      - 但链表/红黑树变长，查询变慢
 *      - 碰撞概率增加
 *
 *    负载因子越小（接近 0.5）：
 *      - 查询快（链表短，碰撞少）
 *      - 但空间浪费（很多空桶）
 *      - 更频繁扩容
 *
 * 2. 0.75 是经验值的平衡点
 *
 *    泊松分布分析：
 *      负载因子 0.75 时，链表长度 >= 8 的概率 < 0.00006
 *      这是一个非常小的概率，几乎不会触发树化
 *
 *    如果负载因子 = 1.0：
 *      链表长度 >= 8 的概率显著增加
 *      查询性能下降明显
 *
 *    如果负载因子 = 0.5：
 *      空间浪费 50%
 *      频繁扩容影响性能
 *
 * 3. 源码注释中的解释
 *
 *    "As a general rule, the default load factor (.75)
 *     offers a good tradeoff between time and space costs."
 *
 *    "Higher values decrease the space overhead but increase
 *     the lookup cost (reflected in most of the operations of
 *     the HashMap class, including get and put)."
 */
```

### 9.2 负载因子与性能的关系

```
负载因子    空间利用率    平均链表长度    查询时间
─────────────────────────────────────────────────
  0.5        50%          很短          最快 O(1)
  0.75       75%          短            快 O(1) ✅ 默认
  1.0        100%         较长          较慢 O(1)~O(n)
  2.0        200%         长            慢 O(n)

建议：
- 内存充足、追求查询速度：loadFactor = 0.5 ~ 0.75
- 内存紧张、数据量大：loadFactor = 0.75 ~ 1.0
- 特殊场景（已知数据量）：初始化时指定容量，避免扩容
  HashMap map = new HashMap<>(expectedSize / 0.75 + 1);
```

---

## 十、HashMap 线程不安全的原因

### 10.1 多线程并发写入问题

```java
/**
 * HashMap 线程不安全的表现：
 *
 * 1. 数据丢失
 *    两个线程同时 put，计算出的 index 相同
 *    线程 A 先写入，线程 B 后写入覆盖了 A 的值
 *
 * 2. 扩容时环形链表（JDK 7）
 *    头插法 + 并发 resize → 环形链表 → 死循环
 *
 * 3. size 计数不准确
 *    size++ 不是原子操作
 *    两个线程同时 size++，最终 size 少 1
 *
 * 4. 扩容期间数据丢失
 *    一个线程在扩容，另一个线程在 put
 *    put 的数据可能被扩容后的新数组覆盖
 */
public class HashMapUnsafeDemo {
    public static void main(String[] args) throws Exception {
        HashMap<Integer, Integer> map = new HashMap<>();

        // 多线程并发写入
        Thread[] threads = new Thread[100];
        for (int i = 0; i < 100; i++) {
            final int idx = i;
            threads[i] = new Thread(() -> {
                for (int j = 0; j < 1000; j++) {
                    map.put(idx * 1000 + j, j);
                }
            });
        }

        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();

        // 理论上应该是 100 * 1000 = 100000
        // 实际可能小于 100000，因为数据丢失
        System.out.println("Expected: 100000");
        System.out.println("Actual: " + map.size());
    }
}
```

### 10.2 为什么不用 Hashtable？

```java
/**
 * Hashtable 为什么被淘汰？
 *
 * 1. 所有方法都加 synchronized，锁住整个 table
 *    并发度极低，一个线程操作，其他线程全部阻塞
 *
 * 2. 不允许 null key 和 null value
 *    HashMap 允许一个 null key 和多个 null value
 *
 * 3. 继承 Dictionary（过时的类）
 *    HashMap 继承 AbstractMap
 */
public class Hashtable<K, V> extends Dictionary<K, V>
        implements Map<K, V>, Cloneable, java.io.Serializable {

    // 所有方法都加 synchronized
    public synchronized V put(K key, V value) {
        // ...
    }

    public synchronized V get(Object key) {
        // ...
    }

    public synchronized V remove(Object key) {
        // ...
    }

    // 连 size() 都加锁！
    public synchronized int size() {
        return count;
    }
}
```

### 10.3 线程安全的替代方案

```java
/**
 * 线程安全的 HashMap 替代方案：
 *
 * 1. ConcurrentHashMap（推荐）
 *    - JDK 7：分段锁，并发度 = Segment 数量
 *    - JDK 8：CAS + synchronized，锁粒度更细
 *    - 性能最好，功能最全
 *
 * 2. Collections.synchronizedMap()
 *    - 包装一个 HashMap，所有方法加 synchronized
 *    - 锁粒度粗，性能差
 *    - 简单场景可用
 *
 * 3. Hashtable（不推荐）
 *    - 所有方法加 synchronized
 *    - 性能最差
 *    - 仅用于兼容老代码
 */
public class ThreadSafeMapDemo {
    public static void main(String[] args) {
        // 方案 1：ConcurrentHashMap（推荐）
        Map<Integer, Integer> map1 = new ConcurrentHashMap<>();

        // 方案 2：synchronizedMap
        Map<Integer, Integer> map2 = Collections.synchronizedMap(new HashMap<>());

        // 方案 3：Hashtable（不推荐）
        Map<Integer, Integer> map3 = new Hashtable<>();
    }
}
```

---

## 十一、高频面试题

### Q1: HashMap 的底层实现原理是什么？

**答：**

JDK 7：数组 + 链表，使用头插法。每个数组位置是一个桶，桶内用链表解决哈希冲突。

JDK 8：数组 + 链表 + 红黑树，使用尾插法。当链表长度 ≥ 8 且数组容量 ≥ 64 时，链表转红黑树；当红黑树节点 ≤ 6 时退化回链表。红黑树查询 O(log n)，比链表 O(n) 快得多。

---

### Q2: HashMap 的扩容机制是怎样的？

**答：**

1. **触发条件**：元素数量 > threshold（capacity × loadFactor），默认 16 × 0.75 = 12

2. **扩容方式**：容量翻倍（newCap = oldCap << 1）

3. **rehash 优化**：不需要重新计算 hash，只需判断原 hash 的 oldCap 位：
   - 该位 = 0 → 位置不变
   - 该位 = 1 → 新位置 = 原位置 + oldCap

4. **JDK 7 vs JDK 8**：
   - JDK 7 头插法，链表反转，并发下可能死循环
   - JDK 8 尾插法，链表顺序保持，避免死循环

---

### Q3: 为什么 HashMap 的容量必须是 2 的幂次？

**答：**

1. **位运算替代取模**：index = (n - 1) & hash 等价于 hash % n，位运算更快

2. **均匀分布**：n = 2^k 时，n - 1 的二进制低位全是 1，& 运算能充分利用 hash 的低位信息，分布均匀

3. **扩容均匀**：扩容为 2 倍时，只需要看原 hash 的一个 bit 位就能决定新位置，均匀分散

---

### Q4: HashMap 为什么线程不安全？如何解决？

**答：**

**不安全的原因：**

1. **数据丢失**：两个线程同时 put 到同一个桶，后写入的覆盖前一个
2. **JDK 7 死循环**：头插法 + 并发 resize 形成环形链表
3. **size 不准确**：size++ 不是原子操作

**解决方案：**

1. **ConcurrentHashMap**（推荐）：CAS + synchronized，锁粒度细，性能最好
2. **Collections.synchronizedMap()**：包装 HashMap，所有方法加 synchronized
3. **Hashtable**：所有方法加 synchronized，性能差，不推荐

---

### Q5: ConcurrentHashMap 在 JDK 7 和 JDK 8 的区别？

**答：**

| 对比项 | JDK 7 | JDK 8 |
|--------|-------|-------|
| 锁机制 | 分段锁（Segment） | CAS + synchronized |
| 锁粒度 | 段级别（默认 16 个段） | 桶级别（每个 Node） |
| 并发度 | 最多 16 线程 | 理论上无限制 |
| 扩容 | 单线程扩容 | 多线程协作扩容 |
| 内存占用 | 额外 Segment 数组开销 | 更低，无 Segment |
| get() | 不用锁（volatile） | 不用锁（volatile） |
| 底层结构 | Segment[] × HashEntry[] | Node[]（统一数组） |

**JDK 8 改进：**
- 去掉分段锁，锁粒度从"段"细化到"桶"
- 无冲突时用 CAS 无锁插入，性能大幅提升
- synchronized 只在链表/红黑树操作时加锁，锁粒度更细
- 支持多线程协作扩容，多线程同时参与迁移

---

### Q6: HashMap 如何实现equals和hashCode协同？

**答：**

Java 规范要求：**相等的对象必须有相同的 hashCode**

```java
public class Person {
    private String name;
    private int age;

    // 两个对象 equals() 返回 true → hashCode() 必须相同
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return age == person.age && Objects.equals(name, person.name);
    }

    @Override
    public int hashCode() {
        // 用参与 equals() 判断的字段来计算 hashCode
        return Objects.hash(name, age);
    }
}

/**
 * 常见错误：重写 equals() 但不重写 hashCode()
 *
 * Person p1 = new Person("Alice", 20);
 * Person p2 = new Person("Alice", 20);
 *
 * p1.equals(p2) = true
 * p1.hashCode() = 某个值
 * p2.hashCode() = 另一个值 ❌ 违反契约！
 *
 * 后果：
 * - p1 和 p2 可以同时存入 HashMap（不同桶）
 * - HashSet 可能出现重复元素
 * - HashMap 的查找逻辑失效
 */
```

---

## 📚 参考资料

- [HashMap 源码（JDK 8）](https://hg.openjdk.org/jdk8u/jdk8u/langtools/file/tip/src/share/classes/java/util/HashMap.java)
- [ConcurrentHashMap 源码（JDK 8）](https://hg.openjdk.org/jdk8u/jdk8u/langtools/file/tip/src/share/classes/java/util/concurrent/ConcurrentHashMap.java)
- [HashMap 底层实现详解 - 美团技术团队](https://tech.meituan.com/2016/06/24/java-hashmap.html)
- [ConcurrentHashMap 源码分析 - 郭耀的技术博客](https://www.jianshu.com/p/5c8fcde0c2b3)

---

**⭐ 重点：HashMap 是 Java 最核心的集合，面试必问。建议结合源码阅读，理解会更深刻。**