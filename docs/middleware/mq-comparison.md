---
layout: default
title: 消息队列选型对比：Kafka vs RocketMQ vs RabbitMQ
---

# 消息队列选型对比：Kafka vs RocketMQ vs RabbitMQ

> 三大主流消息队列全方位深度对比

## 🎯 面试重点速览

| 维度 | Kafka | RocketMQ | RabbitMQ |
|------|-------|----------|----------|
| **吞吐量** | 百万级 | 十万级 | 万级 |
| **延迟** | 毫秒级 | 毫秒级 | 微秒级 |
| **事务消息** | ❌ 不支持 | ✅ 原生支持 | ✅ 支持（插件） |
| **延迟/定时消息** | ❌ 需改造 | ✅ 原生支持 | ✅ 原生支持 |
| **消息回溯** | ✅ Offset 机制 | ✅ 重试队列 | ✅ 手动 ACK |
| **顺序消息** | 分区内有序 | 分区/全局有序 | 队列级有序 |
| **适用场景** | 日志、大数据 | 电商交易 | 通用业务 |

---

## 📖 一、架构设计理念对比

### 1.1 Kafka：日志型 / 大数据导向

```java
/**
 * Kafka 设计理念：
 * "Write-ahead Log + 分区副本" — 为高吞吐日志场景而生
 *
 * 核心思想：
 * - 消息追加顺序写，追求极致顺序 IO 性能
 * - 分区副本实现水平扩展和高可用
 * - 消息保留（Retention）代替传统消费确认
 * - 消费者组隔离，不同业务逻辑独立消费同一份数据
 *
 * 架构特点：
 * - 无主从强一致性概念（ISR 机制）
 * - Topic 分区可自由扩展，不影响已有消费者
 * - 元数据管理依赖 Zookeeper（新版 KRaft 自主管理）
 *
 * 典型使用：
 * - 日志采集、监控数据收集
 * - 用户行为分析、推荐系统
 * - CDC 数据同步、大数据 ETL
 */
public class KafkaDesign {}
```

```java
/**
 * Kafka 集群架构图：
 *
 * ┌──────────────────────────────────────────────────────────────┐
 * │                        Kafka Cluster                          │
 * │                                                               │
 * │   ZooKeeper / KRaft                                          │
 * │   (元数据管理、Leader 选举)                                   │
 * │                                                               │
 * │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
 * │   │    Broker 1     │  │    Broker 2     │  │    Broker 3     │
 * │   │                 │  │                 │  │                 │
 * │   │  Topic-A P0(L)  │  │  Topic-A P1(L)  │  │  Topic-A P2(L)  │
 * │   │  Topic-A P1(F)  │  │  Topic-A P2(F)  │  │  Topic-A P0(F)  │
 * │   │  Topic-B P0(F)  │  │  Topic-B P1(L)  │  │  Topic-B P2(F)  │
 * │   │                 │  │                 │  │                 │
 * │   └─────────────────┘  └─────────────────┘  └─────────────────┘
 * │         ↑                     ↑                     ↑          │
 * └─────────┼─────────────────────┼─────────────────────┼────────────┘
 *           │    生产者            │    生产者            │
 *           └─────────────────────┼─────────────────────┘
 *                                 │
 *                    ┌────────────┴────────────┐
 *                    │     Consumer Group A     │
 *                    │  (消费同一份数据，互不影响)│
 *                    └─────────────────────────┘
 */
```

### 1.2 RocketMQ：交易型 / 电商场景导向

```java
/**
 * RocketMQ 设计理念：
 * "可靠消息 + 事务" — 为互联网电商交易场景深度定制
 *
 * 核心思想：
 * - 消息可靠送达是首要目标
 * - 原生支持事务消息，保证本地事务与消息发送的原子性
 * - 原生支持延迟消息/定时消息，适用于超时取消等场景
 * - 队列模型天然支持顺序消息
 *
 * 架构特点：
 * - NameServer 做轻量级服务发现（无中心化，各节点独立）
 * - CommitLog 顺序写 + ConsumeQueue 索引（读写分离）
 * - 消息过滤在 Broker 端执行（Tag + SQL 过滤）
 * - 主从同步支持同步/异步模式
 *
 * 典型使用：
 * - 订单处理、支付流水
 * - 库存扣减、积分变动
 * - 短信/推送通知延迟投递
 * - 分布式事务最终一致性
 */
public class RocketMQDesign {}
```

```java
/**
 * RocketMQ 集群架构图：
 *
 *                        ┌──────────────┐
 *                        │  NameServer  │  ←─── 独立节点，不互相通信
 *                        │   (Broker    │        各自独立注册
 *                        │   注册发现)  │
 *                        └──────┬───────┘
 *                               │
 *          ┌────────────────────┼────────────────────┐
 *          │                    │                    │
 *    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐
 *    │ Broker-M  │◄──────►│ Broker-M  │◄──────►│ Broker-M  │
 *    │ (Master)  │SYNC/   │ (Master)  │SYNC/   │ (Master)  │
 *    └─────┬─────┘ASYNC   └─────┬─────┘ASYNC   └─────┬─────┘
 *          │                    │                    │
 *    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐
 *    │ Broker-S  │        │ Broker-S  │        │ Broker-S  │
 *    │ (Slave)   │        │ (Slave)   │        │ (Slave)   │
 *    └───────────┘        └───────────┘        └───────────┘
 *
 *         ↑ Producer                  ↑ Consumer
 *         └─────────── Pull 模式 ──────┘
 */
```

### 1.3 RabbitMQ：通用型 / 灵活路由导向

```java
/**
 * RabbitMQ 设计理念：
 * "Exchange 路由 + Queue 消费" — 追求路由灵活性和协议完善度
 *
 * 核心思想：
 * - 基于 AMQP 协议，概念完善（Exchange/Queue/Binding）
 * - Exchange 负责消息路由到 Queue，灵活多变
 * - 多协议支持：AMQP、STOMP、MQTT、HTTP
 * - 镜像队列保证高可用
 *
 * 架构特点：
 * - 无中心化元数据服务（Erlang Mnesia 数据库存储元数据）
 * - 消息在内存+磁盘双存储
 * - 支持多种 Exchange 类型（Direct/Fanout/Topic/Headers）
 * - 多租户设计（Virtual Host 隔离）
 *
 * 典型使用：
 * - 跨语言系统集成
 * - 复杂路由逻辑业务
 * - 低延迟即时通讯
 * - 任务队列异步处理
 */
public class RabbitMQDesign {}
```

```java
/**
 * RabbitMQ 架构图：
 *
 * ┌──────────────────────────────────────────────────────────────┐
 * │                         RabbitMQ Cluster                      │
 * │                     (Erlang Mnesia 元数据)                     │
 * │                                                               │
 * │   ┌──────────────────────────────────────────────────────┐   │
 * │   │                    Virtual Host /                   │   │
 * │   │                    Virtual Host /                   │   │
 * │   └──────────────────────────────────────────────────────┘   │
 * │                                                               │
 * │   Exchange A          Exchange B         Exchange C          │
 * │   (Direct)            (Topic)            (Fanout)            │
 * │       │                   │                   │              │
 * │   ┌───┴───┐           ┌───┴───┐           ┌───┴───┐          │
 * │   │Queue A │           │Queue B │           │Queue C│          │
 * │   └────────┘           └────────┘           └────────┘          │
 * │                                                               │
 * └──────────────────────────────────────────────────────────────┘
 *         ↑                         ↑                         ↑
 *      Producer                   Producer                  Producer
 */
```

---

## 📖 二、性能核心指标对比

### 2.1 吞吐量对比

