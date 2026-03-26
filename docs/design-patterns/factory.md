---
layout: default
title: 工厂模式（Factory Pattern）：从简单工厂到抽象工厂
---
# 工厂模式（Factory Pattern）：从简单工厂到抽象工厂

> 工厂模式是创建型设计模式的核心，通过封装对象创建逻辑，实现创建与使用的解耦

## 🎯 面试重点

- 简单工厂、工厂方法、抽象工厂三者的区别与演进
- 开闭原则在三者的体现
- JDK与Spring源码中的工厂模式应用
- 实际项目中的工厂模式落地

## 📖 一、简单工厂（Simple Factory）

### 1.1 核心思想

简单工厂不是一个标准的设计模式，而是一种编程习惯。它通过一个工厂类来封装对象的创建逻辑，客户端只需传入参数即可获得对象，无需关心创建细节。

**优点：**
- 客户端与具体产品解耦
- 创建逻辑集中管理，便于维护

**缺点：**
- 违反开闭原则（添加新产品需修改工厂类）
- 工厂类职责过重，违反单一职责原则

### 1.2 代码示例

```java
/**
 * 产品接口
 */
public interface Product {
    void use();
}

/**
 * 具体产品A
 */
public class ProductA implements Product {
    @Override
    public void use() {
        System.out.println("使用产品A");
    }
}

/**
 * 具体产品B
 */
public class ProductB implements Product {
    @Override
    public void use() {
        System.out.println("使用产品B");
    }
}

/**
 * 简单工厂 - 使用switch分支
 * 问题：添加新产品需要修改工厂类，违反开闭原则
 */
public class SimpleFactory {
    public static Product create(String type) {
        switch (type) {
            case "A":
                return new ProductA();
            case "B":
                return new ProductB();
            default:
                throw new IllegalArgumentException("未知产品类型: " + type);
        }
    }
}

/**
 * 客户端使用
 */
public class Client {
    public static void main(String[] args) {
        Product product = SimpleFactory.create("A");
        product.use();
    }
}
```

### 1.3 简单工厂的改进方案

**方案一：反射机制**

```java
/**
 * 使用反射的简单工厂
 * 优点：添加新产品无需修改工厂类
 * 缺点：反射性能较低，参数字符串容易写错
 */
public class ReflectionFactory {
    public static <T> T create(Class<T> clazz) {
        try {
            return clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("创建对象失败", e);
        }
    }
}

// 使用方式
Product product = ReflectionFactory.create(ProductA.class);
```

**方案二：配置文件 + 反射**

```java
/**
 * 基于配置文件的工厂
 * 通过配置文件解耦，支持运行时动态扩展
 */
public class ConfigurableFactory {
    private static final Properties config = new Properties();
    
    static {
        try (InputStream is = ConfigurableFactory.class
                .getResourceAsStream("/factory.properties")) {
            config.load(is);
        } catch (IOException e) {
            throw new RuntimeException("加载配置失败", e);
        }
    }
    
    @SuppressWarnings("unchecked")
    public static <T> T create(String key) {
        String className = config.getProperty(key);
        try {
            Class<?> clazz = Class.forName(className);
            return (T) clazz.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("创建对象失败: " + key, e);
        }
    }
}

// factory.properties
// productA=com.example.ProductA
// productB=com.example.ProductB
```

## 📖 二、工厂方法（Factory Method）

### 2.1 核心思想

工厂方法模式定义一个创建对象的接口，让子类决定实例化哪一个类。工厂方法使一个类的实例化延迟到其子类。

**核心特点：**
- 一个工厂只生产一种产品
- 符合开闭原则（添加新产品只需添加新的工厂类）
- 符合单一职责原则（每个工厂只负责一个产品）

### 2.2 类图结构

```
       Product                 Creator
          ↑                       ↑
    ┌─────┴─────┐           ┌─────┴─────┐
ProductA    ProductB   ConcreteCreatorA  ConcreteCreatorB
                  ↑                ↑
           creates ProductA   creates ProductB
```

### 2.3 代码示例

