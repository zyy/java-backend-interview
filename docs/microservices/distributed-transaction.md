---
layout: default
title: 分布式事务解决方案
---

# 分布式事务解决方案

> 分布式事务是微服务架构的核心难题，面试必考

## 🎯 面试重点

- ACID vs CAP vs BASE 理论
- 2PC、3PC 的原理与缺陷
- TCC 补偿事务的实现
- 本地消息表与可靠消息最终一致
- Saga 长事务编排
- Seata 框架原理

---

## 📖 一、理论基础

### 1.1 ACID vs CAP vs BASE

| 特性 | ACID | CAP | BASE |
|-----|------|-----|------|
| **适用场景** | 单体数据库 | 分布式系统 | 分布式系统 |
| **一致性** | 强一致 | 分区时选择 CP 或 AP | 最终一致 |
| **可用性** | 高 | 分区时权衡 | 高 |
| **核心思想** | 事务完整性 | 分区容错下二选一 | 基本可用 + 软状态 + 最终一致 |

**关系**：
```
ACID：传统数据库，强一致性
  ↓
CAP：分布式系统理论，分区时必须选择 CP 或 AP
  ↓
BASE：CAP 的实践，AP 方案的延伸，追求最终一致
```

### 1.2 分布式事务的挑战

```
服务 A（订单）                    服务 B（库存）
   │                                  │
   ├── 1. 创建订单 ──────────────────▶│
   │                                  │
   ├── 2. 扣减库存 ──────────────────▶│
   │         （网络超时？）            │
   │                                  │
   ├── 3. 扣减成功？失败？未知？      │
   │                                  │
   └── 4. 如何回滚？如何保证一致？    │
```

**核心问题**：
1. **网络不可靠**：请求可能丢失、延迟、重复
2. **数据一致性**：多个服务数据如何保持一致
3. **故障恢复**：部分成功时如何回滚或补偿

---

## 📖 二、2PC（两阶段提交）

### 2.1 原理

```
协调者（Coordinator）              参与者（Participants）
   │                                  │
   │-------- 1. Prepare 请求 --------▶│
   │                                  │
   │◀------- 2. Prepare 响应 --------│
   │    （Yes/No）                    │
   │                                  │
   │-------- 3. Commit 请求 --------▶│  （如果全部 Yes）
   │                                  │
   │◀------- 4. Commit 响应 --------│
```

**阶段一：Prepare**
1. 协调者向所有参与者发送 Prepare 请求
2. 参与者执行本地事务，锁定资源，写 Undo/Redo 日志
3. 参与者返回 Yes（成功）或 No（失败）

**阶段二：Commit/Rollback**
- 全部 Yes → 发送 Commit 请求，参与者提交事务
- 任一 No → 发送 Rollback 请求，参与者回滚事务

### 2.2 实现示例

```java
@Service
public class OrderService {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private InventoryFeignClient inventoryClient;
    
    @Autowired
    private PaymentFeignClient paymentClient;
    
    // 2PC 协调者
    public void createOrderWith2PC(OrderRequest request) {
        // 阶段一：Prepare
        boolean orderPrepared = orderRepository.prepare(request);
        boolean inventoryPrepared = inventoryClient.prepare(request.getSkuId(), request.getQuantity());
        boolean paymentPrepared = paymentClient.prepare(request.getUserId(), request.getAmount());
        
        // 阶段二：Commit 或 Rollback
        if (orderPrepared && inventoryPrepared && paymentPrepared) {
            orderRepository.commit();
            inventoryClient.commit();
            paymentClient.commit();
        } else {
            orderRepository.rollback();
            inventoryClient.rollback();
            paymentClient.rollback();
            throw new DistributedTransactionException("事务回滚");
        }
    }
}
```

### 2.3 缺陷

| 问题 | 说明 |
|-----|------|
| **同步阻塞** | Prepare 阶段锁定资源，其他事务等待 |
| **单点故障** | 协调者宕机，参与者无法完成事务 |
| **数据不一致** | 协调者发送 Commit 后宕机，部分参与者未收到 |
| **性能差** | 两次网络往返，延迟高 |

**结论**：2PC 适合对一致性要求极高、并发量低的场景（如金融核心系统），互联网高并发场景很少使用。

---

## 📖 三、3PC（三阶段提交）

