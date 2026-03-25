# Spring 循环依赖与三级缓存 ⭐⭐⭐

## 面试题：Spring 是如何解决循环依赖的？

### 核心回答

Spring 通过**三级缓存**机制解决单例 Bean 的循环依赖问题。三级缓存分别存储不同阶段的 Bean 对象，通过提前暴露未完成初始化的 Bean 引用，打破循环依赖的死锁状态。

### 什么是循环依赖？

**循环依赖**：两个或多个 Bean 相互依赖，形成闭环。

```java
@Service
public class A {
    @Autowired
    private B b;  // A 依赖 B
    
    public void test() {
        b.doSomething();
    }
}

@Service
public class B {
    @Autowired
    private A a;  // B 依赖 A，形成循环！
}
```

**循环依赖的三种场景**：

| 场景 | 能否解决 | 说明 |
|------|---------|------|
| Setter 注入（单例） | ✅ 能解决 | Spring 三级缓存 |
| Field 注入（单例） | ✅ 能解决 | Spring 三级缓存 |
| 构造器注入 | ❌ 无法解决 | 构造时就需要完整对象 |

### 三级缓存结构

```java
public class DefaultSingletonBeanRegistry extends FactoryBeanRegistrySupport {
    
    // 一级缓存：完全初始化好的 Bean，直接可用
    private final Map<String, Object> singletonObjects = 
        new ConcurrentHashMap<>(256);
    
    // 二级缓存：早期曝光的 Bean（已实例化但未完成属性填充和初始化）
    private final Map<String, Object> earlySingletonObjects = 
        new ConcurrentHashMap<>(16);
    
    // 三级缓存：Bean 工厂对象，用于创建早期 Bean（支持 AOP 代理）
    private final Map<String, ObjectFactory<?>> singletonFactories = 
        new ConcurrentHashMap<>(16);
}
```

**三级缓存的作用**：

```
┌─────────────────────────────────────────────────────────────┐
│                     三级缓存工作原理                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  一级缓存 (singletonObjects)                                 │
│  ├── 存放：完全初始化好的 Bean                              │
│  └── 特点：可直接使用                                      │
│                                                             │
│  二级缓存 (earlySingletonObjects)                           │
│  ├── 存放：已实例化但未初始化的 Bean（半成品）             │
│  └── 特点：防止重复创建代理对象                            │
│                                                             │
│  三级缓存 (singletonFactories)                              │
│  ├── 存放：ObjectFactory（Lambda 表达式）                  │
│  └── 特点：延迟创建、支持 AOP 代理                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 循环依赖解决流程

#### 场景：A → B → A

```
┌────────────────────────────────────────────────────────────────────┐
│                      创建 Bean A 的流程                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. 调用 getBean(A)                                                │
│     ↓                                                              │
│  2. 一级缓存没有，二级缓存没有，三级缓存有 ObjectFactory            │
│     ↓                                                              │
│  3. 调用 ObjectFactory.getObject() 创建早期 A 对象                  │
│     ↓                                                              │
│  4. 将早期 A 对象放入二级缓存，删除三级缓存                        │
│     ↓                                                              │
│  5. 属性注入：发现依赖 B，调用 getBean(B)                          │
│     ↓                                                              │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │              创建 Bean B 的流程                          │    │
│  ├───────────────────────────────────────────────────────────┤    │
│  │                                                           │    │
│  │  1. 调用 getBean(B)                                       │    │
│  │     ↓                                                     │    │
│  │  2. 一级缓存没有，二级缓存没有，三级缓存没有               │    │
│  │     ↓                                                     │    │
│  │  3. 创建 B 实例，将 ObjectFactory 放入三级缓存              │    │
│  │     ↓                                                     │    │
│  │  4. 属性注入：发现依赖 A，调用 getBean(A)                  │    │
│  │     ↓                                                     │    │
│  │  5. 调用 getBean(A)                                        │    │
│  │     ↓                                                     │    │
│  │  6. A 已经在二级缓存中！直接返回早期 A 对象                │    │
│  │     ↓                                                     │    │
│  │  7. B 获得 A 的引用，属性注入完成                          │    │
│  │     ↓                                                     │    │
│  │  8. B 完成初始化，放入一级缓存                             │    │
│  │     ↓                                                     │    │
│  │  9. 返回 B                                                │    │
│  │                                                           │    │
│  └───────────────────────────────────────────────────────────┘    │
│     ↓                                                              │
│  6. B 创建完成，A 获得 B 的引用，属性注入完成                      │
│     ↓                                                              │
│  7. A 完成初始化，放入一级缓存                                      │
│     ↓                                                              │
│  8. 返回完整的 A 对象                                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 源码解析