```java
/**
 * 产品接口
 */
public interface Product {
    void use();
}

/**
 * 具体产品A
 */
public class ProductA implements Product {
    @Override
    public void use() {
        System.out.println("使用产品A");
    }
}

/**
 * 具体产品B
 */
public class ProductB implements Product {
    @Override
    public void use() {
        System.out.println("使用产品B");
    }
}

/**
 * 工厂接口 - 定义创建对象的抽象方法
 */
public interface Factory {
    Product create();
}

/**
 * 具体工厂A - 只负责创建产品A
 */
public class FactoryA implements Factory {
    @Override
    public Product create() {
        return new ProductA();
    }
}

/**
 * 具体工厂B - 只负责创建产品B
 */
public class FactoryB implements Factory {
    @Override
    public Product create() {
        return new ProductB();
    }
}

/**
 * 客户端使用
 * 添加新产品时：只需新增ProductC和FactoryC，无需修改现有代码
 */
public class Client {
    public static void main(String[] args) {
        Factory factory = new FactoryA();
        Product product = factory.create();
        product.use();
    }
}
```

### 2.4 工厂方法的优化

**问题：** 每个产品都需要一个工厂类，类数量爆炸

**优化：使用泛型或反射减少工厂类**

```java
/**
 * 泛型工厂 - 减少工厂类数量
 */
public class GenericFactory<T extends Product> implements Factory {
    private final Class<T> productClass;
    
    public GenericFactory(Class<T> productClass) {
        this.productClass = productClass;
    }
    
    @Override
    public Product create() {
        try {
            return productClass.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            throw new RuntimeException("创建对象失败", e);
        }
    }
}

// 使用方式
Factory factoryA = new GenericFactory<>(ProductA.class);
Factory factoryB = new GenericFactory<>(ProductB.class);
```

## 📖 三、抽象工厂（Abstract Factory）

### 3.1 核心思想

抽象工厂模式提供一个创建一系列相关或相互依赖对象的接口，无需指定它们具体的类。

**核心特点：**
- 一个工厂可以创建多种产品（产品族）
- 产品族内的产品之间有约束关系
- 切换产品族只需切换工厂

**应用场景：**
- 跨平台UI组件（Windows按钮、Mac按钮）
- 数据库访问（MySQL连接池、Oracle连接池）
- 主题切换（亮色主题、暗色主题）

### 3.2 类图结构

```
          AbstractFactory
                ↑
      ┌─────────┴─────────┐
  MySQLFactory       OracleFactory
      ↓                    ↓
  ┌───┴───┐          ┌───┴───┐
Connection Command  Connection Command
  (MySQL) (MySQL)    (Oracle)(Oracle)
```

### 3.3 代码示例：数据库产品族

```java
/**
 * 抽象产品：数据库连接
 */
public interface Connection {
    void connect();
    void close();
}

/**
 * 抽象产品：SQL命令
 */
public interface Command {
    void execute(String sql);
}

/**
 * 具体产品：MySQL连接
 */
public class MySqlConnection implements Connection {
    @Override
    public void connect() {
        System.out.println("连接MySQL数据库");
    }
    
    @Override
    public void close() {
        System.out.println("关闭MySQL连接");
    }
}

/**
 * 具体产品：MySQL命令
 */
public class MySqlCommand implements Command {
    @Override
    public void execute(String sql) {
        System.out.println("MySQL执行: " + sql);
    }
}

/**
 * 具体产品：Oracle连接
 */
public class OracleConnection implements Connection {
    @Override
    public void connect() {
        System.out.println("连接Oracle数据库");
    }
    
    @Override
    public void close() {
        System.out.println("关闭Oracle连接");
    }
}

/**
 * 具体产品：Oracle命令
 */
public class OracleCommand implements Command {
    @Override
    public void execute(String sql) {
        System.out.println("Oracle执行: " + sql);
    }
}

/**
 * 抽象工厂 - 定义创建产品族的接口
 */
public interface DatabaseFactory {
    Connection createConnection();
    Command createCommand();
}

/**
 * 具体工厂：MySQL工厂
 * 负责创建MySQL相关的所有产品
 */
public class MySQLFactory implements DatabaseFactory {
    @Override
    public Connection createConnection() {
        return new MySqlConnection();
    }
    
    @Override
    public Command createCommand() {
        return new MySqlCommand();
    }
}

/**
 * 具体工厂：Oracle工厂
 * 负责创建Oracle相关的所有产品
 */
public class OracleFactory implements DatabaseFactory {
    @Override
    public Connection createConnection() {
        return new OracleConnection();
    }
    
    @Override
    public Command createCommand() {
        return new OracleCommand();
    }
}

/**
 * 客户端使用
 * 切换数据库只需切换工厂
 */
public class Client {
    private final DatabaseFactory factory;
    
    public Client(DatabaseFactory factory) {
        this.factory = factory;
    }
    
    public void work() {
        Connection conn = factory.createConnection();
        Command cmd = factory.createCommand();
        
        conn.connect();
        cmd.execute("SELECT * FROM users");
        conn.close();
    }
    
    public static void main(String[] args) {
        // 使用MySQL
        Client mysqlClient = new Client(new MySQLFactory());
        mysqlClient.work();
        
        // 切换到Oracle
        Client oracleClient = new Client(new OracleFactory());
        oracleClient.work();
    }
}
```

