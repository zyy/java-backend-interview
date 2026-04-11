---
layout: default
title: 策略模式（Strategy Pattern）
---

# 策略模式（Strategy Pattern）：消除 if-else 的利器

> 本文系统讲解策略模式的核心思想、与工厂/状态模式的区别、JDK/Spring 源码应用，以及实战面试题

---

## 一、核心思想

策略模式（Strategy Pattern）是一种**行为型设计模式**，它将**一组算法/行为**封装为独立的策略对象，使得它们可以**在运行时被动态替换**，而客户端代码无需改动。

### 1.1 模式结构

```
┌─────────────────────┐       ┌─────────────────────┐
│     Context         │       │   <<interface>>    │
│  (持有并使用策略)    │ ──── │     Strategy        │
│                     │       │  (策略接口)         │
└─────────────────────┘       └─────────────────────┘
                                    △  △  △
                    ┌──────────────┐│  │  │┌──────────────┐
                    │ StrategyA   ││  │  ││ StrategyB   │
                    │ (具体策略A)  ││  │  ││ (具体策略B)  │
                    └──────────────┘│  │  │└──────────────┘
                                   ┌─┘  │  └─┐
                    ┌──────────────┐┌───┘  └───┐┌──────────────┐
                    │ StrategyC   ││          ││ StrategyD   │
                    │ (具体策略C)  ││          ││ (具体策略D)  │
                    └──────────────┘└──────────┘└──────────────┘
```

**策略接口（Strategy）**：定义所有具体策略的公共接口，通常包含一个 `execute()` 或 `doSomething()` 方法。

**具体策略（ConcreteStrategy）**：实现策略接口，提供算法的具体实现。

**上下文（Context）**：持有一个策略对象的引用，通过策略接口调用算法，不关心具体是哪个策略。

### 1.2 为什么需要策略模式？

考虑一个电商系统的价格计算场景：

```java
// ❌ 不用策略模式：大量 if-else，难以维护
public double calculatePrice(Order order, String userType) {
    if ("VIP".equals(userType)) {
        // VIP 逻辑：打折、积分翻倍...
        double price = order.getBasePrice() * 0.8;
        order.addPoints((int)(price * 2));
        return price;
    } else if ("SVIP".equals(userType)) {
        // SVIP 逻辑：更低折扣、免运费...
        double price = order.getBasePrice() * 0.6;
        order.addPoints((int)(price * 3));
        order.setFreeShipping(true);
        return price;
    } else if ("LIMITED".equals(userType)) {
        // 限时折扣逻辑...
        // 30+ 种用户类型，每个都有一段独立逻辑
        ...
    }
    return order.getBasePrice();
}
```

上述代码的问题：
- **违反开闭原则**：新增用户类型必须修改原有代码
- **单一职责缺失**：一个方法承担了所有算法的职责
- **测试困难**：无法单独测试某一个算法的正确性
- **代码膨胀**：1000 行方法，难以维护

**用策略模式重构：**

```java
// 1. 定义策略接口
public interface PricingStrategy {
    double calculate(Order order);
}

// 2. 具体策略实现
public class VipPricingStrategy implements PricingStrategy {
    @Override
    public double calculate(Order order) {
        double price = order.getBasePrice() * 0.8;
        order.addPoints((int)(price * 2));
        return price;
    }
}

public class SvipPricingStrategy implements PricingStrategy {
    @Override
    public double calculate(Order order) {
        double price = order.getBasePrice() * 0.6;
        order.addPoints((int)(price * 3));
        order.setFreeShipping(true);
        return price;
    }
}

public class NormalPricingStrategy implements PricingStrategy {
    @Override
    public double calculate(Order order) {
        return order.getBasePrice();
    }
}

// 3. 上下文持有策略
public class PriceCalculator {
    private PricingStrategy strategy;

    public void setStrategy(PricingStrategy strategy) {
        this.strategy = strategy;
    }

    public double calculate(Order order) {
        return strategy.calculate(order);
    }
}

// 4. 客户端使用
public class OrderService {
    private Map<String, PricingStrategy> strategyMap;

    @Autowired
    public OrderService(Map<String, PricingStrategy> strategyMap) {
        this.strategyMap = strategyMap;  // Spring 自动注入所有策略
    }

    public double checkout(Order order, String userType) {
        PricingStrategy strategy = strategyMap.get(userType);
        if (strategy == null) {
            strategy = strategyMap.get("NORMAL"); // 默认策略
        }
        return strategy.calculate(order);
    }
}
```

