---
layout: default
title: 栈与队列高频面试题精讲 ⭐⭐⭐
---

# 栈与队列高频面试题精讲 ⭐⭐⭐

## 🎯 面试核心

栈和队列是最基础的数据结构，也是面试的必考题。掌握栈和队列的特性、常见操作和高频题目，对理解递归、BFS、DFS 等算法也很有帮助。

---

## 一、栈高频面试题

### 1. 最小栈（LeetCode 155）

**问题描述**

设计一个栈，支持 push、pop、top 操作，同时能在 O(1) 时间内获取栈中的最小值。

```
MinStack stack = new MinStack();
stack.push(-2);
stack.push(0);
stack.push(-3);
stack.getMin();  // 返回 -3
stack.pop();
stack.top();     // 返回 0
stack.getMin();  // 返回 -2
```

**思路分析**

- 使用两个栈：一个存储所有元素，一个存储最小值
- 每次 push 时，同时更新最小值栈
- 每次 pop 时，同时弹出最小值栈

**Java 代码**

```java
class MinStack {
    private Stack<Integer> stack;
    private Stack<Integer> minStack;  // 存储最小值
    
    public MinStack() {
        stack = new Stack<>();
        minStack = new Stack<>();
    }
    
    /**
     * 压入元素
     */
    public void push(int val) {
        stack.push(val);
        
        // 最小值栈：如果为空或新元素 <= 栈顶最小值，则压入
        if (minStack.isEmpty() || val <= minStack.peek()) {
            minStack.push(val);
        }
    }
    
    /**
     * 弹出元素
     */
    public void pop() {
        int val = stack.pop();
        
        // 如果弹出的是最小值，也从最小值栈中弹出
        if (val == minStack.peek()) {
            minStack.pop();
        }
    }
    
    /**
     * 获取栈顶元素
     */
    public int top() {
        return stack.peek();
    }
    
    /**
     * 获取最小值，O(1)
     */
    public int getMin() {
        return minStack.peek();
    }
}
```

**复杂度分析**

- 时间复杂度：push O(1)，pop O(1)，top O(1)，getMin O(1)
- 空间复杂度：O(N)

---

### 2. 单调栈 - Next Greater Element（LeetCode 496）

**问题描述**

给定一个数组，对于每个元素，找出右边第一个比它大的元素。

```
输入：nums = [1, 2]
输出：[2, -1]
解释：1 的右边第一个更大的元素是 2，2 没有更大的元素

输入：nums = [1, 2, 1]
输出：[2, -1, -1]
```

**思路分析**

- **暴力法**：O(N²)，对每个元素向右扫描
- **单调栈**：O(N)，栈中存储下标，从右向左遍历
  - 栈中元素从底到顶递减
  - 当遇到比栈顶大的元素时，栈顶的答案就是这个元素

**Java 代码**

```java
public int[] nextGreaterElement(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    Arrays.fill(result, -1);
    
    // 栈中存储下标
    Stack<Integer> stack = new Stack<>();
    
    // 从右向左遍历
    for (int i = n - 1; i >= 0; i--) {
        // 弹出所有小于等于当前元素的元素
        while (!stack.isEmpty() && nums[stack.peek()] <= nums[i]) {
            stack.pop();
        }
        
        // 栈顶就是答案
        if (!stack.isEmpty()) {
            result[i] = nums[stack.peek()];
        }
        
        // 当前元素入栈
        stack.push(i);
    }
    
    return result;
}
```

**复杂度分析**

- 时间复杂度：O(N)，每个元素最多入栈和出栈一次
- 空间复杂度：O(N)，栈的空间

---

### 3. 括号匹配（LeetCode 20）

**问题描述**

给定一个只包含括号的字符串，判断括号是否匹配。

```
输入："()"
输出：true

输入："([{}])"
输出：true

输入："([)]"
输出：false
```

**思路分析**

- 使用栈存储左括号
- 遇到右括号时，检查栈顶是否匹配
- 最后栈应该为空

**Java 代码**

```java
public boolean isValid(String s) {
    Stack<Character> stack = new Stack<>();
    
    for (char c : s.toCharArray()) {
        if (c == '(' || c == '[' || c == '{') {
            // 左括号入栈
            stack.push(c);
        } else {
            // 右括号
            if (stack.isEmpty()) {
                return false;  // 没有匹配的左括号
            }
            
            char top = stack.pop();
            
            // 检查是否匹配
            if ((c == ')' && top != '(') ||
                (c == ']' && top != '[') ||
                (c == '}' && top != '{')) {
                return false;
            }
        }
    }
    
    // 栈应该为空
    return stack.isEmpty();
}
```

**复杂度分析**

- 时间复杂度：O(N)，遍历一遍字符串
- 空间复杂度：O(N)，栈的空间

---

## 二、队列高频面试题

