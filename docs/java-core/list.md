---
layout: default
title: ArrayList 与 LinkedList 区别 ⭐⭐
---
# ArrayList 与 LinkedList 区别 ⭐⭐

## 面试题：ArrayList 和 LinkedList 有什么区别？

### 核心回答

ArrayList 和 LinkedList 都是 List 接口的实现类，但底层数据结构不同，导致它们在性能特征上有显著差异。

### 对比总览

| 特性 | ArrayList | LinkedList |
|------|-----------|------------|
| **底层结构** | 动态数组（Object[]） | 双向链表（Node） |
| **随机访问** | O(1) - 极快 | O(n) - 慢 |
| **尾部插入/删除** | O(1)（均摊） | O(1) |
| **中间插入/删除** | O(n) - 需要移动元素 | O(1)（找到位置后） |
| **内存占用** | 较少（只存数据） | 较多（额外存前后指针） |
| **扩容机制** | 1.5 倍扩容 | 无需扩容 |
| **线程安全** | 不安全 | 不安全 |

### ArrayList 详解

#### 底层结构

```java
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, Serializable {
    
    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 10;
    
    // 存储元素的数组
    transient Object[] elementData;
    
    // 实际元素个数
    private int size;
}
```

#### 扩容机制

```java
// 添加元素时的扩容逻辑
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    // 新容量 = 旧容量的 1.5 倍
    int newCapacity = oldCapacity + (oldCapacity >> 1);
    
    // 如果还不够，使用所需的最小容量
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    
    // 创建新数组，复制数据
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

**扩容过程**：
1. 创建新数组，容量为原来的 1.5 倍
2. 使用 `System.arraycopy` 复制旧数据到新数组
3. 丢弃旧数组

**优化建议**：
```java
// 预估数据量，避免频繁扩容
ArrayList<String> list = new ArrayList<>(10000);
```

#### 随机访问为什么快？

```java
// 直接通过索引计算内存地址
public E get(int index) {
    rangeCheck(index);
    return elementData(index);  // O(1)
}

// 内存地址 = 数组起始地址 + index * 元素大小
```

数组在内存中是连续存储的，通过索引可直接计算出元素的内存地址。

### LinkedList 详解

#### 底层结构

```java
public class LinkedList<E> extends AbstractSequentialList<E>
        implements List<E>, Deque<E>, Cloneable, Serializable {
    
    // 链表长度
    transient int size = 0;
    
    // 头节点
    transient Node<E> first;
    
    // 尾节点
    transient Node<E> last;
    
    // 节点定义
    private static class Node<E> {
        E item;           // 数据
        Node<E> next;     // 后继节点
        Node<E> prev;     // 前驱节点
        
        Node(Node<E> prev, E element, Node<E> next) {
            this.item = element;
            this.next = next;
            this.prev = prev;
        }
    }
}
```

#### 插入操作

```java
// 在指定位置插入
public void add(int index, E element) {
    checkPositionIndex(index);
    
    if (index == size)
        linkLast(element);      // 尾部插入 O(1)
    else
        linkBefore(element, node(index));  // 中间插入 O(n)
}

// 找到指定位置的节点
Node<E> node(int index) {
    // 优化：从头部或尾部开始遍历
    if (index < (size >> 1)) {
        Node<E> x = first;
        for (int i = 0; i < index; i++)
            x = x.next;
        return x;
    } else {
        Node<E> x = last;
        for (int i = size - 1; i > index; i--)
            x = x.prev;
        return x;
    }
}
```

### 性能对比测试

```java
public class ListPerformanceTest {
    public static void main(String[] args) {
        int count = 100000;
        
        // 1. 随机访问测试
        ArrayList<Integer> arrayList = new ArrayList<>();
        LinkedList<Integer> linkedList = new LinkedList<>();
        
        for (int i = 0; i < count; i++) {
            arrayList.add(i);
            linkedList.add(i);
        }
        
        // ArrayList 随机访问
        long start1 = System.currentTimeMillis();
        for (int i = 0; i < count; i++) {
            arrayList.get(i);
        }
        System.out.println("ArrayList get: " + (System.currentTimeMillis() - start1) + "ms");
        
        // LinkedList 随机访问
        long start2 = System.currentTimeMillis();
        for (int i = 0; i < count; i++) {
            linkedList.get(i);
        }
        System.out.println("LinkedList get: " + (System.currentTimeMillis() - start2) + "ms");
        
        // 2. 头部插入测试
        ArrayList<Integer> arrayList2 = new ArrayList<>();
        LinkedList<Integer> linkedList2 = new LinkedList<>();
        
        long start3 = System.currentTimeMillis();
        for (int i = 0; i < 10000; i++) {
            arrayList2.add(0, i);  // 头部插入
        }
        System.out.println("ArrayList add(0): " + (System.currentTimeMillis() - start3) + "ms");
        
        long start4 = System.currentTimeMillis();
        for (int i = 0; i < 10000; i++) {
            linkedList2.addFirst(i);  // 头部插入
        }
        System.out.println("LinkedList addFirst: " + (System.currentTimeMillis() - start4) + "ms");
    }
}
```

**典型结果**：
```
ArrayList get: 5ms
LinkedList get: 8000ms+  （慢 1000+ 倍）

