---
layout: default
title: 泛型机制
---
# 泛型机制

> Java 的类型参数化

## 🎯 面试重点

- 泛型的作用和类型参数
- 泛型擦除
- 泛型限定

## 📖 泛型基础

### 什么是泛型？

```java
/**
 * 泛型：参数化类型
 * 
 * 作用：
 * 1. 编译时类型检查
 * 2. 避免强制类型转换
 * 3. 代码复用
 */
public class GenericDemo {
    // 泛型类
    /*
     * class Box<T> {
     *     T value;
     *     public void set(T v) { this.value = v; }
     *     public T get() { return value; }
     * }
     * 
     * Box<String> box = new Box<>();
     * box.set("hello");
     * String s = box.get();  // 无需强转
     */
    
    // 泛型方法
    /*
     * <T> T getFirst(List<T> list) {
     *     return list.get(0);
     * }
     */
}
```

### 泛型限定

```java
/**
 * 泛型限定
 */
public class GenericBound {
    // 上界限定
    /*
     * <T extends Number> T add(T a, T b) { ... }
     * 
     * Integer 继承 Number -> 合法
     * String 不继承 Number -> 不合法
     */
    
    // 下界限定
    /*
     * <? super Integer>
     * 可以接受 Integer 或 Integer 的父类
     */
    
    // 无限定通配符
    /*
     * <?>
     * 可以接受任意类型
     */
}
```

## 📖 泛型擦除

### 类型擦除

```java
/**
 * 泛型擦除
 * 
 * 编译后泛型类型被擦除为 Object 或限定类型
 */
public class TypeErasure {
    // 源码
    /*
     * class Box<T> {
     *     T value;
     * }
     * 
     * 编译后
     * class Box {
     *     Object value;
     * }
     * 
     * Box<String> 编译后：
     * class Box {
     *     Object value;
     * }
     */
    
    // 泛型方法的擦除
    /*
     * <T extends Comparable<T>> T max(T[] arr)
     * 
     * 编译后：
     * Comparable max(Comparable[] arr)
     */
}
```

### 面试真题

```java
/**
 * 面试题：泛型擦除的影响？
 */
public class ErasureQuestion {
    // 问题1：无法使用泛型创建数组
    /*
     * T[] arr = new T[10];  // 编译错误
     * T[] arr = (T[]) new Object[10];  // 可以但不推荐
     */
    
    // 问题2：无法实例化泛型
    /*
     * new T();  // 编译错误
     * 
     * 解决：使用反射或 Class 对象
     */
    
    // 问题3：泛型static方法
    /*
     * static <T> T create() { return new T(); }  // 编译错误
     */
}
```

## 📖 面试真题

### Q1: 泛型的作用？

**答：** 编译时类型检查、避免强转、代码复用。

### Q2: 泛型擦除是什么？

**答：** 编译后泛型类型被替换为 Object 或限定类型，运行时没有泛型信息。

### Q3: 为什么不能创建泛型数组？

**答：** 泛型擦除后无法确定具体类型，编译器无法安全地创建泛型数组。

---

**⭐ 重点：理解泛型擦除是理解 Java 类型系统的关键**