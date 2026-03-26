---
layout: default
title: 图算法高频面试题精讲 ⭐⭐⭐
---

# 图算法高频面试题精讲 ⭐⭐⭐

## 🎯 面试核心

图算法是算法面试的重点，涉及 BFS、DFS、拓扑排序、最短路径等多个知识点。掌握图的表示、遍历和常见算法，对系统设计和复杂问题求解都很有帮助。

---

## 一、图的存储

### 1. 邻接矩阵 vs 邻接表

**邻接矩阵**

```
优点：
- 查询两个顶点是否相邻：O(1)
- 实现简单

缺点：
- 空间复杂度：O(V²)，不适合稀疏图
- 遍历所有边：O(V²)

适用场景：
- 顶点数较少（< 1000）
- 边数较多（接近完全图）
```

```java
// 邻接矩阵表示
int[][] graph = new int[n][n];
// graph[i][j] = 1 表示 i 和 j 之间有边
// graph[i][j] = 0 表示 i 和 j 之间无边
```

**邻接表**

```
优点：
- 空间复杂度：O(V + E)，适合稀疏图
- 遍历所有边：O(V + E)

缺点：
- 查询两个顶点是否相邻：O(degree)

适用场景：
- 顶点数较多
- 边数较少（稀疏图）
```

```java
// 邻接表表示
List<Integer>[] graph = new List[n];
for (int i = 0; i < n; i++) {
    graph[i] = new ArrayList<>();
}
// graph[i].add(j) 表示 i 和 j 之间有边
```

**对比表**

| 操作 | 邻接矩阵 | 邻接表 |
|------|--------|--------|
| 查询边 | O(1) | O(degree) |
| 遍历所有边 | O(V²) | O(V + E) |
| 空间 | O(V²) | O(V + E) |
| 适用 | 稠密图 | 稀疏图 |

---

## 二、BFS 和 DFS

### 2. BFS 模板（广度优先搜索）

**核心思想**

```
从起点开始，逐层向外扩展，找到最短路径。

应用场景：
- 最短路径（无权图）
- 层序遍历
- 拓扑排序
```

**Java 代码**

```java
/**
 * BFS 模板
 * 时间：O(V + E)
 * 空间：O(V)
 */
public void bfs(List<Integer>[] graph, int start) {
    int n = graph.length;
    boolean[] visited = new boolean[n];
    Queue<Integer> queue = new LinkedList<>();
    
    queue.offer(start);
    visited[start] = true;
    
    while (!queue.isEmpty()) {
        int node = queue.poll();
        System.out.println(node);  // 处理节点
        
        // 遍历所有邻接节点
        for (int neighbor : graph[node]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                queue.offer(neighbor);
            }
        }
    }
}

/**
 * BFS 求最短路径
 */
public int[] bfsShortestPath(List<Integer>[] graph, int start) {
    int n = graph.length;
    int[] dist = new int[n];
    Arrays.fill(dist, -1);
    
    Queue<Integer> queue = new LinkedList<>();
    queue.offer(start);
    dist[start] = 0;
    
    while (!queue.isEmpty()) {
        int node = queue.poll();
        
        for (int neighbor : graph[node]) {
            if (dist[neighbor] == -1) {
                dist[neighbor] = dist[node] + 1;
                queue.offer(neighbor);
            }
        }
    }
    
    return dist;
}
```

---

### 3. DFS 模板（深度优先搜索）

**核心思想**

```
从起点开始，沿着一条路径尽可能深地探索，直到无法继续，然后回溯。

应用场景：
- 连通性检测
- 环检测
- 拓扑排序
- 强连通分量
```

**Java 代码**

