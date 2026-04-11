---
layout: default
title: 设计模式实战应用
---

# 设计模式实战应用

设计模式是软件工程中的最佳实践总结，掌握设计模式能够提升代码的可维护性、可扩展性和复用性。本文结合 Spring 框架源码，深入讲解常用设计模式的实战应用。

---

## 目录

1. [单例模式](#单例模式)
2. [工厂模式](#工厂模式)
3. [策略模式](#策略模式)
4. [观察者模式](#观察者模式)
5. [模板方法模式](#模板方法模式)
6. [装饰器模式](#装饰器模式)
7. [代理模式](#代理模式)
8. [Spring 源码中的设计模式汇总](#spring-源码中的设计模式汇总)
9. [面试题精选](#面试题精选)

---

## 单例模式

单例模式确保一个类只有一个实例，并提供一个全局访问点。

### 单例模式的应用场景

- 配置管理器
- 连接池
- 线程池
- 缓存管理器
- Spring 中的 Bean（默认单例）

### JVM 三种单例写法

#### 1. 饱汉式（懒汉式）

延迟加载，第一次使用时创建实例。

```java
public class Singleton {
    private static Singleton instance;
    
    private Singleton() {}
    
    // 线程不安全版本
    public static Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```

**线程安全版本（synchronized）：**

```java
public class Singleton {
    private static Singleton instance;
    
    private Singleton() {}
    
    public static synchronized Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```

**缺点：** 每次获取实例都加锁，性能较差。

#### 2. DCL（Double Check Lock，双重检查锁定）

```java
public class Singleton {
    // volatile 禁止指令重排序
    private volatile static Singleton instance;
    
    private Singleton() {}
    
    public static Singleton getInstance() {
        // 第一次检查：避免不必要的同步
        if (instance == null) {
            synchronized (Singleton.class) {
                // 第二次检查：确保只创建一次
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

**为什么需要 volatile？**

`instance = new Singleton()` 实际上分为三步：
1. 分配内存空间
2. 初始化对象
3. 将引用指向内存地址

如果没有 volatile，步骤 2 和 3 可能重排序，导致其他线程获取到未初始化的对象。

#### 3. 枚举单例（推荐）

```java
public enum Singleton {
    INSTANCE;
    
    private String config;
    
    public void doSomething() {
        System.out.println("Doing something...");
    }
    
    public String getConfig() {
        return config;
    }
    
    public void setConfig(String config) {
        this.config = config;
    }
}

// 使用
Singleton.INSTANCE.doSomething();
```

**优点：**
- 线程安全（由 JVM 保证）
- 防止反射攻击
- 防止反序列化创建新对象
- 代码简洁

### Spring 中的单例 Bean

Spring 默认将 Bean 作为单例管理：

```java
@Service
public class UserService {
    // 默认单例，整个 Spring 容器只有一个实例
}
```

**Spring 单例 vs 设计模式单例：**

| 特性 | Spring 单例 | 设计模式单例 |
|------|-------------|--------------|
| 范围 | Spring 容器 | JVM 虚拟机 |
| 实现方式 | IoC 容器管理 | 编码实现 |
| 线程安全 | 容器保证 | 开发者保证 |
| 生命周期 | 容器管理 | 开发者管理 |

---

## 工厂模式

工厂模式将对象的创建和使用分离，降低耦合度。

### 简单工厂

一个工厂类根据参数创建不同类型的对象。

```java
public class PaymentFactory {
    public static Payment createPayment(String type) {
        switch (type) {
            case "alipay":
                return new Alipay();
            case "wechat":
                return new WechatPay();
            case "unionpay":
                return new UnionPay();
            default:
                throw new IllegalArgumentException("Unsupported payment type");
        }
    }
}

// 使用
Payment payment = PaymentFactory.createPayment("alipay");
payment.pay(100);
```

### Spring BeanFactory

Spring 的核心容器本身就是一个大工厂。

```java
// BeanFactory 接口
public interface BeanFactory {
    Object getBean(String name);
    <T> T getBean(String name, Class<T> requiredType);
    <T> T getBean(Class<T> requiredType);
}

// 使用
ApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
UserService userService = context.getBean(UserService.class);
```

**Spring 工厂的优势：**
- 解耦对象的创建和使用
- 支持依赖注入
- 管理对象的生命周期
- 支持 AOP 代理

### Spring 的 FactoryBean

FactoryBean 是 Spring 提供的扩展接口，用于创建复杂的 Bean。

```java
@Component
public class ConnectionFactoryBean implements FactoryBean<Connection>, InitializingBean {
    
    private String url;
    private String username;
    private String password;
    private Connection connection;
    
    @Override
    public Connection getObject() throws Exception {
        return connection;
    }
    
    @Override
    public Class<?> getObjectType() {
        return Connection.class;
    }
    
    @Override
    public boolean isSingleton() {
        return true;
    }
    
    @Override
    public void afterPropertiesSet() throws Exception {
        // 复杂的初始化逻辑
        this.connection = DriverManager.getConnection(url, username, password);
    }
}
```

**使用：**

```java
@Autowired
private Connection connection;  // 注入的是 FactoryBean 创建的对象
```

**FactoryBean vs BeanFactory：**

| 特性 | FactoryBean | BeanFactory |
|------|-------------|-------------|
| 角色 | 被管理的对象 | 容器本身 |
| 用途 | 创建特定 Bean | 管理所有 Bean |
| 获取方式 | `&` 前缀获取工厂本身 | `getBean()` |

---

## 策略模式

策略模式定义一系列算法，将它们封装起来，并且使它们可以互相替换。

### 策略模式结构

```java
// 策略接口
public interface PaymentStrategy {
    void pay(BigDecimal amount);
    boolean supports(String paymentType);
}

// 具体策略：支付宝
@Service
public class AlipayStrategy implements PaymentStrategy {
    @Override
    public void pay(BigDecimal amount) {
        System.out.println("支付宝支付：" + amount);
    }
    
    @Override
    public boolean supports(String paymentType) {
        return "alipay".equals(paymentType);
    }
}

// 具体策略：微信支付
@Service
public class WechatPayStrategy implements PaymentStrategy {
    @Override
    public void pay(BigDecimal amount) {
        System.out.println("微信支付：" + amount);
    }
    
    @Override
    public boolean supports(String paymentType) {
        return "wechat".equals(paymentType);
    }
}
```

### 策略上下文

```java
@Service
public class PaymentService {
    
    private final List<PaymentStrategy> strategies;
    
    // Spring 自动注入所有策略实现
    public PaymentService(List<PaymentStrategy> strategies) {
        this.strategies = strategies;
    }
    
    public void pay(String paymentType, BigDecimal amount) {
        PaymentStrategy strategy = strategies.stream()
            .filter(s -> s.supports(paymentType))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Unsupported payment type"));
        
        strategy.pay(amount);
    }
}
```

### 价格计算策略

```java
// 价格计算策略
public interface PriceCalculationStrategy {
    BigDecimal calculatePrice(BigDecimal originalPrice, User user);
}

// 会员折扣策略
@Component
public class MemberDiscountStrategy implements PriceCalculationStrategy {
    @Override
    public BigDecimal calculatePrice(BigDecimal originalPrice, User user) {
        if (user.isMember()) {
            return originalPrice.multiply(new BigDecimal("0.9"));
        }
        return originalPrice;
    }
}

// 满减策略
@Component
public class FullReductionStrategy implements PriceCalculationStrategy {
    @Override
    public BigDecimal calculatePrice(BigDecimal originalPrice, User user) {
        if (originalPrice.compareTo(new BigDecimal("200")) >= 0) {
            return originalPrice.subtract(new BigDecimal("30"));
        }
        return originalPrice;
    }
}

// 组合策略
@Component
public class CompositePriceStrategy implements PriceCalculationStrategy {
    
    private final List<PriceCalculationStrategy> strategies;
    
    public CompositePriceStrategy(List<PriceCalculationStrategy> strategies) {
        // 按优先级排序
        this.strategies = strategies.stream()
            .sorted(Comparator.comparingInt(this::getPriority))
            .collect(Collectors.toList());
    }
    
    @Override
    public BigDecimal calculatePrice(BigDecimal originalPrice, User user) {
        BigDecimal price = originalPrice;
        for (PriceCalculationStrategy strategy : strategies) {
            price = strategy.calculatePrice(price, user);
        }
        return price;
    }
}
```

---

## 观察者模式

观察者模式定义对象之间的一对多依赖关系，当一个对象状态改变时，所有依赖者都会收到通知。

### Spring 事件机制

Spring 提供了完整的事件发布/监听机制。

#### 定义事件

```java
public class OrderCreatedEvent extends ApplicationEvent {
    private final Order order;
    
    public OrderCreatedEvent(Object source, Order order) {
        super(source);
        this.order = order;
    }
    
    public Order getOrder() {
        return order;
    }
}
```

#### 发布事件

```java
@Service
public class OrderService {
    
    private final ApplicationEventPublisher eventPublisher;
    
    public OrderService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }
    
    public void createOrder(Order order) {
        // 保存订单
        orderRepository.save(order);
        
        // 发布事件
        eventPublisher.publishEvent(new OrderCreatedEvent(this, order));
    }
}
```

#### 监听事件

```java
@Component
public class OrderEventListener {
    
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        Order order = event.getOrder();
        // 发送通知
        notificationService.sendOrderConfirmation(order);
    }
    
    @EventListener
    public void handleOrderCreatedForInventory(OrderCreatedEvent event) {
        Order order = event.getOrder();
        // 扣减库存
        inventoryService.deduct(order.getItems());
    }
    
    @EventListener
    public void handleOrderCreatedForLogistics(OrderCreatedEvent event) {
        Order order = event.getOrder();
        // 创建物流单
        logisticsService.createShipment(order);
    }
}
```

### 异步事件处理

```java
@Configuration
@EnableAsync
public class AsyncConfig {
    
    @Bean(name = "eventAsyncExecutor")
    public Executor eventAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("event-");
        executor.initialize();
        return executor;
    }
}

@Component
public class OrderEventListener {
    
    @Async("eventAsyncExecutor")
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 异步处理
        emailService.sendOrderEmail(event.getOrder());
    }
}
```

### 条件监听

```java
@Component
public class ConditionalEventListener {
    
    // 只处理大额订单
    @EventListener(condition = "#event.order.amount > 10000")
    public void handleLargeOrder(OrderCreatedEvent event) {
        // 大额订单特殊处理
        riskControlService.reviewOrder(event.getOrder());
    }
}
```

---

## 模板方法模式

模板方法模式定义一个算法的骨架，将某些步骤延迟到子类实现。

### Spring JdbcTemplate

JdbcTemplate 是模板方法模式的经典应用。

```java
@Service
public class UserDao {
    
    private final JdbcTemplate jdbcTemplate;
    
    public UserDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }
    
    // 使用模板方法
    public User findById(Long id) {
        return jdbcTemplate.queryForObject(
            "SELECT * FROM users WHERE id = ?",
            new BeanPropertyRowMapper<>(User.class),
            id
        );
    }
    
    // 批量操作
    public void batchInsert(List<User> users) {
        jdbcTemplate.batchUpdate(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            new BatchPreparedStatementSetter() {
                @Override
                public void setValues(PreparedStatement ps, int i) throws SQLException {
                    User user = users.get(i);
                    ps.setString(1, user.getName());
                    ps.setString(2, user.getEmail());
                }
                
                @Override
                public int getBatchSize() {
                    return users.size();
                }
            }
        );
    }
}
```

### 自定义模板方法

```java
// 抽象模板类
public abstract class DataImporter<T> {
    
    // 模板方法，定义算法骨架
    public final ImportResult importData(List<T> data) {
        // 1. 数据验证（固定步骤）
        validate(data);
        
        // 2. 数据转换（抽象步骤，子类实现）
        List<T> transformedData = transform(data);
        
        // 3. 数据保存（抽象步骤，子类实现）
        save(transformedData);
        
        // 4. 发送通知（固定步骤）
        sendNotification(transformedData.size());
        
        return new ImportResult(transformedData.size());
    }
    
    // 固定步骤
    private void validate(List<T> data) {
        if (data == null || data.isEmpty()) {
            throw new IllegalArgumentException("Data cannot be empty");
        }
    }
    
    // 抽象步骤
    protected abstract List<T> transform(List<T> data);
    protected abstract void save(List<T> data);
    
    // 钩子方法，子类可选择重写
    protected void sendNotification(int count) {
        System.out.println("Imported " + count + " records");
    }
}

// 具体实现：用户导入
@Component
public class UserImporter extends DataImporter<User> {
    
    @Override
    protected List<User> transform(List<User> users) {
        return users.stream()
            .map(u -> {
                u.setEmail(u.getEmail().toLowerCase());
                return u;
            })
            .collect(Collectors.toList());
    }
    
    @Override
    protected void save(List<User> users) {
        userRepository.saveAll(users);
    }
}

// 具体实现：订单导入
@Component
public class OrderImporter extends DataImporter<Order> {
    
    @Override
    protected List<Order> transform(List<Order> orders) {
        // 订单特殊转换逻辑
        return orders;
    }
    
    @Override
    protected void save(List<Order> orders) {
        orderRepository.saveAll(orders);
    }
    
    @Override
    protected void sendNotification(int count) {
        // 订单导入特殊通知
        notificationService.notifyOrderImport(count);
    }
}
```

---

## 装饰器模式

装饰器模式动态地给对象添加额外的职责，比继承更灵活。

### JDK IO 流

Java IO 流是装饰器模式的经典实现。

```java
// 基础流
InputStream fileStream = new FileInputStream("file.txt");

// 添加缓冲功能
InputStream bufferedStream = new BufferedInputStream(fileStream);

// 添加数据操作功能
DataInputStream dataStream = new DataInputStream(bufferedStream);

// 使用
int data = dataStream.readInt();
```

**装饰器链：**

```
FileInputStream（基础功能）
    ↓ 包装
BufferedInputStream（添加缓冲）
    ↓ 包装
DataInputStream（添加数据类型支持）
```

### 自定义装饰器

```java
// 组件接口
public interface Coffee {
    double cost();
    String description();
}

// 具体组件
public class SimpleCoffee implements Coffee {
    @Override
    public double cost() {
        return 10;
    }
    
    @Override
    public String description() {
        return "Simple coffee";
    }
}

// 抽象装饰器
public abstract class CoffeeDecorator implements Coffee {
    protected Coffee decoratedCoffee;
    
    public CoffeeDecorator(Coffee coffee) {
        this.decoratedCoffee = coffee;
    }
    
    @Override
    public double cost() {
        return decoratedCoffee.cost();
    }
    
    @Override
    public String description() {
        return decoratedCoffee.description();
    }
}

// 具体装饰器：牛奶
public class MilkDecorator extends CoffeeDecorator {
    public MilkDecorator(Coffee coffee) {
        super(coffee);
    }
    
    @Override
    public double cost() {
        return super.cost() + 2;
    }
    
    @Override
    public String description() {
        return super.description() + ", milk";
    }
}

// 具体装饰器：糖
public class SugarDecorator extends CoffeeDecorator {
    public SugarDecorator(Coffee coffee) {
        super(coffee);
    }
    
    @Override
    public double cost() {
        return super.cost() + 1;
    }
    
    @Override
    public String description() {
        return super.description() + ", sugar";
    }
}

// 使用
Coffee coffee = new SimpleCoffee();
coffee = new MilkDecorator(coffee);  // 加牛奶
coffee = new SugarDecorator(coffee); // 加糖

System.out.println(coffee.description()); // Simple coffee, milk, sugar
System.out.println(coffee.cost());        // 13.0
```

---

## 代理模式

代理模式为其他对象提供一种代理以控制对这个对象的访问。

### Spring AOP 代理

Spring AOP 使用代理模式实现声明式事务和切面编程。

```java
@Service
public class OrderService {
    
    @Transactional
    public void createOrder(Order order) {
        // 保存订单
        orderRepository.save(order);
        // 扣减库存
        inventoryService.deduct(order.getItems());
    }
}
```

**Spring AOP 代理类型：**

| 代理类型 | 适用场景 | 实现方式 |
|----------|----------|----------|
| JDK 动态代理 | 目标类实现接口 | `java.lang.reflect.Proxy` |
| CGLIB 代理 | 目标类无接口 | 继承目标类生成子类 |

**强制使用 CGLIB：**

```java
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true)  // 强制使用 CGLIB
public class Application {
}
```

### JDK 动态代理

```java
// 接口
public interface UserService {
    void save(User user);
}

// 实现类
public class UserServiceImpl implements UserService {
    @Override
    public void save(User user) {
        System.out.println("Saving user: " + user.getName());
    }
}

// 代理处理器
public class PerformanceHandler implements InvocationHandler {
    private final Object target;
    
    public PerformanceHandler(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        long start = System.currentTimeMillis();
        
        Object result = method.invoke(target, args);
        
        long end = System.currentTimeMillis();
        System.out.println(method.getName() + " took " + (end - start) + "ms");
        
        return result;
    }
}

// 创建代理
UserService target = new UserServiceImpl();
UserService proxy = (UserService) Proxy.newProxyInstance(
    target.getClass().getClassLoader(),
    target.getClass().getInterfaces(),
    new PerformanceHandler(target)
);

// 使用代理
proxy.save(new User("John"));  // 自动记录性能
```

### 性能监控埋点

```java
@Component
@Aspect
public class PerformanceAspect {
    
    @Around("@annotation(Monitor)")
    public Object monitorPerformance(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        long start = System.currentTimeMillis();
        
        try {
            return joinPoint.proceed();
        } finally {
            long duration = System.currentTimeMillis() - start;
            Metrics.timer("method.execution", "method", methodName)
                   .record(duration, TimeUnit.MILLISECONDS);
        }
    }
}

// 使用
@Service
public class PaymentService {
    
    @Monitor
    public void processPayment(Order order) {
        // 支付逻辑
    }
}
```

---

## Spring 源码中的设计模式汇总

Spring 框架大量使用了设计模式，以下是主要的设计模式应用：

### 1. 工厂模式

**应用：** BeanFactory、ApplicationContext

```java
// BeanFactory 是工厂模式的典型应用
BeanFactory factory = new XmlBeanFactory(new ClassPathResource("beans.xml"));
UserService userService = factory.getBean(UserService.class);
```

### 2. 单例模式

**应用：** Spring Bean 的默认作用域

```java
// 默认单例
@Service
public class UserService {
    // 容器内只有一个实例
}
```

### 3. 代理模式

**应用：** Spring AOP、声明式事务

```java
// AOP 代理实现声明式事务
@Transactional
public void transferMoney(Account from, Account to, BigDecimal amount) {
    // 自动开启事务
    // 业务逻辑
    // 自动提交或回滚
}
```

### 4. 策略模式

**应用：** Resource 接口的不同实现、InstantiationStrategy

```java
// Resource 策略
Resource resource = new ClassPathResource("config.xml");
// 或
Resource resource = new FileSystemResource("/path/to/file");
// 或
Resource resource = new UrlResource("http://example.com/config.xml");
```

### 5. 模板方法模式

**应用：** JdbcTemplate、HibernateTemplate、RestTemplate

```java
// JdbcTemplate 使用模板方法模式
jdbcTemplate.query(
    "SELECT * FROM users",
    new RowMapper<User>() {
        @Override
        public User mapRow(ResultSet rs, int rowNum) throws SQLException {
            // 只需实现数据映射
            return new User(rs.getLong("id"), rs.getString("name"));
        }
    }
);
```

### 6. 观察者模式

**应用：** Spring 事件机制（ApplicationEvent、ApplicationListener）

```java
// 事件发布
applicationContext.publishEvent(new CustomEvent(this, data));

// 事件监听
@EventListener
public void handleCustomEvent(CustomEvent event) {
    // 处理事件
}
```

### 7. 装饰器模式

**应用：** InputStream、OutputStream 的装饰器链

```java
// 装饰器链
new DataInputStream(
    new BufferedInputStream(
        new FileInputStream("file.txt")
    )
);
```

### 8. 适配器模式

**应用：** HandlerAdapter、AdvisorAdapter

```java
// HandlerAdapter 适配不同类型的 Controller
public interface HandlerAdapter {
    boolean supports(Object handler);
    ModelAndView handle(HttpServletRequest request, 
                        HttpServletResponse response, 
                        Object handler) throws Exception;
}
```

### 9. 责任链模式

**应用：** HandlerInterceptor 链、Filter 链

```java
// 拦截器链
registry.addInterceptor(new AuthInterceptor())
        .addInterceptor(new LogInterceptor())
        .addInterceptor(new PerformanceInterceptor());
```

### 10. 建造者模式

**应用：** BeanDefinitionBuilder、ResponseEntity

```java
// ResponseEntity 建造者
return ResponseEntity
    .status(HttpStatus.OK)
    .header("X-Custom-Header", "value")
    .body(responseBody);
```

---

## 面试题精选

### 1. 单例模式有哪些实现方式？DCL 为什么要使用 volatile？

**答案：**

**三种实现方式：**

1. **饱汉式（懒汉式）**：延迟加载，第一次使用时创建实例
2. **DCL（双重检查锁定）**：两次检查 + synchronized，兼顾性能和线程安全
3. **枚举单例**：最推荐的方式，由 JVM 保证线程安全

**DCL 需要 volatile 的原因：**

`instance = new Singleton()` 不是原子操作，分为三步：
1. 分配内存空间
2. 初始化对象
3. 将引用指向内存地址

步骤 2 和 3 可能重排序，导致其他线程获取到未初始化的对象。volatile 禁止指令重排序，确保对象完全初始化后才暴露引用。

### 2. Spring 中的 Bean 是单例吗？与设计模式中的单例有什么区别？

**答案：**

**Spring Bean 默认是单例**，通过 `@Scope("singleton")` 或默认配置实现。

**区别：**

| 特性 | Spring 单例 | 设计模式单例 |
|------|-------------|--------------|
| 范围 | Spring 容器内唯一 | JVM 虚拟机内唯一 |
| 实现 | IoC 容器管理 | 编码实现（DCL/枚举等）|
| 线程安全 | 容器保证 | 开发者保证 |
| 生命周期 | 容器管理 | 开发者管理 |

**Spring 的其他作用域：**

| 作用域 | 说明 |
|--------|------|
| singleton | 默认，每个容器一个实例 |
| prototype | 每次请求创建新实例 |
| request | 每个 HTTP 请求一个实例 |
| session | 每个 HTTP Session 一个实例 |

### 3. 策略模式在 Spring 中是如何应用的？请举例说明。

**答案：**

**Spring 中的策略模式应用：**

1. **Resource 接口**：
   ```java
   Resource resource = new ClassPathResource("config.xml");
   // 或
   Resource resource = new FileSystemResource("/path/to/file");
   ```

2. **InstantiationStrategy**：
   - SimpleInstantiationStrategy
   - CglibSubclassingInstantiationStrategy

3. **HandlerAdapter**：
   - HttpRequestHandlerAdapter
   - SimpleControllerHandlerAdapter
   - RequestMappingHandlerAdapter

**自定义策略模式示例：**

```java
// 支付策略
public interface PaymentStrategy {
    void pay(BigDecimal amount);
    boolean supports(String type);
}

// Spring 自动注入所有策略
@Service
public class PaymentService {
    private final List<PaymentStrategy> strategies;
    
    public PaymentService(List<PaymentStrategy> strategies) {
        this.strategies = strategies;
    }
    
    public void pay(String type, BigDecimal amount) {
        strategies.stream()
            .filter(s -> s.supports(type))
            .findFirst()
            .ifPresent(s -> s.pay(amount));
    }
}
```

### 4. Spring 事件机制是如何实现的？如何实现异步事件处理？

**答案：**

**Spring 事件机制组成：**

1. **事件（Event）**：继承 `ApplicationEvent`
2. **发布器（Publisher）**：`ApplicationEventPublisher`
3. **监听器（Listener）**：`@EventListener` 或 `ApplicationListener`

**实现步骤：**

```java
// 1. 定义事件
public class OrderCreatedEvent extends ApplicationEvent {
    private final Order order;
    public OrderCreatedEvent(Object source, Order order) {
        super(source);
        this.order = order;
    }
}

// 2. 发布事件
@Service
public class OrderService {
    @Autowired
    private ApplicationEventPublisher publisher;
    
    public void createOrder(Order order) {
        // 保存订单
        publisher.publishEvent(new OrderCreatedEvent(this, order));
    }
}

// 3. 监听事件
@Component
public class OrderEventListener {
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 处理事件
    }
}
```

**异步事件处理：**

```java
@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        return executor;
    }
}

