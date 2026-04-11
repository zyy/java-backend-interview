---
layout: default
title: 位运算技巧：代码优化与高频面试题 ⭐⭐
---
# 位运算技巧：代码优化与高频面试题 ⭐⭐

## 🎯 面试题：如何用位运算判断一个数是否为 2 的幂次方？

> 位运算是代码优化利器，在算法面试和系统设计中都很重要。

---

## 一、位运算基础

```java
// 六种基本位运算
int a = 6, b = 3;

// 与（AND）：两位都为 1 才为 1
a & b  // 110 & 011 = 010 = 2

// 或（OR）：任一位为 1 就为 1
a | b  // 110 | 011 = 111 = 7

// 异或（XOR）：相同为 0，不同为 1
a ^ b  // 110 ^ 011 = 101 = 5

// 取反（NOT）：0 变 1，1 变 0
~a     // ~6 = -7（补码取反）

// 左移
a << 1  // 6 << 1 = 12（乘以 2^n）

// 右移（算术右移，正数高位补 0，负数高位补 1）
a >> 1  // 6 >> 1 = 3（除以 2^n，向下取整）
-6 >> 1 // -6 >> 1 = -3

// 无符号右移（高位始终补 0）
-6 >>> 1 // 巨大的正数（符号位变为 0）
```

---

## 二、常用技巧

```java
// 1. 判断奇偶数（比 % 2 快）
if ((n & 1) == 1) // n 是奇数
if ((n & 1) == 0) // n 是偶数

// 2. 交换两数（不用临时变量）
a = a ^ b;        // a = a ^ b
b = a ^ b;        // b = (a ^ b) ^ b = a
a = a ^ b;        // a = (a ^ b) ^ a = b

// 3. 获取第 i 位（从 0 开始）
int bit = (n >> i) & 1;

// 4. 设置第 i 位为 1
n = n | (1 << i);

// 5. 清除第 i 位（设为 0）
n = n & ~(1 << i);

// 6. 更新第 i 位为 v（v 为 0 或 1）
n = (n & ~(1 << i)) | (v << i);

// 7. 取最低位的 1（lowbit）
int lowbit = n & (-n);
// n = 12 = 1100
// -n = ~n + 1 = 0011 + 1 = 0100
// lowbit = 1100 & 0100 = 0100 = 4

// 8. 判断是否为 2 的幂次方
// n > 0 && (n & (n-1)) == 0
// 原理：2^n 只有一位是 1，n-1 把那一位变成 0，后面全变 1，& 运算为 0
```

---

## 三、面试真题

### 题目 1：二进制中 1 的个数

```java
// 方法一：Brian Kernighan 算法（最优 O(k)，k 为 1 的个数）
public int hammingWeight(int n) {
    int count = 0;
    while (n != 0) {
        n = n & (n - 1);  // 消除最低位的 1
        count++;
    }
    return count;
}

// 方法二：标准算法（O(32)）
public int hammingWeight(int n) {
    int count = 0;
    while (n != 0) {
        count += (n & 1);
        n >>>= 1;
    }
    return count;
}

// 方法三：Integer.bitCount()（Java 内置）
return Integer.bitCount(n);
```

### 题目 2：两数之和（不用 + - * /）

```java
// 用异或实现加法
public int add(int a, int b) {
    while (b != 0) {
        int carry = (a & b) << 1;  // 进位
        a = a ^ b;                 // 非进位和
        b = carry;
    }
    return a;
}

// 减法：a - b = a + (-b)
public int subtract(int a, int b) {
    return add(a, add(~b, 1));
}

// 乘法：
public int multiply(int a, int b) {
    boolean neg = (a < 0) ^ (b < 0);
    a = Math.abs(a);
    b = Math.abs(b);
    int result = 0;
    while (b > 0) {
        if ((b & 1) == 1) result = add(result, a);
        a <<= 1;
        b >>= 1;
    }
    return neg ? -result : result;
}
```

### 题目 3：只出现一次的数字 II

```java
// 数组中除了一个数字外，其他数字都出现 3 次
// 要求找到那个只出现 1 次的数字
// 思路：统计每一位上 1 的个数 % 3，余数就是答案对应位

public int singleNumber(int[] nums) {
    int result = 0;
    for (int i = 0; i < 32; i++) {
        int bitCount = 0;
        for (int num : nums) {
            bitCount += (num >> i) & 1;
        }
        if (bitCount % 3 != 0) {
            result |= (1 << i);
        }
    }
    return result;
}
```