```java
/**
 * 吞吐量对比（单集群 3 节点，标准配置）
 *
 * ┌──────────────────────────────────────────────────────────┐
 * │                    吞吐量对比                              │
 * │  120w ─┤                                                     │
 * │  100w ─┤  ★ Kafka                                         │
 * │   80w ─┤       ★★★ RocketMQ                              │
 * │   60w ─┤                                                    │
 * │   40w ─┤                                                    │
 * │   20w ─┤  ★ RabbitMQ                                       │
 * │    0  ─┴─────────────────────────────────────             │
 * │         Kafka    RocketMQ    RabbitMQ                      │
 * └──────────────────────────────────────────────────────────┘
 *
 * Kafka：100万～500万条/秒
 *   - 顺序写磁盘，零拷贝（sendfile）
 *   - 批量发送（batch）+ 批量压缩
 *   - 水平扩展分区，并行处理
 *   - 无太多协议开销
 *
 * RocketMQ：10万～100万条/秒
 *   - CommitLog 顺序写，读写分离
 *   - 消息过滤在 Broker 端，减少网络传输
 *   - 批量消费优化
 *   - 略低于 Kafka，主要差距在于功能优先于极致性能
 *
 * RabbitMQ：1万～10万条/秒
 *   - Erlang 运行时开销
 *   - 消息持久化到磁盘（非纯粹顺序写）
 *   - 内存+磁盘混合存储
 *   - 多协议支持带来额外开销
 *   - 单队列性能有上限，高吞吐需集群+分片
 *
 * 注意：以上为经验参考值，实际性能取决于：
 * - 消息大小（越大 Kafka 优势越明显）
 * - 硬件配置（磁盘 IO、网络带宽）
 * - 集群规模和分区数
 */
public class ThroughputComparison {}
```

### 2.2 延迟对比

```java
/**
 * 延迟对比（P99 分位）
 *
 * ┌──────────────────────────────────────────────────────────┐
 * │                    P99 延迟对比                            │
 * │   100ms ─┤                                                     │
 * │    50ms ─┤                                                     │
 * │    10ms ─┤                                                     │
 * │     5ms ─┤  ★ Kafka (3~10ms)                                │
 * │     2ms ─┤  ★ RocketMQ (2~10ms)                             │
 * │     1ms ─┤                                                     │
 * │   500μs ─┤                                                     │
 * │   100μs ─┤  ★ RabbitMQ (50~500μs)                          │
 * │    10μs ─┤  (延迟队列场景更优)                              │
 * │     0  ─┴─────────────────────────────────────             │
 * │         Kafka    RocketMQ    RabbitMQ                      │
 * └──────────────────────────────────────────────────────────┘
 *
 * RabbitMQ：微秒级（50μs ~ 500μs）
 *   - 内存队列，消息可直接在内存中转发
 *   - Erlang 运行时针对低延迟优化
 *   - 适合对延迟敏感的即时通讯场景
 *
 * Kafka：毫秒级（3ms ~ 10ms）
 *   - 批量处理增加延迟，但提高吞吐
 *   - 副本同步（ISR）增加一定延迟
 *   - 网络传输 + 磁盘写入（异步刷盘）
 *
 * RocketMQ：毫秒级（2ms ~ 10ms）
 *   - 介于两者之间
 *   - 同步刷盘模式下延迟增加
 *   - 消费 Pull 模式，可控性强
 *
 * 延迟优化技巧：
 * - Kafka：调小 batch.size / linger.ms（牺牲吞吐换延迟）
 * - RocketMQ：调整刷盘策略，使用异步刷盘
 * - RabbitMQ：Lazy Queue，将消息存磁盘减少内存压力
 */
public class LatencyComparison {}
```

---

## 📖 三、消息可靠性：ACK 机制深度对比

### 3.1 Kafka ACK 机制

```java
/**
 * Kafka 的 ACK 配置（Producer 端）
 *
 * acks = 0：发出去就不管了
 *   - 最高吞吐，最低可靠
 *   - 网络抖动直接丢消息
 *   - 适用：日志采集，允许少量丢失
 *
 * acks = 1（默认）：Leader 确认即可
 *   - Leader 写入成功即返回
 *   - Follower 还没同步完就挂了 → 消息丢失
 *   - 最常用配置
 *
 * acks = -1 / all：ISR 全员确认
 *   - 所有同步副本都写入成功才返回
 *   - 最可靠，但延迟高
 *   - 配置：replica.lag.time.max.ms 控制同步标准
 *
 * 代码示例：
 */
// Kafka Producer 可靠性配置
Properties props = new Properties();
props.put("bootstrap.servers", "kafka:9092");
props.put("key.serializer", "StringSerializer");
props.put("value.serializer", "StringSerializer");

// 最高可靠配置
props.put("acks", "all");              // 全部分区同步确认
props.put("retries", 3);              // 重试次数
props.put("enable.idempotence", true); // 幂等发送
props.put("max.in.flight.requests.per.connection", 5);

// Consumer 端：手动提交 offset
props.put("enable.auto.commit", "false");
props.put("auto.offset.reset", "earliest");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
```

```java
/**
 * Kafka 幂等性原理
 *
 * 问题：Producer 重试时，可能产生重复消息
 * 解决：幂等性（Idempotence）
 *
 * 原理：
 * - 每个 Producer 有一个唯一的 PID（Producer ID）
 * - 每个 Partition 维护一个 Sequence Number
 * - Broker 接收消息时判断：
 *   PID + Partition + Sequence Number → 唯一
 * - 重复消息直接忽略
 *
 * 限制：
 * - 同一 Producer 重启后 PID 变化，幂等失效
 * - 只能保证单 Producer 单 Partition 的幂等
 * - 跨 Producer 的幂等需要业务层处理
 */
public class KafkaIdempotent {}
```

### 3.2 RocketMQ ACK 机制

```java
/**
 * RocketMQ 的消息可靠性
 *
 * 1. Producer 端：
 *    - 同步发送：等待 Broker 确认
 *    - 异步发送：回调确认
 *    - 单向发送：不等待（可靠性最低）
 *
 * 2. Broker 端：
 *    - 同步刷盘（flushDiskType = SYNC_FLUSH）：写入磁盘才返回
 *    - 异步刷盘（ASYNC_FLUSH）：写入内存 PageCache，定时刷盘
 *    - 主从同步：
 *      - SYNC_MASTER：Master 和 Slave 都写入成功才返回（最可靠）
 *      - ASYNC_MASTER：Master 写入即返回（性能优先）
 *
 * 3. Consumer 端：
 *    - 手动 ACK：消费成功才确认
 *    - 自动 ACK：消息取出即确认（不可靠）
 */

// Broker 配置：最高可靠
brokerConfig.setFlushDiskType(SyncFlush);  // 同步刷盘
brokerConfig.setBrokerRole(SYNC_MASTER);   // 同步主从复制

// Consumer 端：手动 ACK
consumer.registerMessageListener(new MessageListenerConcurrently() {
    @Override
    public ConsumeConcurrentlyStatus consumeMessage(
            List<MessageExt> msgs,
            ConsumeConcurrentlyContext context) {
        for (MessageExt msg : msgs) {
            try {
                // 业务处理
                process(msg);
                return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
            } catch (Exception e) {
                // 失败，返回重试
                return ConsumeConcurrentlyStatus.RECONSUME_LATER;
            }
        }
        return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
    }
});
```

### 3.3 RabbitMQ ACK 机制

```java
/**
 * RabbitMQ 的 ACK 机制
 *
 * 消息确认模式：
 * 1. 自动确认（autoAck = true）
 *    - 消息投递给消费者后立即删除
 *    - 消费者挂掉 = 消息丢失
 *
 * 2. 手动确认（autoAck = false）
 *    - 消费者调用 basicAck 确认
 *    - 消费者调用 basicNack/basicReject 拒绝
 *    - 支持批量确认（basicAck multiple = true）
 *    - 支持 negative acknowledgment（basicNack requeue）
 *
 * 3. Publisher Confirms（发布确认）
 *    - Broker 确认收到消息
 *    - 支持事务模式（tx Select / tx Commit / tx Rollback）
 *    - 事务模式开销大（性能降低约 2-10 倍）
 *
 * 代码示例：
 */
Channel channel = connection.createChannel();
channel.queueDeclare("order_queue", true, false, false, null);
channel.basicQos(10); // 每次最多预取 10 条消息

// 手动 ACK 模式
channel.basicConsume("order_queue", false, new DefaultConsumer(channel) {
    @Override
    public void handleDelivery(String consumerTag, Envelope envelope,
                               AMQP.BasicProperties properties,
                               byte[] body) throws IOException {
        try {
            processOrder(body);
            // 手动确认，消息被标记删除
            channel.basicAck(envelope.getDeliveryTag(), false);
        } catch (Exception e) {
            // 拒绝消息，requeue=true 重新入队
            channel.basicNack(envelope.getDeliveryTag(), false, true);
        }
    }
});
```