---

## 二、与相关模式的区别

### 2.1 策略模式 vs 简单工厂模式

| 对比维度 | 简单工厂 | 策略模式 |
|---------|---------|---------|
| **目的** | 创建对象（"这个对象是怎么 new 出来的"） | 选择行为（"我该用哪种算法来处理"） |
| **关注点** | 对象的创建过程封装 | 算法/行为的可替换性 |
| **客户端** | 客户端不直接 new 对象，交给工厂 | 客户端知道所有策略，需要选择 |
| **组合使用 | 工厂负责创建策略对象，策略负责执行算法 | 工厂创建策略，策略执行行为 |

**组合使用示例：**

```java
// 工厂负责创建策略（隐藏了 new 细节）
public class PricingStrategyFactory {
    public static PricingStrategy create(String userType) {
        return switch (userType) {
            case "VIP" -> new VipPricingStrategy();
            case "SVIP" -> new SvipPricingStrategy();
            case "LIMITED" -> new LimitedTimePricingStrategy();
            default -> new NormalPricingStrategy();
        };
    }
}

// 客户端调用工厂获取策略，然后使用策略
public class OrderService {
    public double checkout(Order order, String userType) {
        PricingStrategy strategy = PricingStrategyFactory.create(userType);
        return strategy.calculate(order);
    }
}
```

### 2.2 策略模式 vs 状态模式

| 对比维度 | 策略模式 | 状态模式 |
|---------|---------|---------|
| **行为发起者** | 客户端**主动**选择策略 | 状态对象**自动**决定行为 |
| **状态转移** | 客户端或外部代码决定切换 | 状态对象内部决定何时切换到下一个状态 |
| **策略间关系** | 各策略之间**平等**，可以互换 | 各状态之间有**先后/层级**关系 |
| **典型场景** | 支付方式、促销计算、压缩算法 | 订单流程、游戏状态、TCP 连接状态 |

**状态模式示例（订单流程）：**

```java
// 状态模式：状态决定行为，且状态自动流转
public interface OrderState {
    void handle(OrderContext context);
}

public class PendingState implements OrderState {
    @Override
    public void handle(OrderContext context) {
        // 待支付状态 -> 检查超时 -> 跳转到取消状态
        if (context.isTimeout()) {
            context.setState(new CancelledState());
        } else {
            context.setState(new PaidState());
        }
    }
}
```

**核心区别一句话：策略模式是"客户端请客点菜"，状态模式是"服务员根据情况自动上菜"。**

---

## 三、JDK 源码中的策略模式

### 3.1 Comparator — 最经典的策略模式

`java.util.Comparator` 是 JDK 中策略模式的最典型应用：

```java
// 策略接口
public interface Comparator<T> {
    int compare(T o1, T o2);
}

// 具体策略1：按年龄排序
Comparator<Person> byAge = (p1, p2) -> p1.getAge() - p2.getAge();

// 具体策略2：按姓名排序
Comparator<Person> byName = (p1, p2) -> p1.getName().compareTo(p2.getName());

// 具体策略3：按工资降序
Comparator<Person> bySalaryDesc = (p1, p2) -> p2.getSalary() - p1.getSalary();

// 上下文：Collections.sort
List<Person> people = new ArrayList<>();
Collections.sort(people, byAge);  // 运行时动态选择排序策略
people.sort(byName);
```

