# 设计模式详解 ⭐⭐

## 面试题：说说你了解的设计模式

### 核心回答

设计模式分为三大类：**创建型**（5种）、**结构型**（7种）、**行为型**（11种），共 23 种经典模式。

### 设计模式分类

```
设计模式（23种经典模式）
├── 创建型（5种）
│   ├── 单例模式（Singleton）
│   ├── 工厂方法模式（Factory Method）
│   ├── 抽象工厂模式（Abstract Factory）
│   ├── 建造者模式（Builder）
│   └── 原型模式（Prototype）
│
├── 结构型（7种）
│   ├── 适配器模式（Adapter）
│   ├── 装饰器模式（Decorator）
│   ├── 代理模式（Proxy）
│   ├── 外观模式（Facade）
│   ├── 桥接模式（Bridge）
│   ├── 组合模式（Composite）
│   └── 享元模式（Flyweight）
│
└── 行为型（11种）
    ├── 策略模式（Strategy）
    ├── 观察者模式（Observer）
    ├── 迭代器模式（Iterator）
    ├── 模板方法模式（Template Method）
    ├── 职责链模式（Chain of Responsibility）
    ├── 命令模式（Command）
    ├── 备忘录模式（Memento）
    ├── 状态模式（State）
    ├── 访问者模式（Visitor）
    ├── 中介者模式（Mediator）
    └── 解释器模式（Interpreter）
```

---

## 一、单例模式（Singleton）

### 定义

确保一个类只有一个实例，并提供一个全局访问点。

### 实现方式

#### 1. 饿汉式（线程安全）

```java
public class HungrySingleton {
    // 类加载时就创建实例
    private static final HungrySingleton INSTANCE = new HungrySingleton();
    
    private HungrySingleton() {}
    
    public static HungrySingleton getInstance() {
        return INSTANCE;
    }
}
```

#### 2. 懒汉式（线程不安全）

```java
public class LazySingleton {
    private static LazySingleton instance;
    
    private LazySingleton() {}
    
    public static LazySingleton getInstance() {
        if (instance == null) {
            instance = new LazySingleton();
        }
        return instance;
    }
}
```

#### 3. 双重检查锁（推荐）

```java
public class DoubleCheckSingleton {
    // volatile 防止指令重排序
    private static volatile DoubleCheckSingleton instance;
    
    private DoubleCheckSingleton() {}
    
    public static DoubleCheckSingleton getInstance() {
        if (instance == null) {
            synchronized (DoubleCheckSingleton.class) {
                if (instance == null) {
                    instance = new DoubleCheckSingleton();
                    // 可能发生指令重排序：
                    // 1. 分配内存
                    // 2. 调用构造方法
                    // 3. 将引用指向内存
                    // 如果 2 和 3 重排序，其他线程可能看到不完整的对象
                }
            }
        }
        return instance;
    }
}
```

#### 4. 静态内部类（推荐）

```java
public class StaticInnerClassSingleton {
    
    private StaticInnerClassSingleton() {}
    
    // 静态内部类：类加载时不会创建，只有调用 getInstance 时才会创建
    // JVM 保证线程安全
    private static class Holder {
        private static final StaticInnerClassSingleton INSTANCE = 
            new StaticInnerClassSingleton();
    }
    
    public static StaticInnerClassSingleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

#### 5. 枚举（最安全）

```java
public enum EnumSingleton {
    INSTANCE;
    
    public void doSomething() {}
}

// 使用
EnumSingleton.INSTANCE.doSomething();
```

### 应用场景

- 配置管理器
- 连接池
- 日志器
- 缓存管理器

---

## 二、工厂模式（Factory）

### 1. 简单工厂（违背开闭原则）

```java
// 违反开闭原则，不推荐
public class SimpleFactory {
    
    public static Product create(String type) {
        switch (type) {
            case "A":
                return new ProductA();
            case "B":
                return new ProductB();
            default:
                throw new IllegalArgumentException();
        }
    }
}
```

### 2. 工厂方法模式

```java
// 产品接口
public interface Product {
    void use();
}

// 具体产品
public class ConcreteProductA implements Product {
    @Override
    public void use() {
        System.out.println("使用产品A");
    }
}

public class ConcreteProductB implements Product {
    @Override
    public void use() {
        System.out.println("使用产品B");
    }
}

// 工厂接口
public interface Factory {
    Product create();
}

// 具体工厂
public class FactoryA implements Factory {
    @Override
    public Product create() {
        return new ConcreteProductA();
    }
}

public class FactoryB implements Factory {
    @Override
    public Product create() {
        return new ConcreteProductB();
    }
}

