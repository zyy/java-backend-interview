---
layout: default
title: 集合类对比
---
# 集合类对比

> 选择合适的集合类

## 🎯 面试重点

- 各集合类的特点
- 适用场景
- 线程安全问题

## 📖 List 对比

```java
/**
 * List 对比
 */
public class ListCompare {
    // ArrayList
    /*
     * 特点：数组实现，随机访问 O(1)，插入删除 O(n)
     * 适用：随机访问多，插入删除少
     * 线程安全：无
     */
    
    // LinkedList
    /*
     * 特点：链表实现，插入删除 O(1)，随机访问 O(n)
     * 适用：插入删除多，随机访问少
     * 线程安全：无
     */
    
    // Vector
    /*
     * 特点：数组实现，线程安全（synchronized）
     * 适用：需要线程安全时（已淘汰，用 Collections.synchronizedList）
     */
}
```

## 📖 Set 对比

```java
/**
 * Set 对比
 */
public class SetCompare {
    // HashSet
    /*
     * 特点：哈希表实现，无序，唯一
     * 时间复杂度：添加/删除/查找 O(1)
     */
    
    // LinkedHashSet
    /*
     * 特点：哈希表 + 链表，保持插入顺序
     * 适用：需要保持顺序的去重
     */
    
    // TreeSet
    /*
     * 特点：红黑树实现，有序，唯一
     * 时间复杂度：O(log n)
     * 适用：需要排序的场景
     */
}
```

## 📖 Map 对比

```java
/**
 * Map 对比
 */
public class MapCompare {
    // HashMap
    /*
     * 特点：哈希表实现，O(1) 查找/插入
     * 允许 null 键/值
     * JDK 8+ 红黑树优化
     */
    
    // LinkedHashMap
    /*
     * 特点：保持插入顺序
     * 适用：LRU 缓存
     */
    
    // TreeMap
    /*
     * 特点：红黑树实现，按键排序
     * 适用：需要排序的场景
     */
    
    // Hashtable
    /*
     * 特点：线程安全（synchronized）
     * 不允许 null 键/值（已淘汰）
     */
    
    // ConcurrentHashMap
    /*
     * 特点：JDK 8+ CAS + synchronized，线程安全，高性能
     * 适用：高并发场景
     */
}
```

## 📖 面试真题

### Q1: HashMap 和 Hashtable 的区别？

**答：** 
- Hashtable 线程安全，不允许 null
- HashMap 线程不安全，允许 null
- HashMap 性能更好

### Q2: ArrayList 和 LinkedList 的区别？

**答：** ArrayList 随机访问 O(1)，LinkedList 插入删除 O(1)。

---

**⭐ 重点：根据场景选择合适的集合类**