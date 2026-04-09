---
layout: default
title: 设计模式实战应用
---
# 设计模式实战应用

## 🎯 面试题：Spring 源码中用到了哪些设计模式？

> 设计模式不能死记硬背，要在 Spring 源码中理解其实际应用。Spring 框架本身就是一个设计模式的集大成者。

---

## 一、Spring 核心设计模式

### 1. 单例模式（Singleton）

```java
// Spring Bean 默认就是单例
// Spring 通过 ConcurrentHashMap 管理单例 Bean

// 三种单例注册方式
DefaultSingletonBeanRegistry registry = new DefaultSingletonBeanRegistry();

// 1. 直接注册
registry.registerSingleton("orderService", new OrderServiceImpl());

// 2. 构造方法自动注册
// @Component 默认就是单例

// 3. 枚举单例（最安全，防反射和反序列化）
public enum SingletonEnum {
    INSTANCE;
    private Object data;
    public Object getData() { return data; }
}
```

### 2. 工厂模式（Factory）

```java
// Spring BeanFactory 就是工厂模式
ConfigurableBeanFactory bf = new DefaultListableBeanFactory();

// 方式一：BeanDefinitionRegistry 注册 Bean 定义
AbstractBeanDefinition bd = BeanDefinitionBuilder
    .rootBeanDefinition(OrderServiceImpl.class)
    .getBeanDefinition();
((BeanDefinitionRegistry) bf).registerBeanDefinition("orderService", bd);

// 方式二：FactoryBean 接口
public class MyFactoryBean<T> implements FactoryBean<T> {
    @Override
    public T getObject() { return new OrderService(); }
    @Override
    public Class<?> getObjectType() { return OrderService.class; }
}

// Spring 调用 getObject() 获取真实 Bean
```

### 3. 策略模式（Strategy）

```java
// Spring 的 InstantiationStrategy 策略接口
public interface InstantiationStrategy {
    Object instantiate(RootBeanDefinition bd, String beanName,
                       BeanFactory owner, Constructor<?> ctor, Object[] args)
        throws BeansException;
}

// 两种实现策略
public class SimpleInstantiationStrategy implements InstantiationStrategy { ... }
public class CglibSubclassingInstantiationStrategy extends SimpleInstantiationStrategy { ... }

// Spring 根据情况选择策略：
// 有构造函数 → CGLIB 动态代理
// 无构造函数 / 构造函数参数简单 → 反射
```

### 4. 观察者模式（Observer）

```java
// Spring 事件机制就是观察者模式
// 三个角色：ApplicationEvent（事件）、ApplicationListener（监听器）、ApplicationEventPublisher（发布者）

// 1. 定义事件
public class OrderCreatedEvent extends ApplicationEvent {
    private final Order order;
    public OrderCreatedEvent(Object source, Order order) {
        super(source);
        this.order = order;
    }
}

// 2. 定义监听器
@Component
public class OrderCreatedListener implements ApplicationListener<OrderCreatedEvent> {
    @Override
    public void onApplicationEvent(OrderCreatedEvent event) {
        // 发短信通知、发送 MQ 消息等
        sendNotification(event.getOrder());
    }
}

// 3. 发布事件
@Service
public class OrderService {
    @Autowired
    private ApplicationEventPublisher publisher;

    public void createOrder(Order order) {
        // 创建订单逻辑...
        publisher.publishEvent(new OrderCreatedEvent(this, order));
    }
}
```

### 5. 模板方法模式（Template Method）

```java
// JdbcTemplate 就是模板方法模式
// 固定流程：获取连接 → 执行 SQL → 处理结果 → 关闭连接

jdbcTemplate.query("SELECT * FROM orders WHERE user_id = ?",
    new Object[]{userId},
    (rs, rowNum) -> {
        Order order = new Order();
        order.setId(rs.getLong("id"));
        order.setUserId(rs.getLong("user_id"));
        return order;
    });

// execute 源码：
public <T> T execute(StatementCallback<T> action) {
    Connection con = DataSourceUtils.getConnection(this);
    Statement stmt = null;
    try {
        stmt = con.createStatement();
        return action.doInStatement(stmt); // 钩子方法，子类实现
    } finally {
        closeStatement(stmt);
        DataSourceUtils.releaseConnection(con, this);
    }
}
```

### 6. 装饰器模式（Decorator）

```java
// JDK IO 流就是装饰器模式
// BufferedInputStream = 装饰器 + InputStream = 被装饰对象

InputStream in = new FileInputStream("data.txt");           // 核心：读取文件
BufferedInputStream bin = new BufferedInputStream(in);       // 装饰：缓冲加速
GzipInputStream gin = new GzipInputStream(bin);              // 装饰： gzip 解压
DataInputStream din = new DataInputStream(gin);                 // 装饰：解析基本类型

// Spring 中的装饰器：
HttpServletRequestWrapper requestWrapper = new ContentCachingRequestWrapper(request);
```

