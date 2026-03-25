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

### Q1: Kafka 为什么快？

**答：** 顺序写、零拷贝、批量处理、压缩。

---

**⭐ 重点：Kafka 是大数据生态的核心**