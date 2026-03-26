---
layout: default
title: 适配器模式（Adapter Pattern）
---
# 适配器模式（Adapter Pattern）：对象与类的桥梁

> "把"既有的东西"装进"新的接口里，让不兼容的双方能够愉快地合作。"

## 🎯 面试重点速览

| 维度 | 内容 |
|------|------|
| **核心作用** | 接口转换，使不兼容的类能一起工作 |
| **三种类型** | 类适配器、对象适配器、接口适配器 |
| **Spring 经典应用** | HandlerAdapter — 适配不同 Controller |
| **JDK 经典案例** | InputStreamReader、Arrays.asList()、Collections.enumeration() |
| **与装饰器/代理的区别** | 适配器"改写接口"，装饰器"增强功能"，代理"控制访问" |
| **面试高频问法** | "适配器模式解决了什么问题？""Spring 中哪些地方用了适配器？" |

---

## 1. 为什么需要适配器模式？

在软件开发中，我们经常会遇到这样的场景：

- **旧代码不可改**：系统早期已经写好了一个类 `LegacyLogger`，但接口签名和现在需要的不一样。
- **第三方库不兼容**：引入了第三方 SDK，它提供的接口和你系统定义的接口完全不同。
- **统一抽象层**：需要对接多种外部系统，每种系统的接口各不相同，但业务层只愿意面对一套统一接口。

这些问题催生了**适配器模式**——它本质上是一个"翻译官"，把 A 接口"翻译"成 B 接口，让双方都能正常工作，而无需改动原有的代码。

> 适配器模式（Adapter Pattern）**不属于**创建型模式，而是一种**结构型模式**。它位于 GoF 设计模式的第二类，和代理模式、装饰器模式同属一类。

---

## 2. 三种适配器类型详解

适配器模式根据实现方式的不同，分为三大类型。下面我们用同一个业务场景来逐一演示：

**业务场景：** 物流系统需要调用不同的运输服务。老系统提供了一个 `LogisticsService`，它的方法是 `sendBySea()`，而业务层希望调用统一的方法 `transport()`。

### 2.1 类适配器（Class Adapter）—— 通过继承实现

**原理：** 适配器同时**继承**被适配类（Adaptee）和**实现**目标接口（Target）。这样，它既有父类的方法，又满足目标接口的契约。

```java
// 目标接口：业务层期望的接口
public interface Transport {
    void transport(String goods, String destination);
}

// 被适配类：已有的旧物流服务
public class LegacyLogistics {
    // 老系统只有海运方法
    public void sendBySea(String goods) {
        System.out.println("通过海运发送：" + goods);
    }
}

// 类适配器：继承被适配类 + 实现目标接口
public class ClassLogisticsAdapter extends LegacyLogistics implements Transport {
    @Override
    public void transport(String goods, String destination) {
        // 把业务层的调用"翻译"成老系统的方法
        sendBySea(goods + " 到 " + destination);
    }
}
```

**测试：**

```java
public class AdapterPatternTest {
    public static void main(String[] args) {
        Transport transport = new ClassLogisticsAdapter();
        transport.transport("电子产品", "美国洛杉矶");
        // 输出：通过海运发送：电子产品 到 美国洛杉矶
    }
}
```

**UML 类图：**

```
┌─────────────┐       ┌─────────────────────┐       ┌─────────────┐
│  Transport  │       │ ClassLogisticsAdapter│       │LegacyLogistics│
│ (Target)   │       │     (Adapter)        │       │  (Adaptee)  │
├─────────────┤       ├─────────────────────┤       ├─────────────┤
│+transport()│       │+transport()         │       │+sendBySea() │
└──────┬──────┘       └─────────┬───────────┘       └──────▲──────┘
       │                         │                           │
       │                         │  extends                  │
       │◄────────────────────────┘                           │
       │                                                      │
       │  implements                                         │
───────┴──────────────────────────────────────────────────────┘
```

