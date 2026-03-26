---
layout: default
title: 如何设计一个排行榜系统？⭐⭐⭐
---
# 如何设计一个排行榜系统？

## 🎯 面试题：如何设计一个实时排行榜？

> 排行榜是社交和游戏场景中的核心功能：游戏战力榜、积分榜、带货达人榜……需要支撑实时更新、高并发查询，同时保证数据准确性。

---

## 一、排行榜的核心挑战

```
❌ 数据量巨大：千万级玩家，战力排序
❌ 写入频繁：每次战斗/消费都更新分数
❌ 查询并发高：首页展示 TOP 100 万人同时访问
❌ 需要实时：不能有明显的延迟
❌ 周边需求：查自己的排名、查前一名后一名

MySQL ORDER BY score DESC → 百万数据全表扫描 ❌
```

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    排行榜系统架构                         │
│                                                         │
│  用户行为  ──▶  行为事件 Kafka ──▶  分数计算服务 ──▶ Redis │
│                                                         │
│  查询请求  ──▶  排行榜服务  ──▶  Redis ZSet  ──▶  返回   │
│                              │                           │
│                         异步同步  ──▶  MySQL 归档          │
└─────────────────────────────────────────────────────────┘
```

**核心数据结构：Redis Sorted Set（ZSet）**

```
ZSet = 唯一成员 + 分值（score）
ZRANGE key 0 99 WITHSCORES  →  获取 TOP 100
ZRANK key member            →  获取成员排名（0-based）
ZSCORE key member           →  获取成员分数
ZREVRANK key member         →  获取倒序排名（0-based）
```

---

## 三、Redis ZSet 实现排行榜

### 1. 基本操作

```java
@Service
@Slf4j
public class RankingService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final String RANKING_KEY = "ranking:game:power";

    /**
     * 更新用户分数（自动更新排名）
     * ZADD：member 已存在则更新 score，不存在则新增
     */
    public void updateScore(Long userId, double score) {
        redisTemplate.opsForZSet().add(RANKING_KEY, String.valueOf(userId), score);
        log.debug("[Ranking] Updated score: userId={}, score={}", userId, score);
    }

    /**
     * 批量更新分数（活动结算、批量导入等场景）
     */
    public void batchUpdateScore(Map<Long, Double> userScores) {
        Set<ZSetOperations.TypedTuple<String>> tuples = userScores.entrySet().stream()
            .map(e -> ZSetOperations.TypedTuple.of(
                String.valueOf(e.getKey()),
                e.getValue()
            ))
            .collect(Collectors.toSet());
        redisTemplate.opsForZSet().add(RANKING_KEY, tuples);
    }

    /**
     * 获取 TOP N 排行榜
     */
    public List<RankingEntry> getTopN(int n) {
        Set<ZSetOperations.TypedTuple<String>> topSet = redisTemplate.opsForZSet()
            .reverseRangeWithScores(RANKING_KEY, 0, n - 1);

        if (topSet == null) return Collections.emptyList();

        List<RankingEntry> result = new ArrayList<>();
        int rank = 1;
        for (ZSetOperations.TypedTuple<String> tuple : topSet) {
            result.add(new RankingEntry(
                rank++,
                Long.parseLong(tuple.getValue()),
                tuple.getScore()
            ));
        }
        return result;
    }

    /**
     * 获取用户排名（从 1 开始）
     */
    public Long getUserRank(Long userId) {
        Long rank = redisTemplate.opsForZSet().reverseRank(RANKING_KEY, String.valueOf(userId));
        return rank != null ? rank + 1 : null;
    }

    /**
     * 获取用户周围的排名（前三名后三名）
     */
    public List<RankingEntry> getNeighborRanks(Long userId) {
        Long rank = redisTemplate.opsForZSet().reverseRank(RANKING_KEY, String.valueOf(userId));
        if (rank == null) return Collections.emptyList();

        long start = Math.max(0, rank - 3);
        long stop = rank + 3;

        Set<ZSetOperations.TypedTuple<String>> neighborSet = redisTemplate.opsForZSet()
            .reverseRangeWithScores(RANKING_KEY, start, stop);

        List<RankingEntry> result = new ArrayList<>();
        int displayRank = (int) start + 1;
        for (ZSetOperations.TypedTuple<String> tuple : neighborSet) {
            result.add(new RankingEntry(
                displayRank++,
                Long.parseLong(tuple.getValue()),
                tuple.getScore()
            ));
        }
        return result;
    }

    /**
     * 获取指定区间排名（如第 1001-1100 名）
     */
    public List<RankingEntry> getRange(int start, int end) {
        Set<ZSetOperations.TypedTuple<String>> rangeSet = redisTemplate.opsForZSet()
            .reverseRangeWithScores(RANKING_KEY, start, end);

        List<RankingEntry> result = new ArrayList<>();
        int rank = start + 1;
        for (ZSetOperations.TypedTuple<String> tuple : rangeSet) {
            result.add(new RankingEntry(
                rank++,
                Long.parseLong(tuple.getValue()),
                tuple.getScore()
            ));
        }
        return result;
    }

    /**
     * 移除用户（封禁、清榜等场景）
     */
    public void removeUser(Long userId) {
        redisTemplate.opsForZSet().remove(RANKING_KEY, String.valueOf(userId));
    }

    /**
     * 获取排行榜总人数
     */
    public Long getTotalCount() {
        return redisTemplate.opsForZSet().zCard(RANKING_KEY);
    }

    @Data
    @AllArgsConstructor
    public static class RankingEntry {
        private long rank;
        private long userId;
        private double score;
    }
}
```

### 2. 增量更新（防频繁写入）

```
问题：每次战斗都更新 Redis，高并发时 Redis 压力大

