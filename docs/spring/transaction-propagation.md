# Spring 事务传播机制详解 ⭐⭐⭐

## 面试题：Spring 事务传播机制有哪些？

### 核心回答

Spring 事务传播机制定义了**多个事务方法相互调用时，事务如何在方法间传播**。Spring 提供了 7 种传播行为，通过 `@Transactional(propagation = Propagation.XXX)` 配置。

### 七种传播行为

| 传播行为 | 说明 | 常用场景 |
|---------|------|---------|
| **REQUIRED** | 默认。如果当前有事务，加入该事务；如果没有，创建新事务 | 大多数业务 |
| **REQUIRES_NEW** | 始终新建事务，挂起当前事务 | 日志、通知 |
| **SUPPORTS** | 如果当前有事务，加入事务；如果没有，非事务执行 | 查询方法 |
| **NOT_SUPPORTED** | 以非事务执行，挂起当前事务 | 发送短信、MQ |
| **MANDATORY** | 必须在事务中执行，否则抛异常 | 强制需要事务 |
| **NEVER** | 必须不在事务中执行，否则抛异常 | 禁止事务 |
| **NESTED** | 如果当前有事务，嵌套执行；如果没有，同 REQUIRED | 局部回滚 |

### 传播行为详解

#### 1. REQUIRED（默认）

**行为**：如果当前有事务，加入该事务；如果没有，创建新事务。

```java
@Service
public class AccountService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void transfer(Account from, Account to, BigDecimal amount) {
        // 参与父事务
        from.withdraw(amount);
        to.deposit(amount);
    }
}

@Service
public class OrderService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void createOrder(Order order) {
        // 调用 transfer
        accountService.transfer(from, to, amount);  // 参与同一个事务
        // 如果抛出异常，都会回滚
    }
}
```

**特点**：
- 多个方法在同一个事务中
- 任一方法抛异常，全部回滚

#### 2. REQUIRES_NEW

**行为**：始终新建事务，挂起当前事务。

```java
@Service
public class LogService {
    
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLog(String operation, String detail) {
        // 独立事务，不受主事务影响
        logRepository.save(operation, detail);
    }
}

@Service
public class OrderService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void createOrder(Order order) {
        // 主事务
        orderRepository.save(order);
        
        try {
            // REQUIRES_NEW：新建独立事务
            logService.saveLog("CREATE_ORDER", order.getId());
        } catch (Exception e) {
            // 日志失败不影响主事务
        }
        
        // 即使日志失败，订单仍然提交
    }
}
```

**特点**：
- 两个事务完全独立
- 子事务回滚不影响父事务
- 父事务回滚也不影响子事务（已提交的部分）

#### 3. SUPPORTS

**行为**：如果当前有事务，加入事务；如果没有，非事务执行。

```java
@Service
public class QueryService {
    
    @Transactional(propagation = Propagation.SUPPORTS)
    public User findById(Long id) {
        // 有事务则加入，无事务则非事务执行
        return userRepository.findById(id);
    }
}
```

**场景**：
- 查询方法：希望在有事务时保证一致性，无事务时普通查询
- 适用于只读操作

#### 4. NOT_SUPPORTED

**行为**：以非事务执行，挂起当前事务。

```java
@Service
public class NotificationService {
    
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void sendEmail(String to, String subject) {
        // 不参与事务，防止事务超时
        emailService.send(to, subject);
    }
}

@Service
public class OrderService {
    
    @Transactional(propagation = Propagation.REQUIRED, timeout = 30)
    public void createOrder(Order order) {
        // 处理订单（30秒超时）
        orderRepository.save(order);
        
        // 发送通知：不参与事务，防止超时
        notificationService.sendEmail(order.getEmail(), "订单创建成功");
    }
}
```

**场景**：
- 发送短信、MQ 消息
- 不希望被长事务影响

#### 5. MANDATORY

**行为**：必须在事务中执行，否则抛异常。

```java
@Service
public class InventoryService {
    
    @Transactional(propagation = Propagation.MANDATORY)
    public void deductStock(Long productId, Integer count) {
        // 必须有外部事务调用，否则抛异常
        stockRepository.deduct(productId, count);
    }
}

@Service
public class OrderService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void createOrder(Order order) {
        // 必须在事务中调用
        inventoryService.deductStock(productId, 1);
    }
}
```

**场景**：
- 强制依赖外部事务的方法
- 子流程必须有事务保证

