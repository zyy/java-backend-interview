---
layout: default
title: 图论基础
---
# 图论基础

> 复杂关系建模

## 🎯 面试重点

- 图的表示
- BFS/DFS

## 📖 图的表示

```java
/**
 * 图的表示
 */
public class GraphRepresentation {
    // 邻接矩阵
    /*
     * int[][] matrix;
     * matrix[i][j] = 1 表示有边
     */
    
    // 邻接表
    /*
     * List<List<Integer>> adj;
     * adj.get(i) 存储节点 i 的邻居
     */
}
```

## 📖 遍历

```java
/**
 * BFS
 */
public class BFS {
    void bfs(int start, List<List<Integer>> adj) {
        boolean[] visited = new boolean[adj.size()];
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(start);
        visited[start] = true;
        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int neighbor : adj.get(node)) {
                if (!visited[neighbor]) {
                    visited[neighbor] = true;
                    queue.offer(neighbor);
                }
            }
        }
    }
}
```

## 📖 面试真题

### Q1: BFS 和 DFS 区别？

**答：** BFS 用队列，逐层遍历；DFS 用栈（递归），深入到底。

---

**⭐ 重点：图算法是高级数据结构**