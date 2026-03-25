# 双亲委派模型

> Java 类加载的核心机制

## 🎯 面试重点

- 双亲委派的工作流程
- 为什么要使用双亲委派
- 如何打破双亲委派

## 📖 工作原理

### 委派流程

```java
/**
 * 双亲委派流程：
 * 
 * 1. 类加载器收到加载请求
 * 2. 将请求委托给父类加载器处理
 * 3. 父类再委托其父类...
 * 4. 到达 Bootstrap ClassLoader
 * 5. Bootstrap 无法处理时，子加载器尝试自己加载
 */
public class ParentDelegation {
    // 示例：当加载 java.lang.String 时
    /*
     * Bootstrap ← Ext ← App ← 自定义
     *              ↓
     *         Bootstrap 加载成功
     *         返回 String.class
     * 
     * 流程图：
     *     ClassLoader A
     *          ↓
     *     ClassLoader B (parent)
     *          ↓
     *     ClassLoader C (parent)
     *          ↓
     *   Bootstrap ClassLoader
     */
}
```

### 源码解析

```java
/**
 * loadClass() 方法源码分析
 */
public class LoadClassSource {
    // ClassLoader.loadClass() 核心逻辑
    /*
     * protected Class<?> loadClass(String name, boolean resolve)
     *     throws ClassNotFoundException {
     * 
     *     // 1. 检查是否已加载
     *     Class<?> c = findLoadedClass(name);
     *     if (c != null) {
     *         return c;
     *     }
     * 
     *     // 2. 委托给父类加载
     *     try {
     *         return parent.loadClass(name, false);
     *     } catch (ClassNotFoundException e) {
     *         // 3. 父类无法加载，自己尝试
     *         return findClass(name);
     *     }
     * }
     */
}
```

## 📖 为什么需要双亲委派

### 优点

```java
/**
 * 双亲委派的优点：
 * 
 * 1. 避免类的重复加载
 *    - 父类已加载，子类不需要重复加载
 *    - 保证类的唯一性
 * 
 * 2. 保证类的安全性
 *    - 核心类无法被篡改
 *    - 如 java.lang.String 只能由 Bootstrap 加载
 *    - 防止用户自定义 java.lang.String
 */
public class Benefits {
    // 示例：防止篡改核心类
    /*
     * 用户编写：
     * package java.lang;
     * public class String {
     *     public static void main(String[] args) {
     *         System.out.println(" malicious");
     *     }
     * }
     * 
     * 加载过程：
     * - AppClassLoader 收到请求
     * - 委托给 ExtClassLoader
     * - 委托给 Bootstrap
     * - Bootstrap 找到 java/lang/String.class (rt.jar)
     * - 返回 Bootstrap 加载的 String
     * 
     * 结果：用户自定义的 String 不会被加载
     */
}
```

### 类加载器层级

```java
/**
 * 类加载器层级：
 */
public class ClassLoaderLevels {
    // Bootstrap ClassLoader (启动类加载器)
    /*
     * - C++ 实现，无法在 Java 代码中获取
     * - 负责加载 JAVA_HOME/lib 下的核心类库
     * - 如 java.lang.String, java.util.List
     */
    
    // Extension ClassLoader (扩展类加载器)
    /*
     * - Java 实现：sun.misc.Launcher$ExtClassLoader
     * - 负责加载 JAVA_HOME/lib/ext 下的类
     * - 负责加载 -Djava.ext.dirs 指定目录下的类
     */
    
    // Application ClassLoader (应用类加载器)
    /*
     * - Java 实现：sun.misc.Launcher$AppClassLoader
     * - 负责加载 classpath 下的类
     * - 负责加载 -cp 或 -classpath 指定目录下的类
     */
    
    // 自定义 ClassLoader
    /*
     * - 用户自定义的类加载器
     * - 继承 ClassLoader
     * - 可以打破双亲委派
     */
    
    // 验证层级
    public static void main(String[] args) {
        // 输出各级加载器
        System.out.println("String: " + String.class.getClassLoader());  // null
        System.out.println("App: " + ParentDelegation.class.getClassLoader());  // AppClassLoader
    }
}
```