`Arrays.sort()`、`Collections.sort()`、`TreeSet`、`TreeMap` 都可以传入不同的 `Comparator` 策略，实现不同的排序/比较行为，而无需修改核心排序逻辑。

### 3.2 javax.crypto.Cipher — 加密算法策略

```java
// 策略接口：加密算法
public class CipherDemo {
    public static void encrypt(byte[] data, String algorithm) throws Exception {
        Cipher cipher = Cipher.getInstance(algorithm); // 策略创建
        cipher.init(Cipher.ENCRYPT_MODE, key);
        byte[] result = cipher.doFinal(data);          // 策略执行
    }

    public static void main(String[] args) {
        encrypt(data, "AES/CBC/PKCS5Padding");    // AES 策略
        encrypt(data, "RSA/ECB/OAEPWithSHA-256"); // RSA 策略
        encrypt(data, "DESede/CBC/PKCS5Padding");  // 3DES 策略
    }
}
```

### 3.3 javax.servlet.Filter — Web 请求过滤策略

```java
// 策略接口
public interface Filter {
    void doFilter(ServletRequest request, ServletResponse response, FilterChain chain);
}

// Spring Security 中的具体策略
public class UsernamePasswordAuthenticationFilter implements Filter {
    // 具体的认证策略实现
}

// 具体策略
public class CorsFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) {
        HttpServletResponse response = (HttpServletResponse) res;
        response.setHeader("Access-Control-Allow-Origin", "*");
        chain.doFilter(req, res);
    }
}
```

### 3.4 ThreadPoolExecutor 的拒绝策略

```java
// 策略接口
public interface RejectedExecutionHandler {
    void rejectedExecution(Runnable r, ThreadPoolExecutor executor);
}

// 策略1：调用者执行
public class CallerRunsPolicy implements RejectedExecutionHandler { ... }

// 策略2：丢弃任务，抛异常
public class AbortPolicy implements RejectedExecutionHandler { ... }

// 策略3：丢弃最老的任务
public class DiscardOldestPolicy implements RejectedExecutionHandler { ... }

// 策略4：静默丢弃
public class DiscardPolicy implements RejectedExecutionHandler { ... }

// 上下文
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    2, 4, 60, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(100),
    new DiscardOldestPolicy()  // 运行时选择丢弃策略
);
```

---

## 四、Spring 中的策略模式

### 4.1 InstantiationStrategy — Bean 实例化策略

Spring 在创建 Bean 实例时使用了策略模式：

```java
// 策略接口
public interface InstantiationStrategy {
    Object instantiate(RootBeanDefinition bd, String beanName, BeanFactory owner);
}

// 具体策略1：cglib 动态代理
public class CglibSubclassingInstantiationStrategy implements InstantiationStrategy {
    @Override
    public Object instantiate(...) {
        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(bd.getBeanClass());
        return enhancer.create();
    }
}

// 具体策略2：简单实例化
public class SimpleInstantiationStrategy implements InstantiationStrategy {
    @Override
    public Object instantiate(...) {
        return bd.getBeanClass().getDeclaredConstructor().newInstance();
    }
}
```

Spring 通过 `AbstractAutowireCapableBeanFactory` 来选择使用哪种实例化策略，从而在构造器注入和 setter 注入之间切换。

### 4.2 ContentNegotiatingViewResolver — 视图解析策略

```java
// Spring 根据请求的 Accept 头选择不同的视图解析策略
// text/html -> InternalResourceView
// application/json -> MappingJackson2JsonView
// application/xml -> MarshallingView

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML)
            .mediaType("html", MediaType.TEXT_HTML);
    }
}
```

### 4.3 Resource 接口 — 资源加载策略

```java
// 策略接口：不同资源加载方式
public interface Resource {
    InputStream getInputStream() throws IOException;
    boolean exists();
    long contentLength();
}

// ClassPathResource：classpath 下加载
public class ClassPathResource implements Resource { ... }

// FileSystemResource：文件系统加载
public class FileSystemResource implements Resource { ... }

// UrlResource：URL 加载
public class UrlResource implements Resource { ... }

// ServletContextResource：Web 上下文加载
public class ServletContextResource implements Resource { ... }
```

