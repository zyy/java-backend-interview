# 注解与反射

> Java 的元编程能力

## 🎯 面试重点

- 注解的定义和使用
- 反射的原理和应用
- 两者结合使用场景

## 📖 注解

### 内置注解

```java
/**
 * 常见内置注解
 */
public class BuiltInAnnotations {
    // @Override - 方法重写
    // @Deprecated - 已废弃
    // @SuppressWarnings - 抑制警告
    // @FunctionalInterface - 函数式接口
    // @SafeVarargs - 安全可变参数
    
    @Override
    public String toString() { return ""; }
    
    @Deprecated
    public void oldMethod() {}
    
    @SuppressWarnings("unchecked")
    public void warning() {
        List list = new ArrayList();
    }
}
```

### 自定义注解

```java
/**
 * 自定义注解
 */
public class CustomAnnotation {
    // 定义
    /*
     * @Retention(RetentionPolicy.RUNTIME)
     * @Target(ElementType.METHOD)
     * public @interface MyAnnotation {
     *     String value() default "";
     *     int priority() default 1;
     * }
     */
    
    // 使用
    /*
     * @MyAnnotation(value = "test", priority = 3)
     * public void method() { }
     */
}
```

### 元注解

```java
/**
 * 元注解（注解的注解）
 */
public class MetaAnnotation {
    // @Retention - 保留策略
    /*
     * SOURCE：源码可见，编译时丢弃
     * CLASS：编译时可见，运行时丢弃
     * RUNTIME：运行时可见，可反射读取
     */
    
    // @Target - 作用目标
    /*
     * TYPE, METHOD, FIELD, PARAMETER, CONSTRUCTOR, LOCAL_VARIABLE, ANNOTATION_TYPE, PACKAGE
     */
}
```

## 📖 反射

### 获取 Class

```java
/**
 * 获取 Class 对象
 */
public class GetClass {
    // 三种方式
    /*
     * // 1. 类名.class
     * Class<?> clazz = String.class;
     * 
     * // 2. 对象.getClass()
     * String s = "hello";
     * Class<?> clazz = s.getClass();
     * 
     * // 3. Class.forName()
     * Class<?> clazz = Class.forName("java.lang.String");
     */
}
```

### 反射操作

```java
/**
 * 反射操作
 */
public class ReflectOperation {
    // 创建对象
    /*
     * Class<?> clazz = Class.forName("com.example.Person");
     * Person p = (Person) clazz.newInstance();  // 无参构造
     * 
     * // 有参构造
     * Constructor<?> constructor = clazz.getConstructor(String.class, int.class);
     * Person p = (Person) constructor.newInstance("Tom", 20);
     */
    
    // 获取属性
    /*
     * Field nameField = clazz.getDeclaredField("name");
     * nameField.setAccessible(true);  // 私有属性需要
     * nameField.set(p, "Tom");
     */
    
    // 获取方法
    /*
     * Method method = clazz.getMethod("setName", String.class);
     * method.invoke(p, "Tom");
     */
}
```

## 📖 面试真题

### Q1: 注解和反射的关系？

**答：** 注解是元数据，反射可以在运行时读取注解信息，常用于框架实现（如 Spring 的依赖注入）。

### Q2: 反射的缺点？

**答：** 性能较低、安全性问题、破坏封装性。

---

**⭐ 重点：注解和反射是框架底层的基础**