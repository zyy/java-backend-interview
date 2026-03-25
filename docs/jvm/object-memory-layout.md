# 对象内存布局

> 了解对象在内存中的存储结构

## 🎯 面试重点

- 对象由哪几部分组成
- 对象头包含什么
- 内存对齐的作用

## 📖 对象内存布局

### 对象结构

```java
/**
 * Java 对象在内存中的布局：
 * 
 * ┌─────────────────────────────────────┐
 * │           对象头（Header）           │
 * │  ┌───────────────────────────────┐  │
 * │  │      Mark Word（标记字段）     │  │  8字节 (64位)
 * │  │  (hashcode, age, lock, etc)    │  │
 * │  ├───────────────────────────────┤  │
 * │  │      Klass Pointer（类指针）   │  │  4/8字节
 * │  │  (指向类元数据的指针)          │  │
 * │  ├───────────────────────────────┤  │
 * │  │   数组长度（仅数组对象有）     │  │  4字节
 * │  └───────────────────────────────┘  │
 * ├─────────────────────────────────────┤
 * │         实例数据（Instance Data）    │
 * │   父类字段 + 自身字段                │
 * ├─────────────────────────────────────┤
 * │          对齐填充（Padding）         │
 * └─────────────────────────────────────┘
 */
public class ObjectLayout {}
```

### 对象头详解

```java
/**
 * Mark Word（标记字段）
 * 64位 JVM 下占 8 字节，存储对象自身运行时数据：
 */
public class MarkWordDemo {
    /*
     * 对象未锁定状态：
     * 25bit hashcode + 2bit age + 1bit lock(01) + 4bit unused = 64bit
     *
     *轻量级锁定状态：
     * 62bit pointer to lock record + 2bit lock(00) = 64bit
     *
     *重量级锁定状态：
     * 62bit pointer to monitor + 2bit lock(10) = 64bit
     *
     *GC 标记状态：
     * 62bit unused + 2bit lock(11) = 64bit
     */
}

/**
 * Klass Pointer（类指针）
 * - 指向方法区中类元数据的指针
 * - 通过这个指针确定对象是哪个类的实例
 * - 开启了指针压缩（-XX:+UseCompressedClassPointers）时为 4 字节，否则 8 字节
 */
public class KlassPointerDemo {
    // Class 对象在堆中，类元数据在方法区
    // Object obj = new Object();
    // obj.getClass() 通过 Klass Pointer 找到 Class 对象
}
```

### 实例数据

```java
/**
 * 实例数据存放规则：
 * 1. 父类变量排在子类之前
 * 2. 相同宽度的字段放在一起
 * 3. 成员变量按照声明顺序排放
 */
public class InstanceData {
    // 示例
    class Parent {
        long l;     // 8字节
        int i;      // 4字节
    }
    
    class Child extends Parent {
        String s;   // 4/8字节（引用）
        int j;      // 4字节
        double d;   // 8字节
        byte b;     // 1字节
    }
    
    // 实际顺序（考虑对齐）：
    // l (8) + i (4) + 空白(4) = 16
    // s (4/8) + j (4) + d (8) + b (1) + 空白(7) = 32/40
}
```

### 对齐填充

```java
/**
 * 对齐填充（Padding）
 * 
 * 原因：CPU 访问内存时以字（word）为单位
 *      不是对齐的数据可能需要多次访问
 * 
 * 规则：对象大小必须是 8 字节的整数倍
 *      不够则填充
 */
public class PaddingDemo {
    // 示例
    /*
     * class A {
     *     byte b;    // 1字节
     * }
     * 
     * 实际占用：1 + 7(填充) = 8字节
     * 
     * class B {
     *     long l;    // 8字节
     *     byte b;    // 1字节
     * }
     * 
     * 实际占用：8 + 1 + 7(填充) = 16字节
     */
}
```

### 验证方法

```java
/**
 * 使用 JOL (Java Object Layout) 验证
 */
public class JOLTest {
    // 添加依赖
    // <dependency>
    //     <groupId>org.openjdk.jol</groupId>
    //     <artifactId>jol-core</artifactId>
    //     <version>0.17</version>
    // </dependency>
    
    public static void main(String[] args) {
        // 查看对象布局
        System.out.println(ClassLayout.parseInstance(new Object()).toPrintable());
        
        // 查看数组布局
        System.out.println(ClassLayout.parseInstance(new int[0]).toPrintable());
        
        // 查看带锁对象布局
        synchronized (new Object()) {
            System.out.println(ClassLayout.parseInstance(new Object()).toPrintable());
        }
    }
}
```

## 📖 面试真题

### Q1: new Object() 占多少字节？

**答：**
- 不开启压缩：8(Mark Word) + 8(Klass) + 0(实例数据) + 8(对齐) = **24字节**
- 开启压缩：8(Mark Word) + 4(Klass) + 0(实例数据) + 4(对齐) = **16字节**

### Q2: new Object[10] 占多少字节？

**答：**
- 数组对象多 4 字节存储数组长度
- 开启压缩：8 + 4 + 4(数组长度) + 40(10个引用) + 4(对齐) = **60字节** ≈ **64字节**

### Q3: 对象头中的锁状态？

**答：**
- 无锁：00/01
- 偏向锁：101
- 轻量级锁：00
- 重量级锁：10
- GC 标记：11

---

**⭐ 重点：对象内存布局是理解 JVM 的基础，面试中经常结合 OOM 问题考察**