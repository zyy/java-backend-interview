---
layout: default
title: ShardingSphere 分库分表实战与原理
---
# ShardingSphere 分库分表实战与原理

## 🎯 面试题：什么时候需要分库分表？如何选择分片键？

> 分库分表是解决单表数据量过大、单库并发过高的核心方案。ShardingSphere 是目前最主流的分库分表中间件。

---

## 一、什么时候需要分库分表？

```
单表数据量超过 2000 万行 → 索引 B+ 树层数增加，查询变慢
单库 QPS 超过 5000 → 数据库连接数、CPU 成为瓶颈
单库存储超过 500GB → 备份恢复时间过长

优先考虑的优化手段（按顺序）：
  1. 加索引、优化 SQL
  2. 读写分离（主库写，从库读）
  3. 缓存（Redis 缓存热点数据）
  4. 垂直分表（大字段拆分到另一张表）
  5. 垂直分库（按业务模块拆分数据库）
  6. 水平分表（同一张表数据分散到多张表）
  7. 水平分库（数据分散到多个数据库）
```

---

## 二、ShardingSphere 产品线

| 产品 | 部署方式 | 适用场景 |
|------|----------|----------|
| ShardingSphere-JDBC | 客户端 JAR | Java 应用，无需额外部署 |
| ShardingSphere-Proxy | 独立代理服务 | 多语言、DBA 管理 |
| ShardingSphere-Sidecar | K8s Sidecar | 云原生场景 |

---

## 三、分片策略

### 哈希分片

```yaml
# application.yml
spring:
  shardingsphere:
    datasource:
      names: ds0, ds1
      ds0:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://db0:3306/order_db
        username: root
        password: 123456
      ds1:
        type: com.zaxxer.hikari.HikariDataSource
        jdbc-url: jdbc:mysql://db1:3306/order_db
        username: root
        password: 123456

    rules:
      sharding:
        tables:
          t_order:
            actual-data-nodes: ds${0..1}.t_order_${0..3}  # 2库 × 4表 = 8张表
            database-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: db-hash
            table-strategy:
              standard:
                sharding-column: order_id
                sharding-algorithm-name: table-hash
            key-generate-strategy:
              column: order_id
              key-generator-name: snowflake

        sharding-algorithms:
          db-hash:
            type: HASH_MOD
            props:
              sharding-count: 2
          table-hash:
            type: HASH_MOD
            props:
              sharding-count: 4

        key-generators:
          snowflake:
            type: SNOWFLAKE
```

### 范围分片

```yaml
# 按时间范围分片（适合日志、订单等时序数据）
sharding-algorithms:
  time-range:
    type: RANGE
    props:
      # 2024年数据 → t_order_2024
      # 2025年数据 → t_order_2025
      range-lower: 20240101
      range-upper: 20241231
      sharding-suffix-pattern: yyyy
      datetime-pattern: yyyyMMdd
```

---

## 四、分库分表后的核心问题

### 1. 分布式 ID

```java
// 雪花算法（Snowflake）
// 64 bit = 1(符号) + 41(时间戳ms) + 10(机器ID) + 12(序列号)
// 每毫秒最多生成 4096 个 ID，理论 QPS = 4096 * 1000 = 400万

// 号段模式（美团 Leaf）
// 从数据库批量获取 ID 段，减少数据库压力
// 每次取 1000 个 ID，用完再取
CREATE TABLE id_alloc (
    biz_tag VARCHAR(128) NOT NULL,
    max_id BIGINT NOT NULL,
    step INT NOT NULL,
    PRIMARY KEY (biz_tag)
);
```

### 2. 跨库查询

```java
// ❌ 跨库 JOIN（ShardingSphere 支持但性能差）
SELECT o.*, u.name FROM t_order o JOIN t_user u ON o.user_id = u.id

// ✅ 方案一：冗余字段（反范式）
// 在 t_order 中冗余 user_name 字段，避免跨库 JOIN

// ✅ 方案二：广播表（字典表）
// 小表（如城市、分类）在每个分片都保存一份
spring:
  shardingsphere:
    rules:
      sharding:
        broadcast-tables:
          - t_city
          - t_category

// ✅ 方案三：应用层 JOIN
// 先查 t_order，再根据 user_id 批量查 t_user
List<Order> orders = orderMapper.findByUserId(userId);
List<Long> userIds = orders.stream().map(Order::getUserId).collect(toList());
Map<Long, User> userMap = userMapper.findByIds(userIds).stream()
    .collect(toMap(User::getId, u -> u));
```

### 3. 分页查询

```java
// ❌ 深分页问题：SELECT * FROM t_order LIMIT 10000, 10
// ShardingSphere 需要从每个分片取 10010 条，再归并排序，性能极差

// ✅ 方案一：禁止深分页，用 search_after 游标
// ✅ 方案二：二次查询法
// 第一次：每个分片取 LIMIT 10010，取最小 offset 的 ID
// 第二次：WHERE id >= minId LIMIT 10

// ✅ 方案三：ES 存储分页数据，MySQL 存储完整数据
```

### 4. 分布式事务

```yaml
# ShardingSphere 支持 XA 分布式事务
spring:
  shardingsphere:
    rules:
      transaction:
        default-type: XA
        provider-type: Atomikos

# 或者使用 Seata AT 模式（推荐）
spring:
  shardingsphere:
    rules:
      transaction:
        default-type: BASE
        provider-type: Seata
```

---

## 五、面试高频题

**Q1: 如何选择分片键？**
> 分片键选择原则：① 均匀分布：数据能均匀分散到各分片，避免热点（如用 user_id 哈希，不用 status）；② 查询频率高：大多数查询都带分片键，避免全分片扫描；③ 不可变：分片键一旦确定不能修改（修改需要迁移数据）；④ 业务相关：如订单系统用 user_id，日志系统用时间。常见问题：用自增 ID 做分片键会导致数据集中在最新分片（热点）。

**Q2: 分库分表后如何处理跨库 JOIN？**
> 三种方案：① 冗余字段（反范式）：在表中冗余关联字段，避免 JOIN；② 广播表：小字典表在每个分片都保存一份；③ 应用层 JOIN：先查主表，再批量查关联表，在应用层组装。推荐优先用冗余字段，其次广播表，最后应用层 JOIN。跨库 JOIN 虽然 ShardingSphere 支持，但性能差，不推荐。

**Q3: 分库分表后分页查询怎么做？**
> 深分页是分库分表的经典难题。ShardingSphere 默认会从每个分片取 offset+limit 条数据再归并，深分页性能极差。解决方案：① 禁止深分页，改用游标分页（search_after）；② 二次查询法：先取各分片最小 offset 的 ID，再用 WHERE id >= minId 精确查询；③ 将分页数据同步到 ES，用 ES 做分页查询，MySQL 只做精确查询。