### 3.1 改进点

在 2PC 基础上增加 CanCommit 阶段，减少阻塞时间：

```
阶段一：CanCommit（预检查）
  协调者询问参与者是否可以执行（不锁定资源）
  
阶段二：PreCommit（预提交）
  参与者锁定资源，写日志
  
阶段三：DoCommit（正式提交）
  提交或回滚
```

### 3.2 优缺点

- **优点**：CanCommit 阶段不锁定资源，减少阻塞
- **缺点**：实现复杂，网络分区时仍可能不一致

**实际应用**：3PC 理论意义大于实践，生产中很少使用。

---

## 📖 四、TCC（Try-Confirm-Cancel）

### 4.1 原理

TCC 是业务层面的 2PC，将每个操作拆分为三个阶段：

| 阶段 | 操作 | 说明 |
|-----|------|------|
| **Try** | 预留资源 | 执行业务检查，预留必要资源 |
| **Confirm** | 确认执行 | 真正执行业务（Try 成功） |
| **Cancel** | 取消回滚 | 释放预留资源（Try 失败） |

```
订单服务                          库存服务
   │                                │
   ├── Try：创建订单（状态：待确认）──▶│
   │                                │
   ├── Try：冻结库存 ────────────────▶│
   │                                │
   │◀──── 全部 Try 成功 ─────────────│
   │                                │
   ├── Confirm：确认订单 ────────────▶│
   │                                │
   └── Confirm：扣减冻结库存 ────────▶│
```

### 4.2 实现示例

```java
@Service
public class OrderTccService {
    
    @Autowired
    private OrderTccAction orderTccAction;
    
    @Autowired
    private InventoryTccAction inventoryTccAction;
    
    @GlobalTransactional  // Seata 注解
    public void createOrder(OrderRequest request) {
        // Try 阶段
        boolean orderTry = orderTccAction.tryCreateOrder(request);
        boolean inventoryTry = inventoryTccAction.tryDeduct(request.getSkuId(), request.getQuantity());
        
        if (!orderTry || !inventoryTry) {
            throw new BusinessException("资源不足");
        }
        
        // Confirm 由框架自动调用（或业务代码显式调用）
        // 如果 Confirm 失败，不断重试
    }
}

@Component
public class InventoryTccAction {
    
    @Autowired
    private InventoryRepository inventoryRepository;
    
    @Autowired
    private InventoryFreezeRepository freezeRepository;
    
    // Try：冻结库存
    public boolean tryDeduct(String skuId, int quantity) {
        Inventory inventory = inventoryRepository.findBySkuId(skuId);
        
        // 检查库存
        if (inventory.getAvailable() < quantity) {
            return false;
        }
        
        // 冻结库存
        inventory.setAvailable(inventory.getAvailable() - quantity);
        inventory.setFrozen(inventory.getFrozen() + quantity);
        inventoryRepository.save(inventory);
        
        // 记录冻结记录（用于幂等和回滚）
        freezeRepository.save(new InventoryFreeze(skuId, quantity));
        
        return true;
    }
    
    // Confirm：确认扣减
    public boolean confirmDeduct(String skuId, int quantity) {
        Inventory inventory = inventoryRepository.findBySkuId(skuId);
        
        // 扣减冻结库存
        inventory.setFrozen(inventory.getFrozen() - quantity);
        inventoryRepository.save(inventory);
        
        // 删除冻结记录
        freezeRepository.deleteBySkuId(skuId);
        
        return true;
    }
    
    // Cancel：释放冻结
    public boolean cancelDeduct(String skuId, int quantity) {
        Inventory inventory = inventoryRepository.findBySkuId(skuId);
        
        // 释放冻结库存
        inventory.setAvailable(inventory.getAvailable() + quantity);
        inventory.setFrozen(inventory.getFrozen() - quantity);
        inventoryRepository.save(inventory);
        
        // 删除冻结记录
        freezeRepository.deleteBySkuId(skuId);
        
        return true;
    }
}
```

### 4.3 TCC 注意事项

**幂等性**：
```java
// Confirm 和 Cancel 必须保证幂等（可能重复调用）
public boolean confirmDeduct(String skuId, int quantity) {
    // 检查是否已处理
    if (freezeRepository.findBySkuId(skuId) == null) {
        return true;  // 已处理，直接返回
    }
    // 执行业务
}
```

