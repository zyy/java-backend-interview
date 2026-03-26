---
layout: default
title: LRU 缓存设计与实现 ⭐⭐⭐
---

# LRU 缓存设计与实现 ⭐⭐⭐

## 🎯 面试核心

LRU（Least Recently Used）缓存是高频面试题，考察数据结构设计、哈希表、链表等多个知识点。理解 LRU 的原理和实现，对系统设计也很有帮助。

---

## 一、LRU 核心思想

### 什么是 LRU？

```
LRU = Least Recently Used（最近最少使用）

核心规则：
1. 容量有限（capacity）
2. 访问数据时，该数据变为"最近使用"
3. 容量满时，删除"最近最少使用"的数据
4. 新数据插入时，变为"最近使用"

时间轴示例：
初始：[]
put(1, 'a')：[1]
put(2, 'b')：[1, 2]（2 最近）
get(1)：[2, 1]（1 变为最近）
put(3, 'c')，capacity=2：[1, 3]（2 被删除，因为最少使用）
```

### 为什么需要 LRU？

- **缓存淘汰策略**：内存有限，需要删除不常用的数据
- **性能优化**：热数据保留，冷数据删除
- **实际应用**：CPU 缓存、Redis 缓存、浏览器缓存等

---

## 二、数据结构选择

### 需要什么操作？

```
1. get(key)：O(1) 查询
2. put(key, value)：O(1) 插入/更新
3. 删除最少使用的数据：O(1)
4. 更新访问顺序：O(1)
```

### 为什么选择 HashMap + 双向链表？

| 数据结构 | get | put | 删除最少使用 | 更新顺序 |
|---------|-----|-----|------------|---------|
| HashMap | O(1) | O(1) | O(N) | ✗ |
| 单向链表 | O(N) | O(N) | O(1) | O(N) |
| **HashMap + 双向链表** | **O(1)** | **O(1)** | **O(1)** | **O(1)** |

**双向链表的作用**：
- 维护访问顺序（最近使用的在头部，最少使用的在尾部）
- 支持 O(1) 删除任意节点（需要前驱指针）

---

## 三、手写 LRU 缓存（推荐方案）

### 方案 1：HashMap + 双向链表（完全手写）

```java
class LRUCache {
    // 双向链表节点
    private class Node {
        int key;
        int value;
        Node prev;
        Node next;
        
        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }
    
    private int capacity;
    private Map<Integer, Node> cache;  // key -> Node
    private Node head;  // 虚拟头节点（最近使用）
    private Node tail;  // 虚拟尾节点（最少使用）
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        
        // 初始化虚拟头尾节点
        this.head = new Node(0, 0);
        this.tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }
    
    /**
     * 获取缓存值
     * 时间：O(1)
     */
    public int get(int key) {
        if (!cache.containsKey(key)) {
            return -1;
        }
        
        Node node = cache.get(key);
        // 将该节点移到头部（标记为最近使用）
        moveToHead(node);
        return node.value;
    }
    
    /**
     * 放入缓存
     * 时间：O(1)
     */
    public void put(int key, int value) {
        if (cache.containsKey(key)) {
            // 更新已存在的 key
            Node node = cache.get(key);
            node.value = value;
            moveToHead(node);
        } else {
            // 新增 key
            Node newNode = new Node(key, value);
            cache.put(key, newNode);
            addToHead(newNode);
            
            // 检查容量
            if (cache.size() > capacity) {
                // 删除最少使用的节点（尾部）
                Node removed = removeTail();
                cache.remove(removed.key);
            }
        }
    }
    
    /**
     * 将节点移到头部
     */
    private void moveToHead(Node node) {
        removeNode(node);
        addToHead(node);
    }
    
    /**
     * 添加节点到头部
     */
    private void addToHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }
    
    /**
     * 删除节点
     */
    private void removeNode(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    /**
     * 删除尾部节点（最少使用）
     */
    private Node removeTail() {
        Node node = tail.prev;
        removeNode(node);
        return node;
    }
}

/**
 * 使用示例
 */
public class LRUCacheDemo {
    public static void main(String[] args) {
        LRUCache cache = new LRUCache(2);
        
        cache.put(1, 1);
        cache.put(2, 2);
        System.out.println(cache.get(1));  // 1
        
        cache.put(3, 3);  // 删除 key 2
        System.out.println(cache.get(2));  // -1
        
        cache.put(4, 4);  // 删除 key 1
        System.out.println(cache.get(1));  // -1
        System.out.println(cache.get(3));  // 3
        System.out.println(cache.get(4));  // 4
    }
}
```