#### 6. NEVER

**行为**：必须不在事务中执行，否则抛异常。

```java
@Service
public class ReportService {
    
    @Transactional(propagation = Propagation.NEVER)
    public void exportReport() {
        // 禁止在事务中执行，防止锁定
        reportGenerator.export();
    }
}
```

**场景**：
- 导出报表：长时间操作，不应被事务锁定
- 某些查询操作

#### 7. NESTED

**行为**：如果当前有事务，在嵌套事务中执行；如果没有，同 REQUIRED。

```java
@Service
public class BatchService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void batchInsert(List<Item> items) {
        for (Item item : items) {
            try {
                // NESTED：子事务可独立回滚
                itemService.saveItem(item);
            } catch (Exception e) {
                // 单条失败，不影响整体
                log.error("保存失败: {}", item.getId());
            }
        }
    }
}

@Service
public class ItemService {
    
    @Transactional(propagation = Propagation.NESTED)
    public void saveItem(Item item) {
        // 嵌套事务：失败时只回滚自身
        itemRepository.save(item);
    }
}
```

**与 REQUIRES_NEW 的区别**：

| 特性 | NESTED | REQUIRES_NEW |
|------|--------|--------------|
| 事务关系 | 嵌套在父事务中 | 完全独立 |
| 父事务回滚 | 子事务也回滚 | 子事务不受影响 |
| 子事务回滚 | 可单独回滚 | 不影响父事务 |
| savepoint | 使用数据库保存点 | 新建事务 |

### 传播行为对比图

```
REQUIRED:
┌─────────────────────────────────┐
│         父事务                    │
│  ┌─────────────────────────┐   │
│  │ 子事务（加入父事务）     │   │
│  │ 一起提交，一起回滚       │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘

REQUIRES_NEW:
┌──────────────┐   ┌──────────────┐
│   父事务      │   │   子事务      │
│  ┌─────────┐ │   │ ┌─────────┐  │
│  │ ...     │─┼──→│ │ 独立运行 │  │
│  └─────────┘ │   │ └─────────┘  │
│              │   │              │
└──────────────┘   └──────────────┘

NESTED:
┌─────────────────────────────────┐
│         父事务                    │
│  ┌─────────────────────────┐   │
│  │     子事务（嵌套）       │   │
│  │     可单独回滚           │   │
│  │     父回滚则子回滚       │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### 代码示例

#### 典型业务场景

```java
@Service
public class OrderService {
    
    @Autowired
    private AccountService accountService;
    
    @Autowired
    private InventoryService inventoryService;
    
    @Autowired
    private LogService logService;
    
    @Transactional(timeout = 30)
    public void createOrder(OrderDTO dto) {
        // 1. 创建订单（参与主事务）
        Order order = orderRepository.save(new Order(dto));
        
        // 2. 扣减库存（参与主事务，一起回滚）
        inventoryService.deductStock(dto.getProductId(), dto.getCount());
        
        // 3. 扣减余额（参与主事务，一起回滚）
        accountService.deduct(dto.getUserId(), dto.getAmount());
        
        // 4. 发送通知（独立事务，不影响主事务）
        try {
            notificationService.sendSms(dto.getPhone(), "订单创建成功");
        } catch (Exception e) {
            log.warn("短信发送失败，不影响订单创建");
        }
    }
}

@Service
public class AccountService {
    
    @Transactional(propagation = Propagation.REQUIRED)
    public void deduct(Long userId, BigDecimal amount) {
        // 默认传播行为
        accountRepository.deduct(userId, amount);
    }
}

@Service
public class NotificationService {
    
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendSms(String phone, String content) {
        // 独立事务，即使失败也不影响调用方
        smsGateway.send(phone, content);
    }
}
```

### @Transactional 失效场景

#### 1. 方法访问权限问题

```java
// ❌ 失效：private 方法不会被代理
@Service
public class Service {
    @Transactional
    private void save(Data data) {  // 不会生效
        // ...
    }
}

// ✅ 正确：public 方法
@Service
public class Service {
    @Transactional
    public void save(Data data) {  // 生效
        // ...
    }
}
```

#### 2. 自我调用（this 调用）

```java
@Service
public class Service {
    
    public void methodA() {
        // 调用同类中的另一个方法
        this.methodB();  // 不会走代理！
    }
    
    @Transactional
    public void methodB() {  // 不会生效
        // ...
    }
}