**空回滚**：
```java
// Try 超时未执行，Cancel 先执行
public boolean cancelDeduct(String skuId, int quantity) {
    // 检查是否有冻结记录
    if (freezeRepository.findBySkuId(skuId) == null) {
        // 空回滚，记录回滚状态，防止后续 Try 执行
        idempotentRepository.recordCancel(skuId);
        return true;
    }
    // 正常回滚
}
```

**悬挂**：
```java
// Cancel 先执行，Try 后到达
public boolean tryDeduct(String skuId, int quantity) {
    // 检查是否已回滚
    if (idempotentRepository.isCancelled(skuId)) {
        return false;  // 拒绝执行
    }
    // 正常执行
}
```

### 4.4 TCC 优缺点

| 优点 | 缺点 |
|-----|------|
| 无全局锁，性能高 | 业务侵入性强，需实现 3 个接口 |
| 数据最终一致 |  Confirm/Cancel 需保证幂等 |
| 适合长事务 |  开发成本高 |

---

## 📖 五、本地消息表（可靠消息最终一致）

### 5.1 原理

将分布式事务拆分为本地事务 + 消息投递：

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────────┐
│   业务服务       │────▶│   消息表     │────▶│   消息队列       │
│（订单服务）      │     │（本地事务）   │     │（RocketMQ）     │
└─────────────────┘     └─────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   下游服务       │
                                               │（库存服务）      │
                                               └─────────────────┘
```

**核心思想**：
1. 业务操作和消息记录在同一个本地事务中
2. 定时任务扫描消息表，投递到 MQ
3. 下游服务消费消息并执行业务
4. 失败消息重试，保证最终一致

### 5.2 实现示例

```java
@Service
public class OrderServiceWithMessageTable {
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Autowired
    private MessageRepository messageRepository;
    
    @Transactional
    public void createOrder(OrderRequest request) {
        // 1. 创建订单
        Order order = new Order();
        order.setUserId(request.getUserId());
        order.setAmount(request.getAmount());
        order.setStatus(OrderStatus.CREATED);
        orderRepository.save(order);
        
        // 2. 记录消息（同一事务）
        Message message = new Message();
        message.setTopic("order_created");
        message.setBody(JsonUtils.toJson(new OrderCreatedEvent(order.getId())));
        message.setStatus(MessageStatus.PENDING);
        messageRepository.save(message);
        
        // 事务提交后，订单和消息同时成功或同时失败
    }
}

@Component
public class MessageSender {
    
    @Autowired
    private MessageRepository messageRepository;
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    // 定时扫描，每 5 秒执行一次
    @Scheduled(fixedDelay = 5000)
    public void sendPendingMessages() {
        List<Message> pendingMessages = messageRepository
            .findByStatusAndRetryLessThan(MessageStatus.PENDING, 3);
        
        for (Message message : pendingMessages) {
            try {
                SendResult result = rocketMQTemplate.syncSend(
                    message.getTopic(), 
                    message.getBody()
                );
                
                if (result.getSendStatus() == SendStatus.SEND_OK) {
                    message.setStatus(MessageStatus.SENT);
                    messageRepository.save(message);
                }
            } catch (Exception e) {
                message.setRetryCount(message.getRetryCount() + 1);
                messageRepository.save(message);
            }
        }
    }
}

@Component
@RocketMQMessageListener(topic = "order_created", consumerGroup = "inventory_consumer")
public class InventoryConsumer implements RocketMQListener<OrderCreatedEvent> {
    
    @Autowired
    private InventoryService inventoryService;
    
    @Override
    public void onMessage(OrderCreatedEvent event) {
        // 幂等检查
        if (inventoryService.isProcessed(event.getOrderId())) {
            return;
        }
        
        // 扣减库存
        inventoryService.deduct(event.getOrderId());
        
        // 记录已处理
        inventoryService.markProcessed(event.getOrderId());
    }
}
```

### 5.3 优缺点

| 优点 | 缺点 |
|-----|------|
| 实现简单，无外部依赖 | 最终一致，有延迟 |
| 消息可靠投递 | 需维护消息表，定时任务 |
| 适合异步场景 | 消费端需保证幂等 |

---

## 📖 六、Saga 模式

### 6.1 原理

将长事务拆分为多个本地事务，每个事务有对应的补偿操作：

```
订单创建 ──▶ 库存扣减 ──▶ 支付 ──▶ 物流
   │            │          │
   └── 取消订单 ◀── 恢复库存 ◀── 退款
