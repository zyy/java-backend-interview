---
layout: default
title: 如何统计 UV、独立访客与海量数据去重？⭐⭐⭐
---
# 如何统计 UV、独立访客与海量数据去重？

## 🎯 面试题：DAU 如何统计？40 亿数据如何去重？

---

## 一、UV 统计的核心矛盾

```
DAU = 一天内有多少独立用户访问了系统

❌ 直接 COUNT(DISTINCT user_id)
   → 亿级数据，全表去重，查询极慢
   → 100ms~几秒的延迟，无法实时

✅ 方案：专用数据结构，在写入时去重
   → HyperLogLog / Bitmap / HashSet
   → 查询 O(1)，毫秒级返回
```

---

## 二、HyperLogLog（生产推荐方案）

### 原理

```
HyperLogLog 是一种概率算法：
  通过哈希函数将每个 userId 映射为一个 64 位二进制串
  统计二进制串从左开始连续出现的最大 0 前缀长度：maxZeros
  估计基数 ≈ 2^maxZeros

举例：
  哈希值 001011... → 前导零 = 2
  哈希值 0001011... → 前导零 = 3

  maxZeros = 3 → 估计基数为 2^3 = 8

误差率：约 0.81%（可接受）

空间：固定 12KB，存 2^64 个数的基数 ✅
```

```java
@Service
@Slf4j
public class UvService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final String UV_KEY_PREFIX = "uv:daily:";

    /**
     * 记录一次访问
     * userId 可以是登录用户 ID，也可以是匿名访客的 cookie/session ID
     */
    public void recordVisit(String userId) {
        LocalDate today = LocalDate.now();
        String key = UV_KEY_PREFIX + today;
        // PFADD 自动去重
        redisTemplate.opsForHyperLogLog().add(key, userId);
    }

    /**
     * 获取当天 DAU
     */
    public long getDailyUv() {
        String key = UV_KEY_PREFIX + LocalDate.now();
        return redisTemplate.opsForHyperLogLog().size(key);
    }

    /**
     * 获取时间段内 UV（去重合并）
     * 例：过去 7 天的去重 UV
     */
    public long getUvBetween(LocalDate start, LocalDate end) {
        List<String> keys = new ArrayList<>();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            keys.add(UV_KEY_PREFIX + d.toString());
        }
        if (keys.isEmpty()) return 0;

        return redisTemplate.opsForHyperLogLog().size(
            keys.toArray(new String[0])
        );
    }

    /**
     * 设置过期时间（保留 90 天）
     */
    @Scheduled(cron = "0 5 0 * * ?") // 每天凌晨 00:05 执行
    public void setKeyExpire() {
        LocalDate today = LocalDate.now();
        String key = UV_KEY_PREFIX + today;
        redisTemplate.expire(key, 90, TimeUnit.DAYS);
    }
}
```

### 精确去重合并场景

```
需求：同时统计 DAU、周 UV、月 UV

实现：用 HyperLogLog 做周/月合并

周 UV = PFCOUNT 周一 Key + 周二 Key + ... + 周日 Key
       → 自动去重，返回真实周独立访客数
```

---

## 三、Bitmap 方案（精确版）

### 适用条件

```
用户 ID 必须满足：
  ✅ 是数字类型
  ✅ 范围已知且相对连续（如 1 ~ 1 亿）
  ✅ 可预测最大值

原理：每个 bit 代表一个用户 ID
  bit[1] = 1 → 用户 ID 1 今天访问过
  bit[2] = 1 → 用户 ID 2 今天访问过
  COUNT(bit == 1) = DAU

空间：1 亿用户 = 100,000,000 bits ≈ 12.5MB ✅
```

```java
@Service
@Slf4j
public class UvBitmapService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * 用户访问 → 对应 bit 位置 1
     */
    public void recordVisit(long userId) {
        LocalDate today = LocalDate.now();
        String key = String.format("uv:bitmap:%s", today);
        // userId - 1，因为 bit 从 0 开始
        redisTemplate.opsForValue().setBit(key, userId - 1, true);
    }

    /**
     * 获取当天 DAU
     */
    public long getDailyUv() {
        String key = String.format("uv:bitmap:%s", LocalDate.now());
        return redisTemplate.opsForValue().bitCount(key);
    }

    /**
     * 获取指定用户今天是否访问
     */
    public boolean hasVisited(long userId) {
        String key = String.format("uv:bitmap:%s", LocalDate.now());
        return Boolean.TRUE.equals(
            redisTemplate.opsForValue().getBit(key, userId - 1)
        );
    }

    /**
     * 跨天 UV 合并（BITOP OR）
     */
    public long getUvBetween(LocalDate start, LocalDate end) {
        String destKey = String.format("uv:bitmap:merged:%s_%s", start, end);
        List<String> srcKeys = new ArrayList<>();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            srcKeys.add(String.format("uv:bitmap:%s", d));
        }

        // BITOP OR：将所有天的 bitmap OR 合并，结果存 destKey
        redisTemplate.opsForValue().bitOp(
            RedisStringCommands.BitOperation.OR,
            destKey,
            srcKeys.toArray(new String[0])
        );

        long uv = redisTemplate.opsForValue().bitCount(destKey);
        // 合并完删除临时 key
        redisTemplate.delete(destKey);
        return uv;
    }
}
```