```java
/**
 * 三种 MQ ACK 机制总结对比
 *
 * ┌─────────────────────────────────────────────────────────────────┐
 * │                   消息可靠性保证对比                              │
 * ├──────────────┬──────────────┬───────────────┬──────────────────┤
 * │    维度      │    Kafka     │   RocketMQ    │    RabbitMQ      │
 * ├──────────────┼──────────────┼───────────────┼──────────────────┤
 * │ Producer 确认 │ acks=0/1/all │ 同步发送      │ Publisher Confirm │
 * │ Broker 持久化 │ 异步刷盘(默认)│ 同步/异步刷盘 │ 内存+磁盘持久化   │
 * │ 主从复制     │ ISR 同步     │ SYNC/ASYNC    │ 镜像队列          │
 * │ Consumer 确认 │ 手动提交     │ 手动 ACK      │ 手动/自动 ACK     │
 * │ 消息重试     │ 无自动重试   │ 重试队列      │ requeue           │
 * │ 幂等性      │ 幂等 Producer │ 业务实现      │ 业务实现          │
 * └──────────────┴──────────────┴───────────────┴──────────────────┘
 *
 * 可靠性排序（高到低）：
 * RocketMQ(同步刷盘+同步主从) > Kafka(acks=all) > RabbitMQ(事务模式) > Kafka(acks=1)
 */
public class AckComparison {}
```

---

## 📖 四、消息顺序性深度解析

### 4.1 顺序性的三种级别

```java
/**
 * 消息顺序性分三个级别：
 *
 * 1. 生产顺序（Producer Order）
 *    - 消息发送的先后顺序
 *    - 大多数 MQ 能保证
 *
 * 2. 存储顺序（Storage Order）
 *    - 消息在 Broker 中的存储顺序
 *    - Kafka 单 Partition 内有序
 *    - RocketMQ 单队列内有序
 *    - RabbitMQ 单队列内有序
 *
 * 3. 消费顺序（Consumer Order）
 *    - 消费者处理消息的顺序
 *    - 最难保证，需要串行消费
 */
public class OrderLevels {}
```

### 4.2 Kafka 顺序性实现

```java
/**
 * Kafka 顺序性保证
 *
 * 单 Partition 内有序 → 跨 Partition 需要业务路由
 *
 * 场景：同一订单的消息必须有序处理
 * 解决方案：相同订单 ID → 同一 Partition
 */

// 自定义分区器
public class OrderPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        // 按订单 ID 哈希，保证同一订单到同一 Partition
        String orderId = (String) key;
        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        int numPartitions = partitions.size();
        return Math.abs(orderId.hashCode()) % numPartitions;
    }
}

// Producer 配置
props.put("partitioner.class", OrderPartitioner.class.getName());
props.put("key.serializer", "StringSerializer"); // 消息 key 就是 orderId

// 发送时指定 key
ProducerRecord<String, String> record =
    new ProducerRecord<>("order-topic", orderId, orderJson);

// 注意：
// - 如果 1 个 Partition 挂了，消息无法消费
// - 吞吐量受单 Partition 限制
// - 全局有序（1 个 Partition）性能最低
```

### 4.3 RocketMQ 顺序性实现

```java
/**
 * RocketMQ 顺序消息
 *
 * 提供两种顺序模式：
 * 1. 分区顺序（推荐）：同一队列内有序
 * 2. 全局顺序：整个 Topic 只有 1 个队列
 */

// 分区顺序消息
Message msg = new Message("OrderTopic",
    "TagA",
    orderId.getBytes(StandardCharsets.UTF_8));

// 使用 MessageQueueSelector 指定队列
producer.send(msg, new MessageQueueSelector() {
    @Override
    public MessageQueue select(List<MessageQueue> mqs,
                               Message msg,
                               Object arg) {
        // 按订单 ID 选择队列
        String orderId = (String) arg;
        int index = Math.abs(orderId.hashCode()) % mqs.size();
        return mqs.get(index);
    }
}, orderId); // arg 传入订单 ID

// Consumer 使用 MessageListenerOrderly 顺序消费
consumer.registerMessageListener(new MessageListenerOrderly() {
    @Override
    public ConsumeOrderlyStatus consumeMessage(
            List<MessageExt> msgs,
            ConsumeOrderlyContext context) {
        context.setAutoCommit(true); // 自动提交
        for (MessageExt msg : msgs) {
            processOrder(msg);
        }
        return ConsumeOrderlyStatus.SUCCESS;
    }
});

// RocketMQ 全局顺序配置
// Topic 创建时指定只有一个队列
mqAdminExt.createTopic("defaultCluster", "GlobalOrderTopic", 1, 8);
```

### 4.4 RabbitMQ 顺序性实现

```java
/**
 * RabbitMQ 顺序消息
 *
 * 单队列本身有序 → 扩展性差
 * 解决方案：按业务字段哈希 routing key
 */

// 单队列顺序消息
channel.queueDeclare("order_queue", false, false, false, null);
channel.basicConsume("order_queue", false, consumer);

// 多队列扩展场景：相同业务 ID → 同一队列
// 通过两个步骤实现：
// 1. Exchange 按 routing key 哈希路由到队列
// 2. 队列内部顺序消费

Map<String, Object> args = new HashMap<>();
args.put("x-match", "all");
args.put("order_id", orderId); // 过滤参数
channel.queueDeclare("order_queue", true, false, false, args);

// Consumer 顺序消费
DeliverCallback deliverCallback = (consumerTag, delivery) -> {
    String message = new String(delivery.getBody(), "UTF-8");
    processOrder(message);
    channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
};
```

```java
/**
 * 三种 MQ 顺序性对比总结
 *
 * ┌────────────────────────────────────────────────────────────┐
 * │              消息顺序性保证能力对比                          │
 * ├──────────────┬──────────────┬──────────────┬─────────────┤
 * │    特性      │    Kafka     │   RocketMQ   │  RabbitMQ   │
 * ├──────────────┼──────────────┼──────────────┼─────────────┤
 * │ 天然保证     │ 单 Partition │ 单队列内     │ 单队列内    │
 * │ 全局有序     │ 1 个 Partition│ 1 个队列    │ 1 个队列    │
 * │ 分区有序     │ ✅ Key 路由   │ ✅ 队列路由  │ ❌ 不支持   │
 * │ 消费并行度   │ 分区数决定   │ 队列数决定  │ 队列数决定  │
 * │ 扩展性      │ 好（多分区） │ 好（多队列）│ 一般        │
 * └──────────────┴──────────────┴──────────────┴─────────────┘
 *
 * 面试加分话术：
 * "顺序消息的本质是串行化消费，保证顺序一定会牺牲性能。
 *  实际项目中，我们通常采用'业务字段哈希分区+消费端串行处理'
 *  的方式，在保证业务顺序的同时兼顾扩展性。"
 */
public class OrderComparison {}
```

---

## 📖 五、消息回溯机制对比

### 5.1 Kafka 消息回溯

```java
/**
 * Kafka 消息回溯 — 基于 Offset 机制
 *
 * 核心概念：
 * - Consumer 可以从任意 Offset 开始消费
 * - 通过 offset 管理实现消息回溯
 * - 不支持"单条消息"的精确定位回溯
 *
 * 回溯场景：
 * 1. 消费者重启后继续消费
 * 2. 消费者 Group Rebalance 后重新分配分区
 * 3. 业务需要重新处理历史消息
 * 4. 消费失败重试
 */

// 方式一：seek 到指定位置重读
consumer.seek(new TopicPartition(topic, partition), offset);

// 方式二：从头开始消费（用于故障恢复或重处理）
consumer.seekToBeginning(
    Collections.singleton(new TopicPartition(topic, partition)));

// 方式三：从最新位置开始消费（跳过历史消息）
consumer.seekToEnd(
    Collections.singleton(new TopicPartition(topic, partition)));

// 方式四：基于时间回溯（时间戳定位 Offset）
Map<TopicPartition, Long> timestampsToSearch = new HashMap<>();
timestampsToSearch.put(new TopicPartition(topic, partition),
    System.currentTimeMillis() - 3600 * 1000); // 1小时前
Map<TopicPartition, OffsetAndTimestamp> result =
    consumer.offsetsForTimes(timestampsToSearch);
for (Map.Entry<TopicPartition, OffsetAndTimestamp> entry : result.entrySet()) {
    consumer.seek(entry.getKey(), entry.getValue().offset());
}

// 方式五：重置消费者组 Offset
// 命令行：
// kafka-consumer-groups.sh --bootstrap-server localhost:9092
//   --group my-group --reset-offsets
//   --topic my-topic --to-offset 1000 --execute

// Kafka Topic 消息保留策略
// retention.ms / retention.bytes
// 过期消息自动删除
// 最佳实践：处理完成后，手动提交 Offset
```