### 4.4 FormatAnnotationFormatterFactory — 数据格式化策略

Spring MVC 用策略模式处理 `@DateTimeFormat`、`@NumberFormat` 等注解，根据字段类型选择不同的格式化策略。

---

## 五、实战场景

### 5.1 支付系统策略

```java
// 策略接口
public interface PaymentStrategy {
    /**
     * 支付
     * @param order 订单
     * @return 支付结果
     */
    PayResult pay(Order order);

    /**
     * 退款
     * @param order 订单
     * @return 退款结果
     */
    RefundResult refund(Order order);

    /**
     * 获取支付渠道名称
     */
    String getChannel();
}

// 支付宝策略
@Service
@Order(1) // 控制排序
public class AlipayStrategy implements PaymentStrategy {
    @Autowired private AlipayClient alipayClient;

    @Override
    public PayResult pay(Order order) {
        // 调用支付宝 SDK
        AlipayTradePagePayRequest request = new AlipayTradePagePayRequest();
        request.setBizContent("{...}");
        return alipayClient.pageExecute(request);
    }

    @Override
    public RefundResult refund(Order order) {
        // 调用支付宝退款 API
        AlipayTradeRefundRequest request = new AlipayTradeRefundRequest();
        return alipayClient.execute(request);
    }

    @Override
    public String getChannel() {
        return "ALIPAY";
    }
}

// 微信支付策略
@Service
@Order(2)
public class WechatPayStrategy implements PaymentStrategy {
    @Override
    public PayResult pay(Order order) {
        // 调用微信支付统一下单 API
        return wechatPayService.unifiedOrder(order);
    }

    @Override
    public RefundResult refund(Order order) {
        return wechatPayService.refund(order);
    }

    @Override
    public String getChannel() {
        return "WECHAT";
    }
}

// 银行卡策略
@Service
@Order(3)
public class BankCardStrategy implements PaymentStrategy {
    @Override
    public PayResult pay(Order order) {
        // 银行卡支付逻辑
        return bankService.pay(order);
    }

    @Override
    public RefundResult refund(Order order) {
        return bankService.refund(order);
    }

    @Override
    public String getChannel() {
        return "BANK_CARD";
    }
}

// 积分支付策略
@Service
@Order(4)
public class PointsStrategy implements PaymentStrategy {
    @Override
    public PayResult pay(Order order) {
        User user = userService.getCurrentUser();
        int points = (int) (order.getTotalAmount() * 100);
        if (user.getPoints() < points) {
            throw new InsufficientPointsException();
        }
        user.deductPoints(points);
        return PayResult.success(order.getOrderId(), "积分支付");
    }

    @Override
    public RefundResult refund(Order order) {
        int points = (int) (order.getTotalAmount() * 100);
        userService.addPoints(order.getUserId(), points);
        return RefundResult.success(order.getOrderId());
    }

    @Override
    public String getChannel() {
        return "POINTS";
    }
}

// 支付服务：使用策略
@Service
public class PaymentService {
    private final Map<String, PaymentStrategy> strategyMap;

    @Autowired
    public PaymentService(Map<String, PaymentStrategy> strategyMap) {
        // Spring 自动注入所有 PaymentStrategy 实现，key 为 bean 名称
        this.strategyMap = strategyMap;
    }

    public PayResult pay(Order order, String channel) {
        PaymentStrategy strategy = strategyMap.get(channel.toLowerCase() + "Strategy");
        if (strategy == null) {
            throw new UnsupportedPaymentChannelException(channel);
        }
        log.info("使用支付渠道: {}", strategy.getChannel());
        return strategy.pay(order);
    }

    // 查询所有可用支付渠道
    public List<String> getAvailableChannels() {
        return strategyMap.values().stream()
            .map(PaymentStrategy::getChannel)
            .collect(Collectors.toList());
    }
}
```

### 5.2 价格计算策略

