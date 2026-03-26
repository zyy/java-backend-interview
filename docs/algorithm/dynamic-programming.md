---
layout: default
title: 动态规划（DP）解题套路详解 ⭐⭐⭐
---
# 动态规划（DP）解题套路详解 ⭐⭐⭐

## 🎯 面试题：动态规划是算法面试最难也最重要的高频考点

---

## 一、DP 核心思想

### 什么是动态规划？

```
动态规划（Dynamic Programming）是一种通过把原问题分解为相对简单的子问题的方式求解复杂问题的方法。

核心三要素：
  1. 最优子结构：问题的最优解包含子问题的最优解
  2. 状态转移方程：描述状态之间的转换关系（核心！）
  3. 重叠子问题：子问题会被重复计算，需要记忆化

与递归的区别：
  - 递归：自顶向下，可能重复计算子问题
  - DP：自底向上，通过填表避免重复计算
```

### DP vs 其他算法

| 算法 | 思想 | 适用场景 |
|------|------|---------|
| **分治** | 分解独立子问题，合并结果 | 子问题不重叠（归并排序、快排） |
| **贪心** | 每步局部最优 | 局部最优能推导全局最优 |
| **DP** | 记忆化重叠子问题 | 子问题重叠、有最优子结构 |
| **回溯** | 暴力搜索所有可能 | 找所有解、组合排列问题 |

---

## 二、DP 解题四步法（万能套路）

```
步骤一：定义状态
  - 明确 dp[i] 或 dp[i][j] 代表什么
  - 状态定义决定了后续一切

步骤二：找状态转移方程
  - 思考：当前状态怎么由之前的状态推导出来？
  - dp[i] = f(dp[i-1], dp[i-2], ...)

步骤三：初始化
  - 边界条件：dp[0], dp[1] 等基础情况
  - 防止数组越界

步骤四：确定遍历顺序并填表
  - 一维：从左到右 or 从右到左
  - 二维：从上到下、从左到右
  - 原则：计算 dp[i] 时，依赖的状态已经计算过
```

### 四步法示例：爬楼梯

```
问题：每次可以爬 1 或 2 个台阶，问爬到第 n 阶有多少种方法？

步骤一：定义状态
  dp[i] = 爬到第 i 阶的方法数

步骤二：状态转移方程
  到第 i 阶可以从第 i-1 阶爬 1 步，或从第 i-2 阶爬 2 步
  dp[i] = dp[i-1] + dp[i-2]

步骤三：初始化
  dp[0] = 1  （在地面，算 1 种方法）
  dp[1] = 1  （爬 1 阶，只有 1 种方法）

步骤四：填表
  for i = 2 to n:
    dp[i] = dp[i-1] + dp[i-2]
```

```java
/**
 * 爬楼梯（斐波那契数列）
 * 时间：O(n)
 * 空间：O(n) → 优化后 O(1)
 */
public int climbStairs(int n) {
    if (n <= 1) return 1;

    // 完整版本
    int[] dp = new int[n + 1];
    dp[0] = 1;
    dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }
    return dp[n];
}

/**
 * 空间优化版本：只用两个变量
 */
public int climbStairsOptimized(int n) {
    if (n <= 1) return 1;

    int prev2 = 1;  // dp[i-2]
    int prev1 = 1;  // dp[i-1]

    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

---

## 三、基础问题

### 3.1 斐波那契数列

```
问题：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)，求 F(n)

分析：
  - 典型的重叠子问题
  - 递归时间复杂度 O(2^n)，存在大量重复计算
  - DP 时间复杂度 O(n)
```

```java
/**
 * 斐波那契数列 - DP 解法
 * 时间：O(n)
 * 空间：O(1)
 */
public int fib(int n) {
    if (n <= 1) return n;

    int prev2 = 0;  // F(0)
    int prev1 = 1;  // F(1)

    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}

/**
 * 斐波那契 - 矩阵快速幂解法
 * 时间：O(log n)
 * 空间：O(1)
 * 原理：[F(n+1), F(n)] = [F(1), F(0)] * [[1,1],[1,0]]^n
 */
public int fibMatrix(int n) {
    if (n <= 1) return n;

    int[][] matrix = {{1, 1}, {1, 0}};
    int[][] result = matrixPow(matrix, n - 1);
    return result[0][0];
}

