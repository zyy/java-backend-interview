---
layout: default
title: 剑指 Offer 高频面试题精讲 ⭐⭐⭐
---

# 剑指 Offer 高频面试题精讲 ⭐⭐⭐

> 剑指 Offer 系列是面试算法中的"常考题库"，涵盖数组、链表、树、栈队列、动态规划、字符串、搜索等核心题型。本文档精选面试中出现频率最高的题目，每道题均包含 **问题描述 → 思路分析 → 代码实现（Java/Python） → 复杂度分析**，帮助你高效备战面试。

---

## 一、数组类

### 1. 两数之和（LeetCode 1）⭐⭐⭐

**问题描述**

> 给定一个整数数组 `nums` 和一个整数 `target`，请你在数组中找出 **和为目标值** 的两个整数，返回它们的 **下标**。假设每种输入只会对应一个答案，且同样的元素不能被重复利用。

**思路分析**

- **暴力法**：双层 for 循环，时间复杂度 O(n²)，面试不推荐。
- **哈希表法（推荐）**：遍历数组时，用 HashMap 记录 `值 → 下标`。对于每个元素 `nums[i]`，检查 `target - nums[i]` 是否已在哈希表中。边存边查，一遍搞定。
- **关键点**：`map.get()` 的索引一定要小于当前索引，避免重复利用同一元素。

**Java 实现**

```java
import java.util.*;

public class TwoSum {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[]{map.get(complement), i};
            }
            map.put(nums[i], i);
        }
        throw new IllegalArgumentException("No two sum solution");
    }
}
```

**Python 实现**

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    raise ValueError("No two sum solution")
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，遍历数组一次 |
| 空间复杂度 | **O(n)**，最坏情况下哈希表存储 n 个元素 |

---

### 2. 三数之和（LeetCode 15）⭐⭐⭐

**问题描述**

> 给你一个整数数组 `nums`，判断是否存在三元组 `[nums[a], nums[b], nums[c]]` 满足 `a、b、c` 均互不相同且 `nums[a] + nums[b] + nums[c] == 0`。返回所有满足条件的三元组，顺序不限。

**思路分析**

- 先对数组排序（升序），固定第一个数 `nums[i]`，然后用 **双指针** 在 `[i+1, n-1]` 范围内找另外两个数。
- 若 `nums[i] > 0`，由于数组升序，三数之和必大于 0，直接 break。
- 去重：若 `nums[i] == nums[i-1]`，跳过，避免重复结果。
- 双指针：若和 > 0，右指针左移；若和 < 0，左指针右移；若和 == 0，记录结果并同时移动左右指针（跳过重复值）。

**Java 实现**

```java
import java.util.*;

public class ThreeSum {
    public List<List<Integer>> threeSum(int[] nums) {
        Arrays.sort(nums);
        List<List<Integer>> result = new ArrayList<>();

        for (int i = 0; i < nums.length - 2; i++) {
            if (nums[i] > 0) break;  // 最小值已为正，不可能和为0
            if (i > 0 && nums[i] == nums[i - 1]) continue;  // 去重

            int left = i + 1;
            int right = nums.length - 1;

            while (left < right) {
                int sum = nums[i] + nums[left] + nums[right];
                if (sum == 0) {
                    result.add(Arrays.asList(nums[i], nums[left], nums[right]));
                    // 跳过重复元素
                    while (left < right && nums[left] == nums[left + 1]) left++;
                    while (left < right && nums[right] == nums[right - 1]) right--;
                    left++;
                    right--;
                } else if (sum < 0) {
                    left++;
                } else {
                    right--;
                }
            }
        }
        return result;
    }
}
```

**Python 实现**

```python
def three_sum(nums: list[int]) -> list[list[int]]:
    nums.sort()
    n = len(nums)
    result = []

    for i in range(n - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue

        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n²)**，排序 O(n log n) + 双指针遍历 O(n²) |
| 空间复杂度 | **O(1)**（不计结果存储） |

---

### 3. 接雨水（LeetCode 42）⭐⭐⭐

**问题描述**

> 给定 `n` 个非负整数表示宽度为 1 的柱子的高度图，计算按此排列之后能接多少雨水。

```
输入: [0,1,0,2,1,0,1,3,2,1,2,1]
输出: 6（蓝色部分为接住的雨水）
```

**思路分析**

- **按列计算**：每个位置能接的水 = `min(左边最高柱子, 右边最高柱子) - 当前柱子高度`。
- **双指针优化**：用双指针从两端向中间收缩，维护 `leftMax` 和 `rightMax`。哪边小就处理哪边，避免 O(n) 的额外空间。
- **核心思想**：木桶原理 — 一个位置能装多少水，由它左右两侧较短的木板决定。

**Java 实现**

```java
public class TrapRainWater {
    public int trap(int[] height) {
        int left = 0, right = height.length - 1;
        int leftMax = 0, rightMax = 0;
        int result = 0;

        while (left < right) {
            if (height[left] <= height[right]) {
                leftMax = Math.max(leftMax, height[left]);
                result += leftMax - height[left];
                left++;
            } else {
                rightMax = Math.max(rightMax, height[right]);
                result += rightMax - height[right];
                right--;
            }
        }
        return result;
    }
}
```

**Python 实现**

```python
def trap(height: list[int]) -> int:
    left, right = 0, len(height) - 1
    left_max, right_max = 0, 0
    result = 0

    while left < right:
        if height[left] <= height[right]:
            left_max = max(left_max, height[left])
            result += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            result += right_max - height[right]
            right -= 1
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，双指针只遍历一遍 |
| 空间复杂度 | **O(1)**，原地计算 |