```java
// 促销上下文
public class PromotionContext {
    private String promotionType;
    private BigDecimal threshold;   // 满减门槛
    private BigDecimal discount;    // 折扣/金额
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    // ...
}

// 策略接口
public interface PromotionStrategy {
    BigDecimal apply(Order order, PromotionContext context);
}

// 普通价策略
public class NormalPricingStrategy implements PromotionStrategy {
    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        return order.getBasePrice();
    }
}

// VIP 折扣策略
public class VipDiscountStrategy implements PromotionStrategy {
    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        BigDecimal price = order.getBasePrice();
        BigDecimal vipDiscount = price.multiply(new BigDecimal("0.85"));
        // VIP 额外积分
        order.addPoints(vipDiscount.multiply(new BigDecimal("2")).intValue());
        return vipDiscount;
    }
}

// 限时折扣策略
public class FlashSaleStrategy implements PromotionStrategy {
    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        // 限时折扣：通常是固定折扣，如 7 折
        return order.getBasePrice().multiply(new BigDecimal("0.7"));
    }
}

// 满减活动策略
public class FullReductionStrategy implements PromotionStrategy {
    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        BigDecimal basePrice = order.getBasePrice();
        BigDecimal threshold = context.getThreshold();
        BigDecimal discount = context.getDiscount();

        if (basePrice.compareTo(threshold) >= 0) {
            // 满 threshold 减 discount
            return basePrice.subtract(discount);
        }
        return basePrice;
    }
}

// 阶梯满减策略（满100减10，满200减30，满500减100）
public class TieredFullReductionStrategy implements PromotionStrategy {
    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        BigDecimal price = order.getBasePrice();
        // 根据金额匹配阶梯
        if (price.compareTo(new BigDecimal("500")) >= 0) {
            return price.subtract(new BigDecimal("100"));
        } else if (price.compareTo(new BigDecimal("200")) >= 0) {
            return price.subtract(new BigDecimal("30"));
        } else if (price.compareTo(new BigDecimal("100")) >= 0) {
            return price.subtract(new BigDecimal("10"));
        }
        return price;
    }
}

// 组合优惠策略：叠加使用多个策略
public class CombinedPromotionStrategy implements PromotionStrategy {
    private final List<PromotionStrategy> strategies;

    public CombinedPromotionStrategy(List<PromotionStrategy> strategies) {
        this.strategies = strategies;
    }

    @Override
    public BigDecimal apply(Order order, PromotionContext context) {
        BigDecimal price = order.getBasePrice();
        for (PromotionStrategy strategy : strategies) {
            price = strategy.apply(order, context);
        }
        return price;
    }
}
```

### 5.3 Java 8 Lambda 实现策略（无接口也能用策略）

```java
// 传统策略模式需要定义接口和实现类
// Java 8 之后，可以用 Lambda 表达式更简洁地实现策略

public class LambdaStrategyDemo {

    // 定义策略类型（函数式接口）
    @FunctionalInterface
    public interface ValidationStrategy<T> {
        boolean validate(T t);
    }

    // 使用 Lambda 实现具体策略（无需创建新类）
    public static void main(String[] args) {
        List<String> inputs = Arrays.asList("13812345678", "abc123", "12345", "19999999999");

        // 策略1：验证手机号
        ValidationStrategy<String> phoneValidator = phone ->
            phone != null && phone.matches("^1[3-9]\\d{9}$");

        // 策略2：验证密码强度
        ValidationStrategy<String> passwordValidator = password ->
            password != null && password.length() >= 8 &&
            password.matches(".*[A-Z].*") &&
            password.matches(".*\\d.*");

        // 策略3：验证邮箱
        ValidationStrategy<String> emailValidator = email ->
            email != null && email.matches("^[\\w.-]+@[\\w.-]+\\.\\w+$");

        // 过滤手机号
        List<String> phones = inputs.stream()
            .filter(phoneValidator::validate)
            .collect(Collectors.toList());
        System.out.println("有效手机号: " + phones);

        // 灵活组合策略
        ValidationStrategy<String> combinedValidator = input ->
            phoneValidator.validate(input) ||
            passwordValidator.validate(input) ||
            emailValidator.validate(input);
    }
}
```

