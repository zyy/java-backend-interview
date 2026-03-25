# 数组与链表

> 基础数据结构

## 🎯 面试重点

- 数组和链表的区别
- 常见面试题

## 📖 对比

```java
/**
 * 数组 vs 链表
 */
public class ArrayVsLinkedList {
    /*
     * | 特性     | 数组   | 链表   |
     * |----------|--------|--------|
     * | 内存     | 连续   | 不连续 |
     * | 访问     | O(1)   | O(n)   |
     * | 插入     | O(n)   | O(1)   |
     * | 删除     | O(n)   | O(1)   |
     * | 空间     | 固定   | 动态   |
     */
}
```

## 📖 常见题型

```java
/**
 * 常见题型
 */
public class CommonProblems {
    // 1. 反转链表
    /*
     * public ListNode reverse(ListNode head) {
     *     ListNode prev = null;
     *     while (head != null) {
     *         ListNode next = head.next;
     *         head.next = prev;
     *         prev = head;
     *         head = next;
     *     }
     *     return prev;
     * }
     */
    
    // 2. 合并有序链表
    /*
     * public ListNode merge(ListNode l1, ListNode l2) {
     *     if (l1 == null) return l2;
     *     if (l2 == null) return l1;
     *     if (l1.val < l2.val) {
     *         l1.next = merge(l1.next, l2);
     *         return l1;
     *     } else {
     *         l2.next = merge(l1, l2.next);
     *         return l2;
     *     }
     * }
     */
}
```

## 📖 面试真题

### Q1: 数组和链表的区别？

**答：** 数组连续内存，O(1) 访问；链表不连续，O(1) 插入删除。

---

**⭐ 重点：数组和链表是最基础的数据结构**