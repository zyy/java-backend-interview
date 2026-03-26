---
layout: default
title: 如何设计一个短链系统？⭐⭐⭐
---
# 如何设计一个短链系统？

## 🎯 面试题：设计一个高并发、高可用的短链系统

> 短链系统是互联网基础设施，广泛应用于微博、抖音、二维码等场景。需要支撑百亿级短链生成、千万级并发访问，同时保证低延迟和高可用。

---

## 一、短链系统的核心需求

### 业务场景

```
微博分享链接：
  长链：https://example.com/article/2024/03/26/why-short-url-matters?utm_source=weibo&utm_medium=share
  短链：https://t.co/abc123

二维码场景：
  长链：https://shop.example.com/product/12345?promo=spring2024&channel=offline
  短链：https://qr.example.com/xyz789

广告投放：
  长链：https://ads.example.com/campaign/2024/spring?utm_source=google&utm_medium=cpc&utm_campaign=spring_sale
  短链：https://ad.example.com/abc123
```

### 核心需求

```
功能需求：
  ✅ 长链 → 短链（生成）
  ✅ 短链 → 长链（跳转）
  ✅ 短链统计（访问量、来源、设备等）
  ✅ 短链管理（删除、过期、禁用）

非功能需求：
  ✅ 高吞吐：每秒生成 10 万+ 短链
  ✅ 低延迟：短链跳转 < 100ms
  ✅ 高可用：99.99% 可用性
  ✅ 可扩展：支持百亿级短链
  ✅ 安全性：防止恶意短链、防止被封禁
```

### 性能指标

```
写入（生成短链）：
  - QPS：10 万/秒
  - 延迟：P99 < 50ms
  - 吞吐：每天 10 亿+ 短链

读取（短链跳转）：
  - QPS：1000 万/秒（热点短链）
  - 延迟：P99 < 10ms
  - 缓存命中率：> 99%

存储：
  - 数据量：百亿级短链
  - 单条记录：~500 字节
  - 总存储：~5TB
```

---

## 二、短链生成方案对比

### 方案一：哈希算法

**思路**：对长链进行哈希，取前 6 位作为短链

```
长链：https://example.com/article/123
  ↓
MD5 哈希：5d41402abc4b2a76b9719d911017c592
  ↓
Base62 编码：9Yd7Aq
  ↓
短链：https://t.co/9Yd7Aq
```

**优点**：
- 相同长链生成相同短链（幂等性）
- 无需中心化发号器

**缺点**：
- 哈希冲突概率高（6 位 Base62 = 56 亿种组合，百亿数据冲突率 > 1%）
- 冲突处理复杂（追加随机数重试）
- 无法预测短链长度

```java
@Service
public class HashBasedShortUrlService {

    private static final String BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private static final int SHORT_URL_LENGTH = 6;

    /**
     * 哈希方案：MD5 + Base62 编码
     */
    public String generateShortUrl(String longUrl) {
        String hash = md5(longUrl);
        String base62 = toBase62(hash);
        
        // 取前 6 位
        String shortCode = base62.substring(0, SHORT_URL_LENGTH);

        // 检查冲突
        int retry = 0;
        while (isShortCodeExists(shortCode) && retry < 10) {
            // 冲突了，追加随机数重试
            String randomSuffix = UUID.randomUUID().toString().substring(0, 2);
            shortCode = (base62 + randomSuffix).substring(0, SHORT_URL_LENGTH);
            retry++;
        }

        if (retry >= 10) {
            throw new RuntimeException("Failed to generate unique short code after 10 retries");
        }

        return shortCode;
    }

    private String md5(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(input.getBytes());
            return bytesToHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    private String toBase62(String hex) {
        BigInteger num = new BigInteger(hex, 16);
        StringBuilder sb = new StringBuilder();
        while (num.compareTo(BigInteger.ZERO) > 0) {
            sb.insert(0, BASE62.charAt(num.mod(BigInteger.valueOf(62)).intValue()));
            num = num.divide(BigInteger.valueOf(62));
        }
        return sb.toString();
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private boolean isShortCodeExists(String shortCode) {
        return shortUrlMapper.selectByCode(shortCode) != null;
    }
}
```

---

### 方案二：发号器（推荐）

**思路**：中心化发号器分配递增 ID，然后 Base62 编码

```
发号器分配 ID：1, 2, 3, 4, ...
  ↓
Base62 编码：1, 2, 3, 4, ..., Z, 10, 11, ...
  ↓
短链：https://t.co/1, https://t.co/2, ...
```

**优点**：
- 无冲突
- 短链长度可预测
- 支持分布式扩展（雪花算法）

**缺点**：
- 需要中心化发号器
- ID 递增可能暴露业务量