**特点：**
- ✅ 直接继承被适配类，可以调用父类的方法，实现简单。
- ✅ 可重写被适配类的方法，灵活性高。
- ❌ Java 是单继承，一旦继承了某个类，就不能再继承其他类。如果被适配类是 `final` 类，则无法使用。
- ❌ 如果 Target 是接口，Adaptee 是类，类适配器需要继承 Adaptee，这在 Java 中只能单继承，限制了扩展性。

---

### 2.2 对象适配器（Object Adapter）—— 通过组合实现（推荐）

**原理：** 适配器**持有**被适配类的一个实例（组合），而不是继承它。然后在实现目标接口时，内部委托给这个实例。

```java
// 目标接口
public interface Transport {
    void transport(String goods, String destination);
}

// 被适配类
public class LegacyLogistics {
    public void sendBySea(String goods) {
        System.out.println("通过海运发送：" + goods);
    }
}

// 对象适配器：持有被适配类的实例
public class ObjectLogisticsAdapter implements Transport {
    
    // 持有被适配类的引用（组合）
    private LegacyLogistics legacyLogistics;
    
    public ObjectLogisticsAdapter(LegacyLogistics legacyLogistics) {
        this.legacyLogistics = legacyLogistics;
    }
    
    @Override
    public void transport(String goods, String destination) {
        // 适配逻辑：包装参数，委托给老系统
        legacyLogistics.sendBySea(goods + " [目的地: " + destination + "]");
    }
}
```

**测试：**

```java
public class AdapterPatternTest {
    public static void main(String[] args) {
        LegacyLogistics legacy = new LegacyLogistics();
        Transport transport = new ObjectLogisticsAdapter(legacy);
        transport.transport("医疗器械", "德国法兰克福");
        // 输出：通过海运发送：医疗器械 [目的地: 德国法兰克福]
    }
}
```

**UML 类图：**

```
┌─────────────┐       ┌─────────────────────┐       ┌─────────────────┐
│  Transport  │       │ObjectLogisticsAdapter│       │ LegacyLogistics │
│ (Target)   │       │     (Adapter)        │       │   (Adaptee)     │
├─────────────┤       ├─────────────────────┤       ├─────────────────┤
│+transport()│       │-legacyLogistics     │       │+sendBySea()     │
└──────┬──────┘       │+transport()         │       └─────────────────┘
       │              │+ObjectLogistics...()│              ▲
       │◄─────────────┤                     ├──────────────┘
       │              │                     │   (持有实例)
       │  implements  └─────────────────────┘
───────┴──────────────────────────────────────────────────────
```

**特点：**
- ✅ **组合优于继承**：对象适配器不依赖被适配类的继承结构，更灵活。
- ✅ 可以适配被适配类的所有子类，只要传入对应的实例即可。
- ✅ 符合"合成复用原则"（CARP）。
- ✅ 被适配类可以是 `final`、可以是接口、可以是任何类。
- ❌ 相比类适配器，多了一次方法调用（间接调用），性能略低（但微乎其微）。
- ❌ 需要在适配器中写更多的"胶水代码"。

> **面试重点：绝大多数场景推荐使用对象适配器。** 这也是《Effective Java》第 18 条"组合优于继承"的精神体现。

---

### 2.3 接口适配器（Interface Adapter）—— 按需覆盖

**原理：** 当一个接口中定义了太多方法，而我们的类只需要使用其中少数几个时，可以先用一个抽象类（Default Adapter）实现该接口的所有方法（空实现或默认实现），然后让具体的业务类继承这个抽象类，只重写需要的方法即可。

**也叫"缺省适配器模式"（Default Adapter Pattern）。**

