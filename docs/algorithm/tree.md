---
layout: default
title: 二叉树高频面试题精讲 ⭐⭐⭐
---
# 二叉树高频面试题精讲 ⭐⭐⭐

> 二叉树是算法面试的核心考点，几乎每场面试必考

## 🎯 面试重点

- 二叉树基础概念与性质
- 前序/中序/后序遍历（递归 + 非递归）
- 层序遍历（BFS）
- Morris 遍历（O(1) 空间）
- 二叉树深度、直径、路径问题
- 最近公共祖先（LCA）
- 二叉搜索树（BST）操作
- 二叉树构建与序列化

---

## 📖 一、二叉树基础概念

### 1.1 基本定义

```java
/**
 * 二叉树节点定义
 */
public class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    
    TreeNode() {}
    
    TreeNode(int val) {
        this.val = val;
    }
    
    TreeNode(int val, TreeNode left, TreeNode right) {
        this.val = val;
        this.left = left;
        this.right = right;
    }
}
```

### 1.2 特殊二叉树类型

#### 满二叉树（Full Binary Tree）

```
定义：每个节点要么是叶子节点，要么有两个子节点

        1
       / \
      2   3
     / \ / \
    4  5 6  7

性质：
- 第 h 层有 2^(h-1) 个节点
- 总节点数 = 2^h - 1（h 为高度）
- 叶子节点数 = 内部节点数 + 1
```

#### 完全二叉树（Complete Binary Tree）

```
定义：除最后一层外，每层节点数达到最大，最后一层节点靠左排列

        1
       / \
      2   3
     / \  /
    4  5 6

性质：
- 适合用数组存储（堆的底层结构）
- 节点 i 的左孩子：2i + 1
- 节点 i 的右孩子：2i + 2
- 节点 i 的父节点：(i - 1) / 2
- 总节点数 n，高度 = ⌊log₂n⌋ + 1
```

```java
/**
 * 判断完全二叉树
 */
public boolean isCompleteTree(TreeNode root) {
    if (root == null) return true;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    boolean hasNull = false;  // 是否遇到过空节点
    
    while (!queue.isEmpty()) {
        TreeNode node = queue.poll();
        
        if (node == null) {
            hasNull = true;
        } else {
            // 如果之前遇到过空节点，当前节点不为空，则不是完全二叉树
            if (hasNull) return false;
            queue.offer(node.left);
            queue.offer(node.right);
        }
    }
    return true;
}
```

#### 平衡二叉树（Balanced Binary Tree / AVL 树）

```
定义：每个节点的左右子树高度差不超过 1

        4
       / \
      2   6
     / \ / \
    1  3 5  7

性质：
- 查找/插入/删除：O(log n)
- 保持平衡需要旋转操作
```

```java
/**
 * 判断平衡二叉树
 */
public boolean isBalanced(TreeNode root) {
    return getHeight(root) != -1;
}

// 返回高度，如果不平衡返回 -1
private int getHeight(TreeNode node) {
    if (node == null) return 0;
    
    int leftHeight = getHeight(node.left);
    if (leftHeight == -1) return -1;
    
    int rightHeight = getHeight(node.right);
    if (rightHeight == -1) return -1;
    
    // 高度差超过 1，不平衡
    if (Math.abs(leftHeight - rightHeight) > 1) return -1;
    
    return Math.max(leftHeight, rightHeight) + 1;
}
```

#### 二叉搜索树（Binary Search Tree / BST）

```
定义：左子树所有节点 < 根节点 < 右子树所有节点

        5
       / \
      3   7
     / \ / \
    2  4 6  8

性质：
- 中序遍历是有序序列
- 查找/插入/删除：平均 O(log n)，最坏 O(n)
- 最坏情况：退化成链表
```

### 1.3 二叉树重要性质

```
1. 第 i 层最多有 2^(i-1) 个节点（i ≥ 1）

2. 深度为 k 的二叉树最多有 2^k - 1 个节点

3. 任何一棵二叉树，叶子节点数 n0 = 度为 2 的节点数 n2 + 1
   推导：n = n0 + n1 + n2
         边数 = n - 1 = n1 + 2*n2
         解得：n0 = n2 + 1

4. n 个节点的完全二叉树深度 = ⌊log₂n⌋ + 1

5. 完全二叉树性质（节点从 0 开始编号）：
   - 节点 i 的父节点 = (i - 1) / 2
   - 节点 i 的左孩子 = 2i + 1
   - 节点 i 的右孩子 = 2i + 2
```