### 3.4 抽象工厂的扩展问题

**问题：** 添加新产品等级结构困难（如添加Transaction产品）

```java
/**
 * 解决方案：在抽象工厂中添加方法
 * 缺点：需要修改所有工厂类，违反开闭原则
 */
public interface DatabaseFactory {
    Connection createConnection();
    Command createCommand();
    Transaction createTransaction(); // 新增方法
}
```

## 📖 四、JDK中的工厂模式案例

### 4.1 Calendar.getInstance()

```java
/**
 * JDK Calendar工厂方法
 * java.util.Calendar
 */
public abstract class Calendar implements Serializable, Cloneable, Comparable<Calendar> {
    
    // 静态工厂方法
    public static Calendar getInstance() {
        return createCalendar(TimeZone.getDefault(), Locale.getDefault(Locale.Category.FORMAT));
    }
    
    public static Calendar getInstance(TimeZone zone) {
        return createCalendar(zone, Locale.getDefault(Locale.Category.FORMAT));
    }
    
    public static Calendar getInstance(Locale aLocale) {
        return createCalendar(TimeZone.getDefault(), aLocale);
    }
    
    public static Calendar getInstance(TimeZone zone, Locale aLocale) {
        return createCalendar(zone, aLocale);
    }
    
    // 内部根据Locale创建具体的Calendar实现
    private static Calendar createCalendar(TimeZone zone, Locale aLocale) {
        Calendar cal = null;
        
        if (aLocale.hasExtensions()) {
            String caltype = aLocale.getUnicodeLocaleType("ca");
            if (caltype != null) {
                switch (caltype) {
                    case "buddhist":
                        cal = new BuddhistCalendar(zone, aLocale);
                        break;
                    case "japanese":
                        cal = new JapaneseImperialCalendar(zone, aLocale);
                        break;
                    case "gregory":
                        cal = new GregorianCalendar(zone, aLocale);
                        break;
                }
            }
        }
        
        if (cal == null) {
            // 默认使用GregorianCalendar
            if (aLocale.equals(Locale.th_TH)) {
                cal = new BuddhistCalendar(zone, aLocale);
            } else if (aLocale.equals(Locale.ja_JP)) {
                cal = new JapaneseImperialCalendar(zone, aLocale);
            } else {
                cal = new GregorianCalendar(zone, aLocale);
            }
        }
        
        return cal;
    }
}

// 使用方式
Calendar calendar = Calendar.getInstance(); // 返回GregorianCalendar
Calendar japanCalendar = Calendar.getInstance(Locale.JAPAN); // 返回JapaneseImperialCalendar
```

### 4.2 DriverManager.getConnection()

