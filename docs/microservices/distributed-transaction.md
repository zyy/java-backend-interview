---
layout: default
title: 分布式事务
---
# 分布式事务

> 微服务架构下的数据一致性挑战

## 🎯 面试重点

- 分布式事务的解决方案
- 2PC、TCC、消息队列的区别
- 如何选择合适的事务方案

## 📖 分布式事务问题

### 什么是分布式事务？

```java
/**
 * 分布式事务：跨多个服务/数据库的事务操作
 * 
 * 示例：下单服务（订单库）+ 库存服务（库存库）+ 支付服务（支付库）
 * 必须保证要么全部成功，要么全部回滚
 */
public class DistributedTransaction {
    // 传统事务（单机）
    // BEGIN TRANSACTION
    //   UPDATE order SET status='PAID' WHERE id=123;
    //   UPDATE inventory SET count=count-1 WHERE sku='SKU001';
    //   UPDATE account SET balance=balance-100 WHERE userId=456;
    // COMMIT;
    
    // 分布式事务
    // 需要跨三个数据库保证一致性
}
```

### 分布式事务的理论基础

```java
/**
 * CAP 定理：一致性、可用性、分区容错
 * BASE 理论：基本可用、软状态、最终一致
 * 
 * 分布式事务的两种思路：
 * 1. 强一致性：2PC、3PC
 * 2. 最终一致性：TCC、消息队列、Saga
 */
public class TransactionTheory {}
```

## 📖 解决方案

### 1. 2PC（两阶段提交）

```java
/**
 * Two Phase Commit
 * 
 * 阶段1：准备阶段（Prepare）
 * - 协调者向所有参与者发送 Prepare 请求
 * - 参与者执行事务但不提交，返回成功/失败
 * - 锁定资源（行锁、表锁）
 * 
 * 阶段2：提交阶段（Commit/Rollback）
 * - 协调者收到所有成功响应
 * - 发送 Commit 请求
 * - 参与者提交事务
 * - 任一失败则 Rollback
 */
public class TwoPhaseCommit {
    // 问题
    /*
     * 1. 同步阻塞：Prepare 阶段锁定资源，其他事务等待
     * 2. 单点故障：协调者宕机，参与者一直等待
     * 3. 数据不一致：部分 Commit 成功，部分失败
     */
    
    // Spring 实现
    // @EnableTransactionManagement
    // JTA + Atomikos / Seata
}
```

### 2. TCC（Try-Confirm-Cancel）

```java
/**
 * TCC 事务
 * 
 * Try：预留资源（try）
 * - 检查业务可行性
 * - 预留业务资源
 * 
 * Confirm：确认执行（confirm）
 * - 确认预留资源
 * - 执行业务操作
 * 
 * Cancel：取消预留（cancel）
 * - 释放预留资源
 * - 回滚业务操作
 */
public class TCCTransaction {
    // 示例：库存服务
    interface InventoryTCCService {
        // Try: 冻结库存
        boolean tryFreezeStock(String orderId, String sku, int count);
        
        // Confirm: 扣减库存
        boolean confirmDeductStock(String orderId);
        
        // Cancel: 解冻库存
        boolean cancelFreezeStock(String orderId);
    }
    
    /*
     * TCC 与 2PC 的区别：
     * - 2PC 是资源层面的锁定
     * - TCC 是业务层面的预留
     * - TCC 性能更好，但侵入性强
     */
}
```

### 3. 可靠消息最终一致

```java
/**
 * 可靠消息最终一致方案
 * 
 * 核心思想：
 * - 发送消息和本地事务绑定
 * - 消息消费失败重试
 * - 最终达到一致
 */
public class ReliableMessage {
    // 方案1：本地消息表
    // 
    // 1. 业务操作和消息入库在同一事务
    // 2. 定时轮询消息表，发送消息
    // 3. 消费端消费成功后删除消息
    // 4. 定时重试发送失败的消息
    
    // 方案2：RocketMQ 事务消息
    // 
    // 1. 发送半消息（Prepare）
    // 2. 执行本地事务
    // 3. 提交或回滚消息
    // 4. 消费者消费
    
    // 示例
    /*
     * @RocketMQTransactionListener
     * public class OrderTransactionListener implements RocketMQLocalTransactionListener {
     *     
     *     @Override
     *     public RocketMQLocalTransactionState executeLocalTransaction(Message msg, Object arg) {
     *         // 本地事务
     *         orderService.createOrder((Order) arg);
     *         return RocketMQLocalTransactionState.COMMIT;
     *     }
     *     
     *     @Override
     *     public RocketMQLocalTransactionState checkLocalTransaction(Message msg) {
     *         // 检查事务状态
     *         return RocketMQLocalTransactionState.COMMIT;
     *     }
     * }
     */
}
```

