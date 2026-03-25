---
layout: default
title: 代理模式
---
# 代理模式

> 对象的代理访问

## 🎯 面试重点

- 静态代理 vs 动态代理
- JDK 动态代理 vs CGLIB

## 📖 实现

### 静态代理

```java
/**
 * 静态代理
 */
public class StaticProxy {
    public interface Subject { void request(); }
    
    public static class RealSubject implements Subject {
        public void request() { System.out.println("real"); }
    }
    
    public static class Proxy implements Subject {
        private Subject real;
        public Proxy(Subject real) { this.real = real; }
        public void request() {
            System.out.println("before");
            real.request();
            System.out.println("after");
        }
    }
}
```

### JDK 动态代理

```java
/**
 * JDK 动态代理
 */
public class JdkProxy {
    public static Object newProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                System.out.println("before");
                Object result = method.invoke(target, args);
                System.out.println("after");
                return result;
            }
        );
    }
}
```

## 📖 面试真题

### Q1: JDK 动态代理和 CGLIB 区别？

**答：** JDK 基于接口，CGLIB 基于继承。

---

**⭐ 重点：Spring AOP 使用代理模式**