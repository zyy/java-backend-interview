---
layout: default
title: 如何实现 IP 归属地查询？⭐⭐⭐
---
# 如何实现 IP 归属地查询？

## 🎯 面试题：如何根据 IP 地址查询归属地？

---

## 一、IP 地址基础

```
IPv4：4 字节，范围 0 ~ 4,294,967,295
  例：192.168.1.100 → 数值化后 = 3232235876

IPv6：16 字节，范围 0 ~ 2^128-1
  例：2001:0db8:85a3:0000:0000:8a2e:0370:7334

查询任务：
  输入一个 IP 地址（字符串）
  输出归属地信息：国家 / 省份 / 城市 / 运营商
```

---

## 二、IP 库的数据结构

### IP 库文件格式

```
每条记录：
[start_ip, end_ip, country, province, city, isp]

示例：
3232235776, 3232236031, 中国, 广东省, 深圳市, 电信
3232236032, 3232236287, 中国, 广东省, 深圳市, 联通
```

### 数值化方法

```java
/**
 * IP 字符串 → 数值
 * 192.168.1.100
 * = 192×256³ + 168×256² + 1×256¹ + 100
 * = 3232235876
 */
public static long ipToLong(String ip) {
    if (ip == null || ip.isEmpty()) return 0;

    // IPv6 暂不处理（复杂度差异很大）
    if (ip.contains(":")) return 0; // IPv6 placeholder

    String[] parts = ip.split("\\.");
    if (parts.length != 4) return 0;

    return (Long.parseLong(parts[0]) << 24)
         | (Long.parseLong(parts[1]) << 16)
         | (Long.parseLong(parts[2]) << 8)
         | Long.parseLong(parts[3]);
}

/**
 * 数值 → IP 字符串
 */
public static String longToIp(long ipNum) {
    return ((ipNum >> 24) & 0xFF) + "." +
           ((ipNum >> 16) & 0xFF) + "." +
           ((ipNum >> 8)  & 0xFF) + "." +
           (ipNum & 0xFF);
}
```

---

## 三、二分查找定位归属地

### 核心思想

```
IP 库按 start_ip 升序排列

查找：给定 IP = 3232235900
  ↓
二分查找到第一个 end_ip >= 3232235900 的区间
  ↓
该区间即为 IP 所在范围

为什么二分而不是 HashMap？
  IP 库有 40 万条记录
  IP 值跨度很大（从几百万到几十亿）
  HashMap 存储开销极大（key 是 8 字节数值）
  二分查找 O(log N) = O(log 40万) ≈ 19 次
```

