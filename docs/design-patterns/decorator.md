---
layout: default
title: 装饰器模式（Decorator Pattern）
---
# 装饰器模式（Decorator Pattern）：动态增强对象功能

> 继承是静态的、"一次性"的扩展；装饰器是动态的、"可叠加"的扩展。理解装饰器模式，就理解了一半的 Java I/O 体系。

---

## 🎯 面试重点速览

| 维度 | 核心内容 |
|------|---------|
| **定义** | 动态地给对象添加额外职责，比继承更灵活 |
| **JDK 代表** | `InputStream` 家族：`FileInputStream → BufferedInputStream → DataInputStream` |
| **核心思想** | 组合优于继承，装饰器与组件实现同一接口 |
| **vs 代理** | 装饰器增强功能，代理控制访问 |
| **典型场景** | I/O 流、日志装饰器、压缩装饰器、加密装饰器 |

---

## 一、核心思想：什么是装饰器模式？

装饰器模式（Decorator Pattern）又称**包装器模式（Wrapper Pattern）**，是 GoF 23 种设计模式之一，属于**结构型设计模式**。

### 1.1 一句话定义

> **动态地给一个对象添加一些额外的职责。就增加功能来说，装饰器模式相比生成子类更为灵活。**
>
> ——《设计模式》GoF

### 1.2 生活中的"装饰器"

想象你去咖啡店点单：

- 你要了一杯 **美式咖啡（Component）**
- 服务员问：要不要加**牛奶（Decorator）**？
- 又问：要不要加**摩卡糖浆（Decorator）**？
- 最后问：要不要加**奶泡（Decorator）**？

最终你拿到的是：**奶泡 + 摩卡 + 牛奶 + 美式**的组合，每一层"装饰"都叠加在前面基础上。这就是装饰器模式的精髓——**层层叠加、按需组合**。

如果用继承来实现，你需要为每一种咖啡组合创建子类：
- `MilkCoffee`
- `MochaCoffee`
- `MilkMochaCoffee`
- `MilkMochaFoamCoffee`
- ……

这就会产生 **类爆炸**，而装饰器模式优雅地解决了这个问题。

### 1.3 设计原则支撑

装饰器模式的实现遵循了以下设计原则：

1. **开闭原则（Open-Closed Principle）**：类应该对扩展开放，对修改关闭。装饰器模式允许在不修改原有类的情况下新增功能。
2. **组合优先于继承（Composition over Inheritance）**：通过组合实现功能扩展，避免继承带来的类膨胀和耦合。
3. **单一职责原则（Single Responsibility Principle）**：每个装饰器只负责一项功能，职责清晰。

---

## 二、类结构：四个核心角色

装饰器模式的类结构非常清晰，由四个核心角色组成：

```
┌─────────────────────┐
│   <<interface>>     │
│     Component       │  抽象组件
│  + operation()      │
└─────────┬───────────┘
          │
          │ implements
          │ extends
┌─────────┴───────────┐      ┌─────────────────────────┐
│  ConcreteComponent   │      │   <<abstract>>          │
│  + operation()      │      │     Decorator           │
└─────────────────────┘      │  - component: Component  │
                             │  + operation()           │
                             └─────────┬───────────────┘
                                       │ extends
                          ┌────────────┴───────────┐
                          │                        │
             ┌────────────▼───────────┐ ┌──────────▼─────────┐
             │  ConcreteDecoratorA    │ │  ConcreteDecoratorB │
             │  + operation()         │ │  + operation()      │
             │    // 增强 before      │ │    // 增强 after   │
             └─────────────────────────┘ └────────────────────┘
```

### 2.1 Component（抽象组件）

```java
/**
 * 抽象组件接口
 * 定义了组件和装饰器共同的操作接口
 */
public interface Component {
    /** 执行组件的核心操作 */
    void operation();
}
```

### 2.2 ConcreteComponent（具体组件）

```java
/**
 * 具体组件
 * 定义了被装饰的原始对象，实现了组件接口的核心功能
 */
public class ConcreteComponent implements Component {
    
    @Override
    public void operation() {
        System.out.println("执行 ConcreteComponent 的核心操作");
    }
}
```

### 2.3 Decorator（抽象装饰器）

```java
/**
 * 抽象装饰器
 * 维持一个对组件对象的引用，并将调用转发给组件对象
 * 同时提供可扩展的接口，供具体装饰器添加额外功能
 */
public abstract class Decorator implements Component {
    
    /** 持有组件引用（通过组合实现） */
    protected Component component;
    
    /** 通过构造函数注入被装饰的组件 */
    public Decorator(Component component) {
        this.component = component;
    }
    
    @Override
    public void operation() {
        // 默认直接转发给组件执行
        component.operation();
    }
}
```

### 2.4 ConcreteDecorator（具体装饰器）

