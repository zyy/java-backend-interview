---
layout: default
title: 数组与链表高频面试题精讲 ⭐⭐⭐
---

# 数组与链表高频面试题精讲 ⭐⭐⭐

## 🎯 面试核心

数组和链表是最基础的数据结构，也是面试的必考题。掌握这两种结构的特性、常见操作和高频题目，是进阶算法的基础。

---

## 一、数组高频面试题

### 1. 两数之和（LeetCode 1）

**问题描述**

给定一个整数数组 `nums` 和一个整数 `target`，找出数组中两个数之和等于 `target` 的下标，返回这两个下标。

```
输入：nums = [2, 7, 11, 15], target = 9
输出：[0, 1]
解释：nums[0] + nums[1] = 2 + 7 = 9
```

**思路分析**

- **暴力法**：两层循环，O(N²)，不推荐
- **哈希表法**：一遍扫描，记录已见数字，O(N) 时间，O(N) 空间，推荐
- **双指针法**：需要先排序，O(N log N)，适合有序数组

**Java 代码（哈希表）**

```java
public int[] twoSum(int[] nums, int target) {
    // key: 数值，value: 下标
    Map<Integer, Integer> map = new HashMap<>();
    
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        
        if (map.containsKey(complement)) {
            // 找到了！返回两个下标
            return new int[]{map.get(complement), i};
        }
        
        // 记录当前数值和下标
        map.put(nums[i], i);
    }
    
    return new int[]{};  // 无解
}
```

**复杂度分析**

- 时间复杂度：O(N)，一遍扫描
- 空间复杂度：O(N)，哈希表存储

---

### 2. 三数之和（LeetCode 15）

**问题描述**

给定一个数组 `nums`，找出所有满足 `nums[i] + nums[j] + nums[k] = 0` 的三元组，且不重复。

```
输入：nums = [-1, 0, 1, 2, -1, -4]
输出：[[-1, -1, 2], [-1, 0, 1]]
```

**思路分析**

- 先排序，然后固定一个数，用双指针找另外两个数
- 关键：去重处理（跳过重复元素）
- 时间复杂度：O(N²)

**Java 代码**

```java
public List<List<Integer>> threeSum(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    
    if (nums == null || nums.length < 3) {
        return result;
    }
    
    // 第一步：排序
    Arrays.sort(nums);
    
    for (int i = 0; i < nums.length - 2; i++) {
        // 优化：如果当前数 > 0，后续不可能有和为 0 的三元组
        if (nums[i] > 0) break;
        
        // 去重：跳过重复的第一个数
        if (i > 0 && nums[i] == nums[i - 1]) continue;
        
        // 双指针找另外两个数
        int left = i + 1;
        int right = nums.length - 1;
        int target = -nums[i];
        
        while (left < right) {
            int sum = nums[left] + nums[right];
            
            if (sum == target) {
                result.add(Arrays.asList(nums[i], nums[left], nums[right]));
                
                // 去重：跳过重复的第二个数
                while (left < right && nums[left] == nums[left + 1]) left++;
                // 去重：跳过重复的第三个数
                while (left < right && nums[right] == nums[right - 1]) right--;
                
                left++;
                right--;
            } else if (sum < target) {
                left++;
            } else {
                right--;
            }
        }
    }
    
    return result;
}
```

**复杂度分析**

- 时间复杂度：O(N²)，排序 O(N log N) + 双指针 O(N²)
- 空间复杂度：O(1)，不计结果空间

---

### 3. 最长连续序列（LeetCode 128）

**问题描述**

给定一个未排序的整数数组，找出最长连续元素序列的长度。

```
输入：nums = [100, 4, 200, 1, 3, 2]
输出：4
解释：最长连续序列是 [1, 2, 3, 4]，长度为 4
```

**思路分析**

- 暴力排序：O(N log N)，不是最优
- **哈希集合**：O(N)，关键是只从序列的起点开始计数
  - 如果 `num - 1` 不在集合中，说明 `num` 是序列的起点
  - 从起点开始计数，找最长连续序列

**Java 代码**

