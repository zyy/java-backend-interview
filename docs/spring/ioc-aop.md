---
layout: default
title: Spring IoC 与 AOP 原理 ⭐⭐⭐
---
# Spring IoC 与 AOP 原理 ⭐⭐⭐

## 面试题：说说你对 Spring IoC 和 AOP 的理解

### 核心回答

**IoC（控制反转）**和 **AOP（面向切面编程）**是 Spring 框架的两大核心特性，分别解决**对象依赖管理**和**横切关注点复用**问题。

---

## 一、IoC（控制反转 / 依赖注入）

### 什么是 IoC？

**控制反转（Inversion of Control）**：将对象的创建和依赖关系的管理交给 Spring 容器，而不是由开发者手动创建。

**传统方式 vs IoC 方式**：

```java
// 传统方式：手动创建对象，耦合度高
public class UserService {
    private UserDao userDao = new UserDaoImpl();  // 强耦合
}

// IoC 方式：依赖注入，解耦
public class UserService {
    @Autowired
    private UserDao userDao;  // 由 Spring 容器注入
}
```

### IoC 的实现原理

**核心技术**：反射 + 工厂模式 + 配置文件/注解

```java
// 简化版 IoC 容器实现思路
public class SimpleIoCContainer {
    private Map<String, Object> beanMap = new ConcurrentHashMap<>();
    
    // 1. 扫描并注册 Bean 定义
    public void registerBean(Class<?> clazz) {
        String beanName = clazz.getSimpleName();
        Object instance = clazz.newInstance();
        beanMap.put(beanName, instance);
    }
    
    // 2. 依赖注入
    public void injectDependencies() {
        for (Object bean : beanMap.values()) {
            for (Field field : bean.getClass().getDeclaredFields()) {
                if (field.isAnnotationPresent(Autowired.class)) {
                    Object dependency = beanMap.get(field.getType().getSimpleName());
                    field.setAccessible(true);
                    field.set(bean, dependency);
                }
            }
        }
    }
}
```

### IoC 容器体系

```
BeanFactory（基础容器）
    └── ApplicationContext（高级容器）
            ├── ClassPathXmlApplicationContext
            ├── FileSystemXmlApplicationContext
            └── AnnotationConfigApplicationContext
```

**BeanFactory vs ApplicationContext**：

| 特性 | BeanFactory | ApplicationContext |
|------|-------------|-------------------|
| 加载时机 | 懒加载（使用时才创建） | 预加载（启动时创建） |
| 功能 | 基础功能 | 完整功能（AOP、国际化、事件等） |
| 适用场景 | 资源受限环境 | 企业级应用 |

### Bean 的生命周期

```
1. 实例化（Instantiation）
    ↓ 调用构造方法
2. 属性赋值（Populate）
    ↓ 依赖注入
3. 初始化（Initialization）
    ↓ 调用初始化方法
4. 使用（In Use）
    ↓ 
5. 销毁（Destruction）
    ↓ 调用销毁方法
```

**扩展点**：
```java
// 1. BeanNameAware - 获取 Bean 名称
public void setBeanName(String name) {}

// 2. BeanFactoryAware - 获取 BeanFactory
public void setBeanFactory(BeanFactory beanFactory) {}

// 3. InitializingBean - 初始化逻辑
public void afterPropertiesSet() {}

// 4. @PostConstruct - JSR-250 标准
@PostConstruct
public void init() {}

// 5. DisposableBean - 销毁逻辑
public void destroy() {}

// 6. @PreDestroy - JSR-250 标准
@PreDestroy
public void cleanup() {}
```

### 依赖注入的三种方式

```java
// 1. 构造器注入（推荐）
@Service
public class UserService {
    private final UserDao userDao;
    
    @Autowired  // Spring 4.3+ 可省略
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}

// 2. Setter 注入
@Service
public class UserService {
    private UserDao userDao;
    
    @Autowired
    public void setUserDao(UserDao userDao) {
        this.userDao = userDao;
    }
}

// 3. 字段注入（不推荐）
@Service
public class UserService {
    @Autowired
    private UserDao userDao;
}
```

**推荐顺序**：构造器注入 > Setter 注入 > 字段注入