```java
/**
 * 具体装饰器A - 前置增强
 * 在调用组件操作之前添加额外功能
 */
public class ConcreteDecoratorA extends Decorator {
    
    public ConcreteDecoratorA(Component component) {
        super(component);
    }
    
    @Override
    public void operation() {
        beforeDecoration();
        component.operation();
    }
    
    private void beforeDecoration() {
        System.out.println("【装饰器A】执行前置增强逻辑：参数校验、日志记录等");
    }
}

/**
 * 具体装饰器B - 后置增强
 * 在调用组件操作之后添加额外功能
 */
public class ConcreteDecoratorB extends Decorator {
    
    public ConcreteDecoratorB(Component component) {
        super(component);
    }
    
    @Override
    public void operation() {
        component.operation();
        afterDecoration();
    }
    
    private void afterDecoration() {
        System.out.println("【装饰器B】执行后置增强逻辑：结果缓存、通知发送等");
    }
}

/**
 * 具体装饰器C - 环绕增强
 * 同时在调用前后添加功能
 */
public class ConcreteDecoratorC extends Decorator {
    
    public ConcreteDecoratorC(Component component) {
        super(component);
    }
    
    @Override
    public void operation() {
        System.out.println("【装饰器C-前置】开始计时...");
        long start = System.currentTimeMillis();
        component.operation();
        long end = System.currentTimeMillis();
        System.out.println("【装饰器C-后置】操作耗时：" + (end - start) + "ms");
    }
}
```

### 2.5 客户端使用

```java
/**
 * 客户端代码演示
 */
public class DecoratorClient {
    
    public static void main(String[] args) {
        // 1. 创建最基础的组件
        Component base = new ConcreteComponent();
        
        // 2. 用装饰器A包装（添加前置增强）
        Component withA = new ConcreteDecoratorA(base);
        
        // 3. 用装饰器B包装（添加后置增强）
        Component withAB = new ConcreteDecoratorB(withA);
        
        // 4. 用装饰器C包装（添加计时功能）
        Component fullyDecorated = new ConcreteDecoratorC(withAB);
        
        // 5. 执行——从外到内调用，从内到外返回
        fullyDecorated.operation();
        // 输出顺序：
        // 【装饰器C-前置】开始计时...
        // 【装饰器A】执行前置增强逻辑
        // 执行 ConcreteComponent 的核心操作
        // 【装饰器B】执行后置增强逻辑
        // 【装饰器C-后置】操作耗时：xxxms
    }
}
```

---

## 三、JDK 经典案例：Java I/O 流体系

> **装饰器模式是 Java I/O 库的灵魂。** 如果你理解过 `InputStream` 的层层嵌套，你就已经理解了装饰器模式的精髓。

### 3.1 Java I/O 架构图

```
                        ┌──────────────┐
                        │   InputStream │  ← 抽象组件（Component）
                        │  + read()    │
                        └──────┬───────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
     ┌──────▼──────┐    ┌───────▼───────┐  ┌──────▼──────┐
     │FileInputStream│   │ ByteArray     │  │ Filter      │
     │(具体组件)     │   │ InputStream   │  │ InputStream │ ← 抽象装饰器
     └─────────────┘   └───────────────┘  └──────┬──────┘
                                                │
                               ┌────────────────┼────────────────┐
                               │                │                │
                        ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
                        │Buffered     │  │DataInput    │  │ Cipher      │
                        │InputStream  │  │Stream       │  │ InputStream │
                        │(缓冲装饰器)  │  │(数据转换    │  │(加密装饰器) │
                        └─────────────┘  │ 装饰器)     │  └─────────────┘
                                         └─────────────┘
```

### 3.2 从源码看装饰器模式

#### Step 1：抽象组件 —— `InputStream`

```java
/**
 * InputStream 是所有字节输入流的抽象父类
 * 定义了 read() 方法作为组件接口
 * 
 * 位置：java.io.InputStream
 */
public abstract class InputStream implements Closeable {
    
    /** 读取下一个字节，返回值 0-255，到达末尾返回 -1 */
    public abstract int read();
    
    /** 读取多个字节到缓冲区 */
    public int read(byte[] b, int off, int len) {
        return -1;
    }
    
    public void close() throws IOException {
    }
}
```

#### Step 2：具体组件 —— `FileInputStream`

```java
/**
 * FileInputStream 是具体组件
 * 从文件系统读取字节，是最原始的数据来源
 * 
 * 位置：java.io.FileInputStream
 */
public class FileInputStream extends InputStream {
    
    private final FileDescriptor fdObj;
    private final String path;
    
    public FileInputStream(String name) throws FileNotFoundException {
        this(new File(name));
    }
    
    /** 读取文件的下一个字节（核心操作） */
    @Override
    public native int read() throws IOException;
    
    @Override
    public void close() throws IOException {
        // 关闭文件描述符
    }
}
```

#### Step 3：抽象装饰器 —— `FilterInputStream`

```java
/**
 * FilterInputStream 是抽象装饰器
 * 它持有对另一个 InputStream 的引用，并将其操作转发给它
 * 所有 I/O 装饰器都继承自它
 * 
 * 位置：java.io.FilterInputStream
 */
public class FilterInputStream extends InputStream {
    
    /** 被装饰的输入流（组合关系） */
    protected volatile InputStream in;
    
    /** 构造函数，接收被装饰的流 */
    protected FilterInputStream(InputStream in) {
        this.in = in;
    }
    
    /** 默认直接转发 read 请求给被装饰的流 */
    @Override
    public int read() throws IOException {
        return in.read();
    }
    
    @Override
    public int read(byte[] b, int off, int len) throws IOException {
        return in.read(b, off, len);
    }
    
    @Override
    public void close() throws IOException {
        in.close();
    }
}
```

#### Step 4：具体装饰器 —— `BufferedInputStream`

