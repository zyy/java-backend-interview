---
layout: default
title: MySQL 锁机制详解 ⭐⭐⭐
---
# MySQL 锁机制详解 ⭐⭐⭐

## 面试题：MySQL 有哪些锁？分别适用于什么场景？

### 核心回答

MySQL InnoDB 存储引擎实现了多种锁机制，包括行锁、表锁、意向锁、Gap 锁等，用于控制并发访问和数据一致性。

### 锁的分类

```
MySQL 锁
├── 按粒度分
│   ├── 表锁
│   ├── 行锁
│   └── 页锁
├── 按属性分
│   ├── 共享锁（S 锁）
│   └── 排他锁（X 锁）
├── 按模式分
│   ├── 记录锁（Record Lock）
│   ├── 间隙锁（Gap Lock）
│   └── Next-Key Lock
└── 按算法分
    ├── 乐观锁
    └── 悲观锁
```

### InnoDB 行锁

#### 1. 记录锁（Record Lock）

**定义**：锁定索引记录本身。

```sql
-- 锁定 id = 1 的记录
SELECT * FROM user WHERE id = 1 FOR UPDATE;
```

**特点**：
- 锁定单条索引记录
- 其他事务无法修改或删除该记录
- 不会阻止其他事务读取（除非显式加锁）

#### 2. 间隙锁（Gap Lock）

**定义**：锁定索引记录之间的间隙。

```sql
-- 锁定 id 在 (1, 5) 之间的间隙
SELECT * FROM user WHERE id BETWEEN 1 AND 5 FOR UPDATE;
-- 锁定 id > 1 AND id < 5 的记录
```

**特点**：
- 防止幻读（Phantom Read）
- 只在 REPEATABLE READ 隔离级别下生效
- 锁定的是索引之间的空隙，而不是数据行

```
Gap Lock 示意：

id:   1    3    5    7    9
     ┌──┐  ┌──┐  ┌──┐  ┌──┐
     │  │  │  │  │  │  │  │
     └──┘  └──┘  └──┘  └──┘
      ↑      ↑      ↑      ↑
   gap   gap   gap   gap
```

#### 3. Next-Key Lock

**定义**：记录锁 + 间隙锁的组合，锁定记录及其前面的间隙。

```sql
-- 锁定 id = 3 的记录以及 (1, 3) 和 (3, 5) 的间隙
SELECT * FROM user WHERE id = 3 FOR UPDATE;
```

**作用**：
- 防止幻读
- 锁定索引范围，包括记录本身和间隙
- InnoDB 默认的锁算法

### 共享锁与排他锁

#### 共享锁（S 锁）

```sql
-- 事务 A 获取共享锁
SELECT * FROM user WHERE id = 1 LOCK IN SHARE MODE;

-- 事务 B 也可以获取共享锁
SELECT * FROM user WHERE id = 1 LOCK IN SHARE MODE;

-- 事务 B 不能获取排他锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;  -- 阻塞
```

**特点**：
- 读读兼容
- 读写互斥

#### 排他锁（X 锁）

```sql
-- 事务 A 获取排他锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;

-- 事务 B 不能获取任何锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;  -- 阻塞
SELECT * FROM user WHERE id = 1 LOCK IN SHARE MODE;  -- 阻塞
```

**特点**：
- 写写互斥
- 读写互斥

### 意向锁

#### 什么是意向锁？

意向锁是表级锁，表示事务即将对某行加锁。

| 锁类型 | 作用 |
|--------|------|
| 意向共享锁（IS） | 事务即将对行加共享锁 |
| 意向排他锁（IX） | 事务即将对行加排他锁 |

#### 意向锁的作用

```sql
-- 事务 A：对某行加排他锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;

-- 自动加锁过程：
-- 1. 先对表加意向排他锁（IX）
-- 2. 再对行加排他锁（X）

-- 事务 B：想对整个表加表锁
LOCK TABLE user WRITE;

-- 检查意向锁：
-- 存在 IX，表示有事务正在锁定某些行
-- 需要等待行锁释放才能获取表锁
```

### 死锁

#### 什么是死锁？

两个或多个事务相互等待对方持有的锁，形成循环等待。

```sql
-- 事务 A
BEGIN;
UPDATE user SET name = 'A' WHERE id = 1;  -- 锁定 id=1
UPDATE user SET name = 'B' WHERE id = 2;  -- 等待 id=2

-- 事务 B（同时执行）
BEGIN;
UPDATE user SET name = 'B' WHERE id = 2;  -- 锁定 id=2
UPDATE user SET name = 'A' WHERE id = 1;  -- 等待 id=1

-- 死锁形成！
```

#### InnoDB 处理死锁

```sql
-- InnoDB 自动检测死锁
-- 回滚最小事务（undo log 最少的事务）

SHOW ENGINE INNODB STATUS;

-- 返回结果示例：
-- ------------------------
-- LATEST DETECTED DEADLOCK
-- ------------------------
-- Transaction 1 ...
-- Transaction 2 ...
-- ROLLBACK TRANSACTION 2
```