### 5.2 RocketMQ 消息回溯

```java
/**
 * RocketMQ 消息回溯 — 重试队列 + Offset 组合
 *
 * 核心机制：
 * - 消费失败 → 消息进入重试队列（%RETRY%TopicName）
 * - 重试队列有自己的 Offset 管理
 * - 支持延迟重试（可配置重试次数和间隔）
 *
 * 重试策略：
 * - 最大重试次数（默认 16 次）
 * - 指数退避：重试间隔递增
 * - 超过最大次数 → 进入死信队列（DLQ）
 */

// RocketMQ 消费失败返回重试
public ConsumeConcurrentlyStatus consumeMessage(
        List<MessageExt> msgs,
        ConsumeConcurrentlyContext context) {
    for (MessageExt msg : msgs) {
        try {
            process(msg);
            return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
        } catch (Exception e) {
            // 返回重试，系统自动将消息发到重试队列
            return ConsumeConcurrentlyStatus.RECONSUME_LATER;
        }
    }
    return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
}

// 死信队列（Dead Letter Queue）
// 超过最大重试次数的消息，进入死信队列
// 死信队列Topic：%DLQ%TopicName
// 死信队列特性：
// - 消息保留 3 天
// - 不会自动删除，需人工处理
// - 可通过管理后台查看和重新消费

// 手动重置消费位点
// RocketMQ Console 或命令：
// mqadmin resetOffsetByTime -g {consumerGroup}
//   -t {topic} -s {timestamp}

// 顺序消息的回溯：
// 使用 consumeSequenceContext 控制消费进度
// 失败时暂停队列消费，排查后再继续
```

### 5.3 RabbitMQ 消息回溯

```java
/**
 * RabbitMQ 消息回溯 — 基于消息 ID 和队列机制
 *
 * 核心机制：
 * - nack / reject + requeue 实现重试
 * - 设置 x-death 追踪消息死亡路径
 * - 死信交换机（DLX）处理失败消息
 * - 消息持久化支持重启后恢复
 */

// 拒绝消息并重新入队
channel.basicReject(deliveryTag, true); // requeue=true

// 拒绝消息不重入队 → 进入死信交换机
channel.basicReject(deliveryTag, false); // requeue=false

// 批量拒绝
channel.basicNack(deliveryTag, false, false); // multiple=false, requeue=false

// 死信交换机配置
Map<String, Object> args = new HashMap<>();
args.put("x-dead-letter-exchange", "dlx.exchange");
args.put("x-dead-letter-routing-key", "dlx.routing.key");
args.put("x-message-ttl", 60000); // 60秒后进入 DLX

channel.queueDeclare("order.queue", true, false, false, args);

// 死信队列处理
channel.exchangeDeclare("dlx.exchange", "direct", true);
channel.queueDeclare("dlx.queue", true, false, false, null);
channel.queueBind("dlx.queue", "dlx.exchange", "dlx.routing.key");

// 设置消费重试次数（通过消息头）
Map<String, Object> headers = new HashMap<>();
headers.put("x-retry-count", 0);
AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
    .headers(headers)
    .build();

channel.basicPublish("order.exchange", "order.routing",
    props, message.getBytes());

// x-death 信息示例（追踪消息投递历史）
// [
//   {
//     "time": "2024-01-01 12:00:00",
//     "exchange": "order.exchange",
//     "routing-keys": ["order.routing"],
//     "queue": "order.queue",
//     "reason": "rejected",
//     "count": 1
//   }
// ]
```

```java
/**
 * 三种 MQ 消息回溯对比
 *
 * ┌─────────────────────────────────────────────────────────────────┐
 * │                    消息回溯能力对比                               │
 * ├──────────────┬──────────────┬───────────────┬──────────────────┤
 * │    特性      │    Kafka     │   RocketMQ    │    RabbitMQ      │
 * ├──────────────┼──────────────┼───────────────┼──────────────────┤
 * │ 回溯单位     │ Offset       │ 消息粒度       │ 消息粒度          │
 * │ 回溯粒度     │ 粗粒度(Offset)│ 细粒度(单条)   │ 细粒度(单条)      │
 * │ 定时重试     │ 需外部实现    │ ✅ 原生支持    │ ✅ 原生支持       │
 * │ 重试次数控制 │ 无内置        │ ✅ 最大16次    │ ✅ 可配置         │
 * │ 死信队列     │ ❌ 无         │ ✅ DLQ         │ ✅ DLX           │
 * │ 消息过期     │ ✅ retention  │ ❌ 无内置      │ ✅ TTL           │
 * │ 业务补偿     │ 常用          │ 可选           │ 可选              │
 * └──────────────┴──────────────┴───────────────┴──────────────────┘
 *
 * 面试重点：
 * "Kafka 的回溯本质是 Offset 重置，适合故障恢复；
 *  RocketMQ/RabbitMQ 的回溯是消息重试，适合业务处理失败重试。
 *  生产环境中，如果业务对消息处理有强顺序要求，
 *  建议在消费端自己做幂等处理，而不是依赖 MQ 的回溯机制。"
 */
public class MessageBacktrackComparison {}
```

---

## 📖 六、适用场景深度分析

### 6.1 日志采集场景：Kafka 首选

```java
/**
 * 日志采集场景 — Kafka 最佳实践
 *
 * 场景特点：
 * - 海量数据（GB/TB 级/天）
 * - 允许少量丢失（不是 0 容忍）
 * - 吞吐量要求极高
 * - 多消费者订阅同一数据源
 * - 需要长期存储和回溯分析
 *
 * 为什么选 Kafka：
 * 1. 百万级吞吐量，轻松应对日志洪峰
 * 2. 顺序写磁盘，IO 效率高
 * 3. 消息持久化 + 分区副本，数据不丢失
 * 4. 消费者组机制，多个下游消费者独立消费
 * 5. 与 Hadoop/Spark/Flink 等大数据组件天然集成
 * 6. 消息保留时间长（可配置 7 天/30 天）
 *
 * 架构示例：
 *
 * ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
 * │   App Logs   │────▶│    Kafka     │────▶│   Logstash   │
 * │  (Filebeat)  │     │   Topic:     │     │  (处理/过滤)  │
 * │              │     │  app-logs    │     └──────┬───────┘
 * └──────────────┘     │  Partition:8 │            │
 *                      └──────────────┘     ┌──────┴───────┐
 *                                           │              │
 *                                    ┌──────┴────┐   ┌──────┴────┐
 *                                    │  Elastic  │   │  Hive/HDFS │
 *                                    │  Search   │   │  (离线分析) │
 *                                    └───────────┘   └────────────┘
 *
 * Kafka 配置优化：
 */
props.put("bootstrap.servers", "kafka:9092");
props.put("batch.size", 65536);        // 批次大小 64KB
props.put("linger.ms", 10);           // 批次等待时间
props.put("buffer.memory", 33554432); // 32MB 缓冲区
props.put("compression.type", "lz4"); // LZ4 压缩
props.put("acks", "1");               // 日志场景不需要太高可靠性
props.put("retries", 0);              // 减少重试
```

### 6.2 订单交易场景：RocketMQ 首选