```java
/**
 * BufferedInputStream 是具体装饰器
 * 为底层输入流添加缓冲功能，减少磁盘/网络 I/O 次数
 * 
 * 位置：java.io.BufferedInputStream
 */
public class BufferedInputStream extends FilterInputStream {
    
    /** 内部缓冲数组 */
    private byte[] buffer;
    
    /** 缓冲区中当前有效数据的末尾位置 */
    private int count;
    
    /** 缓冲区中下一个读取位置 */
    private int pos;
    
    /** 标记位置 */
    private int markpos = -1;
    
    /** 标记后允许读取的最大字节数 */
    private int marklimit;
    
    public BufferedInputStream(InputStream in) {
        this(in, defaultSize);
    }
    
    public BufferedInputStream(InputStream in, int size) {
        super(in);  // 调用父类构造函数，保存被装饰的流
        buffer = new byte[size];
    }
    
    /**
     * 带缓冲的读取方法（核心增强逻辑）
     * 先从缓冲区读取，缓冲区空时一次性从底层流读入更多数据
     */
    @Override
    public synchronized int read() throws IOException {
        if (pos >= count) {
            fill();
            if (pos >= count) {
                return -1;
            }
        }
        return buffer[pos++] & 0xff;
    }
    
    /** 填充缓冲区：从底层流一次性读取尽可能多的字节到缓冲区 */
    private void fill() throws IOException {
        // ... 实现从 in.read() 批量读取到 buffer
    }
}
```

#### Step 5：具体装饰器 —— `DataInputStream`

```java
/**
 * DataInputStream 是具体装饰器
 * 提供读取 Java 基本数据类型的能力
 * 
 * 位置：java.io.DataInputStream
 */
public class DataInputStream extends FilterInputStream implements DataInput {
    
    public DataInputStream(InputStream in) {
        super(in);
    }
    
    /** 读取一个 boolean */
    public final boolean readBoolean() throws IOException {
        int ch = in.read();
        if (ch < 0) throw new EOFException();
        return (ch != 0);
    }
    
    /** 读取一个 int（4字节，big-endian） */
    public final int readInt() throws IOException {
        int ch1 = in.read();
        int ch2 = in.read();
        int ch3 = in.read();
        int ch4 = in.read();
        if ((ch1 | ch2 | ch3 | ch4) < 0) throw new EOFException();
        return (ch1 << 24) | (ch2 << 16) | (ch3 << 8) | ch4;
    }
    
    /** 读取一个 UTF-8 编码的字符串 */
    public final String readUTF() throws IOException {
        return DataInputStream.readUTF(this);
    }
}
```

### 3.3 典型使用方式

```java
/**
 * Java I/O 装饰器的典型使用
 * 层层包装，功能叠加
 */
public class IOStreamDemo {
    
    public static void main(String[] args) throws Exception {
        
        // 传统方式（只读原始字节）：
        InputStream fis = new FileInputStream("data.bin");
        int byte1 = fis.read();
        int byte2 = fis.read();
        fis.close();
        
        // 装饰器方式（层层叠加）：
        // 第1层：FileInputStream - 文件读取（最底层数据源）
        InputStream fileStream = new FileInputStream("data.bin");
        
        // 第2层：BufferedInputStream - 添加缓冲，减少 I/O 次数
        InputStream bufferedStream = new BufferedInputStream(fileStream);
        
        // 第3层：DataInputStream - 提供高级数据类型读取
        DataInputStream dataStream = new DataInputStream(bufferedStream);
        
        // 现在可以优雅地读取各种数据类型
        int intVal = dataStream.readInt();       // 读 int
        double doubleVal = dataStream.readDouble(); // 读 double
        String strVal = dataStream.readUTF();      // 读 UTF 字符串
        boolean boolVal = dataStream.readBoolean(); // 读 boolean
        
        // 只需要关闭最外层装饰器（装饰器会自动关闭内层）
        dataStream.close();
    }
}
```

### 3.4 Java I/O 装饰器家族一览

| 装饰器 | 位置 | 功能 |
|--------|------|------|
| `FilterInputStream` | `java.io` | 抽象装饰器基类 |
| `BufferedInputStream` | `java.io` | 为 I/O 添加缓冲，减少 I/O 次数 |
| `DataInputStream` | `java.io` | 读取 Java 基本数据类型 |
| `PushbackInputStream` | `java.io` | 支持推回（unread）操作 |
| `CipherInputStream` | `javax.crypto` | 加密/解密流 |
| `GZIPInputStream` | `java.util.zip` | 解压缩流 |
| `ZipInputStream` | `java.util.zip` | ZIP 解压流 |
| `DeflaterInputStream` | `java.util.zip` | 通用压缩流 |

**同理，`OutputStream` 体系也遵循同样的装饰器模式：**
- `FileOutputStream` → `BufferedOutputStream` → `DataOutputStream`
- `Writer` → `BufferedWriter` → `PrintWriter`

---

## 四、装饰器 vs 继承：组合优于继承的经典案例

### 4.1 继承方案的问题

假设我们需要给咖啡添加不同配料：

```java
// 用继承实现：类爆炸
class Coffee {}
class MilkCoffee extends Coffee {}           // 加牛奶
class MochaCoffee extends Coffee {}         // 加摩卡
class FoamCoffee extends Coffee {}          // 加奶泡
class MilkMochaCoffee extends Coffee {}    // 加牛奶+摩卡
class MilkFoamCoffee extends Coffee {}     // 加牛奶+奶泡
class MochaFoamCoffee extends Coffee {}    // 加摩卡+奶泡
class MilkMochaFoamCoffee extends Coffee {} // 加牛奶+摩卡+奶泡

// 每增加一种配料，子类数量翻倍！
// 3种配料 → 8个子类
// 5种配料 → 32个子类
// 10种配料 → 1024个子类！！！类爆炸！
```