```

**两种实现方式**：
- **编排式（Choreography）**：各服务完成本地事务后，发送事件触发下一个服务
- **编排式（Orchestration）**：由 Saga 协调器统一调度各服务

### 6.2 实现示例（编排式）

```java
@Service
public class SagaOrchestrator {
    
    @Autowired
    private OrderService orderService;
    
    @Autowired
    private InventoryService inventoryService;
    
    @Autowired
    private PaymentService paymentService;
    
    public void executeOrderSaga(OrderRequest request) {
        String sagaId = generateSagaId();
        
        try {
            // Step 1: 创建订单
            Long orderId = orderService.createOrder(request);
            recordSagaStep(sagaId, "CREATE_ORDER", orderId);
            
            // Step 2: 扣减库存
            boolean inventoryResult = inventoryService.deduct(request.getSkuId(), request.getQuantity());
            if (!inventoryResult) {
                throw new InventoryInsufficientException();
            }
            recordSagaStep(sagaId, "DEDUCT_INVENTORY", null);
            
            // Step 3: 支付
            boolean paymentResult = paymentService.pay(request.getUserId(), request.getAmount());
            if (!paymentResult) {
                throw new PaymentFailedException();
            }
            recordSagaStep(sagaId, "PAY", null);
            
            // Saga 完成
            completeSaga(sagaId);
            
        } catch (Exception e) {
            // 执行补偿
            compensateSaga(sagaId);
        }
    }
    
    private void compensateSaga(String sagaId) {
        List<SagaStep> steps = getSagaSteps(sagaId);
        
        // 反向执行补偿
        for (int i = steps.size() - 1; i >= 0; i--) {
            SagaStep step = steps.get(i);
            
            switch (step.getStepName()) {
                case "PAY":
                    paymentService.refund(step.getContext());
                    break;
                case "DEDUCT_INVENTORY":
                    inventoryService.rollbackDeduct(step.getContext());
                    break;
                case "CREATE_ORDER":
                    orderService.cancelOrder(step.getContext());
                    break;
            }
        }
    }
}
```

### 6.3 优缺点

| 优点 | 缺点 |
|-----|------|
| 适合长事务、业务流程复杂 | 补偿逻辑复杂 |
| 无全局锁，并发性能好 | 补偿可能失败，需人工介入 |
| 可视化流程 |  最终一致，有中间状态 |

---

## 📖 七、Seata 框架

### 7.1 架构

```
┌─────────────────────────────────────────┐
│              Seata Server                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ TC      │  │ TM      │  │ RM      │ │
│  │ 事务协调器│  │ 事务管理器│  │ 资源管理器│ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
   维护全局事务    开启/提交/回滚   管理分支事务
```

**三种模式**：
- **AT 模式**：自动补偿，基于 SQL 解析（类似 TCC，但自动实现）
- **TCC 模式**：手动实现 Try/Confirm/Cancel
- **Saga 模式**：状态机引擎编排长事务
- **XA 模式**：基于 XA 协议的强一致性

### 7.2 AT 模式原理

```
业务应用                          Seata TC
   │                                │
   ├── 1. 注册分支事务 ──────────────▶│
   │                                │
   ├── 2. 执行业务 SQL（UPDATE）      │
   │                                │
   ├── 3. 解析 SQL，生成前后镜像      │
   │   （undo_log 表记录）            │
   │                                │
   ├── 4. 提交本地事务 ──────────────▶│
   │                                │
   ├── 5. 全局提交/回滚 ─────────────▶│
   │                                │
   └── 6. 成功：删除 undo_log         │
       失败：根据 undo_log 回滚       │
```

### 7.3 使用示例

```java
// 启动类
@SpringBootApplication
@EnableAutoDataSourceProxy  // Seata 数据源代理
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}

// 业务代码
@Service
public class OrderService {
    
    @Autowired
    private OrderMapper orderMapper;
    
    @Autowired
    private InventoryFeignClient inventoryFeignClient;
    
