# Kafka 核心原理

> 高吞吐量的分布式消息队列

## 🎯 面试重点

- Kafka 的架构和核心概念
- 分区和副本机制
- 消息顺序性和可靠性
- 消费者组和_offset 管理

## 📖 Kafka 架构

### 核心概念

```java
/**
 * Kafka 核心概念：
 * 
 * Broker：Kafka 服务器，一个 Broker 就是一个 Kafka 实例
 * 
 * Topic：消息主题，用于对消息进行分类
 *   - Producer 向 Topic 发送消息
 *   - Consumer 从 Topic 消费消息
 * 
 * Partition：Topic 的分区
 *   - 实现消息的分片存储
 *   - 每个 Partition 内部有序
 * 
 * Replica：副本
 *   - Leader Replica：处理读写请求
 *   - Follower Replica：同步数据
 * 
 * Producer：消息生产者
 * 
 * Consumer：消息消费者
 * 
 * Consumer Group：消费者组
 *   - 同一组内的消费者共同消费一个 Topic
 *   - 不同组之间相互独立
 */
public class KafkaConcepts {}
```

### 架构图

```java
/**
 * Kafka 整体架构：
 * 
 * ┌─────────────────────────────────────────────────────────┐
 * │                      Kafka Cluster                      │
 * │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
 * │  │   Broker 1  │   │   Broker 2  │   │   Broker 3  │   │
 * │  │  P0(L/F)    │   │  P1(L/F)    │   │  P2(L/F)    │   │
 * │  │  P1(F)      │   │  P2(F)      │   │  P0(F)      │   │
 * │  │  P2(L/F)    │   │  P0(F)      │   │  P1(L/F)    │   │
 * │  └─────────────┘   └─────────────┘   └─────────────┘   │
 * └─────────────────────────────────────────────────────────┘
 *                          ↑
 *            ┌─────────────┴─────────────┐
 *            │                           │
 *      ┌─────┴─────┐              ┌─────┴─────┐
 *      │ Producer  │              │ Consumer  │
 *      │           │              │  Group A  │
 *      └───────────┘              └───────────┘
 */
```

## 📖 分区和副本机制

### Partition 分区

```java
/**
 * Partition 的作用：
 * 1. 实现消息的并行处理
 * 2. 提高 Kafka 的吞吐量
 * 3. 实现消息的分片存储
 */
public class PartitionExample {
    // Topic 创建时指定分区数
    // bin/kafka-topics.sh --create --topic test --partitions 3
    
    // 分区分配策略
    /*
     * 1. 轮询策略（RoundRobin）
     *    - 消息均匀分配到各分区
     *    - 默认策略
     * 
     * 2. 随机策略（Random）
     * 
     * 3. 消息键分配（Key Ordering）
     *    - 相同 Key 的消息到同一分区
     *    - 保证同一 Key 的消息顺序
     * 
     * Producer 代码示例：
     * 
     * Properties props = new Properties();
     * props.put("bootstrap.servers", "localhost:9092");
     * props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
     * props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
     * 
     * KafkaProducer<String, String> producer = new KafkaProducer<>(props);
     * 
     * // 发送消息
     * ProducerRecord<String, String> record = new ProducerRecord<>("topic", "key", "value");
     * producer.send(record);
     */
}
```

### Replica 副本

```java
/**
 * 副本机制
 * 
 * ISR（In-Sync Replicas）：同步副本
 *   - 与 Leader 保持同步的副本集合
 *   - 同步标准：replica.lag.time.max.ms 内追上 Leader
 * 
 * AR（Assigned Replicas）：所有副本
 *   - 包括 ISR 和非 ISR
 */
public class ReplicaExample {
    // 副本配置
    /*
     * topics:
     *   my-topic:
     *     partitions: 3
     *     replication-factor: 3  # 副本因子
     * 
     * 副本分布（假设3个Broker）：
     * Partition 0: Broker 1(Leader), Broker 2, Broker 3
     * Partition 1: Broker 2(Leader), Broker 3, Broker 1
     * Partition 2: Broker 3(Leader), Broker 1, Broker 2
     */
    
    // Leader 选举
    /*
     * 1. 优先从 ISR 中选择作为 Leader
     * 2. ISR 为空时，从 AR 中选择
     * 3. 可能导致消息丢失（选择不是最新的副本）
     */
}
```

## 📖 消息可靠性

### ACK 机制