### 4. 滑动窗口最大值（LeetCode 239）

**问题描述**

给定一个数组和窗口大小 k，找出每个窗口的最大值。

```
输入：nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
输出：[3, 3, 5, 5, 6, 7]

解释：
窗口 [1, 3, -1]，最大值 3
窗口 [3, -1, -3]，最大值 3
窗口 [-1, -3, 5]，最大值 5
...
```

**思路分析**

- **暴力法**：O(N * K)，对每个窗口找最大值
- **单调队列**：O(N)，队列中存储下标，从大到小排序
  - 队列前端是当前窗口的最大值
  - 移动窗口时，删除过期元素，添加新元素

**Java 代码**

```java
public int[] maxSlidingWindow(int[] nums, int k) {
    if (nums == null || nums.length == 0) {
        return new int[0];
    }
    
    int n = nums.length;
    int[] result = new int[n - k + 1];
    
    // 单调队列：存储下标，从大到小排序
    Deque<Integer> deque = new LinkedList<>();
    
    for (int i = 0; i < n; i++) {
        // 删除过期元素（超出窗口范围）
        if (!deque.isEmpty() && deque.peekFirst() < i - k + 1) {
            deque.pollFirst();
        }
        
        // 删除所有小于当前元素的元素
        while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) {
            deque.pollLast();
        }
        
        // 当前元素入队
        deque.addLast(i);
        
        // 当窗口形成时，记录最大值
        if (i >= k - 1) {
            result[i - k + 1] = nums[deque.peekFirst()];
        }
    }
    
    return result;
}
```

**复杂度分析**

- 时间复杂度：O(N)，每个元素最多入队和出队一次
- 空间复杂度：O(K)，队列的空间

---

### 5. 设计阻塞队列（LeetCode 1188）

**问题描述**

设计一个阻塞队列，支持以下操作：
- enqueue(value)：如果队列未满，添加元素；否则阻塞
- dequeue()：如果队列非空，移除元素；否则阻塞
- size()：返回队列大小

**思路分析**

- 使用 LinkedList 作为底层存储
- 使用 ReentrantLock 和 Condition 实现同步
- 两个 Condition：notFull（队列未满）和 notEmpty（队列非空）

**Java 代码**

```java
class BlockingQueue {
    private Queue<Integer> queue;
    private int capacity;
    private ReentrantLock lock;
    private Condition notFull;
    private Condition notEmpty;
    
    public BlockingQueue(int capacity) {
        this.queue = new LinkedList<>();
        this.capacity = capacity;
        this.lock = new ReentrantLock();
        this.notFull = lock.newCondition();
        this.notEmpty = lock.newCondition();
    }
    
    /**
     * 添加元素，如果队列满则阻塞
     */
    public void enqueue(int value) throws InterruptedException {
        lock.lock();
        try {
            // 等待队列未满
            while (queue.size() == capacity) {
                notFull.await();
            }
            
            // 添加元素
            queue.offer(value);
            
            // 唤醒等待的消费者
            notEmpty.signalAll();
        } finally {
            lock.unlock();
        }
    }
    
    /**
     * 移除元素，如果队列空则阻塞
     */
    public int dequeue() throws InterruptedException {
        lock.lock();
        try {
            // 等待队列非空
            while (queue.isEmpty()) {
                notEmpty.await();
            }
            
            // 移除元素
            int value = queue.poll();
            
            // 唤醒等待的生产者
            notFull.signalAll();
            
            return value;
        } finally {
            lock.unlock();
        }
    }
    
    /**
     * 获取队列大小
     */
    public int size() {
        lock.lock();
        try {
            return queue.size();
        } finally {
            lock.unlock();
        }
    }
}
```

**复杂度分析**

- 时间复杂度：enqueue O(1)，dequeue O(1)，size O(1)
- 空间复杂度：O(capacity)

---

## 三、栈和队列的相互实现

### 6. 两个栈实现队列（LeetCode 232）

**问题描述**

使用两个栈实现一个队列。

**思路分析**

- 栈 1（inStack）：用于入队
- 栈 2（outStack）：用于出队
- 出队时，如果 outStack 为空，将 inStack 的所有元素转移到 outStack

**Java 代码**

```java
class QueueUsingStacks {
    private Stack<Integer> inStack;
    private Stack<Integer> outStack;
    
    public QueueUsingStacks() {
        inStack = new Stack<>();
        outStack = new Stack<>();
    }
    
    /**
     * 入队
     */
    public void push(int x) {
        inStack.push(x);
    }
    
    /**
     * 出队
     */
    public int pop() {
        if (outStack.isEmpty()) {
            // 将 inStack 的所有元素转移到 outStack
            while (!inStack.isEmpty()) {
                outStack.push(inStack.pop());
            }
        }
        
        return outStack.pop();
    }
    
    /**
     * 获取队首元素
     */
    public int peek() {
        if (outStack.isEmpty()) {
            while (!inStack.isEmpty()) {
                outStack.push(inStack.pop());
            }
        }
        
        return outStack.peek();
    }
    
    /**
     * 判断队列是否为空
     */
    public boolean empty() {
        return inStack.isEmpty() && outStack.isEmpty();
    }
}
```

