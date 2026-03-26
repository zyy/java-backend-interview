---
layout: default
title: SOLID 原则详解：面向对象设计的六大原则
---
# SOLID 原则详解：面向对象设计的六大原则

## 🎯 面试题：SOLID 原则分别指的是什么？

> SOLID 是面向对象设计的五个基本原则，由 Robert C. Martin（Uncle Bob）提出。它们是写出高可维护性代码的理论基础，面试中常用来考察候选人的设计能力。

---

## 一、单一职责原则（SRP — Single Responsibility Principle）

### 核心定义

> 一个类应该只有一个引起它变化的原因。

### 反面案例

```java
// ❌ 违反 SRP：一个类承担了多个职责
public class User {
    public void saveUser() { /* 持久化 */ }
    public void sendEmail() { /* 发送邮件 */ }
    public void validateUser() { /* 数据验证 */ }
    public void generateReport() { /* 生成报表 */ }
}
// 这个类会因为任何职责的变化而被修改
```

### 正面案例

```java
// ✅ 符合 SRP：职责分离
public class UserValidator {
    public boolean validate(User user) { /* 数据验证 */ }
}

public class UserRepository {
    public void save(User user) { /* 持久化 */ }
}

public class EmailService {
    public void sendWelcomeEmail(User user) { /* 发邮件 */ }
}

public class ReportGenerator {
    public Report generateUserReport(User user) { /* 生成报表 */ }
}
```

### Spring 中的体现

```java
// 每个类只做一件事
@Component
public class PaymentService { /* 只负责支付逻辑 */ }

@Component
public class NotificationService { /* 只负责通知 */ }

@Component
public class AuditLogService { /* 只负责审计日志 */ }
```

### 判断标准

```
变化原因检查：
  问：改变这个类的理由是什么？
  如果有多个不同的理由 → 违反 SRP
  如果只有一个理由 → 符合 SRP
```

---

## 二、开闭原则（OCP — Open-Closed Principle）

### 核心定义

> 软件实体应该对扩展开放，对修改关闭。

### 反面案例

```java
// ❌ 违反 OCP：新增支付方式要修改原有代码
public class PaymentService {
    public void pay(String type) {
        if ("alipay".equals(type)) {
            // 支付宝支付
        } else if ("wechat".equals(type)) {
            // 微信支付
        } else if ("card".equals(type)) {
            // 银行卡支付
        }
        // 每加一个支付方式都要改这里
    }
}
```

### 正面案例：策略模式

```java
// ✅ 符合 OCP：新增支付方式只需新增类，不改原有代码
public interface PaymentStrategy {
    void pay(Order order);
}

@Component
public class AlipayStrategy implements PaymentStrategy {
    @Override
    public void pay(Order order) { /* 支付宝支付逻辑 */ }
}

@Component
public class WechatPayStrategy implements PaymentStrategy {
    @Override
    public void pay(Order order) { /* 微信支付逻辑 */ }
}

@Service
public class PaymentService {
    @Autowired
    private Map<String, PaymentStrategy> strategies; // Spring 自动注入所有实现

    public void pay(String type, Order order) {
        PaymentStrategy strategy = strategies.get(type);
        if (strategy == null) throw new BizException("不支持的支付方式");
        strategy.pay(order);
    }
    // 新增支付方式只需新增一个实现类，PaymentService 不用改
}
```

### Spring 中的体现

```java
// Spring 的扩展点机制就是 OCP 的经典应用
// 定义扩展点（对修改关闭）
@FunctionalInterface
public interface BeanFactoryPostProcessor {
    void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) throws BeansException;
}

// 用户实现扩展点（对扩展开放）
@Component
public class MyBeanFactoryPostProcessor implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 在 Bean 创建前修改 Bean 定义
    }
}
```

---

## 三、里氏替换原则（LSP — Liskov Substitution Principle）

### 核心定义

> 子类对象可以替换父类对象，而程序行为不变。

### 反面案例

```java
// ❌ 违反 LSP：子类改变了父类行为
public class Rectangle {
    protected int width;
    protected int height;

    public void setWidth(int width) { this.width = width; }
    public void setHeight(int height) { this.height = height; }
    public int getArea() { return width * height; }
}

public class Square extends Rectangle {
    // 正方形：宽高必须相等
    @Override
    public void setWidth(int width) {
        super.setWidth(width);
        super.setHeight(width);
    }
    @Override
    public void setHeight(int height) {
        super.setWidth(height);
        super.setHeight(height);
    }
}

// 调用方
public void resize(Rectangle rect, int width, int height) {
    rect.setWidth(width);
    rect.setHeight(height);
    // 期望宽高分别设成了 width 和 height
    // 但如果是 Square，结果是 width * width
}

// 调用
Rectangle rect = new Square();
resize(rect, 5, 3); // 期望面积 15，实际面积 25 ❌
```

### 正面案例