```java
@Service
public class SequenceBasedShortUrlService {

    private static final String BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    @Autowired private IdGeneratorService idGeneratorService;
    @Autowired private ShortUrlMapper shortUrlMapper;

    /**
     * 发号器方案：递增 ID + Base62 编码
     */
    public String generateShortUrl(String longUrl) {
        // 1. 从发号器获取递增 ID
        long id = idGeneratorService.nextId();

        // 2. Base62 编码
        String shortCode = toBase62(id);

        // 3. 保存映射关系
        ShortUrl shortUrl = new ShortUrl();
        shortUrl.setId(id);
        shortUrl.setShortCode(shortCode);
        shortUrl.setLongUrl(longUrl);
        shortUrl.setCreatedAt(new Date());
        shortUrlMapper.insert(shortUrl);

        return shortCode;
    }

    /**
     * 将 ID 转换为 Base62
     * 例：1 → "1", 62 → "10", 3844 → "100"
     */
    public String toBase62(long id) {
        if (id == 0) return "0";

        StringBuilder sb = new StringBuilder();
        while (id > 0) {
            sb.insert(0, BASE62.charAt((int) (id % 62)));
            id /= 62;
        }
        return sb.toString();
    }

    /**
     * 将 Base62 转换回 ID
     */
    public long fromBase62(String code) {
        long id = 0;
        for (char c : code.toCharArray()) {
            id = id * 62 + BASE62.indexOf(c);
        }
        return id;
    }
}
```

---

### 方案三：号段模式（分布式发号器）

**思路**：中心数据库预分配号段，各服务器本地消费，减少数据库访问

```
数据库预分配：
  服务器 A：1-100000
  服务器 B：100001-200000
  服务器 C：200001-300000

各服务器本地消费，号段用完后再向数据库申请新号段
```

**优点**：
- 分布式，无单点
- 减少数据库访问
- 高吞吐

```java
@Service
@Slf4j
public class SegmentIdGeneratorService {

    @Autowired private IdSegmentMapper idSegmentMapper;

    // 本地号段缓存
    private final Map<String, IdSegment> segmentCache = new ConcurrentHashMap<>();

    // 号段用量达到 80% 时提前申请新号段
    private static final double THRESHOLD = 0.8;

    /**
     * 获取下一个 ID
     */
    public synchronized long nextId(String bizType) {
        IdSegment segment = segmentCache.computeIfAbsent(bizType, k -> {
            // 首次申请号段
            return allocateSegment(bizType);
        });

        // 检查号段是否用完
        if (segment.getCurrentId() >= segment.getMaxId()) {
            // 号段用完，申请新号段
            segment = allocateSegment(bizType);
            segmentCache.put(bizType, segment);
        }

        // 检查是否需要提前申请下一个号段（异步）
        if (segment.getCurrentId() >= segment.getMaxId() * THRESHOLD) {
            asyncAllocateNextSegment(bizType);
        }

        long id = segment.getCurrentId();
        segment.setCurrentId(id + 1);
        return id;
    }

    /**
     * 从数据库申请号段
     */
    private IdSegment allocateSegment(String bizType) {
        IdSegmentDO segmentDO = idSegmentMapper.selectByBizType(bizType);

        if (segmentDO == null) {
            // 首次初始化
            segmentDO = new IdSegmentDO();
            segmentDO.setBizType(bizType);
            segmentDO.setMaxId(100_000L);
            idSegmentMapper.insert(segmentDO);
        }

        // 申请新号段：[maxId, maxId + step)
        long step = 100_000L;
        long newMaxId = segmentDO.getMaxId() + step;

        // 更新数据库
        idSegmentMapper.updateMaxId(bizType, newMaxId);

        IdSegment segment = new IdSegment();
        segment.setCurrentId(segmentDO.getMaxId());
        segment.setMaxId(newMaxId);

        log.info("[IdGenerator] Allocated segment for {}: [{}, {})",
            bizType, segment.getCurrentId(), segment.getMaxId());

        return segment;
    }

    /**
     * 异步申请下一个号段（避免阻塞）
     */
    private void asyncAllocateNextSegment(String bizType) {
        CompletableFuture.runAsync(() -> {
            try {
                IdSegment nextSegment = allocateSegment(bizType);
                // 缓存下一个号段
                segmentCache.put(bizType + ":next", nextSegment);
            } catch (Exception e) {
                log.error("[IdGenerator] Failed to allocate next segment for {}", bizType, e);
            }
        });
    }

    @Data
    public static class IdSegment {
        private long currentId;
        private long maxId;
    }
}
```

---

## 三、分布式 ID 生成方案：雪花算法

### 雪花算法原理

```
64 位 Long 分布：
┌─────────────────────────────────────────────────────────────────┐
│ 1 bit │ 41 bit 时间戳 │ 10 bit 机器 ID │ 12 bit 序列号 │
│ 符号位 │ (毫秒级)     │ (1024 台机器)  │ (4096 个/ms)  │
└─────────────────────────────────────────────────────────────────┘

特点：
- 递增性：同一机器上 ID 递增
- 分布式：不同机器 ID 不重复
- 高性能：本地生成，无网络调用
- 时间戳：包含生成时间，可反推
```

