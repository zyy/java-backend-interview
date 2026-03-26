---
layout: default
title: 如何设计一个站内消息系统？⭐⭐⭐
---
# 如何设计一个站内消息系统？

## 🎯 面试题：设计一个站内消息系统

> 站内消息系统是互联网产品的标配能力，看似简单，但要支撑大规模用户、多消息类型、实时推送，有很多设计难点。

---

## 一、需求分析

### 消息类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **系统通知** | 平台级推送，全员或定向 | 系统维护公告、活动通知 |
| **互动消息** | 用户间交互触发 | 有人@你、评论回复、点赞 |
| **私信** | 一对一/多对多聊天 | 站内私信 |
| **业务消息** | 业务流程节点通知 | 订单状态变更、审批通过 |

### 核心功能

```
✅ 消息发送（单发/群发/广播）
✅ 消息接收与列表查询
✅ 未读计数与已读标记
✅ 消息推送（实时通知）
✅ 消息模板（运营配置）
✅ 消息归档与清理
```

### 非功能需求

```
- 高可用：消息不能丢，不能重复
- 低延迟：发送到展示 < 500ms
- 高吞吐：支撑千万级 DAU
- 可扩展：新消息类型方便接入
```

---

## 二、整体架构设计

```
                        ┌──────────────┐
                        │  消息发送方   │
                        │ (业务服务)    │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  消息网关     │  ← 统一接入层
                        │ (API Gateway)│
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
      ┌───────────┐   ┌──────────────┐  ┌────────────┐
      │ 消息聚合  │   │  消息存储     │  │ 推送服务   │
      │ 服务      │   │  (DB + Redis) │  │ (WebSocket)│
      └───────────┘   └──────────────┘  └────────────┘
              │                │                │
              ▼                ▼                ▼
       ┌──────────┐   ┌─────────────┐   ┌────────────┐
       │ 消息列表  │   │ MySQL       │   │ 客户端     │
       │ 查询服务  │   │ (持久化)     │   │ App/Web    │
       └──────────┘   └─────────────┘   └────────────┘
```

---

## 三、核心模块设计

### 1. 消息存储方案

**核心矛盾：消息要持久化（查历史），又要实时（推送到客户端）。**

```
┌─────────────────────────────────────────┐
│              消息存储分层                 │
│                                         │
│  Redis（热数据）                         │
│  ├── 最近 N 条消息（收件箱模型）         │
│  ├── 未读计数（Hash/Counter）           │
│  └── 在线状态 & 推送通道标识             │
│                                         │
│  MySQL（全量数据）                       │
│  ├── message（消息表）                   │
│  ├── message_recipient（收件关系表）     │
│  └── message_template（模板表）          │
│                                         │
│  Elasticsearch（可选，消息搜索）         │
└─────────────────────────────────────────┘
```

#### MySQL 表设计

```sql
-- 消息主表
CREATE TABLE `message` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `msg_type`        TINYINT NOT NULL COMMENT '消息类型: 1-系统 2-互动 3-私信 4-业务',
    `sender_id`       BIGINT NOT NULL DEFAULT 0 COMMENT '发送者, 0=系统',
    `template_id`     BIGINT NULL COMMENT '模板ID',
    `title`           VARCHAR(255) NOT NULL,
    `content`         TEXT NOT NULL,
    `extra_data`      JSON NULL COMMENT '扩展字段(跳转链接等)',
    `status`          TINYINT NOT NULL DEFAULT 1 COMMENT '1-正常 2-撤回 3-删除',
    `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_sender` (`sender_id`),
    INDEX `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 收件关系表（解耦发送和接收，支持群发）
