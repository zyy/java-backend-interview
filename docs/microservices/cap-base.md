# CAP 理论与 BASE 理论

> 分布式系统的基石，面试必问

## 🎯 面试重点

- CAP 理论的理解和三选二的误区
- CAP 在不同场景下的选择
- BASE 理论的核心思想
- 实际系统中的权衡

## 📖 CAP 理论

### 什么是 CAP？

```java
/**
 * CAP 理论由 Eric Brewer 提出：
 * 
 * C (Consistency) - 一致性
 *   所有节点在同一时刻看到相同的数据
 *   每次读取都能获取到最近写入的值
 * 
 * A (Availability) - 可用性
 *   每个请求都能在有限时间内得到响应
 *   响应该是成功的（非错误）
 * 
 * P (Partition Tolerance) - 分区容错性
 *   系统在网络分区的情况下仍能继续运行
 *   即使消息丢失、延迟也能正常工作
 */
public class CAPTheory {
    // CAP 核心：分布式系统无法同时满足 CAP 三个特性
    // 只能满足其中两个
    
    /*
     * 组合选择：
     * CA: 单点系统，不存在网络分区（实际不存在）
     * CP: 优先保证一致性，牺牲可用性（如 Zookeeper、HBase）
     * AP: 优先保证可用性，牺牲一致性（如 Cassandra、Eureka）
     */
}
```

### CAP 三选二的误区

```java
/**
 * 常见误解：三分法
 * 实际：P 是必然发生的，不是可选的
 * 
 * 正确理解：
 * - 网络分区 P 是必然发生的
 * - 发生 P 时，只能在 C 和 A 之间选择
 * - 没有分区时，可以同时满足 CAP
 */
public class CAPMisunderstanding {
    /*
     * 分区发生前：系统可以同时满足 CAP
     * 
     *     正常状态
     *    ┌─────────┐
     *    │ C + A + P│ ← 可以同时满足
     *    └─────────┘
     *          ↓ 分区发生
     *    ┌─────────┐
     *    │ C + P   │  或  │ A + P  │
     *    └─────────┘      └─────────┘
     *     牺牲可用性      牺牲一致性
     */
}
```

### 各组合的典型系统

```java
/**
 * CP 系统（一致性优先）
 * - Zookeeper：CP，选举期间不可用
 * - HBase：CP，保证数据一致性
 * - Redis：CP，保证数据一致
 * - Etcd：CP，分布式协调
 *
 * AP 系统（可用性优先）  
 * - Cassandra：AP，最终一致性
 * - Eureka：AP，服务发现
 * - Amazon Dynamo：AP
 *
 * 传统数据库（CA）
 * - 单点 MySQL
 * - 单点 PostgreSQL
 */
public class CAPSystems {
    // CP 系统示例：Zookeeper
    // Zookeeper 保证一致性，但在选举 Leader 时不可用
    
    // AP 系统示例：Cassandra
    // Cassandra 保证高可用，但数据可能暂时不一致
}
```

### 实际案例分析

```java
/**
 * 案例1：订单系统（CP vs AP 如何选择？）
 */
public class OrderSystemExample {
    /*
     * 场景：用户下单
     * 
     * CP 选择（强一致性）：
     * - 库存扣减必须立即成功
     * - 库存不足时立即返回失败
     * - 适合高价值商品
     * 
     * AP 选择（最终一致性）：
     * - 允许短暂超卖（后续补偿）
     * - 立即返回成功
     * - 适合秒杀场景
     */
}

/**
 * 案例2：服务注册中心
 */
public class ServiceRegistryExample {
    /*
     * Eureka（AP）：
     * - 服务可以随时注册和发现
     * - 即使部分节点故障，服务仍可用
     * - 可能返回过期的服务地址
     * 
     * Zookeeper（CP）：
     * - 强一致性保证
     * - 选举期间服务不可用
     * - 适合配置管理
     */
}
```

## 📖 BASE 理论

### 什么是 BASE？

```java
/**
 * BASE 理论是对 CAP 中 AP 方案的补充：
 * 
 * BA (Basically Available) - 基本可用
 *   允许系统在故障时降级保证核心功能可用
 * 
 * S (Soft State) - 软状态
 *   允许系统数据存在中间状态，不要求强一致
 * 
 * E (Eventually Consistent) - 最终一致性
 *   系统在一段时间后达到一致状态
 */
public class BASETheroy {
    /*
     * BASE 核心思想：
     * 不追求强一致，而是接受最终一致
     * 通过牺牲实时性换取系统可用性
     * 
     * 适合场景：
     * - 互联网应用
     * - 高并发分布式系统
     * - 对一致性要求不严格的业务
     */
}
```

### BASE vs CAP