---

## 📖 二、二叉树遍历

### 2.1 前序遍历（Preorder）

遍历顺序：根 → 左 → 右

#### 递归实现

```java
/**
 * 前序遍历 - 递归
 */
public List<Integer> preorderTraversal(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    preorder(root, result);
    return result;
}

private void preorder(TreeNode node, List<Integer> result) {
    if (node == null) return;
    
    result.add(node.val);       // 1. 访问根
    preorder(node.left, result);  // 2. 遍历左子树
    preorder(node.right, result); // 3. 遍历右子树
}
```

#### 非递归实现（栈）

```java
/**
 * 前序遍历 - 迭代（栈）
 * 
 * 思路：
 * 1. 访问根节点
 * 2. 右孩子先入栈（后出栈）
 * 3. 左孩子后入栈（先出栈）
 */
public List<Integer> preorderTraversalIterative(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);
    
    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        result.add(node.val);
        
        // 右孩子先入栈，保证左孩子先处理
        if (node.right != null) stack.push(node.right);
        if (node.left != null) stack.push(node.left);
    }
    
    return result;
}
```

#### 统一迭代写法

```java
/**
 * 前序遍历 - 统一迭代写法
 * 
 * 思路：使用 null 标记待访问节点
 */
public List<Integer> preorderTraversalUnified(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);
    
    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        
        if (node != null) {
            // 前序：根 → 左 → 右，入栈顺序相反
            if (node.right != null) stack.push(node.right);
            if (node.left != null) stack.push(node.left);
            stack.push(node);
            stack.push(null);  // 标记已处理
        } else {
            result.add(stack.pop().val);
        }
    }
    
    return result;
}
```

### 2.2 中序遍历（Inorder）

遍历顺序：左 → 根 → 右

#### 递归实现

```java
/**
 * 中序遍历 - 递归
 */
public List<Integer> inorderTraversal(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    inorder(root, result);
    return result;
}

private void inorder(TreeNode node, List<Integer> result) {
    if (node == null) return;
    
    inorder(node.left, result);   // 1. 遍历左子树
    result.add(node.val);         // 2. 访问根
    inorder(node.right, result);  // 3. 遍历右子树
}
```

#### 非递归实现（栈）

```java
/**
 * 中序遍历 - 迭代（栈）
 * 
 * 思路：
 * 1. 先将所有左孩子入栈
 * 2. 弹出栈顶并访问
 * 3. 转向右子树，重复步骤 1
 */
public List<Integer> inorderTraversalIterative(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    Deque<TreeNode> stack = new ArrayDeque<>();
    TreeNode cur = root;
    
    while (cur != null || !stack.isEmpty()) {
        // 先走到最左边
        while (cur != null) {
            stack.push(cur);
            cur = cur.left;
        }
        
        // 弹出并访问
        cur = stack.pop();
        result.add(cur.val);
        
        // 转向右子树
        cur = cur.right;
    }
    
    return result;
}
```

#### 统一迭代写法

```java
/**
 * 中序遍历 - 统一迭代写法
 */
public List<Integer> inorderTraversalUnified(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);
    
    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        
        if (node != null) {
            // 中序：左 → 根 → 右，入栈顺序相反
            if (node.right != null) stack.push(node.right);
            stack.push(node);
            stack.push(null);  // 标记
            if (node.left != null) stack.push(node.left);
        } else {
            result.add(stack.pop().val);
        }
    }
    
    return result;
}
```

### 2.3 后序遍历（Postorder）

遍历顺序：左 → 右 → 根

#### 递归实现

```java
/**
 * 后序遍历 - 递归
 */
public List<Integer> postorderTraversal(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    postorder(root, result);
    return result;
}

private void postorder(TreeNode node, List<Integer> result) {
    if (node == null) return;
    
    postorder(node.left, result);   // 1. 遍历左子树
    postorder(node.right, result);  // 2. 遍历右子树
    result.add(node.val);           // 3. 访问根
}
```

#### 非递归实现（栈）

```java
/**
 * 后序遍历 - 迭代（栈）
 * 
 * 方法1：反转前序遍历结果
 * 前序：根 → 左 → 右
 * 修改前序：根 → 右 → 左
 * 反转得到：左 → 右 → 根（后序）
 */
public List<Integer> postorderTraversalIterative(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);
    
    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        result.add(node.val);
        
        // 与前序相反：左先入栈
        if (node.left != null) stack.push(node.left);
        if (node.right != null) stack.push(node.right);
    }
    
    Collections.reverse(result);
    return result;
}
```

