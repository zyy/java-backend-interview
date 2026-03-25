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

### Q1: RocketMQ 的特点？

**答：** 事务消息、顺序消息、延迟消息，功能完善。

---

**⭐ 重点：理解 RocketMQ 架构**