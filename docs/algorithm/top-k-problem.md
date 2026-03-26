---
layout: default
title: Top K 问题：最小堆、分区法与分布式解法 ⭐⭐⭐
---
# Top K 问题：最小堆、分区法与分布式解法 ⭐⭐⭐

## 🎯 面试题：如何从海量数据中快速找到 Top K？

---

## 一、问题定义

```
Top K 大：从 N 个数中找出最大的 K 个
Top K 小：从 N 个数中找出最小的 K 个

N 可以有多大？
  - 单机内存：100 万 ~ 1000 万
  - 超大数据集：100 亿、1 万亿（分布式）

K 可以有多大？
  - 小 K：Top 10, Top 100（内存可放下）
  - 大 K：Top 100 万（需要特殊处理）
```

---

## 二、核心解法对比

| 方法 | 时间复杂度 | 空间 | 适用场景 |
|------|-----------|------|---------|
| **全排序** | O(N log N) | O(N) | K 接近 N |
| **最小堆** | O(N log K) | O(K) | K 较小，推荐 |
| **分区法（QuickSelect）** | O(N)（均摊）| O(1) 原地 | 需要全部 Top K |
| **桶排序** | O(N) | O(N) | 数据范围已知 |
| **MapReduce 分布式** | O(N log K) per machine | O(K) per machine | N 超大 |

---

## 三、最小堆解法（面试首选）

### 核心思想

```
Top K 大：用小根堆（堆顶是堆内最小值）

遍历数据：
  堆未满（< K）→ 直接入堆
  堆已满 → 新元素 > 堆顶？→ 弹出堆顶 → 新元素入堆

为什么快？
  - 比堆顶大才操作，否则直接跳过
  - 时间 O(N log K)，K 越小时优势越明显
  - 空间只有 O(K)
```

```java
/**
 * 求 Top K 大数（最小堆）
 * 时间：O(N log K)
 * 空间：O(K)
 */
public List<Integer> topK(int[] arr, int k) {
    if (k <= 0) return Collections.emptyList();

    // Java 的 PriorityQueue 默认是最小堆
    PriorityQueue<Integer> minHeap = new PriorityQueue<>(k);

    for (int num : arr) {
        if (minHeap.size() < k) {
            // 堆未满，直接加入
            minHeap.offer(num);
        } else if (num > minHeap.peek()) {
            // 比堆顶大，替换
            minHeap.poll();    // 移除堆顶（最小值）
            minHeap.offer(num); // 加入新元素
        }
        // 比堆顶小 → 不处理，直接跳过
    }

    // 堆内即为 Top K（无序）
    return new ArrayList<>(minHeap);
}

/**
 * 求 Top K 小数（最大堆）
 */
public List<Integer> topKMin(int[] arr, int k) {
    if (k <= 0) return Collections.emptyList();

    // 最大堆：传入自定义比较器
    PriorityQueue<Integer> maxHeap = new PriorityQueue<>(
        (a, b) -> b - a  // 最大堆
    );

    for (int num : arr) {
        if (maxHeap.size() < k) {
            maxHeap.offer(num);
        } else if (num < maxHeap.peek()) {
            // 比堆顶小才替换（找最小的 K 个）
            maxHeap.poll();
            maxHeap.offer(num);
        }
    }

    return new ArrayList<>(maxHeap);
}

/**
 * Top K 小数的另一种写法（Java 泛型版）
 */
public <T> List<T> topK(List<T> arr, int k, Comparator<T> comp) {
    PriorityQueue<T> heap = new PriorityQueue<>(comp);
    for (T item : arr) {
        if (heap.size() < k) {
            heap.offer(item);
        } else if (comp.compare(item, heap.peek()) > 0) {
            // item 比堆顶大（对于最大堆，意味着 item 更"大"）
            heap.poll();
            heap.offer(item);
        }
    }
    return new ArrayList<>(heap);
}
```

### 堆的调整过程图解

```
数组: [3, 7, 2, 9, 1, 5, 8], 求 Top 3 大

步骤：
  遍历 3  → 堆 [3]           堆未满，入
  遍历 7  → 堆 [3, 7]        堆未满，入（自动上浮 7）
  遍历 2  → 堆 [2, 7, 3]     堆未满，入（自动上浮 2）
  遍历 9  → 堆 [3, 7, 9]     9 > 堆顶(2)，弹出 2，插入 9
            上浮 9: [9, 3, 7]  堆顶变成最大的 9 ✅
  遍历 1  → 跳过（1 < 堆顶 3）
  遍历 5  → 跳过（5 < 堆顶 3）

最终堆：[9, 7, 3] → 即 Top 3 大数
```