---

## 二、链表类

### 4. 反转链表（LeetCode 206）⭐⭐⭐

**问题描述**

> 给你单链表的头节点 `head`，反转链表并返回反转后的头节点。

**思路分析**

- **迭代法**：三个指针 `prev`、`curr`、`next`。每次让 `curr.next = prev` 实现反转，然后三者同步前移。`prev` 最终指向新头。
- **递归法**：递归到链表末端，以子链表反转结果为新头，逐层修正指针。时间复杂度相同，递归深度为 O(n)。
- **面试建议**：迭代法更直观、更安全（避免栈溢出）。

**Java 实现（迭代）**

```java
public class ReverseList {
    public ListNode reverseList(ListNode head) {
        ListNode prev = null;
        ListNode curr = head;

        while (curr != null) {
            ListNode next = curr.next;  // 1. 保存下一个节点
            curr.next = prev;            // 2. 反转当前节点指针
            prev = curr;                 // 3. prev 前移
            curr = next;                 // 4. curr 前移
        }
        return prev;  // prev 即新的头节点
    }

    // 递归版本
    public ListNode reverseListRecursive(ListNode head) {
        if (head == null || head.next == null) {
            return head;
        }
        ListNode newHead = reverseListRecursive(head.next);
        head.next.next = head;
        head.next = null;
        return newHead;
    }

    class ListNode {
        int val;
        ListNode next;
        ListNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

def reverse_list(head: ListNode) -> ListNode:
    prev, curr = None, head
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，遍历链表一次 |
| 空间复杂度 | **O(1)**（迭代）/ **O(n)**（递归，调用栈） |

---

### 5. 合并两个有序链表（LeetCode 21）⭐⭐⭐

**问题描述**

> 将两个升序链表合并为一个新的升序链表并返回。新链表通过拼接给定两个链表的节点组成。

**思路分析**

- 使用 **虚拟头节点（dummy）** 简化边界处理，避免单独处理头节点。
- 同时遍历两个链表，每次取较小者接入结果链表。
- 其中一个链表遍历完后，直接将另一个链表的剩余部分接入。

**Java 实现**

```java
public class MergeTwoLists {
    public ListNode mergeTwoLists(ListNode l1, ListNode l2) {
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

        // 处理剩余部分
        curr.next = (l1 != null) ? l1 : l2;
        return dummy.next;
    }

    class ListNode {
        int val;
        ListNode next;
        ListNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def merge_two_lists(l1: ListNode, l2: ListNode) -> ListNode:
    dummy = ListNode(0)
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    curr.next = l1 or l2
    return dummy.next
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(m + n)**，每个节点最多访问一次 |
| 空间复杂度 | **O(1)**，不计结果存储 |

---

### 6. 链表环入口（LeetCode 142）⭐⭐⭐

**问题描述**

> 给定一个链表，返回链表开始入环的第一个节点。如果链表无环，则返回 `null`。

**思路分析**

- **快慢指针（Floyd 判圈算法）**：
  1. 快指针每次走 2 步，慢指针每次走 1 步。若有环，两者必在环内某点相遇。
  2. 相遇后，将任一指针重置到头节点，两指针均改为每次走 1 步，再次相遇点即为环入口。
- **数学证明**：设环前长度为 F，环长度为 C。快慢指针相遇时，慢指针走了 F + a，快指针走了 F + a + nC，且快指针路程是慢指针的 2 倍 → F + a = nC → **F = nC - a = (n-1)C + (C-a)**。将指针重置到头后，走 F 步的路径与从相遇点走 (C-a) 步的路径等价。

**Java 实现**

```java
public class DetectCycle {
    public ListNode detectCycle(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;

        // 第一步：找相遇点
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                // 第二步：找环入口
                slow = head;
                while (slow != fast) {
                    slow = slow.next;
                    fast = fast.next;
                }
                return slow;
            }
        }
        return null;  // 无环
    }

    class ListNode {
        int val;
        ListNode next;
        ListNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def detect_cycle(head: ListNode) -> ListNode:
    slow = fast = head
    # 找相遇点
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # 找环入口
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，快慢指针最多走 n + n 步 |
| 空间复杂度 | **O(1)** |

---

### 7. 相交链表（LeetCode 160）⭐⭐⭐

**问题描述**

> 给你两个单链表的头节点 `headA` 和 `headB`，找出并返回两个链表相交的起始节点。如果两链表没有交点，返回 `null`。

**思路分析**

- **双指针法**：设链表 A 长度为 LA，链表 B 长度为 LB。
  - 指针 pA 从 A 出发，走完 A 后换到 B；指针 pB 从 B 出发，走完 B 后换到 A。
  - 两者走过总长度均为 LA + LB。若有交点，必在中间某点相遇；若无交点，最终两者同时走到 null。
- **优化**：也可以先计算长度差，让较长链表的指针先走差值步，再同步前进。

**Java 实现（双指针）**

```java
public class IntersectionNode {
    public ListNode getIntersectionNode(ListNode headA, ListNode headB) {
        if (headA == null || headB == null) return null;

        ListNode pA = headA;
        ListNode pB = headB;

        while (pA != pB) {
            pA = (pA == null) ? headB : pA.next;
            pB = (pB == null) ? headA : pB.next;
        }
        return pA;  // 相交点或 null
    }