```java
/**
 * 订单交易场景 — RocketMQ 最佳实践
 *
 * 场景特点：
 * - 交易数据，0 容错（不允许丢失）
 * - 需要事务消息保证一致性
 * - 需要延迟消息处理超时订单
 * - 需要顺序消息保证订单流程
 * - 国内电商生态完善，文档丰富
 *
 * 为什么选 RocketMQ：
 * 1. 原生事务消息，本地事务和消息发送原子性
 * 2. 原生延迟消息（18 个延迟级别）
 * 3. 队列模型，天然支持顺序消费
 * 4. 单队列有序 + 多队列并行，性能与顺序兼顾
 * 5. 阿里开源，国内生态好，中文文档全
 * 6. 消息过滤在 Broker 端，减少无效传输
 *
 * 订单超时取消场景：
 */
// 订单创建时，发送延迟消息（30分钟后检查）
Message delayMsg = new Message(
    "OrderDelayTopic",
    "order_timeout",
    orderId.getBytes(StandardCharsets.UTF_8)
);
// 延迟级别 15 = 30 分钟
delayMsg.setDelayTimeLevel(15);
producer.send(delayMsg);

// 延迟消息 Consumer
consumer.subscribe("OrderDelayTopic", "order_timeout");
consumer.registerMessageListener(new MessageListenerConcurrently() {
    @Override
    public ConsumeConcurrentlyStatus consumeMessage(
            List<MessageExt> msgs,
            ConsumeConcurrentlyContext context) {
        for (MessageExt msg : msgs) {
            String orderId = new String(msg.getBody());
            // 检查订单是否已支付
            if (!orderService.isPaid(orderId)) {
                orderService.cancel(orderId); // 超时取消
            }
        }
        return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
    }
});
```

### 6.3 即时通讯场景：RabbitMQ 首选

```java
/**
 * 即时通讯场景 — RabbitMQ 最佳实践
 *
 * 场景特点：
 * - 延迟要求极高（微秒级）
 * - 消息量中等（不像日志那么大）
 * - 路由逻辑复杂（一对一、一对多、广播）
 * - 需要灵活的消息路由
 * - 跨语言系统集成
 *
 * 为什么选 RabbitMQ：
 * 1. 微秒级延迟，实时性最强
 * 2. Exchange 路由模式丰富，灵活应对复杂路由
 * 3. 支持多协议（AMQP/MQTT），适合移动端 IM 场景
 * 4. 配置简单，学习曲线平缓
 * 5. 多租户隔离，适合 SaaS 平台
 * 6. 社区活跃，插件丰富
 *
 * 架构示例：即时通讯路由
 */
// RabbitMQ 消息路由实现
// 用户发消息给好友：Direct Exchange
// 用户发消息给群组：Fanout Exchange
// 用户订阅频道：Topic Exchange

// Direct 路由：一对一消息
channel.exchangeDeclare("im.direct", "direct", true);
channel.queueBind("user.1001.queue", "im.direct", "user.1001");
channel.queueBind("user.1002.queue", "im.direct", "user.1002");
// 发消息给指定用户
channel.basicPublish("im.direct", "user.1002", null,
    ("To:1002|" + message).getBytes());

// Fanout 路由：群组消息
channel.exchangeDeclare("im.group", "fanout", true);
channel.queueBind("group.888.queue", "im.group", "");
// 群内所有用户都能收到
channel.basicPublish("im.group", "", null,
    ("Group:888|" + message).getBytes());

// Topic 路由：订阅频道
channel.exchangeDeclare("im.channel", "topic", true);
channel.queueBind("tech.channel.queue", "im.channel", "channel.tech.*");
// 订阅技术频道的用户都能收到
channel.basicPublish("im.channel", "channel.tech.java", null,
    message.getBytes());
```

---

## 📖 七、延迟消息 / 定时消息对比

### 7.1 三种 MQ 延迟消息支持

```java
/**
 * 延迟消息 / 定时消息对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             延迟消息能力对比                                 │
 * ├──────────────┬──────────────┬──────────────┬────────────────┤
 * │    特性      │    Kafka     │   RocketMQ  │   RabbitMQ     │
 * ├──────────────┼──────────────┼──────────────┼────────────────┤
 * │ 原生支持     │ ❌ 不支持     │ ✅ 支持      │ ✅ 支持        │
 * │ 延迟精度     │ —            │ 秒级/分级    │ 毫秒级         │
 * │ 最大延迟     │ —            │ 2h 内分级   │ 无限制          │
 * │ 实现原理     │ 外部定时器    │ 延迟队列    │ 消息 TTL + DLX │
 * └──────────────┴──────────────┴──────────────┴────────────────┘
 */

/**
 * Kafka 延迟消息实现方案
 *
 * Kafka 本身不支持延迟消息，需要外部实现：
 * 1. 外部定时器 + 延迟投递
 * 2. 使用 Kafka Stream 状态机实现
 * 3. 依赖外部调度系统（如Scheduler）
 */

// 方案一：外部定时器实现延迟
// 使用 JDK ScheduledExecutorService 或 Quartz
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

// 模拟延迟消息发送
public void sendDelayMessage(String msg, long delayMs) {
    scheduler.schedule(() -> {
        producer.send(new ProducerRecord<>("delay-topic", msg));
    }, delayMs, TimeUnit.MILLISECONDS);
}

// 方案二：使用 Kafka 的时间轮算法（内部实现参考）
// Kafka 内部使用 TimingWheel 实现延迟操作（用于请求超时）
// 外部可参考实现：单消费者定时消费 + 延迟分级 Topic
// - Topic: delay-1s, delay-5s, delay-10s ...
// - 每个层级定时触发拉取
```

```java
/**
 * RocketMQ 延迟消息实现
 *
 * RocketMQ 原生支持延迟消息，但不支持任意时间
 * 支持 18 个延迟级别：
 * 1s, 5s, 10s, 30s, 1m, 2m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, 10m,
 * 20m, 30m, 1h, 2h
 */

// 发送延迟消息
Message msg = new Message("DelayTopic", "tag", key, value.getBytes());
// 设置延迟级别（15 = 30分钟，18 = 2小时）
msg.setDelayTimeLevel(15);
producer.send(msg);

// RocketMQ 延迟消息原理：
// 1. 消息先写入 CommitLog，不立即投递给消费者
// 2. 延迟时间到后，消息被重新投递到原 Topic 的消费队列
// 3. 消费者从队列中拉取消息
//
// 注意：所有延迟消息共用同一个 CommitLog
// 延迟消息的延迟时间必须与已存在的级别匹配
// 不支持自定义任意延迟时间
```

```java
/**
 * RabbitMQ 延迟消息实现
 *
 * RabbitMQ 支持两种方式：
 * 1. x-message-ttl + x-dead-letter-exchange（推荐）
 * 2. 延迟插件 rabbitmq_delayed_message_exchange
 *
 * 方式一：消息 TTL + 死信交换机
 */

// 创建延迟队列（消息 TTL 为 30 秒）
Map<String, Object> args = new HashMap<>();
args.put("x-message-ttl", 30000);  // 30秒后进入死信队列
args.put("x-dead-letter-exchange", "delay.exchange");
args.put("x-dead-letter-routing-key", "delay.done");

channel.queueDeclare("delay.queue", false, false, false, args);

// 死信交换机：接收延迟到期的消息
channel.exchangeDeclare("delay.exchange", "direct", true);
channel.queueDeclare("delay.done.queue", false, false, false, null);
channel.queueBind("delay.done.queue", "delay.exchange", "delay.done");

// 发送延迟消息（30秒后自动投递给 delay.done.queue）
channel.basicPublish("", "delay.queue", null, message.getBytes());

// 消费延迟消息
channel.basicConsume("delay.done.queue", true, (tag, delivery) -> {
    // 消息已延迟 30 秒送达
    processMessage(new String(delivery.getBody()));
});

// 方式二：延迟插件（支持任意时间延迟）
// 需要安装：rabbitmq_delayed_message_exchange 插件
// 支持毫秒级精度延迟

// 声明延迟交换机
Map<String, Object> delayedArgs = new HashMap<>();
delayedArgs.put("x-delayed-type", "direct");
channel.exchangeDeclare("my.delayed.exchange", "x-delayed-message",
    true, false, delayedArgs);

// 消息头指定延迟时间（毫秒）
Map<String, Object> headers = new HashMap<>();
headers.put("x-delay", 5000); // 5秒后投递
AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
    .headers(headers)
    .build();

channel.basicPublish("my.delayed.exchange", "routing.key",
    props, message.getBytes());
```