```java
/**
 * DFS 模板（递归）
 * 时间：O(V + E)
 * 空间：O(V)（递归栈）
 */
public void dfs(List<Integer>[] graph, int node, boolean[] visited) {
    visited[node] = true;
    System.out.println(node);  // 处理节点
    
    for (int neighbor : graph[node]) {
        if (!visited[neighbor]) {
            dfs(graph, neighbor, visited);
        }
    }
}

/**
 * DFS 模板（迭代）
 */
public void dfIterative(List<Integer>[] graph, int start) {
    int n = graph.length;
    boolean[] visited = new boolean[n];
    Stack<Integer> stack = new Stack<>();
    
    stack.push(start);
    visited[start] = true;
    
    while (!stack.isEmpty()) {
        int node = stack.pop();
        System.out.println(node);  // 处理节点
        
        for (int neighbor : graph[node]) {
            if (!visited[neighbor]) {
                visited[neighbor] = true;
                stack.push(neighbor);
            }
        }
    }
}

/**
 * DFS 检测环
 */
public boolean hasCycle(List<Integer>[] graph) {
    int n = graph.length;
    int[] color = new int[n];  // 0: 白色，1: 灰色，2: 黑色
    
    for (int i = 0; i < n; i++) {
        if (color[i] == 0) {
            if (dfsCycle(graph, i, color)) {
                return true;
            }
        }
    }
    
    return false;
}

private boolean dfsCycle(List<Integer>[] graph, int node, int[] color) {
    color[node] = 1;  // 灰色
    
    for (int neighbor : graph[node]) {
        if (color[neighbor] == 1) {
            // 回边，存在环
            return true;
        }
        if (color[neighbor] == 0) {
            if (dfsCycle(graph, neighbor, color)) {
                return true;
            }
        }
    }
    
    color[node] = 2;  // 黑色
    return false;
}
```

---

## 三、拓扑排序

### 4. 拓扑排序（LeetCode 207 & 210）

**问题描述**

给定一个有向无环图（DAG），找出所有顶点的一个线性排序，使得对于每条边 (u, v)，u 都在 v 之前。

```
输入：numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
输出：[0, 1, 2, 3] 或 [0, 2, 1, 3]
```

**思路分析**

- **Kahn 算法**：基于入度的 BFS
  1. 计算每个顶点的入度
  2. 将入度为 0 的顶点加入队列
  3. 逐个处理队列中的顶点，更新邻接顶点的入度
  4. 如果最后处理的顶点数 < 总顶点数，说明存在环

**Java 代码（Kahn 算法）**

```java
/**
 * 拓扑排序 - Kahn 算法
 * 时间：O(V + E)
 * 空间：O(V)
 */
public int[] topologicalSort(int numCourses, int[][] prerequisites) {
    // 构建邻接表和入度数组
    List<Integer>[] graph = new List[numCourses];
    int[] inDegree = new int[numCourses];
    
    for (int i = 0; i < numCourses; i++) {
        graph[i] = new ArrayList<>();
    }
    
    for (int[] edge : prerequisites) {
        int from = edge[1];
        int to = edge[0];
        graph[from].add(to);
        inDegree[to]++;
    }
    
    // 将入度为 0 的顶点加入队列
    Queue<Integer> queue = new LinkedList<>();
    for (int i = 0; i < numCourses; i++) {
        if (inDegree[i] == 0) {
            queue.offer(i);
        }
    }
    
    // BFS 处理
    int[] result = new int[numCourses];
    int index = 0;
    
    while (!queue.isEmpty()) {
        int node = queue.poll();
        result[index++] = node;
        
        // 更新邻接顶点的入度
        for (int neighbor : graph[node]) {
            inDegree[neighbor]--;
            if (inDegree[neighbor] == 0) {
                queue.offer(neighbor);
            }
        }
    }
    
    // 检查是否存在环
    if (index != numCourses) {
        return new int[0];  // 存在环
    }
    
    return result;
}
```

**Java 代码（DFS 方案）**