```java
// 一个大型接口，定义了 5 个方法
public interface FileOperation {
    void openFile();
    void readFile();
    void writeFile();
    void closeFile();
    void backupFile();
}

// 抽象适配器：实现接口的所有方法，提供空实现
public abstract class AbstractFileAdapter implements FileOperation {
    @Override
    public void openFile() { }
    
    @Override
    public void readFile() { }
    
    @Override
    public void writeFile() { }
    
    @Override
    public void closeFile() { }
    
    @Override
    public void backupFile() { }
}

// 具体业务类：只需要读写功能，只重写这两个方法
public class SimpleFileReader extends AbstractFileAdapter {
    private String filePath;
    
    public SimpleFileReader(String filePath) {
        this.filePath = filePath;
    }
    
    @Override
    public void openFile() {
        System.out.println("打开文件：" + filePath);
    }
    
    @Override
    public void readFile() {
        System.out.println("读取文件内容...");
    }
    
    @Override
    public void closeFile() {
        System.out.println("关闭文件");
    }
    
    // 不需要的方法，无需重写
}
```

**使用场景：**
- WindowAdapter、MouseAdapter、KeyAdapter（Java AWT 中的经典用法）
- Spring MVC 的 `HandlerAdapter` 也有类似的思路

---

## 3. JDK 中的适配器模式

### 3.1 InputStreamReader —— 字节流 → 字符流的桥梁

```java
// InputStreamReader 是典型的适配器
// 被适配者：InputStream（字节流，字节输入）
// 目标接口：Reader（字符流，字符输入）

InputStream is = new FileInputStream("data.txt");
// 把字节流适配成字符流
Reader reader = new InputStreamReader(is, StandardCharsets.UTF_8);

char[] buffer = new char[1024];
int len = reader.read(buffer);
reader.close();
```

在 JDK 中，`InputStreamReader` 继承自 `Reader`（目标抽象），内部持有一个 `StreamDecoder`（实际是被适配者的包装），将字节流 decode 成字符流。这正是一个**对象适配器**的实现。

```java
// 简化版原理
public class InputStreamReader extends Reader {
    private final StreamDecoder decoder;  // 持有被适配者的引用
    
    public InputStreamReader(InputStream in, Charset charset) {
        this.decoder = new StreamDecoder(in, charset);
    }
    
    @Override
    public int read(char[] cbuf, int offset, int length) throws IOException {
        return decoder.read(cbuf, offset, length);
    }
}
```

### 3.2 Arrays.asList() —— 数组 → 列表的适配

```java
String[] array = {"Java", "Python", "Go"};
List<String> list = Arrays.asList(array);

// asList() 返回的是一个适配器对象
// 它持有原数组的引用，而非拷贝
// 对 list 的修改会影响原数组！
```

`Arrays.asList()` 返回的是 `Arrays.ArrayList`（内部类），它**并非** `java.util.ArrayList`。它是一个适配器——持有数组引用，只提供有限的 List 操作（不支持增删）。这是适配器模式的经典应用。

### 3.3 Collections.enumeration() —— 旧 API 适配新 API

```java
// Enumeration 是 JDK 1.0 的遗留接口
// Iterator 是 JDK 1.2 引入的更优接口
// Collections.enumeration() 将 Iterator 适配成 Enumeration

List<String> list = new ArrayList<>();
list.add("a");
list.add("b");

Enumeration<String> enumeration = Collections.enumeration(list);

while (enumeration.hasMoreElements()) {
    System.out.println(enumeration.nextElement());
}
```

---

## 4. Spring 框架中的适配器模式

### 4.1 HandlerAdapter —— DispatcherServlet 的核心

Spring MVC 的 `DispatcherServlet` 是前端控制器，所有请求都经过它。但请求对应的 Controller 类型五花八门：

- `@Controller` 注解的 Controller
- 实现 `HttpRequestHandler` 接口的 Handler
- 实现 `Servlet` 接口的原生 Servlet
- 实现 `ResponseEntityExceptionHandler` 的异常处理器

`DispatcherServlet` 不可能为每种 Controller 写一套处理逻辑。它定义了一个统一的接口 `HandlerAdapter`：

```java
public interface HandlerAdapter {
    // 判断这个适配器能否处理给定的 handler
    boolean supports(Object handler);
    
    // 用适配好的 handler 处理请求
    ModelAndView handle(HttpServletRequest request, 
                        HttpServletResponse response, 
                        Object handler) throws Exception;
    
    long getLastModified(HttpServletRequest request, Object handler);
}
```