```java
/**
 * CAP 和 BASE 的关系：
 * 
 * CAP：
 * - 理论模型
 * - 强调强一致
 * - 同一时刻的确定性
 * 
 * BASE：
 * - 实践指导
 * - 接受最终一致
 * - 允许过程不确定
 */
public class CAPvsBASE {
    /*
     * CAP 理论说：不能同时满足 CAP
     * 
     * BASE 解决方案：
     * - 接受 A + P，在一定时间后达到 C
     * - 通过补偿机制实现最终一致性
     * 
     * 实际实现：
     * 1. 记录事务日志
     * 2. 定时任务补偿
     * 3. 消息队列可靠投递
     * 4. TCC 分布式事务
     */
}
```

### BASE 实践模式

```java
/**
 * 1. 基本可用（Basically Available）
 */
public class BasicAvailable {
    // 降级策略示例
    public interface OrderService {
        // 正常情况
        OrderResult createOrder(Order order);
        
        // 降级情况
        default OrderResult createOrderFallback(Order order) {
            // 返回排队号码，让用户稍后查询
            return OrderResult.queue("系统繁忙，请稍后查询订单状态");
        }
    }
}

/**
 * 2. 软状态（Soft State）
 */
public class SoftStateExample {
    // 订单状态流转
    enum OrderStatus {
        PENDING,      // 待处理（软状态）
        CONFIRMED,    // 已确认
        SHIPPED,      // 已发货
        COMPLETED     // 已完成
    }
    // 状态可以中间停留，不要求立即一致
}

/**
 * 3. 最终一致性（Eventually Consistent）
 */
public class EventuallyConsistent {
    // 实现方式：消息队列 + 定时任务
    
    // 方式1：消息可靠投递
    // 发送消息 -> 消息表 -> 消费成功 -> 删除消息
    
    // 方式2：定时任务补偿
    // 定时扫描未完成的操作 -> 重试
    
    // 方式3：TCC 事务
    // Try -> Confirm -> Cancel
}
```

## 📖 分布式事务方案

### 2PC（两阶段提交）

```java
/**
 * 2PC (Two Phase Commit)
 * 
 * 阶段1：准备阶段（Prepare）
 *   - 协调者向所有参与者发送 Prepare 请求
 *   - 参与者执行事务并锁定资源
 *   - 参与者返回成功/失败
 * 
 * 阶段2：提交阶段（Commit）
 *   - 协调者收到所有成功响应
 *   - 向所有参与者发送 Commit 请求
 *   - 参与者提交事务并释放资源
 * 
 * 问题：
 * - 同步阻塞
 * - 单点故障
 * - 数据不一致风险
 */
public class TwoPhaseCommit {
    // 实现：Spring JTA、Atomikos
}
```

### TCC（补偿事务）

```java
/**
 * TCC (Try-Confirm-Cancel)
 * 
 * Try：预留资源
 * Confirm：确认执行
 * Cancel：取消预留
 * 
 * 优点：
 * - 不阻塞
 * - 最终一致
 * 
 * 缺点：
 * - 侵入性强
 * - 需要编写三个接口
 */
public class TCCExample {
    // Try：冻结库存
    // Confirm：扣减库存
    // Cancel：解冻库存
}
```

### 可靠消息最终一致

```java
/**
 * 可靠消息最终一致方案
 * 
 * 1. 本地消息表
 *    - 发消息前先存库
 *    - 定时重试发送
 *    - 消费成功后删除
 * 
 * 2. 消息事务
 *    - RocketMQ 事务消息
 *    - 半消息机制
 */
public class ReliableMessage {
    // RocketMQ 事务消息示例
    /*
     * 1. 发送半消息
     * 2. 执行本地事务
     * 3. 提交或回滚
     * 4. 消费者消费
     */
}
```

## 📖 面试真题

### Q1: CAP 理论中为什么 P 是必须的？

**答：** 网络分区在分布式系统中是必然发生的（网络抖动、机器故障等）。CAP 理论描述的是在发生网络分区时，系统必须在 C 和 A 之间做出选择。因此 P 不是可选项，而是必须接受的现实。

### Q2: 如何选择 CP 还是 AP？

**答：** 
- 对一致性要求高的场景（金融、库存）→ CP
- 对可用性要求高的场景（秒杀、社交）→ AP
- 可以根据业务容错能力灵活选择

### Q3: BASE 理论的核心？

**答：** 
- 基本可用：允许降级，但核心功能可用
- 软状态：允许数据存在中间状态
- 最终一致：系统在一段时间后达到一致状态

### Q4: 分布式事务解决方案？

**答：**
- 2PC：强一致，但有阻塞问题
- TCC：性能好，但侵入性强
- 消息队列：最终一致，适合高并发
- Saga：长流程事务

---

**⭐ 重点：CAP 和 BASE 是分布式系统的核心理论，必须深入理解并能在实际场景中应用**