```java
/**
 * JDBC DriverManager - 工厂模式的变体
 * java.sql.DriverManager
 */
public class DriverManager {
    
    // 注册的驱动列表
    private final static CopyOnWriteArrayList<DriverInfo> registeredDrivers 
        = new CopyOnWriteArrayList<>();
    
    // 工厂方法：根据URL创建连接
    public static Connection getConnection(String url) throws SQLException {
        return getConnection(url, new Properties());
    }
    
    public static Connection getConnection(String url, String user, String password) 
            throws SQLException {
        Properties info = new Properties();
        info.put("user", user);
        info.put("password", password);
        return getConnection(url, info);
    }
    
    public static Connection getConnection(String url, Properties info) 
            throws SQLException {
        // 遍历所有注册的驱动，找到能处理该URL的驱动
        for (DriverInfo driverInfo : registeredDrivers) {
            Driver driver = driverInfo.driver;
            try {
                if (driver.acceptsURL(url)) {
                    return driver.connect(url, info);
                }
            } catch (SQLException e) {
                // 继续尝试下一个驱动
            }
        }
        throw new SQLException("No suitable driver found for " + url);
    }
    
    // 注册驱动
    public static synchronized void registerDriver(Driver driver) 
            throws SQLException {
        registeredDrivers.addIfAbsent(new DriverInfo(driver));
    }
}

// 使用方式
Connection conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/test");
Connection conn2 = DriverManager.getConnection("jdbc:oracle:thin:@localhost:1521:orcl");
```

### 4.3 NumberFormat.getInstance()

```java
/**
 * NumberFormat工厂方法
 * java.text.NumberFormat
 */
public abstract class NumberFormat extends Format {
    
    // 工厂方法
    public static NumberFormat getInstance() {
        return getInstance(Locale.getDefault(Locale.Category.FORMAT), NUMBERSTYLE);
    }
    
    public static NumberFormat getInstance(Locale inLocale) {
        return getInstance(inLocale, NUMBERSTYLE);
    }
    
    public static NumberFormat getCurrencyInstance() {
        return getInstance(Locale.getDefault(Locale.Category.FORMAT), CURRENCYSTYLE);
    }
    
    public static NumberFormat getPercentInstance() {
        return getInstance(Locale.getDefault(Locale.Category.FORMAT), PERCENTSTYLE);
    }
    
    // 内部创建具体实现
    private static NumberFormat getInstance(Locale desiredLocale, int choice) {
        // 根据Locale和样式创建具体的NumberFormat实现
        // 如DecimalFormat、ChoiceFormat等
        return new DecimalFormat(...);
    }
}
```

## 📖 五、Spring中的工厂模式

### 5.1 BeanFactory

```java
/**
 * Spring核心容器 - BeanFactory
 * 最基础的IoC容器接口
 */
public interface BeanFactory {
    
    // 核心方法：根据名称获取Bean
    Object getBean(String name) throws BeansException;
    
    // 根据名称和类型获取Bean
    <T> T getBean(String name, Class<T> requiredType) throws BeansException;
    
    // 根据类型获取Bean
    <T> T getBean(Class<T> requiredType) throws BeansException;
    
    // 根据类型获取多个Bean
    <T> Map<String, T> getBeansOfType(Class<T> type) throws BeansException;
    
    // 判断是否包含Bean
    boolean containsBean(String name);
    
    // 判断是否单例
    boolean isSingleton(String name) throws NoSuchBeanDefinitionException;
    
    // 判断是否原型
    boolean isPrototype(String name) throws NoSuchBeanDefinitionException;
}

/**
 * 默认实现：DefaultListableBeanFactory
 */
public class DefaultListableBeanFactory extends AbstractAutowireCapableBeanFactory
        implements ConfigurableListableBeanFactory, BeanDefinitionRegistry {
    
    // Bean定义注册表
    private final Map<String, BeanDefinition> beanDefinitionMap = new ConcurrentHashMap<>();
    
    // 单例Bean缓存
    private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>();
    
    @Override
    public Object getBean(String name) throws BeansException {
        return doGetBean(name, null, null, false);
    }
    
    protected <T> T doGetBean(String name, Class<T> requiredType, 
            Object[] args, boolean typeCheckOnly) throws BeansException {
        
        // 1. 转换Bean名称
        String beanName = transformedBeanName(name);
        
        // 2. 检查单例缓存
        Object sharedInstance = getSingleton(beanName);
        if (sharedInstance != null) {
            return (T) getObjectForBeanInstance(sharedInstance, name, beanName, null);
        }
        
        // 3. 获取BeanDefinition
        BeanDefinition bd = getBeanDefinition(beanName);
        
        // 4. 根据Scope创建Bean
        if (bd.isSingleton()) {
            sharedInstance = getSingleton(beanName, () -> {
                return createBean(beanName, bd, args);
            });
            return (T) getObjectForBeanInstance(sharedInstance, name, beanName, bd);
        } else if (bd.isPrototype()) {
            Object prototypeInstance = createBean(beanName, bd, args);
            return (T) getObjectForBeanInstance(prototypeInstance, name, beanName, bd);
        } else {
            // 其他Scope（如request, session）
            String scopeName = bd.getScope();
            Scope scope = this.scopes.get(scopeName);
            return (T) scope.get(beanName, () -> createBean(beanName, bd, args));
        }
    }
}
```