```java
/**
 * 后序遍历 - 迭代（使用 prev 标记）
 */
public List<Integer> postorderTraversalIterative2(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    TreeNode prev = null;  // 上一个访问的节点
    
    while (root != null || !stack.isEmpty()) {
        // 走到最左边
        while (root != null) {
            stack.push(root);
            root = root.left;
        }
        
        root = stack.pop();
        
        // 右子树为空或已访问过
        if (root.right == null || root.right == prev) {
            result.add(root.val);
            prev = root;
            root = null;
        } else {
            // 重新入栈，转向右子树
            stack.push(root);
            root = root.right;
        }
    }
    
    return result;
}
```

#### 统一迭代写法

```java
/**
 * 后序遍历 - 统一迭代写法
 */
public List<Integer> postorderTraversalUnified(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Deque<TreeNode> stack = new ArrayDeque<>();
    stack.push(root);
    
    while (!stack.isEmpty()) {
        TreeNode node = stack.pop();
        
        if (node != null) {
            // 后序：左 → 右 → 根，入栈顺序相反
            stack.push(node);
            stack.push(null);  // 标记
            if (node.right != null) stack.push(node.right);
            if (node.left != null) stack.push(node.left);
        } else {
            result.add(stack.pop().val);
        }
    }
    
    return result;
}
```

### 2.4 遍历复杂度对比

| 遍历方式 | 时间复杂度 | 空间复杂度（递归） | 空间复杂度（迭代） |
|---------|-----------|-----------------|-----------------|
| 前序遍历 | O(n)      | O(h) 最坏 O(n)   | O(h) 最坏 O(n)   |
| 中序遍历 | O(n)      | O(h) 最坏 O(n)   | O(h) 最坏 O(n)   |
| 后序遍历 | O(n)      | O(h) 最坏 O(n)   | O(h) 最坏 O(n)   |

> h 为树高度，平衡树 h = log n，链状树 h = n

---

## 📖 三、层序遍历（BFS）

### 3.1 基本层序遍历

```java
/**
 * 层序遍历 - 基础版
 */
public List<Integer> levelOrder(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    
    while (!queue.isEmpty()) {
        TreeNode node = queue.poll();
        result.add(node.val);
        
        if (node.left != null) queue.offer(node.left);
        if (node.right != null) queue.offer(node.right);
    }
    
    return result;
}
```

### 3.2 按层分组

```java
/**
 * 层序遍历 - 按层分组
 */
public List<List<Integer>> levelOrderGrouped(TreeNode root) {
    List<List<Integer>> result = new ArrayList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    
    while (!queue.isEmpty()) {
        int levelSize = queue.size();  // 当前层节点数
        List<Integer> level = new ArrayList<>();
        
        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            level.add(node.val);
            
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        
        result.add(level);
    }
    
    return result;
}
```

### 3.3 自底向上层序遍历

```java
/**
 * 自底向上层序遍历
 */
public List<List<Integer>> levelOrderBottom(TreeNode root) {
    LinkedList<List<Integer>> result = new LinkedList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    
    while (!queue.isEmpty()) {
        int levelSize = queue.size();
        List<Integer> level = new ArrayList<>();
        
        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            level.add(node.val);
            
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        
        result.addFirst(level);  // 头插法
    }
    
    return result;
}
```

### 3.4 锯齿形层序遍历

```java
/**
 * 锯齿形层序遍历（之字形）
 */
public List<List<Integer>> zigzagLevelOrder(TreeNode root) {
    List<List<Integer>> result = new ArrayList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    boolean leftToRight = true;
    
    while (!queue.isEmpty()) {
        int levelSize = queue.size();
        LinkedList<Integer> level = new LinkedList<>();
        
        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            
            if (leftToRight) {
                level.addLast(node.val);
            } else {
                level.addFirst(node.val);
            }
            
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        
        result.add(level);
        leftToRight = !leftToRight;
    }
    
    return result;
}
```

### 3.5 层序遍历应用

```java
/**
 * 二叉树右视图
 */
public List<Integer> rightSideView(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    if (root == null) return result;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    
    while (!queue.isEmpty()) {
        int levelSize = queue.size();
        
        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            
            // 当前层最后一个节点
            if (i == levelSize - 1) {
                result.add(node.val);
            }
            
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
    }
    
    return result;
}
```