```java
/**
 * Producer ACK 配置
 * 
 * acks = 0（最少等待）
 * - Producer 不等待 Leader 确认
 * - 最高吞吐量，可能丢失消息
 * - 适用于日志采集
 * 
 * acks = 1（默认）
 * - 等待 Leader 确认
 * - 可能丢失Follower同步成功的消息
 * 
 * acks = -1/all（最可靠）
 * - 等待 ISR 中所有副本确认
 * - 等待时间最长，可靠性最高
 * - 可能因 ISR 为空而阻塞
 */
public class AckMechanism {
    // 配置示例
    /*
     * props.put("acks", "all");
     * props.put("retries", 3);  // 重试次数
     * props.put("enable.idempotence", true);  // 幂等性
     */
    
    // 幂等性配置
    /*
     * enable.idempotence = true
     * 
     * 原理：
     * - Producer 增加 PID（Producer ID）
     * - 每个 Partition 维护 Sequence Number
     * - 相同 PID + Partition + Sequence Number 的消息只写入一次
     * 
     * 注意：
     * - 需要设置 acks=all
     * - 同一 Producer 进程重启后 PID 变化，幂等性失效
     */
}
```

### 消息顺序性

```java
/**
 * Kafka 消息顺序性
 * 
 * 1. 单 Partition 内有序
 * - Kafka 保证同一 Partition 内消息有序
 * 
 * 2. 全局有序
 * - 只设置 1 个 Partition
 * - 降低吞吐量
 * 
 * 3. 跨 Partition 全局有序
 * - 自定义分区器：相同特征的消息到同一 Partition
 * - 通过 Key 路由
 */
public class MessageOrder {
    // 自定义分区器
    /*
     * public class OrderPartitioner implements Partitioner {
     *     @Override
     *     public int partition(String topic, Object key, byte[] keyBytes, 
     *                          Object value, byte[] valueBytes, Cluster cluster) {
     *         // 按订单 ID 取模，保证同一订单消息有序
     *         String orderId = (String) key;
     *         int partition = Math.abs(orderId.hashCode()) % cluster.partitionCountForTopic(topic);
     *         return partition;
     *     }
     * }
     */
}
```

## 📖 消费者和消费者组

### 消费者组

```java
/**
 * 消费者组原理
 * 
 * 规则：
 * 1. 同一消费者组内，一个 Partition 只能被一个消费者消费
 * 2. 不同消费者组之间，消息相互独立消费
 * 3. 消费者数量不应超过 Partition 数量
 * 
 * 负载均衡：
 * - 当消费者数量变化时，触发 Rebalance
 * - 所有消费者暂停消费
 * - 重新分配 Partition
 * - 可能导致消费暂停（Stop The World）
 */
public class ConsumerGroupExample {
    // 配置示例
    /*
     * props.put("bootstrap.servers", "localhost:9092");
     * props.put("group.id", "my-consumer-group");
     * props.put("enable.auto.commit", "true");
     * props.put("auto.commit.interval.ms", "5000");
     * 
     * KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
     * consumer.subscribe(Arrays.asList("topic1", "topic2"));
     * 
     * while (true) {
     *     ConsumerRecords<String, String> records = consumer.poll(100);
     *     for (ConsumerRecord<String, String> record : records) {
     *         System.out.println(record.value());
     *     }
     * }
     */
}
```

### Offset 管理

```java
/**
 * Offset 管理
 * 
 * 1. 自动提交（默认）
 * enable.auto.commit = true
 * auto.commit.interval.ms = 5000
 * - 可能导致重复消费或消息丢失
 * 
 * 2. 手动提交
 * enable.auto.commit = false
 * - 同步提交：consumer.commitSync()
 * - 异步提交：consumer.commitAsync()
 * 
 * 3. Offset 重置策略
 * auto.offset.reset = latest / earliest
 * 
 * 4. 精确一次消费
 * - 幂等性 + 手动提交
 * - 事务 + 手动提交
 */
public class OffsetManagement {
    // 手动提交示例
    /*
     * while (true) {
     *     ConsumerRecords<String, String> records = consumer.poll(100);
     *     for (ConsumerRecord<String, String> record : records) {
     *         process(record);
     *     }
     *     // 同步提交
     *     consumer.commitSync();
     * }
     */
}
```

## 📖 面试真题

### Q1: Kafka 为什么这么快？

**答：**
1. 顺序读写：利用磁盘顺序读写，比随机读快
2. 零拷贝：使用 sendfile 系统调用，避免内核和用户空间之间的数据复制
3. 批量处理：消息批量发送和消费
4. 压缩：支持多种压缩算法（GZIP、Snappy、LZ4）
5. 分区：并行处理

### Q2: 如何保证消息不丢失？

**答：**
1. Producer 端：设置 acks=all，重试 retries>0，启用幂等性
2. Broker 端：设置 replica.lag.time.max.ms，合理配置副本因子
3. Consumer 端：手动提交 offset

### Q3: Kafka 消费者组 rebalance 的问题？

**答：**
- 问题：所有消费者停止消费，重新分配分区
- 解决：
  1. 合理设计分区数（避免频繁 rebalance）
  2. 使用静态成员（cooperative rebalance）
  3. 调整 rebalance 超时时间

---

**⭐ 重点：Kafka 是大数据领域最常用的消息队列，需要掌握其架构、可靠性和性能优化**