    class ListNode {
        int val;
        ListNode next;
        ListNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def get_intersection_node(headA, headB):
    if not headA or not headB:
        return None
    pA, pB = headA, headB
    while pA != pB:
        pA = headB if not pA else pA.next
        pB = headA if not pB else pB.next
    return pA
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(m + n)** |
| 空间复杂度 | **O(1)** |

---

## 三、二叉树类

### 8. 二叉树前序遍历（非递归）⭐⭐⭐

**问题描述**

> 实现二叉树前序遍历（根-左-右）的非递归版本。

**思路分析**

- 前序遍历顺序：**根 → 左子树 → 右子树**。
- 非递归用 **显式栈** 模拟递归：
  1. 将根节点压栈。
  2. 循环：弹出栈顶节点，访问其值，再依次压入右子节点、左子节点（因为栈是 LIFO，左先出）。
  3. 栈空时遍历结束。

**Java 实现**

```java
import java.util.*;

public class PreorderTraversal {
    public List<Integer> preorderTraversal(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        if (root == null) return result;

        Stack<TreeNode> stack = new Stack<>();
        stack.push(root);

        while (!stack.isEmpty()) {
            TreeNode node = stack.pop();
            result.add(node.val);          // 访问根

            if (node.right != null) stack.push(node.right);  // 先压右
            if (node.left != null) stack.push(node.left);     // 后压左，左先出
        }
        return result;
    }

    class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def preorder_traversal(root: TreeNode) -> list[int]:
    if not root:
        return []
    result, stack = [], [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，每个节点访问一次 |
| 空间复杂度 | **O(h)**，h 为树高，最坏 O(n)（退化为链表） |

---

### 9. 二叉树中序遍历（非递归）⭐⭐⭐

**问题描述**

> 实现二叉树中序遍历（左-根-右）的非递归版本。

**思路分析**

- 中序遍历需要先遍历完左子树再访问根，所以用栈保存路径。
- 从根开始沿左子树一路压栈，直到左子节点为空。然后弹出栈顶访问，再转向右子树继续。

**Java 实现**

```java
import java.util.*;

public class InorderTraversal {
    public List<Integer> inorderTraversal(TreeNode root) {
        List<Integer> result = new ArrayList<>();
        Stack<TreeNode> stack = new Stack<>();
        TreeNode curr = root;

        while (curr != null || !stack.isEmpty()) {
            // 一路压入左子树
            while (curr != null) {
                stack.push(curr);
                curr = curr.left;
            }
            // 弹出并访问
            curr = stack.pop();
            result.add(curr.val);
            // 转向右子树
            curr = curr.right;
        }
        return result;
    }