---

## 六、策略模式 + Spring 的高级用法

### 6.1 @Autowired Map<String, Strategy> 自动注入

这是 Spring 中策略模式最优雅的使用方式：

```java
@Service
public class OrderService {
    // Spring 自动注入所有 PricingStrategy 实现
    // key = bean 名称（首字母小写），value = bean 实例
    private final Map<String, PricingStrategy> strategyMap;

    @Autowired
    public OrderService(Map<String, PricingStrategy> strategyMap) {
        this.strategyMap = strategyMap;
    }

    public double calculatePrice(Order order, String userType) {
        PricingStrategy strategy = strategyMap.get(userType.toLowerCase() + "PricingStrategy");
        if (strategy == null) {
            strategy = strategyMap.get("normalPricingStrategy"); // 默认
        }
        return strategy.calculate(order);
    }
}
```

如果需要注入自定义的策略 key，可以使用 `@Qualifier` 注解：

```java
@Component("ALIPAY")
public class AlipayStrategy implements PaymentStrategy { ... }

@Component("WECHAT")
public class WechatPayStrategy implements PaymentStrategy { ... }
```

### 6.2 @PostConstruct 初始化 + 策略注册表

```java
@Service
public class ImageCompressService {
    private final Map<String, CompressStrategy> strategyMap = new ConcurrentHashMap<>();

    // 手动注册策略（更灵活，支持动态注册）
    @PostConstruct
    public void init() {
        strategyMap.put("jpg", new JpegCompressStrategy());
        strategyMap.put("png", new PngCompressStrategy());
        strategyMap.put("webp", new WebpCompressStrategy());
        strategyMap.put("gif", new GifCompressStrategy());
    }

    public byte[] compress(byte[] imageData, String format) {
        CompressStrategy strategy = strategyMap.get(format.toLowerCase());
        if (strategy == null) {
            throw new UnsupportedFormatException(format);
        }
        return strategy.compress(imageData);
    }

    // 动态注册新策略（支持插件扩展）
    public void registerStrategy(String format, CompressStrategy strategy) {
        strategyMap.put(format.toLowerCase(), strategy);
    }
}
```

### 6.3 Spring Boot 自动配置 + 策略模式

```java
@Configuration
public class PaymentStrategyConfig {
    @Bean
    public Map<String, PaymentStrategy> paymentStrategies(
            List<PaymentStrategy> strategies) {
        return strategies.stream()
            .collect(Collectors.toMap(
                s -> s.getChannel(),  // 用策略的渠道名作为 key
                Function.identity(),
                (v1, v2) -> v1  // 重复时保留前者
            ));
    }
}
```

---

## 七、面试高频题

### 面试题 1：什么是策略模式？它解决了什么问题？

**参考答案：**

策略模式是一种行为型设计模式，它定义了一系列算法/行为，将每一个算法封装为独立类，并使它们可以互换。

**解决的问题：**
1. **消除 if-else**：将大量条件分支重构为可替换的策略对象
2. **开闭原则**：新增策略无需修改原有代码，只需添加新类
3. **单一职责**：每个策略类只负责一种算法，职责清晰
4. **可测试性**：每个策略可单独测试
5. **运行时切换**：可以在运行时动态替换算法

**适用场景：**
- 需要在多个算法中选择一个
- 需要在不同场景下使用不同的业务规则
- 核心类有多个变体，不想用大量条件语句

---

### 面试题 2：策略模式和工厂模式有什么区别？

**参考答案：**