---

## 📖 八、事务消息支持对比

### 8.1 三种 MQ 事务消息支持

```java
/**
 * 事务消息对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             事务消息能力对比                                 │
 * ├──────────────┬──────────────┬──────────────┬────────────────┤
 * │    特性      │    Kafka     │   RocketMQ  │   RabbitMQ     │
 * ├──────────────┼──────────────┼──────────────┼────────────────┤
 * │ 原生事务消息 │ ❌ 不支持     │ ✅ 支持      │ ✅ 支持(插件)  │
 * │ 半消息机制   │ —            │ ✅           │ —              │
 * │ 本地事务回查 │ —            │ ✅           │ —              │
 * │ 消息回滚     │ —            │ ✅           │ ✅             │
 * │ 实现复杂度   │ —            │ 中等         │ 高             │
 * └──────────────┴──────────────┴──────────────┴────────────────┘
 */

/**
 * Kafka 事务消息
 *
 * Kafka 0.11+ 支持事务，但与 RocketMQ 事务消息设计不同
 * Kafka 事务：保证 Exactly-Once 语义（跨分区原子性）
 * 不支持本地事务回查
 */

// Kafka 事务配置
props.put("enable.idempotence", true);
props.put("transactional.id", "my-transactional-id"); // 事务 ID

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
producer.initTransactions();

try {
    producer.beginTransaction();

    // 发送消息到多个 Topic（原子性）
    producer.send(new ProducerRecord<>("topic-a", "key", "value1"));
    producer.send(new ProducerRecord<>("topic-b", "key", "value2"));

    // 业务处理（需自己实现与本地事务的绑定）
    orderService.createOrder(order);

    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();
}

// Kafka 事务与数据库事务结合
// 需要使用 2PC 或 saga 模式自己实现
// 常用方案：业务消息表 + 补偿任务
```

```java
/**
 * RocketMQ 事务消息（重点掌握）
 *
 * 设计：半消息（Half Message）+ 本地事务 + 回查
 *
 * 原理：
 * 1. 发送半消息到 Broker（此时消息对消费者不可见）
 * 2. 执行本地事务
 * 3. 提交或回滚半消息
 *    - COMMIT：消息对消费者可见
 *    - ROLLBACK：消息丢弃
 * 4. 如果 Broker 长时间没收到结果，定时回查事务状态
 */

// 事务消息完整示例
TransactionListener transactionListener = new TransactionListener() {
    // 执行本地事务
    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        try {
            // 1. 创建订单（本地事务）
            Order order = (Order) arg;
            orderService.createOrder(order);

            // 2. 扣减库存（可能失败）
            inventoryService.deduct(order.getProductId(), order.getQuantity());

            // 3. 扣减余额（可能失败）
            accountService.deduct(order.getUserId(), order.getAmount());

            // 本地事务全部成功，提交消息
            return LocalTransactionState.COMMIT_MESSAGE;

        } catch (InventoryException e) {
            // 库存不足，回滚消息
            return LocalTransactionState.ROLLBACK_MESSAGE;
        } catch (AccountException e) {
            // 余额不足，回滚消息
            return LocalTransactionState.ROLLBACK_MESSAGE;
        } catch (Exception e) {
            // 其他异常，不确定状态，等待回查
            return LocalTransactionState.UNKNOW;
        }
    }

    // Broker 定时回查事务状态
    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        String transactionId = msg.getTransactionId();
        String orderId = msg.getKeys();

        // 查询本地订单表，确认订单状态
        Order order = orderService.findById(orderId);
        if (order == null) {
            // 订单不存在，说明本地事务未执行
            return LocalTransactionState.ROLLBACK_MESSAGE;
        }

        if ("PAID".equals(order.getStatus()) || "CREATED".equals(order.getStatus())) {
            // 订单已创建/已支付，提交消息
            return LocalTransactionState.COMMIT_MESSAGE;
        }

        // 其他状态（处理中），继续等待
        return LocalTransactionState.UNKNOW;
    }
};

TransactionMQProducer producer = new TransactionMQProducer("producerGroup");
producer.setTransactionListener(transactionListener);
producer.setExecutorService(Executors.newFixedThreadPool(10));

// 发送事务消息
Message msg = new Message("OrderTopic",
    order.getOrderId().getBytes(StandardCharsets.UTF_8));
TransactionSendResult result = producer.sendMessageInTransaction(msg, order);
```

```java
/**
 * RabbitMQ 事务消息
 *
 * RabbitMQ 支持 AMQP 事务，但性能损耗严重（约 10 倍）
 * 通常不推荐使用，改用 消息确认 + 补偿机制
 */

// AMQP 事务模式（不推荐）
channel.txSelect(); // 开启事务
try {
    channel.basicPublish("exchange", "routing.key",
        MessageProperties.PERSISTENT, message.getBytes());
    channel.basicAck(deliveryTag, false);
    channel.txCommit(); // 提交
} catch (Exception e) {
    channel.txRollback(); // 回滚
}

// 推荐方案：消息确认 + 业务补偿
// 1. Publisher 确认（Publisher Confirms）
// 2. 消费者手动 ACK
// 3. 业务幂等性处理
// 4. 定时任务补偿未确认消息
```

---

## 📖 九、消费模式对比

### 9.1 Push vs Pull 模式

```java
/**
 * 消费模式对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             消费模式对比                                     │
 * ├──────────────┬──────────────┬──────────────┬────────────────┤
 * │    特性      │    Kafka     │   RocketMQ  │   RabbitMQ     │
 * ├──────────────┼──────────────┼──────────────┼────────────────┤
 * │ 主动权       │ Consumer Pull│ Broker Push │ Broker Push   │
 * │ 实时性       │ 轮询控制      │ 高           │ 高             │
 * │ 消费速率     │ Consumer 控制 │ Broker 控制 │ Broker 控制    │
 * │ 积压控制     │ Consumer 自主│ 可能丢失     │ 可控            │
 * │ 实现复杂度   │ 低           │ 中           │ 中             │
 * └──────────────┴──────────────┴──────────────┴────────────────┘
 */

/**
 * Kafka：Pull 模式（Consumer 主动拉取）
 *
 * 优点：
 * - Consumer 可控消费速率（积压时主动拉慢）
 * - 批量拉取，提高吞吐量
 * - 消费逻辑简单，不依赖 Broker 状态
 *
 * 缺点：
 * - 有一定延迟（轮询间隔）
 * - 可能产生无效轮询（无消息时）
 */

// Kafka Consumer Pull 模式
KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("my-topic"));

while (true) {
    // 拉取消息，100ms 超时
    ConsumerRecords<String, String> records =
        consumer.poll(Duration.ofMillis(100));

    for (ConsumerRecord<String, String> record : records) {
        process(record);
    }

    // 手动提交 offset
    consumer.commitSync();
}
```

```java
/**
 * RocketMQ：Push 模式（实际底层是 Pull）
 *
 * RocketMQ 的 Push 是"伪推送"：
 * - Broker 端长轮询（Long Polling）
 * - 消费者注册监听器，消息到来时自动触发
 * - 实现低延迟的同时保持可控性
 */

// RocketMQ Push 模式（实际内部是 Pull）
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("CID_EXAMPLE");
consumer.subscribe("TopicTest", "*");

// 消息监听器
consumer.registerMessageListener(new MessageListenerConcurrently() {
    @Override
    public ConsumeConcurrentlyStatus consumeMessage(
            List<MessageExt> msgs,
            ConsumeConcurrentlyContext context) {
        for (MessageExt msg : msgs) {
            System.out.println(new String(msg.getBody()));
        }
        // 返回成功或重试
        return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
    }
});

consumer.start();

// RocketMQ 也支持真正的 Pull 模式
DefaultMQPullConsumer pullConsumer = new DefaultMQPullConsumer("CID_EXAMPLE");
pullConsumer.start();

// 手动拉取消息
Set<MessageQueue> queues = fetchMessageQueues("TopicTest");
for (MessageQueue queue : queues) {
    SingleMessageListenerConsuming pullConsumer.pullBlockIfNotFound(
        queue, subExpression, offset, maxMsgNums);
}
```

