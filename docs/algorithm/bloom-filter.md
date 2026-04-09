---
layout: default
title: 布隆过滤器原理与实战：从入门到面试 ⭐⭐⭐
---

# 布隆过滤器原理与实战：从入门到面试 ⭐⭐⭐

## 一、引言：什么是布隆过滤器？

布隆过滤器（Bloom Filter）由 Burton Howard Bloom 于 1970 年提出，是一种空间效率极高的**概率型数据结构**。它主要用于判断一个元素是否**可能存在**于一个集合中，能够以极小的内存代价快速回答"这个元素在不在集合里"这个问题。

布隆过滤器的核心特点是：

- **可能存在假阳性（False Positive）**：如果布隆过滤器说"可能存在"，那元素可能真的存在，也可能不存在。
- **绝对不存在假阴性（False Negative）**：如果布隆过滤器说"一定不存在"，那元素就**一定不存在**。
- **不支持删除操作**（除非使用计数布隆过滤器）。

理解布隆过滤器对于后端工程师至关重要，它是大规模数据处理、缓存系统、爬虫系统等场景中的核心技术之一，也是 Java 后端面试中的高频考点。

## 二、底层原理：位图 + 哈希函数

### 2.1 位图（BitMap）基础

位图是一种用每一位（bit）来表示某种状态的数据结构。假设我们有一个长度为 `m` 的位数组，所有位初始值都为 0。

```
位数组: [0] [1] [2] [3] [4] [5] [6] [7] [8] [9] ... [m-1]
初始值:  0   0   0   0   0   0   0   0   0   0       0
```

当要添加一个元素时，我们用 `k` 个不同的哈希函数分别计算该元素的哈希值，得到 `k` 个哈希值 `h1(x), h2(x), ..., hk(x)`，然后将这 `k` 个哈希值对 `m` 取模，得到 `k` 个位数组下标，将这 `k` 个位置的值从 0 设为 1。

```
添加元素 "hello":
  哈希函数1 → h1("hello") = 3  →  将位[3]设为1
  哈希函数2 → h2("hello") = 7  →  将位[7]设为1
  哈希函数3 → h3("hello") = 11 →  将位[11]设为1
```

当要查询一个元素是否存在时，用同样的 `k` 个哈希函数计算 `k` 个下标，检查这 `k` 个位置是否**全部为 1**：

- 如果**全部为 1** → 返回"可能存在"（True Positive / False Positive）
- 如果**任意一个为 0** → 返回"一定不存在"（True Negative）

### 2.2 哈希函数的选择

理想的哈希函数需要满足以下条件：

1. **计算速度快**：因为每个元素需要经过 `k` 个哈希函数计算。
2. **分布均匀**：哈希值应均匀分布在 `[0, m-1]` 范围内，避免哈希碰撞集中在某些区域。
3. **相互独立**：多个哈希函数之间应尽量相互独立。

常用的哈希函数组合包括 MurmurHash、MD5（不推荐，速度慢）、SHA 系列（不推荐，速度慢）、Guava 提供的 MurmurHash 等。在生产环境中，通常使用多个 MurmurHash 函数或者对同一个哈希值进行不同盐值的二次哈希。

```
二次哈希生成多个哈希值（避免多个独立哈希函数）：
  h(i, x) = h1(x) + i * h2(x) mod m

其中 h1(x) 和 h2(x) 是两个独立的哈希函数，i = 0, 1, 2, ..., k-1
```

### 2.3 为什么需要多个哈希函数？

单个哈希函数会导致大量哈希碰撞。例如，如果只用 1 个哈希函数，那么所有不同的元素都会竞争同一个位数组的槽位，很快就会导致位数组几乎填满。

多个哈希函数通过将"元素映射到多个位"来降低碰撞概率。一个元素对应多个位，只有当这多个位都被其他元素占据时，才会发生误判（假阳性）。但哈希函数数量也并非越多越好，需要在误判率和空间利用率之间找到平衡。