解决：本地缓存聚合 + 定时批量同步

用户战斗 → 本地缓存（内存 Map）→ 定时批量写入 Redis
```

```java
@Component
@Slf4j
public class ScoreAggregator {

    // 本地聚合缓存（用户 ID → 累计增量）
    private final Map<Long, Double> localCache = new ConcurrentHashMap<>();

    // 每 5 秒批量同步到 Redis
    private static final long SYNC_INTERVAL = 5_000L;

    @PostConstruct
    public void init() {
        Executors.newSingleThreadScheduledExecutor().scheduleAtFixedRate(
            this::flushToRedis, SYNC_INTERVAL, SYNC_INTERVAL, TimeUnit.MILLISECONDS
        );
    }

    /**
     * 增量更新分数（写本地缓存，不直接写 Redis）
     */
    public void addScore(Long userId, double delta) {
        localCache.merge(userId, delta, Double::sum);
    }

    /**
     * 定时将本地缓存批量同步到 Redis
     */
    private void flushToRedis() {
        if (localCache.isEmpty()) return;

        Map<Long, Double> toFlush = new HashMap<>(localCache);
        localCache.clear();

        for (Map.Entry<Long, Double> entry : toFlush.entrySet()) {
            Long userId = entry.getKey();
            Double delta = entry.getValue();

            String member = String.valueOf(userId);
            // 先获取当前分数
            Double currentScore = redisTemplate.opsForZSet()
                .score("ranking:game:power", member);

            double newScore = (currentScore != null ? currentScore : 0) + delta;
            redisTemplate.opsForZSet().add("ranking:game:power", member, newScore);
        }

        log.info("[ScoreAggregator] Flushed {} users to Redis", toFlush.size());
    }
}
```

---

## 四、分层排行榜设计

```
问题：TOP 1000 热门，其他名次查询少但数据量大

解决：分层存储 + 分级查询

Redis 热层：只存 TOP 10000（实时同步，高频访问）
MySQL 冷层：全量数据（低频访问，按需归档）
```

```
写入流程：
用户分数变化
    ↓
先更新 Redis ZSet（热层）
    ↓
异步写入 MySQL（冷层）→ 按需归档

查询流程：
    ├── 查 TOP 100 → Redis 热层（毫秒级）
    ├── 查自己排名 → Redis 热层 + 自己分数区间判断
    └── 查万名后 → MySQL 索引查询
```

```java
@Service
public class TieredRankingService {

