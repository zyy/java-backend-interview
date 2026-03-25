---
layout: default
title: 打破双亲委派
---
# 打破双亲委派

> 特殊场景下的类加载策略

## 🎯 面试重点

- 何时需要打破双亲委派
- 常见的打破方式
- Tomcat 的类加载器架构

## 📖 打破场景

### Tomcat 类加载器架构

```java
/**
 * Tomcat 类加载器架构（经典版本）
 * 
 * Bootstrap ClassLoader
 *         ↑
 *    System ClassLoader
 *         ↑
 *    Common ClassLoader
 *         ↑
 *  ┌────┴────┬────┐
 *  ↓         ↓    ↓
 * WebApp1  WebApp2  WebApp3  ← 每个 Web 应用独立类加载器
 * 
 * 特点：
 * 1. 每个 Web 应用有自己的 WebAppClassLoader
 * 2. WebAppClassLoader 先尝试自己加载，不成功再委托
 * 3. 不同 Web 应用可以加载同名的不同类
 */
public class TomcatClassLoader {}
```

### Tomcat 加载流程

```java
/**
 * Tomcat 类加载器工作流程
 * 
 * 加载类时查找顺序：
 * 1. Bootstrap ClassLoader
 * 2. System ClassLoader
 * 3. Common ClassLoader
 * 4. WebAppClassLoader (先自己的 WebAPP_HOME/lib)
 * 5. WebAppClassLoader (委托给父类)
 */
public class TomcatLoadOrder {
    // Tomcat 7 及之前：先子后父
    /*
     * WebAppClassLoader.loadClass()
     *     ↓ 先查询缓存
     *     ↓ 未找到则尝试自己加载
     *     ↓ 加载失败才委托父类
     * 
     * 这打破了双亲委派！
     */
    
    // Tomcat 8+：双向委派
    /*
     * 增加了逆向委派：
     * - 先按双亲委派
     * - 失败后再尝试 WebAppClassLoader
     * 
     * 更灵活地支持类的覆盖
     */
}
```

### JDBC 驱动加载

```java
/**
 * JDBC 打破双亲委派
 * 
 * 问题：
 * 1. java.sql.DriverManager 在 rt.jar 中，由 Bootstrap 加载
 * 2. 厂商驱动如 com.mysql.cj.jdbc.Driver 在 classpath 中
 * 3. Bootstrap 无法加载 classpath 中的类
 * 
 * 解决：线程上下文类加载器
 */
public class JDBCBreak {
    // DriverManager 初始化时
    /*
     * static {
     *     // 获取线程上下文类加载器
     *     ClassLoader cl = Thread.currentThread().getContextClassLoader();
     *     if (cl == null) {
     *         cl = DriverManager.class.getClassLoader();
     *     }
     *     
     *     // 加载驱动
     *     ServiceLoader<Driver> loadedDrivers = ServiceLoader.load(Driver.class, cl);
     * }
     */
    
    // 关键代码
    // Thread.currentThread().setContextClassLoader(appClassLoader);
    // ServiceLoader.load(Driver.class) 会使用上下文类加载器
}
```

### SPI 机制

```java
/**
 * SPI (Service Provider Interface)
 * 
 * Java SPI 使用场景：
 * - JDBC 驱动
 * - SLF4J 日志
 * - JSON 解析（Jackson/Gson）
 * - 文件系统（Java NIO）
 */
public class SPIMechanism {
    // SPI 使用流程
    /*
     * 1. 定义接口（在核心库中）
     *    package java.sql;
     *    public interface Driver {}
     * 
     * 2. 在厂商 jar 包中创建实现
     *    META-INF/services/java.sql.Driver
     *    内容：com.mysql.cj.jdbc.Driver
     * 
     * 3. 应用使用 ServiceLoader 加载
     *    ServiceLoader<Driver> loader = ServiceLoader.load(Driver.class);
     *    for (Driver driver : loader) {
     *        driver.connect(...);
     *    }
     */
    
    // SPI 问题
    /*
     * ServiceLoader 使用当前线程的上下文类加载器
     * 如果没有设置，会使用当前类的类加载器（通常是 AppClassLoader）
     * 这会导致加载到厂商的 Driver 实现类
     */
}
```

## 📖 打破方式

### 重写 loadClass

```java
/**
 * 方式1：重写 loadClass()
 * 
 * 不推荐：完全破坏双亲委派
 */
public class BreakByLoadClass {
    static class MyClassLoader extends ClassLoader {
        @Override
        public Class<?> loadClass(String name) throws ClassNotFoundException {
            // 完全自己加载，不委托
            if (name.startsWith("com.myapp.")) {
                return findClass(name);
            }
            // 其他类正常加载
            return super.loadClass(name);
        }
        
        @Override
        protected Class<?> findClass(String name) throws ClassNotFoundException {
            // 读取 .class 文件并定义类
            String path = "path/to/" + name.replace('.', '/') + ".class";
            byte[] bytes = Files.readAllBytes(Paths.get(path));
            return defineClass(name, bytes, 0, bytes.length);
        }
    }
}
```

### 线程上下文类加载器

```java
/**
 * 方式2：线程上下文类加载器
 * 
 * 推荐：部分打破，保留大部分委派逻辑
 */
public class BreakByContextLoader {
    // 设置线程上下文类加载器
    public static void main(String[] args) {
        // 获取当前线程的上下文类加载器
        ClassLoader original = Thread.currentThread().getContextClassLoader();
        
        try {
            // 设置新的上下文类加载器
            ClassLoader myLoader = new MyClassLoader();
            Thread.currentThread().setContextClassLoader(myLoader);
            
            // 后续的 SPI 调用会使用新的类加载器
            // 例如：ServiceLoader.load(Driver.class)
            
        } finally {
            // 恢复原始类加载器
            Thread.currentThread().setContextClassLoader(original);
        }
    }
}
```

### 自定义类加载器组合

```java
/**
 * 方式3：组合方式
 * 
 * 例如 OSGi 的模块化类加载
 */
public class CombinationLoader {
    // 模拟 OSGi 类加载器
    /*
     * Bundle A 导出 com.example.service
     * Bundle B 导入 com.example.service
     * 
     * Bundle B 的类加载器需要：
     * 1. 首先尝试从自己的 bundle 中加载
     * 2. 然后从依赖的 bundle 中加载
     * 3. 最后从父加载器加载
     * 
     * 这是混合委派模式
     */
}
```

## 📖 面试真题

### Q1: Tomcat 为什么打破双亲委派？

**答：** 
1. 每个 Web 应用需要隔离，不能加载其他应用的类
2. Web 应用可能需要加载同名但不同版本的类
3. Web 应用可能需要覆盖 JDK 的类

### Q2: 如何实现热部署？

**答：** 
1. 自定义类加载器，每次加载重新读取 .class 文件
2. 不使用双亲委派，直接使用自己的类加载器
3. 卸载旧类：让旧的类加载器变为不可达，触发 GC

### Q3: 类加载器的隔离方案？

**答：** 
1. 不同的类加载器加载的类视为不同的类
2. 即使类名相同，只要类加载器不同，就是不同的类
3. 类的全限定名 = 类名 + 类加载器实例 ID

---

**⭐ 重点：理解打破双亲委派的场景和方式，对于理解模块化系统非常重要**