private int[][] matrixPow(int[][] m, int n) {
    int[][] result = {{1, 0}, {0, 1}}; // 单位矩阵
    while (n > 0) {
        if ((n & 1) == 1) {
            result = multiply(result, m);
        }
        m = multiply(m, m);
        n >>= 1;
    }
    return result;
}

private int[][] multiply(int[][] a, int[][] b) {
    int[][] c = new int[2][2];
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            c[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j];
        }
    }
    return c;
}
```

### 3.2 打家劫舍

```
问题：不能偷相邻的房子，求能偷到的最大金额

示例：[1, 2, 3, 1] → 偷 1+3=4 或 2+1=3，最大 4

分析：
  - 对于第 i 家，有两种选择：偷或不偷
  - 偷：dp[i] = dp[i-2] + nums[i]（不能偷相邻的）
  - 不偷：dp[i] = dp[i-1]
  - 取两者最大值
```

```java
/**
 * 打家劫舍 I
 * 时间：O(n)
 * 空间：O(1)
 */
public int rob(int[] nums) {
    if (nums == null || nums.length == 0) return 0;
    if (nums.length == 1) return nums[0];

    int prev2 = 0;   // dp[i-2]
    int prev1 = 0;   // dp[i-1]

    for (int num : nums) {
        int curr = Math.max(prev1, prev2 + num);
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

### 3.3 打家劫舍 II（环形）

```
问题：房子围成一圈，首尾相连

分析：
  - 分两种情况：偷第一家 / 不偷第一家
  - 情况1：偷第一家 → 不能偷最后一家 → 考虑 [0, n-2]
  - 情况2：不偷第一家 → 可以偷最后一家 → 考虑 [1, n-1]
  - 取两种情况的最大值
```

```java
/**
 * 打家劫舍 II（环形）
 * 时间：O(n)
 * 空间：O(1)
 */
public int rob2(int[] nums) {
    if (nums == null || nums.length == 0) return 0;
    if (nums.length == 1) return nums[0];
    if (nums.length == 2) return Math.max(nums[0], nums[1]);

    // 情况1：偷第一家，不偷最后一家
    int case1 = robRange(nums, 0, nums.length - 2);
    // 情况2：不偷第一家，可以偷最后一家
    int case2 = robRange(nums, 1, nums.length - 1);

    return Math.max(case1, case2);
}

private int robRange(int[] nums, int start, int end) {
    int prev2 = 0;
    int prev1 = 0;

    for (int i = start; i <= end; i++) {
        int curr = Math.max(prev1, prev2 + nums[i]);
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

---

## 四、路径问题

### 4.1 不同路径

```
问题：m×n 网格，从左上角走到右下角，每次只能向右或向下，有多少种路径？

分析：
  - 到达 (i, j) 只能从 (i-1, j) 或 (i, j-1)
  - dp[i][j] = dp[i-1][j] + dp[i][j-1]
  - 边界：第一行和第一列都是 1（只有一种走法）
```

```java
/**
 * 不同路径
 * 时间：O(m×n)
 * 空间：O(m×n) → 优化后 O(n)
 */
public int uniquePaths(int m, int n) {
    int[][] dp = new int[m][n];

    // 初始化：第一行和第一列都是 1
    for (int i = 0; i < m; i++) dp[i][0] = 1;
    for (int j = 0; j < n; j++) dp[0][j] = 1;

    // 填表
    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1];
        }
    }
    return dp[m - 1][n - 1];
}

/**
 * 空间优化：一维数组
 */
public int uniquePathsOptimized(int m, int n) {
    int[] dp = new int[n];
    Arrays.fill(dp, 1);  // 第一行全是 1

    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            // dp[j] 相当于 dp[i-1][j]（上一行）
            // dp[j-1] 相当于 dp[i][j-1]（当前行左边）
            dp[j] = dp[j] + dp[j - 1];
        }
    }
    return dp[n - 1];
}
```

### 4.2 最小路径和

```
问题：m×n 网格，每个格子有数字，找从左上到右下的最小路径和

分析：
  - dp[i][j] = min(dp[i-1][j], dp[i][j-1]) + grid[i][j]
  - 边界：第一行只能从左边来，第一列只能从上边来
```

```java
/**
 * 最小路径和
 * 时间：O(m×n)
 * 空间：O(1) 原地修改
 */
