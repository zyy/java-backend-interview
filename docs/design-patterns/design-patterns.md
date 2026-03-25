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

### Q1: JDK 中哪些用到了设计模式？

**答：** 
- 工厂模式：Calendar.getInstance()
- 单例模式：Runtime.getRuntime()
- 策略模式：Comparator

---

**⭐ 重点：设计模式体现代码设计能力**