---

## 📖 四、Morris 遍历（O(1) 空间）

### 4.1 核心思想

```
传统遍历需要 O(h) 的栈空间（递归或显式栈）

Morris 遍历：利用空闲的 right 指针
- 遍历时，将右子树的最右节点（前驱节点）的 right 指向当前节点
- 这样可以回到上层节点，不需要额外空间
- 遍历完成后恢复原结构

核心操作：找前驱节点
- 当前节点 cur 的前驱 = 左子树的最右节点
```

### 4.2 Morris 前序遍历

```java
/**
 * Morris 前序遍历
 * 
 * 步骤：
 * 1. 如果没有左孩子，访问当前节点，转向右孩子
 * 2. 如果有左孩子，找前驱节点 pre（左子树最右）
 *    - 如果 pre.right == null：
 *      访问当前节点，pre.right = cur，转向左孩子
 *    - 如果 pre.right == cur：
 *      pre.right = null（恢复），转向右孩子
 */
public List<Integer> morrisPreorder(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    TreeNode cur = root;
    
    while (cur != null) {
        if (cur.left == null) {
            // 没有左子树，直接访问
            result.add(cur.val);
            cur = cur.right;
        } else {
            // 找前驱节点
            TreeNode pre = cur.left;
            while (pre.right != null && pre.right != cur) {
                pre = pre.right;
            }
            
            if (pre.right == null) {
                // 第一次访问，建立链接
                result.add(cur.val);  // 前序：建立链接时访问
                pre.right = cur;
                cur = cur.left;
            } else {
                // 第二次访问，断开链接
                pre.right = null;
                cur = cur.right;
            }
        }
    }
    
    return result;
}
```

### 4.3 Morris 中序遍历

```java
/**
 * Morris 中序遍历
 * 
 * 与前序的区别：访问节点的时机
 * - 前序：第一次到达时访问（建立链接时）
 * - 中序：第二次到达时访问（断开链接时或没有左子树时）
 */
public List<Integer> morrisInorder(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    TreeNode cur = root;
    
    while (cur != null) {
        if (cur.left == null) {
            // 没有左子树，访问并转向右
            result.add(cur.val);
            cur = cur.right;
        } else {
            // 找前驱
            TreeNode pre = cur.left;
            while (pre.right != null && pre.right != cur) {
                pre = pre.right;
            }
            
            if (pre.right == null) {
                // 建立链接
                pre.right = cur;
                cur = cur.left;
            } else {
                // 断开链接，访问当前节点
                pre.right = null;
                result.add(cur.val);  // 中序：断开链接时访问
                cur = cur.right;
            }
        }
    }
    
    return result;
}
```

### 4.4 Morris 后序遍历

```java
/**
 * Morris 后序遍历
 * 
 * 思路：
 * 1. 创建虚拟节点 dummy，dummy.left = root
 * 2. 对于每个节点，访问其左子树的右边界（逆序）
 * 3. 最终结果就是后序遍历
 */
public List<Integer> morrisPostorder(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    
    // 虚拟节点
    TreeNode dummy = new TreeNode(0);
    dummy.left = root;
    TreeNode cur = dummy;
    
    while (cur != null) {
        if (cur.left == null) {
            cur = cur.right;
        } else {
            TreeNode pre = cur.left;
            while (pre.right != null && pre.right != cur) {
                pre = pre.right;
            }
            
            if (pre.right == null) {
                pre.right = cur;
                cur = cur.left;
            } else {
                // 访问左子树右边界（逆序）
                addPath(result, cur.left);
                pre.right = null;
                cur = cur.right;
            }
        }
    }
    
    return result;
}

// 逆序添加从 node 到右边界
private void addPath(List<Integer> result, TreeNode node) {
    int count = 0;
    while (node != null) {
        count++;
        result.add(node.val);
        node = node.right;
    }
    // 反转
    int left = result.size() - count;
    int right = result.size() - 1;
    while (left < right) {
        int temp = result.get(left);
        result.set(left, result.get(right));
        result.set(right, temp);
        left++;
        right--;
    }
}
```

### 4.5 Morris 遍历复杂度

| 指标 | 复杂度 |
|-----|-------|
| 时间 | O(n) |
| 空间 | **O(1)** |

> 虽然找前驱看似 O(n)，但每个节点最多被访问两次（找前驱 + 遍历），总时间仍为 O(n)