### 5.2 FactoryBean

```java
/**
 * FactoryBean - 工厂Bean
 * 用于创建复杂Bean的特殊接口
 */
public interface FactoryBean<T> {
    
    // 返回由该工厂创建的对象
    T getObject() throws Exception;
    
    // 返回对象的类型
    Class<?> getObjectType();
    
    // 是否单例
    default boolean isSingleton() {
        return true;
    }
}

/**
 * 示例：创建连接池的FactoryBean
 */
public class ConnectionPoolFactoryBean implements FactoryBean<ConnectionPool>, 
        InitializingBean, DisposableBean {
    
    private String url;
    private String username;
    private String password;
    private int maxPoolSize = 10;
    
    private ConnectionPool connectionPool;
    
    @Override
    public void afterPropertiesSet() throws Exception {
        // 初始化连接池
        connectionPool = new ConnectionPool(url, username, password, maxPoolSize);
    }
    
    @Override
    public ConnectionPool getObject() throws Exception {
        return connectionPool;
    }
    
    @Override
    public Class<?> getObjectType() {
        return ConnectionPool.class;
    }
    
    @Override
    public boolean isSingleton() {
        return true;
    }
    
    @Override
    public void destroy() throws Exception {
        if (connectionPool != null) {
            connectionPool.close();
        }
    }
    
    // getter/setter
}

/**
 * Spring配置
 */
@Configuration
public class AppConfig {
    
    @Bean
    public FactoryBean<ConnectionPool> connectionPool() {
        ConnectionPoolFactoryBean factory = new ConnectionPoolFactoryBean();
        factory.setUrl("jdbc:mysql://localhost:3306/test");
        factory.setUsername("root");
        factory.setPassword("password");
        factory.setMaxPoolSize(20);
        return factory;
    }
}

/**
 * 获取FactoryBean创建的对象 vs FactoryBean本身
 */
@RunWith(SpringRunner.class)
@SpringBootTest
public class FactoryBeanTest {
    
    @Autowired
    private ApplicationContext context;
    
    @Test
    public void testFactoryBean() {
        // 获取FactoryBean创建的对象
        ConnectionPool pool = context.getBean("connectionPool", ConnectionPool.class);
        
        // 获取FactoryBean本身（加&前缀）
        FactoryBean<?> factory = (FactoryBean<?>) context.getBean("&connectionPool");
    }
}
```

### 5.3 Spring中的其他工厂模式应用

