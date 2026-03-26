---
layout: default
title: 建造者模式（Builder Pattern）：分步构建复杂对象
---
# 建造者模式（Builder Pattern）：分步构建复杂对象

> 建造者模式将复杂对象的构建与表示分离，使得同样的构建过程可以创建不同的表示

## 🎯 面试重点

- 建造者模式解决构造器重载问题
- 传统Builder与Lombok @Builder的区别
- Spring源码中的建造者模式应用
- 建造者模式与工厂模式的区别

## 📖 一、核心思想

### 1.1 问题背景：构造器重载地狱

```java
/**
 * 构造器重载地狱示例
 * 问题：参数多时，构造器组合爆炸
 */
public class User {
    private String name;        // 必填
    private int age;            // 可选
    private String email;       // 可选
    private String phone;       // 可选
    private String address;     // 可选
    
    // 全参数构造器
    public User(String name, int age, String email, String phone, String address) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.phone = phone;
        this.address = address;
    }
    
    // 部分参数构造器1
    public User(String name, int age, String email) {
        this(name, age, email, null, null);
    }
    
    // 部分参数构造器2
    public User(String name, String email) {
        this(name, 0, email, null, null);
    }
    
    // 部分参数构造器3
    public User(String name, int age) {
        this(name, age, null, null, null);
    }
    
    // ... 需要定义很多构造器
}

/**
 * 使用问题：
 * 1. 参数顺序容易混淆
 * 2. 不知道每个参数的含义
 * 3. 构造器数量爆炸
 */
User user1 = new User("张三", 25, "zhangsan@example.com");
User user2 = new User("张三", "zhangsan@example.com"); // email传给age位置？
```

### 1.2 问题背景：Setter方式的不安全

```java
/**
 * Setter方式的问题
 */
public class User {
    private String name;
    private int age;
    private String email;
    
    // setter方法
    public void setName(String name) { this.name = name; }
    public void setAge(int age) { this.age = age; }
    public void setEmail(String email) { this.email = email; }
}

/**
 * 使用问题：
 * 1. 对象状态不完整（分步设置，中间状态不一致）
 * 2. 对象可变（非线程安全）
 * 3. 无法保证必填参数
 */
User user = new User();
user.setName("张三");
// 此时user对象状态不完整
user.setAge(25);
// 可能忘记设置email
```

### 1.3 建造者模式的解决方案

```java
/**
 * 建造者模式解决上述问题
 */
public class User {
    private final String name;    // 必填，final保证不可变
    private final int age;
    private final String email;
    private final String phone;
    private final String address;
    
    // 私有构造器，只能通过Builder创建
    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
        this.phone = builder.phone;
        this.address = builder.address;
    }
    
    // 静态内部Builder类
    public static class Builder {
        private String name;      // 必填
        private int age = 0;      // 默认值
        private String email;
        private String phone;
        private String address;
        
        // 必填参数构造器
        public Builder(String name) {
            this.name = name;
        }
        
        // 可选参数setter，返回Builder实现链式调用
        public Builder age(int age) {
            this.age = age;
            return this;
        }
        
        public Builder email(String email) {
            this.email = email;
            return this;
        }
        
        public Builder phone(String phone) {
            this.phone = phone;
            return this;
        }
        
        public Builder address(String address) {
            this.address = address;
            return this;
        }
        
        // 构建方法
        public User build() {
            // 可以在这里添加校验逻辑
            if (name == null || name.isEmpty()) {
                throw new IllegalStateException("name不能为空");
            }
            return new User(this);
        }
    }
    
    // getter方法
    public String getName() { return name; }
    public int getAge() { return age; }
    public String getEmail() { return email; }
}

/**
 * 使用方式：链式调用，参数清晰
 */
User user = new User.Builder("张三")
    .age(25)
    .email("zhangsan@example.com")
    .phone("13800138000")
    .build();
```

## 📖 二、传统Builder模式详解

### 2.1 类图结构

```
Director ──────> Builder
                   ↑
            ┌──────┴──────┐
      ConcreteBuilder   AnotherBuilder
            ↓                ↓
        Product          AnotherProduct
```

### 2.2 核心角色

- **Product（产品）：** 最终要构建的复杂对象
- **Builder（抽象建造者）：** 定义构建产品的抽象接口
- **ConcreteBuilder（具体建造者）：** 实现Builder接口，具体构建产品
- **Director（指挥者）：** 控制构建流程，调用Builder的方法

### 2.3 完整代码示例