每种 Controller 都有对应的适配器：

```
RequestMappingHandlerAdapter   → 处理 @RequestMapping/@GetMapping 等
HttpRequestHandlerAdapter      → 处理实现 HttpRequestHandler 接口的类
SimpleControllerHandlerAdapter → 处理实现 Controller 接口的类（老式）
SimpleServletHandlerAdapter     → 处理实现 Servlet 接口的类
```

**核心工作流程：**

```java
public class DispatcherServlet {
    
    private List<HandlerAdapter> handlerAdapters;
    
    // DispatcherServlet 的 doDispatch 方法简化版
    protected void doDispatch(HttpServletRequest request, 
                               HttpServletResponse response) {
        
        // 1. 根据 URL 获取 handler
        HandlerExecutionChain handler = getHandler(request);
        
        // 2. 找到支持这个 handler 的适配器
        HandlerAdapter adapter = getHandlerAdapter(handler.getHandler());
        
        // 3. 用适配器统一处理（适配器内部负责调用具体 Controller）
        adapter.handle(request, response, handler.getHandler());
    }
    
    private HandlerAdapter getHandlerAdapter(Object handler) {
        for (HandlerAdapter adapter : handlerAdapters) {
            if (adapter.supports(handler)) {
                return adapter;  // 找到匹配的适配器就返回
            }
        }
        throw new ServletException("找不到支持的适配器: " + handler);
    }
}
```

> **面试点：** `HandlerAdapter` 的好处是 `DispatcherServlet` 永远不需要知道具体是哪种 Controller，所有适配逻辑都封装在各自的 HandlerAdapter 中。这是典型的适配器模式应用，符合**开闭原则**——新增一种 Controller 类型，只需新增一个 HandlerAdapter，无需修改中央调度器。

### 4.2 Spring AOP 中的适配器

Spring MVC 3.0 开始引入了 `RequestMappingHandlerAdapter`，它内部处理方法参数解析、返回值处理、异常处理等。这个组件也大量使用了适配器思想——将 `HandlerMethod`（持有方法 + 对象 + 参数信息的封装）的调用，适配成统一的 `ModelAndView` 返回。

---

## 5. JDBC 适配器——统一数据库操作

Java 程序与数据库通信时，面对的是统一的 `JDBC` 接口（`java.sql.Driver`、`Connection`、`Statement`、`ResultSet`）。但各数据库厂商提供的驱动实现完全不同：

```
Oracle     → oracle.jdbc.driver.OracleDriver
MySQL      → com.mysql.cj.jdbc.Driver
PostgreSQL → org.postgresql.Driver
SQL Server → com.microsoft.sqlserver.jdbc.SQLServerDriver
```

JDBC 本身就是一个巨大的适配器系统：

```
应用程序（使用 JDBC 标准接口）
        ↓
    JDBC API（java.sql 包）
        ↓
    JDBC Driver Manager（根据 URL 选择驱动）
        ↓
    数据库驱动（各厂商实现，适配具体数据库协议）
        ↓
    数据库（MySQL/Oracle/PostgreSQL...）
```

`Class.forName("com.mysql.cj.jdbc.Driver")` 注册驱动后，`DriverManager.getConnection()` 实际上是创建了一个适配器对象，它把你的标准 SQL 调用"翻译"成 MySQL 私有协议。

---

## 6. 实际业务场景

### 场景一：对接第三方支付

业务系统定义了一套统一的支付接口 `PaymentGateway`，但需要对接支付宝、微信支付、银联等多个第三方。每家支付 SDK 的接口完全不同：