CREATE TABLE `message_recipient` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `message_id`      BIGINT NOT NULL,
    `recipient_id`    BIGINT NOT NULL COMMENT '接收者',
    `is_read`         TINYINT NOT NULL DEFAULT 0 COMMENT '0-未读 1-已读',
    `read_at`         DATETIME NULL,
    `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_msg_recipient` (`message_id`, `recipient_id`),
    INDEX `idx_recipient_read` (`recipient_id`, `is_read`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 消息模板表（运营配置）
CREATE TABLE `message_template` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `template_code`   VARCHAR(64) NOT NULL UNIQUE,
    `title_template`  VARCHAR(255) NOT NULL COMMENT '标题模板, 支持${变量}',
    `content_template` TEXT NOT NULL COMMENT '内容模板',
    `msg_type`        TINYINT NOT NULL,
    `status`          TINYINT NOT NULL DEFAULT 1,
    `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**设计要点：**
- **收件关系表独立**：一条消息发给 10 万人，message 表只存 1 条，recipient 表存 10 万条关系
- **未读计数走 Redis**：不查 DB，避免高频读
- **分表策略**：recipient 表按 recipient_id 分表（用户维度查询多）

### 2. Redis 缓存设计

```
# 未读计数
unread:{userId}:{msgType} → String (计数器)
unread:{userId}:total     → String (总未读数)

# 收件箱（最近 N 条消息 ID 列表，按时间倒序）
inbox:{userId}:{msgType}  → List (存 message_id)

# 消息详情缓存（读多写少，缓存最近消息）
msg:detail:{messageId}    → Hash (title, content, sender_id, created_at)

# 在线用户推送通道
online:{userId}           → String (WebSocket sessionId / MQ consumer tag)
```

```java
// 未读计数操作
public long getUnreadCount(Long userId, int msgType) {
    String key = String.format("unread:%d:%d", userId, msgType);
    return redisTemplate.opsForValue().increment(key, 0);
}

public void markAsRead(Long userId, Long messageId, int msgType) {
    // 1. Redis 原子减 1
    String key = String.format("unread:%d:%d", userId, msgType);
    Long count = redisTemplate.opsForValue().decrement(key);
    if (count != null && count < 0) {
        redisTemplate.opsForValue().set(key, 0L);
    }
    // 2. 异步更新 DB（MySQL 批量标记已读）
    mqProducer.send(new MarkReadEvent(userId, messageId));
}
```

### 3. 消息发送流程

```
业务服务调用消息 API
    ↓
消息网关（参数校验 + 鉴权）
    ↓
写入 MySQL（message + recipient）
    ↓
写入 Redis 收件箱（List LPUSH）
    ↓
Redis 未读计数 +1（INCR）
    ↓
发送 MQ 消息（通知推送服务）
    ↓
推送服务检查接收者是否在线
    ├── 在线 → WebSocket 推送 + APNs/FCM（移动端）
    └── 离线 → 等待下次上线拉取
```

**关键设计：读写分离的发送链路**

```java
@Service
public class MessageService {

    @Autowired
    private MessageMapper messageMapper;
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    @Autowired
    private RocketMQTemplate mqTemplate;

    @Transactional
    public SendMessageResult send(SendMessageRequest request) {
        // 1. 写入消息主表
        Message message = new Message();
        message.setMsgType(request.getMsgType());
        message.setTitle(request.getTitle());
        message.setContent(request.getContent());
        messageMapper.insert(message);

        // 2. 批量写入收件关系（群发场景分批插入）
        List<Long> recipientIds = request.getRecipientIds();
        batchInsertRecipients(message.getId(), recipientIds);

        // 3. 写入 Redis 收件箱 + 未读计数（批量 Pipeline）
        redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
            for (Long recipientId : recipientIds) {
                String inboxKey = String.format("inbox:%d:%d", recipientId, request.getMsgType());
                connection.lPush(inboxKey.getBytes(),
                    String.valueOf(message.getId()).getBytes());
                // 限制收件箱长度，只保留最近 100 条
                connection.lTrim(inboxKey.getBytes(), 0, 99);

                String unreadKey = String.format("unread:%d:%d", recipientId, request.getMsgType());
                connection.incr(unreadKey.getBytes());

                String totalKey = String.format("unread:%d:total", recipientId);
                connection.incr(totalKey.getBytes());
            }
            return null;
        });

        // 4. 异步通知推送服务
        mqTemplate.convertAndSend("message-push-topic",
            new PushEvent(message.getId(), recipientIds));

        return new SendMessageResult(message.getId());
    }
}
```

### 4. 消息列表查询

```
用户请求消息列表
    ↓
先查 Redis 收件箱（最近 N 条 messageId）
    ├── 命中 → 批量从 Redis/DB 获取消息详情
    └── 未命中 → 查 DB 分页，回填 Redis

展示列表 + 未读计数
```

```java
public PageResult<MessageVO> listMessages(Long userId, int msgType, int page, int size) {
    String inboxKey = String.format("inbox:%d:%d", userId, msgType);

    // 1. 从 Redis 收件箱获取 messageId 列表
    List<String> msgIds = redisTemplate.opsForList().range(
        inboxKey, (long) (page - 1) * size, (long) page * size - 1);

    if (msgIds != null && !msgIds.isEmpty()) {
        // 2. 批量获取消息详情（先 Redis 缓存，miss 再查 DB）
        List<MessageVO> messages = getMessageDetailBatch(msgIds);
        return new PageResult<>(messages, getTotalCount(userId, msgType));
    }

    // 3. Redis 无数据，走 DB 分页
    return messageMapper.selectByRecipientPage(userId, msgType, page, size);
}
```

### 5. 实时推送方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **WebSocket** | 长连接双向通信 | 实时性最好，服务端主动推 | 需要维护长连接，集群扩展复杂 |
| **SSE** | HTTP 长连接单向推送 | 实现简单，兼容好 | 单向，无法从客户端收消息 |
| **MQ 长轮询** | 客户端轮询拉取 | 实现最简单 | 实时性差，资源浪费 |
| **MQTT** | 轻量级消息协议 | 移动端友好，省电 | 需要额外 Broker |

**推荐方案：WebSocket + MQTT（移动端）**

```
推送服务集群
    ├── WebSocket Server（Web/App 在线用户）
    │   ├── 本地 session 管理（userId → session 映射）
    │   └── 跨节点推送：通过 Redis Pub/Sub 广播
    │
    └── MQTT Broker（移动端，如 EMQX）
        ├── 离线消息缓存
        └── QoS 0/1/2 消息质量保证
