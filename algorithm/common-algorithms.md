# 常见算法与数据结构 ⭐⭐⭐

## 面试题：手写几个常见算法

### 核心回答

算法是面试的硬通货，需要熟练掌握常见数据结构和算法。

---

## 一、数组与链表

### 1. 反转链表

```java
// 方法1：迭代法
public ListNode reverseList(ListNode head) {
    ListNode prev = null;
    ListNode curr = head;
    
    while (curr != null) {
        ListNode next = curr.next;  // 保存下一个节点
        curr.next = prev;            // 反转指针
        prev = curr;                // prev 前移
        curr = next;                // curr 前移
    }
    
    return prev;  // 新的头节点
}

// 方法2：递归法
public ListNode reverseListRecursively(ListNode head) {
    if (head == null || head.next == null) {
        return head;
    }
    
    ListNode newHead = reverseListRecursively(head.next);
    head.next.next = head;
    head.next = null;
    
    return newHead;
}

// 链表节点定义
class ListNode {
    int val;
    ListNode next;
    ListNode(int x) { val = x; }
}
```

### 2. 合并两个有序链表

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
    
    // 剩余部分
    curr.next = (l1 != null) ? l1 : l2;
    
    return dummy.next;
}
```

### 3. 两数之和

```java
// 方法1：暴力遍历 O(n²)
public int[] twoSum1(int[] nums, int target) {
    for (int i = 0; i < nums.length; i++) {
        for (int j = i + 1; j < nums.length; j++) {
            if (nums[i] + nums[j] == target) {
                return new int[]{i, j};
            }
        }
    }
    return new int[]{};
}

// 方法2：哈希表 O(n) - 推荐
public int[] twoSum2(int[] nums, int target) {
    Map<Integer, Integer> map = new HashMap<>();
    
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        if (map.containsKey(complement)) {
            return new int[]{map.get(complement), i};
        }
        map.put(nums[i], i);
    }
    
    return new int[]{};
}
```

---

## 二、栈与队列

### 1. 有效括号

```java
public boolean isValid(String s) {
    Stack<Character> stack = new Stack<>();
    
    for (char c : s.toCharArray()) {
        if (c == '(' || c == '{' || c == '[') {
            stack.push(c);
        } else {
            if (stack.isEmpty()) return false;
            
            char top = stack.pop();
            if ((c == ')' && top != '(') ||
                (c == '}' && top != '{') ||
                (c == ']' && top != '[')) {
                return false;
            }
        }
    }
    
    return stack.isEmpty();
}
```

### 2. 用栈实现队列

```java
class MyQueue {
    private Stack<Integer> stack1;  // 入队用
    private Stack<Integer> stack2;  // 出队用
    
    public MyQueue() {
        stack1 = new Stack<>();
        stack2 = new Stack<>();
    }
    
    public void push(int x) {
        stack1.push(x);
    }
    
    public int pop() {
        if (stack2.isEmpty()) {
            while (!stack1.isEmpty()) {
                stack2.push(stack1.pop());
            }
        }
        return stack2.isEmpty() ? -1 : stack2.pop();
    }
    
    public int peek() {
        if (stack2.isEmpty()) {
            while (!stack1.isEmpty()) {
                stack2.push(stack1.pop());
            }
        }
        return stack2.isEmpty() ? -1 : stack2.peek();
    }
    
    public boolean empty() {
        return stack1.isEmpty() && stack2.isEmpty();
    }
}
```

---

## 三、树

### 1. 二叉树遍历

```java
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode(int x) { val = x; }
}

// 前序遍历（根-左-右）
public List<Integer> preorderTraversal(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    preorder(root, result);
    return result;
}

private void preorder(TreeNode node, List<Integer> result) {
    if (node == null) return;
    result.add(node.val);
    preorder(node.left, result);
    preorder(node.right, result);
}

// 中序遍历（左-根-右）
public List<Integer> inorderTraversal(TreeNode root) {
    List<Integer> result = new ArrayList<>();
    inorder(root, result);
    return result;
}

private void inorder(TreeNode node, List<Integer> result) {
    if (node == null) return;
    inorder(node.left, result);
    result.add(node.val);
    inorder(node.right, result);
}

// 层序遍历（BFS）
public List<List<Integer>> levelOrder(TreeNode root) {
    List<List<Integer>> result = new ArrayList<>();
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
        result.add(level);
    }
    
    return result;
}
```

### 2. 二叉树最大深度

```java
// 方法1：递归
public int maxDepth(TreeNode root) {
    if (root == null) return 0;
    return Math.max(maxDepth(root.left), maxDepth(root.right)) + 1;
}

// 方法2：层序遍历
public int maxDepth2(TreeNode root) {
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
```

### 3. 验证二叉搜索树

```java
// 方法1：递归 + 上下界
public boolean isValidBST(TreeNode root) {
    return validate(root, null, null);
}

private boolean validate(TreeNode node, Integer min, Integer max) {
    if (node == null) return true;
    
    if (min != null && node.val <= min) return false;
    if (max != null && node.val >= max) return false;
    
    return validate(node.left, min, node.val) &&
           validate(node.right, node.val, max);
}

// 方法2：中序遍历（ BST 中序遍历是有序的）
public boolean isValidBST2(TreeNode root) {
    Stack<TreeNode> stack = new Stack<>();
    double inorder = -Double.MAX_VALUE;
    
    while (!stack.isEmpty() || root != null) {
        while (root != null) {
            stack.push(root);
            root = root.left;
        }
        
        root = stack.pop();
        if (root.val <= inorder) return false;
        inorder = root.val;
        root = root.right;
    }
    
    return true;
}
```

---

## 四、排序算法

### 1. 快速排序

```java
public void quickSort(int[] arr, int low, int high) {
    if (low < high) {
        int pivotIndex = partition(arr, low, high);
        quickSort(arr, low, pivotIndex - 1);
        quickSort(arr, pivotIndex + 1, high);
    }
}

private int partition(int[] arr, int low, int high) {
    int pivot = arr[high];  // 选择最后一个元素作为基准
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(arr, i, j);
        }
    }
    
    swap(arr, i + 1, high);
    return i + 1;
}

