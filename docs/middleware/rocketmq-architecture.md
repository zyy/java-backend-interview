---
layout: default
title: RocketMQ 架构
---
# RocketMQ 架构

> RocketMQ 核心组件

## 🎯 面试重点

- RocketMQ 架构组件
- 消息存储原理

## 📖 架构组件

### 核心组件

```java
/**
 * RocketMQ 架构
 */
public class RocketMQArchitecture {
    // NameServer
    /*
     * - 轻量级注册中心
     * - 负责 Broker 管理、服务发现
     * - 每个 NameServer 独立
     */
    
    // Broker
    /*
     * - 消息存储和转发
     * - 主从部署
     */
    
    // Producer
    /*
     * - 消息生产者
     */
    
    // Consumer
    /*
     * - 消息消费者
     * - 推/拉模式
     */
}
```

## 📖 面试真题

### Q1: RocketMQ 的事务消息原理？

**答：** RocketMQ 的事务消息是一种保证分布式事务最终一致性的机制，其核心原理如下：

#### 1. 事务消息流程
RocketMQ 事务消息采用“两阶段提交”的思想，具体流程如下：

**第一阶段：发送半消息**
1. 生产者发送“半消息”（Half Message）到 Broker。
2. Broker 将消息存储到特殊的 Topic（RMQ_SYS_TRANS_HALF_TOPIC）中，此时消费者不可见。
3. Broker 返回发送结果给生产者。

**第二阶段：执行本地事务**
1. 生产者执行本地事务（如更新数据库）。
2. 根据本地事务执行结果，生产者向 Broker 发送“提交”或“回滚”指令。

**第三阶段：Broker 处理**
- **提交**：Broker 将半消息从 RMQ_SYS_TRANS_HALF_TOPIC 移动到原始 Topic，消费者可见。
- **回滚**：Broker 删除半消息，消费者永远不会看到。
- **未决状态**：如果生产者没有返回最终状态，Broker 会定时回查生产者。

#### 2. 事务回查机制
- **触发条件**：如果 Broker 在一定时间（默认 1 分钟）内没有收到生产者的最终确认，会发起回查。
- **回查次数**：默认最多 15 次，超过后默认丢弃消息（可配置为回滚）。
- **实现要求**：生产者需要实现 `TransactionListener` 接口，提供本地事务执行和回查逻辑。

#### 3. 代码示例
```java
// 1. 创建事务消息生产者
TransactionMQProducer producer = new TransactionMQProducer("group");
producer.setNamesrvAddr("localhost:9876");

// 2. 设置事务监听器
producer.setTransactionListener(new TransactionListener() {
    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        // 执行本地事务
        try {
            // 更新数据库等操作
            boolean success = doBusiness();
            return success ? LocalTransactionState.COMMIT_MESSAGE : 
                           LocalTransactionState.ROLLBACK_MESSAGE;
        } catch (Exception e) {
            return LocalTransactionState.ROLLBACK_MESSAGE;
        }
    }
    
    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        // 事务回查逻辑
        return checkBusinessStatus() ? LocalTransactionState.COMMIT_MESSAGE : 
                                     LocalTransactionState.ROLLBACK_MESSAGE;
    }
});

// 3. 发送事务消息
Message msg = new Message("Topic", "Tag", "Key", "Body".getBytes());
TransactionSendResult result = producer.sendMessageInTransaction(msg, null);
```

#### 4. 使用场景
- **分布式事务**：如订单创建（扣库存、创建订单、扣余额等）。
- **数据一致性**：保证多个系统间的数据最终一致。
- **异步处理**：将耗时操作异步化，提高系统响应速度。

#### 5. 注意事项
- **消息重复消费**：消费者需要实现幂等性处理。
- **事务状态丢失**：生产者需要持久化事务状态，以便回查时能正确返回。
- **性能影响**：事务消息比普通消息多一次网络交互，性能略有下降。

#### 6. 与其他方案对比
| 特性 | RocketMQ 事务消息 | TCC | 本地消息表 |
|------|------------------|-----|-----------|
| 一致性 | 最终一致 | 最终一致 | 最终一致 |
| 侵入性 | 低 | 高 | 中 |
| 性能 | 较高 | 中 | 中 |
| 实现复杂度 | 低 | 高 | 中 |
| 适用场景 | 异步消息场景 | 强一致性要求 | 简单分布式事务 |

**总结**：RocketMQ 事务消息通过半消息、两阶段提交和事务回查机制，实现了分布式事务的最终一致性，是解决分布式事务问题的常用方案之一。

---

**⭐ 重点：理解 RocketMQ 架构**