---

## 📖 五、二叉树深度与路径

### 5.1 二叉树最大深度

#### DFS 解法

```java
/**
 * 最大深度 - DFS（递归）
 */
public int maxDepth(TreeNode root) {
    if (root == null) return 0;
    
    int leftDepth = maxDepth(root.left);
    int rightDepth = maxDepth(root.right);
    
    return Math.max(leftDepth, rightDepth) + 1;
}
```

#### BFS 解法

```java
/**
 * 最大深度 - BFS（层序）
 */
public int maxDepthBFS(TreeNode root) {
    if (root == null) return 0;
    
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    int depth = 0;
    
    while (!queue.isEmpty()) {
        int size = queue.size();
        depth++;
        
        for (int i = 0; i < size; i++) {
            TreeNode node = queue.poll();
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
    }
    
    return depth;
}
```

### 5.2 二叉树最小深度

```java
/**
 * 最小深度
 * 
 * 注意：最小深度是从根到最近叶子节点的距离
 * 如果左子树为空，不能返回 0
 */
public int minDepth(TreeNode root) {
    if (root == null) return 0;
    
    // 叶子节点
    if (root.left == null && root.right == null) return 1;
    
    // 只有右子树
    if (root.left == null) return minDepth(root.right) + 1;
    
    // 只有左子树
    if (root.right == null) return minDepth(root.left) + 1;
    
    // 两边都有
    return Math.min(minDepth(root.left), minDepth(root.right)) + 1;
}
```

### 5.3 二叉树直径

```java
/**
 * 二叉树直径
 * 
 * 直径 = 任意两节点间最长路径的边数
 * 路径可能不过根节点
 */
private int maxDiameter = 0;

public int diameterOfBinaryTree(TreeNode root) {
    maxDepthForDiameter(root);
    return maxDiameter;
}

private int maxDepthForDiameter(TreeNode node) {
    if (node == null) return 0;
    
    int left = maxDepthForDiameter(node.left);
    int right = maxDepthForDiameter(node.right);
    
    // 更新直径：左深度 + 右深度
    maxDiameter = Math.max(maxDiameter, left + right);
    
    return Math.max(left, right) + 1;
}
```

### 5.4 路径总和

```java
/**
 * 路径总和 I：是否存在根到叶子的路径和等于 targetSum
 */
public boolean hasPathSum(TreeNode root, int targetSum) {
    if (root == null) return false;
    
    // 叶子节点
    if (root.left == null && root.right == null) {
        return targetSum == root.val;
    }
    
    return hasPathSum(root.left, targetSum - root.val) 
        || hasPathSum(root.right, targetSum - root.val);
}
```

```java
/**
 * 路径总和 II：找出所有根到叶子的路径和等于 targetSum
 */
public List<List<Integer>> pathSum(TreeNode root, int targetSum) {
    List<List<Integer>> result = new ArrayList<>();
    List<Integer> path = new ArrayList<>();
    dfsPathSum(root, targetSum, path, result);
    return result;
}

private void dfsPathSum(TreeNode node, int remain, List<Integer> path, 
                        List<List<Integer>> result) {
    if (node == null) return;
    
    path.add(node.val);
    
    // 叶子节点
    if (node.left == null && node.right == null && remain == node.val) {
        result.add(new ArrayList<>(path));
    }
    
    dfsPathSum(node.left, remain - node.val, path, result);
    dfsPathSum(node.right, remain - node.val, path, result);
    
    path.remove(path.size() - 1);  // 回溯
}
```

```java
/**
 * 路径总和 III：路径不需要从根到叶子，任意起点终点
 */
public int pathSumIII(TreeNode root, int targetSum) {
    Map<Long, Integer> prefixSum = new HashMap<>();
    prefixSum.put(0L, 1);
    return dfsPathSumIII(root, 0, targetSum, prefixSum);
}

private int dfsPathSumIII(TreeNode node, long curSum, int target, 
                          Map<Long, Integer> prefixSum) {
    if (node == null) return 0;
    
    curSum += node.val;
    
    // 找前缀和 = curSum - target 的路径数
    int count = prefixSum.getOrDefault(curSum - target, 0);
    
    // 更新前缀和
    prefixSum.put(curSum, prefixSum.getOrDefault(curSum, 0) + 1);
    
    count += dfsPathSumIII(node.left, curSum, target, prefixSum);
    count += dfsPathSumIII(node.right, curSum, target, prefixSum);
    
    // 回溯
    prefixSum.put(curSum, prefixSum.get(curSum) - 1);
    
    return count;
}
```

