---
layout: default
title: 排序算法详解：常用排序原理与对比 ⭐⭐⭐
---

# 排序算法详解：常用排序原理与对比 ⭐⭐⭐

> 排序是面试的基础中的基础，几乎逢面必问。本文系统梳理七大排序算法的原理、代码实现、时间/空间复杂度及稳定性，结合 Top K 问题、非比较排序和高频面试题，帮助你彻底拿下排序！

---

## 一、冒泡排序（Bubble Sort）

### 1.1 算法原理

冒泡排序是最简单的排序算法之一，核心思想是：**两两比较相邻元素，如果逆序则交换，像气泡一样将最大/最小的元素逐步"冒"到序列一端**。

具体过程：
1. 从数组第一个元素开始，与下一个元素比较大小
2. 如果前者大于后者，交换两者位置
3. 一轮遍历后，最大的元素就"冒"到了最后
4. 对前 n-1 个元素重复上述过程，直到没有需要交换的元素

冒泡排序的名字来源于其过程：小的元素像气泡一样逐渐上浮到数组前面。

### 1.2 Java 代码实现

```java
/**
 * 冒泡排序 - 基础版本
 * 时间复杂度：O(n²)
 * 空间复杂度：O(1)
 * 稳定性：稳定
 */
public class BubbleSort {

    public static void bubbleSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            boolean swapped = false;  // 优化：记录本轮是否有交换
            for (int j = 0; j < n - 1 - i; j++) {
                if (arr[j] > arr[j + 1]) {
                    swap(arr, j, j + 1);
                    swapped = true;
                }
            }
            // 如果本轮没有发生交换，说明已经有序，提前结束
            if (!swapped) break;
        }
    }

    // 交换数组中两个元素的位置
    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}
```

### 1.3 优化版本：鸡尾酒排序（双向冒泡）

鸡尾酒排序是冒泡排序的变体，**每一轮遍历中，既从左向右把大元素"冒"到右边，又从右向左把小元素"冒"到左边**。这种双向交换的方式在某些情况下效率更高，尤其适合**近乎有序**的数组。

```java
/**
 * 鸡尾酒排序（双向冒泡）
 * 适用于近乎有序的数组，对完全有序数组可以做到 O(n)
 */
public static void cocktailSort(int[] arr) {
    if (arr == null || arr.length < 2) return;

    int left = 0;
    int right = arr.length - 1;
    boolean swapped;

    while (left < right) {
        swapped = false;

        // 从左向右冒泡：将较大元素放到右边
        for (int i = left; i < right; i++) {
            if (arr[i] > arr[i + 1]) {
                swap(arr, i, i + 1);
                swapped = true;
            }
        }
        right--;

        if (!swapped) break;

        swapped = false;

        // 从右向左冒泡：将较小元素放到左边
        for (int i = right; i > left; i--) {
            if (arr[i] < arr[i - 1]) {
                swap(arr, i, i - 1);
                swapped = true;
            }
        }
        left++;

        if (!swapped) break;
    }
}
```

### 1.4 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n) | 数组已经有序，经过优化可在第一轮就发现有序 |
| 平均 | O(n²) | 每轮需要比较 O(n) 次，共 O(n) 轮 |
| 最坏 | O(n²) | 数组完全逆序，每轮都需要大量交换 |
| 空间 | O(1) | 原地排序，只用到常数个临时变量 |
| 稳定性 | **稳定** | 相等元素不会交换先后顺序 |

**面试加分点**：冒泡排序虽然简单，但在近乎有序的情况下（如"排序到一半的数组"），优化后的冒泡排序效率很高。鸡尾酒排序对特定模式（如两端无序、中间接近有序）的数据表现更好。

---

## 二、选择排序（Selection Sort）

### 2.1 算法原理

选择排序的核心思想是：**每一轮从未排序区间中找出最小（或最大）元素，将其放到已排序区间的末尾**。

具体过程：
1. 在未排序序列中找到最小元素，记下其位置
2. 将该元素与未排序序列的第一个元素交换
3. 将已排序序列末尾扩大一个位置
4. 重复以上步骤，直到所有元素排序完成

选择排序的关键特征是：**无论数组初始状态如何，都要进行固定次数的比较**，时间复杂度与数据无关。

### 2.2 Java 代码实现

```java
/**
 * 选择排序
 * 时间复杂度：O(n²) —— 无论数据是否有序，都需要进行 n(n-1)/2 次比较
 * 空间复杂度：O(1)
 * 稳定性：不稳定 ⭐
 */
public class SelectionSort {

    public static void selectionSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            int minIndex = i;  // 假设当前 i 为最小值索引

            // 在未排序区间 [i+1, n-1] 中找最小元素
            for (int j = i + 1; j < n; j++) {
                if (arr[j] < arr[minIndex]) {
                    minIndex = j;
                }
            }

            // 将找到的最小元素与未排序区间的第一个元素交换
            if (minIndex != i) {
                swap(arr, i, minIndex);
            }
        }
    }

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}
```

### 2.3 为什么选择排序不稳定？

选择排序的**不稳定性**是一个高频面试点。考虑数组 `[2, 2, 1]`，第一轮找到最小值 `1`（索引 2），将其与索引 0 的 `2` 交换，得到 `[1, 2, 2]`。此时，两个 `2` 的相对顺序被改变了。

**如何让选择排序变得稳定？** 可以改为将最小元素与未排序区间的第一个位置交换（即不使用 swap 直接交换），但这需要额外 O(n) 的空间来移动元素，实践中一般不这么做，因为稳定性的代价较大。

### 2.4 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n²) | 仍然需要遍历所有未排序区间进行比较 |
| 平均 | O(n²) | 无论初始状态，都需要进行 n(n-1)/2 次比较 |
| 最坏 | O(n²) | 每次都要找最小值 + 交换 |
| 空间 | O(1) | 原地排序 |
| 稳定性 | **不稳定** | 交换操作可能改变相等元素的相对顺序 |

**面试加分点**：虽然选择排序的时间复杂度都是 O(n²)，但相比冒泡排序，它**减少了交换次数**——每轮最多只交换一次。冒泡排序可能需要 O(n²) 次交换，而选择排序最多只需要 O(n) 次交换。当交换成本很高时，选择排序可能比冒泡排序更快。

---

## 三、插入排序（Insertion Sort）

### 3.1 算法原理

插入排序的核心思想类似于**摸牌整理**：将数组分为已排序区和未排序区，每次从未排序区取出一个元素，在已排序区中找到合适的位置插入。

关键洞察：**插入排序对于近乎有序的数组，效率接近 O(n)**！这是它最重要的特点，也是面试中经常考查的场景。

### 3.2 Java 代码实现