**继承的问题：**
1. **类爆炸**：配料组合数 = 2^n（n = 配料种类数）
2. **静态扩展**：编译时就决定了所有组合，无法运行时动态调整
3. **高度耦合**：子类与父类强耦合，修改父类影响所有子类
4. **违背开闭原则**：新增配料需要修改现有类

### 4.2 装饰器方案的优势

```java
/**
 * 装饰器方案：类数量 = n + 2（线性增长）
 */
public interface Coffee {
    double cost();
    String description();
}

// 具体组件
public class SimpleCoffee implements Coffee {
    @Override public double cost() { return 10.0; }
    @Override public String description() { return "美式咖啡"; }
}

// 抽象装饰器
public abstract class CoffeeDecorator implements Coffee {
    protected Coffee coffee;
    public CoffeeDecorator(Coffee coffee) { this.coffee = coffee; }
}

// 具体装饰器：牛奶
public class MilkDecorator extends CoffeeDecorator {
    public MilkDecorator(Coffee coffee) { super(coffee); }
    
    @Override public double cost() { return coffee.cost() + 3.0; }
    @Override public String description() { return coffee.description() + " + 牛奶"; }
}

// 具体装饰器：摩卡
public class MochaDecorator extends CoffeeDecorator {
    public MochaDecorator(Coffee coffee) { super(coffee); }
    
    @Override public double cost() { return coffee.cost() + 5.0; }
    @Override public String description() { return coffee.description() + " + 摩卡"; }
}

// 具体装饰器：奶泡
public class FoamDecorator extends CoffeeDecorator {
    public FoamDecorator(Coffee coffee) { super(coffee); }
    
    @Override public double cost() { return coffee.cost() + 4.0; }
    @Override public String description() { return coffee.description() + " + 奶泡"; }
}

// 客户端使用
public class CoffeeShop {
    public static void main(String[] args) {
        // 1. 只要美式
        Coffee c1 = new SimpleCoffee();
        System.out.println(c1.description() + " = ¥" + c1.cost());
        
        // 2. 美式 + 牛奶 + 摩卡（运行时动态组合！）
        Coffee c2 = new MilkDecorator(new MochaDecorator(new SimpleCoffee()));
        System.out.println(c2.description() + " = ¥" + c2.cost());
        
        // 3. 美式 + 奶泡
        Coffee c3 = new FoamDecorator(new SimpleCoffee());
        System.out.println(c3.description() + " = ¥" + c3.cost());
        
        // 4. 任意组合，任意顺序
        Coffee c4 = new MochaDecorator(new MilkDecorator(new SimpleCoffee()));
        System.out.println(c4.description() + " = ¥" + c4.cost());
    }
}
```

**输出：**
```
美式咖啡 = ¥10.0
美式咖啡 + 牛奶 + 摩卡 = ¥18.0
美式咖啡 + 奶泡 = ¥14.0
美式咖啡 + 牛奶 + 摩卡 = ¥18.0
```

### 4.3 对比总结

| 维度 | 继承方案 | 装饰器方案 |
|------|---------|-----------|
| **类数量** | 2^n（指数爆炸） | n + 2（线性增长） |
| **运行时灵活性** | ❌ 编译时固定 | ✅ 运行时动态组合 |
| **添加新配料** | 需要新增所有组合类 | 新增一个装饰器类即可 |
| **修改现有类** | 可能影响所有子类 | 不影响现有类 |
| **依赖关系** | 强耦合 | 松耦合（通过接口） |
| **复用性** | 低 | 高（装饰器可复用） |

---

## 五、装饰器 vs 代理：增强 vs 控制

> 这是面试中问到最多的对比题之一，必须深入理解。

### 5.1 本质区别

| 对比项 | 装饰器模式 | 代理模式 |
|--------|-----------|---------|
| **目的** | 动态**增强**对象功能 | **控制和管理**对对象的访问 |
| **关注点** | 功能增强（add behavior） | 访问控制（control access） |
| **透明性** | 客户端知道使用了装饰器 | 客户端通常不知道使用了代理 |
| **代码形式** | 在原方法前后添加代码 | 替换原方法或阻止调用 |
| **关系** | 组合 + 接口继承 | 组合 + 接口继承 |
| **运行时** | 可以任意组合多个装饰器 | 通常一对一代理 |

### 5.2 代理模式的实现

```java
/**
 * 代理模式示例
 * 代理：控制对对象的访问，可以阻止、增强或转发调用
 */
public class ProxyPattern {
    
    // ==== 代理：延迟加载 ====
    public interface Image { void display(); }
    
    public class RealImage implements Image {
        private String filename;
        
        public RealImage(String filename) {
            this.filename = filename;
            loadFromDisk(); // 模拟：构造时就加载（很重）
        }
        
        private void loadFromDisk() {
            System.out.println("从磁盘加载大图片: " + filename);
        }
        
        @Override
        public void display() {
            System.out.println("显示图片: " + filename);
        }
    }
    
    /**
     * 代理对象：延迟加载，控制访问时机
     */
    public class ImageProxy implements Image {
        private RealImage realImage;
        private String filename;
        
        public ImageProxy(String filename) { this.filename = filename; }
        
        @Override
        public void display() {
            // 懒加载：第一次调用时才创建真实对象
            if (realImage == null) {
                realImage = new RealImage(filename);
            }
            realImage.display();
        }
    }
    
    // ==== 代理：访问控制 ====
    public interface UserService {
        String getUserInfo(String userId);
        void deleteUser(String userId);
    }
    
    public class RealUserService implements UserService {
        @Override
        public String getUserInfo(String userId) {
            return "用户: " + userId + ", 姓名: 张三";
        }
        
        @Override
        public void deleteUser(String userId) {
            System.out.println("删除用户: " + userId);
        }
    }
    
    /**
     * 权限检查代理：控制谁可以删除用户
     */
    public class UserServiceProxy implements UserService {
        private RealUserService realService;
        private String currentUserRole;
        
        public UserServiceProxy(String currentUserRole) {
            this.realService = new RealUserService();
            this.currentUserRole = currentUserRole;
        }
        
        @Override
        public String getUserInfo(String userId) {
            return realService.getUserInfo(userId);
        }
        
        @Override
        public void deleteUser(String userId) {
            // 只有管理员可以删除（访问控制）
            if (!"ADMIN".equals(currentUserRole)) {
                throw new SecurityException("只有管理员可以删除用户！");
            }
            realService.deleteUser(userId);
        }
    }
}
```

