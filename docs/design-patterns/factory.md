# 工厂模式

> 对象创建的封装

## 🎯 面试重点

- 简单工厂 vs 工厂方法
- 抽象工厂

## 📖 实现

### 简单工厂

```java
/**
 * 简单工厂
 */
public class SimpleFactory {
    public interface Product { void use(); }
    public static class ProductA implements Product { public void use() {} }
    public static class ProductB implements Product { public void use() {} }
    
    public static Product create(String type) {
        switch (type) {
            case "A": return new ProductA();
            case "B": return new ProductB();
            default: throw new IllegalArgumentException();
        }
    }
}
```

### 工厂方法

```java
/**
 * 工厂方法
 */
public class FactoryMethod {
    public interface Factory { Product create(); }
    
    public static class FactoryA implements Factory {
        public Product create() { return new ProductA(); }
    }
}
```

## 📖 面试真题

### Q1: 工厂模式的优点？

**答：** 解耦、扩展方便、符合开闭原则。

---

**⭐ 重点：工厂模式是创建型模式的基础**