```java
public int longestConsecutive(int[] nums) {
    if (nums == null || nums.length == 0) {
        return 0;
    }
    
    // 转换为 HashSet，O(1) 查询
    Set<Integer> numSet = new HashSet<>();
    for (int num : nums) {
        numSet.add(num);
    }
    
    int maxLength = 0;
    
    for (int num : numSet) {
        // 只从序列的起点开始计数
        if (!numSet.contains(num - 1)) {
            int currentNum = num;
            int currentLength = 1;
            
            // 向后计数
            while (numSet.contains(currentNum + 1)) {
                currentNum++;
                currentLength++;
            }
            
            maxLength = Math.max(maxLength, currentLength);
        }
    }
    
    return maxLength;
}
```

**复杂度分析**

- 时间复杂度：O(N)，虽然有嵌套循环，但每个数最多被访问两次
- 空间复杂度：O(N)，哈希集合

---

### 4. 合并区间（LeetCode 56）

**问题描述**

给定一个区间列表，合并所有重叠的区间。

```
输入：intervals = [[1,3],[2,6],[8,10],[15,18]]
输出：[[1,6],[8,10],[15,18]]
```

**思路分析**

- 先按起点排序
- 遍历区间，如果当前区间与前一个区间重叠，则合并
- 重叠判断：`current.start <= prev.end`

**Java 代码**

```java
public int[][] merge(int[][] intervals) {
    if (intervals == null || intervals.length == 0) {
        return new int[0][0];
    }
    
    // 按起点排序
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]);
    
    List<int[]> merged = new ArrayList<>();
    int[] current = intervals[0];
    
    for (int i = 1; i < intervals.length; i++) {
        if (intervals[i][0] <= current[1]) {
            // 重叠，合并
            current[1] = Math.max(current[1], intervals[i][1]);
        } else {
            // 不重叠，保存当前区间，开始新区间
            merged.add(current);
            current = intervals[i];
        }
    }
    
    // 别忘了最后一个区间
    merged.add(current);
    
    return merged.toArray(new int[0][0]);
}
```

**复杂度分析**

- 时间复杂度：O(N log N)，排序主导
- 空间复杂度：O(1)，不计结果空间

---

## 二、链表高频面试题

### 5. 反转链表（LeetCode 206）

**问题描述**

反转一个单链表。

```
输入：1 -> 2 -> 3 -> 4 -> 5
输出：5 -> 4 -> 3 -> 2 -> 1
```

**思路分析**

- **迭代法**：三指针（prev, curr, next），逐个反转指针方向
- **递归法**：到达链表末尾，然后逐层反转

**Java 代码（迭代法）**

```java
public ListNode reverseList(ListNode head) {
    ListNode prev = null;
    ListNode curr = head;
    
    while (curr != null) {
        // 保存下一个节点
        ListNode next = curr.next;
        
        // 反转指针
        curr.next = prev;
        
        // 前移指针
        prev = curr;
        curr = next;
    }
    
    return prev;  // 新的头节点
}

// 链表节点定义
class ListNode {
    int val;
    ListNode next;
    ListNode(int x) { val = x; }
}
```

**Java 代码（递归法）**

```java
public ListNode reverseListRecursive(ListNode head) {
    // 递归终止条件
    if (head == null || head.next == null) {
        return head;
    }
    
    // 递归反转后续链表
    ListNode newHead = reverseListRecursive(head.next);
    
    // 反转当前节点
    head.next.next = head;
    head.next = null;
    
    return newHead;
}
```

**复杂度分析**

- 时间复杂度：O(N)，遍历一遍链表
- 空间复杂度：迭代 O(1)，递归 O(N)（递归栈）

---

### 6. 合并有序链表（LeetCode 21）

**问题描述**

合并两个有序链表为一个有序链表。

```
输入：l1 = 1 -> 2 -> 4, l2 = 1 -> 3 -> 4
输出：1 -> 1 -> 2 -> 3 -> 4 -> 4
```

**思路分析**

- 使用虚拟头节点简化代码
- 双指针比较两个链表的节点，小的先连接
- 最后连接剩余部分

**Java 代码**

```java
public ListNode mergeTwoLists(ListNode l1, ListNode l2) {
    // 虚拟头节点
    ListNode dummy = new ListNode(0);
    ListNode curr = dummy;
    
    while (l1 != null && l2 != null) {
        if (l1.val <= l2.val) {
            curr.next = l1;
            l1 = l1.next;
        } else {
            curr.next = l2;
            l2 = l2.next;
        }
        curr = curr.next;
    }
    
    // 连接剩余部分
    curr.next = (l1 != null) ? l1 : l2;
    
    return dummy.next;
}
```