## 三、核心数学公式：误判率分析

### 3.1 误判率公式推导

假设位数组长度为 `m`，集合中有 `n` 个元素，使用的哈希函数数量为 `k`。

**位数组中某一位在插入 n 个元素后仍为 0 的概率：**

一个哈希函数将某个元素映射到位数组中某一位的概率为 `1/m`，因此映射后该位仍为 0 的概率为 `(1 - 1/m)`。对于 `k` 个哈希函数，插入一个元素后某位仍为 0 的概率为 `(1 - 1/m)^k`。

插入 `n` 个元素后，该位仍为 0 的概率为：

```
P(该位为0) = (1 - 1/m)^(kn) ≈ e^(-kn/m)
```

（根据极限公式：当 m 很大时，(1 - 1/m)^m ≈ 1/e）

**位数组中某一位被设置为 1 的概率：**

```
P(该位为1) = 1 - e^(-kn/m)
```

**误判率（fpp, false positive probability）：**

当查询一个不存在的元素时，需要检查 `k` 个位，这 `k` 个位**恰好全部为 1**（导致误判）的概率为：

```
f = P(某位为1)^k = (1 - e^(-kn/m))^k
```

这就是布隆过滤器的**误判率公式**：

```
f = (1 - e^(-kn/m))^k
```

### 3.2 最优哈希函数数量

对误判率公式求导，可以找到使得误判率最低的哈希函数数量 `k`：

```
k_opt = (m/n) * ln(2) ≈ 0.693 * (m/n)
```

即：**最优哈希函数数量 ≈ (位数组长度 / 插入元素数量) × ln(2)**

### 3.3 最优位数组长度

在实际应用中，通常会先确定两个关键参数：预计插入元素数量 `n` 和期望的误判率 `p`，然后反推最优的位数组长度 `m`：

```
m = - (n * ln(p)) / (ln(2)^2)
```

例如，假设要插入 1000 万个 URL，要求误判率不超过 1%，则：

```
m = - (10^7 * ln(0.01)) / (0.693^2) ≈ 9.585 MB 空间
```

| 预计元素数 n | 误判率 p | 位数组大小 m | 最优哈希数 k |
|---|---|---|---|
| 1000万 | 0.01 (1%) | ~95.85 Mb (~12MB) | ~7 |
| 1000万 | 0.001 (0.1%) | ~143.78 Mb (~18MB) | ~10 |
| 1亿 | 0.01 (1%) | ~958.5 Mb (~120MB) | ~7 |

## 四、Guava BloomFilter 实战

### 4.1 Maven 依赖

```xml
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
    <version>32.1.3-jre</version>
</dependency>
```

### 4.2 基本使用

```java
import com.google.common.base.Charsets;
import com.google.common.hash.BloomFilter;
import com.google.common.hash.Funnels;

public class BloomFilterDemo {

    public static void main(String[] args) {
        // 创建一个预期插入 1000 个元素的布隆过滤器，期望误判率为 0.01 (1%)
        BloomFilter<String> bloomFilter = BloomFilter.create(
            Funnels.stringFunnel(Charsets.UTF_8),
            1000,          // 预期插入数量
            0.01           // 期望误判率
        );

        // 添加元素
        bloomFilter.put("https://www.example.com/page1");
        bloomFilter.put("https://www.example.com/page2");
        bloomFilter.put("https://www.example.com/page3");

        // 检查元素
        System.out.println(bloomFilter.mightContain("https://www.example.com/page1")); // true
        System.out.println(bloomFilter.mightContain("https://www.example.com/page4")); // false 或 true（误判）
        System.out.println(bloomFilter.mightContain("not-exists")); // false（确定不存在）
    }
}
```

### 4.3 在 Redis 场景中的集成

在分布式系统中，通常使用 Redis 来部署布隆过滤器，以供多个服务实例共享。

