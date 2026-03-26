---
layout: default
title: 中间件
---
# 中间件

> 中间件是构建高并发系统的基石

## 📋 内容大纲

### 1. Redis ⭐⭐⭐
- [数据类型与应用场景](./redis-data-types.md)
- [持久化与过期策略](./redis-persistence.md) ⭐⭐⭐
- [缓存穿透、击穿、雪崩](./cache-problems.md) ⭐⭐⭐
- [主从复制与哨兵](./redis-replication.md)
- [Cluster 集群](./redis-cluster.md)
- [分布式锁实现](./distributed-lock.md)

### 2. 消息队列 ⭐⭐⭐
- [消息队列选型](./mq-comparison.md)
- [RocketMQ 架构](./rocketmq-architecture.md)
- [Kafka 原理](./kafka-principles.md)
- [消息可靠性保证](./message-reliability.md)
- [顺序消息与延迟消息](./message-patterns.md)
- [订单超时自动取消：Redis 延时队列实现](./order-delay-queue.md) ⭐⭐⭐

### 3. Elasticsearch ⭐⭐
- [倒排索引原理](./inverted-index.md)
- [分词与映射](./analysis-mapping.md)
- [搜索与聚合](./search-aggregate.md)
- [性能优化](./es-optimization.md)

## 🎯 面试高频题

1. **[Redis 为什么这么快？](./redis-data-types.md)**
2. **[什么是缓存穿透、击穿、雪崩？如何解决？](./cache-problems.md)**
3. **[Redis 的持久化方式有哪些？过期策略是什么？](./redis-persistence.md)**
4. **[RocketMQ 的事务消息原理？](./rocketmq-architecture.md)**
5. **[Kafka 如何保证消息不丢失？](./kafka-principles.md)**

## 📚 延伸阅读

- [Redis 官方文档](https://redis.io/documentation)
- [RocketMQ 官方文档](https://rocketmq.apache.org/)