```java
/**
 * 插入排序
 * 时间复杂度：最好 O(n)，平均/最坏 O(n²)
 * 空间复杂度：O(1)
 * 稳定性：稳定
 */
public class InsertionSort {

    public static void insertionSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;
        for (int i = 1; i < n; i++) {
            int current = arr[i];  // 待插入的元素
            int j = i - 1;

            // 将比 current 大的元素向后移动，为 current 腾出位置
            while (j >= 0 && arr[j] > current) {
                arr[j + 1] = arr[j];  // 元素后移
                j--;
            }

            // 插入 current 到正确位置
            arr[j + 1] = current;
        }
    }

    /**
     * 二分插入排序（折半插入）
     * 在已排序区间使用二分查找，减少比较次数
     * 但移动次数不变，所以整体时间复杂度仍是 O(n²)
     */
    public static void binaryInsertionSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;
        for (int i = 1; i < n; i++) {
            int current = arr[i];
            int left = 0, right = i - 1;

            // 二分查找插入位置
            while (left <= right) {
                int mid = left + (right - left) / 2;
                if (arr[mid] > current) {
                    right = mid - 1;
                } else {
                    left = mid + 1;
                }
            }

            // 将 [left, i-1] 区间的元素后移
            for (int j = i - 1; j >= left; j--) {
                arr[j + 1] = arr[j];
            }

            arr[left] = current;
        }
    }
}
```

### 3.3 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | **O(n)** | 数组已经有序，每个元素只需要比较一次 |
| 平均 | O(n²) | 随机数组，每个元素平均移动 n/2 次 |
| 最坏 | O(n²) | 数组完全逆序，每次都要移动整个已排序区 |
| 空间 | O(1) | 原地排序 |
| 稳定性 | **稳定** | 相等元素不会跨越已排序元素插入 |

**面试加分点**：插入排序的 O(n) 最好情况让它成为**小规模数据排序**的首选！很多语言内置的排序算法（如 Java 的 TimSort、V8 的 TimSort）在小规模数据块（通常 < 64 个元素）上会切换到插入排序，因为对小规模数据 O(n²) 的常数因子反而比递归开销小。

---

## 四、希尔排序（Shell Sort）

### 4.1 算法原理

希尔排序是插入排序的**优化版本**，由 Donald Shell 于 1959 年提出。其核心思想是：

1. 引入**增量（gap）** 的概念，将数组按增量划分为多个子序列
2. 对每个子序列分别进行插入排序
3. 逐步缩小增量，重复上述过程
4. 最后当增量 = 1 时，对整个数组进行插入排序

希尔排序的关键是：**通过大增量先将数组变得"基本有序"，减少最后一步插入排序的移动次数**。这比直接对原始数组进行插入排序要快得多。

### 4.2 Java 代码实现

```java
/**
 * 希尔排序（Shell Sort）
 * 时间复杂度：平均 O(n^1.3)，最坏 O(n²)
 * 空间复杂度：O(1)
 * 稳定性：不稳定
 */
public class ShellSort {

    public static void shellSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;

        // 初始增量：n/2，逐步缩小
        for (int gap = n / 2; gap >= 1; gap /= 2) {

            // 对每个子序列进行插入排序
            for (int i = gap; i < n; i++) {
                int current = arr[i];
                int j = i - gap;

                // 在当前子序列中寻找插入位置
                while (j >= 0 && arr[j] > current) {
                    arr[j + gap] = arr[j];
                    j -= gap;
                }
                arr[j + gap] = current;
            }
        }
    }

    /**
     * 使用 Knuth 序列的希尔排序
     * 增量公式：h = 3*h + 1 (h 初始为 1)
     * Knuth 序列在实践中通常比简单的 n/2 序列更快
     */
    public static void shellSortKnuth(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;

        // 使用 Knuth 序列计算初始增量
        // h = 1, 4, 13, 40, 121, ...
        int gap = 1;
        while (gap < n / 3) {
            gap = gap * 3 + 1;
        }

        while (gap >= 1) {
            for (int i = gap; i < n; i++) {
                int current = arr[i];
                int j = i - gap;

                while (j >= 0 && arr[j] > current) {
                    arr[j + gap] = arr[j];
                    j -= gap;
                }
                arr[j + gap] = current;
            }
            gap /= 3;  // 缩小增量
        }
    }
}
```

### 4.3 增量序列的选择

希尔排序的效率与增量序列的选择密切相关。常见的增量序列：

| 增量序列 | 最好情况时间复杂度 | 说明 |
|---------|-------------------|------|
| n/2, n/4, ..., 1（原始 Shell） | O(n²) | 简单但不是最优 |
| 2^k（Knuth 序列） | O(n^1.5) | Donald Knuth 提出，效果较好 |
| 2^i * 3^j（Pratt 序列） | O(n log² n) | 理论最优之一 |
| Hibbard 序列 | O(n^1.5) | 2^k - 1 |
| Sedgewick 序列 | O(n^1.3) | 目前实践中最优的序列之一 |

### 4.4 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n log² n) | 使用 Pratt 序列 |
| 平均 | O(n^1.3) ~ O(n^1.5) | 取决于增量序列 |
| 最坏 | O(n²) | 使用简单增量序列且数组逆序 |
| 空间 | O(1) | 原地排序 |
| 稳定性 | **不稳定** | 增量划分可能导致相等元素跨越分组 |

---

## 五、归并排序（Merge Sort）

### 5.1 算法原理

归并排序采用**分治（Divide and Conquer）** 策略，核心步骤：

1. **分解（Divide）**：将数组从中间分成两半，递归地对左右两部分排序
2. **解决（Conquer）**：当子数组长度 <= 1 时，认为已经有序
3. **合并（Merge）**：将两个有序子数组合并为一个有序数组

归并排序的核心在于 **merge 操作**，它通过双指针技术将两个有序数组合并，时间复杂度是线性的 O(n)。

### 5.2 Java 代码实现