**复杂度分析**

- 时间复杂度：O(N + M)，N 和 M 分别是两个链表的长度
- 空间复杂度：O(1)，只使用常数空间

---

### 7. 链表环检测（LeetCode 141 & 142）

**问题描述**

检测链表中是否存在环，如果存在，找出环的入口。

**思路分析**

- **Floyd 算法（龟兔赛跑）**：
  - 快指针每次走 2 步，慢指针每次走 1 步
  - 如果有环，快慢指针必定相遇
  - 相遇后，一个指针从头开始，另一个从相遇点开始，每次走 1 步，再次相遇点就是环入口

**Java 代码**

```java
// 检测是否有环
public boolean hasCycle(ListNode head) {
    if (head == null || head.next == null) {
        return false;
    }
    
    ListNode slow = head;
    ListNode fast = head;
    
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        
        if (slow == fast) {
            return true;  // 有环
        }
    }
    
    return false;  // 无环
}

// 找环的入口
public ListNode detectCycle(ListNode head) {
    if (head == null || head.next == null) {
        return null;
    }
    
    ListNode slow = head;
    ListNode fast = head;
    
    // 第一步：检测是否有环
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        
        if (slow == fast) {
            // 有环，进入第二步
            break;
        }
    }
    
    // 如果没有环
    if (fast == null || fast.next == null) {
        return null;
    }
    
    // 第二步：找环入口
    ListNode ptr1 = head;
    ListNode ptr2 = slow;
    
    while (ptr1 != ptr2) {
        ptr1 = ptr1.next;
        ptr2 = ptr2.next;
    }
    
    return ptr1;  // 环入口
}
```

**复杂度分析**

- 时间复杂度：O(N)，最多遍历链表两次
- 空间复杂度：O(1)，只使用指针

---

### 8. 相交链表（LeetCode 160）

**问题描述**

给定两个链表，找出它们的相交节点。

```
链表 A：a1 -> a2 -> c1 -> c2 -> c3
链表 B：b1 -> b2 -> b3 -> c1 -> c2 -> c3
相交节点：c1
```

**思路分析**

- **双指针法**：
  - 指针 A 遍历链表 A，到达末尾后转向链表 B
  - 指针 B 遍历链表 B，到达末尾后转向链表 A
  - 如果两个链表相交，指针最终会在相交节点相遇
  - 如果不相交，两个指针都会到达 null

**Java 代码**

```java
public ListNode getIntersectionNode(ListNode headA, ListNode headB) {
    if (headA == null || headB == null) {
        return null;
    }
    
    ListNode pA = headA;
    ListNode pB = headB;
    
    // 两个指针同时遍历
    while (pA != pB) {
        // pA 到达末尾后，转向 headB
        pA = (pA == null) ? headB : pA.next;
        
        // pB 到达末尾后，转向 headA
        pB = (pB == null) ? headA : pB.next;
    }
    
    return pA;  // 相交节点或 null
}
```

**复杂度分析**

- 时间复杂度：O(N + M)，N 和 M 分别是两个链表的长度
- 空间复杂度：O(1)，只使用指针

---

## 三、高频面试题总结

| 题目 | 难度 | 关键点 | 时间复杂度 |
|------|------|--------|-----------|
| 两数之和 | ⭐ | 哈希表 | O(N) |
| 三数之和 | ⭐⭐ | 排序 + 双指针 + 去重 | O(N²) |
| 最长连续序列 | ⭐⭐ | 哈希集合 + 起点判断 | O(N) |
| 合并区间 | ⭐⭐ | 排序 + 贪心 | O(N log N) |
| 反转链表 | ⭐ | 指针反转 | O(N) |
| 合并有序链表 | ⭐ | 虚拟头节点 | O(N + M) |
| 链表环检测 | ⭐⭐ | Floyd 算法 | O(N) |
| 相交链表 | ⭐⭐ | 双指针 | O(N + M) |

---

## 四、面试建议

1. **数组**：掌握哈希表、双指针、排序等基础技巧
2. **链表**：熟练使用虚拟头节点、快慢指针等技巧
3. **代码规范**：边界条件、空指针检查、变量命名
4. **时间复杂度**：优先选择 O(N) 或 O(N log N) 的解法
5. **多做练习**：LeetCode 上反复练习，形成肌肉记忆
