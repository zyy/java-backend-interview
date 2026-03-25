---
layout: default
title: 时间复杂度和空间复杂度
---
# 时间复杂度和空间复杂度

> 算法分析的基础

## 🎯 面试重点

- 常见时间复杂度
- 复杂度的计算方法
- 空间复杂度分析

## 📖 时间复杂度

### 常见复杂度

```java
/**
 * 常见时间复杂度（按从小到大排序）：
 * 
 * O(1) - 常数时间
 * O(log n) - 对数时间
 * O(n) - 线性时间
 * O(n log n) - 线性对数时间
 * O(n²) - 平方时间
 * O(n³) - 立方时间
 * O(2ⁿ) - 指数时间
 * O(n!) - 阶乘时间
 */
public class TimeComplexity {}
```

### 示例

```java
/**
 * 时间复杂度示例
 */
public class ComplexityExamples {
    // O(1)
    /*
     * int a = 1;
     * int b = 2;
     * int c = a + b;
     */
    
    // O(n)
    /*
     * for (int i = 0; i < n; i++) {
     *     System.out.println(i);
     * }
     */
    
    // O(n²)
    /*
     * for (int i = 0; i < n; i++) {
     *     for (int j = 0; j < n; j++) {
     *         System.out.println(i + j);
     *     }
     * }
     */
    
    // O(log n)
    /*
     * int i = 1;
     * while (i < n) {
     *     i = i * 2;
     * }
     */
    
    // O(n log n)
    /*
     * // 排序算法如快速排序、归并排序
     * Arrays.sort(arr);  // O(n log n)
     */
}
```

### 规则

```java
/**
 * 复杂度计算规则
 */
public class ComplexityRules {
    // 1. 忽略常数
    /*
     * O(2n) -> O(n)
     * O(100) -> O(1)
     */
    
    // 2. 忽略低阶项
    /*
     * O(n² + n) -> O(n²)
     * O(n³ + n² + n) -> O(n³)
     */
    
    // 3. 嵌套复杂度相乘
    /*
     * for (int i = 0; i < n; i++) {
     *     for (int j = 0; j < m; j++) {
     *         // O(n * m)
     *     }
     * }
     */
    
    // 4. 取最大复杂度
    /*
     * O(n) + O(n²) -> O(n²)
     */
}
```

## 📖 空间复杂度

### 常见空间复杂度

```java
/**
 * 空间复杂度示例
 */
public class SpaceComplexity {
    // O(1)
    /*
     * int a = 1;
     * int b = 2;
     */
    
    // O(n)
    /*
     * int[] arr = new int[n];
     * 
     * StringBuilder sb = new StringBuilder();
     * for (int i = 0; i < n; i++) {
     *     sb.append(i);
     * }
     */
    
    // O(n²)
    /*
     * int[][] matrix = new int[n][n];
     */
}
```

### 递归空间

```java
/**
 * 递归空间复杂度
 */
public class RecursionSpace {
    // 递归调用栈空间
    /*
     * 递归深度 = 空间复杂度
     * 
     * void recursion(int n) {
     *     if (n <= 0) return;
     *     recursion(n - 1);  // O(n)
     * }
     */
}
```

## 📖 面试真题

### Q1: 二分查找的时间复杂度？

**答：** O(log n)

### Q2: 冒泡排序的时间/空间复杂度？

**答：** 
- 时间复杂度：O(n²)（最优 O(n)）
- 空间复杂度：O(1)

---

**⭐ 重点：复杂度分析是算法基础，必须熟练掌握**