| 维度 | 工厂模式 | 策略模式 |
|------|---------|---------|
| **职责** | 负责创建对象（生产） | 负责执行行为（使用） |
| **关注点** | 对象是怎么被创建出来的 | 用哪个算法/策略来处理 |
| **客户端参与** | 客户端不直接 new，通过工厂获取 | 客户端需要了解策略之间的差异 |
| **调用次数** | 通常只调用一次（创建） | 可以多次调用（每次业务处理） |
| **典型方法** | `create()` | `execute()` / `calculate()` |
| **组合** | 常作为策略模式的底层支持 | 策略模式可反过来影响工厂的选择 |

两者经常组合使用：工厂负责创建策略对象，策略模式负责使用这些对象。

---

### 面试题 3：JDK 中哪些地方用到了策略模式？请举例

**参考答案：**

1. **`Comparator<T>`**：不同的比较算法，`Collections.sort(list, comparator)` 传入不同比较器实现不同的排序逻辑

2. **`ThreadPoolExecutor` 的 `RejectedExecutionHandler`**：线程池满时选择不同的拒绝策略（AbortPolicy、CallerRunsPolicy、DiscardPolicy、DiscardOldestPolicy）

3. **`javax.servlet.Filter`**：不同的 Filter 实现不同的横切关注点（CorsFilter、AuthFilter、LoggingFilter）

4. **`javax.crypto.Cipher`**：选择不同的加密算法（AES、RSA、DES）

5. **`javax.naming.ldap.StartTlsRequest`**：TLS 版本协商

6. **`java.util.stream.Collectors`**：`toList()`、`toSet()`、`toMap()` 实际上也是收集策略

---

### 面试题 4：策略模式和状态模式有什么区别？

**参考答案：**

两者很容易混淆，关键区别在于**行为由谁发起**：

- **策略模式**：客户端**主动选择**使用哪个策略，策略之间是平等的、可互换的。切换由外部驱动。

- **状态模式**：状态对象**内部决定**何时切换到下一个状态，状态之间有先后关系。切换由状态自身驱动。

**举例：**
- 策略模式：购物车结算时，用户选择"支付宝"或"微信"支付——**用户主动选择**
- 状态模式：订单从"待支付"→"已支付"→"已发货"→"已完成"，状态自动流转——**状态自身决定流转**

---

### 面试题 5：如何在 Spring 中优雅地实现策略模式？

**参考答案：**

核心技巧是 `@Autowired Map<String, 接口名>` 自动注入：

```java
@Service
public class StrategyService {
    private final Map<String, DiscountStrategy> strategyMap;

    // Spring 自动注入所有 DiscountStrategy 实现
    @Autowired
    public StrategyService(Map<String, DiscountStrategy> strategyMap) {
        this.strategyMap = strategyMap;
    }

    public BigDecimal calculate(Order order) {
        String key = determineStrategyKey(order);
        DiscountStrategy strategy = strategyMap.get(key);
        return strategy.execute(order);
    }
}
```

**进阶技巧：**
1. 使用 `@Order` 控制策略优先级
2. 使用 `@Primary` 标记默认策略
3. 配合 `@Qualifier("beanName")` 自定义 key
4. 使用 `@PostConstruct` 做策略初始化
5. 注册表模式：提供 `registerStrategy()` 支持动态扩展

---

## 八、总结

策略模式是后端开发中最常用的设计模式之一，它的**核心价值**在于：

1. **消除 if-else 链**：用策略对象替代大量条件分支
2. **开闭原则**：新增策略不影响现有代码
3. **运行时可切换**：灵活应对业务规则变化
4. **与 Spring 天然契合**：`@Autowired Map<String,Strategy>` 自动注入所有策略

**记住一句话：策略模式就是"把 if-else 里的每一种分支逻辑，拆成独立的策略类，让它们实现同一个接口，然后在运行时选择用哪个"。**

---

> 📚 **延伸阅读**
> - [Head First 设计模式 - 策略模式章节](https://book.douban.com/subject/2243615/)
> - [JDK 源码：Comparator 设计与实现](https://docs.oracle.com/javase/8/docs/api/java/util/Comparator.html)
> - [Spring 源码：InstantiationStrategy](https://github.com/spring-projects/spring-framework)