public int minPathSum(int[][] grid) {
    if (grid == null || grid.length == 0) return 0;

    int m = grid.length;
    int n = grid[0].length;

    // 初始化第一行
    for (int j = 1; j < n; j++) {
        grid[0][j] += grid[0][j - 1];
    }

    // 初始化第一列
    for (int i = 1; i < m; i++) {
        grid[i][0] += grid[i - 1][0];
    }

    // 填表
    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) {
            grid[i][j] += Math.min(grid[i - 1][j], grid[i][j - 1]);
        }
    }

    return grid[m - 1][n - 1];
}

/**
 * 不修改原数组的版本
 */
public int minPathSumNoModify(int[][] grid) {
    if (grid == null || grid.length == 0) return 0;

    int m = grid.length;
    int n = grid[0].length;
    int[] dp = new int[n];

    dp[0] = grid[0][0];
    for (int j = 1; j < n; j++) {
        dp[j] = dp[j - 1] + grid[0][j];
    }

    for (int i = 1; i < m; i++) {
        dp[0] += grid[i][0];  // 第一列特殊处理
        for (int j = 1; j < n; j++) {
            dp[j] = Math.min(dp[j], dp[j - 1]) + grid[i][j];
        }
    }

    return dp[n - 1];
}
```

---

## 五、股票系列（面试高频！）

### 5.1 买卖股票的最佳时机 I（只能买卖一次）

```
问题：只能买卖一次，求最大利润

分析：
  - 维护一个最小价格 minPrice
  - 每天的利润 = 当前价格 - minPrice
  - dp[i] = max(dp[i-1], prices[i] - minPrice)
```

```java
/**
 * 买卖股票 I（一次交易）
 * 时间：O(n)
 * 空间：O(1)
 */
public int maxProfit1(int[] prices) {
    if (prices == null || prices.length < 2) return 0;

    int minPrice = prices[0];
    int maxProfit = 0;

    for (int i = 1; i < prices.length; i++) {
        minPrice = Math.min(minPrice, prices[i]);
        maxProfit = Math.max(maxProfit, prices[i] - minPrice);
    }

    return maxProfit;
}
```

### 5.2 买卖股票的最佳时机 II（无限次交易）

```
问题：可以买卖无限次，但必须先卖再买

分析：
  - 只要今天比昨天贵，就买卖
  - 贪心思想：所有上涨都吃进
```

```java
/**
 * 买卖股票 II（无限次交易）
 * 时间：O(n)
 * 空间：O(1)
 */
public int maxProfit2(int[] prices) {
    if (prices == null || prices.length < 2) return 0;

    int maxProfit = 0;
    for (int i = 1; i < prices.length; i++) {
        if (prices[i] > prices[i - 1]) {
            maxProfit += prices[i] - prices[i - 1];
        }
    }
    return maxProfit;
}

/**
 * DP 解法（通用思路）
 * dp[i][0] = 第 i 天不持有股票的最大利润
 * dp[i][1] = 第 i 天持有股票的最大利润
 */
public int maxProfit2DP(int[] prices) {
    int n = prices.length;
    int[][] dp = new int[n][2];

    dp[0][0] = 0;            // 第一天不持有
    dp[0][1] = -prices[0];   // 第一天持有（买入）

    for (int i = 1; i < n; i++) {
        dp[i][0] = Math.max(dp[i - 1][0], dp[i - 1][1] + prices[i]);
        dp[i][1] = Math.max(dp[i - 1][1], dp[i - 1][0] - prices[i]);
    }

    return dp[n - 1][0];
}
```

### 5.3 买卖股票的最佳时机 III（最多两次交易）

```
问题：最多买卖两次

分析：
  - 定义四个状态：
    buy1: 第一次买入后的最大利润
    sell1: 第一次卖出后的最大利润
    buy2: 第二次买入后的最大利润
    sell2: 第二次卖出后的最大利润
```

```java
/**
 * 买卖股票 III（最多两次交易）
 * 时间：O(n)
 * 空间：O(1)
 */
public int maxProfit3(int[] prices) {
    if (prices == null || prices.length < 2) return 0;

    int buy1 = -prices[0];   // 第一次买入
    int sell1 = 0;           // 第一次卖出
    int buy2 = -prices[0];   // 第二次买入（用第一次卖出的钱）
    int sell2 = 0;           // 第二次卖出

    for (int i = 1; i < prices.length; i++) {
        buy1 = Math.max(buy1, -prices[i]);
        sell1 = Math.max(sell1, buy1 + prices[i]);
        buy2 = Math.max(buy2, sell1 - prices[i]);
        sell2 = Math.max(sell2, buy2 + prices[i]);
    }

    return sell2;
}
```

### 5.4 买卖股票的最佳时机 IV（最多 K 次交易）

```
问题：最多买卖 K 次

