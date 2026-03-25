---
layout: default
title: 消息可靠性保证
---
# 消息可靠性保证

> 确保消息不丢失

## 🎯 面试重点

- 消息丢失场景
- 可靠消息方案

## 📖 可靠性保证

### 生产端

```java
/**
 * 生产端可靠性
 */
public class ProducerReliability {
    // 同步发送 + 重试
    /*
     * producer.send(msg);
     * producer.send(msg, callback);
     * 
     * props.put("acks", "all");
     * props.put("retries", 3);
     */
}
```

### 消费端

```java
/**
 * 消费端可靠性
 */
public class ConsumerReliability {
    // 手动提交 offset
    /*
     * 消费成功后再提交
     * 避免重复消费
     */
}
```

## 📖 面试真题

### Q1: 如何保证消息不丢失？

**答：** 
- 生产端：ACK=all + 重试
- 存储端：同步刷盘 + 副本
- 消费端：手动提交 offset

---

**⭐ 重点：消息可靠性是 MQ 的核心**