### HyperLogLog vs Bitmap 对比

| 指标 | HyperLogLog | Bitmap |
|------|-------------|--------|
| 空间 | 固定 12KB | userId 最大值 / 8 |
| 精度 | ≈ 0.81% 误差 | 100% 精确 |
| 适用 DAU | 亿级 | 百万~亿级（ID 连续） |
| 合并去重 | PFCOUNT 多 key | BITOP OR |
| 适用场景 | 精确度要求不高 | 需要 100% 精确 |

---

## 四、40 亿数据去重方案

### 问题分析

```
40 亿 QQ 号，1GB 内存
每个 QQ 号 8 字节（long）→ 320GB ❌

目标：在 1GB 内存内完成去重

核心思路：
  1. 用 bit 代替 byte（节省 8 倍空间）
  2. 分桶处理（将数据分散到多个桶）
  3. 外部排序（数据在外存，分批读入）
```

### 方案一：Bitmap（QQ 号范围已知）

```
QQ 号范围：100000000 ~ 2999999999（约 29 亿个可能的号码）
29 亿 bits ≈ 360MB ✅ 1GB 内存足够
```

```python
# Python 伪代码
import bitarray

QQ_MIN = 100_000_000
QQ_MAX = 2_999_999_999
BIT_COUNT = QQ_MAX - QQ_MIN  # ≈ 29 亿

# 创建 bitmap
bits = bitarray.bitarray(BIT_COUNT)
bits.setall(0)

duplicates = 0
unique = 0

# 遍历 40 亿 QQ 号（分批从文件/数据库读取）
with open("qq_numbers.dat", "rb") as f:
    while True:
        batch = f.read(8_000_000)  # 每次读 800 万个
        if not batch: break
        for i in range(0, len(batch), 8):
            qq = int.from_bytes(batch[i:i+8], 'big')
            offset = qq - QQ_MIN
            if bits[offset]:
                duplicates += 1
            else:
                bits[offset] = 1
                unique += 1

print(f"唯一 QQ 号: {unique}, 重复: {duplicates}")
# 空间：≈ 360MB + 少量处理开销
```

### 方案二：外部排序归并（通用方案）

```
内存 1GB：每次读 5000 万条（5000万 × 8字节 = 400MB）

步骤：
  1. 分批读取：40亿条分 80 批读入内存
  2. 每批内部排序：QuickSort O(N log N)
  3. 每批排好序后写入临时文件（共 80 个临时文件）
  4. 多路归并：每次从 80 个文件各取一条，取最小的输出
     → 相同号码相邻输出 → 跳过重复 → 最终唯一序列
```

```java
public class ExternalMergeSort {

    private static final long BATCH_SIZE = 50_000_000L; // 5000 万条

    /**
     * 第一阶段：分批排序写文件
     */
    public void phase1Sort(String inputFile, List<String> tempFiles) throws IOException {
        long totalRecords = countRecords(inputFile);
        long batches = (totalRecords + BATCH_SIZE - 1) / BATCH_SIZE;

        try (FileInputStream fis = new FileInputStream(inputFile);
             BufferedInputStream bis = new BufferedInputStream(fis, 8 * 1024 * 1024);
             DataInputStream dis = new DataInputStream(bis)) {

            for (long b = 0; b < batches; b++) {
                long[] batch = new long[(int) Math.min(BATCH_SIZE, totalRecords - b * BATCH_SIZE)];
                for (int i = 0; i < batch.length; i++) {
                    batch[i] = dis.readLong();
                }
                Arrays.sort(batch);
                String tempFile = "/tmp/sorted_" + b + ".bin";
                writeSortedBatch(tempFile, batch);
                tempFiles.add(tempFile);
            }
        }
    }

    /**
     * 第二阶段：N 路归并去重
     */
    public void phase2Merge(List<String> tempFiles, String outputFile) throws IOException {
        // 1. 初始化 N 个文件的迭代器
        PriorityQueue<RecordPointer> heap = new PriorityQueue<>();
        List<DataInputStream> inputs = new ArrayList<>();

        for (int i = 0; i < tempFiles.size(); i++) {
            DataInputStream dis = new DataInputStream(
                new BufferedInputStream(new FileInputStream(tempFiles.get(i)), 1024 * 1024));
            inputs.add(dis);
            if (dis.available() > 0) {
                heap.add(new RecordPointer(i, dis.readLong()));
            }
        }

        // 2. 归并输出
        try (BufferedOutputStream bos = new BufferedOutputStream(
                new FileOutputStream(outputFile), 8 * 1024 * 1024);
             DataOutputStream dos = new DataOutputStream(bos)) {

            long last = -1;
            while (!heap.isEmpty()) {
                RecordPointer min = heap.poll();
                long current = min.value;

                // 去重：只输出与上一个不同的
                if (current != last) {
                    dos.writeLong(current);
                    last = current;
                }

                // 从同一文件读下一条
                DataInputStream dis = inputs.get(min.fileIndex);
                if (dis.available() >= 8) {
                    min.value = dis.readLong();
                    heap.add(min);
                }
            }
        }
    }
}
```