```java
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class BloomFilterService {

    private final RedisTemplate<String, String> redisTemplate;
    private static final String BLOOM_FILTER_KEY = "bloom:urls";

    public BloomFilterService(RedisTemplate<String, String> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * 添加 URL 到布隆过滤器
     */
    public void addUrl(String url) {
        redisTemplate.opsForValue().setBit(BLOOM_FILTER_KEY, generateBitIndex(url), true);
    }

    /**
     * 批量添加 URL
     */
    public void addUrls(List<String> urls) {
        urls.forEach(this::addUrl);
    }

    /**
     * 检查 URL 是否可能存在于过滤器中
     */
    public boolean mightContain(String url) {
        long bitIndex = generateBitIndex(url);
        Boolean result = redisTemplate.opsForValue().getBit(BLOOM_FILTER_KEY, bitIndex);
        return Boolean.TRUE.equals(result);
    }

    /**
     * 生成位数组索引（简化版本，实际生产中应使用多个哈希函数）
     */
    private long generateBitIndex(String url) {
        int hash = url.hashCode();
        return Math.abs(hash);
    }
}
```

## 五、RedisBloom 模块详解

Redis 从 4.0 版本开始支持插件化扩展，RedisBloom 是其中一个非常流行的模块，提供了原生布隆过滤器支持。

### 5.1 安装 RedisBloom

```bash
# 使用 Docker 安装
docker run -d -p 6379:6379 redislabs/rebloom:latest

# 或者编译安装
git clone https://github.com/RedisBloom/RedisBloom.git
cd RedisBloom
make
```

### 5.2 核心命令

**创建布隆过滤器：**

```redis
# 创建一个默认精度的布隆过滤器
BF.ADD bloom_key "item1"

# 创建自定义参数的布隆过滤器
# capacity: 预计元素数量
# error_rate: 期望误判率
BF.RESERVE bloom_key 0.01 1000000
```

**检查元素是否存在：**

```redis
# 检查单个元素
BF.EXISTS bloom_key "item1"    # 返回 1（可能存在）或 0（一定不存在）

# 批量检查多个元素
BF.MEXISTS bloom_key "item1" "item2" "item3"
```

**获取布隆过滤器信息：**

```redis
BF.INFO bloom_key
# 返回：
#   Capacity: 1000000
#   Size: 1349092
#   Number of filters: 1
#   Number of items inserted: 500000
#   Expansion rate: 2
```

### 5.3 使用 RedisBloom 解决缓存穿透

缓存穿透是指查询一个**既不存在于缓存中、也不存在于数据库中**的数据，每次请求都会穿透到数据库，给数据库带来巨大压力。布隆过滤器是解决缓存穿透的经典方案之一。

```java
@Service
public class ProductService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final String BLOOM_FILTER_KEY = "bloom:product:ids";

    public ProductService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * 查询商品详情
     * 解决缓存穿透的核心逻辑：
     * 1. 先查布隆过滤器，如果返回不存在 → 直接返回 null（不查数据库）
     * 2. 如果返回可能存在 → 继续查 Redis 缓存
     * 3. 如果缓存未命中 → 查数据库
     */
    public Product getProduct(Long productId) {
        // 步骤1：布隆过滤器检查
        if (!bloomFilterMightContain(productId)) {
            // 布隆过滤器明确返回不存在，直接返回
            return null;
        }

        // 步骤2：查 Redis 缓存
        String cacheKey = "product:" + productId;
        Product cached = (Product) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }

        // 步骤3：查数据库
        Product product = productMapper.selectById(productId);

        // 步骤4：写缓存
        if (product != null) {
            redisTemplate.opsForValue().set(cacheKey, product, 1, TimeUnit.HOURS);
        }

        return product;
    }

    /**
     * 添加商品时同步更新布隆过滤器
     */
    public void addProduct(Product product) {
        productMapper.insert(product);
        // 添加商品后，将商品ID加入布隆过滤器
        addToBloomFilter(product.getId());
    }

    private boolean bloomFilterMightContain(Long productId) {
        // 调用 Redis 的 BF.EXISTS 命令
        return Boolean.TRUE.equals(
            redisTemplate.execute(new RedisCallback<Boolean>() {
                @Override
                public Boolean doInRedis(RedisConnection connection) throws DataAccessException {
                    return connection.commands().bFExists(
                        BLOOM_FILTER_KEY.getBytes(),
                        String.valueOf(productId).getBytes()
                    ) == 1;
                }
            })
        );
    }

    private void addToBloomFilter(Long productId) {
        redisTemplate.execute(new RedisCallback<Void>() {
            @Override
            public Void doInRedis(RedisConnection connection) throws DataAccessException {
                connection.commands().bFAdd(
                    BLOOM_FILTER_KEY.getBytes(),
                    String.valueOf(productId).getBytes()
                );
                return null;
            }
        });
    }
}
```