---

## 二、AOP（面向切面编程）

### 什么是 AOP？

**面向切面编程（Aspect-Oriented Programming）**：将横切关注点（日志、事务、权限等）从业务逻辑中分离出来，实现模块化。

**核心概念**：

| 概念 | 说明 | 类比 |
|------|------|------|
| Aspect（切面） | 横切关注点的模块化 | 一个功能模块 |
| Join Point（连接点） | 程序执行点（方法、异常等） | 具体的方法 |
| Pointcut（切点） | 匹配连接点的表达式 | 方法筛选条件 |
| Advice（通知） | 切面的具体动作 | 具体执行逻辑 |
| Target（目标对象） | 被代理的对象 | 原始对象 |
| Proxy（代理） | 生成的代理对象 | 包装后的对象 |

### AOP 的实现原理

**基于动态代理**：
- **JDK 动态代理**：目标类实现接口时使用
- **CGLIB 代理**：目标类没有实现接口时使用

```java
// JDK 动态代理示例
public class JdkProxyDemo {
    public static Object createProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                System.out.println("前置通知");
                Object result = method.invoke(target, args);
                System.out.println("后置通知");
                return result;
            }
        );
    }
}

// CGLIB 代理示例
public class CglibProxyDemo implements MethodInterceptor {
    public Object createProxy(Class<?> targetClass) {
        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(targetClass);
        enhancer.setCallback(this);
        return enhancer.create();
    }
    
    @Override
    public Object intercept(Object obj, Method method, Object[] args, MethodProxy proxy) {
        System.out.println("前置通知");
        Object result = proxy.invokeSuper(obj, args);
        System.out.println("后置通知");
        return result;
    }
}
```

### Spring AOP 的执行流程

```
1. 创建 Bean 实例
    ↓
2. 判断是否需要 AOP 代理（匹配 Pointcut）
    ↓ 是
3. 选择代理策略（JDK / CGLIB）
    ↓
4. 创建代理对象
    ↓
5. 调用目标方法时，执行 Advice 链
```

### 通知类型

```java
@Aspect
@Component
public class LogAspect {
    
    // 前置通知
    @Before("execution(* com.service.*.*(..))")
    public void before(JoinPoint joinPoint) {
        System.out.println("方法执行前: " + joinPoint.getSignature().getName());
    }
    
    // 后置通知（无论是否异常都执行）
    @After("execution(* com.service.*.*(..))")
    public void after() {
        System.out.println("方法执行后");
    }
    
    // 返回通知（方法正常返回后执行）
    @AfterReturning(pointcut = "execution(* com.service.*.*(..))", returning = "result")
    public void afterReturning(Object result) {
        System.out.println("方法返回值: " + result);
    }
    
    // 异常通知（方法抛出异常时执行）
    @AfterThrowing(pointcut = "execution(* com.service.*.*(..))", throwing = "ex")
    public void afterThrowing(Exception ex) {
        System.out.println("方法异常: " + ex.getMessage());
    }
    
    // 环绕通知（最强大的通知类型）
    @Around("execution(* com.service.*.*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("环绕前");
        Object result = pjp.proceed();  // 执行目标方法
        System.out.println("环绕后");
        return result;
    }
}
```

### 切点表达式

```java
// execution 表达式语法
execution(修饰符? 返回类型 声明类型? 方法名(参数类型) 异常类型?)

// 示例
@Pointcut("execution(public * com.service.*.*(..))")  // service 包下所有 public 方法
@Pointcut("execution(* com.service.UserService.*(..))")  // UserService 的所有方法
@Pointcut("execution(* com.service..*.*(..))")  // service 包及其子包下的所有方法
@Pointcut("@annotation(com.annotation.Log)")  // 带有 @Log 注解的方法
@Pointcut("within(com.service.*)")  // service 包下的所有类
```

### Spring AOP 的局限性

1. **只能代理 Spring 管理的 Bean**
2. **内部调用不会触发 AOP**（this 调用不走代理）
3. **final 方法不能被代理**
4. **私有方法不能被代理**

