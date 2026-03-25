---
layout: default
title: String、StringBuilder、StringBuffer 区别 ⭐⭐
---
# String、StringBuilder、StringBuffer 区别 ⭐⭐

## 面试题：String、StringBuilder、StringBuffer 有什么区别？

### 核心回答

三者都是 Java 中用于处理字符串的类，核心区别在于**可变性**和**线程安全性**。

### 对比总览

| 特性 | String | StringBuilder | StringBuffer |
|------|--------|---------------|--------------|
| **可变性** | 不可变 | 可变 | 可变 |
| **线程安全** | 安全（不可变） | 不安全 | 安全（synchronized） |
| **性能** | 低（每次修改创建新对象） | 高（单线程） | 中（多线程有锁开销） |
| **使用场景** | 字符串常量 | 单线程字符串操作 | 多线程字符串操作 |
| **JDK版本** | 1.0 | 1.5 | 1.0 |

### String - 不可变字符串

#### 不可变性的实现

```java
public final class String implements java.io.Serializable, Comparable<String>, CharSequence {
    // 字符数组被 final 修饰
    private final char value[];
    
    // 没有提供修改 value 数组的方法
}
```

**不可变原因**：
1. `final class`：类不能被继承，防止方法被重写
2. `final char[] value`：字符数组引用不可变
3. 无修改方法：String 类没有提供修改字符数组内容的方法

#### 字符串常量池

```java
// 方式1：直接赋值（推荐）
String s1 = "hello";  // 从常量池获取，可能复用已有对象

// 方式2：new 创建
String s2 = new String("hello");  // 堆中创建新对象

// 验证
System.out.println(s1 == s2);      // false
System.out.println(s1.equals(s2)); // true
```

**intern() 方法**：
```java
String s3 = new String("hello").intern();  // 将字符串放入常量池
System.out.println(s1 == s3);  // true
```

#### 字符串拼接的问题

```java
// 错误做法：循环中使用 String 拼接
String sql = "";
for (int i = 0; i < 10000; i++) {
    sql += "value" + i + ",";  // 每次循环创建新对象，GC压力大
}

// 正确做法：使用 StringBuilder
StringBuilder sb = new StringBuilder(100000);
for (int i = 0; i < 10000; i++) {
    sb.append("value").append(i).append(",");
}
```

### StringBuilder - 可变字符串（单线程）

#### 特点

- **可变**：底层使用可扩容的字符数组
- **非线程安全**：方法没有 synchronized 修饰
- **高性能**：单线程下无锁开销

#### 源码分析

```java
public final class StringBuilder extends AbstractStringBuilder 
    implements java.io.Serializable, CharSequence {
    
    // 继承 AbstractStringBuilder 的可变数组
    // char[] value;  // 非 final，可扩容
    
    public StringBuilder append(String str) {
        super.append(str);  // 调用父类方法，无同步
        return this;
    }
}
```

#### 扩容机制

```java
// 默认初始容量 16
public StringBuilder() {
    super(16);
}

// 扩容：原长度 * 2 + 2
void expandCapacity(int minimumCapacity) {
    int newCapacity = (value.length << 1) + 2;
    if (newCapacity - minimumCapacity < 0)
        newCapacity = minimumCapacity;
    value = Arrays.copyOf(value, newCapacity);
}
```

**优化建议**：预估字符串长度，避免频繁扩容
```java
// 预估容量，减少扩容次数
StringBuilder sb = new StringBuilder(1000);
```

### StringBuffer - 可变字符串（多线程）

#### 特点

- **可变**：与 StringBuilder 相同的底层结构
- **线程安全**：方法使用 `synchronized` 修饰
- **性能较低**：同步带来额外开销

#### 源码分析

```java
public final class StringBuffer extends AbstractStringBuilder 
    implements java.io.Serializable, CharSequence {
    
    public synchronized StringBuffer append(String str) {
        super.append(str);  // 同步方法
        return this;
    }
}
```

### 继承关系

```
Object
  └── AbstractStringBuilder（抽象类，定义可变字符串操作）
        ├── StringBuilder（非线程安全）
        └── StringBuffer（线程安全）

String 独立继承体系：
Object
  └── String（final 类，不可变）
```

### 性能对比测试

```java
public class StringPerformanceTest {
    public static void main(String[] args) {
        int count = 100000;
        
        // String 拼接
        long start1 = System.currentTimeMillis();
        String s = "";
        for (int i = 0; i < count; i++) {
            s += i;  // 极慢，每次创建新对象
        }
        System.out.println("String: " + (System.currentTimeMillis() - start1) + "ms");
        
        // StringBuilder
        long start2 = System.currentTimeMillis();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < count; i++) {
            sb.append(i);
        }
        System.out.println("StringBuilder: " + (System.currentTimeMillis() - start2) + "ms");
        
        // StringBuffer
        long start3 = System.currentTimeMillis();
        StringBuffer sbf = new StringBuffer();
        for (int i = 0; i < count; i++) {
            sbf.append(i);
        }
        System.out.println("StringBuffer: " + (System.currentTimeMillis() - start3) + "ms");
    }
}
```

**典型结果**：
```
String: 8000+ ms
StringBuilder: 10 ms
StringBuffer: 15 ms
```

### 使用场景总结

| 场景 | 推荐类 |
|------|--------|
| 字符串常量，不修改 | String |
| 单线程，频繁修改字符串 | StringBuilder |
| 多线程，频繁修改字符串 | StringBuffer |
| 循环中拼接字符串 | StringBuilder |
| SQL 语句拼接 | StringBuilder |
| JSON/XML 字符串构建 | StringBuilder |

### 高频面试题

**Q1: 为什么 String 要设计成不可变的？**
1. **安全性**：字符串常用作参数（如网络连接、文件路径），不可变可防止被篡改
2. **线程安全**：不可变对象天然线程安全，无需同步
3. **哈希缓存**：String 的 hashCode 可缓存，适合作为 HashMap 的 key
4. **字符串常量池**：不可变才能实现常量池复用，节省内存

**Q2: StringBuilder 和 StringBuffer 的扩容机制？**
- 默认初始容量 16
- 扩容时：新容量 = 旧容量 × 2 + 2
- 如果还不够，使用所需的最小容量

**Q3: 如何在多线程环境下安全使用 StringBuilder？**
```java
// 方案1：使用 ThreadLocal
private static final ThreadLocal<StringBuilder> TL = 
    ThreadLocal.withInitial(() -> new StringBuilder(100));

// 方案2：使用 synchronized 块
synchronized (sb) {
    sb.append("data");
}

// 方案3：每个线程创建新的 StringBuilder（推荐）
```

**Q4: JDK 对字符串拼接的优化？**
```java
// 编译前
String s = "a" + "b" + "c";

// 编译后（常量折叠）
String s = "abc";

// 编译前
String s = str1 + str2 + str3;

// 编译后（JDK 8+ 自动优化为 StringBuilder）
String s = new StringBuilder().append(str1).append(str2).append(str3).toString();
```

### 最佳实践

1. **优先使用 StringBuilder**：单线程环境下性能最优
2. **预估容量**：减少扩容带来的数组拷贝开销
3. **避免在循环中使用 String 拼接**：编译器优化有限，大循环仍会创建大量对象
4. **多线程考虑 ThreadLocal**：比 StringBuffer 性能更好

---

**参考链接：**
- [String、StringBuffer和StringBuilder的区别-CSDN](https://blog.csdn.net/lklalmq/article/details/144623349)
- [Java中String、StringBuffer和StringBuilder的区别-面试鸭](http://www.mianshiya.com/question/1780933294519513089)
