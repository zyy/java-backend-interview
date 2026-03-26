---
layout: default
title: 消息队列可靠性保障方案
---
# 消息队列可靠性保障方案

## 🎯 面试题：如何保证消息队列不丢消息？

> 消息丢失是 MQ 最严重的事故——支付成功消息丢了意味着用户付了钱但订单没创建，库存扣减消息丢了意味着超卖。这三节课覆盖了消息从生产者到 broker 到消费者的全链路可靠性。

---

## 一、消息丢失的三种场景

```
消息生命周期中的三个丢消息节点：

Producer ──①丢──→ Broker ──②丢──→ Consumer
                    ↓
              ① 生产者发送失败
              ② Broker 存储失败
              ③ 消费者处理失败
```

---

## 二、生产者端可靠性

### 发送模式对比

```java
// 方式一：发完即忘（fire-and-forget）—— 最高效，最不可靠
kafkaTemplate.send(topic, message);
// 不关心是否到达 broker，网络抖动就丢了

// 方式二：同步发送 —— 可靠，性能差
try {
    RecordMetadata metadata = kafkaTemplate.send(topic, message).get(3, TimeUnit.SECONDS);
    System.out.println("发送成功，offset=" + metadata.getOffset());
} catch (ExecutionException e) {
    // 发送失败，broker 没收到
    handleFailure(e);
}

// 方式三：异步发送 + 回调 —— 推荐
kafkaTemplate.send(topic, message, new Callback() {
    @Override
    public void onCompletion(RecordMetadata metadata, Exception e) {
        if (e != null) {
            log.error("发送失败", e);
            // 记录失败，重试
            retrySend(topic, message);
        } else {
            log.info("发送成功 offset={}", metadata.getOffset());
        }
    }
});
```

### Producer 端重试策略

```yaml
spring:
  kafka:
    producer:
      retries: 3                        # 重试次数
      retry-backoff-ms: 1000            # 重试间隔
      acks: all                         # 所有副本确认
      properties:
        enable.idempotence: true        # 开启幂等发送
```

---

## 三、Broker 端可靠性

### Kafka 可靠性核心参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `acks` | `all` | 所有 ISR 副本确认后才算发送成功 |
| `min.insync.replicas` | `2` | 最小同步副本数 |
| `replication.factor` | `3` | 分区副本数 |
| `unclean.leader.election.enable` | `false` | 不允许非 ISR 副本成为 leader |

### 刷盘策略

```yaml
# Kafka 配置
log.flush.interval.messages=10000   # 消息达到多少条时刷盘
log.flush.interval.ms=1000           # 最多等多久刷盘

# 生产建议：不要用同步刷盘，用异步批量刷盘
# Kafka 默认就是异步刷盘，配合 acks=all 在性能和可靠性间取得平衡
```

### Broker 端防丢配置完整示例

```yaml
spring:
  kafka:
    producer:
      acks: all                      # 最强可靠性
      retries: 3
      properties:
        enable.idempotence: true     # 开启幂等
        max.in.flight.requests.per.connection: 5
        acks: all
    consumer:
      auto-offset-reset: earliest    # 最早未消费消息开始消费
      enable-auto-commit: false       # 手动提交 offset
```

---

## 四、消费者端可靠性

### 手动提交 offset

```java
@KafkaListener(topics = "payment-success", groupId = "order-service")
public void handlePaymentSuccess(ConsumerRecord<String, PaymentMessage> record, Acknowledgment ack) {
    PaymentMessage message = record.value();

    try {
        // 1. 业务处理
        orderService.confirmOrder(message.getOrderId());

        // 2. 业务处理成功后才提交 offset
        ack.acknowledge();
        log.info("消费成功 offset={}", record.offset());

    } catch (Exception e) {
        // 3. 业务处理失败，不提交 offset，消息会被重新消费
        log.error("消费失败 offset={}", record.offset(), e);
        // 可以在这里记录失败日志，便于排查
        throw e; // 重新抛出，让 Kafka 自动重试
    }
}
```

### ⚠️ 先提交 offset 还是先处理业务？

```
❌ 先提交 offset，后处理业务：
  ack.submit() → 记录 offset=100
  处理业务时崩溃
  → 重启后从 offset=101 开始消费
  → offset=100 的消息被永久跳过 ❌

✅ 先处理业务，后提交 offset（正确）：
  处理业务 → 成功
  ack.submit() → 记录 offset=100
  → 最多重复消费，不会漏消息 ✅
```