ArrayList add(0): 500ms
LinkedList addFirst: 5ms  （快 100 倍）
```

### 使用场景

| 场景 | 推荐 | 原因 |
|------|------|------|
| 频繁随机访问 | ArrayList | O(1) 访问速度 |
| 频繁在头部/中间插入删除 | LinkedList | O(1) 插入删除 |
| 只需要在尾部添加 | ArrayList | 缓存友好，内存占用少 |
| 实现队列/栈 | LinkedList | 已实现 Deque 接口 |
| 数据量固定 | ArrayList | 内存连续，性能好 |

### 线程安全问题

两者都是线程不安全的，多线程环境下需要：

```java
// 方式1：使用 Collections.synchronizedList
List<String> syncList = Collections.synchronizedList(new ArrayList<>());

// 方式2：使用 CopyOnWriteArrayList（读多写少场景）
List<String> cowList = new CopyOnWriteArrayList<>();

// 方式3：使用 Vector（已过时，不推荐）
List<String> vector = new Vector<>();
```

### 高频面试题

**Q1: 为什么 ArrayList 扩容是 1.5 倍而不是 2 倍？**

- 1.5 倍是空间和时间折中的结果
- 2 倍扩容可能导致内存浪费
- 1.5 倍在扩容频率和内存占用之间取得平衡

**Q2: LinkedList 实现了哪些接口？**

```java
public class LinkedList<E> extends AbstractSequentialList<E>
        implements List<E>, Deque<E>, Cloneable, Serializable
```

实现了 `Deque` 接口，可以作为队列（FIFO）或栈（LIFO）使用：

```java
// 作为队列使用
Queue<String> queue = new LinkedList<>();
queue.offer("A");
String item = queue.poll();

// 作为栈使用
Deque<String> stack = new LinkedList<>();
stack.push("A");
String top = stack.pop();
```

**Q3: ArrayList 的 trimToSize() 方法有什么用？**

```java
ArrayList<String> list = new ArrayList<>(100);
list.add("A");
list.add("B");
// 当前 elementData.length = 100，但 size = 2

list.trimToSize();  // 将 elementData 缩容到 size 大小
// elementData.length = 2
```

用于释放未使用的数组空间。

**Q4: 遍历 List 时删除元素的正确方式？**

```java
// 错误方式：会抛出 ConcurrentModificationException
for (String s : list) {
    if (s.equals("A")) list.remove(s);
}

// 正确方式1：使用迭代器
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (it.next().equals("A")) {
        it.remove();  // 使用迭代器的 remove 方法
    }
}

// 正确方式2：倒序遍历（只适用于 ArrayList）
for (int i = list.size() - 1; i >= 0; i--) {
    if (list.get(i).equals("A")) {
        list.remove(i);
    }
}

// 正确方式3：Java 8+ removeIf
list.removeIf(s -> s.equals("A"));
```

---

**参考链接：**
- [ArrayList和LinkedList区别-PHP中文网](https://m.php.cn/faq/1282994.html)
- [ArrayList和LinkedList的区别-博客园](https://www.cnblogs.com/wztblogs/p/16587339.html)