```java
@Component
@Slf4j
public class SnowflakeIdGenerator {

    // 起始时间戳（2020-01-01）
    private static final long EPOCH = 1577836800000L;

    // 各部分位数
    private static final int TIMESTAMP_BITS = 41;
    private static final int MACHINE_ID_BITS = 10;
    private static final int SEQUENCE_BITS = 12;

    // 最大值
    private static final long MAX_MACHINE_ID = (1L << MACHINE_ID_BITS) - 1;
    private static final long MAX_SEQUENCE = (1L << SEQUENCE_BITS) - 1;

    private final long machineId;
    private long lastTimestamp = -1L;
    private long sequence = 0L;

    public SnowflakeIdGenerator(long machineId) {
        if (machineId > MAX_MACHINE_ID || machineId < 0) {
            throw new IllegalArgumentException("Machine ID must be between 0 and " + MAX_MACHINE_ID);
        }
        this.machineId = machineId;
    }

    /**
     * 生成下一个 ID
     */
    public synchronized long nextId() {
        long timestamp = System.currentTimeMillis();

        // 时钟回拨处理
        if (timestamp < lastTimestamp) {
            log.warn("[Snowflake] Clock moved backwards. Waiting...");
            timestamp = waitUntilNextMillis(lastTimestamp);
        }

        // 同一毫秒内，序列号递增
        if (timestamp == lastTimestamp) {
            sequence = (sequence + 1) & MAX_SEQUENCE;
            if (sequence == 0) {
                // 序列号溢出，等待下一毫秒
                timestamp = waitUntilNextMillis(lastTimestamp);
            }
        } else {
            // 新的毫秒，序列号重置
            sequence = 0L;
        }

        lastTimestamp = timestamp;

        // 组装 ID
        long id = ((timestamp - EPOCH) << (MACHINE_ID_BITS + SEQUENCE_BITS))
                | (machineId << SEQUENCE_BITS)
                | sequence;

        return id;
    }

    /**
     * 等待直到下一毫秒
     */
    private long waitUntilNextMillis(long lastTimestamp) {
        long timestamp = System.currentTimeMillis();
        while (timestamp <= lastTimestamp) {
            timestamp = System.currentTimeMillis();
        }
        return timestamp;
    }

    /**
     * 从 ID 反推生成时间
     */
    public static long getTimestamp(long id) {
        return ((id >> (MACHINE_ID_BITS + SEQUENCE_BITS)) + EPOCH);
    }

    /**
     * 从 ID 反推机器 ID
     */
    public static long getMachineId(long id) {
        return (id >> SEQUENCE_BITS) & MAX_MACHINE_ID;
    }
}
```

---

## 四、数据库表设计

### 短链表