```java
/**
 * RabbitMQ：Push 模式（Broker 主动推送）
 *
 * 通过 basic.qos 控制推送速率
 * 预取（prefetch）机制避免消费者过载
 */

// RabbitMQ Push 模式
channel.basicQos(10); // 最多预取 10 条消息

DeliverCallback deliverCallback = (tag, delivery) -> {
    try {
        processMessage(new String(delivery.getBody(), "UTF-8"));
        channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
    } catch (Exception e) {
        // 消费失败，拒绝并重新入队
        channel.basicNack(delivery.getEnvelope().getDeliveryTag(),
            false, true);
    }
};

channel.basicConsume("my.queue", false, deliverCallback, cancelCallback);

// basic.qos 参数详解
// prefetchCount = 0：不限制（不推荐）
// prefetchCount = 1：严格顺序消费
// prefetchCount = N：批量并行消费，N 越大吞吐越高
```

---

## 📖 十、集群架构差异

### 10.1 元数据管理架构对比

```java
/**
 * 元数据管理架构对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             元数据管理对比                                     │
 * ├──────────────┬──────────────┬──────────────┬──────────────────┤
 * │    组件      │    Kafka     │   RocketMQ  │   RabbitMQ       │
 * ├──────────────┼──────────────┼──────────────┼──────────────────┤
 * │ 元数据服务   │ ZooKeeper /  │ NameServer   │ Erlang Mnesia   │
 * │              │ KRaft        │ (无中心化)    │ (内置)           │
 * │ Leader 选举  │ ZK Controller│ NameServer   │ 无主从           │
 * │ 服务发现     │ ZK 订阅      │ HTTP 轮询    │ 客户端直连       │
 * │ 依赖外部组件 │ 是/否（KRaft)│ 否           │ 否               │
 * └──────────────┴──────────────┴──────────────┴──────────────────┘
 */

/**
 * Kafka 元数据管理
 *
 * 旧版（依赖 Zookeeper）：
 * - Topic 分区信息、Leader 信息存储在 ZK
 * - Broker 注册到 ZK
 * - Consumer 通过 ZK 感知分区变化
 * - 问题：ZK 压力大，依赖重
 *
 * 新版（KRaft 模式）：
 * - 元数据存储在 Kafka 自身（Raft 协议）
 * - 无需外部 ZK 依赖
 * - 架构更简单
 */

// KRaft 模式配置
// server.properties
// process.roles=broker,controller
// node.id=1
// controller.quorum.voters=1@localhost:9093
// listeners=PLAINTEXT://:9092,CONTROLLER://:9093
```

```java
/**
 * RocketMQ 元数据管理
 *
 * NameServer 特点：
 * - 无中心化，各节点独立运行
 * - Broker 启动时向所有 NameServer 注册
 * - Consumer/Producer 轮询 NameServer 获取路由信息
 * - 各 NameServer 数据最终一致（通过心跳同步）
 *
 * 优点：架构简单，无单点故障
 * 缺点：可能有短暂路由信息不一致
 */

// NameServer 配置示例
namesrvAddr=192.168.1.101:9876;192.168.1.102:9876;192.168.1.103:9876

// Producer 获取路由
DefaultMQProducer producer = new DefaultMQProducer("ProducerGroup");
producer.setNamesrvAddr("192.168.1.101:9876;192.168.1.102:9876");
producer.start();

// Producer 内部轮询 NameServer 获取 Topic 路由
// 路由信息缓存本地，定时更新
```

```java
/**
 * RabbitMQ 元数据管理
 *
 * Erlang Mnesia 特点：
 * - 内置分布式数据库
 * - 存储 Queue 定义、Exchange 绑定、用户权限
 * - 集群内自动同步
 * - 无需外部依赖
 *
 * 镜像队列（Mirroring）：
 * - 队列主节点在某个 Broker
 * - 副本自动同步到其他 Broker
 * - 主节点挂了，从节点自动提升
 */

// RabbitMQ 集群配置
// 节点 1
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl join_cluster --ram rabbit@node2
rabbitmqctl start_app

// 镜像队列策略
// ha-mode: all（所有节点镜像）
// ha-mode: exactly（指定数量镜像）
// ha-mode: nodes（指定节点镜像）
rabbitmqctl set_policy ha-all "^order\." '{"ha-mode":"all"}'
```

### 10.2 分区 / 队列分配策略

```java
/**
 * 分区分配策略对比
 *
 * Kafka：
 * - RangeAssignor：按范围分配
 * - RoundRobinAssignor：轮询分配
 * - StickyAssignor：粘性分配（尽量保持原有分配）
 * - CooperativeStickyAssignor：支持协作者的粘性分配
 *
 * RocketMQ：
 * - 平均分配（AllocateMessageQueueAveragely）
 * - 一致性哈希（AllocateMessageQueueConsistentHash）
 * - 配置指定
 *
 * RabbitMQ：
 * - 队列固定，消费者竞争
 * - 镜像队列主节点接收消息
 */

/**
 * Kafka Rebalance 机制
 *
 * 问题：消费者变化时，触发全局 Rebalance
 * 所有消费者暂停消费（Stop The World）
 *
 * 解决方案：
 * 1. 合理规划分区数（不频繁变更）
 * 2. 使用静态成员（Static Membership）
 * 3. 使用 Cooperative Rebalance（增量 rebalance）
 */
props.put("group.instance.id", "consumer-1"); // 静态成员 ID
props.put("partition.assignment.strategy",
    "cooperative-sticky"); // 协作者粘性分配
```

---

## 📖 十一、运维和生态对比

### 11.1 运维复杂度

```java
/**
 * 运维复杂度对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             运维复杂度对比                                     │
 * ├──────────────┬──────────────┬──────────────┬────────────────┤
 * │    维度      │    Kafka     │   RocketMQ   │   RabbitMQ    │
 * ├──────────────┼──────────────┼──────────────┼────────────────┤
 * │ 外部依赖     │ ZK（可选KRaft)│ 无           │ 无             │
 * │ 部署难度     │ 中等          │ 简单         │ 简单           │
 * │ 配置复杂度   │ 高            │ 中           │ 低             │
 * │ 监控成熟度   │ 高（丰富工具)│ 中（控制台) │ 高（丰富插件)│
 * │ 扩缩容       │ 分区可动态调整│ 队列可动态调整│ 队列需重建    │
 * │ 版本升级     │ 滚动升级      │ 滚动升级     │ 滚动升级       │
 * └──────────────┴──────────────┴──────────────┴────────────────┘
 */

/**
 * Kafka 运维要点
 *
 * 1. Topic 规划：
 *    - 分区数 = 消费者数（上浮 20%）
 *    - 副本数 = 3（生产环境）
 *    - retention 根据业务设置
 *
 * 2. 监控指标：
 *    - UnderReplicatedPartitions（ISR 副本缺失）
 *    - Consumer Lag（消费延迟）
 *    - Producer Error Rate
 *
 * 3. 常用命令：
 */
// 创建 Topic
kafka-topics.sh --create --topic my-topic \
  --partitions 12 --replication-factor 3 \
  --bootstrap-server localhost:9092

// 查看消费者组 Lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --describe

// 重置 Offset
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --reset-offsets \
  --topic my-topic --to-earliest --execute
```

```java
/**
 * RocketMQ 运维要点
 *
 * 1. 集群模式：
 *    - 单 Master（测试）
 *    - 多 Master（高可用）
 *    - 多 Master 多 Slave（同步双写，最可靠）
 *
 * 2. 监控指标：
 *    - JVM 指标（堆内存、GC）
 *    - 消息堆积数量
 *    - 消费延迟
 *
 * 3. 常用命令：
 */
// 创建 Topic
mqadmin updateTopic -n localhost:9876 \
  -c DefaultCluster -t my-topic -r 8 -w 8

// 查看消费者组
mqadmin consumerProgress -n localhost:9876 -g my-consumer-group

// 查看消息堆积
mqadmin statsAll -n localhost:9876
```