### 题目 4：位图排序（海量数据去重）

```java
// 用 BitSet 对 40 亿整数排序/去重（只需要 512MB 内存）
// int 范围：-2^31 ~ 2^31-1，共 2^32 个数
// BitSet 需要 2^32 / 8 = 512MB

public class Bitmap {
    private long[] bits;  // 1 bit 表示一个数字
    private int max;

    public Bitmap(int max) {
        this.max = max;
        this.bits = new long[(max >> 6) + 1];  // /64
    }

    public void add(int n) {
        bits[n >> 6] |= (1L << (n & 63));  // n % 64
    }

    public boolean contains(int n) {
        return (bits[n >> 6] & (1L << (n & 63))) != 0;
    }

    // 使用示例：排序 100 万个范围在 [1, 1000万] 的整数
    public static void sort(int[] nums) {
        Bitmap bitmap = new Bitmap(10_000_000);
        for (int n : nums) bitmap.add(n);
        for (int i = 0; i < bitmap.bits.length; i++) {
            for (int j = 0; j < 64; j++) {
                if ((bitmap.bits[i] & (1L << j)) != 0) {
                    System.out.println((i << 6) + j);
                }
            }
        }
    }
}
```

### 题目 5：找出重复的数字（位运算法）

```java
// 长度为 n+1 的数组，值为 1~n，找出重复数字
// O(1) 空间，O(n log n) 时间

public int findDuplicate(int[] nums) {
    int result = 0;
    for (int i = 0; i < 32; i++) {
        int bit = 1 << i;
        int count1 = 0, count2 = 0;
        for (int j = 0; j < nums.length; j++) {
            if ((nums[j] & bit) != 0) count1++;
        }
        for (int j = 1; j <= nums.length - 1; j++) {
            if ((j & bit) != 0) count2++;
        }
        if (count1 > count2) {
            result |= bit;
        }
    }
    return result;
}
```

---

## 四、位运算在系统设计中的应用

```java
// 1. 权限系统：用位掩码表示权限
public class Permission {
    public static final int READ    = 1 << 0;  // 0001
    public static final int WRITE   = 1 << 1;  // 0010
    public static final int DELETE  = 1 << 2;  // 0100
    public static final int ADMIN   = 1 << 3;  // 1000

    private int permissions;

    public void grant(int p) { permissions |= p; }
    public void revoke(int p) { permissions &= ~p; }
    public boolean has(int p) { return (permissions & p) == p; }
}

// 使用
Permission p = new Permission();
p.grant(READ | WRITE);
p.has(READ);  // true
p.has(DELETE); // false
p.revoke(WRITE);

// 2. 状态机：用位掩码表示复合状态
// 用户同时有 VIP + 活跃 + 已验证状态
int state = VIP | ACTIVE | VERIFIED;
boolean isVipActive = (state & (VIP | ACTIVE)) != 0;
```

---

## 五、面试高频题

**Q1: 如何判断一个数是否为 2 的幂次方？**
> 核心思想：`n > 0 && (n & (n-1)) == 0`。原理：2 的幂次方二进制只有一位为 1（如 8=1000），减 1 后变成 0111，两者 & 运算为 0。如果是负数要先特殊处理。另外 `n > 0 && (n & -n) == n` 也可判断，-n 的最低位 1 和 n 的最低位 1 是同一位。

**Q2: 异或运算有哪些性质？**
> 四个性质：① 归零律 `a ^ a = 0`；② 恒等律 `a ^ 0 = a`；③ 交换律 `a ^ b = b ^ a`；④ 结合律 `(a ^ b) ^ c = a ^ (b ^ c)`。应用：不借助临时变量交换两数（`a = a ^ b; b = a ^ b; a = a ^ b`）、找出出现奇数次的数字（全员异或）。

**Q3: 布隆过滤器如何用位运算实现？**
> 布隆过滤器用 k 个哈希函数将 key 映射到 m 位的位数组，将对应 k 个位置设为 1。查询时检查 k 个位置是否全为 1，全为 1 则可能存在，否则一定不存在。空间效率高（1 bit 存一个状态），时间 O(k)。位数组大小选择：`m = -n * ln(p) / (ln(2)^2)`，其中 n 为预估元素个数，p 为期望误判率。