```java
/**
 * 1. ApplicationContext - BeanFactory的增强版
 */
public interface ApplicationContext extends EnvironmentCapable, 
        ListableBeanFactory, HierarchicalBeanFactory, 
        MessageSource, ApplicationEventPublisher, ResourcePatternResolver {
    // 继承BeanFactory，提供更多企业级功能
}

/**
 * 2. FactoryBean在Spring内部的应用
 */
// SqlSessionFactoryBean - MyBatis整合Spring
public class SqlSessionFactoryBean implements FactoryBean<SqlSessionFactory>, 
        InitializingBean, ApplicationListener<ApplicationEvent> {
    
    private DataSource dataSource;
    private Resource[] mapperLocations;
    
    @Override
    public SqlSessionFactory getObject() throws Exception {
        SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
        factory.setDataSource(dataSource);
        factory.setMapperLocations(mapperLocations);
        return factory.getObject();
    }
}

// RedisConnectionFactory - Redis连接工厂
public interface RedisConnectionFactory {
    RedisConnection getConnection();
    RedisConnection getClusterConnection();
}

// JedisConnectionFactory
public class JedisConnectionFactory implements RedisConnectionFactory, 
        InitializingBean, DisposableBean {
    
    private String host = "localhost";
    private int port = 6379;
    
    @Override
    public RedisConnection getConnection() {
        return new JedisConnection(jedisPool.getResource());
    }
}

/**
 * 3. InstantiationStrategy - Bean实例化策略工厂
 */
public interface InstantiationStrategy {
    Object instantiate(RootBeanDefinition bd, String beanName, BeanFactory owner);
    Object instantiate(RootBeanDefinition bd, String beanName, BeanFactory owner, 
            Constructor<?> ctor, Object... args);
    Object instantiate(RootBeanDefinition bd, String beanName, BeanFactory owner, 
            Object factoryBean, Method factoryMethod, Object... args);
}

// SimpleInstantiationStrategy - 简单实例化策略
// CglibSubclassingInstantiationStrategy - CGLIB实例化策略
```

## 📖 六、实际项目应用

### 6.1 支付工厂

```java
/**
 * 支付策略接口
 */
public interface PaymentStrategy {
    PayResult pay(PayRequest request);
    RefundResult refund(RefundRequest request);
    String getPaymentType();
}

/**
 * 支付宝支付
 */
@Service
public class AlipayStrategy implements PaymentStrategy {
    @Override
    public PayResult pay(PayRequest request) {
        // 调用支付宝SDK
        return new PayResult("支付宝支付成功");
    }
    
    @Override
    public RefundResult refund(RefundRequest request) {
        return new RefundResult("支付宝退款成功");
    }
    
    @Override
    public String getPaymentType() {
        return "ALIPAY";
    }
}

/**
 * 微信支付
 */
@Service
public class WechatPayStrategy implements PaymentStrategy {
    @Override
    public PayResult pay(PayRequest request) {
        // 调用微信支付SDK
        return new PayResult("微信支付成功");
    }
    
    @Override
    public RefundResult refund(RefundRequest request) {
        return new RefundResult("微信退款成功");
    }
    
    @Override
    public String getPaymentType() {
        return "WECHAT";
    }
}

/**
 * 支付工厂 - 策略模式 + 工厂模式
 */
@Component
public class PaymentFactory {
    
    private final Map<String, PaymentStrategy> strategyMap = new HashMap<>();
    
    /**
     * 通过构造器注入所有PaymentStrategy实现
     * Spring会自动注入所有实现了该接口的Bean
     */
    public PaymentFactory(List<PaymentStrategy> strategies) {
        for (PaymentStrategy strategy : strategies) {
            strategyMap.put(strategy.getPaymentType(), strategy);
        }
    }
    
    /**
     * 根据类型获取支付策略
     */
    public PaymentStrategy getStrategy(String paymentType) {
        PaymentStrategy strategy = strategyMap.get(paymentType);
        if (strategy == null) {
            throw new IllegalArgumentException("不支持的支付方式: " + paymentType);
        }
        return strategy;
    }
    
    /**
     * 支付方法
     */
    public PayResult pay(String paymentType, PayRequest request) {
        return getStrategy(paymentType).pay(request);
    }
}

/**
 * 支付服务
 */
@Service
public class PaymentService {
    
    @Autowired
    private PaymentFactory paymentFactory;
    
    public PayResult pay(Order order) {
        PayRequest request = new PayRequest(order);
        return paymentFactory.pay(order.getPaymentType(), request);
    }
}
```

### 6.2 消息工厂

