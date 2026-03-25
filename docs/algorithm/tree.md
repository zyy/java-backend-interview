# 树与二叉树

> 层级数据结构

## 🎯 面试重点

- 二叉树遍历
- 常见题型

## 📖 遍历

```java
/**
 * 二叉树遍历
 */
public class TreeTraversal {
    static class TreeNode {
        int val;
        TreeNode left, right;
    }
    
    // 前序（根-左-右）
    void preorder(TreeNode root) {
        if (root == null) return;
        System.out.println(root.val);
        preorder(root.left);
        preorder(root.right);
    }
    
    // 中序（左-根-右）
    void inorder(TreeNode root) {
        if (root == null) return;
        inorder(root.left);
        System.out.println(root.val);
        inorder(root.right);
    }
    
    // 后序（左-右-根）
    void postorder(TreeNode root) {
        if (root == null) return;
        postorder(root.left);
        postorder(root.right);
        System.out.println(root.val);
    }
    
    // 层序（BFS）
    void levelOrder(TreeNode root) {
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            TreeNode node = queue.poll();
            System.out.println(node.val);
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
    }
}
```

## 📖 面试真题

### Q1: 前/中/后序遍历区别？

**答：** 根节点访问顺序不同：前序先根，中序中间，后序最后。

---

**⭐ 重点：二叉树遍历是树算法的基础**