---
layout: default
title: 如何设计一个 Feed 流系统？⭐⭐⭐
---
# 如何设计一个 Feed 流系统？

## 🎯 面试题：设计一个微博/朋友圈/Twitter 样式的信息流

> Feed 流是内容分发的核心形态，本质是"谁发了什么内容，推给谁看"。

---

## 一、Feed 流的核心概念

### 什么是 Feed？

```
Timeline（时间线）
┌──────────────────────────────────────┐
│  张三 发了动态                         │
│  李四 发了动态                         │  ← 按时间倒序排列
│  王五 发了动态                         │
│  赵六 发了动态                         │
└──────────────────────────────────────┘
```

### Feed 流的几种模式

| 模式 | 说明 | 代表产品 | 核心挑战 |
|------|------|---------|---------|
| **Timeline** | 每个用户看到自己的关注列表，按时间排序 | 微博、朋友圈 | 如何快速拉取 |
| **Rank** | 按算法重新排序，不严格按时间 | 抖音、微信视频号 | 排序算法 |
| **Inbox** | 消息先聚合，再推送 | 微博 Push 模式 | 推送量大 |
| **Pull** | 用户拉取时实时聚合 | 微博 Timeline | 读延迟高 |

### 核心性能指标

```
- 写入吞吐量：每秒发布消息数
- 读取延迟：用户打开 Feed 到内容展示 < 500ms
- 存储成本：每条消息的存储空间
- 推送成本：消息写放大比例（1:N 扩散）
```

---

## 二、整体架构设计

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  内容发布     │───▶│  Feed 写入服务 │───▶│  Message Queue  │
│ (发微博/发动态)│    │ (写扩散/读扩散)│    │ (Kafka/RocketMQ)│
└──────────────┘    └──────────────┘    └────────┬─────────┘
                                                  │
                           ┌──────────────────────┴──────────┐
                           ▼                              ▼
                    ┌──────────────┐              ┌──────────────┐
                    │  写入扩散     │              │  读取聚合     │
                    │ (Push Model) │              │ (Pull Model) │
                    └──────┬───────┘              └──────┬───────┘
                           │                              │
                           ▼                              ▼
                    ┌──────────────┐              ┌──────────────┐
                    │  收件箱存储   │              │  内容表       │
                    │ (Redis List) │              │ (MySQL/ES)   │
                    └──────────────┘              └──────────────┘
                           │                              │
                           ▼                              ▼
                    ┌──────────────┐              ┌──────────────┐
                    │  用户请求     │◀────────────│  关注列表     │
                    │ (读取收件箱)  │              │ (Redis Set)   │
                    └──────────────┘              └──────────────┘
```

---

## 三、核心存储方案

### 方案一：写扩散（Push）

**思路**：发布时主动把内容写入所有粉丝的收件箱。

```
发布流程：
用户A 发布内容
    ↓
查询 A 的所有粉丝列表（Redis Set）
    ↓
遍历粉丝列表，向每个粉丝的收件箱 LPUSH 新内容
    ↓
如果粉丝数 > 阈值，改用异步任务队列
```

**优点**：读取极快，直接从自己的收件箱拿数据  
**缺点**：大 V 发布的写放大问题（1 粉丝 = N 次写操作）

```
大 V 问题：
粉丝数 = 1000 万
每次发微博 = 1000 万次写操作 ❌

解决方案：阈值截断
  - 粉丝数 < 1 万 → 实时写扩散
  - 粉丝数 >= 1 万 → 写扩散降级为只写自己收件箱
```

```java
@Service
public class FeedPushService {

    @Autowired private FeedMapper feedMapper;
    @Autowired private FollowMapper followMapper;
    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private RocketMQTemplate mqTemplate;

    // 大 V 粉丝数阈值，超过则降级
    private static final long PUSH_THRESHOLD = 10_000;