```java
/**
 * 归并排序
 * 时间复杂度：所有情况 O(n log n)
 * 空间复杂度：O(n) —— 需要额外的辅助数组
 * 稳定性：稳定 ⭐
 */
public class MergeSort {

    /**
     * 递归版本
     */
    public static void mergeSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int[] temp = new int[arr.length];  // 一次性分配，避免每次递归分配
        mergeSortHelper(arr, 0, arr.length - 1, temp);
    }

    private static void mergeSortHelper(int[] arr, int left, int right, int[] temp) {
        if (left >= right) return;  // 递归终止条件

        int mid = left + (right - left) / 2;  // 防止溢出

        // 分解：左右两部分分别递归排序
        mergeSortHelper(arr, left, mid, temp);
        mergeSortHelper(arr, mid + 1, right, temp);

        // 合并：左右两部分合并（只有左 > 右 时才合并）
        if (arr[mid] > arr[mid + 1]) {
            merge(arr, left, mid, right, temp);
        }
    }

    /**
     * 合并两个有序数组 arr[left..mid] 和 arr[mid+1..right]
     */
    private static void merge(int[] arr, int left, int mid, int right, int[] temp) {
        int i = left;      // 左半部分指针
        int j = mid + 1;  // 右半部分指针
        int k = left;      // 临时数组指针

        // 双指针合并
        while (i <= mid && j <= right) {
            if (arr[i] <= arr[j]) {  // 注意：<=
                temp[k++] = arr[i++];
            } else {
                temp[k++] = arr[j++];
            }
        }

        // 处理剩余元素
        while (i <= mid) {
            temp[k++] = arr[i++];
        }
        while (j <= right) {
            temp[k++] = arr[j++];
        }

        // 将合并结果拷贝回原数组
        System.arraycopy(temp, left, arr, left, right - left + 1);
    }

    /**
     * 迭代版本（自底向上）
     * 不需要递归，空间上更节省（不需要递归栈）
     */
    public static void mergeSortIterative(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;
        int[] temp = new int[n];

        // 子数组大小从 1 开始，每次翻倍
        for (int size = 1; size < n; size *= 2) {

            // 对所有子数组进行两两合并
            for (int left = 0; left < n - size; left += 2 * size) {
                int mid = left + size - 1;
                int right = Math.min(left + 2 * size - 1, n - 1);
                merge(arr, left, mid, right, temp);
            }
        }
    }

    /**
     * 求逆序对数量（LeetCode 困难题：数组中的逆序对）
     * 归并排序顺便可以解决的问题
     */
    private static long reversePairs = 0;

    public static int reversePairs(int[] arr) {
        if (arr == null || arr.length < 2) return 0;

        int[] temp = new int[arr.length];
        reversePairs = 0;
        mergeSortHelperForReverse(arr, 0, arr.length - 1, temp);
        return (int) reversePairs;
    }

    private static void mergeSortHelperForReverse(int[] arr, int left, int right, int[] temp) {
        if (left >= right) return;

        int mid = left + (right - left) / 2;
        mergeSortHelperForReverse(arr, left, mid, temp);
        mergeSortHelperForReverse(arr, mid + 1, right, temp);

        if (arr[mid] > arr[mid + 1]) {
            mergeForReverse(arr, left, mid, right, temp);
        }
    }

    private static void mergeForReverse(int[] arr, int left, int mid, int right, int[] temp) {
        int i = left;
        int j = mid + 1;
        int k = left;

        while (i <= mid && j <= right) {
            if (arr[i] <= arr[j]) {
                temp[k++] = arr[i++];
            } else {
                // arr[i] > arr[j]，说明 arr[i..mid] 都大于 arr[j]
                // 构成 (mid - i + 1) 个逆序对
                reversePairs += (mid - i + 1);
                temp[k++] = arr[j++];
            }
        }

        while (i <= mid) temp[k++] = arr[i++];
        while (j <= right) temp[k++] = arr[j++];

        System.arraycopy(temp, left, arr, left, right - left + 1);
    }
}
```

### 5.3 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n log n) | 无论如何都要完整地递归分解和合并 |
| 平均 | O(n log n) | 每次合并都是 O(n)，递归深度为 log n |
| 最坏 | O(n log n) | 归并排序没有快速排序的最坏情况退化问题 |
| 空间 | O(n) | 需要额外的辅助数组；递归栈深度为 O(log n) |
| 稳定性 | **稳定** | 在 merge 中使用 `<=` 保持稳定性 |

**面试加分点**：
- **为何归并排序稳定？** 因为在 merge 时使用 `<=` 而不是 `<`，确保相等元素的相对顺序不改变。
- **求逆序对**：归并排序天然适合求逆序对数量，因为合并时左半部分的元素索引都小于右半部分，当左半部分的元素大于右半部分的元素时，就找到了逆序对。这个技巧可以解决 LeetCode 困难题"数组中的逆序对"。
- **外部排序**：归并排序的思路天然适合外部排序（数据量太大无法全部放入内存），可以分块读入、排序后再合并。数据库的 ORDER BY 也常用这种思路。

---

## 六、快速排序（Quick Sort）

### 6.1 算法原理

快速排序是面试中最常考的排序算法，也是实践中最常用的高效排序算法之一（Java 的 Arrays.sort() 在数据量小于 47 时用插入排序，大于 47 时用快速排序）。

核心思想：
1. **选择基准（pivot）**：从数组中选一个元素作为基准
2. **分区（partition）**：将数组分为两部分，左边 <= 基准，右边 >= 基准
3. **递归排序**：对左右两部分递归执行上述过程

### 6.2 Java 代码实现

```java
/**
 * 快速排序
 * 时间复杂度：平均 O(n log n)，最坏 O(n²)
 * 空间复杂度：O(log n)（递归栈）
 * 稳定性：不稳定
 */
public class QuickSort {

    public static void quickSort(int[] arr) {
        if (arr == null || arr.length < 2) return;
        quickSortHelper(arr, 0, arr.length - 1);
    }

    private static void quickSortHelper(int[] arr, int low, int high) {
        if (low < high) {
            int pivotIndex = partition(arr, low, high);
            quickSortHelper(arr, low, pivotIndex - 1);
            quickSortHelper(arr, pivotIndex + 1, high);
        }
    }

    /**
     * Lomuto 分区方案（以最后一个元素为基准）
     * 返回基准最终所在的位置
     */
    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];  // 选择最后一个元素作为基准
        int i = low - 1;        // i 是小于基准区域的边界

        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                swap(arr, i, j);
            }
        }

        // 将基准放到正确位置
        swap(arr, i + 1, high);
        return i + 1;
    }

    /**
     * Hoare 分区方案（更快，减少交换次数）
     */
    private static int partitionHoare(int[] arr, int low, int high) {
        int pivot = arr[low];
        int i = low - 1;
        int j = high + 1;

        while (true) {
            do { i++; } while (arr[i] < pivot);
            do { j--; } while (arr[j] > pivot);

            if (i >= j) return j;
            swap(arr, i, j);
        }
    }

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    // ============================================================
    // 快速排序的优化版本
    // ============================================================

    /**
     * 优化1：三数取中（Median-of-Three）
     * 避免基准选择不当导致最坏情况
     */
    public static void quickSortMedian(int[] arr) {
        if (arr == null || arr.length < 2) return;
        quickSortHelperMedian(arr, 0, arr.length - 1);
    }

    private static void quickSortHelperMedian(int[] arr, int low, int high) {
        if (low < high) {
            // 三数取中：选取 left, mid, right 三个数的中位数作为基准
            int pivotIndex = medianOfThree(arr, low, high);
            // 将中位数交换到 high-1 的位置
            swap(arr, pivotIndex, high - 1);

            int pivot = arr[high - 1];
            int i = low;
            int j = high - 1;

            while (true) {
                while (arr[++i] < pivot) {}
                while (j > low && arr[--j] > pivot) {}

                if (i < j) {
                    swap(arr, i, j);
                } else {
                    break;
                }
            }

            swap(arr, i, high - 1);

            quickSortHelperMedian(arr, low, i - 1);
            quickSortHelperMedian(arr, i + 1, high);
        }
    }

    /**
     * 三数取中：返回中位数的索引
     */
    private static int medianOfThree(int[] arr, int low, int high) {
        int mid = low + (high - low) / 2;

        if (arr[low] > arr[high]) swap(arr, low, high);
        if (arr[mid] > arr[high]) swap(arr, mid, high);
        if (arr[low] > arr[mid]) swap(arr, low, mid);

        return mid;
    }

    /**
     * 优化2：随机基准（Random Pivot）
     * 避免特定输入导致的性能退化
     */
    public static void quickSortRandom(int[] arr) {
        if (arr == null || arr.length < 2) return;
        quickSortHelperRandom(arr, 0, arr.length - 1);
    }

    private static void quickSortHelperRandom(int[] arr, int low, int high) {
        if (low < high) {
            int pivotIndex = randomPartition(arr, low, high);
            quickSortHelperRandom(arr, low, pivotIndex - 1);
            quickSortHelperRandom(arr, pivotIndex + 1, high);
        }
    }

    private static int randomPartition(int[] arr, int low, int high) {
        int randomIndex = low + (int) (Math.random() * (high - low + 1));
        swap(arr, randomIndex, high);
        return partition(arr, low, high);
    }

    /**
     * 优化3：小规模数据切换到插入排序
     * 当子数组规模小于阈值（通常 16-47）时，使用插入排序
     */
    private static final int INSERTION_THRESHOLD = 16;

    public static void quickSortOptimized(int[] arr) {
        if (arr == null || arr.length < 2) return;
        quickSortHelperOptimized(arr, 0, arr.length - 1);
    }

    private static void quickSortHelperOptimized(int[] arr, int low, int high) {
        // 小规模数据用插入排序
        if (high - low < INSERTION_THRESHOLD) {
            insertionSort(arr, low, high);
            return;
        }

        int pivotIndex = partition(arr, low, high);
        quickSortHelperOptimized(arr, low, pivotIndex - 1);
        quickSortHelperOptimized(arr, pivotIndex + 1, high);
    }

    private static void insertionSort(int[] arr, int low, int high) {
        for (int i = low + 1; i <= high; i++) {
            int current = arr[i];
            int j = i - 1;
            while (j >= low && arr[j] > current) {
                arr[j + 1] = arr[j];
                j--;
            }
            arr[j + 1] = current;
        }
    }
}
```