    private static final int HOT_THRESHOLD = 10_000; // 热层只保留 TOP 10000

    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private RankingMapper rankingMapper;

    /**
     * 分层查询：热层优先，冷层兜底
     */
    public RankingEntry queryRank(Long userId) {
        // 1. 先查 Redis 热层
        Long rank = redisTemplate.opsForZSet().reverseRank("ranking:hot", String.valueOf(userId));
        Double score = redisTemplate.opsForZSet().score("ranking:hot", String.valueOf(userId));

        if (rank != null) {
            return new RankingEntry(rank + 1, userId, score);
        }

        // 2. 热层没有，查 MySQL 冷层
        RankingDO ranking = rankingMapper.selectByUserId(userId);
        if (ranking != null) {
            return new RankingEntry(ranking.getRank(), userId, ranking.getScore());
        }

        return null;
    }

    /**
     * 热层数据更新时，同步到 MySQL
     */
    @Scheduled(fixedRate = 60_000) // 每分钟同步一次
    public void syncHotRankingToDB() {
        // 取出热层 TOP 10000 全量同步到 MySQL
        // 实际生产中增量同步更优，这里简化示例
        Set<ZSetOperations.TypedTuple<String>> hotSet = redisTemplate.opsForZSet()
            .reverseRangeWithScores("ranking:hot", 0, HOT_THRESHOLD - 1);

        if (hotSet == null) return;

        rankingMapper.batchUpsert(
            hotSet.stream().map(tuple -> {
                RankingDO r = new RankingDO();
                r.setUserId(Long.parseLong(tuple.getValue()));
                r.setScore(tuple.getScore());
                return r;
            }).toList()
        );
    }
}
```

---

## 五、游戏战力排行榜实战

### 场景：MOBA 类游戏战力排行榜

```
战力分数组成：
- 段位分：青铜/白银/黄金/钻石/王者
- 胜率分：最近 100 场胜率加成
- 战力分：KDA 累计分

更新时机：
- 每场对局结束后（通过 MQ 异步触发）
- 每天凌晨定时刷新（胜率分每日重算）
```

```java
@Service
@Slf4j
public class GamePowerRankingService {

    private static final String POWER_RANKING = "ranking:game:power";
    private static final String TIER_RANKING  = "ranking:game:tier";
    private static final String WEEK_RANKING   = "ranking:game:weekly";

    /**
     * 对局结束后计算战力分并更新排行榜
     */
    public void onGameFinished(GameResultEvent event) {
        long userId = event.getUserId();
        GameStats stats = event.getStats();

        // 计算综合战力分
        double powerScore = calculatePowerScore(stats);

        // 1. 更新总战力榜
        redisTemplate.opsForZSet().add(POWER_RANKING, String.valueOf(userId), powerScore);

        // 2. 更新段位榜（同段位内排名）
        String tierKey = TIER_RANKING + ":" + stats.getTier();
        redisTemplate.opsForZSet().add(tierKey, String.valueOf(userId), powerScore);

        // 3. 更新周榜（每周重置）
        redisTemplate.opsForZSet().add(WEEK_RANKING, String.valueOf(userId), powerScore);

        // 4. 异步记录战绩（持久化）
        mqTemplate.convertAndSend("game-result-topic", event);

        log.info("[Ranking] Updated power: userId={}, power={}, tier={}",
            userId, powerScore, stats.getTier());
    }

    /**
     * 综合战力分计算公式
     */
    private double calculatePowerScore(GameStats stats) {
        // 段位基础分（段位越高基础分越高）
        double tierScore = stats.getTier() * 5000.0;

        // 胜率分：胜率 * 2000（满胜率 = +2000 分）
        double winRateScore = stats.getWinRate() * 2000;

        // KDA 分：最近 20 场平均 KDA * 100
        double kdaScore = stats.getRecentKdaAverage() * 100;

        // 场次加成：打的越多，加成越高（封顶 500 分）
        double gamesScore = Math.min(stats.getTotalGames() * 5, 500);

        return tierScore + winRateScore + kdaScore + gamesScore;
    }