#### 避免死锁

```java
// 1. 统一加锁顺序
// 不好的方式
updateUser(id1);
updateOrder(id2);

// 好的方式：始终按 ID 顺序加锁
if (id1 < id2) {
    updateUser(id1);
    updateOrder(id2);
} else {
    updateOrder(id2);
    updateUser(id1);
}

// 2. 减少锁持有时间
@Transactional
public void updateOrder(Long orderId) {
    // 减少事务中的操作
    Order order = orderRepository.findById(orderId);
    // 业务处理
    // ...
    orderRepository.save(order);
}

// 3. 使用低隔离级别
@Transactional(isolation = Isolation.READ_COMMITTED)
public void update() {
    // ...
}
```

### 锁等待查看

```sql
-- 查看当前锁等待
SELECT * FROM information_schema.INNODB_LOCK_WAITS;

-- 查看当前锁
SELECT * FROM information_schema.INNODB_LOCKS;

-- 查看事务状态
SELECT * FROM information_schema.INNODB_TRX;

-- 查看锁详情
SHOW ENGINE INNODB STATUS;
```

### MVCC 与锁

#### 快照读 vs 当前读

```sql
-- 快照读：不加锁，读取历史版本
SELECT * FROM user WHERE id = 1;  -- 快照读

-- 当前读：加锁，读取最新版本
SELECT * FROM user WHERE id = 1 FOR UPDATE;  -- 当前读
SELECT * FROM user WHERE id = 1 LOCK IN SHARE MODE;  -- 当前读
INSERT/UPDATE/DELETE -- 当前读
```

#### 读已提交 vs 可重复读

```sql
-- 读已提交（RC）：每次读取都生成新的 ReadView
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 可重复读（RR）：事务开始时生成 ReadView
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

### 高频面试题

**Q1: InnoDB 行锁的实现方式？**

```
InnoDB 行锁基于索引实现：
1. 如果查询条件使用索引，加行锁
2. 如果查询条件不使用索引，加表锁

示例：
- WHERE id = 1（id 是主键）：加行锁
- WHERE name = '张三'（name 有索引）：加行锁
- WHERE name = '张三'（name 无索引）：加表锁
```

**Q2: 什么是临键锁（Next-Key Lock）？**

```
Next-Key Lock = Record Lock + Gap Lock

锁定范围：[前一个记录, 当前记录]

示例：
索引值：1, 3, 5, 7, 9

SELECT * FROM t WHERE id = 5 LOCK IN SHARE MODE;

锁定的范围：
- (3, 5)：3 和 5 之间的间隙
- (5, 7)：5 和 7 之间的间隙
- [5]：id=5 的记录

作用：防止幻读
```

**Q3: 如何排查死锁？**

```sql
-- 1. 查看死锁日志
SHOW ENGINE INNODB STATUS;

-- 2. 分析日志中的事务和 SQL
-- 找出相互等待的 SQL

-- 3. 优化 SQL 和事务顺序
-- 统一加锁顺序
-- 减少锁持有时间

-- 4. 设置死锁检测
innodb_deadlock_detect = on  -- 默认开启
```

**Q4: 乐观锁和悲观锁的区别？**

```java
// 乐观锁：假设不会冲突，更新时检查版本
@Version
private Long version;

// UPDATE SET name='xxx', version=version+1 WHERE id=? AND version=?

// 悲观锁：假设会发生冲突，读取时加锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;

// 乐观锁适用：冲突少，低并发
// 悲观锁适用：冲突多，高并发
```

**Q5: SELECT 会加锁吗？**

```
普通 SELECT：不加锁（快照读）

显式加锁的 SELECT：
- SELECT ... LOCK IN SHARE MODE：加共享锁
- SELECT ... FOR UPDATE：加排他锁

带 FOR UPDATE 的子查询：
SELECT * FROM orders WHERE user_id IN (
    SELECT id FROM user WHERE status = 1 FOR UPDATE
);
-- 对子查询中的记录加锁
```

### 最佳实践

```java
// 1. 尽量使用索引，减少锁范围
@Query("SELECT u FROM User u WHERE u.name = :name")
User findByName(@Param("name") String name);

// 2. 批量操作时注意锁等待
@Transactional
public void batchUpdate(List<Long> ids) {
    // 按 ID 排序，统一顺序
    ids.sort(Comparator.naturalOrder());
    for (Long id : ids) {
        update(id);
    }
}

// 3. 使用分布式锁处理热点数据
@Autowired
private RedissonClient redisson;

public void handleHotData(Long productId) {
    RLock lock = redisson.getLock("product:" + productId);
    try {
        lock.lock();
        // 业务逻辑
    } finally {
        lock.unlock();
    }
}

// 4. 监控锁等待
SELECT * FROM performance_schema.events_statements_summary_by_digest
WHERE DIGEST_TEXT LIKE '%FOR UPDATE%';
```

---

**参考链接：**
- [MySQL锁机制详解-腾讯云](https://cloud.tencent.com/developer/article/2398601)
