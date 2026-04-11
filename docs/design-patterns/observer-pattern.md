---
layout: default
title: 观察者模式（Observer Pattern）
---

# 观察者模式（Observer Pattern）：事件驱动架构的核心

> 观察者模式是行为型设计模式的代表，广泛应用于事件驱动架构中

## 一、核心思想

### 1.1 模式定义

观察者模式（Observer Pattern）定义了对象之间的一对多依赖关系，当一个对象状态发生改变时，所有依赖于它的对象都会得到通知并自动更新。

### 1.2 核心角色

```
┌─────────────────────────────────────────────────────────────┐
│                    观察者模式结构图                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐         register/remove                  │
│   │   Subject    │◄──────────────────────────────────────┐  │
│   │  (被观察者)   │                                       │  │
│   └──────┬───────┘                                       │  │
│          │ notify()                                      │  │
│          ▼                                                │  │
│   ┌──────────────┐                                       │  │
│   │   Observer   │◄──────────────────────────────────────┘  │
│   │   (观察者)   │                                          │
│   └──────┬───────┘                                          │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │  Concrete    │    │  Concrete    │    │  Concrete    │  │
│   │  Observer A  │    │  Observer B  │    │  Observer C  │  │
│   └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心组件：**

| 角色 | 职责 | 示例 |
|------|------|------|
| **Subject（主题/被观察者）** | 维护观察者列表，提供注册/移除方法，通知所有观察者 | 订单服务、消息发布者 |
| **Observer（观察者）** | 定义更新接口，接收通知 | 邮件服务、短信服务 |
| **ConcreteSubject** | 具体被观察者，存储状态，状态改变时通知观察者 | 具体订单实现 |
| **ConcreteObserver** | 具体观察者，实现更新逻辑 | 具体邮件发送实现 |

### 1.3 工作流程

```
1. Subject 注册 Observer → 2. Subject 状态改变 → 3. Subject 通知所有 Observer → 4. Observer 执行更新
```

## 二、JDK 内置观察者（已废弃）

### 2.1 基本用法

```java
import java.util.Observable;
import java.util.Observer;

// 被观察者
public class NewsPublisher extends Observable {
    private String latestNews;
    
    public void publishNews(String news) {
        this.latestNews = news;
        setChanged();  // 标记状态已改变
        notifyObservers(news);  // 通知所有观察者
    }
    
    public String getLatestNews() {
        return latestNews;
    }
}

// 观察者
public class NewsSubscriber implements Observer {
    private String name;
    
    public NewsSubscriber(String name) {
        this.name = name;
    }
    
    @Override
    public void update(Observable o, Object arg) {
        System.out.println(name + " 收到新闻: " + arg);
    }
}

// 使用示例
public class ObserverDemo {
    public static void main(String[] args) {
        NewsPublisher publisher = new NewsPublisher();
        
        NewsSubscriber sub1 = new NewsSubscriber("张三");
        NewsSubscriber sub2 = new NewsSubscriber("李四");
        
        publisher.addObserver(sub1);
        publisher.addObserver(sub2);
        
        publisher.publishNews("JDK 21 正式发布！");
    }
}
```

### 2.2 为什么被废弃？

| 问题 | 说明 |
|------|------|
| **设计缺陷** | `Observable` 是类而非接口，限制了扩展性（Java 单继承） |
| **线程不安全** | `notifyObservers()` 方法在遍历观察者列表时没有同步保护 |
| **通知顺序不可控** | 观察者通知顺序依赖于内部集合遍历顺序 |
| **缺乏泛型支持** | API 设计于 Java 1.0，缺乏现代泛型支持 |
| **已被标记 @Deprecated** | Java 9 起标记为废弃，建议使用 `java.beans.PropertyChangeSupport` 或第三方库 |

## 三、Spring 事件机制

### 3.1 ApplicationEvent / ApplicationListener

```java
import org.springframework.context.ApplicationEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

// ==================== 1. 定义事件 ====================
public class OrderCreatedEvent extends ApplicationEvent {
    private final Long orderId;
    private final String userId;
    private final BigDecimal amount;
    private final LocalDateTime createTime;
    
