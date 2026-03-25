# 类加载机制

> 理解类的生命周期和加载过程

## 🎯 面试重点

- 类加载的各个阶段
- 双亲委派模型
- 如何打破双亲委派
- 类加载器的分类

## 📖 类加载过程

### 1. 加载（Loading）

```java
/**
 * 加载阶段完成三件事：
 * 1. 通过类的全限定名获取类的二进制字节流
 * 2. 将字节流转化为方法区的运行时数据结构
 * 3. 在堆中生成 java.lang.Class 对象，作为方法区数据的访问入口
 */
public class LoadingPhase {
    // 类的加载是将 .class 文件加载到内存的过程
    // Class 对象是堆中的实例，类型是 java.lang.Class
    
    public static void main(String[] args) throws Exception {
        // 获取 Class 对象的三种方式
        Class<?> clazz1 = Class.forName("com.example.Person");
        Class<?> clazz2 = Person.class;
        Class<?> clazz3 = new Person().getClass();
        
        // 三种方式获取的是同一个 Class 对象
        System.out.println(clazz1 == clazz2);  // true
        System.out.println(clazz2 == clazz3);  // true
    }
}
```

### 2. 验证（Verification）

```java
/**
 * 验证阶段确保 Class 文件的字节流符合虚拟机规范
 * 包含四类验证：
 * 1. 文件格式验证 - 魔数、版本等
 * 2. 元数据验证 - 语义分析
 * 3. 字节码验证 - 数据流和控制流
 * 4. 符号引用验证 - 能否找到对应类/方法
 */
public class VerificationPhase {
    // 验证阶段由虚拟机自动完成
    // 可以通过 -Xverify:none 关闭（加快启动速度，但不安全）
}
```

### 3. 准备（Preparation）

```java
/**
 * 准备阶段为类变量分配内存并设置初始值
 * 注意：准备阶段只设置零值，真正的赋值在初始化阶段
 *
 * 例：public static int value = 123;
 * - 准备阶段：value = 0
 * - 初始化阶段：value = 123
 */
public class PreparationPhase {
    // 类变量（static）分配在方法区
    public static int staticVar = 123;      // 准备阶段: 0, 初始化: 123
    public static final int constVar = 456; // 准备阶段: 456 (编译期常量)
    
    // 引用类型默认 null
    public static Object staticObj;
    
    // 静态代码块在初始化阶段执行
    static {
        staticVar = 789;
    }
}
```

### 4. 解析（Resolution）

```java
/**
 * 解析阶段将符号引用转换为直接引用
 *
 * 符号引用：以一组符号描述所引用的目标
 * 直接引用：指向目标的指针、相对偏移量
 *
 * 解析的目标：
 * - 类和接口
 * - 字段（成员变量）
 * - 方法
 * - 接口方法
 */
public class ResolutionPhase {
    // 例如：解析符号引用 "java/lang/String" 为直接引用（方法区中的地址）
    
    // 字段解析示例
    class Parent {
        public int value = 1;
    }
    
    class Child extends Parent {
        public int childValue = 2;
        // 访问 value 时，需要解析 Parent 中的 value 字段
    }
}
```

### 5. 初始化（Initialization）

```java
/**
 * 初始化阶段执行 <clinit>() 方法
 * - <clinit>() 由编译器自动收集类中所有类变量的赋值和静态代码块组成
 * - 父子类的 <clinit>() 执行顺序：父类先执行
 * - <clinit>() 是线程安全的
 */
public class InitializationPhase {
    // 示例1：静态代码块和变量赋值
    static {
        System.out.println("父类静态代码块");
    }
    static int a = 1;
    
    // 执行顺序：静态代码块 -> 变量赋值（按源码顺序）
    static int b = print("b");
    static int c = 2;
    
    static int print(String s) {
        System.out.println("初始化 " + s);
        return 0;
    }
    
    // 主动使用类时触发初始化
    public static void main(String[] args) {
        // Child c = new Child();  // 触发父类和子类的初始化
    }
}

class Parent {
    static {
        System.out.println("Parent 初始化");
    }
}

class Child extends Parent {
    static {
        System.out.println("Child 初始化");
    }
}

// 不初始化的情况（被动使用）
class TestPassive {
    public static void main(String[] args) {
        // 1. 通过子类引用父类的静态字段，不会触发子类初始化
        System.out.println(Child.a);  // 只触发 Parent 初始化
        
        // 2. 通过数组定义引用类，不触发初始化
        Parent[] arr = new Parent[10];  // 不触发任何初始化
        
        // 3. 引用常量不会触发初始化（编译期放入常量池）
        System.out.println(Child.CONSTANT);
    }
}
```

## 📖 双亲委派模型

### 模型结构

