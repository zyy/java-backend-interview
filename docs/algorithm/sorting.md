# 排序算法

> 经典排序算法

## 🎯 面试重点

- 各排序算法原理
- 时间/空间复杂度

## 📖 算法对比

```java
/**
 * 排序算法对比
 */
public class SortingComparison {
    /*
     * | 算法     | 最好   | 平均   | 最坏   | 空间   | 稳定 |
     * |----------|--------|--------|--------|--------|------|
     * | 冒泡     | O(n)   | O(n²)  | O(n²)  | O(1)   | 是   |
     * | 选择     | O(n²)  | O(n²)  | O(n²)  | O(1)   | 否   |
     * | 插入     | O(n)   | O(n²)  | O(n²)  | O(1)   | 是   |
     * | 快排     | O(nlogn)|O(nlogn)|O(n²)  | O(logn)| 否   |
     * | 归并     | O(nlogn)|O(nlogn)|O(nlogn)|O(n)   | 是   |
     * | 堆排序   | O(nlogn)|O(nlogn)|O(nlogn)|O(1)   | 否   |
     */
}
```

## 📖 快速排序

```java
/**
 * 快速排序
 */
public class QuickSort {
    public static void sort(int[] arr, int left, int right) {
        if (left >= right) return;
        int pivot = partition(arr, left, right);
        sort(arr, left, pivot - 1);
        sort(arr, pivot + 1, right);
    }
    
    private static int partition(int[] arr, int left, int right) {
        int pivot = arr[right];
        int i = left;
        for (int j = left; j < right; j++) {
            if (arr[j] < pivot) {
                swap(arr, i++, j);
            }
        }
        swap(arr, i, right);
        return i;
    }
}
```

## 📖 面试真题

### Q1: 快排为什么快？

**答：** 平均 O(nlogn)，原地排序，缓存友好。

---

**⭐ 重点：排序是算法基础**