## 📖 打破双亲委派

### 场景

```java
/**
 * 需要打破双亲委派的场景：
 * 
 * 1. Tomcat：每个 Web 应用有独立的类加载器
 *    - 隔离不同应用之间的类
 *    - 加载相同类名的不同类
 * 
 * 2. JDBC：使用线程上下文类加载器
 *    - 驱动由不同厂商实现
 *    - 需要打破双亲委派来加载
 * 
 * 3. OSGi：模块化加载
 * 
 * 4. 热部署：运行时更新类
 */
public class BreakScenarios {}
```

### 打破方式

```java
/**
 * 打破双亲委派的方式：
 */
public class BreakMethods {
    // 方式1：重写 loadClass()
    /*
     * 不推荐：破坏双亲委派机制
     */
    static class MyClassLoader1 extends ClassLoader {
        @Override
        public Class<?> loadClass(String name) throws ClassNotFoundException {
            // 不委托，直接自己加载
            if (name.startsWith("com.myapp.")) {
                return findClass(name);
            }
            return super.loadClass(name);
        }
    }
    
    // 方式2：使用线程上下文类加载器
    /*
     * 原理：设置线程的上下文类加载器
     * 应用场景：JDBC、SPI
     */
    static class MyClassLoader2 {
        public static void main(String[] args) {
            // 获取当前线程的上下文类加载器
            ClassLoader contextLoader = Thread.currentThread().getContextClassLoader();
            
            // 设置新的上下文类加载器
            Thread.currentThread().setContextClassLoader(new MyClassLoader1());
            
            // 后续使用 SPI 时，会使用这个上下文类加载器
        }
    }
    
    // 方式3：Tomcat 的 WebAppClassLoader
    /*
     * 先尝试自己加载，加载失败再委托父类
     * 实现了不同 Web 应用之间的隔离
     */
}
```

## 📖 SPI 与双亲委派

```java
/**
 * SPI (Service Provider Interface)
 * 
 * Java SPI 机制：
 * 1. 在 META-INF/services 下创建配置文件
 * 2. 配置文件名 = 接口全限定名
 * 3. 文件内容 = 实现类全限定名
 * 
 * JDBC 例子：
 */
public class SPIDemo {
    // JDBC 驱动加载
    /*
     * ServiceLoader<Driver> loader = ServiceLoader.load(Driver.class);
     * 
     * 问题：Driver 接口在 java.sql 中，由 Bootstrap 加载
     *      MySQL 驱动由厂商实现，在 classpath 中
     *      Bootstrap 无法加载厂商的 Driver 实现类
     * 
     * 解决：使用线程上下文类加载器
     *      - DriverManager 初始化时获取当前线程的上下文类加载器
     *      - 使用这个加载器来加载驱动类
     */
    
    // JDK 8 及之前的写法
    // Class.forName("com.mysql.cj.jdbc.Driver")
    
    // JDK 9+ 的写法
    // ServiceLoader 机制自动加载
}
```

## 📖 面试真题

### Q1: 双亲委派模型的好处？

**答：** 
1. 避免类的重复加载：父加载器已加载，子加载器不再加载
2. 保护核心类安全：防止用户自定义同名类替换 JDK 类

### Q2: 如何自定义类加载器？

**答：** 
1. 继承 ClassLoader 类
2. 重写 findClass() 方法（推荐）
3. 或重写 loadClass() 方法（打破双亲委派）
4. 读取 .class 文件，调用 defineClass() 定义类

### Q3: 为什么 JDBC 需要打破双亲委派？

**答：** 
JDBC 接口在 java.sql 包中，由 Bootstrap 加载。MySQL 等驱动在 classpath 中，由 AppClassLoader 加载。如果不打破双亲委派，AppClassLoader 无法加载实现类。通过设置线程上下文类加载器解决。

---

**⭐ 重点：理解双亲委派是理解 Java 模块系统的基础，也是面试常考点**