// ✅ 解决方案：注入自身
@Service
public class Service {
    
    @Autowired
    private Service self;  // 注入代理对象
    
    public void methodA() {
        self.methodB();  // 走代理
    }
    
    @Transactional
    public void methodB() {  // 生效
        // ...
    }
}
```

#### 3. 异常被捕获

```java
@Service
public class Service {
    
    @Transactional
    public void save(Data data) {
        try {
            // 异常被捕获，不会传播到代理
            repository.save(data);
            throw new RuntimeException("test");
        } catch (Exception e) {
            // 不会回滚！
        }
    }
}

// ✅ 解决方案
@Service
public class Service {
    
    @Transactional
    public void save(Data data) {
        repository.save(data);
        throw new RuntimeException("test");
    }
}

// 或者手动回滚
@Service
public class Service {
    
    @Transactional
    public void save(Data data) {
        try {
            repository.save(data);
            throw new RuntimeException("test");
        } catch (Exception e) {
            // 手动回滚
            TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        }
    }
}
```

#### 4. 异常类型不匹配

```java
@Service
public class Service {
    
    @Transactional
    public void save(Data data) {
        // 默认只回滚 RuntimeException 和 Error
        throw new IOException("checked exception");  // 不会回滚
    }
}

// ✅ 解决方案
@Service
public class Service {
    
    @Transactional(rollbackFor = Exception.class)
    public void save(Data data) throws IOException {
        throw new IOException("checked exception");  // 会回滚
    }
}
```

#### 5. 非 public 代理问题

```java
// Spring 默认使用 JDK 动态代理
// 需要实现接口才能代理

// ❌ 可能失效：没有实现接口
@Service  // 默认使用 JDK 代理
public class UserService {  // 没有实现接口
    @Transactional
    public void save() { }
}

// ✅ 解决方案1：实现接口
@Service
public class UserService implements UserServiceInterface {
    @Transactional
    public void save() { }
}

// ✅ 解决方案2：配置 CGLIB 代理
@EnableAspectJAutoProxy(proxyTargetClass = true)
```

### 高频面试题

**Q1: REQUIRED 和 NESTED 的区别？**

```
REQUIRED：加入父事务，是一个事务
- 父回滚，子也回滚
- 子回滚，父也回滚

NESTED：嵌套事务，使用 savepoint
- 父回滚，子也回滚
- 子回滚，只回滚子自身
```

**Q2: REQUIRES_NEW 和 REQUIRED 的区别？**

```
REQUIRED：共用一个事务
- A 调用 B，都在一个事务中
- B 失败，A 也回滚

REQUIRES_NEW：完全独立
- A 调用 B，B 在独立事务中
- B 失败，A 不受影响
```

**Q3: 什么场景使用 REQUIRES_NEW？**

1. 日志记录：日志失败不应影响业务
2. 发送通知：短信、MQ 消息
3. 异步任务：不想被长事务阻塞
4. 数据校验：独立事务校验

**Q4: Spring 事务和数据库事务的关系？**

```
Spring 事务是对数据库事务的封装

Spring 事务传播行为控制多个方法是否在同一个数据库事务中

最终都是通过数据库的 COMMIT/ROLLBACK 完成
```

### 最佳实践

```java
// 1. 避免循环依赖导致的代理失效
@Service
public class ServiceA {
    @Autowired
    private ServiceB serviceB;
}

// 2. 使用编程式事务处理复杂场景
@Service
public class ComplexService {
    
    @Autowired
    private TransactionTemplate template;
    
    public void execute() {
        template.executeWithoutResult(status -> {
            // 业务逻辑
        });
        
        // 或者
        template.execute(status -> {
            // 业务逻辑
            status.setRollbackOnly();  // 手动回滚
            return null;
        });
    }
}

// 3. 事务超时设置
@Service
public class LongOperationService {
    
    @Transactional(timeout = 60)  // 60 秒超时
    public void longOperation() {
        // 长时间操作
    }
}

// 4. 设置只读事务
@Service
public class QueryService {
    
    @Transactional(readOnly = true)
    public List<User> findAll() {
        return userRepository.findAll();
    }
}
```

---

**参考链接：**
- [Spring事务的传播机制-CSDN](https://blog.csdn.net/qq_64656621/article/details/138173398)
- [Spring七种事务传播行为一文通关-掘金](https://juejin.cn/post/7498614849582186537)