    public OrderCreatedEvent(Object source, Long orderId, String userId, 
                             BigDecimal amount, LocalDateTime createTime) {
        super(source);
        this.orderId = orderId;
        this.userId = userId;
        this.amount = amount;
        this.createTime = createTime;
    }
    
    // Getters...
    public Long getOrderId() { return orderId; }
    public String getUserId() { return userId; }
    public BigDecimal getAmount() { return amount; }
    public LocalDateTime getCreateTime() { return createTime; }
}

// ==================== 2. 传统方式：实现 ApplicationListener ====================
@Component
public class OrderEmailListener implements ApplicationListener<OrderCreatedEvent> {
    
    @Autowired
    private EmailService emailService;
    
    @Override
    public void onApplicationEvent(OrderCreatedEvent event) {
        // 发送订单确认邮件
        emailService.sendOrderConfirmation(
            event.getUserId(), 
            event.getOrderId(), 
            event.getAmount()
        );
    }
}

// ==================== 3. 注解方式：@EventListener（推荐）====================
@Component
public class OrderEventHandlers {
    
    @Autowired
    private SmsService smsService;
    
    @Autowired
    private InventoryService inventoryService;
    
    @Autowired
    private StatisticsService statisticsService;
    
    /**
     * 发送短信通知
     */
    @EventListener
    public void handleOrderCreatedForSms(OrderCreatedEvent event) {
        smsService.sendOrderNotification(
            event.getUserId(),
            "您的订单 " + event.getOrderId() + " 已创建成功"
        );
    }
    
    /**
     * 扣减库存
     */
    @EventListener
    public void handleOrderCreatedForInventory(OrderCreatedEvent event) {
        inventoryService.decreaseStock(event.getOrderId());
    }
    
    /**
     * 更新统计数据
     */
    @EventListener
    public void handleOrderCreatedForStatistics(OrderCreatedEvent event) {
        statisticsService.incrementOrderCount(event.getCreateTime());
        statisticsService.addOrderAmount(event.getAmount());
    }
}
```

### 3.2 @TransactionalEventListener（事务事件监听）

```java
import org.springframework.transaction.event.TransactionalEventListener;
import org.springframework.transaction.event.TransactionPhase;

@Component
public class OrderTransactionalEventHandler {
    
    @Autowired
    private MqProducer mqProducer;
    
    /**
     * 事务提交后发送 MQ 消息
     * 确保数据库操作成功后才发送消息
     */
    @TransactionalEventListener(
        phase = TransactionPhase.AFTER_COMMIT,
        fallbackExecution = true  // 如果没有事务也执行
    )
    public void sendOrderToMq(OrderCreatedEvent event) {
        OrderMessage message = new OrderMessage();
        message.setOrderId(event.getOrderId());
        message.setUserId(event.getUserId());
        message.setAmount(event.getAmount());
        
        mqProducer.sendOrderCreatedMessage(message);
    }
    
    /**
     * 事务回滚时执行补偿操作
     */
    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void handleTransactionRollback(OrderCreatedEvent event) {
        // 记录失败日志，或发送告警
        log.error("订单创建事务回滚，订单ID: {}", event.getOrderId());
    }
    
    /**
     * 事务完成时（无论提交或回滚）
     */
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMPLETION)
    public void handleTransactionCompletion(OrderCreatedEvent event) {
        // 清理资源等操作
    }
}

// 事务阶段说明
public enum TransactionPhase {
    BEFORE_COMMIT,      // 事务提交前
    AFTER_COMMIT,       // 事务提交后（最常用）
    AFTER_ROLLBACK,     // 事务回滚后
    AFTER_COMPLETION    // 事务完成后（提交或回滚）
}
```

### 3.3 @AsyncEventListener（异步事件监听）

```java
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.EnableAsync;

@Configuration
@EnableAsync
public class AsyncConfig {
    
