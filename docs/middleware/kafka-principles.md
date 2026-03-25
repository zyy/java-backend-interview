---
layout: default
title: Kafka 原理
---
# Kafka 原理

> Kafka 核心原理详解

## 🎯 面试重点

- Kafka 架构
- 分区和副本
- 消息可靠性

## 📖 核心概念

### 架构

```java
/**
 * Kafka 架构
 */
public class KafkaArchitecture {
    // Broker
    /*
     * Kafka 服务器
     */
    
    // Topic
    /*
     * 消息主题
     * 分区存储
     */
    
    // Partition
    /*
     * 分区
     * 副本机制
     */
    
    // Producer / Consumer
    /*
     * 生产者/消费者
     */
    
    // Consumer Group
    /*
     * 消费者组
     * 同一组内负载均衡
     */
}
```

## 📖 面试真题

### Q1: Kafka 如何保证消息不丢失？

**答：** Kafka 通过多层次的机制来保证消息不丢失，主要从生产者、Broker 和消费者三个角度进行保障。

#### 1. 生产者端保证
- **ACK 机制**：
  - `acks=0`：生产者不等待 Broker 确认，可能丢失消息。
  - `acks=1`：等待 Leader 副本写入成功（默认），Leader 故障可能丢失。
  - `acks=all` 或 `acks=-1`：等待所有 ISR（In-Sync Replicas）副本写入成功，最安全。
- **重试机制**：
  - 配置 `retries` 参数（默认 Integer.MAX_VALUE）。
  - 配置 `retry.backoff.ms` 控制重试间隔。
- **同步发送**：使用 `send().get()` 同步等待发送结果。
- **回调处理**：异步发送时，通过回调函数处理发送失败。

```java
// 生产者配置
Properties props = new Properties();
props.put("acks", "all");  // 所有副本确认
props.put("retries", 3);   // 重试次数
props.put("max.in.flight.requests.per.connection", 1);  // 防止乱序

// 发送消息
producer.send(record, new Callback() {
    @Override
    public void onCompletion(RecordMetadata metadata, Exception e) {
        if (e != null) {
            // 处理发送失败
        }
    }
});
```

#### 2. Broker 端保证
- **副本机制**：
  - 每个 Partition 有多个副本（Replica），分布在不同的 Broker 上。
  - Leader 负责读写，Follower 从 Leader 同步数据。
- **ISR 机制**：
  - ISR（In-Sync Replicas）是与 Leader 保持同步的副本集合。
  - 消息需要写入所有 ISR 副本才算成功（当 `acks=all` 时）。
- **持久化**：
  - 消息先写入 Page Cache，然后异步刷盘。
  - 通过 `flush.messages` 和 `flush.ms` 控制刷盘策略。
- **高可用**：
  - Leader 故障时，Controller 会从 ISR 中选举新的 Leader。
  - 通过 `unclean.leader.election.enable` 控制是否允许非 ISR 副本成为 Leader（默认 false，保证不丢失数据）。

#### 3. 消费者端保证
- **手动提交 Offset**：
  - 使用 `enable.auto.commit=false` 关闭自动提交。
  - 处理完消息后手动提交 Offset。
- **消费幂等性**：
  - 消费者需要实现幂等处理，防止重复消费。
- **消费位置重置**：
  - 配置 `auto.offset.reset` 决定消费起始位置（earliest/latest/none）。

```java
// 消费者配置
Properties props = new Properties();
props.put("enable.auto.commit", "false");  // 手动提交
props.put("auto.offset.reset", "earliest"); // 从最早开始消费

// 消费消息
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        try {
            // 处理消息
            processMessage(record);
            // 手动提交 Offset（同步）
            consumer.commitSync();
        } catch (Exception e) {
            // 处理异常，不提交 Offset
            log.error("消费失败", e);
        }
    }
}
```

#### 4. 数据可靠性配置组合
- **最高可靠性**：`acks=all` + 手动提交 Offset + ISR 最小副本数 ≥ 2。
- **平衡方案**：`acks=1` + 自动提交 Offset + 监控告警。
- **高性能方案**：`acks=0` 或 `acks=1`，容忍少量数据丢失。

#### 5. 监控与运维
- **监控指标**：Under Replicated Partitions、ISR 收缩、Leader 选举等。
- **容量规划**：确保磁盘空间充足，避免因磁盘满导致消息丢失。
- **定期测试**：模拟故障场景，验证数据可靠性。

#### 6. 与其他消息队列对比
| 特性 | Kafka | RocketMQ | RabbitMQ |
|------|-------|----------|----------|
| 可靠性 | 高（副本机制） | 高（主从同步） | 高（镜像队列） |
| 性能 | 极高（顺序写） | 高 | 中 |
| 消息顺序 | Partition 内有序 | 队列内有序 | 队列内有序 |
| 使用场景 | 大数据、日志 | 业务消息、事务 | 企业集成 |

**总结**：Kafka 通过生产者 ACK、Broker 副本机制和消费者手动提交 Offset 等多重保障，实现了高可靠的消息传输。在实际使用中，需要根据业务需求在可靠性和性能之间做出权衡。

---

**⭐ 重点：Kafka 是大数据生态的核心**