    class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def inorder_traversal(root: TreeNode) -> list[int]:
    result, stack = [], []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)** |
| 空间复杂度 | **O(h)**，栈深度等于树高 |

---

### 10. 二叉树最大深度（LeetCode 104）⭐⭐⭐

**问题描述**

> 给定一个二叉树根节点，返回该树的最大深度（二叉树的层数）。

**思路分析**

- **递归法（推荐）**：最大深度 = `max(左子树深度, 右子树深度) + 1`。
- **层序迭代法**：用 BFS 逐层遍历，层数即为深度。维护一个队列，统计每层节点数。
- 面试中递归法是首选，简单直观，但要注意递归深度（树高）。

**Java 实现（递归）**

```java
public class MaxDepth {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return Math.max(maxDepth(root.left), maxDepth(root.right)) + 1;
    }

    // 层序迭代版本
    public int maxDepthBFS(TreeNode root) {
        if (root == null) return 0;
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int depth = 0;
        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            depth++;
        }
        return depth;
    }

    class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def max_depth(root: TreeNode) -> int:
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，每个节点访问一次 |
| 空间复杂度 | **O(h)** 递归栈，h 为树高 |

---

### 11. 对称二叉树（LeetCode 101）⭐⭐⭐

**问题描述**

> 给你一个二叉树的根节点 `root`，检查它是否是其镜像（即轴对称）。

```
    1
   / \
  2   2      ← 对称
 / \ / \
3  4 4  3
```

**思路分析**

- **递归法**：对称条件：左子树的左孩子 = 右子树的右孩子 且 左子树的右孩子 = 右子树的左孩子。
- **迭代法**：用队列（或双端队列）成对比较两个节点。

**Java 实现（递归）**

```java
public class SymmetricTree {
    public boolean isSymmetric(TreeNode root) {
        if (root == null) return true;
        return isMirror(root.left, root.right);
    }

    private boolean isMirror(TreeNode left, TreeNode right) {
        if (left == null && right == null) return true;
        if (left == null || right == null) return false;
        return (left.val == right.val)
            && isMirror(left.left, right.right)
            && isMirror(left.right, right.left);
    }

    class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
def is_symmetric(root: TreeNode) -> bool:
    def is_mirror(l: TreeNode, r: TreeNode) -> bool:
        if not l and not r:
            return True
        if not l or not r:
            return False
        return l.val == r.val and is_mirror(l.left, r.right) and is_mirror(l.right, r.left)
    return is_mirror(root.left, root.right) if root else True
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)** |
| 空间复杂度 | **O(h)** 递归栈 |

---

### 12. 二叉树层序遍历（LeetCode 102）⭐⭐⭐

**问题描述**

> 给你二叉树的根节点 `root`，返回其节点值的层序遍历（逐层从左到右访问）。

**思路分析**

- 使用 **BFS（广度优先搜索）**，配合队列实现。
- 关键技巧：**记录当前层节点数 `size = queue.size()`**，确保每层单独处理。
- 每层遍历前先记录当前队列大小，防止队列动态变化导致层数混淆。

**Java 实现**

```java
import java.util.*;

public class LevelOrder {
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);

        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();

            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);

                if (node.left != null) queue.offer(node.left);
                if (node.right != null) queue.offer(node.right);
            }
            result.add(level);
        }
        return result;
    }

    class TreeNode {
        int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int x) { val = x; }
    }
}
```

**Python 实现**

```python
from collections import deque

def level_order(root: TreeNode) -> list[list[int]]:
    if not root:
        return []
    result, queue = [], deque([root])
    while queue:
        size = len(queue)
        level = []
        for _ in range(size):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)** |
| 空间复杂度 | **O(n)**，最坏队列存储一层的所有节点 |

---

## 四、栈与队列类

### 13. 最小栈（LeetCode 155）⭐⭐⭐

**问题描述**

> 设计一个支持 push、pop、top 操作，且能在 **常数时间** 内检索到最小元素的栈。`getMin()` 应返回栈中的最小值。

**思路分析**

- **辅助栈法**：维护一个 `minStack`，每次 push 时如果新值 ≤ 当前最小值，则同时压入 `minStack`。
- 关键点：用 `<=` 而非 `<`，确保重复最小值也被记录，pop 时才不会丢失最小值。
- pop 时，如果弹出的值等于 minStack 栈顶，则 minStack 也同步弹出。
- `getMin()` 直接返回 minStack 栈顶，时间复杂度 O(1)。

**Java 实现**

```java
import java.util.Stack;

public class MinStack {
    private Stack<Integer> stack;
    private Stack<Integer> minStack;

    public MinStack() {
        stack = new Stack<>();
        minStack = new Stack<>();
    }

    public void push(int x) {
        stack.push(x);
        // 注意用 <= 确保重复最小值入栈
        if (minStack.isEmpty() || x <= minStack.peek()) {
            minStack.push(x);
        }
    }

    public void pop() {
        if (stack.isEmpty()) return;
        int top = stack.pop();
        if (top == minStack.peek()) {
            minStack.pop();
        }
    }

    public int top() {
        return stack.peek();
    }