## 六、亿级 URL 去重场景

在大规模爬虫系统中，每天可能需要处理上亿个 URL 的去重工作。布隆过滤器是这一场景的首选方案。

### 6.1 场景分析

假设爬虫系统每天需要处理 **10 亿个 URL**，每个 URL 平均长度 100 字节。

如果使用哈希表（HashSet）来去重：
- 每个 URL 的哈希值需要 8 字节（64位）
- 10 亿 URL 需要 ~8 GB 内存
- 即使使用 Redis 的 Hash 结构，也会消耗大量内存

使用布隆过滤器：
- 10 亿 URL，误判率 1% 时，只需要约 **1.2 GB** 内存
- 相比哈希表节省约 85% 的空间

### 6.2 分布式布隆过滤器

单机布隆过滤器无法跨机器共享。可以采用以下方案：

**方案一：Redis 集中式布隆过滤器**

所有爬虫节点通过 RPC 或 HTTP 调用 Redis 服务，执行 BF.ADD 和 BF.EXISTS 操作。

优点：实现简单，数据集中管理。
缺点：Redis 可能成为性能瓶颈。

**方案二：一致性哈希分区**

将 URL 按某种规则（如哈希取模）分散到多个 Redis 布隆过滤器节点上。

```java
public class DistributedBloomFilter {

    private final List<String> redisNodes; // Redis 节点列表
    private final int nodeCount;

    public DistributedBloomFilter(List<String> redisNodes) {
        this.redisNodes = redisNodes;
        this.nodeCount = redisNodes.size();
    }

    /**
     * 根据 URL 的哈希值选择对应的 Redis 节点
     */
    private String getNodeForUrl(String url) {
        int hashCode = url.hashCode();
        int index = Math.abs(hashCode % nodeCount);
        return redisNodes.get(index);
    }

    public void addUrl(String url) {
        String node = getNodeForUrl(url);
        // 调用对应节点的 BF.ADD 命令
        redisTemplate.getConnectionFactory()
            .getConnection(node)
            .bfAdd(("bloom:" + node).getBytes(), url.getBytes());
    }

    public boolean mightContain(String url) {
        String node = getNodeForUrl(url);
        return redisTemplate.getConnectionFactory()
            .getConnection(node)
            .bfExists(("bloom:" + node).getBytes(), url.getBytes());
    }
}
```

### 6.3 分层去重策略

对于亿级 URL 去重，可以采用分层过滤策略进一步优化：

```
第一层：内存布隆过滤器（Hot URL，访问频繁）
        ↓ 未命中
第二层：Redis 布隆过滤器（今日 URL）
        ↓ 未命中
第三层：Redis 持久化 HashSet（最近 N 天的 URL，使用滑动窗口清理）
        ↓ 未命中
第四层：MySQL/ElasticSearch（全量 URL，需要支持精确查询）
        ↓ 未命中
→ 判定为新 URL，加入爬取队列
```

这种分层策略可以大大减少对后端存储的访问压力，80-90% 的请求可以在第一层和第二层被拦截。

## 七、计数布隆过滤器（支持删除）