### 4. Saga 模式

```java
/**
 * Saga 模式
 * 
 * 思想：将长事务拆分为多个本地事务
 * 每个本地事务都有对应的补偿操作
 * 
 * 正向补偿（继续执行）
 * 反向补偿（回滚）
 */
public class SagaPattern {
    // 示例：订单创建流程
    /*
     * 1. 创建订单（正向）      →  取消订单（补偿）
     * 2. 扣减库存（正向）      →  恢复库存（补偿）
     * 3. 扣减余额（正向）      →  恢复余额（补偿）
     * 4. 发送通知（正向）      →  取消通知（补偿）
     * 
     * 编排方式：
     * - 顺序编排：依次执行各子事务
     * - 并行编排：并行执行独立事务
     */
    
    // Seata 支持 Saga 模式
}
```

## 📖 Seata 框架

```java
/**
 * Seata 分布式事务解决方案
 * 
 * 支持模式：
 * - AT 模式：自动补偿（类似 2PC）
 * - TCC 模式：手动补偿
 * - Saga 模式：状态机编排
 * - XA 模式：强一致性
 */
public class SeataExample {
    // AT 模式（默认）
    // 
    // 1. 解析 SQL，记录前后镜像
    // 2. 执行 SQL
    // 3. 记录反向 SQL
    // 
    // 全局事务 begin
    //   branch transaction
    //     insert/delete/update
    //     undo_log 记录
    // global commit/rollback
    //   删除 undo_log 或 执行 undo_log
    
    // 配置
    /*
     * seata:
     *   tx-service-group: my_test_tx_group
     *   service:
     *     vgroup-mapping:
     *       my_test_tx_group: default
     */
}
```

## 📖 方案对比与选型

```java
/**
 * 分布式事务方案对比
 */
public class TransactionComparison {
    /*
     * | 特性         | 2PC       | TCC       | 消息队列  | Saga     |
     * |--------------|-----------|-----------|-----------|-----------|
     * | 一致性       | 强一致    | 最终一致  | 最终一致  | 最终一致  |
     * | 性能         | 差        | 中        | 好        | 好        |
     * | 侵入性       | 低        | 高        | 中        | 高        |
     * | 复杂度       | 低        | 中        | 中        | 高        |
     * | 适用场景     | 短事务    | 长事务    | 异步消息  | 复杂流程  |
     */
    
    // 选型建议
    /*
     * - 对一致性要求极高 → 2PC / Seata AT
     * - 性能要求高 → TCC / 消息队列
     * - 业务流程复杂 → Saga
     * - 简单场景 → 消息队列最终一致
     */
}
```

## 📖 面试真题

### Q1: 2PC 有什么问题？

**答：**
1. 同步阻塞：Prepare 阶段锁定资源，其他事务等待
2. 单点故障：协调者宕机后参与者无法完成事务
3. 数据不一致：部分提交成功、部分失败

### Q2: TCC 和 2PC 的区别？

**答：**
- 2PC 在数据库层面锁定资源，TCC 在业务层面预留资源
- TCC 性能更好，但需要编写三个接口
- 2PC 是强一致，TCC 是最终一致

### Q3: 如何保证消息不丢失？

**答：**
1. 本地消息表：消息和业务在同一事务，消息表 + 定时重试
2. 消息队列事务：RocketMQ 半消息机制
3. 消费确认：消费者手动 ACK，失败重试
4. 死信队列：多次重试失败后进入死信队列

### Q4: Seata AT 模式原理？

**答：**
1. 解析 SQL，记录前后镜像到 undo_log 表
2. 执行 SQL
3. 全局提交时删除 undo_log，回滚时执行反向 SQL

---

**⭐ 重点：分布式事务是微服务架构的核心难点，理解各方案的优缺点和适用场景**