```java
/**
 * 产品：电脑配置
 */
public class Computer {
    private String cpu;
    private String ram;
    private String storage;
    private String gpu;
    private String monitor;
    
    // getter/setter
    public void setCpu(String cpu) { this.cpu = cpu; }
    public void setRam(String ram) { this.ram = ram; }
    public void setStorage(String storage) { this.storage = storage; }
    public void setGpu(String gpu) { this.gpu = gpu; }
    public void setMonitor(String monitor) { this.monitor = monitor; }
    
    @Override
    public String toString() {
        return String.format("Computer{cpu='%s', ram='%s', storage='%s', gpu='%s', monitor='%s'}",
            cpu, ram, storage, gpu, monitor);
    }
}

/**
 * 抽象建造者
 */
public abstract class ComputerBuilder {
    protected Computer computer = new Computer();
    
    public abstract void buildCpu();
    public abstract void buildRam();
    public abstract void buildStorage();
    public abstract void buildGpu();
    public abstract void buildMonitor();
    
    public Computer getResult() {
        return computer;
    }
}

/**
 * 具体建造者：高端电脑
 */
public class HighEndComputerBuilder extends ComputerBuilder {
    @Override
    public void buildCpu() {
        computer.setCpu("Intel i9-13900K");
    }
    
    @Override
    public void buildRam() {
        computer.setRam("64GB DDR5 6000MHz");
    }
    
    @Override
    public void buildStorage() {
        computer.setStorage("2TB NVMe SSD");
    }
    
    @Override
    public void buildGpu() {
        computer.setGpu("NVIDIA RTX 4090");
    }
    
    @Override
    public void buildMonitor() {
        computer.setMonitor("32寸 4K 144Hz");
    }
}

/**
 * 具体建造者：办公电脑
 */
public class OfficeComputerBuilder extends ComputerBuilder {
    @Override
    public void buildCpu() {
        computer.setCpu("Intel i5-13400");
    }
    
    @Override
    public void buildRam() {
        computer.setRam("16GB DDR4 3200MHz");
    }
    
    @Override
    public void buildStorage() {
        computer.setStorage("512GB SSD");
    }
    
    @Override
    public void buildGpu() {
        computer.setGpu("Intel UHD 730"); // 核显
    }
    
    @Override
    public void buildMonitor() {
        computer.setMonitor("24寸 1080P 60Hz");
    }
}

/**
 * 指挥者：控制构建流程
 */
public class ComputerDirector {
    private ComputerBuilder builder;
    
    public ComputerDirector(ComputerBuilder builder) {
        this.builder = builder;
    }
    
    public void setBuilder(ComputerBuilder builder) {
        this.builder = builder;
    }
    
    /**
     * 构建电脑 - 定义构建顺序和流程
     */
    public Computer construct() {
        builder.buildCpu();
        builder.buildRam();
        builder.buildStorage();
        builder.buildGpu();
        builder.buildMonitor();
        return builder.getResult();
    }
    
    /**
     * 构建无独显电脑
     */
    public Computer constructWithoutGpu() {
        builder.buildCpu();
        builder.buildRam();
        builder.buildStorage();
        // builder.buildGpu(); // 不构建GPU
        builder.buildMonitor();
        return builder.getResult();
    }
}

/**
 * 客户端使用
 */
public class Client {
    public static void main(String[] args) {
        // 创建高端电脑
        ComputerDirector director = new ComputerDirector(new HighEndComputerBuilder());
        Computer highEnd = director.construct();
        System.out.println("高端电脑: " + highEnd);
        
        // 切换到办公电脑
        director.setBuilder(new OfficeComputerBuilder());
        Computer office = director.construct();
        System.out.println("办公电脑: " + office);
    }
}
```

### 2.4 简化版Builder（链式调用）

```java
/**
 * 链式Builder - 最常用的形式
 * 无需Director，Builder直接构建
 */
public class StringBuilder {
    private String value = "";
    
    public StringBuilder append(String str) {
        this.value += str;
        return this;
    }
    
    public StringBuilder appendLine(String str) {
        this.value += str + "\n";
        return this;
    }
    
    public String build() {
        return value;
    }
}

// 使用
String result = new StringBuilder()
    .append("Hello ")
    .append("World")
    .append("!")
    .build();
```

## 📖 三、Spring源码中的Builder模式

### 3.1 BeanDefinitionBuilder

```java
/**
 * Spring BeanDefinition构建器
 * org.springframework.beans.factory.support.BeanDefinitionBuilder
 */
public class BeanDefinitionBuilder {
    
    private final AbstractBeanDefinition beanDefinition;
    private String beanClassName;
    
    // 私有构造器
    private BeanDefinitionBuilder(AbstractBeanDefinition beanDefinition) {
        this.beanDefinition = beanDefinition;
    }
    
    // 静态工厂方法
    public static BeanDefinitionBuilder rootBeanDefinition(Class<?> beanClass) {
        return new BeanDefinitionBuilder(new RootBeanDefinition(beanClass));
    }
    
    public static BeanDefinitionBuilder rootBeanDefinition(String beanClassName) {
        BeanDefinitionBuilder builder = new BeanDefinitionBuilder(new RootBeanDefinition());
        builder.beanClassName = beanClassName;
        return builder;
    }
    
    public static BeanDefinitionBuilder genericBeanDefinition(Class<?> beanClass) {
        return new BeanDefinitionBuilder(new GenericBeanDefinition(beanClass));
    }
    
    // 设置属性值
    public BeanDefinitionBuilder addPropertyValue(String name, Object value) {
        this.beanDefinition.getPropertyValues().add(name, value);
        return this;
    }
    
    // 设置构造参数
    public BeanDefinitionBuilder addConstructorArgValue(Object value) {
        this.beanDefinition.getConstructorArgumentValues().addGenericArgumentValue(value);
        return this;
    }
    
    public BeanDefinitionBuilder addConstructorArgReference(String beanName) {
        this.beanDefinition.getConstructorArgumentValues()
            .