```

**跨节点 WebSocket 推送：**
```java
// 订阅 Redis 频道，收到消息后推送给本节点维护的在线用户
@RocketMQMessageListener(topic = "message-push-topic", consumerGroup = "push-group")
public class PushConsumer implements RocketMQListener<PushEvent> {

    @Autowired
    private WebSocketSessionManager sessionManager;

    @Override
    public void onMessage(PushEvent event) {
        for (Long userId : event.getRecipientIds()) {
            WebSocketSession session = sessionManager.getSession(userId);
            if (session != null && session.isOpen()) {
                // 本节点有该用户的连接，直接推送
                session.sendMessage(new TextMessage(
                    JsonUtils.toJson(new PushNotification(event.getMessageId()))
                ));
            }
            // 其他节点有该用户的连接，由 Pub/Sub 广播处理
            // 或者直接查 Redis 中的在线节点标识
        }
    }
}
```

---

## 四、性能优化

### 1. 群发消息优化

```
场景：给 100 万用户发送系统公告

❌ 逐条插入 recipient 表 → 100 万次 INSERT，耗时极长
✅ 批量插入 + 异步任务分片
```

```java
// 分片异步批量插入
@Async("messageExecutor")
public void batchInsertRecipients(Long messageId, List<Long> recipientIds) {
    Lists.partition(recipientIds, 1000).forEach(batch -> {
        messageMapper.batchInsertRecipient(messageId, batch);
    });
}
```

### 2. 未读计数防脏读

```
问题：Redis 计数和 DB 状态不一致怎么办？

方案：以 Redis 为准（显示），定期与 DB 对账（修复）
```

```java
// 定时对账任务（每天凌晨低峰期执行）
@Scheduled(cron = "0 0 3 * * ?")
public void syncUnreadCount() {
    // 从 DB 查出真实未读数，修复 Redis
    List<UnreadStat> stats = messageMapper.selectUnreadStats();
    stats.forEach(stat -> {
        String key = String.format("unread:%d:%d", stat.getUserId(), stat.getMsgType());
        redisTemplate.opsForValue().set(key, (long) stat.getUnreadCount());
    });
}
```

### 3. 消息已读优化

```
场景：用户一次点开消息列表，所有消息都标记已读

❌ 逐条发请求 → N 次 HTTP + N 次 DB UPDATE
✅ 批量标记已读接口
```

```java
@PostMapping("/batch-read")
public Result batchMarkAsRead(@RequestParam int msgType) {
    Long userId = getCurrentUserId();
    // 1. Redis 批量清零
    String unreadKey = String.format("unread:%d:%d", userId, msgType);
    redisTemplate.opsForValue().set(unreadKey, 0L);
    String totalKey = String.format("unread:%d:total", userId);
    redisTemplate.opsForValue().decrement(totalKey);

    // 2. 异步更新 DB
    mqTemplate.convertAndSend("message-read-topic",
        new BatchReadEvent(userId, msgType));
    return Result.success();
}
```

---

## 五、高频面试题

**Q1: 消息丢失怎么办？**
> 发送链路用 MQ 保证至少一次投递（开启 MQ 重试 + 死信队列）。DB 做持久化兜底，推送失败的消息存 DB，用户上线后拉取补偿。核心原则：**存储 > 推送**，消息先落库，推送是增强。

**Q2: 群发 100 万用户怎么优化？**
> ① recipient 表分批异步插入（每批 1000 条）；② Redis 写入用 Pipeline 批量操作；③ 推送走 MQ 分片消费，不阻塞主链路；④ 运营侧看发送进度，不要求实时完成。

**Q3: 未读消息数不准确怎么解决？**
> 以 Redis 为准做展示，定期凌晨对账修复。极端情况（Redis 故障降级）直接查 DB COUNT。

**Q4: WebSocket 集群怎么保证消息推送到正确的节点？**
> 方案一：Redis Pub/Sub 广播到所有节点，各节点检查本地 session；方案二：一致性哈希 + Redis 存储用户所在节点标识，定向推送。方案一简单但有冗余广播，方案二精准但实现复杂。

**Q5: 消息撤回怎么实现？**
> ① DB 更新消息状态为"已撤回"；② 推送撤回通知给在线用户（WebSocket）；③ 客户端收到撤回指令后本地删除或显示"已撤回"；④ 离线用户下次拉取时看到的是已撤回状态。

---

**参考链接：**
- [美团站内消息系统架构实践](https://tech.meituan.com/2018/10/11/notification-system-architecture.html)
- [微信公众号消息系统设计](https://mp.weixin.qq.com/s/xxx)
