---
layout: default
title: Spring Bean 生命周期详解 ⭐⭐⭐
---
# Spring Bean 生命周期详解 ⭐⭐⭐

## 面试题：说说 Spring Bean 的生命周期

### 核心回答

Spring Bean 的生命周期是指 Bean 从创建到销毁的整个过程，主要分为四个阶段：**实例化 → 属性赋值 → 初始化 → 销毁**。Spring 在每个阶段都提供了扩展点，允许开发者插入自定义逻辑。

### 完整生命周期流程图

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Spring Bean 完整生命周期                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Bean 创建前准备阶段                                              │
│     ├── BeanDefinition 加载                                          │
│     ├── BeanFactoryPostProcessor 处理                                │
│     └── InstantiationAwareBeanPostProcessor 扩展                      │
│                                                                      │
│  2. 实例化阶段（Instantiation）                                      │
│     └── createBeanInstance() → 调用构造方法创建 Bean 实例             │
│                                                                      │
│  3. 属性赋值阶段（Populate）                                         │
│     ├── 属性注入（@Autowired、@Value 等）                              │
│     ├── BeanNameAware.setBeanName()                                 │
│     ├── BeanFactoryAware.setBeanFactory()                           │
│     └── ApplicationContextAware.setApplicationContext()              │
│                                                                      │
│  4. 初始化阶段（Initialization）                                      │
│     ├── BeanPostProcessor.postProcessBeforeInitialization()          │
│     ├── InitializingBean.afterPropertiesSet()                        │
│     ├── @PostConstruct 注解方法                                      │
│     ├── 自定义 init-method                                          │
│     └── BeanPostProcessor.postProcessAfterInitialization()           │
│                                                                      │
│  5. 使用阶段（In Use）                                               │
│                                                                      │
│  6. 销毁阶段（Destruction）                                          │
│     ├── @PreDestroy 注解方法                                         │
│     ├── DisposableBean.destroy()                                      │
│     └── 自定义 destroy-method                                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 详细阶段说明

#### 1. 实例化阶段

```java
// 源码位置：AbstractAutowireCapableBeanFactory.createBeanInstance()

protected BeanWrapper createBeanInstance(String beanName, RootBeanDefinition mbd, 
                                       @Nullable Object[] args) {
    // 1. 使用构造方法创建实例
    BeanInstance instance = instantiateUsingReflection(beanName, mbd, constructor, args);
    return instance;
}
```

**触发时机**：调用 `getBean()` 或容器启动时

#### 2. 属性赋值阶段

```java
// 源码位置：AbstractAutowireCapableBeanFactory.populateBean()

protected void populateBean(String beanName, RootBeanDefinition mbd, BeanWrapper bw) {
    // 1. 属性注入
    applyPropertyValues(beanName, mbd, bw, pvs);
}

// Aware 接口回调
public void setBeanName(String name) { /* 获取 Bean 名称 */ }
public void setBeanFactory(BeanFactory beanFactory) { /* 获取 BeanFactory */ }
```

**Aware 接口列表**：

| 接口 | 方法 | 作用 |
|------|------|------|
| BeanNameAware | setBeanName() | 获取 Bean 名称 |
| BeanFactoryAware | setBeanFactory() | 获取 BeanFactory |
| ApplicationContextAware | setApplicationContext() | 获取 ApplicationContext |
| EnvironmentAware | setEnvironment() | 获取环境变量 |
| ResourceLoaderAware | setResourceLoader() | 获取资源加载器 |

#### 3. 初始化阶段

```java
// 源码位置：AbstractAutowireCapableBeanFactory.initializeBean()

protected Object initializeBean(String beanName, Object bean, RootBeanDefinition mbd) {
    
    // 1. Aware 回调（如果还没执行）
    invokeAwareMethods(beanName, bean);
    
    // 2. 前置处理器
    wrappedBean = applyBeanPostProcessorsBeforeInitialization(wrappedBean, beanName);
    
    // 3. 初始化方法
    invokeInitMethods(beanName, wrappedBean, mbd);
    
    // 4. 后置处理器
    wrappedBean = applyBeanPostProcessorsAfterInitialization(wrappedBean, beanName);
    
    return wrappedBean;
}

// 初始化方法调用顺序
private void invokeInitMethods(String beanName, Object bean, RootBeanDefinition mbd) {
    
    // 1. InitializingBean 接口
    if (bean instanceof InitializingBean) {
        ((InitializingBean) bean).afterPropertiesSet();
    }
    
    // 2. @PostConstruct 注解方法
    // 由 InitDestroyAnnotationBeanPostProcessor 处理
    
    // 3. 自定义 init-method
    if (mbd.hasInitMethodName()) {
        invokeCustomInitMethod(beanName, bean, mbd);
    }
}
```

#### 4. 销毁阶段

```java
// 源码位置：DefaultSingletonBeanRegistry.destroyBean()

public void destroySingleton(String beanName) {
    // 1. @PreDestroy 注解方法
    // 由 InitDestroyAnnotationBeanPostProcessor 处理
    
    // 2. DisposableBean.destroy()
    if (bean instanceof DisposableBean) {
        ((DisposableBean) bean).destroy();
    }
    
    // 3. 自定义 destroy-method
    if (mbd.hasDestroyMethodName()) {
        invokeCustomDestroyMethod(beanName, bean, mbd);
    }
}
```

### 完整代码示例

