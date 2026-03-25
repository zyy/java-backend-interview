---
layout: default
title: JVM 运行时数据区
---
# JVM 运行时数据区

> 理解 JVM 内存划分是排查内存问题的基础

## 🎯 面试重点

- 各内存区域的作用和特点
- 哪些区域是线程私有的，哪些是共享的
- OOM 可能发生在哪些区域

## 📖 详细解析

### 1. 线程私有区域

#### 程序计数器（Program Counter Register）

```java
/**
 * 作用：记录当前线程执行的字节码行号
 * 特点：
 * - 线程私有，每个线程独立拥有
 * - 执行 Java 方法时记录字节码地址
 * - 执行 Native 方法时为空（Undefined）
 * - 唯一不会发生 OutOfMemoryError 的区域
 */
public class PCRExample {
    public static void main(String[] args) {
        // PCR 中保存的是下一条要执行的指令地址
        int a = 1;  // 字节码指令地址 0
        int b = 2;  // 字节码指令地址 3
        int c = a + b;  // 字节码指令地址 6
    }
}
```

#### 虚拟机栈（VM Stack）

```java
/**
 * 作用：存储局部变量表、操作数栈、动态链接、方法返回地址
 * 特点：
 * - 线程私有
 * - 栈深度过深导致 StackOverflowError
 * - 动态扩展失败导致 OutOfMemoryError
 *
 * -Xss 参数设置栈大小（默认 1MB）
 */
public class StackExample {
    // 局部变量表：存储方法参数和局部变量
    public int method(int param) {
        int localVar = param + 1;  // 局部变量
        return localVar;
    }
    
    // 递归调用可能导致栈溢出
    public int factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);  // 递归调用
    }
}
```

**栈帧结构：**
```
┌─────────────────────────┐
│      局部变量表          │  ⭐ 存储局部变量和参数
├─────────────────────────┤
│      操作数栈            │  ⭐ 计算过程的临时存储
├─────────────────────────┤
│      动态链接            │  ⭐ 指向运行时常量池的引用
├─────────────────────────┤
│   方法返回地址            │  ⭐ 方法退出后继续执行的位置
└─────────────────────────┘
```

#### 本地方法栈（Native Method Stack）

- 与虚拟机栈类似，但为 Native 方法服务
- HotSpot 将两者合二为一
- 同样会抛出 StackOverflowError 和 OutOfMemoryError

### 2. 线程共享区域

#### 堆（Heap）

```java
/**
 * 作用：存储对象实例和数组
 * 特点：
 * - 线程共享
 * - GC 管理的主要区域
 * - 可分为新生代和老年代
 * - -Xmx 和 -Xms 设置大小
 *
 * OOM 常见发生区域
 */
public class HeapExample {
    public static void main(String[] args) {
        // 对象分配在堆上
        Object obj = new Object();
        int[] array = new int[1024];
        
        // 无限创建对象导致 OOM
        List<byte[]> list = new ArrayList<>();
        while (true) {
            list.add(new byte[1024 * 1024]);  // 每次分配 1MB
        }
    }
}
```

**堆内存结构：**
```
┌─────────────────────────────────────────┐
│                  堆内存                   │
│  ┌─────────────┬───────────────────────┐│
│  │   Eden 区   │    S0    │    S1     ││  ← 新生代 (1/3)
│  │  (8/10)     │  (1/10)  │  (1/10)   ││
│  ├─────────────┴───────────────────────┤│
│  │              老年代                  ││  ← 老年代 (2/3)
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

#### 方法区（Method Area）

```java
/**
 * 作用：存储类信息（类的元数据）、常量、静态变量、JIT 编译后的代码
 * 特点：
 * - 线程共享
 * - HotSpot 7 之前用永久代实现，8 之后用元空间（Metaspace）
 * - 元空间使用本地内存，不受 -XX:MaxPermSize 限制
 *
 * 存储内容：
 * - 类的元数据（类名、访问修饰符、字段信息、方法信息等）
 * - 常量池（字面量和符号引用）
 * - JIT 编译后的代码
 * - 静态变量（注意：JDK 8 后静态变量移到堆中）
 */
public class MethodAreaExample {
    // 静态变量 JDK 8 后移到堆中
    public static Map<String, String> cache = new ConcurrentHashMap<>();
    
    // 常量存储在运行时常量池
    public static final String CONSTANT = "Hello";
    
    // 类信息、方法信息都存储在方法区
    public void doSomething() {
        // 方法编译后的字节码存储在方法区
    }
}
```

### 3. 直接内存（Direct Memory）

```java
/**
 * 作用：通过 NIO 分配的堆外内存
 * 特点：
 * - 不受堆大小限制
 * - 申请成本高，但读写性能好
 * - 可能导致 OutOfMemoryError
 * - -XX:MaxDirectMemorySize 设置
 *
 * NIO 中的使用：
 * - ByteBuffer.allocateDirect() 分配直接内存
 * - 减少 JVM 和本地内存之间的数据复制
 */
public class DirectMemoryExample {
    public static void main(String[] args) {
        // 分配 1GB 直接内存
        ByteBuffer buffer = ByteBuffer.allocateDirect(1024 * 1024 * 1024);
    }
}
```

## 📊 总结对比

| 区域 | 线程私有 | 作用 | 异常类型 |
|------|---------|------|---------|
| 程序计数器 | ✅ | 记录字节码行号 | 无 |
| 虚拟机栈 | ✅ | 方法执行、局部变量 | StackOverflowError / OOM |
| 本地方法栈 | ✅ | Native 方法执行 | StackOverflowError / OOM |
| 堆 | ❌ | 对象实例存储 | OOM |
| 方法区 | ❌ | 类信息、常量、代码 | OOM（MetaspaceOOM） |
| 直接内存 | ❌ | NIO 堆外内存 | OOM |

## 💡 面试真题

### Q1: 什么是运行时常量池？

**答：** 运行时常量池是方法区的一部分，用于存储编译期生成的字面量和符号引用。运行时可以将新的常量放入池中（如 String.intern()）。

### Q2: String.intern() 方法的作用？

**答：** 当调用 intern() 方法时，如果字符串常量池中已包含该字符串，则返回池中的引用；否则将字符串添加到常量池并返回引用。可以用来节省内存。

### Q3: 对象创建的过程？

**答：**
1. 检查类是否已加载、初始化
2. 分配内存（指针碰撞/空闲列表）
3. 初始化零值
4. 设置对象头
5. 执行 `<init>` 构造函数

---

**⭐ 重点：堆是内存分配的重点区域，面试必问垃圾回收和内存分配策略**