### 6.3 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n log n) | 基准恰好是中间值，每次分区均匀 |
| 平均 | O(n log n) | 随机数据情况下，快速排序的期望性能 |
| 最坏 | **O(n²)** | 基准选取不当（如有序数组选最小值），分区极度不均匀 |
| 空间 | O(log n) | 递归栈深度，最好/平均 O(log n)，最坏 O(n) |
| 稳定性 | **不稳定** | 分区过程中交换操作会改变相等元素的相对顺序 |

**面试加分点**：
- **为何快速排序实际比归并排序快？**
  1. **缓存友好**：快速排序是原地排序，顺序访问模式，CPU 缓存命中率高
  2. **没有额外的空间开销**：归并排序需要 O(n) 的辅助空间
  3. **常数因子小**：虽然两者时间复杂度都是 O(n log n)，但快速排序的常数因子更小
  4. **原地排序**：不需要额外的数组分配

- **基准选择的影响**：有序数组 + 选第一个/最后一个元素 = O(n²)，这就是为什么实际应用中需要"三数取中"或"随机基准"来规避最坏情况。

- **快速排序的递归非递归实现**：面试时可以提及，可以用栈模拟递归过程，避免递归栈溢出。

---

## 七、堆排序（Heap Sort）

### 7.1 算法原理

堆排序利用**堆（Heap）** 这种完全二叉树数据结构进行排序。

- **大顶堆**：每个节点的值都大于等于其子节点的值，堆顶是最大值
- **小顶堆**：每个节点的值都小于等于其子节点的值，堆顶是最小值

堆排序过程：
1. **构建大顶堆**：将数组调整为大顶堆结构
2. **逐个取出堆顶**：将堆顶与堆尾交换，然后对剩余元素 heapify
3. 重复步骤 2，直到堆中只剩一个元素

### 7.2 完全二叉树的性质

对于数组中的第 i 个元素（从 0 开始）：
- 父节点索引：`(i - 1) / 2`
- 左子节点索引：`2 * i + 1`
- 右子节点索引：`2 * i + 2`

对于有 n 个元素的数组：
- 最后一个非叶子节点索引：`(n / 2) - 1`

### 7.3 Java 代码实现

```java
/**
 * 堆排序
 * 时间复杂度：所有情况 O(n log n)
 * 空间复杂度：O(1)
 * 稳定性：不稳定
 */
public class HeapSort {

    public static void heapSort(int[] arr) {
        if (arr == null || arr.length < 2) return;

        int n = arr.length;

        // 第一步：构建大顶堆（从最后一个非叶子节点开始，自下而上调整）
        for (int i = n / 2 - 1; i >= 0; i--) {
            heapify(arr, n, i);
        }

        // 第二步：逐个将堆顶元素（最大值）交换到数组末尾
        for (int i = n - 1; i > 0; i--) {
            swap(arr, 0, i);        // 将堆顶移到末尾
            heapify(arr, i, 0);      // 对剩余堆进行调整
        }
    }

    /**
     * Heapify：将以 i 为根节点的子树调整为大顶堆
     * @param arr 数组
     * @param n   当前堆的大小
     * @param i   待调整的节点索引
     */
    private static void heapify(int[] arr, int n, int i) {
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

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    // ============================================================
    // 堆的常用操作（PriorityQueue 底层原理）
    // ============================================================

    /**
     * 插入操作：向堆中添加一个元素
     * 时间复杂度：O(log n)
     */
    public static void heapInsert(int[] arr, int index) {
        int value = arr[index];
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (arr[parent] >= value) {
                break;
            }
            arr[index] = arr[parent];
            index = parent;
        }
        arr[index] = value;
    }

    /**
     * 移除堆顶：弹出并返回堆顶元素
     * 时间复杂度：O(log n)
     */
    public static int heapPop(int[] arr, int heapSize) {
        int maxValue = arr[0];
        arr[0] = arr[heapSize - 1];
        heapify(arr, heapSize - 1, 0);
        return maxValue;
    }

    /**
     * 获取堆顶元素但不移除
     */
    public static int heapPeek(int[] arr) {
        return arr[0];
    }

    /**
     * 判断数组是否为堆
     */
    public static boolean isHeap(int[] arr, int n, int i) {
        if (i >= n / 2) return true;  // 叶子节点

        int left = 2 * i + 1;
        int right = 2 * i + 2;

        return (arr[i] >= arr[left]) &&
               (arr[i] >= arr[right]) &&
               isHeap(arr, n, left) &&
               isHeap(arr, n, right);
    }
}
```

### 7.4 复杂度分析

| 情况 | 时间复杂度 | 说明 |
|------|-----------|------|
| 最好 | O(n log n) | 所有情况相同 |
| 平均 | O(n log n) | 构建堆 O(n)，n 次 heapify，每次 O(log n) |
| 最坏 | O(n log n) | 所有情况相同，没有退化问题 |
| 空间 | O(1) | 原地排序 |
| 稳定性 | **不稳定** | 堆化过程中可能改变相等元素的相对顺序 |