**复杂度分析**

- 时间复杂度：get O(1)，put O(1)
- 空间复杂度：O(capacity)

---

### 方案 2：LinkedHashMap 实现（JDK 内置）

```java
/**
 * 使用 LinkedHashMap 实现 LRU
 * LinkedHashMap 内部维护了访问顺序
 */
class LRUCacheLinkedHashMap extends LinkedHashMap<Integer, Integer> {
    private int capacity;
    
    public LRUCacheLinkedHashMap(int capacity) {
        // 第三个参数 true 表示按访问顺序排序（LRU）
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }
    
    /**
     * 重写 removeEldestEntry，当容量超过时删除最老的条目
     */
    @Override
    protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
        return size() > capacity;
    }
    
    public int get(int key) {
        return super.getOrDefault(key, -1);
    }
    
    public void put(int key, int value) {
        super.put(key, value);
    }
}

/**
 * 使用示例
 */
public class LRUCacheLinkedHashMapDemo {
    public static void main(String[] args) {
        LRUCacheLinkedHashMap cache = new LRUCacheLinkedHashMap(2);
        
        cache.put(1, 1);
        cache.put(2, 2);
        System.out.println(cache.get(1));  // 1
        
        cache.put(3, 3);  // 删除 key 2
        System.out.println(cache.get(2));  // -1
    }
}
```

**优点**：代码简洁，利用 JDK 内置实现

**缺点**：面试时通常要求手写，不能用 LinkedHashMap

---

## 四、LRU vs LFU vs TTL

### 对比分析

| 策略 | 淘汰规则 | 适用场景 | 实现复杂度 |
|------|--------|--------|----------|
| **LRU** | 最近最少使用 | 热数据集中，访问模式稳定 | 中等 |
| **LFU** | 最不经常使用 | 访问频率差异大 | 高 |
| **TTL** | 过期时间 | 临时数据、会话 | 低 |
| **FIFO** | 先进先出 | 简单场景 | 低 |

### Redis 中的缓存淘汰策略

```
1. noeviction：不删除，返回错误
2. allkeys-lru：在所有 key 中，删除最近最少使用的
3. allkeys-lfu：在所有 key 中，删除最不经常使用的
4. allkeys-random：在所有 key 中，随机删除
5. volatile-lru：在设置了过期时间的 key 中，删除最近最少使用的
6. volatile-lfu：在设置了过期时间的 key 中，删除最不经常使用的
7. volatile-ttl：在设置了过期时间的 key 中，删除剩余 TTL 最短的
8. volatile-random：在设置了过期时间的 key 中，随机删除
```

---

## 五、LFU 缓存实现

### LFU 核心思想

```
LFU = Least Frequently Used（最不经常使用）

与 LRU 的区别：
- LRU：关注最后访问时间
- LFU：关注访问频率

淘汰规则：
1. 删除访问频率最低的数据
2. 如果频率相同，删除最久未使用的数据
```

### LFU 实现

```java
class LFUCache {
    private class Node {
        int key;
        int value;
        int freq;  // 访问频率
        long timestamp;  // 时间戳（用于频率相同时的比较）
        
        Node(int key, int value) {
            this.key = key;
            this.value = value;
            this.freq = 1;
            this.timestamp = System.nanoTime();
        }
    }
    
    private int capacity;
    private Map<Integer, Node> cache;
    private Map<Integer, PriorityQueue<Node>> freqMap;  // freq -> 优先队列
    private int minFreq;
    
    public LFUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        this.freqMap = new HashMap<>();
        this.minFreq = 0;
    }
    
    public int get(int key) {
        if (!cache.containsKey(key)) {
            return -1;
        }
        
        Node node = cache.get(key);
        updateFreq(node);
        return node.value;
    }
    
    public void put(int key, int value) {
        if (capacity <= 0) return;
        
        if (cache.containsKey(key)) {
            Node node = cache.get(key);
            node.value = value;
            updateFreq(node);
        } else {
            if (cache.size() >= capacity) {
                // 删除最不经常使用的节点
                evict();
            }
            
            Node newNode = new Node(key, value);
            cache.put(key, newNode);
            freqMap.computeIfAbsent(1, k -> new PriorityQueue<>(
                (a, b) -> Long.compare(a.timestamp, b.timestamp)
            )).offer(newNode);
            minFreq = 1;
        }
    }
    
    private void updateFreq(Node node) {
        int oldFreq = node.freq;
        node.freq++;
        node.timestamp = System.nanoTime();
        
        // 从旧频率队列中移除
        freqMap.get(oldFreq).remove(node);
        
        // 如果旧频率队列为空且是最小频率，更新最小频率
        if (freqMap.get(oldFreq).isEmpty()) {
            freqMap.remove(oldFreq);
            if (oldFreq == minFreq) {
                minFreq++;
            }
        }
        
        // 添加到新频率队列
        freqMap.computeIfAbsent(node.freq, k -> new PriorityQueue<>(
            (a, b) -> Long.compare(a.timestamp, b.timestamp)
        )).offer(node);
    }
    
    private void evict() {
        PriorityQueue<Node> minFreqQueue = freqMap.get(minFreq);
        Node removed = minFreqQueue.poll();
        cache.remove(removed.key);
        
        if (minFreqQueue.isEmpty()) {
            freqMap.remove(minFreq);
        }
    }
}
```