分析：
  - 当 K >= n/2 时，相当于无限次交易
  - 否则用 DP，定义两个数组：
    buy[k] = 第 k 次买入后的最大利润
    sell[k] = 第 k 次卖出后的最大利润
```

```java
/**
 * 买卖股票 IV（最多 K 次交易）
 * 时间：O(n×k)
 * 空间：O(k)
 */
public int maxProfit4(int k, int[] prices) {
    if (prices == null || prices.length < 2 || k <= 0) return 0;

    int n = prices.length;

    // 如果 K >= n/2，相当于无限次交易
    if (k >= n / 2) {
        return maxProfit2(prices);  // 调用无限次交易的解法
    }

    int[] buy = new int[k + 1];
    int[] sell = new int[k + 1];

    Arrays.fill(buy, -prices[0]);

    for (int i = 1; i < n; i++) {
        for (int j = 1; j <= k; j++) {
            buy[j] = Math.max(buy[j], sell[j - 1] - prices[i]);
            sell[j] = Math.max(sell[j], buy[j] + prices[i]);
        }
    }

    return sell[k];
}
```

### 5.5 买卖股票含冷冻期

```
问题：无限次交易，但卖出后第二天不能买入（冷冻期）

分析：
  - 三个状态：
    hold: 持有股票
    sold: 刚卖出（在冷冻期）
    rest: 不持有且不在冷冻期
```

```java
/**
 * 买卖股票含冷冻期
 * 时间：O(n)
 * 空间：O(1)
 */
public int maxProfitWithCooldown(int[] prices) {
    if (prices == null || prices.length < 2) return 0;

    int hold = -prices[0];   // 持有股票
    int sold = 0;            // 刚卖出（冷冻期）
    int rest = 0;            // 不持有，不在冷冻期

    for (int i = 1; i < prices.length; i++) {
        int prevSold = sold;

        hold = Math.max(hold, rest - prices[i]);
        sold = hold + prices[i];
        rest = Math.max(rest, prevSold);
    }

    return Math.max(sold, rest);
}
```

---

## 六、子序列问题

### 6.1 最长公共子序列（LCS）

```
问题：两个字符串的最长公共子序列长度

分析：
  - dp[i][j] = text1[0..i-1] 和 text2[0..j-1] 的 LCS 长度
  - 如果 text1[i-1] == text2[j-1]:
      dp[i][j] = dp[i-1][j-1] + 1
  - 否则:
      dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

```java
/**
 * 最长公共子序列
 * 时间：O(m×n)
 * 空间：O(m×n)
 */
public int longestCommonSubsequence(String text1, String text2) {
    int m = text1.length();
    int n = text2.length();
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1.charAt(i - 1) == text2.charAt(j - 1)) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    return dp[m][n];
}

/**
 * 空间优化：滚动数组
 */
public int longestCommonSubsequenceOptimized(String text1, String text2) {
    int m = text1.length();
    int n = text2.length();

    // 确保 n 较小，节省空间
    if (m < n) {
        return longestCommonSubsequenceOptimized(text2, text1);
    }

    int[] dp = new int[n + 1];

    for (int i = 1; i <= m; i++) {
        int prev = 0;  // dp[i-1][j-1]
        for (int j = 1; j <= n; j++) {
            int temp = dp[j];  // 保存当前 dp[i-1][j]
            if (text1.charAt(i - 1) == text2.charAt(j - 1)) {
                dp[j] = prev + 1;
            } else {
                dp[j] = Math.max(dp[j], dp[j - 1]);
            }
            prev = temp;
        }
    }

    return dp[n];
}
```

### 6.2 最长递增子序列（LIS）

```
问题：最长严格递增子序列的长度

解法一：O(n²) DP
  - dp[i] = 以 nums[i] 结尾的 LIS 长度
  - dp[i] = max(dp[j] + 1)，其中 j < i 且 nums[j] < nums[i]

解法二：O(n log n) 贪心+二分
  - 维护一个有序数组 tails
  - tails[i] = 长度为 i+1 的递增子序列的最小末尾元素
  - 每次用二分找到插入位置
```