---

## 五、事务消息（最强可靠性）

### RocketMQ 事务消息

```java
// Step 1: 发送半消息（Half Message）—— 对消费者不可见
@Transactional
public void createOrder(OrderCreateRequest request) {
    // 1. 发送半消息，事务开始
    TransactionMQProducer producer = rocketMQTemplate.getProducer();
    Message message = MessageBuilder
        .withPayload(request)
        .setHeader("orderId", request.getOrderId())
        .build();

    // 发送半消息，并注册事务执行器
    TransactionSendResult result = rocketMQTemplate.sendMessageInTransaction(
        "order-topic",
        message,
        new OrderTransactionListener(orderService, request) // 事务回调
    );
}

// Step 2: 事务执行器（本地事务 + 回查）
@Service
@Slf4j
public class OrderTransactionListener implements TransactionListener {

    @Autowired
    private OrderMapper orderMapper;

    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        OrderCreateRequest request = (OrderCreateRequest) arg;
        try {
            // 本地事务：创建订单（和半消息在同一个事务中）
            orderMapper.createOrder(request);
            return LocalTransactionState.COMMIT_MESSAGE; // 提交，消息对消费者可见
        } catch (Exception e) {
            log.error("本地事务失败，回滚", e);
            return LocalTransactionState.ROLLBACK_MESSAGE; // 回滚，消息被丢弃
        }
    }

    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        // RocketMQ 自动回查：事务超时未提交，调用此方法
        String orderId = msg.getUserProperties("orderId");
        Order order = orderMapper.selectByOrderId(orderId);

        if (order != null) {
            return LocalTransactionState.COMMIT_MESSAGE; // 订单存在，提交
        } else {
            return LocalTransactionState.ROLLBACK_MESSAGE; // 订单不存在，回滚
        }
    }
}
```

### 事务消息原理

```
正常流程：
  Producer → 发送 Half Message → Broker 存储（不可消费）
  Producer → 执行本地事务（创建订单）
  Producer → 提交 Transaction Commit → 消息对消费者可见
  Consumer → 消费消息

异常流程（本地事务失败）：
  Producer → 发送 Half Message
  Producer → 本地事务失败
  Producer → 提交 Transaction Rollback → 消息被丢弃

超时流程（RocketMQ 自动回查）：
  Producer → 发送 Half Message
  Producer → 本地事务执行中...（超时）
  Broker → 调用 checkLocalTransaction（回查接口）
  → 根据业务表判断事务是否成功
  → 决定提交或回滚
```

---

## 六、消息幂等消费

### 为什么需要幂等？

```
MQ 重投机制导致消息重复：

Consumer 处理消息成功，发送 ACK 时网络抖动
→ Broker 没收到 ACK
→ Broker 重投消息
→ Consumer 再次处理 → 重复消费 ❌

场景：
  - 支付成功消息重复 → 重复发货
  - 库存扣减消息重复 → 库存扣多次
  - 积分发放消息重复 → 积分多发
```

### 幂等方案一：数据库唯一约束

```java
// 消息处理记录表
@TableName("message_dedup")
public class MessageDedup {
    private String messageId;      // 消息唯一 ID
    private Integer status;        // 0-处理中 1-成功 2-失败
    private LocalDateTime createTime;
}

@Service
public class OrderService {

    @Autowired
    private MessageDedupMapper dedupMapper;

    public void handlePaymentSuccess(PaymentMessage msg) {
        String messageId = msg.getMessageId();

        // 1. 尝试插入幂等记录
        int inserted = dedupMapper.insertIfNotExists(messageId);
        if (inserted == 0) {
            log.info("消息已处理过，跳过: {}", messageId);
            return;
        }

        // 2. 执行业务
        processOrder(msg);

        // 3. 更新状态
        dedupMapper.updateStatus(messageId, 1);
    }
}
```

### 幂等方案二：Redis 去重

```java
public void handleMessage(String messageId) {
    String key = "msg:consumed:" + messageId;

    // SETNX 原子操作
    Boolean success = redisTemplate.opsForValue()
        .setIfAbsent(key, "1", Duration.ofHours(24));

    if (!Boolean.TRUE.equals(success)) {
        log.info("消息已消费，跳过: {}", messageId);
        return;
    }

    // 业务处理...
}
```