### 方案三：布隆过滤器 + 二次确认

```
第一步：40 亿条全部过布隆过滤器
  - 不存在 → 一定不重复 ✅
  - 存在 → 可能重复，需要二次确认

第二步：把判断为"可能重复"的写入文件
  文件内排序去重

布隆过滤器参数：
  - n = 40 亿
  - 期望假阳性率 p = 0.01（1%）
  - m = -n * ln(p) / (ln(2)^2) ≈ 5.1 GB ≈ 480MB ✅
  - k = ln(2) * m / n ≈ 7 个哈希函数
```

---

## 五、DAU 亿级统计实战架构

```
┌──────────────────────────────────────────────────────┐
│                   DAU 统计架构                         │
│                                                       │
│  用户访问 → 写入 Kafka → Flink 实时聚合               │
│                         │                             │
│                    PFADD uv:daily:2026-03-26         │
│                         │                             │
│                    Redis HyperLogLog                   │
│                         │                             │
│               查询 → 毫秒级返回 DAU                    │
│                                                       │
│  备选：每小时预聚合 → 结果写 Redis → 查询直接读         │
└──────────────────────────────────────────────────────┘
```

```java
/**
 * Flink 实时 DAU 统计（Kafka → Redis）
 */
public class DailyUvJob {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        DataStream<String> events = env
            .addSource(new FlinkKafkaConsumer<>("user_visit", new JsonSchema(), props))
            .uid("kafka-source");

        events.keyBy(e -> e.getDate())  // 按天分组
            .window(SlidingEventTimeWindows.of(Time.hours(1), Time.hours(1)))
            .apply(new UvAggregator())
            .addSink(new RedisSink<>()); // 结果写入 Redis

        env.execute("Daily UV Job");
    }

    // 聚合函数：PFADD
    public static class UvAggregator
            implements WindowFunction<String, Long, String, TimeWindow> {

        @Override
        public void apply(String key, TimeWindow window,
                         Iterable<String> records, Collector<Long> out) {
            RedisCommands<String, String> redis = jedisPool.getResource();
            String hllKey = "uv:daily:" + key;
            for (String userId : records) {
                redis.pfadd(hllKey, userId);
            }
            long uv = redis.pfcount(hllKey);
            out.collect(uv);
        }
    }
}
```

---

## 六、高频面试题

**Q1: HyperLogLog 的误差是怎么产生的？**
> 通过哈希后的二进制串前导零个数来估算基数，天然有统计误差。公式：误差率 ≈ 1.04 / sqrt(2^m)，m=registers 数量。Redis HyperLogLog 有 16384 个 registers，误差 ≈ 0.81%，即 1 亿 DAU 的误差在 81 万以内。

**Q2: 40 亿数据用 1GB 内存去重，哪种方案最优？**
> 如果 QQ 号范围已知且跨度不大，用 Bitmap（5 亿 bit ≈ 360MB）。如果号段跨度大且不连续，用外部排序归并（分批读入内存→排序→多路归并去重）。布隆过滤器适合"先判断存在性"而非精确去重场景。

**Q3: DAU 统计的冷启动怎么处理？**
> 每天凌晨从 DB 导出全量用户 ID，PFADD 到 Redis HyperLogLog重建当日数据。如果 Redis 故障降级，直接从 DB COUNT(DISTINCT user_id WHERE login_date = today)。

**Q4: 分布式 UV 怎么统计？**
> 每个机房/服务节点维护自己的 HyperLogLog，最后合并所有节点的 Key。PFCOUNT 支持多 Key 合并，自动去重，不存在重复计数问题。

---

**参考链接：**
- [Redis HyperLogLog 命令参考](https://redis.io/commands/pfadd/)
- [HyperLogLog 算法原理](https://zhuanlan.zhihu.com/p/58226915)
- [海量数据去重方案](https://blog.csdn.net/qq_35190492/article/details/108412891)
