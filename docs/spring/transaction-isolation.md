# Spring 事务隔离级别

> 数据库事务隔离级别在 Spring 中的配置

## 🎯 面试重点

- Spring 事务隔离级别配置
- 隔离级别与数据库的关系

## 📖 隔离级别配置

### 配置方式

```java
/**
 * Spring 事务隔离级别
 */
public class TransactionIsolationSpring {
    // 1. 注解配置
    /*
     * @Transactional(isolation = Isolation.READ_COMMITTED)
     * public void method() { }
     */
    
    // 2. 传播行为
    /*
     * - REQUIRED：支持当前事务，不存在则创建
     * - REQUIRES_NEW：挂起当前事务，创建新事务
     * - SUPPORTS：支持当前事务，不存在则非事务
     * - NOT_SUPPORTED：挂起当前事务，非事务执行
     * - MANDATORY：必须在事务中执行
     * - NEVER：非事务执行，存在事务抛异常
     * - NESTED：嵌套事务（savepoint）
     */
}
```

## 📖 面试真题

### Q1: @Transactional 失效场景？

**答：** 
- 非 public 方法
- 异常被 catch 吞掉
- 传播行为问题
- 自调用

---

**⭐ 重点：理解事务配置和传播行为**