### 7. 代理模式（Proxy）

```java
// Spring AOP 基于代理模式
// JDK 动态代理：目标类实现了接口
// CGLIB 动态代理：目标类没有实现接口

// Spring AOP 自动选择：
// 有接口 → JDK 动态代理
// 无接口 → CGLIB

// 事务代理（声明式事务的核心）
TransactionInterceptor.invoke(() -> {
    // 实际执行业务方法
    return methodProxy.invoke(target, args);
});
// 代理对象在方法执行前后添加了：
// 前：开启事务、设置隔离级别
// 后：提交事务
// 异常：回滚事务
```

---

## 二、生产代码中的设计模式

### 支付方式策略模式

```java
// 策略接口
public interface PayStrategy {
    PayResult pay(Order order);
    PayResult refund(Order order);
}

// 策略实现
@Service
public class AlipayStrategy implements PayStrategy {
    @Override
    public PayResult pay(Order order) { /* 支付宝支付 */ }
    @Override
    public PayResult refund(Order order) { /* 支付宝退款 */ }
}

@Service
public class WechatPayStrategy implements PayStrategy { ... }
@Service
public class UnionPayStrategy implements PayStrategy { ... }

// 策略工厂（简单工厂 + 策略）
@Service
public class PayStrategyFactory {
    @Autowired
    private Map<String, PayStrategy> strategies;

    public PayStrategy getStrategy(String type) {
        PayStrategy strategy = strategies.get(type);
        if (strategy == null) throw new BizException("不支持的支付方式");
        return strategy;
    }
}

// 使用
@Service
public class OrderService {
    @Autowired
    private PayStrategyFactory factory;

    public void pay(Long orderId, String payType) {
        PayStrategy strategy = factory.getStrategy(payType);
        strategy.pay(order);
    }
}
```

---

## 三、Spring 源码设计模式汇总

```
┌─────────────────────────────────────────────────────┐
│ Spring 源码               │ 设计模式                 │
├──────────────────────────┼──────────────────────────┤
│ BeanFactory              │ 工厂模式                 │
│ FactoryBean              │ 工厂 + 策略              │
│ JdbcTemplate            │ 模板方法                  │
│ ApplicationEvent        │ 观察者                    │
│ @Transactional          │ 代理模式                  │
│ ResourceLoader          │ 策略模式                  │
│ BeanDefinitionRegistry  │ 装饰器模式                │
│ Environment             │ 组合模式                  │
│ BeanWrapper             │ 装饰器模式                │
│ PathMatchingResourcePatternResolver │ 策略模式 │
└──────────────────────────┴──────────────────────────┘
```

---

## 四、高频面试题

**Q1: Spring 用到了哪些设计模式？**
> Spring 是设计模式教科书：① 工厂模式：BeanFactory 根据 Bean 定义创建 Bean；② 单例模式：Spring Bean 默认单例；③ 模板方法：JdbcTemplate.execute() 固定流程；④ 观察者模式：ApplicationEvent + ApplicationListener；⑤ 代理模式：@Transactional 基于 AOP 动态代理；⑥ 策略模式：InstantiationStrategy 根据情况选择反射或 CGLIB；⑦ 装饰器模式：HttpServletRequestWrapper 增强请求。

**Q2: 装饰器模式和代理模式的区别？**
> 核心区别在于「目的」不同。装饰器模式目的是「增强对象功能」，运行时动态组合，功能可以叠加（如 BufferedInputStream + GzipInputStream + DataInputStream 层层包装）；代理模式目的是「控制对对象的访问」，在访问前后做拦截，不改变被代理对象的接口（如 Spring AOP 事务、权限控制）。Spring AOP 底层用代理实现，但语义上是代理模式。

**Q3: Spring 为什么默认使用单例模式？**
> 三个原因：① 性能：避免每次请求都创建 Bean，减少 GC 压力；② 共享状态：Bean 通常持有共享数据（数据库连接池、缓存等），单例保证共享；③ 设计哲学：Spring 管理的是无状态或有状态但线程安全的 Bean。需要注意的是，有状态的 Bean 不应该用单例，应该用 prototype 原型模式。

**Q4: 策略模式和工厂模式的区别？**
> 工厂模式解决的是「对象创建」问题（我不知道具体类型，让工厂给我一个）；策略模式解决的是「行为选择」问题（有多种策略，选择一个执行）。可以结合使用：工厂负责创建策略对象（简单工厂），运行时根据条件选择策略（策略模式）。Spring 的 `@Autowired Map<String, xxxStrategy>` 就是工厂 + 策略的组合。