// 使用
Factory factory = new FactoryA();
Product product = factory.create();
```

### 3. 抽象工厂模式

```java
// 抽象产品族
public interface Button {
    void click();
}

public interface TextField {
    void input();
}

// Windows 产品族
public class WindowsButton implements Button {
    @Override
    public void click() {
        System.out.println("Windows 按钮点击");
    }
}

public class WindowsTextField implements TextField {
    @Override
    public void input() {
        System.out.println("Windows 输入框输入");
    }
}

// Mac 产品族
public class MacButton implements Button {
    @Override
    public void click() {
        System.out.println("Mac 按钮点击");
    }
}

public class MacTextField implements TextField {
    @Override
    public void input() {
        System.out.println("Mac 输入框输入");
    }
}

// 抽象工厂
public interface GUIFactory {
    Button createButton();
    TextField createTextField();
}

// 具体工厂
public class WindowsFactory implements GUIFactory {
    @Override
    public Button createButton() {
        return new WindowsButton();
    }
    
    @Override
    public TextField createTextField() {
        return new WindowsTextField();
    }
}

// 使用
GUIFactory factory = new WindowsFactory();
Button button = factory.createButton();
```

---

## 三、策略模式（Strategy）

### 定义

定义一系列算法，将每个算法封装起来，使它们可以互换。

### 实现

```java
// 策略接口
public interface PayStrategy {
    void pay(double amount);
}

// 具体策略
public class AlipayStrategy implements PayStrategy {
    @Override
    public void pay(double amount) {
        System.out.println("使用支付宝支付：" + amount);
    }
}

public class WechatPayStrategy implements PayStrategy {
    @Override
    public void pay(double amount) {
        System.out.println("使用微信支付：" + amount);
    }
}

// 上下文
public class PaymentContext {
    private PayStrategy strategy;
    
    public PaymentContext(PayStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void pay(double amount) {
        strategy.pay(amount);
    }
}

// 使用
PaymentContext context = new PaymentContext(new AlipayStrategy());
context.pay(100.0);

// 策略可以动态切换
context = new PaymentContext(new WechatPayStrategy());
context.pay(200.0);
```

### 应用场景

- 支付方式选择
- 排序算法选择
- 出行路线规划

---

## 四、观察者模式（Observer）

### 定义

定义对象间的一对多依赖关系，当一个对象状态改变时，所有依赖它的对象都会收到通知。

### 实现

```java
// 主题接口
public interface Subject {
    void attach(Observer observer);
    void detach(Observer observer);
    void notifyAllObservers();
}

// 观察者接口
public interface Observer {
    void update(String message);
}

// 具体主题
public class NewsPublisher implements Subject {
    private List<Observer> observers = new ArrayList<>();
    private String news;
    
    @Override
    public void attach(Observer observer) {
        observers.add(observer);
    }
    
    @Override
    public void detach(Observer observer) {
        observers.remove(observer);
    }
    
    @Override
    public void notifyAllObservers() {
        for (Observer observer : observers) {
            observer.update(news);
        }
    }
    
    public void publishNews(String news) {
        this.news = news;
        notifyAllObservers();
    }
}

// 具体观察者
public class Subscriber implements Observer {
    private String name;
    
    public Subscriber(String name) {
        this.name = name;
    }
    
    @Override
    public void update(String message) {
        System.out.println(name + " 收到新闻：" + message);
    }
}

// 使用
NewsPublisher publisher = new NewsPublisher();
publisher.attach(new Subscriber("张三"));
publisher.attach(new Subscriber("李四"));

publisher.publishNews("重大新闻！");
// 张三 收到新闻：重大新闻！
// 李四 收到新闻：重大新闻！
```

### 应用场景

- 消息推送
- 事件监听
- MVC 架构

---

## 五、代理模式（Proxy）

### 定义

为其他对象提供一种代理，以控制对这个对象的访问。

### 静态代理

```java
// 接口
public interface Image {
    void display();
}

// 真实对象
public class RealImage implements Image {
    private String filename;
    
    public RealImage(String filename) {
        this.filename = filename;
        loadFromDisk();
    }
    
    @Override
    public void display() {
        System.out.println("显示图片：" + filename);
    }
    
    private void loadFromDisk() {
        System.out.println("从磁盘加载：" + filename);
    }
}

// 代理对象
public class ImageProxy implements Image {
    private RealImage realImage;
    private String filename;
    
    public ImageProxy(String filename) {
        this.filename = filename;
    }
    
