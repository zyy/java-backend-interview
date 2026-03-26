---
layout: default
title: 微服务架构
---
# 微服务架构

> 微服务是大型系统的标配，架构师面试重点

## 📋 内容大纲

### 1. 分布式基础 ⭐⭐⭐
- [CAP 与 BASE 理论](./cap-base.md)
- [Raft 一致性协议详解](./raft-consensus.md) ⭐⭐⭐
- [分布式一致性（Paxos）](./distributed-consistency.md)
- [分布式事务](./distributed-transaction.md) ⭐⭐⭐
- [一致性哈希](./consistent-hashing.md) ⭐⭐⭐

### 2. 服务治理 ⭐⭐⭐
- [服务注册发现](./service-registry.md)
- [配置中心](./config-server.md)
- [链路追踪](./distributed-tracing.md)

### 3. 高可用设计 ⭐⭐⭐
- [限流算法](./rate-limiting.md)
- [熔断降级](./circuit-breaker-pattern.md)
- [负载均衡策略](./load-balance-strategies.md)

### 4. 容器化与云原生 ⭐⭐
- [Docker 基础](./docker-basics.md)
- [Kubernetes 核心概念](./kubernetes.md)
- [服务网格 Istio](./service-mesh.md)

## 🎯 面试高频题

1. **[CAP 理论是什么？如何取舍？](./cap-base.md)**
2. **[Raft 协议是如何工作的？领导人选举和日志复制流程？](./raft-consensus.md)**
3. **[分布式事务的解决方案有哪些？](./distributed-transaction.md)**
4. **[一致性哈希解决了什么问题？](./consistent-hashing.md)**
5. **[限流的常见算法？](./rate-limiting.md)**
6. **[熔断和降级的区别？](./circuit-breaker-pattern.md)**
7. **[服务网格解决了什么问题？](./service-mesh.md)**

## 📚 延伸阅读

- [微服务设计](https://book.douban.com/subject/26772677/)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)