```java
// 统一支付接口（Target）
public interface PaymentGateway {
    PayResult pay(String orderId, BigDecimal amount, String channel);
    RefundResult refund(String orderId, BigDecimal amount);
}

// 支付宝适配器（对象适配器）
public class AlipayAdapter implements PaymentGateway {
    private final AlipaySdk alipaySdk;  // 第三方 SDK
    
    public AlipayAdapter(AlipaySdk alipaySdk) {
        this.alipaySdk = alipaySdk;
    }
    
    @Override
    public PayResult pay(String orderId, BigDecimal amount, String channel) {
        // 把统一参数适配成支付宝的请求参数
        AlipayTradePayRequest request = new AlipayTradePayRequest();
        request.setBizContent("{\"out_trade_no\":\"" + orderId + "\"," +
                "\"total_amount\":\"" + amount + "\"," +
                "\"subject\":\"商品购买\"}");
        
        AlipayTradePayResponse response = alipaySdk.execute(request);
        
        // 把支付宝的响应适配成统一格式
        return new PayResult(response.getTradeNo(), 
                response.isSuccess() ? "SUCCESS" : "FAILED");
    }
    
    @Override
    public RefundResult refund(String orderId, BigDecimal amount) {
        // 类似适配逻辑...
        return null;
    }
}

// 微信支付适配器
public class WechatPayAdapter implements PaymentGateway {
    private final WXPay wxPay;  // 第三方 SDK
    
    @Override
    public PayResult pay(String orderId, BigDecimal amount, String channel) {
        // 适配微信支付的请求格式
        Map<String, String> data = new HashMap<>();
        data.put("out_trade_no", orderId);
        data.put("total_fee", amount.multiply(BigDecimal.valueOf(100)).toString());
        // ... 其他微信特有参数
        
        Map<String, String> result = wxPay.unifiedOrder(data);
        return new PayResult(result.get("transaction_id"), 
                "SUCCESS".equals(result.get("result_code")) ? "SUCCESS" : "FAILED");
    }
    
    @Override
    public RefundResult refund(String orderId, BigDecimal amount) {
        return null;
    }
}
```

这样业务层完全不需要关心具体用哪家支付，一个 `PaymentGateway` 接口打天下：

```java
public class OrderService {
    
    // 运行时注入具体的适配器实现
    private PaymentGateway paymentGateway;
    
    public void payOrder(String orderId, BigDecimal amount) {
        // 统一调用接口，底层自动适配到对应支付渠道
        PayResult result = paymentGateway.pay(orderId, amount, "alipay");
    }
}
```

### 场景二：兼容旧接口

公司系统升级，旧的 `UserServiceV1` 有方法 `getUserInfoById(int id)`，新的 `UserServiceV2` 改成了 `getUserInfo(String userId)`。为了不对调用方产生冲击，用适配器包装新服务：

```java
public class UserServiceV1Adapter implements UserServiceV1 {
    private final UserServiceV2 userServiceV2;
    
    @Override
    public UserInfo getUserInfoById(int id) {
        // 把旧参数类型适配成新的
        return userServiceV2.getUserInfo(String.valueOf(id));
    }
}
```

### 场景三：多数据源适配

报表系统需要从 MySQL、Redis、MongoDB 三种数据源读取数据。定义统一接口后，每种数据源用一个适配器：

```java
public interface DataSource<T> {
    T query(String key);
    void save(String key, T value);
}

// MySQL 数据源适配器
public class MySQLDataSourceAdapter<T> implements DataSource<T> {
    // 持有 MyBatis / JdbcTemplate
}

// Redis 数据源适配器
public class RedisDataSourceAdapter<T> implements DataSource<T> {
    // 持有 Jedis / Redisson
}

// MongoDB 数据源适配器
public class MongoDataSourceAdapter<T> implements DataSource<T> {
    // 持有 MongoTemplate
}
```

---

## 7. 适配器 vs 装饰器 vs 代理——三剑客对比

这是面试中出现频率极高的问题。三者看起来相似，但意图完全不同：