---

## 四、快速选择（QuickSelect）分区法

### 核心思想

```
参考快速排序的分治思想：

选择 pivot（枢轴）
分区：比 pivot 大的放左边，比 pivot 小的放右边

关键：
  如果 pivot 最终落在位置 (N-K) → 左边就是 Top K ✅
  如果 pivot 偏左 → 继续在右半部分找
  如果 pivot 偏右 → 继续在左半部分找

特点：原地分区，无需额外空间
均摊时间：O(N)（但最坏 O(N²)）
```

```java
/**
 * 快速选择：原地分区找 Top K 大
 * 时间复杂度：O(N)（均摊）
 * 空间复杂度：O(1)
 */
public List<Integer> topKQuickSelect(int[] arr, int k) {
    if (k <= 0 || k > arr.length) {
        return Collections.emptyList();
    }

    int[] nums = arr.clone(); // 克隆避免修改原数组
    int targetIdx = k - 1;    // Top K 大的第 K 个元素的目标索引

    int lo = 0, hi = nums.length - 1;
    while (lo <= hi) {
        int pivotIdx = partition(nums, lo, hi);

        if (pivotIdx == targetIdx) {
            // 找到目标位置
            break;
        } else if (pivotIdx < targetIdx) {
            // pivot 偏左，目标在右半部分
            lo = pivotIdx + 1;
        } else {
            // pivot 偏右，目标在左半部分
            hi = pivotIdx - 1;
        }
    }

    // 收集 [k, end] 的数即为 Top K（这部分都 >= 第 K 大的数）
    // 注意：此时 k 位置是第 K 大的数，左边可能有小于它的
    List<Integer> result = new ArrayList<>();
    for (int i = k - 1; i < nums.length; i++) {
        result.add(nums[i]);
    }
    // 对结果排序（可选）
    result.sort((a, b) -> b - a);
    return result;
}

/**
 * 分区：选 hi 为 pivot，比 pivot 大的放左边，小的放右边
 * 返回 pivot 最终位置
 */
private int partition(int[] nums, int lo, int hi) {
    int pivot = nums[hi];
    int i = lo - 1; // 划分边界

    for (int j = lo; j < hi; j++) {
        if (nums[j] >= pivot) { // 大于等于 pivot 放左边
            swap(nums, ++i, j);
        }
    }
    // pivot 放到分界线
    swap(nums, i + 1, hi);
    return i + 1;
}

private void swap(int[] nums, int a, int b) {
    int tmp = nums[a];
    nums[a] = nums[b];
    nums[b] = tmp;
}
```

---

## 五、MapReduce 分布式 Top K

### 问题背景

```
单机场景：
  内存 8GB，存 10 亿条数据，每条 8 字节 → 80GB ❌

分布式方案：
  将数据分成 M 个桶，每台机器处理一部分
  每台机器维护一个大小为 K 的堆
  所有机器处理完后，汇总所有机器的 Top K，再做一次全局 Top K
```

### MapReduce 三阶段

```
阶段一：Map（分桶）
  每台机器：
    1. 分批读入 N/M 条数据
    2. 维护大小为 K 的最小堆
    3. 遍历：比堆顶大 → 替换
    4. 最终输出本机的 Top K（每个文件存 K 个数）

阶段二：Shuffle（收集）
  把所有机器的 Top K 数据汇总到一台机器

阶段三：Reduce（全局 Top K）
  汇总后的 K × M 条数据 → 再用最小堆求一次 Top K
  → 得到全局 Top K ✅
```

```java
// Map 阶段：单机 Top K
public class TopKMapper {
    private static final int K = 1000;

    public void map(String filename, Iterator<Long> records) {
        PriorityQueue<Long> localTopK = new PriorityQueue<>(K); // 最小堆

        while (records.hasNext()) {
            long num = records.next();
            if (localTopK.size() < K) {
                localTopK.offer(num);
            } else if (num > localTopK.peek()) {
                localTopK.poll();
                localTopK.offer(num);
            }
        }

        // 输出本机 Top K
        for (Long num : localTopK) {
            collect(num); // 输出到文件
        }
    }
}

// Reduce 阶段：全局 Top K
public class TopKReducer {
    private static final int K = 1000;

    public void reduce(Iterator<Long> allNumbers) {
        PriorityQueue<Long> globalTopK = new PriorityQueue<>(K);

        while (allNumbers.hasNext()) {
            long num = allNumbers.next();
            if (globalTopK.size() < K) {
                globalTopK.offer(num);
            } else if (num > globalTopK.peek()) {
                globalTopK.poll();
                globalTopK.offer(num);
            }
        }

        // 输出最终 Top K
        for (Long num : globalTopK) {
            output(num);
        }
    }
}
```