---

## 📖 六、最近公共祖先（LCA）

### 6.1 普通二叉树的 LCA

```java
/**
 * 二叉树的最近公共祖先
 * 
 * 思路：
 * 1. 如果 root 是 p 或 q，返回 root
 * 2. 递归左右子树
 * 3. 如果左右都找到，当前 root 就是 LCA
 * 4. 如果只有一边找到，返回那一边
 */
public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
    // 终止条件
    if (root == null || root == p || root == q) {
        return root;
    }
    
    // 递归左右
    TreeNode left = lowestCommonAncestor(root.left, p, q);
    TreeNode right = lowestCommonAncestor(root.right, p, q);
    
    // 都找到，当前就是 LCA
    if (left != null && right != null) {
        return root;
    }
    
    // 只有一边找到
    return left != null ? left : right;
}
```

### 6.2 BST 的 LCA

```java
/**
 * 二叉搜索树的最近公共祖先
 * 
 * 利用 BST 性质：
 * - 如果 p, q 都小于 root，LCA 在左子树
 * - 如果 p, q 都大于 root，LCA 在右子树
 * - 否则 root 就是 LCA
 */
public TreeNode lowestCommonAncestorBST(TreeNode root, TreeNode p, TreeNode q) {
    if (root == null) return null;
    
    // 都在左子树
    if (p.val < root.val && q.val < root.val) {
        return lowestCommonAncestorBST(root.left, p, q);
    }
    
    // 都在右子树
    if (p.val > root.val && q.val > root.val) {
        return lowestCommonAncestorBST(root.right, p, q);
    }
    
    // 分叉，当前就是 LCA
    return root;
}
```

```java
/**
 * BST 的 LCA - 迭代版
 */
public TreeNode lowestCommonAncestorBSTIterative(TreeNode root, TreeNode p, TreeNode q) {
    while (root != null) {
        if (p.val < root.val && q.val < root.val) {
            root = root.left;
        } else if (p.val > root.val && q.val > root.val) {
            root = root.right;
        } else {
            return root;
        }
    }
    return null;
}
```

### 6.3 LCA 扩展问题

```java
/**
 * 节点到 LCA 的路径
 */
public List<TreeNode> pathToNode(TreeNode root, TreeNode target) {
    List<TreeNode> path = new ArrayList<>();
    findPath(root, target, path);
    return path;
}

private boolean findPath(TreeNode node, TreeNode target, List<TreeNode> path) {
    if (node == null) return false;
    
    path.add(node);
    
    if (node == target) return true;
    
    if (findPath(node.left, target, path) || findPath(node.right, target, path)) {
        return true;
    }
    
    path.remove(path.size() - 1);
    return false;
}
```

---

## 📖 七、二叉树构建

### 7.1 前序 + 中序构建二叉树

```java
/**
 * 前序 + 中序重建二叉树
 * 
 * 原理：
 * - 前序第一个是根
 * - 在中序中找到根位置，左边是左子树，右边是右子树
 * - 递归构建
 */
public TreeNode buildTree(int[] preorder, int[] inorder) {
    // 中序值到索引的映射
    Map<Integer, Integer> inorderMap = new HashMap<>();
    for (int i = 0; i < inorder.length; i++) {
        inorderMap.put(inorder[i], i);
    }
    
    return build(preorder, 0, preorder.length - 1,
                 inorder, 0, inorder.length - 1, inorderMap);
}

private TreeNode build(int[] preorder, int preStart, int preEnd,
                       int[] inorder, int inStart, int inEnd,
                       Map<Integer, Integer> inorderMap) {
    if (preStart > preEnd) return null;
    
    // 前序第一个是根
    int rootVal = preorder[preStart];
    TreeNode root = new TreeNode(rootVal);
    
    // 根在中序的位置
    int rootIndex = inorderMap.get(rootVal);
    
    // 左子树节点数
    int leftSize = rootIndex - inStart;
    
    // 构建左子树
    root.left = build(preorder, preStart + 1, preStart + leftSize,
                      inorder, inStart, rootIndex - 1, inorderMap);
    
    // 构建右子树
    root.right = build(preorder, preStart + leftSize + 1, preEnd,
                       inorder, rootIndex + 1, inEnd, inorderMap);
    
    return root;
}
```