```java
/**
 * LIS - O(n²) 解法
 * 时间：O(n²)
 * 空间：O(n)
 */
public int lengthOfLIS(int[] nums) {
    if (nums == null || nums.length == 0) return 0;

    int n = nums.length;
    int[] dp = new int[n];
    Arrays.fill(dp, 1);

    int maxLen = 1;
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (nums[j] < nums[i]) {
                dp[i] = Math.max(dp[i], dp[j] + 1);
            }
        }
        maxLen = Math.max(maxLen, dp[i]);
    }

    return maxLen;
}

/**
 * LIS - O(n log n) 解法（推荐）
 * 时间：O(n log n)
 * 空间：O(n)
 */
public int lengthOfLISOptimized(int[] nums) {
    if (nums == null || nums.length == 0) return 0;

    int n = nums.length;
    int[] tails = new int[n];
    int size = 0;

    for (int num : nums) {
        int left = 0, right = size;
        // 二分查找第一个 >= num 的位置
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (tails[mid] < num) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }

        tails[left] = num;
        if (left == size) {
            size++;
        }
    }

    return size;
}

/**
 * 输出最长递增子序列本身
 */
public List<Integer> getLIS(int[] nums) {
    if (nums == null || nums.length == 0) return new ArrayList<>();

    int n = nums.length;
    int[] dp = new int[n];
    int[] prev = new int[n];  // 记录前驱索引
    Arrays.fill(dp, 1);
    Arrays.fill(prev, -1);

    int maxLen = 1, maxIdx = 0;
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (nums[j] < nums[i] && dp[j] + 1 > dp[i]) {
                dp[i] = dp[j] + 1;
                prev[i] = j;
            }
        }
        if (dp[i] > maxLen) {
            maxLen = dp[i];
            maxIdx = i;
        }
    }

    // 回溯构造 LIS
    LinkedList<Integer> result = new LinkedList<>();
    while (maxIdx != -1) {
        result.addFirst(nums[maxIdx]);
        maxIdx = prev[maxIdx];
    }

    return result;
}
```

### 6.3 编辑距离

```
问题：将 word1 转换成 word2 的最少操作数（插入、删除、替换）

分析：
  - dp[i][j] = word1[0..i-1] 转换到 word2[0..j-1] 的最小编辑距离
  - 如果 word1[i-1] == word2[j-1]:
      dp[i][j] = dp[i-1][j-1]  （无需操作）
  - 否则:
      dp[i][j] = min(
        dp[i-1][j] + 1,    // 删除 word1[i-1]
        dp[i][j-1] + 1,    // 插入 word2[j-1]
        dp[i-1][j-1] + 1   // 替换
      )
```

```java
/**
 * 编辑距离
 * 时间：O(m×n)
 * 空间：O(m×n)
 */
public int minDistance(String word1, String word2) {
    int m = word1.length();
    int n = word2.length();

    int[][] dp = new int[m + 1][n + 1];

    // 初始化：从空字符串转换
    for (int i = 0; i <= m; i++) dp[i][0] = i;  // 全部删除
    for (int j = 0; j <= n; j++) dp[0][j] = j;  // 全部插入

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (word1.charAt(i - 1) == word2.charAt(j - 1)) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = Math.min(
                    Math.min(dp[i - 1][j], dp[i][j - 1]),
                    dp[i - 1][j - 1]
                ) + 1;
            }
        }
    }

    return dp[m][n];
}

/**
 * 空间优化：滚动数组
 */
public int minDistanceOptimized(String word1, String word2) {
    int m = word1.length();
    int n = word2.length();

    int[] dp = new int[n + 1];

    for (int j = 0; j <= n; j++) dp[j] = j;

    for (int i = 1; i <= m; i++) {
        int prev = dp[0];
        dp[0] = i;  // 第一列

        for (int j = 1; j <= n; j++) {
            int temp = dp[j];
            if (word1.charAt(i - 1) == word2.charAt(j - 1)) {
                dp[j] = prev;
            } else {
                dp[j] = Math.min(Math.min(dp[j], dp[j - 1]), prev) + 1;
            }
            prev = temp;
        }
    }

    return dp[n];
}
```

---

## 七、背包问题

### 7.1 0-1 背包

```
问题：N 个物品，每个物品有重量 w[i] 和价值 v[i]，背包容量 W
     每个物品只能选择一次，求最大价值

分析：
  - dp[i][j] = 前 i 个物品放入容量为 j 的背包的最大价值
  - 对于第 i 个物品：
    不选：dp[i][j] = dp[i-1][j]
    选：  dp[i][j] = dp[i-1][j-w[i]] + v[i]（前提是 j >= w[i]）
  - dp[i][j] = max(不选, 选)
```