```java
// ✅ 符合 LSP：正方形不应该继承矩形
public interface Shape {
    int getArea();
}

public class Rectangle implements Shape {
    private int width;
    private int height;

    @Override
    public int getArea() { return width * height; }
}

public class Square implements Shape {
    private int side;

    @Override
    public int getArea() { return side * side; }
}
```

### Spring 中的体现

```java
// List 是 ArrayList 和 LinkedList 的父类
// 它们可以互换使用而不影响程序行为（符合 LSP）
List<String> list = new ArrayList<>();  // ✅
list = new LinkedList<>();              // ✅ 可以替换
```

---

## 四、接口隔离原则（ISP — Interface Segregation Principle）

### 核心定义

> 客户端不应该依赖它不需要的接口。

### 反面案例

```java
// ❌ 违反 ISP：一个臃肿接口
public interface Animal {
    void fly();      // 鸟需要，鱼不需要
    void swim();     // 鱼需要，鸟不需要
    void run();      // 猫需要，鱼不需要
}

public class Dog implements Animal {
    @Override
    public void fly() { /* 狗不会飞，但必须实现 */ }
    @Override
    public void swim() { /* 狗会游泳 */ }
    @Override
    public void run() { /* 狗会跑 */ }
}
```

### 正面案例

```java
// ✅ 符合 ISP：拆分为多个小接口
public interface Flyable {
    void fly();
}

public interface Swimmable {
    void swim();
}

public interface Runnable {
    void run();
}

public class Dog implements Swimmable, Runnable {
    @Override
    public void swim() { /* 狗游泳 */ }
    @Override
    public void run() { /* 狗跑 */ }
    // 不需要实现 fly()
}

public class Bird implements Flyable, Runnable {
    @Override
    public void fly() { /* 鸟飞 */ }
    @Override
    public void run() { /* 鸟跑 */ }
    // 不需要实现 swim()
}
```

### Spring 中的体现

```java
// Spring 的接口都尽量小而专
// JdbcTemplate 实现了 JdbcOperations
// RestTemplate 实现了 RestOperations
// 用户按需注入

public interface InitializingBean {
    void afterPropertiesSet() throws Exception;
}

public interface DisposableBean {
    void destroy() throws Exception;
}
// 类按需实现，不需要实现所有接口
```

---

## 五、依赖倒置原则（DIP — Dependency Inversion Principle）

### 核心定义

> 高层模块不应该依赖低层模块，两者都应该依赖抽象。
> 抽象不应该依赖细节，细节应该依赖抽象。

### 反面案例

```java
// ❌ 违反 DIP：高层依赖低层
@Service
public class OrderService {
    private MySQLOrderRepository repository = new MySQLOrderRepository(); // 直接依赖实现

    public void createOrder(Order order) {
        repository.save(order); // 耦合具体实现
    }
}

public class MySQLOrderRepository {
    public void save(Order order) { /* MySQL 实现 */ }
}
```

### 正面案例

```java
// ✅ 符合 DIP：依赖抽象
// 1. 定义抽象
public interface OrderRepository {
    void save(Order order);
    Order findById(Long id);
}

// 2. 低层实现
@Repository
public class MySQLOrderRepository implements OrderRepository {
    @Override
    public void save(Order order) { /* MySQL 实现 */ }
    @Override
    public Order findById(Long id) { /* MySQL 实现 */ }
}

@Repository
public class RedisOrderRepository implements OrderRepository {
    @Override
    public void save(Order order) { /* Redis 实现 */ }
    @Override
    public Order findById(Long id) { /* Redis 实现 */ }
}

// 3. 高层依赖抽象
@Service
public class OrderService {
    private final OrderRepository repository; // 依赖抽象，不依赖实现

    @Autowired
    public OrderService(OrderRepository repository) {
        this.repository = repository; // 由 Spring 注入具体实现
    }

    public void createOrder(Order order) {
        repository.save(order); // 不知道具体是 MySQL 还是 Redis
    }
}
```

### Spring 中的体现

```java
// Spring 的依赖注入就是 DIP 的最佳实践
@Service
public class UserService {
    // 依赖接口，不依赖实现类
    private final UserRepository userRepository;

    // 由 Spring 注入具体实现（MySQL/Redis/MongoDB...）
    @Autowired
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
}
```

---

## 六、合成复用原则（CRP — Composite Reuse Principle）

### 核心定义

> 尽量使用组合/聚合，而不是继承来实现复用。

### 继承 vs 组合

```java
// ❌ 继承复用：类耦合高
public class A { void method() { /* ... */ } }

public class B extends A {  // B 和 A 强耦合
    // B 继承了 A 的所有方法
}

// 问题：A 改变 → B 可能受影响
// 问题：单继承限制
```

```java
// ✅ 组合复用：松耦合
public class A { void method() { /* ... */ } }

public class B {
    private A a;  // 组合：has-a 而非 is-a

    public B(A a) { this.a = a; }

    public void doSomething() {
        a.method(); // 委托给 A
    }
}

// 优点：可以运行时替换 A 的实现
// 优点：符合 OCP
```

### Spring 中的体现