标准布隆过滤器不支持删除操作，因为删除一个元素可能会影响其他元素的判断——某个位可能同时被多个元素共享。

### 7.1 原理

计数布隆过滤器（Counting Bloom Filter）将位数组的每一位扩展为一个计数器（通常用 3-4 位整数）。添加元素时，对应位置计数器 +1；删除元素时，计数器 -1。

```
标准布隆过滤器: [1] [0] [1] [1] [0] [0] [1] [0] [1]
计数布隆过滤器: [3] [0] [2] [1] [0] [0] [4] [0] [1]
                   ↑  ↑  ↑  ↑
                 计数器替代了单一的 0/1
```

### 7.2 计数布隆过滤器的权衡

优点：支持元素的删除操作。
缺点：
- 空间开销是标准布隆过滤器的 3-4 倍
- 计数器可能溢出（通常使用 3-4 位，溢出后截断为最大值）
- 仍然无法完全避免假阳性

### 7.3 应用场景

计数布隆过滤器常用于：
- **缓存淘汰策略**：配合缓存系统，动态添加和删除缓存 key 的记录。
- **黑名单动态管理**：需要动态增删黑名单元素的场景。
- **数据同步**：在 CDC（Change Data Capture）场景中跟踪已处理的变更。

## 八、布隆过滤器 vs 哈希表

| 特性 | 布隆过滤器 | 哈希表 |
|---|---|---|
| 空间复杂度 | O(m) 位，固定大小 | O(n)，与元素数量成正比 |
| 查询时间 | O(k)，k 个哈希函数，通常 k ≤ 10 | O(1) 平均，O(n) 最坏 |
| 假阳性 | 有（可控） | 无 |
| 假阴性 | **无** | **无** |
| 支持删除 | 不支持（标准版） | 支持 |
| 空间效率 | 极高（相同元素量下远小于哈希表） | 较低 |
| 精确查询 | 否 | 是 |
| 适用场景 | 大规模存在性判断、去重、缓存穿透 | 需要精确值的场景 |

**选择建议**：
- 数据量极大（百万、亿级）且容忍一定假阳性 → 布隆过滤器
- 需要精确判断且元素数量可控（万级以下）→ 哈希表
- 既要空间效率又要支持删除 → 计数布隆过滤器或布谷鸟过滤器

## 九、布谷鸟过滤器（Cuckoo Filter）

布谷鸟过滤器（Cuckoo Filter）是布隆过滤器的改进版，主要优点是支持删除操作且误判率相近的同时，空间利用率更高。

其原理基于"布谷鸟哈希"——使用两个哈希函数计算两个候选桶，如果两个桶都满了，就将其中一个桶中的某个元素"踢出"重新哈希（就像布谷鸟把其他鸟蛋推出窝一样）。

布谷鸟过滤器的查询和删除复杂度也是 O(1)，但实现复杂度高于布隆过滤器。Guava 从 23.0 版本开始也提供了 CuckooFilter 的实验性支持。

## 十、高频面试题

### 面试题 1：布隆过滤器的原理是什么？有什么优缺点？

**参考答案：**

布隆过滤器的原理是用一个长度为 `m` 的位数组和 `k` 个哈希函数。添加元素时，用 `k` 个哈希函数计算 `k` 个位置，将这 `k` 个位置设为 1。查询时，检查这 `k` 个位置是否全为 1：全为 1 返回"可能存在"，有 0 则返回"一定不存在"。

**优点：**
- 空间效率极高，比哈希表节省数倍到数十倍空间
- 查询速度快，时间复杂度 O(k)
- 简单易实现

**缺点：**
- 有假阳性，不能用于需要精确匹配的场景
- 不支持删除（标准版）
- 误判率受数据规模和哈希函数数量影响

---

### 面试题 2：如何计算布隆过滤器的误判率？给定场景如何选型？

**参考答案：**

误判率公式：`f = (1 - e^(-kn/m))^k`

