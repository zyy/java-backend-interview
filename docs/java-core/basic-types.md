---
layout: default
title: Java 基础数据类型与包装类
---
# Java 基础数据类型与包装类

> 理解基本类型和包装类的区别是 Java 基础

## 🎯 面试重点

- 基本类型和包装类的区别
- 自动装箱和拆箱
- 缓存机制

## 📖 基本类型

### 8 种基本类型

```java
/**
 * 8 种基本数据类型
 */
public class BasicTypes {
    // 整数类型
    /*
     * | 类型   | 字节 | 范围                          |
     * |--------|------|------------------------------|
     * | byte   | 1    | -128 ~ 127                   |
     * | short  | 2    | -32768 ~ 32767               |
     * | int    | 4    | -21亿 ~ 21亿                  |
     * | long   | 8    | -9223372036854775808 ~ ...  |
     */
    byte b = 1;
    short s = 1;
    int i = 1;
    long l = 1L;  // 需要加 L
    
    // 浮点类型
    /*
     * | 类型   | 字节 | 精度    |
     * |--------|------|---------|
     * | float  | 4    | 7位     |
     * | double | 8    | 15位    |
     */
    float f = 1.0f;  // 需要加 f
    double d = 1.0;
    
    // 字符类型
    char c = 'a';
    
    // 布尔类型
    boolean flag = true;
}
```

### 包装类

```java
/**
 * 包装类
 */
public class WrapperTypes {
    // 对应关系
    /*
     * byte    -> Byte
     * short   -> Short
     * int     -> Integer
     * long    -> Long
     * float   -> Float
     * double  -> Double
     * char    -> Character
     * boolean -> Boolean
     */
    
    // 装箱和拆箱
    Integer num = 10;  // 自动装箱
    int n = num;       // 自动拆箱
    
    // 手动装箱
    Integer a = Integer.valueOf(10);
    // 手动拆箱
    int b = a.intValue();
}
```

## 📖 区别

### 基本类型 vs 包装类

```java
/**
 * 区别
 */
public class Difference {
    // 1. 默认值
    /*
     * 基本类型：有默认值（int=0, boolean=false）
     * 包装类：默认 null
     */
    
    // 2. 存储方式
    /*
     * 基本类型：栈中存储值
     * 包装类：堆中存储对象
     */
    
    // 3. 泛型支持
    /*
     * 基本类型：不能用于泛型
     * 包装类：可以用于泛型
     * List<int> 错误
     * List<Integer> 正确
     */
    
    // 4. 方法调用
    /*
     * 基本类型：不能调用方法
     * 包装类：可以调用方法
     */
    Integer num = 10;
    System.out.println(num.intValue());  // 10
    System.out.println(num.toString());   // "10"
}
```

### 缓存机制

```java
/**
 * 包装类的缓存
 */
public class CacheDemo {
    // Integer 缓存 -128 ~ 127
    /*
     * Integer a = 127;
     * Integer b = 127;
     * System.out.println(a == b);  // true（缓存）
     * 
     * Integer c = 128;
     * Integer d = 128;
     * System.out.println(c == d);  // false（不缓存）
     * 
     * valueOf() 使用缓存
     * new Integer() 不使用缓存
     */
    
    // Byte, Short, Integer, Long, Character 有缓存
    // Float, Double 没有缓存
}
```

## 📖 面试真题

### Q1: 基本类型和包装类的区别？

**答：** 
- 基本类型存储在栈中，包装类存储在堆中
- 包装类有默认值 null，基本类型有默认值
- 包装类可以用于泛型，基本类型不可以

### Q2: Integer 的缓存范围？

**答：** -128 到 127

### Q3: new Integer(10) 和 Integer.valueOf(10) 的区别？

**答：** valueOf 使用缓存，new Integer 每次创建新对象。

---

**⭐ 重点：理解基本类型和包装类的区别是理解 Java 的基础**