    /**
     * 获取游戏战力榜详情（含段位信息）
     */
    public List<PowerRankingVO> getTopPowerRanking(int n) {
        Set<ZSetOperations.TypedTuple<String>> topSet = redisTemplate.opsForZSet()
            .reverseRangeWithScores(POWER_RANKING, 0, n - 1);

        List<Long> userIds = topSet.stream()
            .map(t -> Long.parseLong(t.getValue()))
            .collect(Collectors.toList());

        // 批量查询用户段位信息（批量 IN 查询）
        Map<Long, UserInfo> userInfoMap = userMapper.batchSelectUserInfo(userIds);

        List<PowerRankingVO> result = new ArrayList<>();
        int rank = 1;
        for (ZSetOperations.TypedTuple<String> tuple : topSet) {
            long uid = Long.parseLong(tuple.getValue());
            UserInfo info = userInfoMap.getOrDefault(uid, UserInfo.EMPTY);
            result.add(new PowerRankingVO(
                rank++,
                uid,
                info.getNickname(),
                info.getAvatar(),
                info.getTier(),
                tuple.getScore()
            ));
        }
        return result;
    }

    /**
     * 获取自己在战力榜中的位置
     */
    public MyRankVO getMyRank(Long userId) {
        Long rank = redisTemplate.opsForZSet().reverseRank(POWER_RANKING, String.valueOf(userId));
        Double score = redisTemplate.opsForZSet().score(POWER_RANKING, String.valueOf(userId));
        Long total = redisTemplate.opsForZSet().zCard(POWER_RANKING);

        if (rank == null) {
            return new MyRankVO(null, null, total, "未上榜");
        }

        return new MyRankVO(
            rank + 1,
            score,
            total,
            getTierName((int) (score / 5000)) // 根据分值反推段位
        );
    }

    private String getTierName(int tier) {
        return switch (tier) {
            case 0 -> "青铜";
            case 1 -> "白银";
            case 2 -> "黄金";
            case 3 -> "铂金";
            case 4 -> "钻石";
            case 5 -> "星耀";
            case 6 -> "王者";
            default -> tier >= 7 ? "荣耀王者" : "青铜";
        };
    }
}
```

---

## 六、周榜/月榜实现（滑动窗口）

```
需求：每周重置一次排行榜，但保留历史记录

实现：按时间桶分 key

本周 key：  ranking:game:weekly:2026_13  （第 13 周）
上周 key：  ranking:game:weekly:2026_12

每周一凌晨 00:00：
  1. 将上周排行榜归档到 MySQL
  2. 旧 key 删除或归档
  3. 新 key 开始计数
```

```java
@Component
public class WeeklyRankingKeyManager {

    /**
     * 获取当前周期的排行榜 Key
     * 格式：ranking:{type}:weekly:{year}_{week}
     */
    public String getCurrentWeeklyKey(String type) {
        LocalDate now = LocalDate.now();
        int year = now.getYear();
        int week = now.get(WeekFields.ISO.weekOfWeekBasedYear());

        return String.format("ranking:%s:weekly:%d_%02d", type, year, week);
    }

    /**
     * 获取指定周期的排行榜 Key
     */
    public String getWeeklyKey(String type, int year, int week) {
        return String.format("ranking:%s:weekly:%d_%02d", type, year, week);
    }

    /**
     * 每周一归档上周排行榜
     */
    @Scheduled(cron = "0 0 0 ? * MON")  // 每周一凌晨
    public void archiveLastWeekRanking() {
        LocalDate lastWeek = LocalDate.now().minusWeeks(1);
        int year = lastWeek.getYear();
        int week = lastWeek.get(WeekFields.ISO.weekOfWeekBasedYear());

        String lastWeekKey = getWeeklyKey("game", year, week);

        // 1. 取出上周排行榜 TOP 1000
        Set<ZSetOperations.TypedTuple<String>> top1000 = redisTemplate.opsForZSet()
            .reverseRangeWithScores(lastWeekKey, 0, 999);

        if (top1000 != null && !top1000.isEmpty()) {
            // 2. 归档到 MySQL
            archiveService.saveWeeklyRanking("game", year, week, top1000);
        }

        // 3. 删除旧 key 或转移
        // redisTemplate.delete(lastWeekKey);
        redisTemplate.rename(lastWeekKey, "archive:" + lastWeekKey);

        log.info("[WeeklyRanking] Archived: year={}, week={}, count={}",
            year, week, top1000 != null ? top1000.size() : 0);
    }
}
```

---

## 七、排行榜周边需求

### 1. 缓存用户昵称和头像

```
排行榜 ZSet 只存 memberId + score，不存昵称
每次展示都要 JOIN 用户表查昵称 → 性能差