```java
@Service
@Slf4j
public class IpGeoService {

    // IP 段数组，按 startIp 升序排列
    private IpSegment[] ipSegments;
    // 按 startIp 构建的索引
    private long[] startIpIndex;

    @PostConstruct
    public void loadDatabase() {
        long start = System.currentTimeMillis();
        List<IpSegment> segments = loadFromFile("/data/ipdb/ipv4_segment.dat");
        this.ipSegments = segments.toArray(new IpSegment[0]);

        // 构建索引数组，加速二分
        this.startIpIndex = new long[ipSegments.length];
        for (int i = 0; i < ipSegments.length; i++) {
            startIpIndex[i] = ipSegments[i].startIp;
        }

        log.info("IP 库加载完成：{} 条记录，耗时 {}ms",
            ipSegments.length, System.currentTimeMillis() - start);
    }

    /**
     * 二分查找 IP 归属地
     * 找到第一个 endIp >= targetIp 的区间
     */
    public IpGeo query(String ip) {
        long ipNum = ipToLong(ip);
        if (ipNum <= 0) return IpGeo.UNKNOWN;

        int idx = binarySearch(ipNum);
        if (idx == -1) return IpGeo.UNKNOWN;

        IpSegment seg = ipSegments[idx];
        if (ipNum >= seg.startIp && ipNum <= seg.endIp) {
            return new IpGeo(seg.country, seg.province, seg.city, seg.isp);
        }
        return IpGeo.UNKNOWN;
    }

    /**
     * 二分查找：找第一个 endIp >= targetIp 的位置
     */
    private int binarySearch(long targetIp) {
        int lo = 0, hi = ipSegments.length - 1;
        int result = -1;

        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            if (ipSegments[mid].endIp >= targetIp) {
                result = mid;    // 可能是答案
                hi = mid - 1;   // 继续向左找更小的
            } else {
                lo = mid + 1;
            }
        }
        return result;
    }

    /**
     * 预加载优化版：基于 startIp 做标准二分
     * 找第一个 startIp > targetIp 的位置，取前一个
     */
    private int binarySearchByStart(long targetIp) {
        int lo = 0, hi = ipSegments.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            if (startIpIndex[mid] <= targetIp) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        // lo 指向第一个 > targetIp 的位置
        // targetIp 落在 lo-1 的区间内
        int idx = lo - 1;
        if (idx >= 0 && targetIp <= ipSegments[idx].endIp) {
            return idx;
        }
        return -1;
    }

    /**
     * 加载 IP 库文件（纯真/裸 IP 库格式）
     */
    private List<IpSegment> loadFromFile(String path) {
        List<IpSegment> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(path), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length < 5) continue;
                list.add(new IpSegment(
                    Long.parseLong(parts[0].trim()),
                    Long.parseLong(parts[1].trim()),
                    parts[2].trim(), parts[3].trim(),
                    parts[4].trim(),
                    parts.length > 5 ? parts[5].trim() : ""
                ));
            }
        } catch (IOException e) {
            log.error("加载 IP 库失败: {}", path, e);
        }
        return list;
    }

    @Data
    @AllArgsConstructor
    static class IpSegment {
        long startIp;
        long endIp;
        String country;
        String province;
        String city;
        String isp;
    }

    @Data
    @AllArgsConstructor
    static class IpGeo {
        String country, province, city, isp;
        static IpGeo UNKNOWN = new IpGeo("未知", "未知", "未知", "");
    }
}
```

---

## 四、缓存优化

### 多级缓存

```
查询频率分布（典型）：
  80% 请求命中：TOP 20% 的 IP（热 IP）
  20% 请求命中：冷门 IP

L1: 本地 ConcurrentHashMap（TTL 5 分钟，10000 条）
L2: Redis（TTL 1 小时，按 IP 哈希分 key）
L3: 二分查找 IP 库文件
```

```java
@Service
@Slf4j
public class IpGeoCachedService {

    @Autowired
    private IpGeoService ipGeoService;
    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // L1 本地缓存：Guava Cache 或 ConcurrentHashMap + TTL
    private final LoadingCache<String, IpGeo> localCache = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(5, TimeUnit.MINUTES)
        .build(key -> ipGeoService.query(key)); // CacheLoader：miss 时自动查 L2/L3

    // L2 Redis 缓存的 key 前缀
    private static final String CACHE_KEY_PREFIX = "ip:geo:";

    public IpGeo query(String ip) {
        // 1. L1 本地缓存
        IpGeo cached = localCache.getIfPresent(ip);
        if (cached != null) return cached;

        // 2. L2 Redis 缓存
        String redisKey = CACHE_KEY_PREFIX + ip;
        Map<Object, Object> redisCached = redisTemplate.opsForHash().entries(redisKey);
        if (!redisCached.isEmpty()) {
            IpGeo geo = new IpGeo(
                (String) redisCached.get("country"),
                (String) redisCached.get("province"),
                (String) redisCached.get("city"),
                (String) redisCached.get("isp")
            );
            localCache.put(ip, geo);
            return geo;
        }

        // 3. L3 查 IP 库
        IpGeo geo = ipGeoService.query(ip);

        // 4. 回填 L2
        if (!geo.equals(IpGeo.UNKNOWN)) {
            Map<String, String> fields = Map.of(
                "country", geo.getCountry() != null ? geo.getCountry() : "",
                "province", geo.getProvince() != null ? geo.getProvince() : "",
                "city", geo.getCity() != null ? geo.getCity() : "",
                "isp", geo.getIsp() != null ? geo.getIsp() : ""
            );
            redisTemplate.opsForHash().putAll(redisKey, fields);
            redisTemplate.expire(redisKey, 1, TimeUnit.HOURS);
        }

        localCache.put(ip, geo);
        return geo;
    }
}
```