```java
/**
 * 消息发送接口
 */
public interface MessageSender {
    void send(Message message);
    String getChannel();
}

/**
 * 短信发送
 */
@Service
public class SmsSender implements MessageSender {
    @Override
    public void send(Message message) {
        System.out.println("发送短信: " + message.getContent());
    }
    
    @Override
    public String getChannel() {
        return "SMS";
    }
}

/**
 * 邮件发送
 */
@Service
public class EmailSender implements MessageSender {
    @Override
    public void send(Message message) {
        System.out.println("发送邮件: " + message.getContent());
    }
    
    @Override
    public String getChannel() {
        return "EMAIL";
    }
}

/**
 * 推送发送
 */
@Service
public class PushSender implements MessageSender {
    @Override
    public void send(Message message) {
        System.out.println("发送推送: " + message.getContent());
    }
    
    @Override
    public String getChannel() {
        return "PUSH";
    }
}

/**
 * 消息工厂
 */
@Component
public class MessageFactory {
    
    private final Map<String, MessageSender> senderMap;
    
    public MessageFactory(List<MessageSender> senders) {
        this.senderMap = senders.stream()
            .collect(Collectors.toMap(MessageSender::getChannel, Function.identity()));
    }
    
    public void send(String channel, Message message) {
        MessageSender sender = senderMap.get(channel);
        if (sender == null) {
            throw new IllegalArgumentException("不支持的消息渠道: " + channel);
        }
        sender.send(message);
    }
    
    /**
     * 多渠道发送
     */
    public void sendMultiChannel(List<String> channels, Message message) {
        channels.forEach(channel -> send(channel, message));
    }
}
```

## 📖 七、三种工厂模式对比

| 特性 | 简单工厂 | 工厂方法 | 抽象工厂 |
|------|----------|----------|----------|
| **设计目的** | 封装对象创建 | 定义创建接口 | 创建产品族 |
| **产品数量** | 一种产品 | 一种产品 | 多种产品（产品族） |
| **工厂数量** | 一个工厂 | 多个工厂（每种产品一个） | 多个工厂（每个产品族一个） |
| **开闭原则** | 违反（添加产品需修改工厂） | 符合（添加产品添加新工厂） | 部分符合（添加产品族容易，添加产品等级结构困难） |
| **扩展性** | 差 | 好 | 较好 |
| **复杂度** | 低 | 中 | 高 |
| **使用场景** | 产品种类少且固定 | 产品种类多变 | 需要创建产品族 |
| **JDK案例** | Calendar.getInstance() | Collection.iterator() | 无典型案例 |
| **Spring案例** | BeanFactory.getBean() | FactoryBean | 无典型案例 |

**选择建议：**

```java
/**
 * 选择决策树
 */
public class FactoryPatternSelector {
    
    public String select(boolean hasProductFamily, int productCount, 
            boolean needExtension) {
        
        if (hasProductFamily) {
            // 需要创建产品族 → 抽象工厂
            return "抽象工厂模式";
        } else if (productCount <= 3 && !needExtension) {
            // 产品种类少且固定 → 简单工厂
            return "简单工厂模式";
        } else {
            // 产品种类多变 → 工厂方法
            return "工厂方法模式";
        }
    }
}
```

## 📖 八、高频面试题

### Q1: 简单工厂、工厂方法、抽象工厂的区别？

**答：**

1. **简单工厂：**
   - 一个工厂类创建所有产品
   - 使用switch/if-else判断类型
   - 违反开闭原则
   - 适用于产品种类少且固定的场景

2. **工厂方法：**
   - 一个工厂接口，多个具体工厂
   - 每个工厂只创建一种产品
   - 符合开闭原则
   - 适用于产品种类多变的场景

3. **抽象工厂：**
   - 一个工厂创建一个产品族
   - 产品族内的产品有约束关系
   - 符合开闭原则（对产品族）
   - 适用于需要创建产品族的场景

---

### Q2: 工厂模式如何体现开闭原则？

**答：**

**工厂方法模式的开闭原则体现：**

```java
/**
 * 扩展新产品：只需添加新类，无需修改现有代码
 */

// 1. 添加新产品
public class ProductC implements Product {
    @Override
    public void use() {
        System.out.println("使用产品C");
    }
}

// 2. 添加新工厂
public class FactoryC implements Factory {
    @Override
    public Product create() {
        return new ProductC();
    }
}

// 无需修改Factory接口和现有的FactoryA、FactoryB
```

**简单工厂违反开闭原则：**

```java
/**
 * 扩展新产品：需要修改SimpleFactory类
 */
public class SimpleFactory {
    public static Product create(String type) {
        switch (type) {
            case "A": return new ProductA();
            case "B": return new ProductB();
            case "C": return new ProductC(); // 需要修改这里
            default: throw new IllegalArgumentException("未知产品类型");
        }
    }
}
```