#### getSingleton 方法

```java
// DefaultSingletonBeanRegistry.getSingleton()
protected Object getSingleton(String beanName, boolean allowEarlyReference) {
    // 1. 一级缓存：检查完整的 Bean
    Object singletonObject = this.singletonObjects.get(beanName);
    if (singletonObject == null && isSingletonCurrentlyInCreation(beanName)) {
        // 2. 二级缓存：检查早期 Bean
        singletonObject = this.earlySingletonObjects.get(beanName);
        if (singletonObject == null) {
            // 3. 三级缓存：获取工厂创建早期 Bean
            ObjectFactory<?> singletonFactory = this.singletonFactories.get(beanName);
            if (singletonFactory != null) {
                singletonObject = singletonFactory.getObject();
                // 放入二级缓存
                this.earlySingletonObjects.put(beanName, singletonObject);
                // 删除三级缓存
                this.singletonFactories.remove(beanName);
            }
        }
    }
    return singletonObject;
}
```

#### doCreateBean 方法

```java
protected Object doCreateBean(String beanName, RootBeanDefinition mbd, 
                             @Nullable Object[] args) {
    // 1. 实例化 Bean
    BeanWrapper instanceWrapper = createBeanInstance(beanName, mbd, args);
    
    // 2. 关键：将 ObjectFactory 放入三级缓存（提前暴露）
    addSingletonFactory(beanName, () -> {
        return wrapIfNecessary(instanceWrapper.getWrappedInstance(), 
                              beanName, mbd);
    });
    
    // 3. 属性填充（这里会触发循环依赖的解决）
    populateBean(beanName, mbd, instanceWrapper);
    
    // 4. 初始化
    Object exposedObject = initializeBean(beanName, exposedObject, mbd);
    
    return exposedObject;
}
```

### 为什么需要三级缓存？

#### 只用一级缓存的问题

```java
// 如果只用一级缓存
// 问题：无法区分「正在创建」和「已完成」的 Bean

// A 开始创建
// B 开始创建，A 还没完成
// A 放入一级缓存
// B 获取到 A，但 A 还没完成初始化！
```

#### 只用二级缓存的问题

```java
// 如果只用二级缓存
// 问题：无法支持 AOP 代理

// A 创建过程中，需要提前代理
// 但代理需要完整的 Bean 信息（属性已填充）
// 二级缓存无法延迟到正确的时机创建代理
```

#### 三级缓存的完美设计

```java
// 三级缓存 + ObjectFactory 解决 AOP 问题
addSingletonFactory(beanName, () -> {
    // 延迟到真正需要时才创建代理
    // 这里可以检查是否需要 AOP 代理
    return wrapIfNecessary(bean, beanName, mbd);
});
```

### 无法解决的循环依赖

#### 构造器注入

```java
@Service
public class A {
    private final B b;
    
    // 构造器注入，Spring 无法解决循环依赖
    public A(B b) {
        this.b = b;  // 创建 A 时就需要 B，但 B 还没创建完成！
    }
}
```

**错误**：`BeanCurrentlyInCreationException`

