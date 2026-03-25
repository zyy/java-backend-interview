---
layout: default
title: 设计模式
---
# 设计模式

> 创建型、结构型、行为型模式详解

## 🎯 面试重点

- 常用设计模式
- 模式应用场景

## 📖 单例模式

```java
/**
 * 单例模式
 */
public class Singleton {
    // 饿汉式
    /*
     * public class Singleton {
     *     private static final Singleton INSTANCE = new Singleton();
     *     private Singleton() {}
     *     public static Singleton getInstance() {
     *         return INSTANCE;
     *     }
     * }
     */
    
    // 懒汉式（双重检查）
    /*
     * public class Singleton {
     *     private volatile static Singleton instance;
     *     private Singleton() {}
     *     public static Singleton getInstance() {
     *         if (instance == null) {
     *             synchronized (Singleton.class) {
     *                 if (instance == null) {
     *                     instance = new Singleton();
     *                 }
     *             }
     *         }
     *         return instance;
     *     }
     * }
     */
}
```

## 📖 工厂模式

```java
/**
 * 工厂模式
 */
public class FactoryPattern {
    // 简单工厂
    /*
     * public interface Product { void use(); }
     * 
     * public class ProductA implements Product { ... }
     * 
     * public class Factory {
     *     public static Product create(String type) {
     *         if ("A".equals(type)) return new ProductA();
     *         ...
     *     }
     * }
     */
}
```

## 📖 策略模式

```java
/**
 * 策略模式
 */
public class StrategyPattern {
    /*
     * public interface Strategy {
     *     void execute();
     * }
     * 
     * public class Context {
     *     private Strategy strategy;
     *     
     *     public void setStrategy(Strategy s) {
     *         this.strategy = s;
     *     }
     *     
     *     public void execute() {
     *         strategy.execute();
     *     }
     * }
     */
}
```

## 📖 面试真题

### Q1: 单例模式的几种实现方式？线程安全的单例如何实现？

**答：** 单例模式主要有以下几种实现方式：

#### 1. 懒汉式（线程不安全）
```java
public class Singleton {
    private static Singleton instance;
    
    private Singleton() {}
    
    public static Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```

#### 2. 懒汉式（线程安全，synchronized）
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

#### 3. 双重检查锁定（DCL）
```java
public class Singleton {
    private static volatile Singleton instance;
    
    private Singleton() {}
    
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

#### 4. 静态内部类（推荐）
```java
public class Singleton {
    private Singleton() {}
    
    private static class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }
    
    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

#### 5. 枚举（最安全）
```java
public enum Singleton {
    INSTANCE;
    
    public void doSomething() {
        // 业务方法
    }
}
```

**线程安全实现建议**：
- **推荐使用静态内部类或枚举**：线程安全，实现简单。
- **双重检查锁定需要注意**：必须使用 `volatile` 关键字防止指令重排序。
- **避免序列化破坏单例**：实现 `readResolve()` 方法。

### Q2: JDK 中哪些用到了设计模式？

**答：** 
- 工厂模式：`Calendar.getInstance()`、`NumberFormat.getInstance()`
- 单例模式：`Runtime.getRuntime()`、`Desktop.getDesktop()`
- 策略模式：`Comparator`、`ThreadPoolExecutor`（拒绝策略）
- 装饰器模式：`InputStream`/`OutputStream` 系列
- 适配器模式：`Arrays.asList()`、`InputStreamReader`
- 观察者模式：`EventListener`、`PropertyChangeListener`
- 模板方法模式：`AbstractList`、`HttpServlet`

### Q3: 策略模式和代理模式的区别？

**答：** 策略模式和代理模式是两种不同的设计模式，主要区别如下：

| 特性 | 策略模式 | 代理模式 |
|------|---------|---------|
| **目的** | 定义一系列算法，使其可以互相替换 | 为其他对象提供一种代理以控制对这个对象的访问 |
| **关注点** | 算法的选择与替换 | 访问控制、增强功能 |
| **关系** | 策略和上下文是组合关系 | 代理和真实对象是代理关系 |
| **使用时机** | 需要在运行时选择算法 | 需要在访问对象时进行控制或增强 |
| **示例** | 支付方式（微信、支付宝） | 远程代理、虚拟代理、保护代理 |

**策略模式示例**：
```java
// 策略接口
interface PaymentStrategy {
    void pay(int amount);
}

// 具体策略
class WeChatPay implements PaymentStrategy {
    @Override
    public void pay(int amount) {
        System.out.println("微信支付：" + amount);
    }
}

// 上下文
class PaymentContext {
    private PaymentStrategy strategy;
    
    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void executePayment(int amount) {
        strategy.pay(amount);
    }
}
```

**代理模式示例**：
```java
// 接口
interface Image {
    void display();
}

// 真实对象
class RealImage implements Image {
    private String filename;
    
    public RealImage(String filename) {
        this.filename = filename;
        loadFromDisk();
    }
    
    private void loadFromDisk() {
        System.out.println("加载图片：" + filename);
    }
    
    @Override
    public void display() {
        System.out.println("显示图片：" + filename);
    }
}

// 代理
class ProxyImage implements Image {
    private RealImage realImage;
    private String filename;
    
    public ProxyImage(String filename) {
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
```

**总结**：
- 策略模式关注的是**算法的选择**，让算法独立于使用它的客户端。
- 代理模式关注的是**访问控制**，在不改变原始对象的情况下提供额外的功能。

---

**⭐ 重点：设计模式体现代码设计能力**