```sql
CREATE TABLE short_url (
    id BIGINT PRIMARY KEY COMMENT '短链 ID（雪花算法生成）',
    short_code VARCHAR(10) NOT NULL UNIQUE COMMENT '短链编码（Base62）',
    long_url TEXT NOT NULL COMMENT '原始长链',
    user_id BIGINT COMMENT '创建用户 ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expired_at TIMESTAMP COMMENT '过期时间',
    status TINYINT DEFAULT 1 COMMENT '状态：1=正常，0=删除，-1=禁用',
    
    INDEX idx_short_code (short_code),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 访问统计表

```sql
CREATE TABLE short_url_stat (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_url_id BIGINT NOT NULL COMMENT '短链 ID',
    pv BIGINT DEFAULT 0 COMMENT '访问次数',
    uv BIGINT DEFAULT 0 COMMENT '独立用户数',
    click_date DATE NOT NULL COMMENT '统计日期',
    
    UNIQUE KEY uk_short_url_date (short_url_id, click_date),
    INDEX idx_short_url_id (short_url_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 访问明细表（可选，用于分析）

```sql
CREATE TABLE short_url_access_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_url_id BIGINT NOT NULL COMMENT '短链 ID',
    user_ip VARCHAR(50) COMMENT '访问 IP',
    user_agent VARCHAR(500) COMMENT '浏览器 UA',
    referer VARCHAR(500) COMMENT '来源',
    device_type VARCHAR(20) COMMENT '设备类型：PC/Mobile/Tablet',
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',
    
    INDEX idx_short_url_id (short_url_id),
    INDEX idx_accessed_at (accessed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 五、短链跳转的缓存策略

### 多级缓存架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户请求                              │
│                  GET /t/abc123                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  L1: 本地缓存（Caffeine）│  ← 毫秒级
        │  热点短链 100 条        │
        └────────────┬───────────┘
                     │ miss
                     ▼
        ┌────────────────────────┐
        │  L2: Redis 缓存         │  ← 微秒级
        │  热点短链 1000 万条     │
        └────────────┬───────────┘
                     │ miss
                     ▼
        ┌────────────────────────┐
        │  L3: MySQL 数据库       │  ← 毫秒级
        │  全量短链数据           │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  回源 + 更新缓存        │
        └────────────────────────┘
```

```java
@Service
@Slf4j
public class ShortUrlRedirectService {

    @Autowired private ShortUrlMapper shortUrlMapper;
    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private LoadingCache<String, String> localCache;

    private static final String REDIS_KEY_PREFIX = "short_url:";
    private static final long CACHE_TTL = 24 * 60 * 60; // 24 小时

    /**
     * 获取短链对应的长链（三级缓存）
     */
    public String getLongUrl(String shortCode) {
        // L1: 本地缓存（Caffeine）
        try {
            String longUrl = localCache.get(shortCode);
            if (longUrl != null && !longUrl.isEmpty()) {
                log.debug("[Cache] L1 hit: {}", shortCode);
                return longUrl;
            }
        } catch (Exception e) {
            log.warn("[Cache] L1 error", e);
        }

        // L2: Redis 缓存
        String redisKey = REDIS_KEY_PREFIX + shortCode;
        String longUrl = redisTemplate.opsForValue().get(redisKey);
        if (longUrl != null) {
            log.debug("[Cache] L2 hit: {}", shortCode);
            // 回源到 L1
            localCache.put(shortCode, longUrl);
            return longUrl;
        }

        // L3: 数据库查询
        ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
        if (shortUrl == null || shortUrl.getStatus() != 1) {
            log.warn("[ShortUrl] Not found or disabled: {}", shortCode);
            return null;
        }

        longUrl = shortUrl.getLongUrl();

        // 回源到 L2 和 L1
        redisTemplate.opsForValue().set(redisKey, longUrl, CACHE_TTL, TimeUnit.SECONDS);
        localCache.put(shortCode, longUrl);

        log.debug("[Cache] L3 hit and cached: {}", shortCode);
        return longUrl;
    }

    /**
     * 记录访问统计（异步）
     */
    @Async
    public void recordAccess(String shortCode, HttpServletRequest request) {
        try {
            ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
            if (shortUrl == null) return;

            // 记录访问日志
            ShortUrlAccessLog log = new ShortUrlAccessLog();
            log.setShortUrlId(shortUrl.getId());
            log.setUserIp(getClientIp(request));
            log.setUserAgent(request.getHeader("User-Agent"));
            log.setReferer(request.getHeader("Referer"));
            log.setDeviceType(detectDeviceType(request.getHeader("User-Agent")));
            log.setAccessedAt(new Date());

            shortUrlAccessLogMapper.insert(log);

            // 更新统计（PV）
            String statKey = "short_url:stat:" + shortUrl.getId() + ":" + LocalDate.now();
            redisTemplate.opsForValue().increment(statKey);
            redisTemplate.expire(statKey, 30, TimeUnit.DAYS);

        } catch (Exception e) {
            log.error("[ShortUrl] Failed to record access", e);
        }
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        return ip.split(",")[0].trim();
    }

    private String detectDeviceType(String userAgent) {
        if (userAgent == null) return "Unknown";
        if (userAgent.contains("Mobile")) return "Mobile";
        if (userAgent.contains("Tablet")) return "Tablet";
        return "PC";
    }
}
```

### Caffeine 本地缓存配置

```java
@Configuration
public class CacheConfig {

    /**
     * 本地缓存：热点短链
     * 容量 10000，访问后 10 分钟过期
     */
    @Bean
    public LoadingCache<String, String> shortUrlCache() {
        return Caffeine.newBuilder()
            .maximumSize(10_000)
            .expireAfterAccess(10, TimeUnit.MINUTES)
            .recordStats()
            .build(key -> {
                // 缓存 miss 时的加载逻辑
                ShortUrl shortUrl = shortUrlMapper.selectByCode(key);
                return shortUrl != null ? shortUrl.getLongUrl() : "";
            });
    }
}
```

---

## 六、布隆过滤器防穿透

### 问题：缓存穿透

```
场景：恶意用户请求不存在的短链
  GET /t/notexist1
  GET /t/notexist2
  GET /t/notexist3
  ...

结果：
  ❌ 缓存全部 miss
  ❌ 每次都查数据库
  ❌ 数据库被打穿
```

### 解决方案：布隆过滤器

```
布隆过滤器：
  - 快速判断元素是否存在
  - 假正例率低（可配置）
  - 内存占用小（百亿数据 ~ 1GB）

工作流程：
  1. 系统启动时，将所有短链加载到布隆过滤器
  2. 查询时，先用布隆过滤器判断
  3. 如果布隆过滤器说"不存在"，直接返回 404
  4. 如果布隆过滤器说"可能存在"，再查缓存/数据库
```

```java
@Component
@Slf4j
public class BloomFilterService {

    @Autowired private ShortUrlMapper shortUrlMapper;
    @Autowired private RedisTemplate<String, String> redisTemplate;

    private static final String BLOOM_FILTER_KEY = "bloom:short_url";
    private static final double FALSE_POSITIVE_RATE = 0.01; // 1% 假正例率

    /**
     * 初始化布隆过滤器（系统启动时调用）
     */
    @PostConstruct
    public void initBloomFilter() {
        log.info("[BloomFilter] Initializing...");

        // 1. 查询所有有效的短链
        List<String> allShortCodes = shortUrlMapper.selectAllValidCodes();
        log.info("[BloomFilter] Total short codes: {}", allShortCodes.size());

        // 2. 计算布隆过滤器大小
        long expectedInsertions = allShortCodes.size();
        long filterSize = optimalFilterSize(expectedInsertions, FALSE_POSITIVE_RATE);
        int hashFunctions = optimalHashFunctions(filterSize, expectedInsertions);

        log.info("[BloomFilter] Size: {} bits, Hash functions: {}", filterSize, hashFunctions);

        // 3. 使用 Redis 的 Bloom Filter 模块（需要 RedisBloom 插件）
        // 或者使用 Guava 的 BloomFilter 并序列化到 Redis
        for (String code : allShortCodes) {
            addToBloomFilter(code);
        }

        log.info("[BloomFilter] Initialized successfully");
    }

    /**
     * 添加短链到布隆过滤器
     */
    public void addToBloomFilter(String shortCode) {
        // 使用 Redis 的 BF.ADD 命令（需要 RedisBloom）
        // redisTemplate.execute((RedisCallback<Long>) connection ->
        //     connection.execute("BF.ADD", BLOOM_FILTER_KEY.getBytes(), shortCode.getBytes())
        // );

        // 或者使用 Guava BloomFilter（本地内存）
        // bloomFilter.put(shortCode);
    }

    /**
     * 检查短链是否可能存在
     */
    public boolean mightExist(String shortCode) {
        // 使用 Redis 的 BF.EXISTS 命令
        // Boolean result = (Boolean) redisTemplate.execute((RedisCallback<Boolean>) connection ->
        //     connection.execute("BF.EXISTS", BLOOM_FILTER_KEY.getBytes(), shortCode.getBytes())
        // );
        // return result != null && result;

        // 或者使用 Guava BloomFilter
        return bloomFilter.mightContain(shortCode);
    }

    /**
     * 计算最优的布隆过滤器大小
     * 公式：m = -n * ln(p) / (ln(2)^2)
     */
    private long optimalFilterSize(long n, double p) {
        return (long) (-n * Math.log(p) / (Math.log(2) * Math.log(2)));
    }

    /**
     * 计算最优的哈希函数个数
     * 公式：k = m / n * ln(2)
     */
    private int optimalHashFunctions(long m, long n) {
        return Math.max(1, (int) (m / n * Math.log(2)));
    }
}
```

### 集成到查询流程

```java
@Service
public class ShortUrlService {

    @Autowired private BloomFilterService bloomFilterService;
    @Autowired private ShortUrlRedirectService redirectService;

    /**
     * 获取长链（带布隆过滤器防穿透）
     */
    public String getLongUrl(String shortCode) {
        // 1. 布隆过滤器快速判断
        if (!bloomFilterService.mightExist(shortCode)) {
            log.warn("[ShortUrl] Not in bloom filter: {}", shortCode);
            return null; // 直接返回 404，不查数据库
        }

        // 2. 布隆过滤器说"可能存在"，继续查询
        return redirectService.getLongUrl(shortCode);
    }
}
```

---

## 七、高可用：缓存击穿/穿透/雪崩防护

### 缓存击穿（热点 Key 失效）

```
问题：热点短链（如明星微博链接）缓存失效
  → 瞬间大量请求打到数据库
  → 数据库 CPU 飙升

解决方案：
  1. 互斥锁（Mutex Lock）
  2. 热点 Key 永不过期
  3. 后台定时刷新
```

```java
@Service
public class HotKeyRefreshService {

    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private ShortUrlMapper shortUrlMapper;

    private static final String LOCK_KEY_PREFIX = "lock:short_url:";
    private static final long LOCK_TIMEOUT = 3; // 秒

    /**
     * 获取热点短链（带互斥锁）
     */
    public String getHotShortUrl(String shortCode) {
        String cacheKey = "short_url:" + shortCode;

        // 1. 尝试从缓存获取
        String longUrl = redisTemplate.opsForValue().get(cacheKey);
        if (longUrl != null) {
            return longUrl;
        }

        // 2. 缓存 miss，尝试获取互斥锁
        String lockKey = LOCK_KEY_PREFIX + shortCode;
        Boolean lockAcquired = redisTemplate.opsForValue().setIfAbsent(
            lockKey, "1", LOCK_TIMEOUT, TimeUnit.SECONDS
        );

        if (lockAcquired) {
            try {
                // 3. 获得锁，查询数据库
                ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
                if (shortUrl != null) {
                    longUrl = shortUrl.getLongUrl();
                    // 热点 Key 设置更长的 TTL（或永不过期）
                    redisTemplate.opsForValue().set(cacheKey, longUrl, 7, TimeUnit.DAYS);
                }
                return longUrl;
            } finally {
                // 4. 释放锁
                redisTemplate.delete(lockKey);
            }
        } else {
            // 5. 未获得锁，等待后重试
            try {
                Thread.sleep(50);
                return getHotShortUrl(shortCode); // 递归重试
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return null;
            }
        }
    }

    /**
     * 后台定时刷新热点 Key
     */
    @Scheduled(fixedRate = 60_000) // 每分钟刷新一次
    public void refreshHotKeys() {
        // 1. 查询访问量最高的 1000 个短链
        List<String> hotKeys = shortUrlMapper.selectTopHotCodes(1000);

        // 2. 逐个刷新缓存
        for (String shortCode : hotKeys) {
            String cacheKey = "short_url:" + shortCode;
            ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
            if (shortUrl != null) {
                redisTemplate.opsForValue().set(cacheKey, shortUrl.getLongUrl(), 7, TimeUnit.DAYS);
            }
        }

        log.info("[HotKeyRefresh] Refreshed {} hot keys", hotKeys.size());
    }
}
```

### 缓存雪崩（大量 Key 同时失效）

```
问题：大量短链缓存同时过期
  → 瞬间大量请求打到数据库
  → 数据库被压垮

解决方案：
  1. 随机化过期时间（避免同时过期）
  2. 使用本地缓存 + 分布式缓存
  3. 限流 + 熔断
```

```java
@Service
public class CacheAvalancheProtection {

    @Autowired private RedisTemplate<String, String> redisTemplate;

    /**
     * 设置缓存时，添加随机化 TTL
     */
    public void setCacheWithRandomTTL(String key, String value, long baseTTL) {
        // 在基础 TTL 上加 ±10% 的随机偏差
        long randomTTL = baseTTL + (long) ((Math.random() - 0.5) * baseTTL * 0.2);
        redisTemplate.opsForValue().set(key, value, randomTTL, TimeUnit.SECONDS);
    }

    /**
     * 限流保护：防止缓存失效时数据库被打穿
     */
    @Component
    public static class RateLimiter {

        @Autowired private RedisTemplate<String, String> redisTemplate;

        private static final String RATE_LIMIT_KEY = "rate_limit:short_url:";
        private static final int MAX_QPS = 10_000; // 最多 10000 QPS

        public boolean allowRequest(String shortCode) {
            String key = RATE_LIMIT_KEY + shortCode;
            Long count = redisTemplate.opsForValue().increment(key);

            if (count == 1) {
                // 首次请求，设置过期时间
                redisTemplate.expire(key, 1, TimeUnit.SECONDS);
            }

            return count <= MAX_QPS;
        }
    }
}
```

---

## 八、短链的安全性问题

### 问题一：恶意短链（钓鱼、恶意软件）

```
场景：
  短链指向钓鱼网站、恶意软件下载页面
  用户点击后被骗

防护方案：
  1. 内容审核（URL 黑名单）
  2. 用户举报机制
  3. 第三方安全检测（Google Safe Browsing）
```

```java
@Service
public class MaliciousUrlDetection {

    @Autowired private SafetyCheckService safetyCheckService;
    @Autowired private ShortUrlMapper shortUrlMapper;

    /**
     * 创建短链时检测恶意 URL
     */
    public boolean isSafeUrl(String longUrl) {
        // 1. 本地黑名单检查
        if (isInBlacklist(longUrl)) {
            return false;
        }

        // 2. 调用 Google Safe Browsing API
        SafetyCheckResult result = safetyCheckService.check(longUrl);
        if (result.isMalicious()) {
            log.warn("[Safety] Malicious URL detected: {}", longUrl);
            return false;
        }

        return true;
    }

    private boolean isInBlacklist(String url) {
        // 检查 URL 是否在黑名单中
        return false;
    }
}
```

### 问题二：短链被封禁（被平台限制）

```
场景：
  短链被微博/抖音等平台识别为垃圾/恶意
  导致短链无法分享

防护方案：
  1. 监控短链被封禁情况
  2. 自动生成新短链替换
  3. 提供短链替换 API
```

```java
@Service
public class ShortUrlBanProtection {

    @Autowired private ShortUrlMapper shortUrlMapper;
    @Autowired private SequenceBasedShortUrlService sequenceService;

    /**
     * 检测短链是否被封禁
     */
    public boolean isBanned(String shortCode) {
        ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
        return shortUrl != null && shortUrl.getStatus() == -1; // -1 表示被禁用
    }

    /**
     * 替换被封禁的短链
     */
    public String replaceWithNewShortUrl(String bannedShortCode) {
        ShortUrl oldShortUrl = shortUrlMapper.selectByCode(bannedShortCode);
        if (oldShortUrl == null) {
            return null;
        }

        // 生成新短链
        String newShortCode = sequenceService.generateShortUrl(oldShortUrl.getLongUrl());

        // 标记旧短链为已替换
        oldShortUrl.setStatus(-1);
        shortUrlMapper.update(oldShortUrl);

        return newShortCode;
    }
}
```

---

## 九、完整 Java 实现

### 短链服务核心类

```java
@RestController
@RequestMapping("/api/short-url")
@Slf4j
public class ShortUrlController {

    @Autowired private ShortUrlService shortUrlService;
    @Autowired private ShortUrlRedirectService redirectService;

    /**
     * 创建短链
     * POST /api/short-url/create
     * Body: { "longUrl": "https://example.com/article/123" }
     */
    @PostMapping("/create")
    public ResponseEntity<CreateShortUrlResponse> createShortUrl(
            @RequestBody CreateShortUrlRequest request) {

        String longUrl = request.getLongUrl();

        // 1. 验证 URL
        if (!isValidUrl(longUrl)) {
            return ResponseEntity.badRequest().build();
        }

        // 2. 检查是否已存在（幂等性）
        ShortUrl existing = shortUrlService.findByLongUrl(longUrl);
        if (existing != null) {
            return ResponseEntity.ok(new CreateShortUrlResponse(existing.getShortCode()));
        }

        // 3. 检查 URL 安全性
        if (!shortUrlService.isSafeUrl(longUrl)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }

        // 4. 生成短链
        String shortCode = shortUrlService.generateShortUrl(longUrl);

        return ResponseEntity.ok(new CreateShortUrlResponse(shortCode));
    }

    /**
     * 短链跳转
     * GET /t/{shortCode}
     */
    @GetMapping("/{shortCode}")
    public ResponseEntity<Void> redirect(
            @PathVariable String shortCode,
            HttpServletRequest request) {

        // 1. 获取长链
        String longUrl = shortUrlService.getLongUrl(shortCode);
        if (longUrl == null) {
            return ResponseEntity.notFound().build();
        }

        // 2. 异步记录访问统计
        redirectService.recordAccess(shortCode, request);

        // 3. 重定向
        return ResponseEntity.status(HttpStatus.MOVED_PERMANENTLY)
            .location(URI.create(longUrl))
            .build();
    }

    /**
     * 获取短链统计
     * GET /api/short-url/{shortCode}/stats
     */
    @GetMapping("/{shortCode}/stats")
    public ResponseEntity<ShortUrlStatsResponse> getStats(@PathVariable String shortCode) {
        ShortUrlStatsResponse stats = shortUrlService.getStats(shortCode);
        return ResponseEntity.ok(stats);
    }

    private boolean isValidUrl(String url) {
        try {
            new URL(url);
            return true;
        } catch (MalformedURLException e) {
            return false;
        }
    }
}

@Service
@Slf4j
public class ShortUrlService {

    @Autowired private ShortUrlMapper shortUrlMapper;
    @Autowired private SequenceBasedShortUrlService sequenceService;
    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private MaliciousUrlDetection maliciousUrlDetection;
    @Autowired private BloomFilterService bloomFilterService;

    /**
     * 生成短链（核心方法）
     */
    public String generateShortUrl(String longUrl) {
        // 1. 检查是否已存在
        ShortUrl existing = shortUrlMapper.selectByLongUrl(longUrl);
        if (existing != null) {
            return existing.getShortCode();
        }

        // 2. 从发号器获取 ID
        long id = sequenceService.nextId();

        // 3. Base62 编码
        String shortCode = sequenceService.toBase62(id);

        // 4. 保存到数据库
        ShortUrl shortUrl = new ShortUrl();
        shortUrl.setId(id);
        shortUrl.setShortCode(shortCode);
        shortUrl.setLongUrl(longUrl);
        shortUrl.setCreatedAt(new Date());
        shortUrl.setStatus(1);
        shortUrlMapper.insert(shortUrl);

        // 5. 加入布隆过滤器
        bloomFilterService.addToBloomFilter(shortCode);

        // 6. 预热缓存
        String cacheKey = "short_url:" + shortCode;
        redisTemplate.opsForValue().set(cacheKey, longUrl, 24, TimeUnit.HOURS);

        log.info("[ShortUrl] Generated: {} -> {}", shortCode, longUrl);
        return shortCode;
    }

    /**
     * 获取长链（三级缓存）
     */
    public String getLongUrl(String shortCode) {
        // 布隆过滤器快速判断
        if (!bloomFilterService.mightExist(shortCode)) {
            return null;
        }

        // 三级缓存查询
        String cacheKey = "short_url:" + shortCode;

        // L1: Redis
        String longUrl = redisTemplate.opsForValue().get(cacheKey);
        if (longUrl != null) {
            return longUrl;
        }

        // L2: 数据库
        ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
        if (shortUrl == null || shortUrl.getStatus() != 1) {
            return null;
        }

        longUrl = shortUrl.getLongUrl();

        // 回源到缓存
        redisTemplate.opsForValue().set(cacheKey, longUrl, 24, TimeUnit.HOURS);

        return longUrl;
    }

    /**
     * 获取统计信息
     */
    public ShortUrlStatsResponse getStats(String shortCode) {
        ShortUrl shortUrl = shortUrlMapper.selectByCode(shortCode);
        if (shortUrl == null) {
            return null;
        }

        // 查询统计数据
        List<ShortUrlStat> stats = shortUrlMapper.selectStatsByShortUrlId(shortUrl.getId());

        long totalPv = stats.stream().mapToLong(ShortUrlStat::getPv).sum();
        long totalUv = stats.stream().mapToLong(ShortUrlStat::getUv).sum();

        return new ShortUrlStatsResponse(
            shortCode,
            shortUrl.getLongUrl(),
            totalPv,
            totalUv,
            shortUrl.getCreatedAt()
        );
    }

    public boolean isSafeUrl(String longUrl) {
        return maliciousUrlDetection.isSafeUrl(longUrl);
    }

    public ShortUrl findByLongUrl(String longUrl) {
        return shortUrlMapper.selectByLongUrl(longUrl);
    }
}
```

---

## 十、高频面试题

### Q1: 短链系统如何支撑百亿级数据？

> **分布式存储 + 分层缓存**
>
> 1. **数据库分片**：按 short_code 的首字符分片（62 个分片），每个分片 ~1.6 亿条记录
> 2. **缓存分层**：
>    - L1 本地缓存（Caffeine）：热点 1 万条
>    - L2 分布式缓存（Redis）：热点 1000 万条
>    - L3 数据库：全量数据
> 3. **访问统计分离**：统计数据单独存储，不影响主表查询
> 4. **冷热分离**：历史短链归档到 HBase/Hive，只保留最近 1 年数据在 MySQL

### Q2: 短链生成时如何保证幂等性？

> **方案一：哈希方案**
> - 相同长链生成相同短链，天然幂等
> - 缺点：冲突率高
>
> **方案二：发号器 + 去重**
> - 创建前检查长链是否已存在
> - 存在则返回已有短链，不重新生成
> - 使用 Redis Set 缓存已生成的长链，加速查询

### Q3: 短链跳转如何做到 100ms 内响应？

> 1. **多级缓存**：L1 本地缓存 < 1ms，L2 Redis < 5ms，L3 数据库 < 50ms
> 2. **CDN 加速**：短链跳转 API 部署在 CDN 边缘节点
> 3. **异步统计**：访问统计异步处理，不阻塞跳转响应
> 4. **连接池优化**：数据库连接池、Redis 连接池预热
> 5. **HTTP 优化**：使用 HTTP 301 永久重定向，浏览器缓存

### Q4: 如何防止短链被恶意刷量？

> 1. **限流**：按 IP/用户 ID 限流，防止单点刷量
> 2. **验证码**：可疑访问触发验证码
> 3. **黑名单**：恶意 IP 加入黑名单
> 4. **异常检测**：访问模式异常（如瞬间 10 倍增长）触发告警
> 5. **短链过期**：设置短链有效期，过期自动失效

### Q5: 短链系统如何实现高可用？

> 1. **主从复制**：MySQL 主从，Redis 主从
> 2. **多机房部署**：跨机房冗余，故障自动切换
> 3. **缓存多副本**：Redis Cluster，数据多副本
> 4. **熔断降级**：数据库故障时，直接返回缓存数据
> 5. **监控告警**：实时监控 QPS、延迟、错误率，异常自动告警

### Q6: 如何处理短链被平台封禁的问题？

> 1. **监控被封禁短链**：定期检测短链是否被微博/抖音等平台限制
> 2. **自动替换**：被封禁时自动生成新短链，旧短链重定向到新短链
> 3. **用户通知**：通知用户短链已更新，提供新短链
> 4. **内容审核**：创建短链时进行内容审核，防止生成违规短链
> 5. **黑名单维护**：维护被封禁的长链黑名单，防止重复生成

---

## 十一、系统架构总结

```
┌─────────────────────────────────────────────────────────────────┐
│                      短链系统完整架构                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  创建短链     │  │  短链跳转     │  │  统计查询     │          │
│  │  POST /create │  │  GET /t/{code}│  │  GET /stats  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              短链服务（ShortUrlService）              │       │
│  │  - 生成短链（发号器 + Base62）                        │       │
│  │  - 获取长链（三级缓存）                              │       │
│  │  - 安全检测（恶意 URL 检测）                         │       │
│  │  - 统计查询                                          │       │
│  └──────┬───────────────────────────────────────────────┘       │
│         │                                                        │
│    ┌────┴────────────────────────────────────────┐              │
│    │                                              │              │
│    ▼                                              ▼              │
│ ┌──────────────┐                          ┌──────────────┐     │
│ │  L1 缓存      │                          │  布隆过滤器   │     │
│ │ (Caffeine)   │                          │ (防穿透)     │     │
│ │ 热点 1 万条   │                          │              │     │
│ └──────┬───────┘                          └──────────────┘     │
│        │                                                        │
│        ▼                                                        │
│ ┌──────────────┐                                               │
│ │  L2 缓存      │                                               │
│ │  (Redis)     │                                               │
│ │ 热点 1000 万条│                                               │
│ └──────┬───────┘                                               │
│        │                                                        │
│        ▼                                                        │
│ ┌──────────────────────────────────────┐                       │
│ │  L3 数据库（MySQL）                   │                       │
│ │  - short_url 表（主表）              │                       │
│ │  - short_url_stat 表（统计）         │                       │
│ │  - short_url_access_log 表（明细）   │                       │
│ └──────────────────────────────────────┘                       │
│                                                                 │
│  异步处理：                                                      │
│  - 访问统计（MQ）                                               │
│  - 热点 Key 刷新（定时任务）                                    │
│  - 数据库同步（定时任务）                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

**参考链接：**
- [短链系统设计实践](https://tech.meituan.com/2015/02/10/short-url.html)
- [Snowflake 分布式 ID 生成](https://github.com/twitter-archive/snowflake)
- [Redis 缓存设计模式](https://redis.io/docs/manual/client-side-caching/)