    public void publish(PublishRequest request) {
        Long userId = request.getUserId();

        // 1. 写入内容表
        Feed feed = new Feed();
        feed.setUserId(userId);
        feed.setContent(request.getContent());
        feedMapper.insert(feed);

        Long feedId = feed.getId();

        // 2. 判断是否走写扩散
        long fanCount = followMapper.selectFanCount(userId);

        if (fanCount < PUSH_THRESHOLD) {
            // 小 V：实时写扩散，遍历粉丝写入各自收件箱
            List<Long> fanIds = followMapper.selectFanIds(userId);
            for (Long fanId : fanIds) {
                String inboxKey = "inbox:" + fanId;
                redisTemplate.opsForList().leftPush(inboxKey, String.valueOf(feedId));
                // 限制收件箱长度，只保留最近 500 条
                redisTemplate.opsForList().trim(inboxKey, 0, 499);
            }
        } else {
            // 大 V：写扩散降级
            // 只写自己的收件箱，粉丝通过读扩散拉取
            String selfInboxKey = "inbox:" + userId;
            redisTemplate.opsForList().leftPush(selfInboxKey, String.valueOf(feedId));

            // 发 MQ 通知离线粉丝（可选）
            mqTemplate.convertAndSend("fan-notify-topic",
                new FanNotifyEvent(userId, feedId, fanIds));
        }
    }
}
```

### 方案二：读扩散（Pull）

**思路**：发布时只写自己的内容表，读的时候实时聚合关注列表。

```
读取流程：
用户请求 Feed
    ↓
获取关注列表（Redis Set，1000 个用户）
    ↓
批量查询每个用户最近 N 条内容
    ↓
归并排序（按时间/热度）
    ↓
返回前 M 条
```

**优点**：写入成本极低，大 V 无压力  
**缺点**：读取时计算量大，关注列表大时延迟高

```java
@Service
public class FeedPullService {

    @Autowired private FeedMapper feedMapper;
    @Autowired private FollowMapper followMapper;

    public List<FeedVO> getFeed(Long userId, int offset, int limit) {
        // 1. 获取关注列表（带缓存）
        List<Long> followingIds = getFollowingWithCache(userId);
        if (followingIds.isEmpty()) {
            return Collections.emptyList();
        }

        // 2. 批量查询每个用户最近的 feeds
        int pageSize = 20;
        List<Feed> feeds = feedMapper.selectByUsersAndLimit(
            followingIds,
            offset,
            pageSize * followingIds.size()
        );

        // 3. 内存归并排序
        feeds.sort((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()));

        // 4. 截取分页
        return feeds.stream()
            .skip(offset)
            .limit(limit)
            .collect(Collectors.toList());
    }

    private List<Long> getFollowingWithCache(Long userId) {
        String key = "following:" + userId;
        List<String> ids = redisTemplate.opsForList().range(key, 0, -1);
        if (ids == null || ids.isEmpty()) {
            List<Long> followingIds = followMapper.selectFollowingIds(userId);
            if (!followingIds.isEmpty()) {
                redisTemplate.opsForList().rightPushAll(key, followingIds.stream()
                    .map(String::valueOf).toList());
            }
            return followingIds;
        }
        return ids.stream().map(Long::parseLong).toList();
    }
}
```

### 方案三：混合模式（推荐生产方案）

```
核心思路：分层存储 + 分级读取

小 V（粉丝 < 1 万）→ 写扩散，粉丝收件箱直接拿到内容
大 V（粉丝 >= 1 万）→ 写自己收件箱，粉丝用读扩散拉取

读取时：
  1. 先取自己的收件箱（小 V 写进来的）
  2. 再批量拉取大 V 朋友的最新内容
  3. 归并排序后展示
```

```
Redis 存储：
inbox:{userId}  → List（收件箱消息 ID 列表，最大 500 条）
user:feeds:{userId} → List（自己发布的内容，备份用）

内容存储：
feed:{feedId}   → Hash（Feed 详情缓存）
feed:comments:{feedId} → List（评论列表）
```

---

## 四、缓存设计

### 多级缓存策略

```
L1: 用户本地缓存（App 端，LRU，100 条）
L2: Redis 分布式缓存（热内容，TTL 1 小时）
L3: MySQL/ES 持久化存储
```

```java
// 读取流程：先本地 → 再 Redis → 最后 DB
public List<FeedVO> getFeedWithCache(Long userId, int page) {
    int pageSize = 20;
    String cacheKey = "feed:page:" + userId + ":" + page;

    // L1: 本地缓存（Guava Cache / Caffeine）
    List<FeedVO> localCached = localCache.getIfPresent(cacheKey);
    if (localCached != null) {
        return localCached;
    }

    // L2: Redis 缓存
    List<String> cachedIds = redisTemplate.opsForList().range(cacheKey, 0, pageSize - 1);
    if (cachedIds != null && !cachedIds.isEmpty()) {
        List<FeedVO> feeds = batchGetFeedDetail(cachedIds);
        localCache.put(cacheKey, feeds);
        return feeds;
    }

    // L3: 读取收件箱
    String inboxKey = "inbox:" + userId;
    long start = (long) page * pageSize;
    List<String> feedIds = redisTemplate.opsForList().range(inboxKey, start, start + pageSize - 1);

    if (feedIds == null || feedIds.isEmpty()) {
        return Collections.emptyList();
    }

    List<FeedVO> feeds = batchGetFeedDetail(feedIds);
    localCache.put(cacheKey, feeds);
    redisTemplate.opsForList().rightPushAll(cacheKey, feedIds);
    redisTemplate.expire(cacheKey, 1, TimeUnit.HOURS);

    return feeds;
}
```

---

## 五、点赞/评论的写入优化

```
点赞操作：
❌ 每点赞一次 → 写入 Feed 记录
✅ 点赞不写 Feed 表，只更新点赞计数 + 发 MQ 通知被赞用户

