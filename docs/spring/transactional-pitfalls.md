# @Transactional 失效场景与解决方案

> Spring 事务注解的常见陷阱，面试高频考点

## 🎯 面试重点

- @Transactional 注解的工作原理
- 事务失效的常见场景
- 如何排查和解决事务问题
- 事务最佳实践

## 📖 @Transactional 工作原理

### Spring 事务代理机制

```java
/**
 * Spring 事务的 AOP 代理实现
 * 
 * 1. Spring 为 @Transactional 类创建代理
 * 2. 代理拦截方法调用
 * 3. 开启事务、执行业务、提交/回滚
 */
public class TransactionalProxy {
    
    // 代理示例
    /*
     * @Service
     * public class UserService {
     *     
     *     @Transactional
     *     public void createUser(User user) {
     *         // 业务逻辑
     *     }
     * }
     * 
     * Spring 实际创建：UserService$$EnhancerBySpringCGLIB
     * 代理内部：
     * 1. TransactionManager.getTransaction()
     * 2. 调用原始方法
     * 3. 根据结果 commit() 或 rollback()
     */
}
```

### 事务传播行为

```java
/**
 * 传播行为影响事务边界
 */
public class PropagationBehavior {
    
    // REQUIRED（默认）：加入当前事务，没有则新建
    @Transactional(propagation = Propagation.REQUIRED)
    
    // REQUIRES_NEW：新建事务，挂起当前事务
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    
    // NESTED：嵌套事务（Savepoint）
    @Transactional(propagation = Propagation.NESTED)
    
    // SUPPORTS：有事务则加入，没有则以非事务运行
    @Transactional(propagation = Propagation.SUPPORTS)
    
    // NOT_SUPPORTED：以非事务运行，挂起当前事务
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    
    // NEVER：以非事务运行，有事务则抛异常
    @Transactional(propagation = Propagation.NEVER)
    
    // MANDATORY：必须有事务，没有则抛异常
    @Transactional(propagation = Propagation.MANDATORY)
}
```

## 📖 事务失效场景

### 1. 非 public 方法

```java
@Service
public class UserService {
    
    // ✅ 正确：public 方法
    @Transactional
    public void publicMethod() {
        // 事务生效
    }
    
    // ❌ 错误：非 public 方法
    @Transactional
    protected void protectedMethod() {
        // 事务失效！Spring 默认只代理 public 方法
    }
    
    @Transactional
    private void privateMethod() {
        // 事务失效！
    }
}
```

**解决方案：**
- 使用 `@Transactional` 的方法必须是 `public`
- 或配置 `@EnableTransactionManagement(proxyTargetClass = true)` + CGLIB 代理

### 2. 自调用问题

```java
@Service
public class OrderService {
    
    @Transactional
    public void createOrder(Order order) {
        // 业务逻辑...
        updateInventory(order);  // ❌ 自调用，事务失效！
    }
    
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateInventory(Order order) {
        // 这个方法的事务不会生效
        // 因为是通过 this.updateInventory() 调用，不是代理调用
    }
}
```

**解决方案：**
1. **注入自身代理**
```java
@Service
public class OrderService {
    
    @Autowired
    private OrderService self;  // 注入自身代理
    
    @Transactional
    public void createOrder(Order order) {
        self.updateInventory(order);  // ✅ 通过代理调用
    }
}
```

2. **拆分到不同 Service**
```java
@Service
public class InventoryService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateInventory(Order order) {
        // 独立事务
    }
}

@Service
public class OrderService {
    @Autowired
    private InventoryService inventoryService;
    
    @Transactional
    public void createOrder(Order order) {
        inventoryService.updateInventory(order);  // ✅ 代理调用
    }
}
```

### 3. 异常类型不匹配