| 对比维度 | 适配器模式 | 装饰器模式 | 代理模式 |
|---------|-----------|-----------|---------|
| **核心目的** | 转换接口，让不兼容的双方能合作 | 动态增强对象功能 | 控制对对象的访问 |
| **关注点** | 接口兼容性 | 功能增强 | 访问控制 |
| **接口关系** | 适配器实现目标接口，被适配者接口可不同 | 装饰器和被装饰者实现同一接口 | 代理和真实对象实现同一接口 |
| **对象数量** | 适配器持有被适配者（1:1） | 装饰器包装被装饰者（可层层嵌套） | 代理持有真实对象（1:1） |
| **运行时行为** | 编译时接口就确定了 | 可在运行时动态增减装饰器 | 可在运行时动态创建代理 |
| **典型场景** | 对接第三方库、兼容旧接口 | IO 流包装、BufferedInputStream | 远程代理、AOP 切面、权限校验 |
| **是否修改接口** | 适配器**改写/翻译**接口 | 装饰器**保持**接口不变 | 代理**保持**接口不变 |
| **举例** | `InputStreamReader` 把字节流转字符 | `BufferedInputStream` 增强 FileInputStream | `RMI` 远程代理 |

**代码层面的直观区别：**

```java
// 适配器：把 A 接口"翻译"成 B 接口
public class Adapter implements B {
    private A a;  // A 和 B 接口不同
    @Override
    public void methodB() {
        a.methodA();  // 翻译
    }
}

// 装饰器：保持接口不变，增强功能
public class Decorator implements A {
    private A a;  // A 和 Decorator 实现同一接口
    @Override
    public void methodA() {
        a.methodA();      // 先调原功能
        extraOperation(); // 再增强
    }
}

// 代理：保持接口不变，控制访问
public class Proxy implements A {
    private A a;  // A 和 Proxy 实现同一接口
    @Override
    public void methodA() {
        if (!checkAccess()) return;  // 访问控制
        a.methodA();                  // 委托
        logAccess();                 // 记录
    }
}
```

> **记忆口诀：**
> - **适配器**：翻译官——让说不同语言的人对话（接口转换）
> - **装饰器**：增强器——穿衣戴帽，功能更强（功能增强）
> - **代理**：门卫——决定你能不能进门（访问控制）

---

## 8. 优缺点分析

### ✅ 优点

1. **良好的复用性**：复用一个已有的类，不需要修改它的源码。对旧系统改造尤其有用。
2. **解耦**：客户端和被适配者之间解耦，客户端只依赖目标接口，不依赖具体实现。
3. **符合开闭原则**：新增一种被适配者，只需新增适配器，无需修改现有代码。
4. **单一职责原则**：适配器只负责接口转换，职责清晰。
5. **类适配器可以重写被适配者的行为**：子类可以直接覆盖父类方法。

### ❌ 缺点

1. **过多适配器会增加系统复杂度**：如果系统中到处都是适配器，会造成代码可读性下降。
2. **类适配器受 Java 单继承限制**：只能适配一个被适配者，不能同时适配多个。
3. **对象适配器调用链更长**：通过组合调用，性能上多一次间接跳转（影响极小）。
4. **过度使用适配器会掩盖设计问题**：如果到处都是不兼容，说明接口设计一开始就有问题。适配器是补救措施，不能当成主要的设计手段。

---

## 9. 高频面试题

### Q1：适配器模式和策略模式有什么区别？

**答：** 适配器模式和策略模式都涉及将某种行为"包装"起来，但意图完全不同：

- **适配器模式**：解决"接口不匹配"的问题。强调"翻译"——让原本不能工作的组合能够工作。适配器在运行时通常**不变化**。
- **策略模式**：解决"多种算法/行为可互换"的问题。强调"选择"——在运行时根据条件选择不同的策略对象。

```java
// 策略模式：行为可切换
public interface SortStrategy {
    List<T> sort(List<T> list);
}
public class QuickSortStrategy implements SortStrategy { }
public class MergeSortStrategy implements SortStrategy { }
// 运行时选择策略
SortStrategy strategy = useQuickSort ? new QuickSortStrategy() : new MergeSortStrategy();

// 适配器模式：接口转换
// 新旧系统接口不一致，用适配器翻译
public class NewSystemAdapter implements OldInterface {
    private NewSystem newSystem;
    // 把 OldInterface 的调用翻译成 NewSystem 的调用
}
```

### Q2：Spring 中哪些地方用到了适配器模式？

