---
layout: default
title: 手写 LRU 缓存
---
# 手写 LRU 缓存

> 经典面试题

## 🎯 面试重点

- LRU 原理
- 实现方式

## 📖 实现

```java
/**
 * LRU 缓存
 */
public class LRUCache<K, V> {
    private int capacity;
    private Map<K, Node<K, V>> map;
    private Node<K, V> head, tail;
    
    static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev, next;
    }
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.map = new HashMap<>();
        head = new Node<>();
        tail = new Node<>();
        head.next = tail;
        tail.prev = head;
    }
    
    public V get(K key) {
        Node<K, V> node = map.get(key);
        if (node == null) return null;
        moveToHead(node);
        return node.value;
    }
    
    public void put(K key, V value) {
        Node<K, V> node = map.get(key);
        if (node != null) {
            node.value = value;
            moveToHead(node);
        } else {
            node = new Node<>();
            node.key = key;
            node.value = value;
            map.put(key, node);
            addToHead(node);
            if (map.size() > capacity) {
                Node<K, V> removed = removeTail();
                map.remove(removed.key);
            }
        }
    }
    
    private void moveToHead(Node<K, V> node) {
        removeNode(node);
        addToHead(node);
    }
    
    private void addToHead(Node<K, V> node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }
    
    private void removeNode(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    private Node<K, V> removeTail() {
        Node<K, V> node = tail.prev;
        removeNode(node);
        return node;
    }
}
```

## 📖 面试真题

### Q1: LRU 时间复杂度？

**答：** HashMap + 双向链表，get/put 都是 O(1)。

---

**⭐ 重点：LinkedHashMap 已经实现了 LRU**