### 7.2 中序 + 后序构建二叉树

```java
/**
 * 中序 + 后序重建二叉树
 * 
 * 原理：
 * - 后序最后一个是根
 * - 在中序中找到根位置
 * - 递归构建
 */
public TreeNode buildTreeInPost(int[] inorder, int[] postorder) {
    Map<Integer, Integer> inorderMap = new HashMap<>();
    for (int i = 0; i < inorder.length; i++) {
        inorderMap.put(inorder[i], i);
    }
    
    return buildInPost(inorder, 0, inorder.length - 1,
                       postorder, 0, postorder.length - 1, inorderMap);
}

private TreeNode buildInPost(int[] inorder, int inStart, int inEnd,
                             int[] postorder, int postStart, int postEnd,
                             Map<Integer, Integer> inorderMap) {
    if (postStart > postEnd) return null;
    
    // 后序最后一个是根
    int rootVal = postorder[postEnd];
    TreeNode root = new TreeNode(rootVal);
    
    int rootIndex = inorderMap.get(rootVal);
    int leftSize = rootIndex - inStart;
    
    root.left = buildInPost(inorder, inStart, rootIndex - 1,
                            postorder, postStart, postStart + leftSize - 1, inorderMap);
    
    root.right = buildInPost(inorder, rootIndex + 1, inEnd,
                             postorder, postStart + leftSize, postEnd - 1, inorderMap);
    
    return root;
}
```

### 7.3 二叉树序列化与反序列化

```java
/**
 * 二叉树序列化与反序列化
 */
public class Codec {
    
    // 序列化：前序遍历
    public String serialize(TreeNode root) {
        StringBuilder sb = new StringBuilder();
        serializeHelper(root, sb);
        return sb.toString();
    }
    
    private void serializeHelper(TreeNode node, StringBuilder sb) {
        if (node == null) {
            sb.append("null,");
            return;
        }
        
        sb.append(node.val).append(",");
        serializeHelper(node.left, sb);
        serializeHelper(node.right, sb);
    }
    
    // 反序列化
    public TreeNode deserialize(String data) {
        String[] nodes = data.split(",");
        Queue<String> queue = new LinkedList<>(Arrays.asList(nodes));
        return deserializeHelper(queue);
    }
    
    private TreeNode deserializeHelper(Queue<String> queue) {
        String val = queue.poll();
        
        if (val.equals("null")) return null;
        
        TreeNode node = new TreeNode(Integer.parseInt(val));
        node.left = deserializeHelper(queue);
        node.right = deserializeHelper(queue);
        
        return node;
    }
}
```

### 7.4 根据数组构建完全二叉树

```java
/**
 * 数组转完全二叉树
 */
public TreeNode arrayToTree(int[] arr) {
    if (arr == null || arr.length == 0) return null;
    return buildFromArray(arr, 0);
}

private TreeNode buildFromArray(int[] arr, int index) {
    if (index >= arr.length) return null;
    
    TreeNode node = new TreeNode(arr[index]);
    node.left = buildFromArray(arr, 2 * index + 1);
    node.right = buildFromArray(arr, 2 * index + 2);
    
    return node;
}
```

---

## 📖 八、二叉搜索树（BST）

### 8.1 验证 BST

```java
/**
 * 验证二叉搜索树
 * 
 * 方法1：中序遍历，检查是否递增
 */
public boolean isValidBST(TreeNode root) {
    List<Integer> inorder = new ArrayList<>();
    inorderTraversal(root, inorder);
    
    for (int i = 1; i < inorder.size(); i++) {
        if (inorder.get(i) <= inorder.get(i - 1)) {
            return false;
        }
    }
    return true;
}

private void inorderTraversal(TreeNode node, List<Integer> list) {
    if (node == null) return;
    inorderTraversal(node.left, list);
    list.add(node.val);
    inorderTraversal(node.right, list);
}
```

```java
/**
 * 验证 BST - 递归（更优）
 */
public boolean isValidBSTRecursive(TreeNode root) {
    return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
}

private boolean validate(TreeNode node, long min, long max) {
    if (node == null) return true;
    
    // 当前节点值必须在范围内
    if (node.val <= min || node.val >= max) {
        return false;
    }
    
    // 左子树 < node.val，右子树 > node.val
    return validate(node.left, min, node.val) 
        && validate(node.right, node.val, max);
}
```

### 8.2 BST 查找