```java
@Component
public class UserService implements InitializingBean, DisposableBean {
    
    @Autowired
    private UserDao userDao;
    
    private String name;
    
    // 1. 构造方法（实例化阶段）
    public UserService() {
        System.out.println("1. 构造方法执行");
    }
    
    // 2. 属性注入（属性赋值阶段）
    @Autowired
    public void setUserDao(UserDao userDao) {
        System.out.println("2. 属性注入");
        this.userDao = userDao;
    }
    
    // 3. Aware 回调
    @PostConstruct
    public void init() {
        System.out.println("5. @PostConstruct 执行");
    }
    
    // 4. InitializingBean
    @Override
    public void afterPropertiesSet() {
        System.out.println("6. afterPropertiesSet 执行");
    }
    
    // 5. 自定义初始化方法
    public void customInit() {
        System.out.println("7. customInit 执行");
    }
    
    // 6. 销毁方法
    @PreDestroy
    public void cleanup() {
        System.out.println("8. @PreDestroy 执行");
    }
    
    @Override
    public void destroy() {
        System.out.println("9. destroy 执行");
    }
    
    public void customDestroy() {
        System.out.println("10. customDestroy 执行");
    }
}
```

**Bean 配置**：
```xml
<bean id="userService" class="com.example.UserService" 
      init-method="customInit" 
      destroy-method="customDestroy"/>
```

**执行顺序**：
```
1. 构造方法执行
2. 属性注入
5. @PostConstruct 执行
6. afterPropertiesSet 执行
7. customInit 执行
... Bean 使用中 ...
8. @PreDestroy 执行
9. destroy 执行
10. customDestroy 执行
```

### BeanPostProcessor 扩展点

```java
@Component
public class MyBeanPostProcessor implements BeanPostProcessor {
    
    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) {
        System.out.println("Before Initialization: " + beanName);
        return bean;
    }
    
    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        System.out.println("After Initialization: " + beanName);
        return bean;
    }
}
```

**执行顺序**：
```
构造方法 → 属性注入 → 
BeanPostProcessor.postProcessBeforeInitialization() →
@PostConstruct → afterPropertiesSet → customInit →
BeanPostProcessor.postProcessAfterInitialization()
```

### Spring 后置处理器体系

```
BeanPostProcessor
├── InstantiationAwareBeanPostProcessor
│   ├── postProcessBeforeInstantiation()  → 实例化前
│   ├── postProcessAfterInstantiation()   → 实例化后
│   └── postProcessPropertiesValues()     → 属性赋值前
├── DestructionAwareBeanPostProcessor
│   └── postProcessBeforeDestruction()   → 销毁前
└── MergedBeanDefinitionPostProcessor
    └── postProcessMergedBeanDefinition() → 合并 Bean 定义后
```

### Bean 作用域与生命周期

| 作用域 | 实例化时机 | 销毁时机 |
|--------|-----------|---------|
| singleton | 容器启动时 | 容器关闭时 |
| prototype | getBean 时 | GC 时（不主动销毁） |
| request | 每次请求时 | 请求结束 |
| session | 每次会话时 | 会话超时 |
| application | 上下文启动时 | 上下文关闭 |

### 高频面试题

**Q1: BeanFactory 和 FactoryBean 的区别？**

```java
// BeanFactory：IoC 容器接口
ConfigurableBeanFactory beanFactory = new DefaultListableBeanFactory();

// FactoryBean：用于创建复杂 Bean
@Component
public class MyFactoryBean implements FactoryBean<User> {
    @Override
    public User getObject() {
        return new User();
    }
    
    @Override
    public Class<?> getObjectType() {
        return User.class;
    }
}

// 获取 FactoryBean 本身
UserFactory factory = beanFactory.getBean("&myFactoryBean");

// 获取 FactoryBean 创建的对象
User user = beanFactory.getBean("myFactoryBean");
```

**Q2: 为什么有时候要用 BeanPostProcessor？**

- **AOP 代理**：AnnotationAwareAspectJAutoProxyCreator 是 BeanPostProcessor 的实现
- **注解解析**：@Autowired、@PostConstruct 等都依赖 BeanPostProcessor
- **动态代理**：在初始化后创建代理对象

**Q3: 构造方法注入 vs Setter 注入的生命周期差异？**

```java
// 构造方法注入：属性在实例化时就已完成赋值
@Service
public class ServiceA {
    private final ServiceB serviceB;
    
    public ServiceA(ServiceB serviceB) {
        this.serviceB = serviceB;  // 实例化时已完成注入
    }
}

// Setter 注入：属性在 populateBean 阶段赋值
@Service
public class ServiceA {
    private ServiceB serviceB;
    
    @Autowired
    public void setServiceB(ServiceB serviceB) {
        this.serviceB = serviceB;  // 稍后注入
    }
}
```

### 最佳实践

```java
// 1. 优先使用构造方法注入
@Service
public class UserService {
    private final UserDao userDao;
    
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}

// 2. 使用 @PostConstruct 而非 InitializingBean
@Component
public class CacheService {
    @Autowired
    private Cache cache;
    
    @PostConstruct
    public void init() {
        cache.load();
    }
}

// 3. 使用 @PreDestroy 而非 DisposableBean
@Component
public class ConnectionManager {
    @PreDestroy
    public void close() {
        connection.close();
    }
}

// 4. 避免在 init/destroy 方法中抛出异常
```

---

**参考链接：**
- [Spring Bean生命周期最详解-知乎](https://zhuanlan.zhihu.com/p/451683248)
- [Spring Bean生命周期-图灵课堂](https://www.tulingxueyuan.cn/tlzx/javamst/12226.html)