**内部调用问题解决**：
```java
@Service
public class UserService {
    @Autowired
    private ApplicationContext context;
    
    public void methodA() {
        // 错误：内部调用不会触发 AOP
        methodB();
        
        // 正确：通过代理对象调用
        UserService proxy = context.getBean(UserService.class);
        proxy.methodB();
    }
    
    @Transactional
    public void methodB() {
        // 事务逻辑
    }
}
```

---

## 高频面试题

**Q0: Spring IoC 和 AOP 的实现原理？**

**IoC（控制反转）的实现原理：**
1. **BeanDefinition**：Spring 将 Bean 的配置信息（类名、作用域、属性等）解析为 BeanDefinition 对象。
2. **BeanFactory**：核心容器接口，负责 Bean 的创建和管理。
3. **ApplicationContext**：BeanFactory 的扩展，提供更多企业级功能（事件发布、国际化等）。
4. **依赖注入**：通过反射或 CGLIB 为 Bean 注入依赖。
5. **生命周期管理**：管理 Bean 的创建、初始化、使用和销毁。

**关键流程**：
```
1. 加载配置 → 2. 解析 BeanDefinition → 3. 注册到 BeanFactory
4. 实例化 Bean → 5. 属性注入 → 6. 初始化 → 7. 使用 → 8. 销毁
```

**AOP（面向切面编程）的实现原理：**
1. **切面（Aspect）**：横切关注点的模块化（如日志、事务）。
2. **连接点（Joinpoint）**：程序执行过程中的特定点（如方法调用）。
3. **通知（Advice）**：在连接点执行的动作（如前置通知、后置通知）。
4. **切点（Pointcut）**：匹配连接点的表达式。
5. **织入（Weaving）**：将切面应用到目标对象的过程。

**实现方式**：
1. **JDK 动态代理**：基于接口，使用 `Proxy.newProxyInstance()` 创建代理。
2. **CGLIB 动态代理**：基于继承，使用 ASM 字节码生成子类。
3. **AspectJ**：编译时或加载时织入，功能更强大。

**Spring AOP 的工作流程**：
```
1. 定义切面（@Aspect）和通知（@Before、@After 等）
2. 配置自动代理（@EnableAspectJAutoProxy）
3. Spring 创建 Bean 时，检查是否需要 AOP 代理
4. 如果需要，创建代理对象（JDK 或 CGLIB）
5. 调用代理对象的方法时，执行切面逻辑
```

**Q1: Spring 如何解决循环依赖？**

Spring 通过**三级缓存**解决单例 Bean 的循环依赖：
- **一级缓存（singletonObjects）**：存放完全初始化好的 Bean
- **二级缓存（earlySingletonObjects）**：存放提前暴露的 Bean（已实例化但未填充属性）
- **三级缓存（singletonFactories）**：存放 Bean 工厂对象

**注意**：构造器注入的循环依赖无法解决，因为实例化阶段就需要依赖对象。

**Q2: JDK 动态代理和 CGLIB 的区别？**

| 特性 | JDK 动态代理 | CGLIB |
|------|-------------|-------|
| 依赖 | 需要实现接口 | 不需要接口 |
| 原理 | 反射 + 接口 | ASM 字节码生成 |
| 性能 | 调用稍慢（反射） | 调用更快（直接调用） |
| 生成速度 | 快 | 慢（需要生成字节码） |
| 限制 | 只能代理接口方法 | 不能代理 final 类和方法 |

**Q3: @Transactional 失效的场景？**
1. 方法不是 public 的
2. 方法内部调用（this 调用）
3. 异常被捕获未抛出
4. 抛出的异常类型不匹配（默认只回滚 RuntimeException）
5. 类未被 Spring 管理

**Q4: Bean 的作用域有哪些？**
- **singleton**（默认）：单例，每个 Spring 容器一个实例
- **prototype**：原型，每次获取都创建新实例
- **request**：每个 HTTP 请求一个实例
- **session**：每个 HTTP Session 一个实例
- **application**：每个 ServletContext 一个实例

---

**参考链接：**
- [Spring IoC AOP 面试回答-Worktile](https://worktile.com/kb/ask/832758.html)
- [Spring AOP 实现原理-图灵课堂](https://www.tulingxueyuan.cn/tlzx/javamst/5637.html)