```java
/**
 * BST 查找 - 递归
 */
public TreeNode searchBST(TreeNode root, int val) {
    if (root == null || root.val == val) {
        return root;
    }
    
    if (val < root.val) {
        return searchBST(root.left, val);
    } else {
        return searchBST(root.right, val);
    }
}
```

```java
/**
 * BST 查找 - 迭代
 */
public TreeNode searchBSTIterative(TreeNode root, int val) {
    while (root != null && root.val != val) {
        root = val < root.val ? root.left : root.right;
    }
    return root;
}
```

### 8.3 BST 插入

```java
/**
 * BST 插入 - 递归
 */
public TreeNode insertIntoBST(TreeNode root, int val) {
    if (root == null) {
        return new TreeNode(val);
    }
    
    if (val < root.val) {
        root.left = insertIntoBST(root.left, val);
    } else {
        root.right = insertIntoBST(root.right, val);
    }
    
    return root;
}
```

```java
/**
 * BST 插入 - 迭代
 */
public TreeNode insertIntoBSTIterative(TreeNode root, int val) {
    if (root == null) return new TreeNode(val);
    
    TreeNode cur = root;
    while (true) {
        if (val < cur.val) {
            if (cur.left == null) {
                cur.left = new TreeNode(val);
                break;
            }
            cur = cur.left;
        } else {
            if (cur.right == null) {
                cur.right = new TreeNode(val);
                break;
            }
            cur = cur.right;
        }
    }
    
    return root;
}
```

### 8.4 BST 删除

```java
/**
 * BST 删除节点
 * 
 * 三种情况：
 * 1. 叶子节点：直接删除
 * 2. 只有一个子节点：用子节点替换
 * 3. 有两个子节点：用后继节点（右子树最小）或前驱节点（左子树最大）替换
 */
public TreeNode deleteNode(TreeNode root, int key) {
    if (root == null) return null;
    
    if (key < root.val) {
        root.left = deleteNode(root.left, key);
    } else if (key > root.val) {
        root.right = deleteNode(root.right, key);
    } else {
        // 找到要删除的节点
        
        // 情况 1 & 2：只有一个子节点或无子节点
        if (root.left == null) return root.right;
        if (root.right == null) return root.left;
        
        // 情况 3：有两个子节点
        // 找后继节点（右子树最小值）
        TreeNode successor = findMin(root.right);
        root.val = successor.val;
        root.right = deleteNode(root.right, successor.val);
    }
    
    return root;
}

private TreeNode findMin(TreeNode node) {
    while (node.left != null) {
        node = node.left;
    }
    return node;
}
```

### 8.5 BST 第 K 小元素

```java
/**
 * BST 第 K 小元素
 * 
 * 中序遍历，第 k 个就是答案
 */
public int kthSmallest(TreeNode root, int k) {
    int[] count = {0};
    int[] result = {0};
    inorderKth(root, k, count, result);
    return result[0];
}

private void inorderKth(TreeNode node, int k, int[] count, int[] result) {
    if (node == null) return;
    
    inorderKth(node.left, k, count, result);
    
    count[0]++;
    if (count[0] == k) {
        result[0] = node.val;
        return;
    }
    
    inorderKth(node.right, k, count, result);
}
```

### 8.6 BST 转有序链表

```java
/**
 * BST 转有序双向链表
 */
public TreeNode treeToDoublyList(TreeNode root) {
    if (root == null) return null;
    
    TreeNode[] prev = {null};
    TreeNode[] head = {null};
    
    inorderConvert(root, prev, head);
    
    // 首尾相连
    head[0].left = prev[0];
    prev[0].right = head[0];
    
    return head[0];
}

private void inorderConvert(TreeNode node, TreeNode[] prev, TreeNode[] head) {
    if (node == null) return;
    
    inorderConvert(node.left, prev, head);
    
    if (prev[0] == null) {
        head[0] = node;  // 第一个节点
    } else {
        prev[0].right = node;
        node.left = prev[0];
    }
    prev[0] = node;
    
    inorderConvert(node.right, prev, head);
}
```

---

## 📖 九、红黑树与 AVL 树对比

### 9.1 AVL 树

```
定义：严格平衡二叉搜索树，左右子树高度差 ≤ 1

特点：
- 查找效率高：O(log n)
- 插入/删除需要多次旋转
- 适合查找密集型场景

旋转类型：
1. LL 型：右旋
2. RR 型：左旋
3. LR 型：先左旋后右旋
4. RL 型：先右旋后