```java
/**
 * 0-1 背包 - 标准解法
 * 时间：O(N×W)
 * 空间：O(N×W)
 */
public int knapsack01(int[] weights, int[] values, int capacity) {
    int n = weights.length;
    int[][] dp = new int[n + 1][capacity + 1];

    for (int i = 1; i <= n; i++) {
        for (int j = 0; j <= capacity; j++) {
            dp[i][j] = dp[i - 1][j];  // 不选第 i 个物品
            if (j >= weights[i - 1]) {
                dp[i][j] = Math.max(dp[i][j],
                    dp[i - 1][j - weights[i - 1]] + values[i - 1]);
            }
        }
    }

    return dp[n][capacity];
}

/**
 * 0-1 背包 - 空间优化（一维）
 * 注意：容量必须从大到小遍历！
 */
public int knapsack01Optimized(int[] weights, int[] values, int capacity) {
    int n = weights.length;
    int[] dp = new int[capacity + 1];

    for (int i = 0; i < n; i++) {
        // 从大到小遍历，避免重复选择
        for (int j = capacity; j >= weights[i]; j--) {
            dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
        }
    }

    return dp[capacity];
}

/**
 * 应用：分割等和子集
 * 给定数组，能否分成两个和相等的子集
 */
public boolean canPartition(int[] nums) {
    int sum = 0;
    for (int num : nums) sum += num;

    if (sum % 2 != 0) return false;

    int target = sum / 2;
    boolean[] dp = new boolean[target + 1];
    dp[0] = true;

    for (int num : nums) {
        for (int j = target; j >= num; j--) {
            dp[j] = dp[j] || dp[j - num];
        }
    }

    return dp[target];
}
```

### 7.2 完全背包

```
问题：每个物品可以选择无限次

分析：
  - 与 0-1 背包的区别：容量从小到大遍历
  - 这样可以重复选择同一个物品
```

```java
/**
 * 完全背包
 * 时间：O(N×W)
 * 空间：O(W)
 */
public int knapsackComplete(int[] weights, int[] values, int capacity) {
    int[] dp = new int[capacity + 1];

    for (int i = 0; i < weights.length; i++) {
        // 从小到大遍历，允许重复选择
        for (int j = weights[i]; j <= capacity; j++) {
            dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
        }
    }

    return dp[capacity];
}

/**
 * 应用：零钱兑换（完全背包求方案数）
 */
public int coinChange(int[] coins, int amount) {
    int[] dp = new int[amount + 1];
    Arrays.fill(dp, amount + 1);  // 初始化为无穷大
    dp[0] = 0;

    for (int coin : coins) {
        for (int j = coin; j <= amount; j++) {
            dp[j] = Math.min(dp[j], dp[j - coin] + 1);
        }
    }

    return dp[amount] > amount ? -1 : dp[amount];
}

/**
 * 应用：零钱兑换 II（求组合数）
 */
public int change(int amount, int[] coins) {
    int[] dp = new int[amount + 1];
    dp[0] = 1;

    for (int coin : coins) {
        for (int j = coin; j <= amount; j++) {
            dp[j] += dp[j - coin];
        }
    }

    return dp[amount];
}
```

### 7.3 多重背包

```
问题：第 i 个物品最多选择 num[i] 次

分析：
  - 将多重背包转化为 0-1 背包
  - 二进制优化：将 num[i] 拆分成 1, 2, 4, 8, ... 的组合
```

```java
/**
 * 多重背包 - 二进制优化
 * 时间：O(N×W×log(num))
 */
public int knapsackMultiple(int[] weights, int[] values, int[] counts, int capacity) {
    int[] dp = new int[capacity + 1];

    for (int i = 0; i < weights.length; i++) {
        // 二进制拆分
        int count = counts[i];
        for (int k = 1; k <= count; k *= 2) {
            int w = weights[i] * k;
            int v = values[i] * k;

            for (int j = capacity; j >= w; j--) {
                dp[j] = Math.max(dp[j], dp[j - w] + v);
            }

            count -= k;
        }

        // 剩余部分
        if (count > 0) {
            int w = weights[i] * count;
            int v = values[i] * count;
            for (int j = capacity; j >= w; j--) {
                dp[j] = Math.max(dp[j], dp[j - w] + v);
            }
        }
    }

    return dp[capacity];
}
```

---

## 八、字符串问题

### 8.1 正则表达式匹配

