---
layout: default
title: 数据库
---
# 数据库

> 数据库是后端开发的核心技能，面试重点考察

## 📋 内容大纲

### 1. MySQL 基础 ⭐
- [存储引擎对比](./storage-engines.md)
- [数据类型选择](./data-types.md)
- [SQL 优化技巧](./sql-optimization.md)

### 2. 索引原理 ⭐⭐⭐
- [B+树索引原理](./index-principle.md) ⭐⭐⭐
- [索引失效场景](./index-failure.md) ⭐⭐⭐
- [覆盖索引与回表](./covering-index.md)

### 3. 事务与锁 ⭐⭐⭐
- [事务 ACID 与 MVCC](./transaction-mvcc.md) ⭐⭐⭐
- [隔离级别与问题](./isolation-levels.md)
- [锁机制详解](./locking.md) ⭐⭐⭐
- [死锁分析与预防](./deadlock.md)
- [MySQL 日志系统详解](./mysql-logs.md) ⭐⭐⭐

### 4. 分库分表 ⭐⭐⭐
- [分片策略](./sharding-strategy.md)
- [分布式 ID](./distributed-id.md)
- [ShardingSphere 实战](./shardingsphere.md)

### 5. 高并发场景 ⭐⭐⭐
- [金融系统热点账户问题](./hot-account.md) ⭐⭐⭐

### 6. 主从复制与高可用 ⭐⭐⭐
- [MySQL 主从复制与高可用](./replication-ha.md) ⭐⭐⭐
- [数据库读写分离方案详解](./readwrite-splitting.md) ⭐⭐⭐

### 7. 性能优化 ⭐⭐⭐
- [慢查询优化与性能调优](./slow-query-optimization.md) ⭐⭐⭐

### 8. MySQL 8.0 新特性 ⭐⭐
- [MySQL 8.0 新特性详解](./mysql8-features.md)

## 🎯 面试高频题

1. **[InnoDB 和 MyISAM 的区别？](./storage-engines.md)**
2. **[B+树索引的原理？为什么不用 B 树？](./index-principle.md)**
3. **[什么情况下索引会失效？](./index-failure.md)**
4. **[MVCC 如何实现读写不阻塞？](./transaction-mvcc.md)**
5. **[MySQL 有哪些锁？如何避免死锁？](./locking.md)**
6. **[Binlog、Redo Log、Undo Log 的区别？](./mysql-logs.md)**
7. **[两阶段提交（2PC）的原理？](./mysql-logs.md)**
8. **[金融系统热点账户如何解决？](./hot-account.md)**
9. **[MySQL 主从复制的原理？](./replication-ha.md)**
10. **[如何排查慢查询？](./slow-query-optimization.md)**
11. **[MySQL 8.0 有哪些重大改进？](./mysql8-features.md)**

## 📚 延伸阅读

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [高性能 MySQL](https://book.douban.com/subject/23008813/)