    @Override
    public void display() {
        if (realImage == null) {
            realImage = new RealImage(filename);
        }
        realImage.display();
    }
}

// 使用
Image image = new ImageProxy("photo.jpg");
// 不加载，只创建代理
image.display();
// 第一次显示时才加载
```

### 动态代理（JDK）

```java
public class JDKDynamicProxy implements InvocationHandler {
    private Object target;
    
    public JDKDynamicProxy(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) 
            throws Throwable {
        System.out.println("前置操作");
        Object result = method.invoke(target, args);
        System.out.println("后置操作");
        return result;
    }
}

// 使用
Image realImage = new RealImage("photo.jpg");
Image proxy = (Image) Proxy.newProxyInstance(
    realImage.getClass().getClassLoader(),
    realImage.getClass().getInterfaces(),
    new JDKDynamicProxy(realImage)
);
proxy.display();
```

---

## 六、装饰器模式（Decorator）

### 定义

动态地给对象添加一些额外的职责。

```java
// 基础接口
public interface Coffee {
    String getDescription();
    double getCost();
}

// 基础实现
public class SimpleCoffee implements Coffee {
    @Override
    public String getDescription() {
        return "咖啡";
    }
    
    @Override
    public double getCost() {
        return 10.0;
    }
}

// 装饰器基类
public abstract class CoffeeDecorator implements Coffee {
    protected Coffee coffee;
    
    public CoffeeDecorator(Coffee coffee) {
        this.coffee = coffee;
    }
}

// 具体装饰器
public class MilkDecorator extends CoffeeDecorator {
    public MilkDecorator(Coffee coffee) {
        super(coffee);
    }
    
    @Override
    public String getDescription() {
        return coffee.getDescription() + " + 牛奶";
    }
    
    @Override
    public double getCost() {
        return coffee.getCost() + 3.0;
    }
}

public class SugarDecorator extends CoffeeDecorator {
    public SugarDecorator(Coffee coffee) {
        super(coffee);
    }
    
    @Override
    public String getDescription() {
        return coffee.getDescription() + " + 糖";
    }
    
    @Override
    public double getCost() {
        return coffee.getCost() + 2.0;
    }
}

// 使用
Coffee coffee = new SimpleCoffee();
coffee = new MilkDecorator(coffee);
coffee = new SugarDecorator(coffee);

System.out.println(coffee.getDescription()); // 咖啡 + 牛奶 + 糖
System.out.println(coffee.getCost()); // 15.0
```

---

## 七、模板方法模式（Template Method）

```java
public abstract class Game {
    // 模板方法
    public final void play() {
        initialize();
        startPlay();
        endPlay();
    }
    
    abstract void initialize();
    abstract void startPlay();
    abstract void endPlay();
}

public class FootballGame extends Game {
    @Override
    void initialize() {
        System.out.println("足球游戏初始化");
    }
    
    @Override
    void startPlay() {
        System.out.println("开始足球比赛");
    }
    
    @Override
    void endPlay() {
        System.out.println("足球比赛结束");
    }
}

// 使用
Game game = new FootballGame();
game.play();
```

---

## 八、建造者模式（Builder）

```java
public class User {
    private String name;
    private int age;
    private String email;
    private String phone;
    
    // 私有构造方法
    private User(UserBuilder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
        this.phone = builder.phone;
    }
    
    // 建造者
    public static class UserBuilder {
        private String name;
        private int age;
        private String email;
        private String phone;
        
        public UserBuilder name(String name) {
            this.name = name;
            return this;
        }
        
        public UserBuilder age(int age) {
            this.age = age;
            return this;
        }
        
        public UserBuilder email(String email) {
            this.email = email;
            return this;
        }
        
        public UserBuilder phone(String phone) {
            this.phone = phone;
            return this;
        }
        
        public User build() {
            return new User(this);
        }
    }
}

// 使用
User user = new User.UserBuilder()
    .name("张三")
    .age(18)
    .email("zhangsan@example.com")
    .build();
```

---

## 设计原则（SOLID）

| 原则 | 说明 |
|------|------|
| **S**ingle Responsibility | 单一职责：一个类只负责一件事 |
| **O**pen/Closed | 开闭原则：对扩展开放，对修改关闭 |
| **L**iskov Substitution | 里氏替换：子类可以替换父类 |
| **I**nterface Segregation | 接口隔离：接口要小而专 |
| **D**ependency Inversion | 依赖倒置：依赖抽象，不依赖具体 |

---

**参考链接：**
- [Java设计模式面试题及答案-原创力文档](https://max.book118.com/html/2025/0318/7152042001010051.shtm)
- [设计模式面试题全解析-CSDN](https://blog.csdn.net/weixin_44978801/article/details/146538933)