### 5.3 两者融合的例子

实际上，装饰器和代理在代码结构上非常相似——都持有原始对象的引用，都实现同一接口。**关键区别在于 intent（意图）**：

```java
/**
 * 同一段代码，可以是装饰器，也可以是代理
 * 取决于使用意图，而非代码结构
 */
public class LoggingInputStream extends FilterInputStream {
    
    public LoggingInputStream(InputStream in) { super(in); }
    
    @Override
    public int read() throws IOException {
        System.out.println("【装饰器/代理】准备读取一个字节...");
        int result = super.read();
        System.out.println("【装饰器/代理】读取到字节: " + result);
        return result;
    }
}

// 用作装饰器时：给 InputStream 添加日志功能
InputStream loggedStream = new LoggingInputStream(new FileInputStream("data.txt"));

// 用作代理时：监控和限制访问（如果添加访问频率限制，就更偏向代理了）
```

**一句话总结：**
- **装饰器** = "我来给这个对象**加功能**"
- **代理** = "我来**控制**这个对象的访问"

---

## 六、Spring 框架中的装饰器应用

### 6.1 `DataSource` 装饰器

Spring 和 JDBC 中使用装饰器模式来增强数据源：

```java
/**
 * DataSource 接口（Component）
 * javax.sql.DataSource
 */
public interface DataSource extends CommonDataSource, Wrapper, AutoCloseable {
    Connection getConnection() throws SQLException;
    Connection getConnection(String username, String password) throws SQLException;
}

/**
 * 具体装饰器：DelegatingDataSource
 * Spring 提供的基础装饰器，用于代理数据源
 */
public class DelegatingDataSource implements DataSource {
    
    private DataSource targetDataSource;
    
    public DelegatingDataSource(DataSource targetDataSource) {
        this.targetDataSource = targetDataSource;
    }
    
    @Override
    public Connection getConnection() throws SQLException {
        return targetDataSource.getConnection();
    }
    
    @Override
    public Connection getConnection(String username, String password) throws SQLException {
        return targetDataSource.getConnection(username, password);
    }
}

/**
 * 具体装饰器：TransactionAwareDataSourceDecorator
 * 为数据源添加事务感知能力
 * 当在一个事务中获取连接时，返回同一个连接
 */
public class TransactionAwareDataSourceDecorator implements DataSource {
    
    private final DataSource targetDataSource;
    
    public TransactionAwareDataSourceDecorator(DataSource targetDataSource) {
        this.targetDataSource = targetDataSource;
    }
    
    @Override
    public Connection getConnection() throws SQLException {
        // 如果当前有事务，返回事务绑定的连接
        ConnectionHolder conHolder = (ConnectionHolder) TransactionSynchronizationManager
                .getResource(this.targetDataSource);
        if (conHolder != null) {
            return conHolder.getConnection();
        }
        Connection connection = this.targetDataSource.getConnection();
        return new TransactionAwareConnectionProxy(connection, this.targetDataSource);
    }
}

/**
 * 具体装饰器：LazyConnectionDataSourceDecorator
 * 懒加载连接，直到第一次真正使用 SQL 才获取数据库连接
 */
public class LazyConnectionDataSourceDecorator extends AbstractDataSource {
    
    private final DataSource targetDataSource;
    
    @Override
    public Connection getConnection() throws SQLException {
        return new LazyConnectionInvocationHandler(this.targetDataSource).getConnection();
    }
}
```

### 6.2 Spring Web 中的请求/响应装饰器

Spring MVC 中用装饰器模式处理 HTTP 请求和响应的增强：

```java
/**
 * HttpServletRequest 装饰器：日志请求装饰器
 */
public class LoggingHttpServletRequestWrapper extends HttpServletRequestWrapper {
    
    private final Logger logger = LoggerFactory.getLogger(getClass());
    private final long startTime;
    
    public LoggingHttpServletRequestWrapper(HttpServletRequest request) {
        super(request);
        this.startTime = System.currentTimeMillis();
    }
    
    @Override
    public Object getAttribute(String name) {
        Object value = super.getAttribute(name);
        logger.debug("getAttribute({}) = {}", name, value);
        return value;
    }
    
    public long getElapsedTime() {
        return System.currentTimeMillis() - startTime;
    }
}

/**
 * HttpServletResponse 装饰器：压缩响应装饰器
 */
public class GzipHttpServletResponseWrapper extends HttpServletResponseWrapper {
    
    private GzipOutputStream gzipOutputStream;
    
    public GzipHttpServletResponseWrapper(HttpServletResponse response) throws IOException {
        super(response);
    }
    
    @Override
    public ServletOutputStream getOutputStream() throws IOException {
        if (gzipOutputStream == null) {
            gzipOutputStream = new GzipOutputStream(getResponse().getOutputStream());
        }
        return gzipOutputStream;
    }
    
    @Override
    public void setHeader(String name, String value) {
        if ("Content-Encoding".equalsIgnoreCase(name) && "gzip".equalsIgnoreCase(value)) {
            return;
        }
        super.setHeader(name, value);
    }
}
```