```java
/**
 * Java 的类加载器层次（双亲委派模型）：
 *
 * Bootstrap ClassLoader (启动类加载器)
 *     ↑ C++ 实现，无法在 Java 代码中获取
 *     ↑ 负责加载 JAVA_HOME/lib 下的核心类库
 * 
 * Extension ClassLoader (扩展类加载器)
 *     ↑ sun.misc.Launcher$ExtClassLoader
 *     ↑ 负责加载 JAVA_HOME/lib/ext 下的扩展类
 * 
 * Application ClassLoader (应用类加载器)
 *     ↑ sun.misc.Launcher$AppClassLoader
 *     ↑ 负责加载 classpath 下的类
 * 
 * 自定义 ClassLoader
 *     ↑ 用户自定义的类加载器
 */
public class ClassLoaderHierarchy {
    public static void main(String[] args) {
        // 查看类加载器
        System.out.println("String 类加载器: " + String.class.getClassLoader());  // null (Bootstrap)
        System.out.println("当前类加载器: " + ClassLoaderHierarchy.class.getClassLoader());  // AppClassLoader
        
        // 查看父加载器
        ClassLoader appLoader = ClassLoaderHierarchy.class.getClassLoader();
        System.out.println("AppClassLoader 父加载器: " + appLoader.getParent());  // ExtClassLoader
    }
}
```

### 工作原理

```java
/**
 * 双亲委派模型工作流程：
 * 
 * 1. 类加载器收到加载请求
 * 2. 委托给父类加载器处理
 * 3. 父类再委托其父类...
 * 4. 到达 Bootstrap ClassLoader
 * 5. Bootstrap 无法处理时，子加载器尝试自己加载
 * 
 * 优点：
 * - 避免类的重复加载
 * - 保证类的安全性（核心类无法被篡改）
 */
public class ParentDelegationModel {
    // ClassLoader.loadClass() 的核心代码逻辑：
    
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        // 1. 检查是否已加载
        Class<?> c = findLoadedClass(name);
        if (c != null) {
            return c;
        }
        
        // 2. 委托给父类加载
        try {
            return parent.loadClass(name, false);
        } catch (ClassNotFoundException e) {
            // 3. 父类无法加载，自己尝试
            return findClass(name);
        }
    }
}
```

### 打破双亲委派

```java
/**
 * 打破双亲委派的场景：
 * 1. Tomcat：每个 Web 应用都有自己的 WebAppClassLoader
 * 2. SPI：JDBC 使用线程上下文类加载器
 * 3. OSGi：模块化加载
 */
public class BreakDelegation {
    // 方法1：重写 loadClass()
    static class MyClassLoader extends ClassLoader {
        @Override
        public Class<?> loadClass(String name) throws ClassNotFoundException {
            // 不委托给父类，直接自己加载
            if (name.startsWith("com.myapp.")) {
                return findClass(name);
            }
            return super.loadClass(name);
        }
        
        @Override
        protected Class<?> findClass(String name) throws ClassNotFoundException {
            // 自定义加载逻辑
            // 从自定义路径加载 .class 文件
            return null;
        }
    }
    
    // 方法2：线程上下文类加载器（SPI机制）
    public static void main(String[] args) {
        // JDBC 驱动加载示例
        // DriverManager 使用线程上下文类加载器来加载驱动
        
        // 获取当前线程的上下文类加载器
        ClassLoader ctxLoader = Thread.currentThread().getContextClassLoader();
        
        // 设置新的上下文类加载器
        Thread.currentThread().setContextClassLoader(new MyClassLoader());
    }
}
```

## 📖 类加载器分类

```java
/**
 * 启动类加载器（Bootstrap ClassLoader）
 * - C++ 实现
 * - 加载 JAVA_HOME/lib 下的核心类
 * - 无法被 Java 代码引用
 */
public class BootstrapLoader {
    // 验证
    ClassLoader bootstrapLoader = String.class.getClassLoader();  // null
}

/**
 * 扩展类加载器（Extension ClassLoader）
 * - sun.misc.Launcher$ExtClassLoader
 * - 加载 JAVA_HOME/lib/ext 下的类
 * - 可以被 Java 代码引用
 */
public class ExtensionLoader {
    ClassLoader extLoader = new javax.net.ssl.SSLContext("TLS").getClass().getClassLoader();
    // ExtensionLoader
}

/**
 * 应用类加载器（Application ClassLoader）
 * - sun.misc.Launcher$AppClassLoader
 * - 加载 classpath 下的类
 * - 默认的类加载器
 */
public class ApplicationLoader {
    ClassLoader appLoader = ApplicationLoader.class.getClassLoader();  // AppClassLoader
}
```

## 📖 面试真题

### Q1: 什么是双亲委派模型？

**答：** 当类加载器收到加载请求时，会先将请求委托给父类加载器处理，父类再委托其父类...直到启动类加载器。只有父加载器无法完成时，子加载器才尝试自己加载。优点是避免类的重复加载，保证核心类安全。

### Q2: 为什么需要自定义类加载器？

**答：**
1. 隔离加载冲突（Tomcat 每个 Web 应用独立）
2. 动态加载（从非标准路径加载类）
3. 热部署（运行时替换类）
4. 加密保护（自定义解密逻辑）

### Q3: 类的主动使用和被动使用？

**答：** 主动使用会触发初始化：
- new 对象
- 访问类的静态属性/方法
- 反射调用
- 初始化子类（父类先初始化）
- 启动类（main 方法所在类）

被动使用不触发初始化：
- 引用常量（编译期常量）
- 数组定义
- 子类引用父类静态属性（只初始化父类）

---

**⭐ 重点：双亲委派模型是 Java 模块系统的基础，理解其工作原理和如何打破非常重要**