```java
@Service
public class UserService {
    
    // ❌ 错误：默认只回滚 RuntimeException 和 Error
    @Transactional
    public void createUser(User user) throws Exception {
        try {
            userRepository.save(user);
            throw new Exception("业务异常");  // 不会回滚！
        } catch (Exception e) {
            // 事务已提交
        }
    }
    
    // ✅ 正确：指定回滚异常类型
    @Transactional(rollbackFor = Exception.class)
    public void createUserSafe(User user) throws Exception {
        userRepository.save(user);
        throw new Exception("业务异常");  // 会回滚
    }
}
```

**解决方案：**
- 明确指定 `rollbackFor` 属性
```java
@Transactional(rollbackFor = {Exception.class, BusinessException.class})
```

### 4. 异常被捕获

```java
@Service
public class PaymentService {
    
    @Transactional
    public void processPayment(Payment payment) {
        try {
            paymentRepository.save(payment);
            throw new RuntimeException("支付失败");
        } catch (RuntimeException e) {
            log.error("支付异常", e);
            // ❌ 异常被捕获，事务不会回滚！
        }
    }
    
    // ✅ 正确：抛出异常或手动回滚
    @Transactional
    public void processPaymentSafe(Payment payment) {
        try {
            paymentRepository.save(payment);
            throw new RuntimeException("支付失败");
        } catch (RuntimeException e) {
            log.error("支付异常", e);
            // 手动回滚
            TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        }
    }
}
```

### 5. 数据库引擎不支持

```sql
-- MyISAM 引擎不支持事务
CREATE TABLE myisam_table (
    id INT PRIMARY KEY
) ENGINE=MyISAM;

-- ❌ 对 MyISAM 表的操作不会回滚
```

**解决方案：**
- 使用 InnoDB 引擎
```sql
CREATE TABLE innodb_table (
    id INT PRIMARY KEY
) ENGINE=InnoDB;
```

### 6. 非事务方法调用事务方法

```java
@Service
public class UserService {
    
    // ❌ 错误：非事务方法调用事务方法
    public void batchCreateUsers(List<User> users) {
        for (User user : users) {
            createUser(user);  // 每个 createUser 在独立事务中
        }
        // 如果中途失败，已创建的用户不会回滚
    }
    
    @Transactional
    public void createUser(User user) {
        userRepository.save(user);
    }
    
    // ✅ 正确：整个方法在一个事务中
    @Transactional
    public void batchCreateUsersSafe(List<User> users) {
        for (User user : users) {
            userRepository.save(user);
        }
    }
}
```

## 📖 事务最佳实践

### 1. 配置建议

```yaml
# application.yml
spring:
  transaction:
    default-timeout: 30  # 默认超时时间
    rollback-on-commit-failure: true
```

```java
@Configuration
@EnableTransactionManagement
public class TransactionConfig {
    
    @Bean
    public TransactionTemplate transactionTemplate(PlatformTransactionManager txManager) {
        TransactionTemplate template = new TransactionTemplate(txManager);
        template.setTimeout(30);  // 设置超时
        template.setReadOnly(false);
        return template;
    }
}
```

### 2. 编程式事务

```java
@Service
public class OrderService {
    
    @Autowired
    private TransactionTemplate transactionTemplate;
    
    @Autowired
    private PlatformTransactionManager transactionManager;
    
    // 使用 TransactionTemplate
    public void createOrder(Order order) {
        transactionTemplate.execute(status -> {
            try {
                orderRepository.save(order);
                inventoryService.update(order);
                return true;
            } catch (Exception e) {
                status.setRollbackOnly();
                throw e;
            }
        });
    }
    
    // 手动管理事务
    public void manualTransaction() {
        TransactionDefinition definition = new DefaultTransactionDefinition();
        TransactionStatus status = transactionManager.getTransaction(definition);
        
        try {
            // 业务逻辑
            transactionManager.commit(status);
        } catch (Exception e) {
            transactionManager.rollback(status);
            throw e;
        }
    }
}
```

### 3. 事务监控与排查