    @Bean("eventAsyncExecutor")
    public Executor eventAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(500);
        executor.setThreadNamePrefix("event-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}

@Component
public class AsyncOrderEventHandler {
    
    /**
     * 异步处理：发送邮件（不需要阻塞主流程）
     */
    @Async("eventAsyncExecutor")
    @EventListener
    public void asyncSendEmail(OrderCreatedEvent event) {
        // 在独立线程中执行
        emailService.sendOrderConfirmation(
            event.getUserId(),
            event.getOrderId(),
            event.getAmount()
        );
    }
    
    /**
     * 异步处理：记录日志
     */
    @Async("eventAsyncExecutor")
    @EventListener
    public void asyncLogOrder(OrderCreatedEvent event) {
        log.info("订单创建事件 - orderId: {}, userId: {}, amount: {}",
            event.getOrderId(), event.getUserId(), event.getAmount());
    }
}
```

### 3.4 事件发布

```java
@Service
public class OrderService {
    
    @Autowired
    private ApplicationEventPublisher eventPublisher;
    
    @Autowired
    private OrderRepository orderRepository;
    
    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        // 1. 保存订单到数据库
        Order order = new Order();
        order.setUserId(request.getUserId());
        order.setAmount(request.getAmount());
        order.setStatus(OrderStatus.CREATED);
        order.setCreateTime(LocalDateTime.now());
        
        orderRepository.save(order);
        
        // 2. 发布订单创建事件
        OrderCreatedEvent event = new OrderCreatedEvent(
            this,
            order.getId(),
            order.getUserId(),
            order.getAmount(),
            order.getCreateTime()
        );
        eventPublisher.publishEvent(event);
        
        return order;
    }
}
```

## 四、Guava EventBus

### 4.1 基本用法

```java
import com.google.common.eventbus.EventBus;
import com.google.common.eventbus.Subscribe;
import com.google.common.eventbus.AllowConcurrentEvents;

// ==================== 1. 定义事件 ====================
public class PaymentSuccessEvent {
    private final String orderId;
    private final String userId;
    private final BigDecimal amount;
    
    public PaymentSuccessEvent(String orderId, String userId, BigDecimal amount) {
        this.orderId = orderId;
        this.userId = userId;
        this.amount = amount;
    }
    
    // Getters...
}

// ==================== 2. 定义订阅者 ====================
public class PaymentEventSubscriber {
    
    /**
     * 普通订阅（同步执行）
     */
    @Subscribe
    public void handlePaymentSuccess(PaymentSuccessEvent event) {
        System.out.println("处理支付成功: orderId=" + event.getOrderId());
        // 发送邮件
    }
    
    /**
     * 允许并发执行（线程安全的方法）
     */
    @Subscribe
    @AllowConcurrentEvents
    public void handlePaymentSuccessConcurrent(PaymentSuccessEvent event) {
        // 可以并发执行的处理逻辑
        updateStatistics(event);
    }
    
    /**
     * 处理异常事件
     */
    @Subscribe
    public void handlePaymentFailure(PaymentFailedEvent event) {
        System.out.println("处理支付失败: orderId=" + event.getOrderId());
        // 发送告警
    }
    
