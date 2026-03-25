---
layout: default
title: 事务隔离级别
---
# 事务隔离级别

> 并发控制的核心

## 🎯 面试重点

- 四种隔离级别的区别
- 各隔离级别可能出现的问题
- 隔离级别和锁的关系

## 📖 隔离级别

### 四种级别

```java
/**
 * SQL 标准定义的四种隔离级别：
 * 
 * 1. READ UNCOMMITTED（读未提交）
 *    - 读取未提交的数据
 *    - 可能出现脏读
 * 
 * 2. READ COMMITTED（读已提交）
 *    - 读取已提交的数据
 *    - 可能出现不可重复读
 * 
 * 3. REPEATABLE READ（可重复读）
 *    - 多次读取同一数据，结果一致
 *    - MySQL InnoDB 默认
 *    - 可能出现幻读
 * 
 * 4. SERIALIZABLE（串行化）
 *    - 最高隔离级别
 *    - 完全串行执行
 *    - 性能最差
 */
public class IsolationLevels {}
```

### 各级别问题

```java
/**
 * 隔离级别和并发问题
 */
public class IsolationProblems {
    // 设置隔离级别
    /*
     * SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
     */
    
    // 问题演示
    /*
     * 脏读（Dirty Read）：
     * T1: SELECT * FROM account WHERE id=1; -- 读到 1000
     * T2: UPDATE account SET balance=balance-100 WHERE id=1;
     * T1: SELECT * FROM account WHERE id=1; -- 读到 900（脏数据）
     * T2: ROLLBACK;  -- T2 回滚
     * T1: SELECT * FROM account WHERE id=1; -- 读到 1000
     * 
     * 不可重复读（Non-repeatable Read）：
     * T1: SELECT * FROM account WHERE id=1; -- 读到 1000
     * T2: UPDATE account SET balance=balance-100 WHERE id=1; COMMIT;
     * T1: SELECT * FROM account WHERE id=1; -- 读到 900
     * 
     * 幻读（Phantom Read）：
     * T1: SELECT * FROM accounts WHERE balance > 1000; -- 10 条
     * T2: INSERT INTO accounts VALUES (100, 'Bob', 2000); COMMIT;
     * T1: SELECT * FROM accounts WHERE balance > 1000; -- 11 条
     */
}
```

### MySQL 隔离级别

```java
/**
 * MySQL 隔离级别配置
 */
public class MySQLIsolation {
    // 查看当前隔离级别
    /*
     * SELECT @@transaction_isolation;
     */
    
    // MySQL 5.7 默认：REPEATABLE-READ
    // MySQL 8.0 默认：READ-COMMITTED
    
    // 设置隔离级别
    /*
     * SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
     * 
     * 或在配置文件中：
     * transaction-isolation = READ-COMMITTED
     */
}
```

## 📖 MVCC 和锁

### 隔离级别实现

```java
/**
 * 隔离级别实现方式
 */
public class IsolationImpl {
    // READ UNCOMMITTED
    /*
     * 不使用 MVCC
     * 读取最新数据，包括未提交的数据
     */
    
    // READ COMMITTED
    /*
     * 使用 MVCC
     * 每次 SELECT 创建新的 Read View
     * 读取已提交的数据
     */
    
    // REPEATABLE READ
    /*
     * 使用 MVCC
     * 首次 SELECT 创建 Read View
     * 后续使用同一个 Read View
     * 解决不可重复读
     * 
     * InnoDB：next-key lock 解决幻读
     */
    
    // SERIALIZABLE
    /*
     * 不使用 MVCC
     * 所有 SELECT 自动加锁
     * 完全串行执行
     */
}
```

### 锁机制

```java
/**
 * 锁分类
 */
public class LockTypes {
    // 按粒度
    /*
     * 表级锁：开销小，加锁快，冲突高
     * 行级锁：开销大，加锁慢，冲突低
     * 页级锁：介于表级和行级之间
     */
    
    // 按类型
    /*
     * 共享锁（S锁）：SELECT ... LOCK IN SHARE MODE
     * 排他锁（X锁）：SELECT ... FOR UPDATE
     * 
     * 意向锁：表锁和行锁的兼容性标记
     * - IS：意向共享锁
     * - IX：意向排他锁
     */
    
    // 行锁实现
    /*
     * Record Lock：记录锁，锁单行
     * Gap Lock：间隙锁，锁范围（解决幻读）
     * Next-Key Lock：记录锁 + 间隙锁
     */
}
```

## 📖 面试真题

### Q1: MySQL 默认隔离级别？

**答：** MySQL 5.7 默认是 REPEATABLE READ，MySQL 8.0 默认是 READ COMMITTED。

### Q2: 什么是幻读？如何解决？

**答：** 幻读是指在事务中，相同的查询条件两次查询结果不同（因为其他事务插入了新数据）。InnoDB 使用 Next-Key Lock（记录锁+间隙锁）解决幻读。

### Q3: READ COMMITTED 下的 MVCC 原理？

**答：** 每次 SELECT 都创建新的 Read View，通过比较 trx_id 判断可见性。而 REPEATABLE READ 只在事务开始时创建一次 Read View。

---

**⭐ 重点：理解隔离级别是理解并发控制的基础，也是常考点**