**面试加分点**：
- **为何堆排序不稳定？** 考虑 `[2a, 2b, 1]`（2a 在 2b 前面），建堆后可能变成 `[2b, 2a, 1]`，相等元素的相对顺序改变了。
- **PriorityQueue 底层原理**：Java 中的 PriorityQueue（小顶堆）就是用数组实现的大顶堆/小顶堆，用于实现 Dijkstra 最短路径、Top K 问题等。
- **堆排序 vs 快速排序**：堆排序的常数因子比快速排序大（heapify 的比较次数更多），而且堆排序的缓存命中差（不是顺序访问），所以实践中快速排序通常更快。

---

## 八、七大排序算法综合对比

### 8.1 稳定性对比

| 排序算法 | 稳定性 | 说明 |
|---------|--------|------|
| 冒泡排序 | ✅ 稳定 | 相等元素不交换 |
| 插入排序 | ✅ 稳定 | 相等元素插入到右侧 |
| 归并排序 | ✅ 稳定 | merge 时使用 `<=` |
| 快速排序 | ❌ 不稳定 | 分区交换可能打乱相等元素 |
| 选择排序 | ❌ 不稳定 | 交换操作可能打乱相等元素 |
| 希尔排序 | ❌ 不稳定 | 增量序列导致元素跨越分组 |
| 堆排序 | ❌ 不稳定 | 堆化过程中可能改变相对顺序 |

### 8.2 时间复杂度对比

| 排序算法 | 最好 | 平均 | 最坏 | 空间 | 稳定性 |
|---------|------|------|------|------|--------|
| 冒泡排序 | O(n) | O(n²) | O(n²) | O(1) | ✅ 稳定 |
| 选择排序 | O(n²) | O(n²) | O(n²) | O(1) | ❌ 不稳定 |
| 插入排序 | **O(n)** | O(n²) | O(n²) | O(1) | ✅ 稳定 |
| 希尔排序 | O(n log² n) | O(n^1.3) | O(n²) | O(1) | ❌ 不稳定 |
| 归并排序 | O(n log n) | O(n log n) | O(n log n) | O(n) | ✅ 稳定 |
| 快速排序 | O(n log n) | O(n log n) | **O(n²)** | O(log n) | ❌ 不稳定 |
| 堆排序 | O(n log n) | O(n log n) | O(n log n) | O(1) | ❌ 不稳定 |

### 8.3 各排序算法适用场景

| 场景 | 推荐算法 | 原因 |
|------|---------|------|
| 数据量小（n ≤ 50） | 插入排序 | O(n²) 的常数因子小，且近乎有序时接近 O(n) |
| 近乎有序 | 插入排序 / 鸡尾酒排序 | 优化后接近 O(n) |
| 一般情况追求速度 | 快速排序 | 原地排序，缓存友好 |
| 需要稳定排序 | 归并排序 | 唯一稳定的 O(n log n) 算法 |
| 内存受限 | 堆排序 / 插入排序 | O(1) 空间 |
| Top K 问题 | 堆排序 | O(n log k) |
| 外部排序（大数据） | 归并排序 | 分块合并思路天然适合 |

---

## 九、Top K 问题

### 9.1 问题描述

> 如何在海量数据中找出前 K 个最大/最小的元素？

这是面试中高频出现的问题，有多种解法。

### 9.2 解法一：堆排序（推荐）

使用小顶堆维护前 K 大的元素，时间复杂度 O(n log k)。

```java
import java.util.PriorityQueue;

/**
 * Top K 问题 - 使用小顶堆
 * 思路：维护一个大小为 K 的小顶堆，堆顶是 K 个数中的最小值
 * 遍历数组时，如果当前元素大于堆顶，则替换堆顶并调整堆
 *
 * 时间复杂度：O(n log k)
 * 空间复杂度：O(k)
 * 适用于：海量数据 Top K（只需要维护 K 个元素的堆）
 */
public class TopK {

    /**
     * 找出数组中最小的 K 个元素（Top K 小）
     */
    public static int[] topKSmallest(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            return new int[0];
        }

        // 使用小顶堆
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(k);

        for (int num : arr) {
            if (minHeap.size() < k) {
                minHeap.offer(num);
            } else if (num < minHeap.peek()) {
                // 当前数比堆顶（K 个数中的最小值）更小，替换
                minHeap.poll();
                minHeap.offer(num);
            }
        }

        int[] result = new int[k];
        int index = 0;
        for (int num : minHeap) {
            result[index++] = num;
        }
        return result;
    }

    /**
     * 找出数组中最大的 K 个元素（Top K 大）
     */
    public static int[] topKLargest(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            return new int[0];
        }

        // 使用小顶堆，堆顶是 K 个大数中的最小值
        PriorityQueue<Integer> minHeap = new PriorityQueue<>(k);

        for (int num : arr) {
            if (minHeap.size() < k) {
                minHeap.offer(num);
            } else if (num > minHeap.peek()) {
                minHeap.poll();
                minHeap.offer(num);
            }
        }

        int[] result = new int[k];
        int index = 0;
        for (int num : minHeap) {
            result[index++] = num;
        }
        return result;
    }

    /**
     * 使用大顶堆（适用于需要完全有序的 Top K）
     * 先用小顶堆筛选出 Top K，再用大顶堆排序
     */
    public static int[] topKSorted(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            return new int[0];
        }

        // 第一步：找出 Top K（用小顶堆）
        int[] topK = topKLargest(arr, k);

        // 第二步：对 Top K 进行排序（用大顶堆）
        int n = topK.length;
        for (int i = n / 2 - 1; i >= 0; i--) {
            heapify(topK, n, i);
        }
        for (int i = n - 1; i > 0; i--) {
            swap(topK, 0, i);
            heapify(topK, i, 0);
        }

        return topK;
    }

    private static void heapify(int[] arr, int n, int i) {
        int largest = i;
        int left = 2 * i + 1;
        int right = 2 * i + 2;

        if (left < n && arr[left] > arr[largest]) largest = left;
        if (right < n && arr[right] > arr[largest]) largest = right;
        if (largest != i) {
            swap(arr, i, largest);
            heapify(arr, n, largest);
        }
    }

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}
```

### 9.3 解法二：快速选择（QuickSelect）

快速选择是快速排序的变体，平均时间复杂度 O(n)，最坏 O(n²)。