```java
// Spring 大量使用组合而非继承
// 为什么 Spring Bean 不是继承某个基类？
// 因为 Spring 用组合 + 依赖注入实现所有功能

@Component
public class OrderService {
    @Autowired
    private PaymentService paymentService;  // 组合

    @Autowired
    private NotificationService notificationService;  // 组合

    @Autowired
    private InventoryService inventoryService;  // 组合
    // 所有功能通过组合实现，不继承任何基类
}
```

---

## 七、迪米特法则（LoD — Law of Demeter）

### 核心定义

> 只与直接的朋友通信，不要和陌生人说话。

### 反面案例

```java
// ❌ 违反 LoD：调用链过长
public class Customer {
    private Wallet wallet;
    public Wallet getWallet() { return wallet; }
}

public class Wallet {
    private double balance;
    public double getBalance() { return balance; }
}

public class OrderService {
    public void printCustomerBalance(Customer customer) {
        // 链条太长：客户 → 钱包 → 余额
        double balance = customer.getWallet().getBalance(); // ❌ 直接访问了陌生类
    }
}
```

### 正面案例

```java
// ✅ 符合 LoD：通过直接朋友访问
public class Customer {
    private Wallet wallet;

    public double getBalance() {
        return wallet.getBalance(); // 自己内部处理，不暴露内部结构
    }
}

public class OrderService {
    public void printCustomerBalance(Customer customer) {
        double balance = customer.getBalance(); // ✅ 只和 Customer 通信
    }
}
```

### Spring 中的体现

```java
// Spring MVC 中 Controller 只和 Service 层交互
// 不直接操作 Repository/DAO
@RestController
public class UserController {
    @Autowired
    private UserService userService; // 直接朋友

    // ✅ 只调用 Service，不直接操作 Repository
    public UserVO getUser(Long id) {
        return userService.getUserById(id); // ✅ 只和直接朋友通信
    }
}
```

---

## 八、六大原则对比总结

| 原则 | 缩写 | 核心 | 关键词 |
|------|------|------|--------|
| 单一职责 | SRP | 一个类只做一件事 | 职责分离 |
| 开闭原则 | OCP | 对扩展开放，对修改关闭 | 扩展优于修改 |
| 里氏替换 | LSP | 子类可替换父类 | is-a 关系正确 |
| 接口隔离 | ISP | 接口要小而专 | 拒绝臃肿接口 |
| 依赖倒置 | DIP | 依赖抽象而非实现 | 面向接口编程 |
| 合成复用 | CRP | 组合优于继承 | has-a 优于 is-a |
| 迪米特法则 | LoD | 只和直接朋友通信 | 不要和陌生人说话 |

### 六大原则在 Spring 源码中的体现

```
Spring 源码               │ 体现的原则
─────────────────────────┼───────────────────
BeanFactoryPostProcessor  │ OCP（扩展点机制）
@Inject/@Autowired        │ DIP（依赖抽象）
JdbcTemplate/RabbitTemplate│ ISP（专用接口）
BeanDefinitionBuilder     │ CRP（组合优于继承）
JdbcTemplate 只调 Connection│ LoD（直接朋友）
@Scope("prototype") 新实例│ LSP（子类可替换父类）
```

---

## 九、高频面试题

**Q1: SOLID 原则分别指什么？**
> S（Single）单一职责：一个类只负责一件事。O（Open-Closed）开闭原则：对扩展开放，对修改关闭，用策略模式、模板方法实现。L（Liskov）里氏替换：子类可以替换父类，不改变程序正确性。I（Interface Segregation）接口隔离：接口要小而专，不强迫实现不需要的方法。D（Dependency Inversion）依赖倒置：依赖抽象不依赖实现，高层模块和底层模块都依赖抽象。

**Q2: 开闭原则如何落地？**
> 核心手段是「面向接口编程 + 策略模式」。定义抽象接口（对扩展开放），具体实现类实现接口（新增功能只需新增类），业务代码依赖接口而非具体实现（对修改关闭）。典型场景：支付方式、消息发送、日志记录等。Spring 的 BeanFactoryPostProcessor、Servlet 的 Filter 都是开闭原则的经典应用。

**Q3: 依赖倒置和依赖注入有什么区别？**
> DIP 是设计原则（高层依赖抽象），DI 是实现手段（Spring 通过反射注入实现）。DIP 告诉我们应该怎么做，DI 告诉我们怎么落地。依赖注入是 DIP 的一种具体实现方式。

**Q4: 什么情况下应该用继承而不是组合？**
> 当子类「是」父类的一种（is-a 关系），且子类完全继承父类的所有行为时用继承。当子类「有」某个功能（has-a 关系）时用组合。在 Java 中，由于没有多重继承，且继承耦合度高，组合通常优于继承。

**Q5: Spring 为什么大量使用组合而不是继承？**
> 组合比继承更灵活：① 组合可以运行时替换组件，继承是编译时静态绑定；② 组合没有单继承限制；③ 组合降低了类之间的耦合度；④ Spring 用 Bean 容器管理组件，通过 DI 实现组合，避免了继承带来的强耦合。