```java
/**
 * RabbitMQ 运维要点
 *
 * 1. 内存和磁盘监控：
 *    - 内存使用超过阈值触发流控
 *    - 磁盘空间不足拒绝消息
 *
 * 2. 监控指标：
 *    - 队列消息数
 *    - 消费者数量
 *    - 未确认消息数
 *
 * 3. 常用命令：
*/
// 查看队列状态
rabbitmqctl list_queues name messages consumers

// 查看交换机绑定
rabbitmqctl list_bindings

// 添加用户和权限
rabbitmqctl add_user admin password
rabbitmqctl set_permissions admin ".*" ".*" ".*"
rabbitmqctl set_topic_permissions admin ".*" ".*" ".*"
```

### 11.2 生态和社区

```java
/**
 * 生态和社区对比
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │             生态和社区对比                                     │
 * ├──────────────┬──────────────┬──────────────┬────────────────┤
 * │    维度      │    Kafka     │   RocketMQ   │   RabbitMQ    │
 * ├──────────────┼──────────────┼──────────────┼────────────────┤
 * │ 起源公司     │ LinkedIn     │ Alibaba      │ VMware/Pivotal│
 * │ 语言         │ Scala/Java   │ Java         │ Erlang        │
 * │ 社区活跃度   │ 极高          │ 高（国内)    │ 高（国际)     │
 * │ 大数据生态   │ 深度集成      │ 一般         │ 一般          │
 * │ Java 生态    │ 好           │ 最好          │ 好            │
 * │ 多语言客户端 │ 丰富          │ 一般          │ 丰富          │
 * │ 企业级支持   │ Confluent     │ 阿里云        │ VMware        │
 * └──────────────┴──────────────┴──────────────┴────────────────┘
 */

/**
 * 选型建议总结
 *
 * ┌─────────────────────────────────────────────────────────────┐
 * │                    MQ 选型决策树                               │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 1. 日志采集 / 大数据 / 实时流处理？
 *    → Kafka（首选）
 *    → 理由：吞吐量最高，与 Flink/Spark 集成完善
 *
 * 2. 电商交易 / 订单系统 / 需要事务消息？
 *    → RocketMQ（首选）
 *    → 理由：原生事务消息，延迟消息支持完善
 *
 * 3. 低延迟 / 即时通讯 / 复杂路由？
 *    → RabbitMQ（首选）
 *    → 理由：微秒级延迟，Exchange 路由灵活
 *
 * 4. 不确定 / 通用业务消息？
 *    → 国内业务 → RocketMQ（生态好，文档全）
 *    → 国际化业务 → Kafka 或 RabbitMQ
 *
 * 5. 超高吞吐 / 海量数据？
 *    → Kafka（首选）
 *    → 理由：百万级吞吐，水平扩展能力强
 */
```

---

## 📖 十二、高频面试题

### Q1: 消息队列如何保证不丢失消息？

**答：**
从生产者、Broker、消费者三个环节保证：

**生产者端：**
```java
// Kafka
props.put("acks", "all");
props.put("retries", 3);
props.put("enable.idempotence", true);

// RocketMQ
producer.send(msg, new SendCallback() {
    @Override
    public void onSuccess(SendResult result) {
        // 发送成功
    }
    @Override
    public void onException(Throwable e) {
        // 发送失败，补偿重试
    }
});
```

**Broker 端：**
- Kafka：副本因子 ≥ 3，ISR 配置合理
- RocketMQ：同步刷盘 + 同步主从
- RabbitMQ：持久化队列 + 镜像队列

**消费者端：**
- 手动提交 ACK，处理成功后再提交
- 消费逻辑幂等处理

---

### Q2: Kafka 为什么这么快？

**答：**
1. **顺序写磁盘**：消息追加到文件末尾，利用磁盘顺序 IO
2. **零拷贝**：使用 sendfile 系统调用，避免内核空间与用户空间数据拷贝
3. **批量处理**：消息批量发送（batch）和批量压缩（LZ4/Snappy）
4. **分区并行**：Topic 分区支持并行生产和消费
5. **无锁设计**：利用 PageCache 缓存，避免 Java GC 开销
6. **高效序列化**：使用轻量级序列化（Protobuf/Avro）

---

### Q3: Kafka 的 ISR 机制是什么？

**答：**
ISR（In-Sync Replicas，同步副本集合）：

**概念：**
- 与 Leader 保持同步的 Follower 副本集合
- 同步标准：`replica.lag.time.max.ms` 内追上 Leader

**作用：**
- 控制消息可靠性：只有 ISR 内的副本才参与 Leader 选举
- `acks=all` 时，消息需要写入所有 ISR 副本才返回成功

**问题场景：**
- ISR 为空：所有 Follower 都落后，Broker 可能 hang 住
- ISR 收缩：Follower 故障或落后，从 ISR 中移除
- ISR 扩展：Follower 追上后，重新加入 ISR

---

### Q4: RocketMQ 事务消息的原理是什么？

**答：**
```
┌─────────┐   1.发送半消息    ┌─────────┐
│Producer │ ────────────────▶│ Broker  │
└─────────┘                   └────┬────┘
     │                            │  半消息落盘（对 Consumer 不可见）
     │  2.执行本地事务            │
     ▼                            │
┌─────────┐                       │
│ Database│                       │
└────┬────┘                       │
     │  3.提交/回滚                │
     ▼                            │
┌─────────┐                   ┌───▼────┐
│Producer │ ◀── 4.确认结果 ─── │ Broker │
└─────────┘                   └────────┘
                                   │
                    5.定时回查（如无结果）
                    ┌──────────────┘
                    ▼
              ┌─────────┐
              │Producer │ → 检查本地事务状态
              └─────────┘
```

**四步流程：**
1. 发送半消息（Half Message），消息对消费者不可见
2. 执行本地事务
3. 提交或回滚半消息
4. 若 Broker 未收到结果，定时回查 Producer 确认状态

---

### Q5: 消息积压如何处理？

**答：**
```
消息积压 → 分析原因 → 针对性处理
     │
     ├─ 生产过快 ────────────────── 限流 / 扩容 Producer
     │
     ├─ 消费过慢 ────────────────── 扩容 Consumer
     │     │
     │     ├─ 代码问题 ──────────── 优化消费逻辑
     │     ├─ 数据库瓶颈 ────────── 读写分离 / 索引优化
     │     └─ 网络问题 ──────────── 检查网络带宽
     │
     ├─ Consumer 挂掉 ────────────── 重启 / 扩容
     │
     └─ Partition 不足 ───────────── 增加分区数
```

**紧急处理步骤：**
1. 临时扩容消费者（增加分区数 + 启动更多 Consumer）
2. 开启多个 Consumer 实例并行消费
3. 消费日志分析，定位消费慢的原因
4. 消息过期处理（过期消息直接丢弃）
5. 死信队列处理（超长积压的死信消息单独处理）

---

### Q6: 如何保证消息顺序？

**答：**
```
顺序保证的三个层次：
│
├─ 1. 生产有序：Producer 串行发送
│
├─ 2. 存储有序：单 Partition / 单队列内有序
│
└─ 3. 消费有序：Consumer 串行消费
```

**Kafka 保证顺序：**
```java
// 方案：相同 Key → 相同 Partition → 串行消费
ProducerRecord<String, String> record =
    new ProducerRecord<>("order-topic", orderId, message);
// orderId 相同的消息，一定在同一个 Partition
// 单 Partition 内消息有序
// Consumer 端顺序消费该 Partition
```

**RocketMQ 保证顺序：**
```java
// 方案：MessageQueueSelector 保证同一订单到同一队列
producer.send(msg, new MessageQueueSelector() {
    @Override
    public MessageQueue select(List<MessageQueue> mqs,
                              Message msg, Object arg) {
        return mqs.get(Math.abs(orderId.hashCode()) % mqs.size());
    }
}, orderId);

// Consumer 使用 MessageListenerOrderly 顺序消费
```

**面试加分话术：**
> "顺序消息的本质是串行化，一定会影响吞吐量。实际项目中，如果业务允许，我们更推荐'最终一致 + 幂等处理'的方案，而不是强依赖 MQ 的顺序保证。"

---

**⭐ 总结：消息队列选型的核心是场景匹配**
- **Kafka**：大数据、日志、实时流 → 吞吐量优先
- **RocketMQ**：电商交易、事务、延迟消息 → 可靠性优先
- **RabbitMQ**：即时通讯、复杂路由、低延迟 → 灵活性优先

---

*文档更新于 2024 | 持续更新中*