---

### Q3: Spring中BeanFactory和FactoryBean的区别？

**答：**

**BeanFactory：**
- Spring IoC容器的核心接口
- 是一个工厂，负责管理和创建Bean
- 提供getBean()方法获取Bean
- 是Spring框架的基础设施

```java
BeanFactory factory = new DefaultListableBeanFactory();
MyBean bean = factory.getBean(MyBean.class);
```

**FactoryBean：**
- 是一个特殊的Bean，用于创建其他Bean
- 实现FactoryBean接口，自定义Bean创建逻辑
- 创建复杂对象时使用（如连接池、代理对象）
- &前缀获取FactoryBean本身

```java
@Bean
public FactoryBean<MyComplexObject> myObject() {
    return new MyComplexObjectFactoryBean();
}

// 获取创建的对象
MyComplexObject obj = context.getBean("myObject", MyComplexObject.class);

// 获取FactoryBean本身
FactoryBean<?> factory = (FactoryBean<?>) context.getBean("&myObject");
```

---

### Q4: 工厂模式与单例模式如何结合？

**答：**

```java
/**
 * 单例工厂 - 工厂本身是单例
 */
public class SingletonFactory {
    
    private static volatile SingletonFactory instance;
    
    private SingletonFactory() {}
    
    public static SingletonFactory getInstance() {
        if (instance == null) {
            synchronized (SingletonFactory.class) {
                if (instance == null) {
                    instance = new SingletonFactory();
                }
            }
        }
        return instance;
    }
    
    public Product create(String type) {
        // 创建逻辑
        return new ProductA();
    }
}

/**
 * 产品单例工厂 - 创建的产品是单例
 */
public class ProductSingletonFactory {
    
    private static final Map<String, Product> cache = new ConcurrentHashMap<>();
    
    public static Product getProduct(String type) {
        return cache.computeIfAbsent(type, key -> {
            // 根据type创建对应产品
            if ("A".equals(key)) {
                return new ProductA();
            } else {
                return new ProductB();
            }
        });
    }
}

/**
 * Spring中的实现 - 单例Bean由BeanFactory管理
 */
@Configuration
public class AppConfig {
    
    @Bean
    @Scope("singleton") // 默认就是单例
    public Product product() {
        return new ProductA();
    }
}
```

---

### Q5: 抽象工厂模式如何支持扩展？

**答：**

**扩展产品族（容易）：**

```java
// 添加新的产品族 - PostgreSQL
public class PostgreSQLFactory implements DatabaseFactory {
    @Override
    public Connection createConnection() {
        return new PostgreSQLConnection();
    }
    
    @Override
    public Command createCommand() {
        return new PostgreSQLCommand();
    }
}
// 只需添加新类，无需修改现有代码 ✓
```

**扩展产品等级结构（困难）：**

```java
// 添加新的产品类型 - Transaction
public interface Transaction {
    void begin();
    void commit();
    void rollback();
}

// 需要修改抽象工厂接口
public interface DatabaseFactory {
    Connection createConnection();
    Command createCommand();
    Transaction createTransaction(); // 新增方法
}

// 需要修改所有具体工厂
public class MySQLFactory implements DatabaseFactory {
    // ... 原有方法
    @Override
    public Transaction createTransaction() {
        return new MySQLTransaction();
    }
}
// 违反开闭原则 ✗
```

**解决方案：使用抽象工厂+工厂方法的组合**

```java
/**
 * 为每个产品类型提供工厂接口
 */
public interface DatabaseFactory {
    ConnectionFactory getConnectionFactory();
    CommandFactory getCommandFactory();
    TransactionFactory getTransactionFactory(); // 新增容易
}

public interface ConnectionFactory {
    Connection create();
}

public interface CommandFactory {
    Command create();
}

public interface TransactionFactory {
    Transaction create();
}

// MySQL实现
public class MySQLFactory implements DatabaseFactory {
    @Override
    public ConnectionFactory getConnectionFactory() {
        return new MySQLConnectionFactory();
    }
    // ...
}
```

---

**⭐ 重点：理解三种工厂模式的演进关系和适用场景**