    public int getMin() {
        return minStack.peek();
    }
}
```

**Python 实现**

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, x: int) -> None:
        self.stack.append(x)
        if not self.min_stack or x <= self.min_stack[-1]:
            self.min_stack.append(x)

    def pop(self) -> None:
        if self.stack:
            if self.stack[-1] == self.min_stack[-1]:
                self.min_stack.pop()
            self.stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]
```

**复杂度分析**

| 操作 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| push / pop / top / getMin | **O(1)** | **O(n)**（两个栈） |

---

### 14. 用栈实现队列（LeetCode 232）⭐⭐⭐

**问题描述**

> 请你仅使用两个栈实现先入先出队列。你需要实现 `MyQueue` 类：
> - `void push(int x)` 将元素 x 推到队列末尾
> - `int pop()` 从队列前方移除元素
> - `int peek()` 返回队列前方元素
> - `boolean empty()` 判断队列是否为空

**思路分析**

- **双栈模拟队列**：栈1（`stackIn`）负责入队，栈2（`stackOut`）负责出队。
- 入队直接压入 `stackIn`。
- 出队时：若 `stackOut` 非空，直接弹出；否则将 `stackIn` 所有元素逐一弹出压入 `stackOut`（倒序），再弹出。
- **摊还复杂度**：大部分操作是 O(1)，偶尔一次倒栈是 O(n)，但整体摊还仍是 O(1)。

**Java 实现**

```java
import java.util.Stack;

public class MyQueue {
    private Stack<Integer> stackIn;
    private Stack<Integer> stackOut;

    public MyQueue() {
        stackIn = new Stack<>();
        stackOut = new Stack<>();
    }

    public void push(int x) {
        stackIn.push(x);
    }

    public int pop() {
        if (stackOut.isEmpty()) {
            transfer();
        }
        return stackOut.isEmpty() ? -1 : stackOut.pop();
    }

    public int peek() {
        if (stackOut.isEmpty()) {
            transfer();
        }
        return stackOut.isEmpty() ? -1 : stackOut.peek();
    }

    public boolean empty() {
        return stackIn.isEmpty() && stackOut.isEmpty();
    }

    private void transfer() {
        while (!stackIn.isEmpty()) {
            stackOut.push(stackIn.pop());
        }
    }
}
```

**Python 实现**

```python
class MyQueue:
    def __init__(self):
        self.stack_in = []
        self.stack_out = []

    def push(self, x: int) -> None:
        self.stack_in.append(x)

    def pop(self) -> int:
        if not self.stack_out:
            while self.stack_in:
                self.stack_out.append(self.stack_in.pop())
        return self.stack_out.pop() if self.stack_out else -1

    def peek(self) -> int:
        if not self.stack_out:
            while self.stack_in:
                self.stack_out.append(self.stack_in.pop())
        return self.stack_out[-1] if self.stack_out else -1

    def empty(self) -> bool:
        return not self.stack_in and not self.stack_out
```

**复杂度分析**

| 操作 | 均摊时间复杂度 | 空间复杂度 |
|------|--------------|-----------|
| push | **O(1)** | **O(n)** |
| pop / peek | **O(1)**（摊还） | — |

---

### 15. 滑动窗口最大值（LeetCode 239）⭐⭐⭐

**问题描述**

> 给你一个整数数组 `nums`，有一个大小为 `k` 的滑动窗口从数组最左侧移动到最右侧。你只可以看到窗口中的 k 个数字。返回每个滑动窗口中的最大值。

**思路分析**

- **双端队列（单调递减队列）**：维护一个存储**索引**的双端队列。
- 队首始终是当前窗口最大值的索引。
- 新元素入队前，移除队列中所有比它小的元素（它们不可能再成为最大值）。
- 每次取队首元素即为当前窗口最大值。
- 滑动时，移除超出窗口边界的索引。

**Java 实现**

```java
import java.util.*;

public class MaxSlidingWindow {
    public int[] maxSlidingWindow(int[] nums, int k) {
        if (nums == null || k <= 0) return new int[0];

        int n = nums.length;
        int[] result = new int[n - k + 1];
        int ri = 0;

        // 双端队列，存储数组索引，且 nums[索引] 按递减顺序排列
        Deque<Integer> deque = new LinkedList<>();

        for (int i = 0; i < n; i++) {
            // 移除队首不在窗口内的索引
            if (!deque.isEmpty() && deque.peekFirst() <= i - k) {
                deque.pollFirst();
            }

            // 移除队列中所有比当前元素小的索引（单调递减）
            while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) {
                deque.pollLast();
            }

            deque.offerLast(i);

            // 窗口形成后开始记录结果
            if (i >= k - 1) {
                result[ri++] = nums[deque.peekFirst()];
            }
        }
        return result;
    }
}
```

**Python 实现**

```python
from collections import deque

def max_sliding_window(nums: list[int], k: int) -> list[int]:
    if not nums or k == 0:
        return []
    n = len(nums)
    result = []
    dq = deque()  # 存索引

    for i in range(n):
        # 移除超出窗口的索引
        if dq and dq[0] <= i - k:
            dq.popleft()
        # 单调递减：移除所有比当前值小的索引
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()
        dq.append(i)
        # 窗口形成后记录最大值
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，每个元素最多入队出队各一次 |
| 空间复杂度 | **O(k)**，双端队列最多存储 k 个索引 |

---

## 五、动态规划类

### 16. 爬楼梯（LeetCode 70）⭐⭐⭐

**问题描述**

> 假设你正在爬楼梯。每次你可以爬 1 或 2 个台阶。有 `n` 阶台阶，请问有多少种不同的方法可以爬到楼顶？

**思路分析**

- 到达第 `n` 阶的方法 = 到达第 `n-1` 阶后再爬 1 步 + 到达第 `n-2` 阶后再爬 2 步。
- 即 **斐波那契数列**：`dp[n] = dp[n-1] + dp[n-2]`。
- **空间优化**：只需两个变量即可，空间从 O(n) 降到 O(1)。
- 初始值：`dp[1] = 1, dp[2] = 2`。

**Java 实现**

```java
public class ClimbStairs {
    // 方法1：动态规划
    public int climbStairs(int n) {
        if (n <= 2) return n;
        int[] dp = new int[n + 1];
        dp[1] = 1;
        dp[2] = 2;
        for (int i = 3; i <= n; i++) {
            dp[i] = dp[i - 1] + dp[i - 2];
        }
        return dp[n];
    }

