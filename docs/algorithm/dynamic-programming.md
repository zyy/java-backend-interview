# 动态规划专题

> DP 核心思想

## 🎯 面试重点

- DP 核心思想
- 经典题目

## 📖 核心思想

```java
/**
 * 动态规划核心：
 * 1. 最优子结构
 * 2. 状态转移方程
 * 3. 边界条件
 */
public class DPCore {
    // 步骤：
    // 1. 定义状态
    // 2. 状态转移
    // 3. 初始化
    // 4. 计算顺序
}
```

## 📖 经典题目

### 斐波那契

```java
public int fib(int n) {
    if (n < 2) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int c = a + b;
        a = b;
        b = c;
    }
    return b;
}
```

### 最长递增子序列

```java
public int lengthOfLIS(int[] nums) {
    int[] dp = new int[nums.length];
    int max = 0;
    for (int i = 0; i < nums.length; i++) {
        dp[i] = 1;
        for (int j = 0; j < i; j++) {
            if (nums[j] < nums[i]) {
                dp[i] = Math.max(dp[i], dp[j] + 1);
            }
        }
        max = Math.max(max, dp[i]);
    }
    return max;
}
```

## 📖 面试真题

### Q1: DP 和递归的区别？

**答：** DP 避免重复计算，时间换空间。

---

**⭐ 重点：DP 是面试高频考点**