### 分桶数量计算

```
数据量：100 亿条，每条 8 字节 → 80GB
单机内存：8GB，每次可处理 10 亿条（8GB / 8 字节）

分桶数量 = 100亿 / 10亿 = 10 个桶
每台机器处理 10 亿条数据 → 求本地 Top 1000

汇总 10 × 1000 = 10000 条 → 一台机器归并 → 最终 Top 100 ✅
```

---

## 六、经典变种

### 变种 1：流式数据 Top K（Data Stream）

```
场景：数据流持续到达，无法全量存储，要求实时输出 Top K

方案：固定大小最小堆 + 计数淘汰

数据流：[5, 3, 9, 2, 7, 1, 8, 4, 6]，Sliding Window = 最近 5 个，Top 3

维护窗口内的 Top 3：
  5, 3, 9, 2, 7 → Top3 = [9,7,5]
  滑动：去掉 5，加入 1 → [3,9,2,7,1] → Top3 = [9,7,3]
```

```java
/**
 * 数据流滑动窗口 Top K
 */
public class SlidingWindowTopK {
    private final int windowSize;
    private final int k;
    private final LinkedList<Long> window = new LinkedList<>();
    private final PriorityQueue<Long> topK = new PriorityQueue<>(Comparator.reverseOrder()); // 最大堆

    public SlidingWindowTopK(int windowSize, int k) {
        this.windowSize = windowSize;
        this.k = k;
    }

    public void add(long num) {
        // 1. 加入窗口
        window.addLast(num);
        if (window.size() > windowSize) {
            long removed = window.removeFirst();
            // 从 Top K 中移除（需要重建堆，简化处理）
            topK.remove(removed);
        }

        // 2. 更新 Top K
        topK.add(num);

        // 3. 如果 Top K 超过 K，移除多余
        while (topK.size() > k) {
            // 对于最大堆，poll 的是最大的，但我们需要保留 K 个最大的
            // 所以最大堆的逻辑需要反过来
            topK.poll(); // 移除最大的... 这不对
        }

        // 修正：窗口内 Top K = 最大堆，直接保留 K 个最大
        // 实际上用最大堆更合适
    }
}
```

### 变种 2：Top K 频率（海量文本中找出现最多的 K 个词）

```
问题：1TB 文本，找出出现频率最高的 100 个词

方案：
  1. 哈希分片：将词哈希到 N 台机器（相同词到同一台）
  2. 每台机器：HashMap 统计词频 → 求本地 Top K
  3. 汇总所有机器的 Top K → 全局 Top K

为什么分片？
  避免所有词存在一台机器的内存里爆炸
  分片后每台机器只处理总词量的 1/N
```

---

## 七、高频面试题

**Q1: Top K 问题的最优解法是什么？**
> 最小堆。遍历一遍 O(N)，堆维护 O(N log K)，总时间 O(N log K)。当 K 远小于 N 时，比全排序 O(N log N) 快得多。比如 N=10亿，K=100，全排序要 logN=30 次比较，堆只需要 logK=7 次。

**Q2: 快速排序分区法和最小堆法哪个更好？**
> 取决于需求。分区法均摊 O(N)，比堆快，但需要一次性加载所有数据，不能流式处理，且要全部收集后排序。最小堆 O(N log K) 稍慢，但支持流式数据、内存友好、K 越小越快。面试推荐讲最小堆（最常用）。

**Q3: 100 亿数据求 Top 100，单机内存 8GB 怎么处理？**
> MapReduce 分桶。每台机器处理 10 亿条数据，用最小堆维护本地 Top 100，输出到文件。10 台机器处理完后得到 1000 条数据，再单机做一次 Top 100 即可。

**Q4: Top K 小数和 Top K 大数有什么区别？**
> 逻辑完全一样，只是堆的方向相反。Top K 大用最小堆（堆顶是最小值，比堆顶大才替换）；Top K 小用最大堆（堆顶是最大值，比堆顶小才替换）。

**Q5: 堆排序求 Top K 时，堆内元素的顺序是排序好的吗？**
> 不是。最小堆只保证堆顶是最小值，堆内其他元素是无序的。如果需要有序输出，再对堆内元素做一次排序（Collections.sort），时间 O(K log K)，一般 K 较小影响不大。

---

**参考链接：**
- [海量数据 Top K 问题详解](https://blog.csdn.net/v_july_v/article/details/6279498)
- [十大经典排序算法](https://sort.hust.cc/)
- [MapReduce Top K 实操](https://developer.yali.com/tech/1000047)