其中 `n` 是元素数量，`m` 是位数组长度，`k` 是哈希函数数量。

**最优哈希函数数量：** `k = (m/n) × ln(2) ≈ 0.693 × (m/n)`

**给定元素数和误判率，求位数组长度：** `m = -n × ln(p) / (ln(2))^2`

**选型示例：**
假设需要存储 1 亿个用户 ID，期望误判率 ≤ 0.01，则：
`m = -10^8 × ln(0.01) / 0.48 ≈ 958 MB`
`k = 0.693 × (958 / 1) ≈ 7`

---

### 面试题 3：布隆过滤器如何解决缓存穿透？

**参考答案：**

缓存穿透的本质是查询大量不存在的数据，每次都穿透到数据库。

解决思路：在数据库前加一层布隆过滤器。

1. 系统启动时，将所有数据库中存在的 key 加载到布隆过滤器中。
2. 查询请求到来时，先通过布隆过滤器判断：
   - 布隆过滤器返回"不存在"→ 直接返回空结果，**不查数据库**
   - 布隆过滤器返回"可能存在"→ 继续查 Redis 缓存 → 查数据库
3. 写入数据时，同步将 key 加入布隆过滤器。

这样，大量恶意的不存在请求在布隆过滤器层就被拦截了，大幅降低数据库压力。

---

### 面试题 4：RedisBloom 有哪些常用命令？如何用 Java 操作？

**参考答案：**

RedisBloom 常用命令：

```redis
BF.ADD <key> <item>           # 添加元素
BF.EXISTS <key> <item>        # 检查元素是否存在
BF.MADD <key> <item1> <item2> # 批量添加
BF.MEXISTS <key> <item1> ...  # 批量检查
BF.RESERVE <key> <error_rate> <capacity>  # 创建自定义参数的布隆过滤器
BF.INFO <key>                 # 查看过滤器信息
```

Java 操作使用 Jedis 或 RedisTemplate：

```java
Jedis jedis = new Jedis("localhost", 6379);
// 添加
jedis.bfAdd("bloom:users", "user123");
// 检查
boolean exists = jedis.bfExists("bloom:users", "user123") == 1;
// 批量添加
List<String> items = Arrays.asList("a", "b", "c");
jedis.bfMAdd("bloom:users", items.stream()
    .map(SafeEncoder::encode)
    .toArray(byte[][]::new));
```

---

### 面试题 5：布隆过滤器的位数组大小如何确定？如果满了怎么办？

**参考答案：**

位数组大小由两个关键参数决定：
1. **预计插入元素数量 n**：越多需要的空间越大
2. **期望误判率 p**：越低需要的空间越大

计算公式：`m = -n × ln(p) / (ln(2))^2`

**如果位数组满了（所有位都变成1）：**
- 布隆过滤器会退化，所有查询都返回"可能存在"，完全失效。
- 解决方案：定期重建布隆过滤器（基于更大的位数组），或者采用**分层布隆过滤器**策略。
- 分层策略：将数据分片，每个分片用一个独立的布隆过滤器。当某个过滤器接近满时，创建新的过滤器。

---

### 面试题 6：布隆过滤器和布谷鸟过滤器有什么区别？什么时候用哪个？

**参考答案：**

| 特性 | 布隆过滤器 | 布谷鸟过滤器 |
|---|---|---|
| 支持删除 | 否（标准版） | 支持 |
| 空间效率 | 较高 | 更高（约节省 20-30% 空间） |
| 实现复杂度 | 简单 | 较复杂 |
| 查询性能 | O(k) | O(1) 最坏情况 |
| 插入性能 | O(k) | O(1) 均摊，可能失败需要重哈希 |
| 元素个数查询 | 不支持 | 支持（可以估算当前元素数） |

**选择建议：**
- 需要支持删除操作 → 优先选择布谷鸟过滤器
- 追求实现简单、稳定可靠 → 布隆过滤器
- 大规模数据场景 → 两者都需要先进行容量规划