```java
/**
 * 拓扑排序 - DFS 方案
 */
public int[] topologicalSortDFS(int numCourses, int[][] prerequisites) {
    List<Integer>[] graph = new List[numCourses];
    int[] color = new int[numCourses];  // 0: 白色，1: 灰色，2: 黑色
    Stack<Integer> stack = new Stack<>();
    
    for (int i = 0; i < numCourses; i++) {
        graph[i] = new ArrayList<>();
    }
    
    for (int[] edge : prerequisites) {
        graph[edge[1]].add(edge[0]);
    }
    
    // DFS 遍历
    for (int i = 0; i < numCourses; i++) {
        if (color[i] == 0) {
            if (!dfsTopo(graph, i, color, stack)) {
                return new int[0];  // 存在环
            }
        }
    }
    
    // 栈中的顺序就是拓扑排序
    int[] result = new int[numCourses];
    int index = 0;
    while (!stack.isEmpty()) {
        result[index++] = stack.pop();
    }
    
    return result;
}

private boolean dfsTopo(List<Integer>[] graph, int node, int[] color, Stack<Integer> stack) {
    color[node] = 1;  // 灰色
    
    for (int neighbor : graph[node]) {
        if (color[neighbor] == 1) {
            return false;  // 存在环
        }
        if (color[neighbor] == 0) {
            if (!dfsTopo(graph, neighbor, color, stack)) {
                return false;
            }
        }
    }
    
    color[node] = 2;  // 黑色
    stack.push(node);
    return true;
}
```

---

## 四、并查集（Union-Find）

### 5. 并查集基础

**核心思想**

```
并查集用于处理不相交集合的合并和查询问题。

两个基本操作：
1. find(x)：找到 x 所在集合的代表元素
2. union(x, y)：合并 x 和 y 所在的集合

优化技巧：
1. 路径压缩：find 时，直接指向根节点
2. 按秩合并：合并时，将秩小的树挂到秩大的树下
```

**Java 代码**

```java
class UnionFind {
    private int[] parent;
    private int[] rank;
    
    public UnionFind(int n) {
        parent = new int[n];
        rank = new int[n];
        
        for (int i = 0; i < n; i++) {
            parent[i] = i;
            rank[i] = 0;
        }
    }
    
    /**
     * 查找代表元素（路径压缩）
     * 时间：O(α(N))，接近 O(1)
     */
    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // 路径压缩
        }
        return parent[x];
    }
    
    /**
     * 合并两个集合（按秩合并）
     * 时间：O(α(N))，接近 O(1)
     */
    public void union(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        
        if (rootX == rootY) {
            return;  // 已在同一集合
        }
        
        // 按秩合并
        if (rank[rootX] < rank[rootY]) {
            parent[rootX] = rootY;
        } else if (rank[rootX] > rank[rootY]) {
            parent[rootY] = rootX;
        } else {
            parent[rootY] = rootX;
            rank[rootX]++;
        }
    }
    
    /**
     * 判断两个元素是否在同一集合
     */
    public boolean isConnected(int x, int y) {
        return find(x) == find(y);
    }
}
```

---

### 6. 岛屿数量（LeetCode 200）

**问题描述**

给定一个 2D 网格，其中 '1' 表示陆地，'0' 表示水。计算岛屿的数量。

```
输入：
1 1 0 0 0
1 1 0 0 0
0 0 1 0 0
0 0 0 1 1

输出：3
```

**思路分析**

- **DFS 方案**：遍历每个陆地，用 DFS 标记连通的陆地
- **BFS 方案**：遍历每个陆地，用 BFS 标记连通的陆地
- **并查集方案**：将相邻的陆地合并，最后统计集合数量

**Java 代码（DFS）**

```java
public int numIslands(char[][] grid) {
    if (grid == null || grid.length == 0) {
        return 0;
    }
    
    int rows = grid.length;
    int cols = grid[0].length;
    int count = 0;
    
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (grid[i][j] == '1') {
                dfsIsland(grid, i, j);
                count++;
            }
        }
    }
    
    return count;
}

private void dfsIsland(char[][] grid, int i, int j) {
    if (i < 0 || i >= grid.length || j < 0 || j >= grid[0].length || grid[i][j] == '0') {
        return;
    }
    
    grid[i][j] = '0';  // 标记为已访问
    
    // 上下左右四个方向
    dfsIsland(grid, i - 1, j);
    dfsIsland(grid, i + 1, j);
    dfsIsland(grid, i, j - 1);
    dfsIsland(grid, i, j + 1);
}
```