private void swap(int[] arr, int i, int j) {
    int temp = arr[i];
    arr[i] = arr[j];
    arr[j] = temp;
}
```

### 2. 归并排序

```java
public void mergeSort(int[] arr, int left, int right) {
    if (left < right) {
        int mid = (left + right) / 2;
        
        mergeSort(arr, left, mid);
        mergeSort(arr, mid + 1, right);
        merge(arr, left, mid, right);
    }
}

private void merge(int[] arr, int left, int mid, int right) {
    int[] temp = new int[right - left + 1];
    int i = left, j = mid + 1, k = 0;
    
    while (i <= mid && j <= right) {
        if (arr[i] <= arr[j]) {
            temp[k++] = arr[i++];
        } else {
            temp[k++] = arr[j++];
        }
    }
    
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];
    
    System.arraycopy(temp, 0, arr, left, temp.length);
}
```

### 3. 堆排序

```java
public void heapSort(int[] arr) {
    int n = arr.length;
    
    // 构建大顶堆
    for (int i = n / 2 - 1; i >= 0; i--) {
        heapify(arr, n, i);
    }
    
    // 逐个将堆顶元素移到末尾
    for (int i = n - 1; i > 0; i--) {
        swap(arr, 0, i);  // 堆顶移到末尾
        heapify(arr, i, 0);  // 调整堆
    }
}

private void heapify(int[] arr, int n, int i) {
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;
    
    if (left < n && arr[left] > arr[largest]) {
        largest = left;
    }
    if (right < n && arr[right] > arr[largest]) {
        largest = right;
    }
    
    if (largest != i) {
        swap(arr, i, largest);
        heapify(arr, n, largest);
    }
}
```

---

## 五、查找算法

### 1. 二分查找

```java
// 标准二分查找
public int binarySearch(int[] nums, int target) {
    int left = 0, right = nums.length - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;  // 防止溢出
        
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

// 查找左边界
public int lowerBound(int[] nums, int target) {
    int left = 0, right = nums.length;
    
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] < target) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    return left;
}

// 查找右边界
public int upperBound(int[] nums, int target) {
    int left = 0, right = nums.length;
    
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (nums[mid] <= target) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    return left - 1;
}
```

### 2. 旋转数组查找

```java
public int search(int[] nums, int target) {
    if (nums == null || nums.length == 0) return -1;
    
    int left = 0, right = nums.length - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (nums[mid] == target) {
            return mid;
        }
        
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
```

---

## 六、高级数据结构

### 1. LRU 缓存

```java
class LRUCache {
    private Map<Integer, Integer> cache;
    private int capacity;
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new LinkedHashMap<Integer, Integer>(capacity, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry eldest) {
                return size() > LRUCache.this.capacity;
            }
        };
    }
    
    public int get(int key) {
        return cache.getOrDefault(key, -1);
    }
    
    public void put(int key, int value) {
        cache.put(key, value);
    }
}
```

### 2. 并查集（Union-Find）

```java
class UnionFind {
    private int[] parent;
    private int[] rank;
    
    public UnionFind(int size) {
        parent = new int[size];
        rank = new int[size];
        for (int i = 0; i < size; i++) {
            parent[i] = i;
            rank[i] = 1;
        }
    }
    
    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // 路径压缩
        }
        return parent[x];
    }
    
    public void union(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return;
        
        // 按秩合并
        if (rank[px] < rank[py]) {
            parent[px] = py;
        } else if (rank[px] > rank[py]) {
            parent[py] = px;
        } else {
            parent[py] = px;
            rank[px]++;
        }
    }
    
    public boolean connected(int x, int y) {
        return find(x) == find(y);
    }
}
```

---

## 七、算法复杂度速查

| 算法 | 时间复杂度（平均） | 时间复杂度（最坏） | 空间复杂度 |
|------|------------------|-------------------|-----------|
| 冒泡排序 | O(n²) | O(n²) | O(1) |
| 选择排序 | O(n²) | O(n²) | O(1) |
| 插入排序 | O(n²) | O(n²) | O(1) |
| 归并排序 | O(n log n) | O(n log n) | O(n) |
| 快速排序 | O(n log n) | O(n²) | O(log n) |
| 堆排序 | O(n log n) | O(n log n) | O(1) |
| 希尔排序 | O(n^1.3) | O(n²) | O(1) |
| 计数排序 | O(n + k) | O(n + k) | O(k) |
| 基数排序 | O(nk) | O(nk) | O(n + k) |
| 桶排序 | O(n + k) | O(n²) | O(n + k) |
| 二分查找 | O(log n) | O(log n) | O(1) |

| 数据结构 | 查询 | 插入 | 删除 |
|---------|------|------|------|
| 数组 | O(1) | O(n) | O(n) |
| 链表 | O(n) | O(1) | O(1) |
| 栈 | O(n) | O(1) | O(1) |
| 队列 | O(n) | O(1) | O(1) |
| 哈希表 | O(1) | O(1) | O(1) |
| 二叉搜索树 | O(log n) | O(log n) | O(log n) |
| 平衡二叉树 | O(log n) | O(log n) | O(log n) |
| 堆 | O(1) | O(log n) | O(log n) |

---

**参考链接：**
- [LeetCode 热题 100](https://leetcode.cn/problem-list/hot-100/)
- [剑指 Offer](https://leetcode.cn/problem-list/lcof/)