```java
/**
 * 快速选择算法（QuickSelect）
 * 用于在无序数组中找出第 K 大（或第 K 小）的元素
 * 平均时间复杂度 O(n)，空间复杂度 O(1)（不计递归栈）
 */
public class QuickSelect {

    /**
     * 找出第 K 大的元素（K 从 1 开始）
     */
    public static int findKthLargest(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            throw new IllegalArgumentException("Invalid k");
        }

        return quickSelect(arr, 0, arr.length - 1, arr.length - k);  // 第 K 大 = 第 (n-k) 小
    }

    /**
     * 找出第 K 小的元素（K 从 1 开始）
     */
    public static int findKthSmallest(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            throw new IllegalArgumentException("Invalid k");
        }

        return quickSelect(arr, 0, arr.length - 1, k - 1);
    }

    private static int quickSelect(int[] arr, int low, int high, int targetIndex) {
        if (low == high) {
            return arr[low];
        }

        int pivotIndex = partition(arr, low, high);

        if (targetIndex == pivotIndex) {
            return arr[pivotIndex];
        } else if (targetIndex < pivotIndex) {
            return quickSelect(arr, low, pivotIndex - 1, targetIndex);
        } else {
            return quickSelect(arr, pivotIndex + 1, high, targetIndex);
        }
    }

    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
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

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    /**
     * 使用 BFPRT 算法（Median of Medians）
     * 最坏情况也能保证 O(n) 时间复杂度
     */
    public static int findKthLargestBFPRT(int[] arr, int k) {
        if (arr == null || k <= 0 || k > arr.length) {
            throw new IllegalArgumentException("Invalid k");
        }

        return bfprtSelect(arr, 0, arr.length - 1, arr.length - k);
    }

    private static int bfprtSelect(int[] arr, int low, int high, int targetIndex) {
        if (low == high) {
            return arr[low];
        }

        // 1. 将数组分成每组 5 个，找出每组中位数
        int pivot = getMedianOfMedians(arr, low, high);

        // 2. 使用 pivot 进行划分
        int pivotIndex = partitionAroundPivot(arr, low, high, pivot);

        if (targetIndex == pivotIndex) {
            return arr[pivotIndex];
        } else if (targetIndex < pivotIndex) {
            return bfprtSelect(arr, low, pivotIndex - 1, targetIndex);
        } else {
            return bfprtSelect(arr, pivotIndex + 1, high, targetIndex);
        }
    }

    /**
     * 获取中位数的中位数（作为划分基准）
     */
    private static int getMedianOfMedians(int[] arr, int low, int high) {
        int n = high - low + 1;
        int numOfGroups = (n + 4) / 5;  // 向上取整

        int[] medians = new int[numOfGroups];
        int index = 0;

        for (int i = 0; i < numOfGroups; i++) {
            int groupStart = low + i * 5;
            int groupEnd = Math.min(groupStart + 4, high);
            int groupSize = groupEnd - groupStart + 1;

            // 对每组进行简单排序（5 个元素，直接插入排序）
            for (int j = groupStart + 1; j <= groupEnd; j++) {
                int key = arr[j];
                int k = j - 1;
                while (k >= groupStart && arr[k] > key) {
                    arr[k + 1] = arr[k];
                    k--;
                }
                arr[k + 1] = key;
            }

            // 取出中位数（每组第 (groupSize+1)/2 个）
            medians[index++] = arr[groupStart + groupSize / 2];
        }

        // 递归求中位数数组的中位数
        if (numOfGroups == 1) {
            return medians[0];
        }
        return bfprtSelect(medians, 0, numOfGroups - 1, numOfGroups / 2);
    }

    private static int partitionAroundPivot(int[] arr, int low, int high, int pivot) {
        // 将所有等于 pivot 的元素集中到中间区域
        int left = low, right = high;
        int i = low;

        while (i <= right) {
            if (arr[i] == pivot) {
                i++;
            } else if (arr[i] < pivot) {
                swap(arr, left++, i++);
            } else {
                swap(arr, i, right--);
            }
        }

        // 返回中位数区域的位置（取中间的某个等于 pivot 的位置）
        return (left + right) / 2;
    }
}
```

### 9.4 Top K 解法对比

| 解法 | 时间复杂度 | 空间复杂度 | 特点 |
|------|-----------|-----------|------|
| 排序后取 Top K | O(n log n) | O(1) | 简单直接，但效率不是最优 |
| 堆排序 | O(n log k) | O(k) | **推荐**，适合海量数据 |
| 快速选择 | O(n) ~ O(n²) | O(1) | 平均最快，最坏可能退化 |
| BFPRT | **O(n)** | O(1) | 最坏情况也能保证线性 |

---

## 十、非比较排序

非比较排序不通过元素间的比较来完成排序，因此可以突破 O(n log n) 的下界，在特定场景下达到 O(n) 的线性时间复杂度。

### 10.1 计数排序（Counting Sort）

适用于**范围不大**的整数排序，时间复杂度 O(n + k)，其中 k 是数据范围。

```java
/**
 * 计数排序
 * 适用于：整数排序，数据范围不大（最大值 - 最小值不能太大）
 * 时间复杂度：O(n + k)，k 为数据范围
 * 空间复杂度：O(k)
 * 稳定性：稳定 ⭐
 */
public class CountingSort {

    /**
     * 标准计数排序（稳定版本）
     */
    public static int[] countingSort(int[] arr) {
        if (arr == null || arr.length == 0) return arr;

        // 找出数据范围
        int max = arr[0];
        int min = arr[0];
        for (int num : arr) {
            max = Math.max(max, num);
            min = Math.min(min, num);
        }

        int range = max - min + 1;
        int[] count = new int[range];
        int[] output = new int[arr.length];

        // 1. 统计每个元素出现的次数
        for (int num : arr) {
            count[num - min]++;
        }

        // 2. 累加计数（计算元素在输出数组中的位置）
        for (int i = 1; i < range; i++) {
            count[i] += count[i - 1];
        }

        // 3. 从后向前遍历，保证稳定性（相等元素的相对顺序不变）
        for (int i = arr.length - 1; i >= 0; i--) {
            output[count[arr[i] - min] - 1] = arr[i];
            count[arr[i] - min]--;
        }

        // 拷贝回原数组
        System.arraycopy(output, 0, arr, 0, arr.length);
        return arr;
    }

    /**
     * 计数排序扩展：处理负数
     */
    public static int[] countingSortWithNegative(int[] arr) {
        if (arr == null || arr.length == 0) return arr;

        int max = arr[0];
        int min = arr[0];
        for (int num : arr) {
            max = Math.max(max, num);
            min = Math.min(min, num);
        }

        int range = max - min + 1;
        int[] count = new int[range];
        int[] output = new int[arr.length];

        for (int num : arr) {
            count[num - min]++;
        }

        for (int i = 1; i < range; i++) {
            count[i] += count[i - 1];
        }

        for (int i = arr.length - 1; i >= 0; i--) {
            output[count[arr[i] - min] - 1] = arr[i];
            count[arr[i] - min]--;
        }

        System.arraycopy(output, 0, arr, 0, arr.length);
        return arr;
    }
}
```

**面试加分点**：计数排序是**桶排序的特例**，当桶的数量等于数据范围时就是计数排序。它天然是稳定的（从后向前遍历保证了稳定性）。

### 10.2 桶排序（Bucket Sort）

将数据分到有限数量的桶中，对每个桶内部进行排序，然后按顺序合并。

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;

/**
 * 桶排序
 * 适用于：数据分布均匀，范围可控
 * 时间复杂度：平均 O(n + k)，最坏 O(n²)（所有元素都在一个桶中）
 * 空间复杂度：O(n + k)
 * 稳定性：取决于桶内排序使用的算法
 */
public class BucketSort {