**解决方案**：
```java
// 1. 改用 Setter 注入
@Service
public class A {
    private B b;
    
    @Autowired
    public void setB(B b) {
        this.b = b;
    }
}

// 2. 使用 @Lazy 延迟加载
@Service
public class A {
    private final B b;
    
    public A(@Lazy B b) {
        this.b = b;  // 延迟创建 B
    }
}

// 3. 使用 @PostConstruct
@Service
public class A {
    @Autowired
    private B b;
    
    @PostConstruct
    public void init() {
        // 初始化逻辑
    }
}
```

#### prototype 作用域

```java
// prototype 作用域的 Bean 每次都创建新实例
// Spring 不缓存正在创建的 prototype Bean，无法解决循环依赖
@Bean
@Scope("prototype")
public A a() {
    return new A(b());
}

@Bean
@Scope("prototype")
public B b() {
    return new B(a());
}
```

### @Lazy 解决循环依赖

```java
@Service
public class A {
    private final B b;
    
    // 使用 @Lazy 延迟注入
    public A(@Lazy B b) {
        this.b = b;
    }
}

@Service
public class B {
    private final A a;
    
    public B(A a) {
        this.a = a;
    }
}
```

**原理**：
- 构造器参数使用 `@Lazy` 时，Spring 注入的是一个代理对象
- 代理对象在第一次使用时才真正创建目标 Bean
- 打破循环依赖

### 高频面试题

**Q1: 为什么三级缓存要用 ObjectFactory 而不是直接存 Bean？**

```java
// 直接存 Bean 的问题
singletonFactories.put(beanName, bean);  // 存的是完整对象

// 使用 ObjectFactory 的优势
singletonFactories.put(beanName, () -> wrapIfNecessary(bean, beanName, mbd));

// 好处：
// 1. 延迟创建：只有在真正需要时才创建早期引用
// 2. 支持 AOP：可以在创建过程中检查是否需要生成代理对象
// 3. 节省内存：不需要的 Bean 不会被提前创建
```

**Q2: 二级缓存存在的意义？**

```java
// 防止重复创建代理对象

// 场景：A → B → A
// B 获取 A 时，从三级缓存获取，创建一个代理 A
// A 又获取 B，B 再次获取 A
// 如果没有二级缓存，会再次创建代理 A

// 二级缓存保证了：
// 同一个 Bean 在创建过程中只创建一个早期引用
```

**Q3: Spring 为什么设计成不能降级？**

```
一旦升级到重量级锁，就维持在重量级锁，直到释放。

降级的开销可能比维持更高。
```

**Q4: @Async 导致的循环依赖问题？**

```java
@Service
public class A {
    @Autowired
    private B b;
    
    @Async
    public void asyncMethod() { }
}

@Service
public class B {
    @Autowired
    private A a;
}
```

**问题**：`@Async` 会创建代理对象，与循环依赖冲突

**解决方案**：
```java
// 1. 使用 @Lazy
@Autowired
@Lazy
private A a;

// 2. 调整代码结构，避免循环依赖
```

### 最佳实践

```java
// 1. 避免构造器注入产生循环依赖
@Service
public class ServiceA {
    private final ServiceB serviceB;
    
    // 构造器注入不会产生循环依赖（需要通过 setter 配合）
}

// 2. 使用 @Lazy 处理必要的循环依赖
@Service
public class ServiceA {
    private final ServiceB serviceB;
    
    public ServiceA(@Lazy ServiceB serviceB) {
        this.serviceB = serviceB;
    }
}

// 3. 重构代码，消除循环依赖
// 将共享逻辑提取到第三方 Service
@Service
public class SharedService { }

@Service
public class ServiceA {
    @Autowired
    private SharedService sharedService;
}

@Service
public class ServiceB {
    @Autowired
    private SharedService sharedService;
}
```

---

**参考链接：**
- [Spring循环依赖与三级缓存-掘金](https://juejin.cn/post/7216153056281411621)
- [Spring如何解决循环依赖-面试鸭](https://www.mianshiya.com/question/1780933295383539714)