**Java 代码（并查集）**

```java
public int numIslandsUnionFind(char[][] grid) {
    if (grid == null || grid.length == 0) {
        return 0;
    }
    
    int rows = grid.length;
    int cols = grid[0].length;
    UnionFind uf = new UnionFind(rows * cols);
    
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (grid[i][j] == '1') {
                // 与右边的陆地合并
                if (j + 1 < cols && grid[i][j + 1] == '1') {
                    uf.union(i * cols + j, i * cols + j + 1);
                }
                // 与下边的陆地合并
                if (i + 1 < rows && grid[i + 1][j] == '1') {
                    uf.union(i * cols + j, (i + 1) * cols + j);
                }
            }
        }
    }
    
    // 统计集合数量
    Set<Integer> roots = new HashSet<>();
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (grid[i][j] == '1') {
                roots.add(uf.find(i * cols + j));
            }
        }
    }
    
    return roots.size();
}
```

---

## 五、最短路径算法

### 7. Dijkstra 算法

**问题描述**

给定一个加权图，找出从起点到所有其他顶点的最短路径。

**思路分析**

```
贪心算法：
1. 初始化距离数组，起点距离为 0，其他为无穷大
2. 使用优先队列，每次选择距离最小的未访问顶点
3. 更新该顶点的邻接顶点的距离
4. 重复直到所有顶点都被访问
```

**Java 代码**

```java
/**
 * Dijkstra 算法（堆优化）
 * 时间：O((V + E) log V)
 * 空间：O(V)
 */
public int[] dijkstra(List<int[]>[] graph, int start) {
    int n = graph.length;
    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[start] = 0;
    
    // 优先队列：[距离, 顶点]
    PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[0] - b[0]);
    pq.offer(new int[]{0, start});
    
    while (!pq.isEmpty()) {
        int[] curr = pq.poll();
        int d = curr[0];
        int node = curr[1];
        
        // 如果已经找到更短的路径，跳过
        if (d > dist[node]) {
            continue;
        }
        
        // 更新邻接顶点的距离
        for (int[] edge : graph[node]) {
            int neighbor = edge[0];
            int weight = edge[1];
            
            if (dist[node] + weight < dist[neighbor]) {
                dist[neighbor] = dist[node] + weight;
                pq.offer(new int[]{dist[neighbor], neighbor});
            }
        }
    }
    
    return dist;
}
```

---

## 六、高频面试题总结

| 题目 | 难度 | 关键点 | 时间复杂度 |
|------|------|--------|-----------|
| BFS 最短路径 | ⭐ | 队列 | O(V + E) |
| DFS 遍历 | ⭐ | 递归/栈 | O(V + E) |
| 拓扑排序 | ⭐⭐ | Kahn 算法 | O(V + E) |
| 并查集 | ⭐⭐ | 路径压缩 + 按秩合并 | O(α(N)) |
| 岛屿数量 | ⭐⭐ | DFS/BFS/并查集 | O(V + E) |
| Dijkstra | ⭐⭐⭐ | 堆优化 | O((V + E) log V) |

---

## 七、面试建议

1. **掌握基础**：BFS、DFS、拓扑排序是必考题
2. **选择合适的表示**：稀疏图用邻接表，稠密图用邻接矩阵
3. **并查集**：路径压缩和按秩合并是关键优化
4. **最短路径**：Dijkstra 用于非负权重，Bellman-Ford 用于负权重
5. **代码规范**：边界条件、访问标记、环检测
6. **扩展思考**：强连通分量、最小生成树等高级算法