```
问题：实现 '.' 匹配任意字符，'*' 匹配前一个字符 0 次或多次

分析：
  - dp[i][j] = s[0..i-1] 是否匹配 p[0..j-1]
  - 如果 p[j-1] != '*':
      dp[i][j] = dp[i-1][j-1] && (s[i-1] == p[j-1] || p[j-1] == '.')
  - 如果 p[j-1] == '*':
      匹配 0 次：dp[i][j] = dp[i][j-2]
      匹配 1+ 次：dp[i][j] = dp[i-1][j] && (s[i-1] == p[j-2] || p[j-2] == '.')
```

```java
/**
 * 正则表达式匹配
 * 时间：O(m×n)
 * 空间：O(m×n)
 */
public boolean isMatch(String s, String p) {
    int m = s.length();
    int n = p.length();

    boolean[][] dp = new boolean[m + 1][n + 1];
    dp[0][0] = true;

    // 初始化：匹配空字符串
    for (int j = 2; j <= n; j++) {
        if (p.charAt(j - 1) == '*') {
            dp[0][j] = dp[0][j - 2];
        }
    }

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            char sc = s.charAt(i - 1);
            char pc = p.charAt(j - 1);

            if (pc == '*') {
                // 匹配 0 次
                dp[i][j] = dp[i][j - 2];
                // 匹配 1+ 次
                if (s.charAt(i - 1) == p.charAt(j - 2) || p.charAt(j - 2) == '.') {
                    dp[i][j] = dp[i][j] || dp[i - 1][j];
                }
            } else {
                dp[i][j] = dp[i - 1][j - 1] &&
                          (sc == pc || pc == '.');
            }
        }
    }

    return dp[m][n];
}
```

### 8.2 括号生成

```
问题：生成所有有效的括号组合（n 对括号）

分析：
  - 这不是典型的 DP 问题，但可以用 DP 思路
  - 对于 n 对括号，第一个括号内放 k 对，括号外放 n-1-k 对
  - dp[n] = "(" + dp[k] + ")" + dp[n-1-k]
```

```java
/**
 * 括号生成 - DP 解法
 */
public List<String> generateParenthesis(int n) {
    List<List<String>> dp = new ArrayList<>();
    dp.add(Collections.singletonList(""));  // dp[0]

    for (int i = 1; i <= n; i++) {
        List<String> current = new ArrayList<>();
        for (int k = 0; k < i; k++) {
            // 括号内 k 对，括号外 i-1-k 对
            for (String inside : dp.get(k)) {
                for (String outside : dp.get(i - 1 - k)) {
                    current.add("(" + inside + ")" + outside);
                }
            }
        }
        dp.add(current);
    }

    return dp.get(n);
}

/**
 * 括号生成 - 回溯解法（更直观）
 */
public List<String> generateParenthesisBacktrack(int n) {
    List<String> result = new ArrayList<>();
    backtrack(result, "", 0, 0, n);
    return result;
}

private void backtrack(List<String> result, String current, int open, int close, int max) {
    if (current.length() == max * 2) {
        result.add(current);
        return;
    }

    if (open < max) {
        backtrack(result, current + "(", open + 1, close, max);
    }
    if (close < open) {  // 右括号不能多于左括号
        backtrack(result, current + ")", open, close + 1, max);
    }
}
```

---

## 九、空间优化技巧

### 9.1 一维 DP → 滚动变量

```
当 dp[i] 只依赖于 dp[i-1], dp[i-2] 等有限几个状态时，
可以用变量代替数组，将空间从 O(n) 降到 O(1)

示例：斐波那契、爬楼梯、打家劫舍

优化前：
  int[] dp = new int[n];
  dp[0] = 1; dp[1] = 1;
  for (int i = 2; i < n; i++) dp[i] = dp[i-1] + dp[i-2];

优化后：
  int prev2 = 1, prev1 = 1;
  for (int i = 2; i < n; i++) {
    int curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
```

### 9.2 二维 DP → 一维数组

```
当 dp[i][j] 只依赖于 dp[i-1][...] 或 dp[...][j-1] 时，
可以用一维数组滚动更新

示例：不同路径、最小路径和、LCS

优化前：
  int[][] dp = new int[m][n];
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < n; j++) {
      dp[i][j] = dp[i-1][j] + dp[i][j-1];
    }
  }

优化后：
  int[] dp = new int[n];
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < n; j++) {
      dp[j] = dp[j] + dp[j-1];  // dp[j] 是上一行的值
    }
  }
```

### 9.3 滚动数组（交替更新）