    public static void bucketSort(float[] arr) {
        if (arr == null || arr.length == 0) return;

        // 1. 创建 n 个桶
        int n = arr.length;
        LinkedList<Float>[] buckets = new LinkedList[n];

        // 2. 将元素分配到各个桶中
        for (int i = 0; i < n; i++) {
            int bucketIndex = (int) (arr[i] * n);  // 假设数据在 [0, 1) 范围内
            if (buckets[bucketIndex] == null) {
                buckets[bucketIndex] = new LinkedList<>();
            }
            buckets[bucketIndex].add(arr[i]);
        }

        // 3. 对每个桶内部进行排序（使用插入排序或 Collections.sort）
        for (LinkedList<Float> bucket : buckets) {
            if (bucket != null) {
                Collections.sort(bucket);
            }
        }

        // 4. 合并所有桶
        int index = 0;
        for (LinkedList<Float> bucket : buckets) {
            if (bucket != null) {
                for (float num : bucket) {
                    arr[index++] = num;
                }
            }
        }
    }

    /**
     * 整数桶排序（使用计数排序作为桶内排序）
     */
    public static int[] bucketSortInt(int[] arr, int bucketSize) {
        if (arr == null || arr.length == 0) return arr;

        // 找出数据范围
        int max = arr[0], min = arr[0];
        for (int num : arr) {
            max = Math.max(max, num);
            min = Math.min(min, num);
        }

        // 创建桶
        int bucketCount = (max - min) / bucketSize + 1;
        ArrayList<Integer>[] buckets = new ArrayList[bucketCount];
        for (int i = 0; i < bucketCount; i++) {
            buckets[i] = new ArrayList<>();
        }

        // 分配元素到桶
        for (int num : arr) {
            int bucketIndex = (num - min) / bucketSize;
            buckets[bucketIndex].add(num);
        }

        // 对每个桶排序并合并
        int index = 0;
        for (ArrayList<Integer> bucket : buckets) {
            if (bucket.size() > 0) {
                Collections.sort(bucket);
                for (int num : bucket) {
                    arr[index++] = num;
                }
            }
        }

        return arr;
    }
}
```

### 10.3 基数排序（Radix Sort）

按低位到高位（或高位到低位）逐位排序，每一位的排序使用稳定的排序算法（通常是计数排序）。

```java
/**
 * 基数排序
 * 适用于：非负整数或可以映射为非负整数的数据
 * 时间复杂度：O(d * (n + k))，d 为位数，k 为进制
 * 空间复杂度：O(n + k)
 * 稳定性：稳定
 */
public class RadixSort {

    /**
     * LSD（Least Significant Digit）基数排序：从低位开始
     */
    public static void radixSortLSD(int[] arr) {
        if (arr == null || arr.length == 0) return;

        // 找出最大值，确定位数
        int max = arr[0];
        for (int num : arr) {
            max = Math.max(max, num);
        }

        // 从低位到高位，依次进行计数排序
        for (int exp = 1; max / exp > 0; exp *= 10) {
            countingSortByDigit(arr, exp);
        }
    }

    private static void countingSortByDigit(int[] arr, int exp) {
        int n = arr.length;
        int[] output = new int[n];
        int[] count = new int[10];  // 0-9 十个桶

        // 统计每个桶的元素个数
        for (int num : arr) {
            int digit = (num / exp) % 10;
            count[digit]++;
        }

        // 累加计数
        for (int i = 1; i < 10; i++) {
            count[i] += count[i - 1];
        }

        // 从后向前遍历，保证稳定性
        for (int i = n - 1; i >= 0; i--) {
            int digit = (arr[i] / exp) % 10;
            output[count[digit] - 1] = arr[i];
            count[digit]--;
        }

        System.arraycopy(output, 0, arr, 0, n);
    }

    /**
     * MSD（Most Significant Digit）基数排序：从高位开始
     * 可以用递归实现，适合字符串排序
     */
    public static void radixSortMSD(String[] arr) {
        if (arr == null || arr.length == 0) return;
        radixSortMSDHelper(arr, 0, arr.length - 1, 0);
    }

    private static void radixSortMSDHelper(String[] arr, int low, int high, int digitIndex) {
        if (low >= high || digitIndex >= arr[low].length()) {
            return;
        }

        int[] count = new int[256 + 1];  // ASCII 字符 + 1 表示字符串结束
        String[] temp = new String[high - low + 1];

        // 统计每个桶的元素个数
        for (int i = low; i <= high; i++) {
            int d = charAt(arr[i], digitIndex) + 1;  // +1 区分字符串结束
            count[d]++;
        }

        // 累加计数
        for (int i = 1; i < count.length; i++) {
            count[i] += count[i - 1];
        }

        // 分配到临时数组
        for (int i = high; i >= low; i--) {
            int d = charAt(arr[i], digitIndex) + 1;
            temp[--count[d]] = arr[i];
        }

        // 拷贝回原数组
        for (int i = low; i <= high; i++) {
            arr[i] = temp[i - low];
        }

        // 递归处理每个桶
        for (int i = 0; i < count.length - 1; i++) {
            if (count[i + 1] > count[i]) {
                radixSortMSDHelper(arr, low + count[i], low + count[i + 1] - 1, digitIndex + 1);
            }
        }
    }

    /**
     * 获取字符串指定位置的字符（字符串长度不够时返回 -1）
     */
    private static int charAt(String s, int index) {
        if (index >= s.length()) {
            return -1;
        }
        return s.charAt(index);
    }