    // 方法2：空间优化
    public int climbStairsOptimized(int n) {
        if (n <= 2) return n;
        int prev1 = 2, prev2 = 1;  // dp[i-1], dp[i-2]
        for (int i = 3; i <= n; i++) {
            int curr = prev1 + prev2;
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }
}
```

**Python 实现**

```python
def climb_stairs(n: int) -> int:
    if n <= 2:
        return n
    prev1, prev2 = 2, 1  # dp[i-1], dp[i-2]
    for _ in range(3, n + 1):
        curr = prev1 + prev2
        prev2 = prev1
        prev1 = curr
    return prev1
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)** |
| 空间复杂度 | **O(1)**（空间优化版） |

---

### 17. 买卖股票的最佳时机（LeetCode 121）⭐⭐⭐

**问题描述**

> 给定一个数组 `prices`，它的第 `i` 个元素 `prices[i]` 是一支股票第 `i` 天的价格。如果你最多只允许完成一笔交易（即买入和卖出一只股票），设计一个算法来计算你所能获取的最大利润。

**思路分析**

- **贪心思想**：遍历数组，记录历史最低价 `minPrice`，当前卖出利润 = `当前价格 - minPrice`。
- 维护一个 `maxProfit`，每遍历一个价格就更新最大利润。
- 核心公式：`maxProfit = max(maxProfit, price - minPrice)`。

**Java 实现**

```java
public class BestTimeToBuySellStock {
    public int maxProfit(int[] prices) {
        if (prices == null || prices.length == 0) return 0;

        int minPrice = Integer.MAX_VALUE;
        int maxProfit = 0;

        for (int price : prices) {
            minPrice = Math.min(minPrice, price);            // 更新最低价
            maxProfit = Math.max(maxProfit, price - minPrice); // 更新最大利润
        }
        return maxProfit;
    }
}
```

**Python 实现**

```python
def max_profit(prices: list[int]) -> int:
    if not prices:
        return 0
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，遍历一次数组 |
| 空间复杂度 | **O(1)** |

---

### 18. 0-1 背包问题 ⭐⭐⭐

**问题描述**

> 有 `n` 个物品和容量为 `W` 的背包，每个物品有重量 `w[i]` 和价值 `v[i]`。每种物品只能选一次，求背包能装的**最大价值**。

**思路分析**

- **动态规划**：`dp[j]` 表示容量为 `j` 时的最大价值。
- 状态转移：`dp[j] = max(dp[j], dp[j - w[i]] + v[i])`。
- **空间优化**：用一维数组，**倒序遍历容量**（确保每件物品只选一次）。
- 初始化：`dp[0] = 0`，其余为 0。

**Java 实现（空间优化版）**

```java
public class Knapsack01 {
    public int knapsack(int W, int[] weights, int[] values) {
        int n = weights.length;
        int[] dp = new int[W + 1];

        for (int i = 0; i < n; i++) {
            // 倒序遍历，确保每件物品只选一次
            for (int j = W; j >= weights[i]; j--) {
                dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
            }
        }
        return dp[W];
    }
}
```

**Python 实现**

```python
def knapsack_01(W: int, weights: list[int], values: list[int]) -> int:
    n = len(weights)
    dp = [0] * (W + 1)
    for i in range(n):
        for j in range(W, weights[i] - 1, -1):
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    return dp[W]
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n × W)** |
| 空间复杂度 | **O(W)**（一维优化版） |

---

## 六、字符串类

### 19. 字符串全排列（LeetCode 46 变体）⭐⭐⭐

**问题描述**

> 给定一个不含重复字符的字符串 `s`，返回其所有可能的全排列。

**思路分析**

- **回溯算法**：固定一个字符，对剩余字符递归求解。
- 使用 `visited` 数组标记已选字符，避免重复使用。
- 时间复杂度 O(n × n!)，共有 n! 种排列，每种排列构建需要 O(n)。

**Java 实现**

```java
import java.util.*;

public class StringPermutation {
    public List<String> permute(String s) {
        List<String> result = new ArrayList<>();
        char[] chars = s.toCharArray();
        boolean[] visited = new boolean[chars.length];
        backtrack(chars, visited, new StringBuilder(), result);
        return result;
    }

    private void backtrack(char[] chars, boolean[] visited, 
                          StringBuilder path, List<String> result) {
        if (path.length() == chars.length) {
            result.add(path.toString());
            return;
        }

        for (int i = 0; i < chars.length; i++) {
            if (visited[i]) continue;
            visited[i] = true;
            path.append(chars[i]);
            backtrack(chars, visited, path, result);
            path.deleteCharAt(path.length() - 1);  // 回溯
            visited[i] = false;
        }
    }
}
```

**Python 实现**

```python
def permute(s: str) -> list[str]:
    result = []
    chars = list(s)
    n = len(chars)
    visited = [False] * n

    def backtrack(path: list):
        if len(path) == n:
            result.append(''.join(path))
            return
        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            path.append(chars[i])
            backtrack(path)
            path.pop()
            visited[i] = False

    backtrack([])
    return result
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n × n!)** |
| 空间复杂度 | **O(n)**（递归栈 + visited 数组） |

---

### 20. 反转字符串（LeetCode 344）⭐⭐

**问题描述**

> 编写一个函数，其作用是将输入的字符串反转过来。要求 **原地修改**，空间复杂度 O(1)。

**思路分析**

- **双指针**：左指针从头部开始，右指针从尾部开始，交换字符并向中间移动。
- 直到 `left >= right` 为止。

**Java 实现**

```java
public class ReverseString {
    public void reverseString(char[] s) {
        int left = 0, right = s.length - 1;
        while (left < right) {
            char tmp = s[left];
            s[left] = s[right];
            s[right] = tmp;
            left++;
            right--;
        }
    }
}
```

**Python 实现**

```python
def reverse_string(s: list[str]) -> None:
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(n)**，两指针各遍历半个数组 |
| 空间复杂度 | **O(1)**，原地交换 |

---

## 七、搜索类

### 21. 二分查找（LeetCode 704）⭐⭐⭐

**问题描述**

> 给定一个有序整数数组 `nums` 和一个目标值 `target`，如果数组中存在目标，则返回其下标；否则返回 `-1`。

**思路分析**

- 数组有序 → 自然想到 **二分查找**。
- 关键：`mid = left + (right - left) / 2`，避免整数溢出。
- 循环条件 `left <= right`（等于时仍需判断）。
- 更新时：`target > mid` → `left = mid + 1`；否则 → `right = mid - 1`。

**Java 实现（标准版）**

```java
public class BinarySearch {
    public int search(int[] nums, int target) {
        int left = 0, right = nums.length - 1;

        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] == target) {
                return mid;
            } else if (nums[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1;
    }
}
```

**Python 实现**

```python
def binary_search(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(log n)**，每次折半 |
| 空间复杂度 | **O(1)** |

---

### 22. 搜索旋转排序数组（LeetCode 33）⭐⭐⭐

**问题描述**

> 已知排序数组 `nums` 在某个位置被旋转了（例如 `[0,1,2,4,5,6,7]` 旋转后变为 `[4,5,6,7,0,1,2]`）。给定一个目标值 `target`，返回它在数组中的下标，不存在返回 `-1`。

**思路分析**

- 旋转数组虽被打乱，但**每一半仍是有序的**。
- 在 `[left, right]` 区间内，比较 `nums[mid]` 与 `nums[left]` 确定**哪一半是有序的**。
- 然后判断 target 是否在有序的那一半中，缩小搜索范围。

**Java 实现**

```java
public class SearchRotatedArray {
    public int search(int[] nums, int target) {
        if (nums == null || nums.length == 0) return -1;

        int left = 0, right = nums.length - 1;

        while (left <= right) {
            int mid = left + (right - left) / 2;

            if (nums[mid] == target) return mid;

            // 左半部分有序
            if (nums[left] <= nums[mid]) {
                if (nums[left] <= target && target < nums[mid]) {
                    right = mid - 1;
                } else {
                    left = mid + 1;
                }
            }
            // 右半部分有序
            else {
                if (nums[mid] < target && target <= nums[right]) {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            }
        }
        return -1;
    }
}
```

**Python 实现**

```python
def search_rotated(nums: list[int], target: int) -> int:
    if not nums:
        return -1
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid

        # 左半边有序
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # 右半边有序
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
```

**复杂度分析**

| 项目 | 复杂度 |
|------|--------|
| 时间复杂度 | **O(log n)** |
| 空间复杂度 | **O(1)** |

---

## 八、面试高频问题汇总

以下表格汇总了本文档所有题目的核心信息，方便快速查阅和对比：

| 序号 | 题目 | 分类 | 核心解法 | 时间复杂度 | 空间复杂度 |
|------|------|------|---------|-----------|-----------|
| 1 | 两数之和 | 数组 | 哈希表 | O(n) | O(n) |
| 2 | 三数之和 | 数组 | 排序 + 双指针 | O(n²) | O(1) |
| 3 | 接雨水 | 数组 | 双指针 + 木桶原理 | O(n) | O(1) |
| 4 | 反转链表 | 链表 | 三指针迭代 / 递归 | O(n) | O(1) / O(n) |
| 5 | 合并两个有序链表 | 链表 | 虚拟头节点 + 双指针 | O(m+n) | O(1) |
| 6 | 链表环入口 | 链表 | Floyd 判圈（快慢指针） | O(n) | O(1) |
| 7 | 相交链表 | 链表 | 双指针（A走完换B） | O(m+n) | O(1) |
| 8 | 前序遍历（非递归） | 二叉树 | 栈模拟 | O(n) | O(h) |
| 9 | 中序遍历（非递归） | 二叉树 | 栈模拟 | O(n) | O(h) |
| 10 | 二叉树最大深度 | 二叉树 | 递归 / BFS | O(n) | O(h) |
| 11 | 对称二叉树 | 二叉树 | 递归比较镜像子树 | O(n) | O(h) |
| 12 | 层序遍历 | 二叉树 | BFS + 队列 | O(n) | O(n) |
| 13 | 最小栈 | 栈 | 双栈（主栈 + 最小值栈） | O(1) 各操作 | O(n) |
| 14 | 栈实现队列 | 栈 | 双栈（倒序） | O(1) 均摊 | O(n) |
| 15 | 滑动窗口最大值 | 队列 | 单调递减双端队列 | O(n) | O(k) |
| 16 | 爬楼梯 | 动态规划 | 斐波那契 | O(n) | O(1) |
| 17 | 买卖股票 | 动态规划 | 贪心（记录最低价） | O(n) | O(1) |
| 18 | 0-1 背包 | 动态规划 | 一维 DP（倒序） | O(n×W) | O(W) |
| 19 | 字符串全排列 | 字符串 | 回溯 + visited | O(n×n!) | O(n) |
| 20 | 反转字符串 | 字符串 | 双指针原地交换 | O(n) | O(1) |
| 21 | 二分查找 | 搜索 | 二分 | O(log n) | O(1) |
| 22 | 搜索旋转数组 | 搜索 | 二分 + 判断有序区间 | O(log n) | O(1) |

> **h** = 树高，**W** = 背包容量，**n** = 输入规模

---

## 九、面试技巧总结

### 1. 先确认题意，再动手

- 询问数据范围（数组长度、元素大小、是否有重复值等）。
- 确认返回值要求（下标 / 值 / 布尔 / 列表）。
- 边界情况：空数组、单个元素、全重复、全负数。

### 2. 先讲思路，再写代码

面试官更关注你的**思考过程**，而非代码本身。描述清楚：
- 用什么数据结构（数组、哈希表、栈、队列、堆……）
- 核心算法（双指针、滑动窗口、DFS/BFS、回溯、DP……）
- 时间空间复杂度预期

### 3. 代码写完后主动分析复杂度

写完代码后，简要说明："这里我遍历了 n 个元素，时间复杂度是 O(n)，空间上用了几个指针和常数个变量，空间复杂度是 O(1)。"

### 4. 多种解法，体现深度

如果时间充裕，可以补充："暴力法是 O(n²)，但我们可以用哈希表优化到 O(n)。"或者："递归版本好理解，但面试中我更推荐迭代版本，避免栈溢出。"

### 5. 手写代码注意细节

- 变量命名清晰。
- 循环条件不要写错（`left <= right` 还是 `left < right`）。
- 记得处理空指针和越界问题。
- 善用 Java 的 `Arrays` / `Collections` 或 Python 的切片、列表操作简化代码。

---

**参考链接：**

- [LeetCode 热题 100](https://leetcode.cn/problem-list/hot-100/)
- [剑指 Offer 在线刷题](https://leetcode.cn/problem-list/lcof/)
- [程序员面试金典（第 6 版）](https://leetcode.cn/problemset/lcr/)