    @Autowired
    private AccountFeignClient accountFeignClient;
    
    @GlobalTransactional(name = "create-order", rollbackFor = Exception.class)
    public void createOrder(Order order) {
        // 1. 创建订单
        orderMapper.insert(order);
        
        // 2. 扣减库存
        inventoryFeignClient.deduct(order.getSkuId(), order.getCount());
        
        // 3. 扣减账户余额
        accountFeignClient.debit(order.getUserId(), order.getMoney());
        
        // 任意步骤异常，自动回滚
    }
}
```

---

## 📖 八、方案对比与选型

| 方案 | 一致性 | 性能 | 复杂度 | 适用场景 |
|-----|-------|------|-------|---------|
| **2PC** | 强一致 | 低 | 低 | 金融核心，低并发 |
| **3PC** | 强一致 | 中 | 高 | 理论多，实践少 |
| **TCC** | 最终一致 | 高 | 高 | 电商、高并发 |
| **本地消息表** | 最终一致 | 高 | 中 | 异步场景 |
| **Saga** | 最终一致 | 高 | 高 | 长事务、复杂流程 |
| **Seata AT** | 最终一致 | 高 | 低 | 快速接入，推荐 |

**选型建议**：
- 强一致性 + 低并发 → 2PC/XA
- 高并发 + 短事务 → TCC / Seata AT
- 异步场景 → 本地消息表 / RocketMQ 事务消息
- 长事务 + 复杂流程 → Saga

---

## 📖 九、面试真题

### Q1: 分布式事务和本地事务有什么区别？

**答：**

| 特性 | 本地事务 | 分布式事务 |
|-----|---------|-----------|
| 参与者 | 单个数据库 | 多个服务/数据库 |
| ACID 保障 | 数据库保证 | 需额外机制保证 |
| 实现方式 | BEGIN/COMMIT/ROLLBACK | 2PC、TCC、Saga 等 |
| 性能 | 高 | 较低（网络开销） |
| 复杂度 | 低 | 高 |

### Q2: 2PC 有什么问题？为什么互联网很少用？

**答：** 2PC 的主要问题：

1. **同步阻塞**：Prepare 阶段锁定资源，其他事务等待
2. **单点故障**：协调者宕机，参与者无法完成事务
3. **数据不一致**：协调者发送 Commit 后宕机，部分参与者未收到
4. **性能差**：两次网络往返，延迟高

互联网场景高并发，2PC 的阻塞和性能问题无法接受，通常采用最终一致性方案（TCC、消息队列）。

### Q3: TCC 和 2PC 的区别？

**答：**

| 特性 | 2PC | TCC |
|-----|-----|-----|
| 层面 | 数据库层面 | 业务层面 |
| 锁 | 数据库锁，长期持有 | 业务预留，无全局锁 |
| 性能 | 低 | 高 |
| 侵入性 | 低 | 高（需实现 3 个接口） |
| 一致性 | 强一致 | 最终一致 |

### Q4: 如何保证消息队列的可靠投递？

**答：**

1. **本地消息表**：业务操作和消息记录在同一个本地事务
2. **RocketMQ 事务消息**：半消息机制，本地事务成功后才投递
3. **消息确认**：消费者处理成功后发送 ACK
4. **重试机制**：失败消息定时重试，超过阈值进死信队列
5. **幂等消费**：消费者保证幂等，防止重复处理

### Q5: Seata AT 模式和 TCC 模式有什么区别？

**答：**

| 特性 | Seata AT | Seata TCC |
|-----|----------|-----------|
| 实现方式 | 自动代理数据源，解析 SQL | 手动实现 Try/Confirm/Cancel |
| 侵入性 | 低（只需注解） | 高（需改业务代码） |
| 性能 | 中（有 SQL 解析开销） | 高 |
| 适用场景 | 快速接入，简单业务 | 复杂业务，性能要求高 |

---

## 📚 延伸阅读

- [Seata 官方文档](https://seata.io/zh-cn/docs/overview/what-is-seata.html)
- [分布式事务原理](https://www.infoq.cn/article/2018p7d2brvomd3*q8x*)
- [RocketMQ 事务消息](https://rocketmq.apache.org/docs/4.x/producer/04transactionmessage/)
- [Saga 模式详解](https://microservices.io/patterns/data/saga.html)