    private void updateStatistics(PaymentSuccessEvent event) {
        // 更新统计
    }
}

// ==================== 3. 使用 EventBus ====================
public class EventBusDemo {
    public static void main(String[] args) {
        // 创建 EventBus（可以指定标识符）
        EventBus eventBus = new EventBus("payment-event-bus");
        
        // 注册订阅者
        PaymentEventSubscriber subscriber = new PaymentEventSubscriber();
        eventBus.register(subscriber);
        
        // 发布事件
        PaymentSuccessEvent event = new PaymentSuccessEvent(
            "ORDER_001", "USER_001", new BigDecimal("199.99")
        );
        eventBus.post(event);
        
        // 注销订阅者
        eventBus.unregister(subscriber);
    }
}
```

### 4.2 AsyncEventBus（异步事件总线）

```java
import com.google.common.eventbus.AsyncEventBus;
import java.util.concurrent.Executors;

public class AsyncEventBusDemo {
    public static void main(String[] args) {
        // 创建异步 EventBus，指定线程池
        AsyncEventBus asyncEventBus = new AsyncEventBus(
            Executors.newFixedThreadPool(10),
            (exception, context) -> {
                // 异常处理
                System.err.println("事件处理异常: " + exception.getMessage());
                System.err.println("事件类型: " + context.getEvent());
                System.err.println("订阅者: " + context.getSubscriber());
                System.err.println("方法: " + context.getSubscriberMethod());
            }
        );
        
        // 注册和发布与 EventBus 相同
        asyncEventBus.register(new PaymentEventSubscriber());
        asyncEventBus.post(new PaymentSuccessEvent("ORDER_001", "USER_001", new BigDecimal("199.99")));
    }
}
```

### 4.3 EventBus 原理

```
┌─────────────────────────────────────────────────────────────┐
│                    EventBus 工作原理                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 注册阶段 (register)                                      │
│     ┌─────────────┐                                         │
│     │ 扫描 @Subscribe │ → 提取 {EventType → [Method]} 映射    │
│     │ 注解的方法    │                                         │
│     └─────────────┘                                         │
│                                                             │
│  2. 发布阶段 (post)                                          │
│     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│     │  接收事件    │ →  │ 查找订阅者   │ →  │ 调用处理方法 │   │
│     │             │    │ (根据类型)   │    │ (反射调用)   │   │
│     └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                             │
│  3. 分发策略                                                │
│     - 同步 EventBus：直接在当前线程执行                      │
│     - AsyncEventBus：提交到线程池异步执行                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 五、实际应用场景

### 5.1 订单创建后多系统联动

```java
@Service
public class OrderCreationService {
    
    @Autowired
    private ApplicationEventPublisher publisher;
    
    @Transactional
    public Order createOrder(OrderRequest request) {
        // 保存订单
        Order order = saveOrder(request);
        
        // 发布事件，触发以下操作：
        // 1. 发送 MQ 消息通知仓库系统
        // 2. 发送邮件给用户
        // 3. 更新统计数据
        // 4. 记录操作日志
        publisher.publishEvent(new OrderCreatedEvent(this, order));
        
        return order;
    }
}

@Component
public class OrderCreatedEventProcessor {
    
    // 1. 发送 MQ 消息
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void sendToMq(OrderCreatedEvent event) {
        rocketMQTemplate.asyncSend("order-topic", 
            convertToMessage(event), new SendCallback() {
                @Override
                public void onSuccess(SendResult sendResult) {
                    log.info("订单消息发送成功: {}", event.getOrderId());
                }
                @Override
                public void onException(Throwable e) {
                    log.error("订单消息发送失败: {}", event.getOrderId(), e);
                }
            });
    }
    
    // 2. 发送邮件
    @Async
    @EventListener
    public void sendEmail(OrderCreatedEvent event) {
        emailService.sendTemplateEmail(
            event.getUserEmail(),
            "order-confirmation-template",
            Map.of("orderId", event.getOrderId(), "amount", event.getAmount())
        );
    }
    
    // 3. 更新统计
    @EventListener
    public void updateStatistics(OrderCreatedEvent event) {
        statisticsService.recordOrder(event.getCreateTime(), event.getAmount());
    }
    
    // 4. 记录日志
    @EventListener
    public void logOperation(OrderCreatedEvent event) {
        operationLogService.log("ORDER_CREATE", 
            event.getOperatorId(), 
            "创建订单: " + event.getOrderId());
    }
}
```

## 六、与 MQ 消息队列的区别

| 特性 | 观察者模式（进程内） | MQ 消息队列（进程间） |
|------|---------------------|----------------------|
| **通信范围** | 同一 JVM 进程内 | 跨进程、跨机器、跨网络 |
| **持久化** | 不持久化，进程结束即丢失 | 支持持久化，可保证消息不丢失 |
| **可靠性** | 低，进程崩溃事件丢失 | 高，支持消息确认、重试 |
| **解耦程度** | 进程内解耦 | 系统间完全解耦 |
| **性能** | 极高（内存调用） | 较高（网络开销） |
| **适用场景** | 单体应用内部事件 | 微服务间通信、分布式系统 |
| **代表实现** | Spring Event、Guava EventBus | RocketMQ、Kafka、RabbitMQ |

### 6.1 如何选择？

```
单体应用/单体服务内部 → Spring Event / Guava EventBus
微服务之间通信       → RocketMQ / Kafka / RabbitMQ
需要事务保证         → @TransactionalEventListener + MQ
高可靠要求           → MQ（持久化 + 确认机制）
极致性能要求         → 进程内事件（避免网络开销）
```

## 七、与策略模式的区别

| 维度 | 观察者模式 | 策略模式 |
|------|-----------|---------|
| **目的** | 一对多通知，状态变更传播 | 多选一执行，算法替换 |
| **关系** | 一对多（1:N） | 一对一（1:1） |
| **触发方式** | 被动接收通知 | 主动选择策略 |
| **执行时机** | 状态改变时自动触发 | 根据条件主动调用 |
| **关注点** | 对象间的通信与协作 | 算法的封装与切换 |

### 7.1 代码对比

```java
// ========== 观察者模式：一对多通知 ==========
public class OrderService {
    private List<OrderObserver> observers = new ArrayList<>();
    
    public void createOrder() {
        // 创建订单...
        // 通知所有观察者
        notifyObservers(order);
    }
    
    private void notifyObservers(Order order) {
        for (OrderObserver observer : observers) {
            observer.onOrderCreated(order);  // 所有观察者都执行
        }
    }
}

// ========== 策略模式：多选一执行 ==========
public class PaymentService {
    private PaymentStrategy strategy;
    
    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void pay(Order order) {
        // 根据条件选择一个策略执行
        strategy.pay(order);  // 只执行选中的策略
    }
}
```

## 八、面试高频题

### Q1：观察者模式有什么优缺点？

**优点：**
- 实现了对象间的松耦合，被观察者无需知道观察者的具体实现
- 支持广播通信，一对多通知非常高效
- 符合开闭原则，新增观察者无需修改被观察者代码

**缺点：**
- 如果观察者过多，通知耗时可能较长
- 循环依赖可能导致系统崩溃
- 观察者无法感知通知顺序

### Q2：Spring 事件机制和 Guava EventBus 有什么区别？

| 特性 | Spring Event | Guava EventBus |
|------|-------------|----------------|
| 集成度 | 与 Spring 深度集成 | 独立库，轻量级 |
| 事务支持 | 支持 @TransactionalEventListener | 不支持 |
| 异步支持 | @Async + @EventListener | AsyncEventBus |
| 泛型支持 | 完善 | 良好 |
| 适用场景 | Spring 项目 | 任何 Java 项目 |

### Q3：@TransactionalEventListener 的作用是什么？

`@TransactionalEventListener` 用于在事务的不同阶段监听事件：

- `BEFORE_COMMIT`：事务提交前执行（如数据校验）
- `AFTER_COMMIT`：事务提交后执行（如发送 MQ，确保数据库操作成功）
- `AFTER_ROLLBACK`：事务回滚后执行（如补偿操作）
- `AFTER_COMPLETION`：事务完成后执行（无论提交或回滚）

典型应用场景：**订单创建成功后发送 MQ 消息**，确保消息发送时订单数据已持久化。

### Q4：观察者模式和发布订阅模式有什么区别？

```
观察者模式：
Subject ↔ Observer（直接通信）

发布订阅模式：
Publisher → EventBus/Topic → Subscriber（通过中间件）
```

**区别：**
- 观察者模式：Subject 直接维护 Observer 列表，直接调用
- 发布订阅：引入事件中心/消息代理，发布者和订阅者完全解耦

### Q5：如何避免观察者模式中的循环依赖问题？

**解决方案：**

1. **事件去重**：记录已处理的事件 ID
```java
@Component
public class OrderHandler {
    private Set<String> processedEvents = ConcurrentHashMap.newKeySet();
    
    @EventListener
    public void handle(OrderEvent event) {
        if (!processedEvents.add(event.getEventId())) {
            return;  // 已处理过，跳过
        }
        // 处理逻辑...
    }
}
```

2. **限制传播深度**：设置最大传播层级
```java
public class EventContext {
    private static final ThreadLocal<Integer> depth = ThreadLocal.withValue(0);
    
    public static boolean canPropagate() {
        return depth.get() < MAX_DEPTH;
    }
}
```

3. **异步处理**：使用 @Async 避免同步调用链

## 九、最佳实践

1. **事件命名**：使用过去时态（OrderCreatedEvent、PaymentCompletedEvent）
2. **事件粒度**：避免过大事件，保持单一职责
3. **异常处理**：监听器中捕获异常，避免影响其他监听器
4. **异步优先**：非核心逻辑使用异步处理
5. **事务边界**：明确事件是在事务内还是事务外处理
6. **文档化**：维护事件清单，明确事件结构和消费方

---

> **总结**：观察者模式是事件驱动架构的基础，Spring Event 提供了完善的事务和异步支持，是 Java 企业级开发的首选方案。