```java
@Component
public class TransactionMonitor {
    
    // 监控事务提交/回滚
    @EventListener
    public void handleTransactionEvent(TransactionApplicationEvent event) {
        if (event instanceof TransactionCompletedEvent) {
            TransactionCompletedEvent completed = (TransactionCompletedEvent) event;
            log.info("事务 {} 完成，状态: {}", 
                completed.getTransactionName(),
                completed.getTransactionStatus().isCompleted() ? "提交" : "回滚");
        }
    }
    
    // 检查事务是否活跃
    public boolean isTransactionActive() {
        return TransactionSynchronizationManager.isActualTransactionActive();
    }
    
    // 获取当前事务信息
    public void printTransactionInfo() {
        log.info("当前事务: {}", TransactionSynchronizationManager.getCurrentTransactionName());
        log.info("隔离级别: {}", TransactionSynchronizationManager.getCurrentTransactionIsolationLevel());
        log.info("只读: {}", TransactionSynchronizationManager.isCurrentTransactionReadOnly());
    }
}
```

## 📖 面试真题

### Q1: @Transactional 在哪些情况下会失效？

**答：**
1. **方法非 public**：Spring 默认只代理 public 方法
2. **自调用问题**：类内部方法调用，不走代理
3. **异常类型不匹配**：默认只回滚 RuntimeException 和 Error
4. **异常被捕获**：异常未抛出到代理层
5. **数据库引擎不支持**：如 MyISAM
6. **传播行为配置错误**：如 REQUIRES_NEW 被嵌套调用
7. **多数据源未指定**：未指定 transactionManager

### Q2: 如何解决自调用事务失效？

**答：**
1. **注入自身代理**：使用 `@Autowired private OrderService self;`
2. **拆分 Service**：将事务方法移到另一个 Service
3. **使用 AspectJ 模式**：`@EnableTransactionManagement(mode = AdviceMode.ASPECTJ)`
4. **编程式事务**：使用 TransactionTemplate

### Q3: 如何排查事务问题？

**答：**
1. **开启调试日志**：`logging.level.org.springframework.transaction=DEBUG`
2. **检查代理类**：查看 Spring 创建的代理类名
3. **验证异常类型**：确保异常能触发回滚
4. **检查数据库引擎**：确认使用 InnoDB
5. **使用 TransactionMonitor**：监控事务状态

### Q4: 声明式事务和编程式事务的区别？

**答：**
- **声明式事务**：使用 `@Transactional`，基于 AOP，代码简洁
- **编程式事务**：使用 TransactionTemplate，灵活控制事务边界
- **选择建议**：简单场景用声明式，复杂场景用编程式

### Q5: 多数据源下的事务如何配置？

**答：**
```java
@Configuration
public class MultiDataSourceConfig {
    
    @Primary
    @Bean
    @ConfigurationProperties("spring.datasource.primary")
    public DataSource primaryDataSource() {
        return DataSourceBuilder.create().build();
    }
    
    @Bean
    @ConfigurationProperties("spring.datasource.secondary")
    public DataSource secondaryDataSource() {
        return DataSourceBuilder.create().build();
    }
    
    @Primary
    @Bean
    public PlatformTransactionManager primaryTxManager(@Qualifier("primaryDataSource") DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
    
    @Bean
    public PlatformTransactionManager secondaryTxManager(@Qualifier("secondaryDataSource") DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}

// 使用：指定事务管理器
@Transactional(transactionManager = "primaryTxManager")
public void primaryOperation() {}

@Transactional(transactionManager = "secondaryTxManager")  
public void secondaryOperation() {}
```

## 📚 延伸阅读

- [Spring Transaction Documentation](https://docs.spring.io/spring-framework/docs/current/reference/html/data-access.html#transaction)
- [Transaction Best Practices](https://www.baeldung.com/spring-transactional-propagation-isolation)

---

**⭐ 重点：事务是保证数据一致性的关键，必须掌握其原理和常见陷阱**