@Component
public class OrderEventListener {
    @Async
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 异步处理
    }
}
```

### 5. Spring AOP 使用了哪种代理模式？JDK 动态代理和 CGLIB 有什么区别？

**答案：**

**Spring AOP 代理类型：**

| 代理类型 | 适用场景 | 实现方式 |
|----------|----------|----------|
| JDK 动态代理 | 目标类实现了接口 | `java.lang.reflect.Proxy` |
| CGLIB 代理 | 目标类没有实现接口 | 继承目标类生成子类 |

**JDK 动态代理：**
- 基于接口实现
- 只能代理接口中的方法
- 性能较好（反射调用优化）

**CGLIB 代理：**
- 基于继承实现
- 可以代理类中的所有方法（包括 final 方法除外）
- 需要引入 CGLIB 库
- 不能代理 final 类

**强制使用 CGLIB：**

```java
@EnableAspectJAutoProxy(proxyTargetClass = true)
```

---

## 总结

设计模式是软件设计的基石，掌握这些模式能够：

1. **单例模式**：确保全局唯一实例，如配置管理器、连接池
2. **工厂模式**：解耦对象创建，如 Spring BeanFactory
3. **策略模式**：封装算法族，如支付方式、价格计算
4. **观察者模式**：实现事件驱动，如 Spring 事件机制
5. **模板方法模式**：复用算法骨架，如 JdbcTemplate
6. **装饰器模式**：动态添加职责，如 IO 流包装
7. **代理模式**：控制对象访问，如 Spring AOP

Spring 框架本身就是设计模式的集大成者，深入学习 Spring 源码能够更好地理解和应用这些模式。
