# 数据库

> 数据库是后端开发的核心技能，面试重点考察

## 📋 内容大纲

### 1. MySQL 基础 ⭐
- [存储引擎对比](./storage-engines.md)
- [数据类型选择](./data-types.md)
- [SQL 优化技巧](./sql-optimization.md)

### 2. 索引原理 ⭐⭐⭐
- [B+树结构](./b-plus-tree.md)
- [索引设计原则](./index-design.md)
- [索引失效场景](./index-failure.md)
- [覆盖索引与回表](./covering-index.md)

### 3. 事务与锁 ⭐⭐⭐
- [ACID 与实现](./acid.md)
- [隔离级别与问题](./isolation-levels.md)
- [MVCC 机制](./mvcc.md)
- [锁类型与粒度](./locking.md)
- [死锁分析与预防](./deadlock.md)

### 4. 分库分表 ⭐⭐⭐
- [分片策略](./sharding-strategy.md)
- [分布式 ID](./distributed-id.md)
- [ShardingSphere 实战](./shardingsphere.md)

## 🎯 面试高频题

1. **InnoDB 和 MyISAM 的区别？**
2. **B+树索引的原理？为什么不用 B 树？**
3. **聚簇索引和非聚簇索引的区别？**
4. **MVCC 如何实现读写不阻塞？**
5. **什么情况下索引会失效？**

## 📚 延伸阅读

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [高性能 MySQL](https://book.douban.com/subject/23008813/)