解决：排行榜缓存用户信息
```

```java
@Component
public class RankingCacheService {

    private static final String USER_INFO_KEY = "ranking:user:info:";

    /**
     * 批量缓存用户信息
     */
    public void cacheUserInfo(List<UserInfo> users) {
        for (UserInfo user : users) {
            String key = USER_INFO_KEY + user.getUserId();
            Map<String, String> info = Map.of(
                "nickname", user.getNickname(),
                "avatar", user.getAvatar() != null ? user.getAvatar() : "",
                "tier", String.valueOf(user.getTier())
            );
            redisTemplate.opsForHash().putAll(key, info);
            redisTemplate.expire(key, 1, TimeUnit.HOURS);
        }
    }

    /**
     * 获取用户信息（缓存优先，miss 查 DB）
     */
    public UserInfo getUserInfo(Long userId) {
        String key = USER_INFO_KEY + userId;
        Map<Object, Object> cached = redisTemplate.opsForHash().entries(key);

        if (!cached.isEmpty()) {
            return new UserInfo(userId,
                (String) cached.get("nickname"),
                (String) cached.get("avatar"),
                Integer.parseInt((String) cached.get("tier"))
            );
        }

        // 缓存 miss，查 DB 并回填
        UserInfo user = userMapper.selectById(userId);
        if (user != null) {
            cacheUserInfo(List.of(user));
        }
        return user;
    }
}
```

### 2. 排行榜变更事件推送

```
场景：游戏玩家战力变化后，需要通知前端更新展示

方案：WebSocket 推送 + 订阅 Redis Keyspace 通知（不推荐生产）

推荐方案：玩家主动拉取 + 前端轮询
```

---

## 八、高频面试题

**Q1: Redis ZSet 的时间复杂度是多少？**
> ZADD、ZREM、ZINCRBY 都是 O(log N)，N 为集合大小。ZRANGE、ZRANK 是 O(log N + M)（M 为返回元素数量）。因为底层是跳表（SkipList）实现，查询效率接近红黑树但写入并发更好。

**Q2: 如何保证排行榜的精确性？**
> 增量更新要原子操作：用 Lua 脚本保证 ZINCRBY 的原子性。并发写入时分数用 `+delta` 而非先读再写，避免 ABA 问题。如果需要绝对精确，最终以 MySQL 数据为准。

**Q3: 热榜（TOP 100）和长尾榜（万名后）怎么分层处理？**
> 热层用 Redis ZSet 存 TOP 10000，保证毫秒级查询。万名后走 MySQL 索引（score + user_id 复合索引），配合分页查询。查询排名时优先热层，热层 miss 再查 MySQL。

**Q4: 排行榜数据丢失怎么办？**
> Redis 数据定期持久化到 MySQL（比如每分钟增量同步）。Redis 本身开启 AOF 持久化（RDB 每 5 分钟）。异常恢复时从 MySQL 重建 Redis 数据。冷热数据分离让故障恢复更快。

**Q5: 如何防止刷分（作弊）？**
> ① 分数变更必须经过服务端验签；② 单用户更新频率限流（如每秒最多更新 1 次）；③ 异常分数变化监控（如瞬间暴涨 10 倍触发告警）；④ 关键排行榜定期人工复核。

---

**参考链接：**
- [Redis 有序集合详解](https://redis.io/docs/data-types/sorted-sets/)
- [游戏排行榜设计实践](https://cloud.tencent.com/developer/article/1886417)
- [美团如何设计排行榜系统](https://tech.meituan.com/2018/01/19/ranking-system-design.html)