**答：** Spring 源码中适配器模式的应用非常广泛，最典型的有三处：

1. **HandlerAdapter**：适配不同类型的 Controller（`RequestMappingHandlerAdapter`、`HttpRequestHandlerAdapter` 等），`DispatcherServlet` 通过适配器统一处理请求，无需关心 Controller 的具体类型。
2. **AdvisorAdapter**：Spring AOP 中，`MethodInterceptor` 有多种实现（JDK 动态代理的拦截器、CGLIB 的回调），`AdvisorAdapter` 负责将 `Advisor` 适配成 `MethodInterceptor`。
3. **ConstraintValidatorAdapter**：Spring Validation 中，`@Valid` 注解的处理需要适配不同的约束验证器（如 `@NotNull`、`@Size` 等）。

### Q3：适配器模式属于创建型还是结构型？为什么？

**答：** 适配器模式属于**结构型模式**（Structural Pattern），不属于创建型模式。

GoF 设计模式将 23 种设计模式分为三类：
- **创建型**（5种）：单例、工厂、抽象工厂、建造者、原型 —— 关注对象的创建
- **结构型**（7种）：适配器、装饰器、代理、桥接、组合、外观、享元 —— 关注对象之间的组合结构
- **行为型**（11种）：策略、观察者、模板方法、职责链等 —— 关注对象之间的职责分配和算法

适配器模式的核心是"组合/继承已有的类，形成新的结构"，因此归为结构型。

### Q4：什么情况下用类适配器，什么情况下用对象适配器？

**答：** 以下情况**优先使用对象适配器**（99%的场景）：

- 被适配者是类，且 Java 单继承限制了你需要继承其他类
- 被适配者是 `final` 类（无法继承）
- 被适配者可能有多个子类，需要灵活适配任意一个子类
- 追求代码的扩展性和可维护性

以下情况**可以使用类适配器**：

- 被适配者和目标接口都是类（不是接口），且你希望复用被适配者的方法实现而不做额外包装
- 被适配者不太可能变化，且系统规模较小
- Java、C++ 等支持多继承的语言（Python 等动态语言不存在这个问题）

> **实战建议：** 在 Java 中，**始终优先考虑对象适配器**。这是 GoF 书中明确推荐的做法，也是大多数源码（Spring、JDBC）采用的方式。

---

## 10. 总结

```
┌──────────────────────────────────────────────────────────────┐
│                      适配器模式（Adapter Pattern）              │
├──────────────────────────────────────────────────────────────┤
│  核心：把"既有实现"适配到"目标接口"，实现不兼容类之间的协作         │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │  类适配器     │   │  对象适配器   │   │  接口适配器   │    │
│  │ (extends)    │   │ (组合) ⭐    │   │ (DefaultAdp)  │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                              │
│  经典应用：                                                     │
│  ✅ InputStreamReader — 字节流→字符流                          │
│  ✅ Arrays.asList()  — 数组→固定列表                          │
│  ✅ HandlerAdapter   — 统一调度不同 Controller                 │
│  ✅ JDBC Driver      — 统一 API 适配各数据库                     │
│                                                              │
│  vs 装饰器：适配器改接口，装饰器保接口只增强                       │
│  vs 代理：   适配器改接口，代理保接口只控制访问                     │
└──────────────────────────────────────────────────────────────┘
```

适配器模式是面试中"结构型模式"章节的必考内容。建议同学们：

1. **理解三种适配器的实现方式和各自的优劣**，特别是对象适配器为什么是主流。
2. **熟记 Spring 的 HandlerAdapter 原理**，这是源码分析题的高频素材。
3. **能够用口语化的语言描述清楚适配器/装饰器/代理的区别**，这是面试官最常追问的问题。
4. **用生活中的例子理解模式**——就像充电器的转接头、翻译官、插座转换器。

---

**⭐ 重点：适配器模式的核心是"接口转换"，而非"功能增强"。如果你的目标是给类添加新功能，应该考虑装饰器模式或策略模式，而不是适配器模式。**