评论操作：
✅ 评论写 Feed 表 → 进入关注者的信息流
```

```java
// 评论时写 Feed（评论比点赞重要，进入信息流）
public void comment(CommentRequest request) {
    Feed feed = new Feed();
    feed.setUserId(request.getUserId());
    feed.setContent(request.getContent());
    feed.setType(FeedType.COMMENT);
    feed.setRootId(request.getRootId());    // 关联原动态
    feedMapper.insert(feed);

    // 评论扩散：只通知原动态作者
    notifyAuthor(request.getRootId(), feed);
}
```

---

## 六、分页设计

### 游标分页（推荐）

```
避免 Offset 分页的深度翻页性能问题
Feed 是实时性强的数据，Offset 翻到第 1000 页时数据已过时

方案：用 timestamp + id 做游标
```

```java
// 请求参数：lastTime=1700000000, lastId=123
// 返回时带上 nextCursor
public FeedPageResult getFeed(Long userId, String cursor, int limit) {
    long timestamp = 0L;
    long lastId = Long.MAX_VALUE;

    if (cursor != null) {
        String[] parts = cursor.split("_");
        timestamp = Long.parseLong(parts[0]);
        lastId = Long.parseLong(parts[1]);
    }

    List<Feed> feeds = feedMapper.selectWithCursor(
        userId, timestamp, lastId, limit + 1
    );

    boolean hasMore = feeds.size() > limit;
    if (hasMore) {
        feeds = feeds.subList(0, limit);
    }

    List<FeedVO> vos = feeds.stream().map(this::toVO).toList();

    String nextCursor = null;
    if (hasMore && !feeds.isEmpty()) {
        Feed last = feeds.get(feeds.size() - 1);
        nextCursor = last.getCreatedAt().getTime() + "_" + last.getId();
    }

    return new FeedPageResult(vos, nextCursor, hasMore);
}
```

---

## 七、高频面试题

**Q1: 微博的大 V 发微博时，写扩散会不会把系统打挂？**
> 会，所以有阈值截断：粉丝数 < 1 万实时写扩散；超过阈值改走读扩散，大 V 只写自己的收件箱，粉丝读时实时拉取大 V 的最新 N 条内容。

**Q2: 如何保证 Feed 的分页不重复/不漏？**
> 核心是用游标分页（timestamp + id），而非 offset。offset 翻页在插入新内容时会错位，导致重复或遗漏。游标基于数据主键，稳定性强。

**Q3: Feed 流的热更新（刚发完立刻看到）和冷启动（首次加载）怎么处理？**
> 热更新走 WebSocket 推送新内容到客户端，本地列表头部插入。冷启动走 Pull 模式拉取收件箱数据，结合 L1/L2 多级缓存加速。

**Q4: 写扩散的收件箱容量满了怎么办？**
> 定期 trim，只保留最近 500-1000 条。历史内容通过搜索/归档页访问。也可以按时间分桶，访问归档桶时再加载。

**Q5: 如何实现个性化推荐排序（Rank 模式）？**
> 在 Pull 链路中，读完基础内容后加一层 Rank 服务：用 ML 模型对内容打分（互动率、点击率、内容质量），按分数重排序后返回。Rank 服务可前置缓存热门内容的结果。

---

**参考链接：**
- [微博 Feed 系统架构详解](https://www.infoq.cn/article/weibo-feed-architecture)
- [Twitter timeline 设计方案](https://blog.twitter.com/engineering/en_us/a/2012/building-a-complete-twitter-feed)
