# MySQL 死锁分析

> 死锁是并发环境下的常见问题

## 🎯 面试重点

- 死锁的产生原因
- 如何避免死锁
- 死锁的检测和处理

## 📖 死锁产生

### 什么是死锁？

```java
/**
 * 死锁：两个或多个事务相互等待对方释放锁
 * 
 * 经典场景：
 * T1: 持有 A 锁，等待 B 锁
 * T2: 持有 B 锁，等待 A 锁
 */
public class DeadlockExample {
    // 示例
    /*
     * T1: START TRANSACTION;
     * T1: UPDATE accounts SET balance=balance-100 WHERE id=1;  -- 获取 id=1 锁
     * 
     * T2: START TRANSACTION;
     * T2: UPDATE accounts SET balance=balance-100 WHERE id=2;  -- 获取 id=2 锁
     * 
     * T1: UPDATE accounts SET balance=balance+100 WHERE id=2;  -- 等待 id=2 锁
     * T2: UPDATE accounts SET balance=balance+100 WHERE id=1;  -- 等待 id=1 锁
     * 
     * 死锁！
     */
}
```

### 死锁原因

```java
/**
 * 死锁产生的必要条件：
 * 
 * 1. 互斥条件
 *    - 资源一次只能被一个事务持有
 * 
 * 2. 占有并等待
 *    - 事务持有资源的同时等待其他资源
 * 
 * 3. 不可抢占条件
 *    - 资源不能被强制从持有者手中抢夺
 * 
 * 4. 循环等待条件
 *    - 形成等待链
 */
public class DeadlockCauses {}
```

## 📖 避免死锁

### 预防策略

```java
/**
 * 死锁预防
 */
public class DeadlockPrevention {
    // 1. 统一加锁顺序
    /*
     * 所有事务按相同顺序获取锁
     * 
     * T1: UPDATE accounts SET ... WHERE id=1;
     * T2: UPDATE accounts SET ... WHERE id=1;
     * 
     * 避免：T1 先锁 id=1，再锁 id=2
     *      T2 先锁 id=2，再锁 id=1
     */
    
    // 2. 降低隔离级别
    /*
     * READ COMMITTED 减少锁持有时间
     */
    
    // 3. 使用乐观锁
    /*
     * UPDATE accounts 
     * SET balance = balance - 100 
     * WHERE id = 1 AND balance >= 100;
     */
    
    // 4. 减小事务粒度
    /*
     * 只在需要时加锁
     * 尽快提交事务
     */
}
```

### 检测和处理

```java
/**
 * 死锁检测和处理
 */
public class DeadlockHandling {
    // MySQL 死锁检测
    /*
     * SHOW ENGINE INNODB STATUS;
     * 
     * LATEST DETECTED DEADLOCK
     * ...
     */
    
    // 死锁超时
    /*
     * innodb_lock_wait_timeout = 50
     * 默认 50 秒超时
     * 
     * 超时后自动回滚
     */
    
    // 主动检测
    /*
     * SELECT * FROM information_schema.INNODB_TRX;
     * SELECT * FROM information_schema.INNODB_LOCKS;
     * SELECT * FROM information_schema.INNODB_LOCK_WAITS;
     */
}
```

### 监控和优化

```java
/**
 * 死锁监控和优化
 */
public class DeadlockMonitor {
    // 打开慢查询日志
    /*
     * log_queries_not_using_indexes = 1
     */
    
    // 分析死锁日志
    /*
     * 1. 找到参与死锁的 SQL
     * 2. 分析锁等待顺序
     * 3. 优化 SQL 和索引
     */
    
    // 常见优化方案
    /*
     * 1. 添加合适的索引，减少锁范围
     * 2. 拆分大事务为小事务
     * 3. 减少并发冲突
     */
}
```

## 📖 面试真题

### Q1: 如何避免死锁？

**答：**
1. 统一加锁顺序
2. 降低事务隔离级别
3. 使用乐观锁
4. 减小事务粒度
5. 添加合适的索引

### Q2: 发生死锁后如何处理？

**答：**
1. 查看死锁日志：`SHOW ENGINE INNODB STATUS`
2. 分析参与死锁的事务和 SQL
3. 优化 SQL，添加索引
4. 调整事务隔离级别或加锁顺序

---

**⭐ 重点：死锁是生产环境常见问题，需要掌握预防和排查方法**