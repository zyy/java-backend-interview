# RocketMQ 核心原理

> 阿里巴巴开源的分布式消息中间件

## 🎯 面试重点

- RocketMQ 的架构和核心概念
- 顺序消息、事务消息
- 消息可靠性保证
- 与 Kafka 的对比

## 📖 RocketMQ 架构

### 核心组件

```java
/**
 * RocketMQ 核心组件：
 * 
 * NameServer：命名服务
 * - 轻量级注册中心
 * - 负责 Broker 管理和服务发现
 * - 每个 NameServer 独立，不相互通信
 * 
 * Broker：消息服务器
 * - 负责消息存储和转发
 * - 支持主从部署
 * - 分为 Master 和 Slave
 * 
 * Producer：消息生产者
 * - 发送消息到 Broker
 * - 支持同步/异步/单向发送
 * 
 * Consumer：消息消费者
 * - 从 Broker 拉取消息
 * - 支持Push和Pull模式
 */
public class RocketMQComponents {
    /*
     * 架构图：
     * 
     *   ┌──────────────┐
     *   │   Producer   │
     *   └──────┬───────┘
     *          │
     *          ↓
     *   ┌──────────────┐
     *   │  NameServer  │ ←── Broker 注册/发现
     *   └──────┬───────┘
     *          │
     *          ↓
     *   ┌──────────────┐     ┌──────────────┐
     *   │ Broker(M)    │─────│ Broker(S)    │
     *   └──────────────┘     └──────────────┘
     *          ↑
     *   ┌──────┴───────┐
     *   │   Consumer   │
     *   └──────────────┘
     */
}
```

### 消息存储

```java
/**
 * RocketMQ 消息存储
 * 
 * CommitLog：存储消息主体
 * - 每个文件 1GB
 * - 顺序写入
 * - 消息持久化
 * 
 * ConsumeQueue：消费队列
 * - 索引文件
 * - 消息在 CommitLog 的物理位置
 * 
 * 优点：
 * - 消息均匀分布到多个 CommitLog
 * - 顺序写入提高 IO 性能
 */
public class MessageStorage {
    /*
     * 存储结构：
     * 
     * CommitLog/
     *   ├── 0000000000.cq   (1GB)
     *   ├── 0000000100.cq
     *   └── ...
     * 
     * ConsumeQueue/
     *   └── TopicName/
     *       └── QueueId/
     *           └── 0000000000.cq
     */
}
```

## 📖 消息类型

### 普通消息

```java
/**
 * 普通消息（OneWay/同步/异步）
 */
public class NormalMessage {
    // 同步发送
    /*
     * SendResult result = producer.send(msg);
     * // 等待发送结果
     */
    
    // 异步发送
    /*
     * producer.send(msg, new SendCallback() {
     *     @Override
     *     public void onSuccess(SendResult sendResult) {}
     *     @Override
     *     public void onException(Throwable e) {}
     * });
     */
    
    // 单向发送
    /*
     * producer.sendOneway(msg);
     * // 不等待结果
     */
}
```

### 顺序消息

```java
/**
 * 顺序消息
 * 
 * 全局顺序：一个 Topic 一个队列
 * 分区顺序：同一分区有序
 */
public class OrderedMessage {
    // 分区（队列）顺序消息
    /*
     * // Producer 设置顺序
     * Message msg = new Message("OrderTopic", "Order_" + orderId, order.getContent().getBytes());
     * // 使用 MessageQueueSelector 保证同一订单消息到同一队列
     * SendResult result = producer.send(msg, new MessageQueueSelector() {
     *     @Override
     *     public MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {
     *         String orderId = (String) arg;
     *         int hash = orderId.hashCode();
     *         return mqs.get(Math.abs(hash) % mqs.size());
     *     }
     * }, orderId);
     * 
     * // Consumer 按队列顺序消费
     * consumer.registerMessageListener(new MessageListenerOrderly() {
     *     @Override
     *     public ConsumeOrderlyStatus consumeMessage(List<MessageExt> msgs, ConsumeOrderlyContext context) {
     *         context.setAutoCommit(true);
     *         // 处理消息
     *         return ConsumeOrderlyStatus.SUCCESS;
     *     }
     * });
     */
}
```

### 事务消息

```java
/**
 * 事务消息
 * 
 * 阶段：
 * 1. 发送半消息（Prepare）
 * 2. 执行本地事务
 * 3. 提交或回滚
 */
public class TransactionMessage {
    // 实现
    /*
     * TransactionListener transactionListener = new TransactionListener() {
     *     // 执行本地事务
     *     @Override
     *     public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
     *         try {
     *             orderService.createOrder((Order) arg);
     *             return LocalTransactionState.COMMIT_MESSAGE;
     *         } catch (Exception e) {
     *             return LocalTransactionState.ROLLBACK_MESSAGE;
     *         }
     *     }
     *     
     *     // 检查本地事务状态
     *     @Override
     *     public LocalTransactionState checkLocalTransaction(MessageExt msg) {
     *         // 查询订单是否创建成功
     *         if (orderService.exists(msg.getKeys())) {
     *             return LocalTransactionState.COMMIT_MESSAGE;
     *         }
     *         return LocalTransactionState.UNKNOW;
     *     }
     * };
     * 
     * TransactionMQProducer producer = new TransactionMQProducer("producerGroup");
     * producer.setTransactionListener(transactionListener);
     * 
     * // 发送事务消息
     * Message msg = new Message("OrderTopic", order.toString().getBytes());
     * TransactionSendResult result = producer.sendMessageInTransaction(msg, order);
     */
    
    // 注意
    /*
     * 事务消息限制：
     * - 不支持延迟消息和批量消息
     * - 一个事务消息就是一个独立的事务
     * - 半消息发送成功后，本地事务必须执行完成
     */
}
```

