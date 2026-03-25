---
layout: default
title: HashMap 原理详解 ⭐⭐⭐
---
# HashMap 原理详解 ⭐⭐⭐

## 面试题：介绍一下 HashMap 底层的实现原理

### 核心回答

HashMap 是 Java 中最常用的集合类之一，基于**哈希表**实现，提供快速的键值对存取操作。

### 数据结构（JDK 1.8）

```
JDK 1.8 之前：数组 + 链表
JDK 1.8 及之后：数组 + 链表 + 红黑树
```

**结构说明：**
- **数组（Node[] table）**：存储哈希桶，默认初始容量 16
- **链表**：解决哈希冲突，采用拉链法
- **红黑树**：当链表长度超过 8 且数组长度 ≥ 64 时，链表转为红黑树

### 核心参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| DEFAULT_INITIAL_CAPACITY | 16 | 默认初始容量（必须是 2 的幂） |
| DEFAULT_LOAD_FACTOR | 0.75 | 默认负载因子 |
| TREEIFY_THRESHOLD | 8 | 链表转红黑树阈值 |
| UNTREEIFY_THRESHOLD | 6 | 红黑树转链表阈值 |
| MIN_TREEIFY_CAPACITY | 64 | 最小树化容量 |

### put() 方法执行流程

```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}

// 扰动函数：让高位也参与运算，减少哈希冲突
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```

**执行步骤：**

1. **计算哈希值**：通过 `hash()` 方法计算 key 的哈希值
2. **计算索引**：`index = (n - 1) & hash`（等价于 `hash % n`，但位运算更快）
3. **检查位置**：
   - 如果位置为空，直接插入新节点
   - 如果位置不为空，检查 key 是否相同（hashCode 和 equals）
4. **处理冲突**：
   - key 相同：覆盖旧值
   - key 不同：遍历链表/红黑树，找到合适位置插入
5. **检查转换**：链表长度 ≥ 8 且数组长度 ≥ 64，转为红黑树
6. **检查扩容**：元素数量 > 容量 × 负载因子，触发扩容

### 扩容机制

**触发条件**：`size > threshold`（threshold = capacity × loadFactor）

**扩容过程**：
1. 创建新数组，容量为原来的 2 倍
2. 重新计算每个元素在新数组中的位置
3. JDK 1.8 优化：元素位置要么在原位置，要么在原位置 + 旧容量

```java
// JDK 1.8 扩容时的位置计算
if ((e.hash & oldCap) == 0) {
    // 位置不变
} else {
    // 位置 = 原位置 + 旧容量
}
```

### 为什么用红黑树而不是AVL树？

| 特性 | 红黑树 | AVL树 |
|------|--------|-------|
| 平衡度 | 弱平衡（黑高平衡） | 强平衡（高度差 ≤ 1） |
| 查找 | O(log n) | O(log n) |
| 插入/删除 | 旋转次数少，O(1)次 | 旋转次数多，O(log n)次 |
| 适用场景 | 插入删除频繁 | 查询频繁 |

**结论**：HashMap 中插入删除操作频繁，红黑树综合性能更好。

### 为什么容量必须是 2 的幂？

1. **位运算替代取模**：`(n-1) & hash` 等价于 `hash % n`，但位运算效率更高
2. **均匀分布**：2 的幂能让哈希值均匀分布在数组中
3. **扩容优化**：元素在新数组中的位置计算更简单

### 线程安全问题

**HashMap 不是线程安全的**，多线程环境下可能出现：
- 数据丢失（两个线程同时扩容）
- 死循环（JDK 1.7 头插法导致）

**解决方案**：
- 使用 `ConcurrentHashMap`（推荐）
- 使用 `Collections.synchronizedMap()`

### 高频面试题

**Q1: HashMap 和 Hashtable 的区别？**
- HashMap 非线程安全，Hashtable 线程安全
- HashMap 允许 null key/value，Hashtable 不允许
- HashMap 继承 AbstractMap，Hashtable 继承 Dictionary

**Q2: HashMap 和 ConcurrentHashMap 的区别？**
- ConcurrentHashMap 线程安全，采用分段锁（JDK 1.7）或 CAS + synchronized（JDK 1.8）
- ConcurrentHashMap 性能更好，锁粒度更细

**Q3: 为什么重写 equals() 必须重写 hashCode()？**
- HashMap 先比较 hashCode，再比较 equals
- 如果只重写 equals，可能导致相同对象计算出不同哈希值，无法正确查找

### 代码示例

```java
// 自定义对象作为 Key，必须重写 equals 和 hashCode
public class Person {
    private String name;
    private int age;
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return age == person.age && Objects.equals(name, person.name);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}
```

---

**参考链接：**
- [Java HashMap实现原理-阿里云](https://www.aliyun.com/sswb/297758.html)
- [Java面试必问:HashMap底层原理详解-CSDN](https://blog.csdn.net/qwq123q/article/details/146551173)