### 6.3 Spring Cache 的装饰器链

```java
/**
 * Cache 接口就是 Component
 * LoggingCache（添加缓存操作日志）
 * SynchronizedCache（添加线程同步）
 */
public class LoggingCache implements Cache {
    
    private final Cache delegate;
    private final Logger logger;
    
    public LoggingCache(Cache delegate) {
        this.delegate = delegate;
        this.logger = LoggerFactory.getLogger(delegate.getClass());
    }
    
    @Override public String getName() { return delegate.getName(); }
    
    @Override
    public Object get(Object key) {
        Object result = delegate.get(key);
        logger.debug("Cache[{}] get key={}, hit={}", getName(), key, result != null);
        return result;
    }
    
    @Override
    public void put(Object key, Object value) {
        logger.debug("Cache[{}] put key={}", getName(), key);
        delegate.put(key, value);
    }
    
    @Override
    public void evict(Object key) {
        logger.debug("Cache[{}] evict key={}", getName(), key);
        delegate.evict(key);
    }
}
```

---

## 七、实际场景：HTTP 装饰器实战

在 Web 开发中，装饰器模式最常见的应用就是给 HTTP 请求/响应添加**横切关注点**：日志、认证、压缩、加密等。

### 7.1 场景描述

```
请求流程：

客户端 → LoggingFilter → AuthFilter → GzipFilter → CipherFilter → Controller
              ↓              ↓            ↓            ↓
         记录日志      检查认证      压缩数据       解密数据
```

### 7.2 完整实现

```java
// ========== 基础 HTTP 相关类 ==========

/** HTTP 请求接口（Component） */
public interface HttpRequest {
    String getMethod();
    String getPath();
    String getHeader(String name);
    byte[] getBody();
    void setAttribute(String key, Object value);
    Object getAttribute(String key);
}

/** HTTP 响应接口（Component） */
public interface HttpResponse {
    int getStatusCode();
    void setStatus(int code);
    void setHeader(String name, String value);
    void write(byte[] data);
    byte[] getBody();
}

/** HTTP 上下文 */
public class HttpContext {
    public HttpRequest request;
    public HttpResponse response;
    public HttpContext(HttpRequest request, HttpResponse response) {
        this.request = request;
        this.response = response;
    }
}

/** 基础 HTTP 请求（具体组件） */
public class BaseHttpRequest implements HttpRequest {
    private final Map<String, String> headers = new HashMap<>();
    private final Map<String, Object> attributes = new HashMap<>();
    private byte[] body;
    
    @Override public String getMethod() { return "GET"; }
    @Override public String getPath() { return "/api/user"; }
    @Override public String getHeader(String name) { return headers.get(name); }
    @Override public byte[] getBody() { return body; }
    @Override public void setAttribute(String k, Object v) { attributes.put(k, v); }
    @Override public Object getAttribute(String k) { return attributes.get(k); }
}

/** 基础 HTTP 响应（具体组件） */
public class BaseHttpResponse implements HttpResponse {
    private int statusCode = 200;
    private final Map<String, String> headers = new HashMap<>();
    private final ByteArrayOutputStream baos = new ByteArrayOutputStream();
    
    @Override public int getStatusCode() { return statusCode; }
    @Override public void setStatus(int code) { this.statusCode = code; }
    @Override public void setHeader(String name, String value) { headers.put(name, value); }
    @Override public void write(byte[] data) { baos.writeBytes(data); }
    @Override public byte[] getBody() { return baos.toByteArray(); }
}

// ========== 抽象装饰器 ==========

/** HTTP 处理器装饰器抽象基类 */
public abstract class HttpHandlerDecorator implements HttpRequest, HttpResponse {
    
    protected HttpContext wrapped;
    
    public HttpHandlerDecorator(HttpContext wrapped) {
        this.wrapped = wrapped;
    }
    
    // HttpRequest 方法默认转发
    @Override public String getMethod() { return wrapped.request.getMethod(); }
    @Override public String getPath() { return wrapped.request.getPath(); }
    @Override public String getHeader(String name) { return wrapped.request.getHeader(name); }
    @Override public byte[] getBody() { return wrapped.request.getBody(); }
    @Override public void setAttribute(String k, Object v) { wrapped.request.setAttribute(k, v); }
    @Override public Object getAttribute(String k) { return wrapped.request.getAttribute(k); }
    
    // HttpResponse 方法默认转发
    @Override public int getStatusCode() { return wrapped.response.getStatusCode(); }
    @Override public void setStatus(int code) { wrapped.response.setStatus(code); }
    @Override public void setHeader(String name, String value) { wrapped.response.setHeader(name, value); }
    @Override public void write(byte[] data) { wrapped.response.write(data); }
    @Override public byte[] getBody() { return wrapped.response.getBody(); }
}

// ========== 具体装饰器 ==========

/** 装饰器1：日志装饰器 - 记录请求/响应日志 */
public class LoggingDecorator extends HttpHandlerDecorator {
    
    private static final Logger log = LoggerFactory.getLogger(LoggingDecorator.class);
    
    public LoggingDecorator(HttpContext wrapped) { super(wrapped); }
    
    @Override
    public void write(byte[] data) {
        log.info("请求路径: {}, 方法: {}", wrapped.request.getPath(), wrapped.request.getMethod());
        log.info("响应状态: {}", wrapped.response.getStatusCode());
        log.info("响应数据大小: {} bytes", data.length);
        wrapped.response.write(data);
    }
}

/** 装饰器2：认证装饰器 - 检查 API Token */
public class AuthDecorator extends HttpHandlerDecorator {
    
    public AuthDecorator(HttpContext wrapped) { super(wrapped); }
    
    @Override
    public void write(byte[] data) {
        String token = wrapped.request.getHeader("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            wrapped.response.setStatus(401);
            wrapped.response.setHeader("Content-Type", "application/json");
            wrapped.response.write("{\"error\": \"Unauthorized\"}".getBytes());
            return;
        }
        // 验证通过，传递请求
        wrapped.response.write(data);
    }
}

/** 装饰器3：Gzip 压缩装饰器 - 自动压缩响应体 */
public class GzipDecorator extends HttpHandlerDecorator {
    
    public GzipDecorator(HttpContext wrapped) { super(wrapped); }
    
    @Override
    public void write(byte[] data) {
        try {
            // GZIP 压缩
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            GZIPOutputStream gzip = new GZIPOutputStream(bos);
            gzip.write(data);
            gzip.close();
            byte[] compressed = bos.toByteArray();
            
            // 检查压缩是否有效（压缩后更小才使用压缩）
            if (compressed.length < data.length) {
                wrapped.response.setHeader("Content-Encoding", "gzip");
                wrapped.response.write(compressed);
            } else {
                // 压缩无效，直接返回原始数据
                wrapped.response.write(data);
            }
        } catch (IOException e) {
            wrapped.response.write(data);
        }
    }
}

/** 装饰器4：AES 加密装饰器 - 加密响应数据 */
public class CipherDecorator extends HttpHandlerDecorator {
    
    private static final String SECRET_KEY = "0123456789abcdef"; // 16字节 AES key
    
    public CipherDecorator(HttpContext wrapped) { super(wrapped); }
    
    @Override
    public void write(byte[] data) {
        try {
            Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
            SecretKeySpec keySpec = new SecretKeySpec(SECRET_KEY.getBytes(), "AES");
            cipher.init(Cipher.ENCRYPT_MODE, keySpec);
            byte[] encrypted = cipher.doFinal(data);
            wrapped.response.setHeader("X-Encrypted", "true");
            wrapped.response.write(encrypted);
        } catch (Exception e) {
            wrapped.response.write(data);
        }
    }
}

// ========== 使用示例 ==========

public class HttpClientDemo {
    public static void main(String[] args) {
        // 创建基础请求/响应
        HttpContext context = new HttpContext(
            new BaseHttpRequest(),
            new BaseHttpResponse()
        );
        
        // 装饰器链：日志 → 认证 → 压缩 → 加密
        HttpContext decorated = new CipherDecorator(
            new GzipDecorator(
                new AuthDecorator(
                    new LoggingDecorator(context)
                )
            )
        );
        
        // 发送请求
        decorated.write("{\"message\": \"Hello, World!\"}".getBytes());
    }
}
```