    /**
     * 处理负数的基数排序
     */
    public static void radixSortWithNegative(int[] arr) {
        if (arr == null || arr.length == 0) return;

        // 将数组分为负数和非负数两部分
        int max = Math.abs(arr[0]);
        for (int num : arr) {
            max = Math.max(max, Math.abs(num));
        }

        int[] negative = new int[arr.length];
        int[] positive = new int[arr.length];
        int negCount = 0, posCount = 0;

        for (int num : arr) {
            if (num < 0) {
                negative[negCount++] = -num;  // 取绝对值
            } else {
                positive[posCount++] = num;
            }
        }

        // 分别对负数和非负数进行基数排序
        int[] negSorted = new int[negCount];
        int[] posSorted = new int[posCount];

        System.arraycopy(negative, 0, negSorted, 0, negCount);
        System.arraycopy(positive, 0, posSorted, 0, posCount);

        if (negCount > 0) {
            radixSortLSD(negSorted);
            // 负数结果取反并反转顺序
            for (int i = 0; i < negCount; i++) {
                arr[i] = -negSorted[negCount - 1 - i];
            }
        }

        if (posCount > 0) {
            radixSortLSD(posSorted);
            System.arraycopy(posSorted, 0, arr, negCount, posCount);
        }
    }
}
```

### 10.4 非比较排序对比

| 排序算法 | 时间复杂度 | 空间复杂度 | 稳定性 | 适用场景 |
|---------|-----------|-----------|--------|---------|
| 计数排序 | O(n + k) | O(k) | ✅ 稳定 | 整数，数据范围不大 |
| 桶排序 | O(n + k) ~ O(n²) | O(n + k) | 取决于桶内排序 | 数据分布均匀 |
| 基数排序 | O(d * (n + k)) | O(n + k) | ✅ 稳定 | 整数/固定长度字符串 |

---

## 十一、高频面试题

### 面试题 1：手写归并排序，并分析复杂度

**参考回答**：

归并排序采用分治策略，时间复杂度 O(n log n)，空间复杂度 O(n)。

```java
public void mergeSort(int[] arr, int left, int right) {
    if (left >= right) return;
    int mid = left + (right - left) / 2;
    mergeSort(arr, left, mid);
    mergeSort(arr, mid + 1, right);
    merge(arr, left, mid, right);
}
```

**复杂度分析**：
- 时间复杂度：递归深度为 log n，每层 merge 操作需要 O(n)，所以总体 O(n log n)
- 空间复杂度：需要 O(n) 的辅助数组 + O(log n) 的递归栈
- 稳定性：稳定（merge 时使用 `<=` 保证）

---

### 面试题 2：快速排序最坏情况是什么？如何优化？

**参考回答**：

**最坏情况**：数组已经有序（正序或逆序），且每次都选最大/最小值作为基准，导致分区极度不均匀，退化为 O(n²)。

**优化方案**：
1. **三数取中**：每次选取 left、mid、right 三个数的中位数作为基准
2. **随机基准**：随机选择基准，避免特定输入的攻击
3. **小规模切换**：当数据规模小于阈值时，切换到插入排序（减少递归开销）
4. **尾递归优化**：将递归改为迭代，避免栈溢出

---

### 面试题 3：什么场景下适合用插入排序而不是快速排序？

**参考回答**：

1. **数据规模小**（n ≤ 50）：插入排序的常数因子小，且对小规模数据 O(n²) 的复杂度并不会差太多
2. **近乎有序**：当数组接近有序时，插入排序的最好情况是 O(n)，而快速排序仍然是 O(n log n)
3. **链表排序**：链表不支持随机访问，无法使用快速排序（需要随机访问），但插入排序天然适合链表
4. **增量排序**：每次需要维护部分有序的情况（如在线算法），插入排序更合适

**加分点**：Java 的 Arrays.sort() 和 Python 的 TimSort 实际上正是这样做的——大规模用归并/快速排序，小规模数据切换到插入排序。

---

### 面试题 4：堆排序的时间复杂度为什么是 O(n log n)？

**参考回答**：

堆排序分两个阶段：

1. **构建堆**：对 n/2 个非叶子节点执行 heapify，每个 heapify 的时间复杂度是 O(log n)，所以构建堆的总时间 = O(n log n)。但实际上，更精确的分析表明构建堆的时间是 **O(n)**，因为叶子节点的 heapify 操作只需要常数时间。

2. **排序过程**：执行 n-1 次 "交换堆顶 + heapify"，每次 heapify 的时间复杂度是 O(log n)（树的高度），所以排序过程的时间复杂度 = (n-1) * O(log n) = **O(n log n)**。

因此，堆排序的总体时间复杂度是 O(n log n)。

**更精确的分析**（面试加分）：
- 构建堆：O(n)（因为树底层节点多但高度小，顶层节点少但高度大，均摊下来是线性的）
- 排序过程：O(n log n)
- 总体：O(n log n)

---

### 面试题 5：如何判断一个数组是否已经排好序？

**参考回答**：

```java
/**
 * 方法1：简单遍历 O(n)
 * 检查是否严格递增
 */
public boolean isSortedAscending(int[] arr) {
    for (int i = 0; i < arr.length - 1; i++) {
        if (arr[i] > arr[i + 1]) {
            return false;
        }
    }
    return true;
}

/**
 * 方法2：判断是升序还是降序
 * 返回值：1=升序，-1=降序，0=无序
 */
public int checkSortOrder(int[] arr) {
    if (arr == null || arr.length < 2) return 1;

    boolean ascending = true, descending = true;

    for (int i = 0; i < arr.length - 1; i++) {
        if (arr[i] < arr[i + 1]) descending = false;
        if (arr[i] > arr[i + 1]) ascending = false;
    }

    if (ascending) return 1;
    if (descending) return -1;
    return 0;
}

/**
 * 方法3：近乎有序的判断
 * 如果逆序对数量很少（如 < n * k），可以认为是近乎有序
 */
public boolean isNearlySorted(int[] arr, int k) {
    // 逆序对数量 <= k 时，可以通过 k 次相邻交换完成排序
    int inversions = 0;
    for (int i = 0; i < arr.length - 1 && inversions <= k; i++) {
        if (arr[i] > arr[i + 1]) {
            inversions++;
            swap(arr, i, i + 1);
        }
    }
    return inversions <= k;
}
```

---

## 十二、常见误区与面试技巧

### 12.1 稳定性在面试中的重要性

**稳定性**是排序算法中容易被忽略但面试中经常考查的概念。什么情况下需要稳定排序？

- **多关键字排序**：先按年龄排序，再按姓名排序。如果第一次排序不稳定，第二次排序后年龄的相对顺序可能被打乱。
- **电商排序**：先按销量排序，再按评分排序。如果排序不稳定，销量相同的商品评分顺序可能不一致。
- **数据库 ORDER BY**：多字段排序时，稳定排序确保第一个字段相同时按第二个字段的原始顺序排列。

### 12.2 排序算法的选择决策树

```
数据规模？
├── 小（n ≤ 50）
│   └── 插入排序（常数因子小）
└── 大
    ├── 需要稳定排序？
    │   ├── 是 → 归并排序 / TimSort
    │   └── 否
    │       ├── 近乎有序？→ 插入排序
    │       ├── Top K？→ 堆排序（O(n log k)）
    │       └── 一般情况 → 快速排序（三数取中版本）
```

### 12.3 面试回答模板

当面试官问"请介绍一下快速排序"时，推荐按照以下结构回答：

1. **一句话描述**：快速排序是一种基于分治策略的原地排序算法，通过选择基准将数组分为两部分，递归排序。
2. **核心步骤**：选择基准 → 分区（左边 ≤ 基准，右边 ≥ 基准）→ 递归排序左右两部分
3. **复杂度分析**：平均 O(n log n)，最坏 O(n²)（基准选择不当）
4. **稳定性**：不稳定（分区过程会改变相等元素的相对顺序）
5. **优化点**：三数取中、随机基准、小规模切换插入排序
6. **与归并排序对比**：快速排序是原地排序（O(1) 空间），归并排序稳定（O(n) 空间）

---

## 十三、总结

七大排序算法是面试中最基础也最重要的内容，需要熟练掌握每种算法的：

- ✅ **原理**：核心思想和实现思路
- ✅ **代码**：能手写或描述关键代码
- ✅ **复杂度**：时间、空间、稳定性的最好/平均/最坏情况
- ✅ **适用场景**：何时选哪种排序算法

记住一个核心规律：**没有完美的排序算法，只有适合特定场景的排序算法**。面试中不仅要会写代码，更要理解每种算法背后的 trade-off。

**祝你面试顺利，拿到理想 Offer！** 🎉