**复杂度分析**

- 时间复杂度：push O(1)，pop O(1)（均摊），peek O(1)（均摊）
- 空间复杂度：O(N)

---

### 7. 两个队列实现栈（LeetCode 225）

**问题描述**

使用两个队列实现一个栈。

**思路分析**

- 队列 1（mainQueue）：存储栈的元素
- 队列 2（tempQueue）：临时队列
- 压栈时，先将 mainQueue 的元素转移到 tempQueue，再将新元素加入 mainQueue，最后将 tempQueue 的元素转移回 mainQueue

**Java 代码**

```java
class StackUsingQueues {
    private Queue<Integer> mainQueue;
    private Queue<Integer> tempQueue;
    
    public StackUsingQueues() {
        mainQueue = new LinkedList<>();
        tempQueue = new LinkedList<>();
    }
    
    /**
     * 压栈
     */
    public void push(int x) {
        // 将 mainQueue 的元素转移到 tempQueue
        while (!mainQueue.isEmpty()) {
            tempQueue.offer(mainQueue.poll());
        }
        
        // 新元素加入 mainQueue
        mainQueue.offer(x);
        
        // 将 tempQueue 的元素转移回 mainQueue
        while (!tempQueue.isEmpty()) {
            mainQueue.offer(tempQueue.poll());
        }
    }
    
    /**
     * 弹栈
     */
    public int pop() {
        return mainQueue.poll();
    }
    
    /**
     * 获取栈顶元素
     */
    public int top() {
        return mainQueue.peek();
    }
    
    /**
     * 判断栈是否为空
     */
    public boolean empty() {
        return mainQueue.isEmpty();
    }
}
```

**复杂度分析**

- 时间复杂度：push O(N)，pop O(1)，top O(1)
- 空间复杂度：O(N)

---

## 四、优先队列（堆）

### 8. PriorityQueue 基础

**Java 代码**

```java
/**
 * 最小堆（默认）
 */
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
minHeap.offer(3);
minHeap.offer(1);
minHeap.offer(2);
System.out.println(minHeap.poll());  // 1
System.out.println(minHeap.poll());  // 2
System.out.println(minHeap.poll());  // 3

/**
 * 最大堆（自定义比较器）
 */
PriorityQueue<Integer> maxHeap = new PriorityQueue<>((a, b) -> b - a);
maxHeap.offer(3);
maxHeap.offer(1);
maxHeap.offer(2);
System.out.println(maxHeap.poll());  // 3
System.out.println(maxHeap.poll());  // 2
System.out.println(maxHeap.poll());  // 1

/**
 * 自定义对象的优先队列
 */
class Person {
    String name;
    int age;
    
    Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
}

PriorityQueue<Person> pq = new PriorityQueue<>(
    (a, b) -> a.age - b.age  // 按年龄升序
);
pq.offer(new Person("Alice", 30));
pq.offer(new Person("Bob", 25));
pq.offer(new Person("Charlie", 35));

while (!pq.isEmpty()) {
    Person p = pq.poll();
    System.out.println(p.name + ": " + p.age);
}
// 输出：Bob: 25, Alice: 30, Charlie: 35
```

**复杂度分析**

- offer O(log N)，poll O(log N)，peek O(1)

---

## 五、高频面试题总结

| 题目 | 难度 | 关键点 | 时间复杂度 |
|------|------|--------|-----------|
| 最小栈 | ⭐ | 两个栈 | O(1) |
| Next Greater Element | ⭐⭐ | 单调栈 | O(N) |
| 括号匹配 | ⭐ | 栈 | O(N) |
| 滑动窗口最大值 | ⭐⭐ | 单调队列 | O(N) |
| 阻塞队列 | ⭐⭐ | Lock + Condition | O(1) |
| 两个栈实现队列 | ⭐⭐ | 栈转移 | O(1) 均摊 |
| 两个队列实现栈 | ⭐⭐ | 队列转移 | O(N) |
| 优先队列 | ⭐⭐ | 堆 | O(log N) |

---

## 六、面试建议

1. **理解本质**：栈是 LIFO，队列是 FIFO
2. **单调栈/队列**：关键是维护单调性，用于找下一个更大/更小的元素
3. **同步问题**：使用 Lock + Condition 实现阻塞队列
4. **相互实现**：理解两种数据结构的转换
5. **优先队列**：掌握堆的基本操作
6. **代码规范**：边界条件、空指针检查
7. **扩展思考**：循环队列、双端队列等变种