---

## 八、优缺点分析

### 8.1 优点

| 优点 | 说明 |
|------|------|
| **动态扩展** | 运行时动态添加或删除功能，无需修改现有代码 |
| **避免类爆炸** | 用少量类实现大量组合，继承方案需要指数级类数量 |
| **符合开闭原则** | 新增功能只需添加新装饰器，无需修改现有类 |
| **符合单一职责** | 每个装饰器只负责一个功能，职责清晰 |
| **灵活组合** | 可以按需组合多个装饰器，顺序可变 |
| **可撤销** | 运行时可以去掉某个装饰器，恢复到原始对象 |

### 8.2 缺点

| 缺点 | 说明 |
|------|------|
| **增加复杂度** | 会产生许多小对象（装饰器），增加系统复杂度 |
| **调试困难** | 装饰器层层嵌套，调试时难以追踪调用链 |
| **类型识别困难** | 客户端难以知道对象被哪些装饰器包装过 |
| **性能开销** | 每经过一个装饰器就多一层方法调用 |

### 8.3 适用场景

| 场景 | 示例 |
|------|------|
| **需要动态扩展功能** | 咖啡配料、文本格式化 |
| **需要组合多种功能** | HTTP 请求的日志、认证、压缩、加密 |
| **避免类爆炸** | 无法通过继承实现所有组合 |
| **需要可撤销的扩展** | 临时添加功能后可以移除 |
| **I/O 操作** | Java I/O 流的缓冲、压缩、加密等 |

---

## 九、高频面试题

### Q1: 什么是装饰器模式？它的核心思想是什么？

**答案：**

装饰器模式是一种结构型设计模式，**允许在不修改原有对象结构的情况下，动态地给对象添加额外的职责**。

**核心思想：**
- **组合优于继承**：通过组合（持有对象引用）而非继承来扩展功能
- **动态扩展**：在运行时而非编译时决定对象的功能组合
- **层层包装**：装饰器可以嵌套，每层添加一项功能

**生活中的类比：** 点咖啡时可以加牛奶、摩卡、奶泡等，这些"配料"就是装饰器，可以按需组合。

---

### Q2: Java I/O 如何体现装饰器模式？请举例说明。