**复杂度分析**

- 时间复杂度：get O(log N)，put O(log N)
- 空间复杂度：O(capacity)

---

## 六、LeetCode 146 完整代码

```java
/**
 * LeetCode 146: LRU Cache
 * 
 * 设计一个 LRU 缓存，支持以下操作：
 * 1. get(key)：获取值，如果 key 存在返回值，否则返回 -1
 * 2. put(key, value)：设置值，如果 key 存在则更新，否则插入
 * 
 * 两个操作都应该在 O(1) 时间复杂度内完成
 */
class LRUCache {
    private class Node {
        int key;
        int value;
        Node prev;
        Node next;
        
        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }
    
    private int capacity;
    private Map<Integer, Node> cache;
    private Node head;
    private Node tail;
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        this.head = new Node(0, 0);
        this.tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }
    
    public int get(int key) {
        if (!cache.containsKey(key)) {
            return -1;
        }
        
        Node node = cache.get(key);
        moveToHead(node);
        return node.value;
    }
    
    public void put(int key, int value) {
        if (cache.containsKey(key)) {
            Node node = cache.get(key);
            node.value = value;
            moveToHead(node);
        } else {
            Node newNode = new Node(key, value);
            cache.put(key, newNode);
            addToHead(newNode);
            
            if (cache.size() > capacity) {
                Node removed = removeTail();
                cache.remove(removed.key);
            }
        }
    }
    
    private void moveToHead(Node node) {
        removeNode(node);
        addToHead(node);
    }
    
    private void addToHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }
    
    private void removeNode(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    private Node removeTail() {
        Node node = tail.prev;
        removeNode(node);
        return node;
    }
}

/**
 * 测试用例
 */
public class LRUCacheTest {
    public static void main(String[] args) {
        LRUCache cache = new LRUCache(2);
        
        // 测试 1：基本操作
        cache.put(1, 1);
        cache.put(2, 2);
        assert cache.get(1) == 1;  // 返回 1
        
        // 测试 2：容量满，删除最少使用
        cache.put(3, 3);  // 删除 key 2
        assert cache.get(2) == -1;  // 返回 -1
        
        // 测试 3：更新访问顺序
        cache.put(4, 4);  // 删除 key 1
        assert cache.get(1) == -1;  // 返回 -1
        assert cache.get(3) == 3;   // 返回 3
        assert cache.get(4) == 4;   // 返回 4
        
        System.out.println("All tests passed!");
    }
}
```

---

## 七、高频面试题总结

| 题目 | 难度 | 关键点 | 时间复杂度 |
|------|------|--------|-----------|
| LRU 缓存设计 | ⭐⭐⭐ | HashMap + 双向链表 | O(1) |
| LFU 缓存设计 | ⭐⭐⭐ | HashMap + 优先队列 | O(log N) |
| 缓存淘汰策略 | ⭐⭐ | 理解 LRU/LFU/TTL | - |
| Redis 缓存 | ⭐⭐ | 实际应用 | - |

---

## 八、面试建议

1. **理解原理**：LRU 的核心是维护访问顺序，不是简单的删除
2. **选择数据结构**：HashMap + 双向链表是标准方案
3. **边界条件**：容量为 0、1，单个操作等
4. **代码规范**：虚拟头尾节点简化代码，避免空指针
5. **扩展思考**：LFU、TTL、多级缓存等变种
6. **实际应用**：Redis、Memcached、CPU 缓存等