### 延迟消息

```java
/**
 * 延迟消息
 * 
 * RocketMQ 支持特定延迟级别：
 * 1s, 5s, 10s, 30s, 1m, 2m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, 10m, 20m, 30m, 1h, 2h
 */
public class DelayMessage {
    // 示例：订单超时取消
    /*
     * Message msg = new Message("DelayTopic", "OrderTimeout", 
     *     orderId.getBytes());
     * 
     * // 设置延迟级别（这里设置 30 分钟）
     * msg.setDelayTimeLevel(15);
     * 
     * producer.send(msg);
     * 
     * // Consumer 消费延迟消息
     * consumer.subscribe("DelayTopic", "*");
     */
}
```

## 📖 消息可靠性

### 消息丢失场景和应对

```java
/**
 * 消息可靠性保证
 * 
 * 1. 生产端可靠投递
 * - 同步发送 + 重试
 * - 事务消息
 * 
 * 2. Broker 端可靠存储
 * - 同步刷盘（flushDiskType = SYNC_FLUSH）
 * - 主从复制（Broker 集群）
 * 
 * 3. 消费端可靠消费
 * - 手动 ACK
 * - 消费重试队列
 */
public class MessageReliability {
    // Broker 配置
    /*
     * brokerConfig.setFlushDiskType(SyncFlush);  // 同步刷盘
     * brokerConfig.setBrokerRole(SYNC_MASTER);   // 同步主从
     */
    
    // Consumer 配置
    /*
     * consumer.registerMessageListener(new MessageListenerConcurrently() {
     *     @Override
     *     public ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> msgs, 
     *                                                      ConsumeConcurrentlyContext context) {
     *         try {
     *             // 处理消息
     *             return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
     *         } catch (Exception e) {
     *             // 处理失败，发送到重试队列
     *             return ConsumeConcurrentlyStatus.RECONSUME_LATER;
     *         }
     *     }
     * });
     */
}
```

### 消息重复消费

```java
/**
 * 消息重复原因：
 * 1. 生产端重试（超时未收到 ACK）
 * 2. 消费端重试（消费失败）
 * 3. Consumer 恢复消费（Rebalance）
 * 
 * 解决方案：
 * - 幂等性处理
 */
public class MessageDuplicate {
    // 幂等实现方式
    /*
     * 1. 数据库唯一键
     *    - 写入表时使用唯一主键
     *    - INSERT IGNORE / ON DUPLICATE KEY UPDATE
     * 
     * 2. 分布式锁
     *    - Redis SETNX
     *    - 缺点：增加系统复杂度
     * 
     * 3. 消息幂等号
     *    - 消息携带唯一 ID
     *    - 消费前检查是否已处理
     * 
     * 示例：
     * String msgId = msg.getMsgId();
     * if (redis.setIfAbsent(msgId, "1")) {
     *     // 处理消息
     * } else {
     *     // 已处理，跳过
     * }
     */
}
```

## 📖 RocketMQ vs Kafka

```java
/**
 * 对比
 */
public class CompareWithKafka {
    /*
     * | 特性         | RocketMQ         | Kafka           |
     * |--------------|------------------|-----------------|
     * | 架构         | NameServer + Broker | Zookeeper + Broker |
     * | 可靠性       | 同步刷盘 + 主从   | 异步刷盘 + 分区   |
     * | 顺序消息     | 支持（队列级）   | 支持（分区级）   |
     * | 事务消息     | 支持             | 不支持           |
     * | 延迟消息     | 支持             | 不支持           |
     * | 消息堆积     | 强               | 强               |
     * | 吞吐量       | 万级             | 十万级           |
     * | 生态         | 阿里开源         | 大数据生态       |
     * 
     * 选型建议：
     * - 事务场景、延迟消息 → RocketMQ
     * - 大数据、日志采集 → Kafka
     * - 普通业务消息 → 两者都可
     */
}
```

## 📖 面试真题

### Q1: RocketMQ 事务消息原理？

**答：**
1. 发送半消息到 Broker（预提交）
2. 执行本地事务
3. 根据结果提交或回滚
4. 如果没有结果，Broker 定时回查事务状态

### Q2: 如何保证消息顺序？

**答：**
- RocketMQ 本身支持队列级顺序
- 发送时使用 MessageQueueSelector 将同一类消息发送到同一队列
- 消费时使用 MessageListenerOrderly 顺序消费

### Q3: 消息积压如何处理？

**答：**
1. 临时扩容消费者，提高消费能力
2. 排查消费慢的原因（代码问题/数据库瓶颈）
3. 增加队列数，提高并行度
4. 消息过期处理（消息只保留一定时间）

---

**⭐ 重点：RocketMQ 是国内最常用的消息中间件，需要掌握其架构和可靠消息方案**