**答案：**

Java I/O 是装饰器模式的经典应用。`InputStream` 是抽象组件，`FileInputStream` 是具体组件，`FilterInputStream` 是抽象装饰器，`BufferedInputStream`、`DataInputStream` 等是具体装饰器。

**示例代码：**
```java
// 层层装饰
InputStream is = new FileInputStream("data.bin");       // 具体组件：文件读取
is = new BufferedInputStream(is);                      // 装饰器：添加缓冲
is = new DataInputStream(is);                          // 装饰器：添加数据类型读取

// 使用装饰后的流
DataInputStream dis = (DataInputStream) is;
int num = dis.readInt();
String str = dis.readUTF();
```

**继承关系：**
- `InputStream`（抽象组件）
  - `FileInputStream`（具体组件）
  - `FilterInputStream`（抽象装饰器）
    - `BufferedInputStream`（具体装饰器：缓冲）
    - `DataInputStream`（具体装饰器：数据类型）
    - `PushbackInputStream`（具体装饰器：推回）
    - `CipherInputStream`（具体装饰器：加密）

---

### Q3: 装饰器模式和代理模式有什么区别？

**答案：**

| 对比项 | 装饰器模式 | 代理模式 |
|--------|-----------|---------|
| **目的** | 动态增强对象功能 | 控制和管理对对象的访问 |
| **关注点** | 功能增强 | 访问控制 |
| **行为** | 增加行为（add behavior） | 控制行为（control behavior） |
| **组合性** | 可以多层嵌套组合 | 通常一对一代理 |
| **透明性** | 客户端知道使用了装饰器 | 客户端通常不知道 |

**装饰器示例：** 给 `InputStream` 添加缓冲功能
```java
InputStream is = new BufferedInputStream(new FileInputStream("file.txt"));
```

**代理示例：** 控制对图片的延迟加载
```java
Image image = new ImageProxy("photo.jpg"); // 代理，延迟加载
image.display(); // 第一次调用时才真正加载图片
```

**关键区别：**
- 装饰器关注"给对象添加功能"
- 代理关注"控制对象的访问"

---

### Q4: 装饰器模式相比继承有什么优势？为什么说"组合优于继承"？

**答案：**

**继承的问题：**
1. **类爆炸**：如果用继承实现所有功能组合，类数量 = 2^n（指数级增长）
2. **静态扩展**：编译时固定，无法运行时动态调整
3. **高耦合**：子类与父类紧密耦合，修改父类影响所有子类
4. **违反开闭原则**：新增功能需要修改现有类

**装饰器优势：**
1. **类数量少**：类数量 = n + 2（线性增长）
2. **动态扩展**：运行时可灵活组合装饰器
3. **低耦合**：装饰器与被装饰对象只通过接口关联
4. **符合开闭原则**：新增功能只需添加新装饰器类

**示例对比：**
```java
// 继承方案：需要创建大量子类
class MilkMochaFoamCoffee extends MochaFoamCoffee {}

// 装饰器方案：只需创建一个装饰器
Coffee coffee = new FoamDecorator(new MochaDecorator(new MilkDecorator(new SimpleCoffee())));
```

**"组合优于继承"原则：**
- 组合关系在运行时可改变，继承关系在编译时固定
- 组合更灵活，可以随时添加/移除功能
- 组合更松耦合，符合"依赖倒置原则"

---

### Q5: Spring 中有哪些装饰器模式的应用？

**答案：**

**1. DataSource 装饰器：**
```java
// 为数据源添加事务感知
DataSource txAware = new TransactionAwareDataSourceDecorator(dataSource);

// 为数据源添加懒加载
DataSource lazy = new LazyConnectionDataSourceDecorator(dataSource);
```

**2. HttpServletRequestWrapper / HttpServletResponseWrapper：**
```java
// Spring MVC 提供的装饰器基类
public class MyRequestWrapper extends HttpServletRequestWrapper {
    public MyRequestWrapper(HttpServletRequest request) {
        super(request);
    }
    
    @Override
    public String getParameter(String name) {
        // 增强：添加 XSS 过滤
        String value = super.getParameter(name);
        return value == null ? null : value.replaceAll("<", "&lt;");
    }
}
```

**3. Spring Cache 装饰器：**
```java
// Spring Cache 可以通过装饰器添加日志、同步等功能
Cache loggingCache = new LoggingCache(delegateCache);
Cache syncCache = new SynchronizedCache(loggingCache);
```

**4. Spring AOP 中的代理模式：**
- 虽然 AOP 主要使用代理模式，但代理与装饰器在结构上相似
- 都是通过包装对象来增强功能

---

## 十、总结

装饰器模式是 Java 面试中的高频考点，核心要点：

| 核心要点 | 记忆口诀 |
|---------|---------|
| **定义** | 动态给对象添加职责 |
| **角色** | Component、ConcreteComponent、Decorator、ConcreteDecorator |
| **JDK 应用** | InputStream 体系（FileInputStream → BufferedInputStream → DataInputStream） |
| **vs 继承** | 组合优于继承，避免类爆炸 |
| **vs 代理** | 装饰器增强功能，代理控制访问 |
| **Spring 应用** | DataSource、HttpServletRequestWrapper、Cache |

**一句话总结：**
> 装饰器模式 = 组合 + 接口继承 + 层层包装，实现动态、灵活、可组合的功能扩展。

---

**⭐ 重点：深入理解 Java I/O 体系的装饰器实现，掌握装饰器与继承、代理的区别！**