```
当需要保留完整的二维状态，但空间受限时，
可以用两行数组交替更新

int[][] dp = new int[2][n];
int curr = 0;
for (int i = 0; i < m; i++) {
  int prev = curr;
  curr = 1 - curr;
  for (int j = 0; j < n; j++) {
    dp[curr][j] = dp[prev][j] + ...;
  }
}
```

---

## 十、高频面试题

### Q1: DP 和递归有什么区别？

> DP 是递归的优化版本。递归自顶向下，存在大量重复计算；DP 自底向上，通过填表避免重复。时间复杂度上，递归可能指数级，DP 通常多项式级。

### Q2: 什么时候用 DP，什么时候用贪心？

> 贪心要求每一步的局部最优能推导全局最优，适用范围窄但效率高。DP 适用于有重叠子问题和最优子结构的问题，更通用。不确定时先尝试 DP，如果发现贪心性质再优化。

### Q3: 0-1 背包和完全背包的核心区别？

> 0-1 背包每件物品只能选一次，容量从大到小遍历；完全背包每件物品可选无限次，容量从小到大遍历。遍历顺序决定了是否允许重复选择。

### Q4: 股票系列问题的通用 DP 思路？

> 定义状态：dp[i][k][0/1] 表示第 i 天、完成 k 次交易、持有/不持有股票的最大利润。状态转移涉及买入（k 不变）、卖出（k+1）两个动作。根据交易次数限制和冷冻期条件调整转移方程。

### Q5: 如何判断一道题是否用 DP？

> 检查三个特征：(1) 最优子结构——问题的最优解包含子问题的最优解；(2) 重叠子问题——子问题会被重复计算；(3) 无后效性——当前状态确定后，之后的发展与之前如何到达当前状态无关。

### Q6: 最长递增子序列的 O(n log n) 解法原理？

> 维护数组 tails，tails[i] 表示长度为 i+1 的递增子序列的最小末尾元素。新元素用二分找到插入位置，如果比所有元素都大就扩展数组。最终数组长度就是 LIS 长度。贪心思想：末尾越小，后面能接的元素越多。

---

## 十一、DP 问题分类速查表

| 类型 | 代表题目 | 核心状态定义 | 状态转移 |
|------|---------|-------------|---------|
| **线性 DP** | 爬楼梯、打家劫舍 | dp[i] = 第 i 位置的解 | dp[i] = f(dp[i-1], dp[i-2]) |
| **路径 DP** | 不同路径、最小路径和 | dp[i][j] = 到达 (i,j) 的解 | dp[i][j] = f(dp[i-1][j], dp[i][j-1]) |
| **区间 DP** | 回文子串、矩阵链乘 | dp[i][j] = 区间 [i,j] 的解 | dp[i][j] = f(dp[i][k], dp[k+1][j]) |
| **背包 DP** | 0-1背包、完全背包 | dp[j] = 容量 j 的最大价值 | dp[j] = max(dp[j], dp[j-w]+v) |
| **子序列 DP** | LCS、LIS、编辑距离 | dp[i][j] = 子问题的解 | 取决于字符是否匹配 |
| **状态机 DP** | 股票系列 | dp[i][k][state] | 根据买卖操作转移 |
| **树形 DP** | 打家劫舍 III | dp[node][state] | 后序遍历合并子树结果 |

---

## 十二、学习路径建议

```
入门阶段（1-2 周）：
  1. 爬楼梯、斐波那契（理解状态定义）
  2. 打家劫舍（简单状态转移）
  3. 不同路径（二维 DP 入门）

进阶阶段（2-4 周）：
  4. 最小路径和（二维 DP + 空间优化）
  5. 最长公共子序列（经典二维 DP）
  6. 最长递增子序列（O(n²) 和 O(n log n) 两种解法）
  7. 编辑距离（经典字符串 DP）

专题突破（按需）：
  8. 股票系列（状态机 DP）
  9. 背包系列（0-1、完全、多重）
  10. 区间 DP（矩阵链乘、回文）

刷题顺序：
  LeetCode 热题 100 中的 DP 题
  → 按标签刷：动态规划
  → 难度：简单 → 中等 → 困难
```

---

**参考链接：**
- [LeetCode 动态规划专题](https://leetcode.cn/tag/dynamic-programming/)
- [背包问题九讲](https://github.com/tianyicui/pack)
- [动态规划从入门到放弃](https://zhuanlan.zhihu.com/p/31628866)