---

## 七、消息顺序性

### 为什么顺序重要？

```
下单流程：
  ① 创建订单（msg.order=1）
  ② 扣减库存（msg.order=2）
  ③ 扣减积分（msg.order=3）

乱序后果：
  ② 先执行 → 库存不够了
  ① 再执行 → 订单创建失败

支付流程：
  ① 扣款成功（余额 1000 → 900）
  ② 积分发放（发 100 积分）

乱序后果：
  ② 先执行 → 用户凭空多了积分
```

### Kafka 分区有序

```java
// 生产者：指定相同 key 的消息发送到同一分区
kafkaTemplate.send("order-topic", orderId, orderMessage);
// 同一 orderId 的消息一定到同一分区，分区内有序

// 消费者：单分区单线程消费
@KafkaListener(topics = "order-topic", containerFactory = "kafkaListenerContainerFactory")
public void consume(ConsumerRecord<String, OrderMessage> record) {
    // 同一分区的消息顺序消费
    processOrder(record.value());
}
```

---

## 八、死信队列（DLQ）

### 什么是死信？

```
消息进入死信的几种情况：
1. 消费者消费失败，超过最大重试次数
2. 消息过期（TTL）
3. 消息大小超过队列限制
4. 队列满了，新消息被丢弃
```

### RocketMQ 死信队列配置

```yaml
spring:
  rocketmq:
    consumer:
      # 死信队列配置
      max-reconsume-times: 3   # 最大重试次数
```

```java
// 死信队列名称自动生成：DLQ.topic-name
// 消费死信队列消息，处理异常情况
@RocketMQMessageListener(
    topic = "DLQ-order-topic",
    consumerGroup = "dlq-handler-group"
)
public class DlqHandler {
    public void handle(MessageExt msg) {
        log.error("死信消息: {}", new String(msg.getBody()));
        // 人工处理：记录日志、发告警、人工补偿
    }
}
```

### Kafka 死信主题

```yaml
spring:
  kafka:
    listener:
      retry:
        initial-interval: 1000
        max-attempts: 3
        multiplier: 2.0
      # 超过重试次数后进入死信主题
      default-re_topic-recovery: true
```

---

## 九、高频面试题

**Q1: Kafka 如何保证不丢消息？**
> 从三个层面配置：① 生产者端：`acks=all` + `retries=3` + `enable.idempotence=true`，确保消息发送到所有 ISR 副本；② Broker 端：`replication.factor=3` + `min.insync.replicas=2` + `unclean.leader.election.enable=false`；③ 消费者端：`enable.auto.commit=false` + 手动提交 offset，在业务处理完成后才提交。

**Q2: 先提交 offset 还是先处理业务？**
> 正确做法是先处理业务，后提交 offset。如果先提交 offset 再处理业务，处理过程中宕机会导致消息被跳过（永久丢失）。先处理业务后提交 offset，最多出现重复消费（可接受），不会出现消息丢失。

**Q3: RocketMQ 事务消息的原理是什么？**
> RocketMQ 采用半消息机制：发送事务消息时，先发送一条对消费者不可见的半消息；然后执行本地事务；最后根据本地事务结果提交或回滚半消息。如果本地事务超时未响应，RocketMQ 会自动调用回查接口查询事务状态。核心思想是把「发送消息」和「本地事务」绑定为原子操作，确保要么全部成功，要么全部失败。

**Q4: 如何保证消息消费的幂等性？**
> 两种主流方案：① 数据库唯一约束：创建一张消息处理记录表，以消息 ID 为主键，消费前先尝试插入，插入成功才执行业务；② Redis 去重：以消息 ID 为 key 执行 SETNX，操作成功才处理。这两种方案都能保证消息只被处理一次。

**Q5: 如何处理顺序消息？**
> 以 Kafka 为例：① 生产者端用相同业务 key 发送消息（如 orderId），保证同一订单的消息路由到同一分区；② 消费者端单线程消费单个分区；③ 如果需要跨分区有序，可以在消费端用内存队列保证顺序。需要注意的是，分区有序 ≠ 全局有序，需要根据业务场景选择。
