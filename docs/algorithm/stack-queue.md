# 栈与队列

> 线性数据结构

## 🎯 面试重点

- 栈和队列特点
- 常见应用

## 📖 栈

```java
/**
 * 栈：后进先出 (LIFO)
 */
public class StackDemo {
    // 实现
    /*
     * class MyStack<T> {
     *     private LinkedList<T> list = new LinkedList<>();
     *     public void push(T t) { list.addFirst(t); }
     *     public T pop() { return list.removeFirst(); }
     *     public T peek() { return list.getFirst(); }
     * }
     */
    
    // 应用
    /*
     * - 函数调用栈
     * - 括号匹配
     * - 表达式求值
     * - 浏览器前进后退
     */
}
```

## 📖 队列

```java
/**
 * 队列：先进先出 (FIFO)
 */
public class QueueDemo {
    // 实现
    /*
     * class MyQueue<T> {
     *     private LinkedList<T> list = new LinkedList<>();
     *     public void offer(T t) { list.addLast(t); }
     *     public T poll() { return list.removeFirst(); }
     *     public T peek() { return list.getFirst(); }
     * }
     */
    
    // 应用
    /*
     * - BFS
     * - 消息队列
     * - 任务调度
     */
}
```

## 📖 面试真题

### Q1: 用两个栈实现队列？

**答：** 入队时压入 stack1，出队时从 stack2 弹出，stack2 为空时将 stack1 倒入。

---

**⭐ 重点：栈和队列是很多算法的基础**