---

## 五、批量查询优化

```java
/**
 * 批量查询：单 IP → 批量 IN 查询
 * 场景：日志分析，一次处理 1000 个 IP
 */
public Map<String, IpGeo> batchQuery(List<String> ips) {
    Map<String, IpGeo> result = new HashMap<>();
    List<String> missIps = new ArrayList<>();

    for (String ip : ips) {
        IpGeo geo = query(ip); // 走缓存，毫秒级
        result.put(ip, geo);
        if (geo == IpGeo.UNKNOWN) missIps.add(ip);
    }

    log.debug("批量查询: total={}, hit={}, miss={}",
        ips.size(), ips.size() - missIps.size(), missIps.size());
    return result;
}
```

---

## 六、常见 IP 库对比

| IP 库 | 大小 | 精度 | 查询速度 | 特点 |
|-------|------|------|---------|------|
| **ip2region** | ~10MB | 城市级 | ~0.1ms | 国产开源，Java 支持好 |
| **纯真 IP 库** | ~5MB | 城市级 | ~0.5ms | 最流行，免费，中文 |
| **MaxMind GeoIP2** | ~50MB | 精确街道 | ~1ms | 国际权威，精度最高 |
| **qqwry.dat** | ~5MB | 城市级 | ~0.5ms | 国内最常用的免费库 |

**ip2region 使用示例：**

```java
@Service
public class IpGeoServiceImpl {

    private Searcher searcher;

    @PostConstruct
    public void init() throws Exception {
        // 启动时加载 ip2region 数据库文件
        this.searcher = Searcher.newWithFileOnly(
            "/data/ip2region/ip2region.xdb"
        );
    }

    public IpGeo query(String ip) {
        try {
            long ipNum = ipToLong(ip);
            // queryBtree: 二分搜索，最常用
            // queryAll: 全量搜索，支持 IPv6
            String region = searcher.search(ipNum);
            // region 格式：国家|省份|城市|运营商|ISP
            String[] parts = region.split("\\|");
            return new IpGeo(
                parts[0], parts[1], parts[2],
                parts.length > 4 ? parts[4] : ""
            );
        } catch (Exception e) {
            log.warn("IP 查询失败: ip={}, {}", ip, e.getMessage());
            return IpGeo.UNKNOWN;
        }
    }
}
```

---

## 七、高频面试题

**Q1: 为什么不用 HashMap 存储 IP 库？**
> IP 库有 40 万条记录，key 是 8 字节长整型，HashMap 存储开销很大（负载因子 0.75 时约 1.6 倍）。更重要的是，IP 是有序数值区间，天然适合二分查找，O(log N) = 19 次查找即可定位，远低于 HashMap 的空间成本。

**Q2: IP 库如何实现增量更新？**
> 方案一：定时拉取新版 IP 库文件，全量替换；方案二：打增量包（只下发变化区间），在内存中合并覆盖；方案三：按时间戳版本号，增量拉取后追加到现有数据尾部。生产推荐方案一，最简单可靠。

**Q3: IPv4 和 IPv6 查询有什么区别？**
> IPv4 是 4 字节，数值范围小，可全量加载到内存用二分查找。IPv6 是 16 字节，范围极大，无法枚举，需要用 Radix Tree（前缀树）做最长前缀匹配，查询复杂度更高。

**Q4: 如何保证查询的稳定性？**
> ① IP 库文件加载到内存，查询不依赖外部服务；② 缓存穿透：未查到返回默认值，不抛异常；③ 多级缓存兜底：本地缓存 → Redis → 二分查找；④ 异常时降级到离线库或返回"未知"。

---

**参考链接：**
- [ip2region 开源项目](https://github.com/lionsoul2012/ip2region)
- [纯真 IP 库](https://www.cz88.net/)
- [GeoIP2 数据库](https://www.maxmind.com/en/geoip2/services)
