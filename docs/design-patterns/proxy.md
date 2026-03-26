---
layout: default
title: 代理模式（Proxy Pattern）
---
# 代理模式（Proxy Pattern）：静态代理与动态代理详解

> 为其他对象提供一种代理以控制对这个对象的访问

## 🎯 面试重点

- 代理模式的核心思想与应用场景
- 静态代理 vs 动态代理的区别
- JDK 动态代理 vs CGLIB 动态代理
- Spring AOP 如何选择代理方式
- 代理模式与装饰器模式的区别
- Spring 事务的代理实现原理

## 📖 一、代理模式核心思想

### 1.1 什么是代理模式

代理模式（Proxy Pattern）是一种结构型设计模式，**为其他对象提供一种代理以控制对这个对象的访问**。

**核心角色：**

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Client    │──────▶│   Subject   │◀──────│ RealSubject │
└─────────────┘       └─────────────┘       └─────────────┘
                             │
                             │ implements
                             ▼
                      ┌─────────────┐
                      │    Proxy    │
                      └─────────────┘
                      │ - realSubject│
                      │ + request()  │
                      └─────────────┘
```

- **Subject（抽象主题）**：定义代理和真实对象的共同接口
- **RealSubject（真实主题）**：定义代理所代表的真实对象
- **Proxy（代理）**：持有真实对象的引用，控制对真实对象的访问

### 1.2 为什么需要代理模式

```java
/**
 * 代理模式的核心价值
 */
public class WhyProxy {
    
    // ❌ 不使用代理：直接调用，无法添加额外逻辑
    public void withoutProxy() {
        UserService userService = new UserService();
        userService.deleteUser(1);  // 无法记录日志、权限校验等
    }
    
    // ✅ 使用代理：在调用前后添加控制逻辑
    public void withProxy() {
        UserService proxy = new UserServiceProxy(new UserService());
        proxy.deleteUser(1);  // 自动添加：日志、权限、事务等
    }
}
```

**代理模式的核心价值：**

| 场景 | 说明 |
|------|------|
| **访问控制** | 控制对对象的访问权限 |
| **延迟加载** | 延迟创建开销大的对象（虚拟代理） |
| **远程访问** | 为远程对象提供本地代理（远程代理） |
| **日志监控** | 记录方法调用信息 |
| **性能优化** | 缓存结果、统计耗时 |
| **事务管理** | Spring 声明式事务 |

### 1.3 代理模式的三种类型

```java
/**
 * 代理模式的三种类型
 */
public class ProxyTypes {
    
    // 1. 远程代理（Remote Proxy）
    // - 为远程对象提供本地代理
    // - 示例：RMI、Dubbo、Feign
    // RPC调用看起来像本地调用
    
    // 2. 虚拟代理（Virtual Proxy）
    // - 延迟创建开销大的对象
    // - 示例：图片懒加载、数据库连接池
    // 只有真正需要时才创建对象
    
    // 3. 保护代理（Protection Proxy）
    // - 控制对对象的访问权限
    // - 示例：权限校验、防火墙
    // 在访问前检查权限
}
```

---

## 📖 二、静态代理

### 2.1 静态代理实现

静态代理：**代理类在编译时就已确定**，由程序员手动编写或工具生成。

```java
/**
 * 静态代理完整示例
 */
public class StaticProxyDemo {
    
    // 1. 定义接口（Subject）
    public interface UserService {
        void addUser(String name);
        void deleteUser(int id);
        String getUser(int id);
    }
    
    // 2. 真实对象（RealSubject）
    public static class UserServiceImpl implements UserService {
        @Override
        public void addUser(String name) {
            System.out.println("添加用户: " + name);
        }
        
        @Override
        public void deleteUser(int id) {
            System.out.println("删除用户: " + id);
        }
        
        @Override
        public String getUser(int id) {
            System.out.println("查询用户: " + id);
            return "User-" + id;
        }
    }
    
    // 3. 代理对象（Proxy）
    public static class UserServiceProxy implements UserService {
        
        private UserService target;  // 持有真实对象引用
        
        public UserServiceProxy(UserService target) {
            this.target = target;
        }
        
        @Override
        public void addUser(String name) {
            before("addUser");
            target.addUser(name);  // 调用真实对象
            after("addUser");
        }
        
        @Override
        public void deleteUser(int id) {
            before("deleteUser");
            target.deleteUser(id);
            after("deleteUser");
        }
        
        @Override
        public String getUser(int id) {
            before("getUser");
            String result = target.getUser(id);
            after("getUser");
            return result;
        }
        
        private void before(String method) {
            System.out.println("[Proxy] before " + method);
        }
        
        private void after(String method) {
            System.out.println("[Proxy] after " + method);
        }
    }
    
    // 4. 使用示例
    public static void main(String[] args) {
        UserService target = new UserServiceImpl();
        UserService proxy = new UserServiceProxy(target);
        
        proxy.addUser("张三");
        System.out.println("---");
        proxy.getUser(1);
    }
}
```

**输出结果：**

```
[Proxy] before addUser
添加用户: 张三
[Proxy] after addUser
---
[Proxy] before getUser
查询用户: 1
[Proxy] after getUser
```

### 2.2 静态代理的优缺点

```java
/**
 * 静态代理的优缺点分析
 */
public class StaticProxyAnalysis {
    
    // ✅ 优点：
    // 1. 代码直观易懂，便于理解代理模式
    // 2. 在不修改目标对象的前提下扩展功能
    // 3. 代理对象可以控制对目标对象的访问
    
    // ❌ 缺点：
    // 1. 代理类和目标类实现相同接口，接口增加方法时代理类也要修改
    // 2. 每个目标类都需要单独编写代理类，代码冗余
    // 3. 一个代理类只能代理一个目标类，扩展性差
    
    public void example() {
        // 如果有 10 个 Service，就需要写 10 个 Proxy 类
        UserService userProxy = new UserServiceProxy(new UserServiceImpl());
        OrderService orderProxy = new OrderServiceProxy(new OrderServiceImpl());
        ProductService productProxy = new ProductServiceProxy(new ProductServiceImpl());
        // ... 代码爆炸
    }
}
```

**静态代理的问题本质：**

```
接口变化 → 所有实现类都要修改（包括代理类）
新增目标类 → 需要新增对应的代理类
代理逻辑相同 → 代理类代码重复
```

---

## 📖 三、动态代理

动态代理：**代理类在运行时动态生成**，无需手动编写代理类。

### 3.1 JDK 动态代理

JDK 动态代理：使用 `java.lang.reflect.Proxy` 类和 `InvocationHandler` 接口实现。

```java
/**
 * JDK 动态代理实现
 * 核心类：Proxy + InvocationHandler
 */
public class JdkProxyDemo {
    
    // 1. 定义接口
    public interface UserService {
        void addUser(String name);
        void deleteUser(int id);
    }
    
    // 2. 目标类实现接口（JDK 动态代理要求目标类必须实现接口）
    public static class UserServiceImpl implements UserService {
        @Override
        public void addUser(String name) {
            System.out.println("添加用户: " + name);
        }
        
        @Override
        public void deleteUser(int id) {
            System.out.println("删除用户: " + id);
        }
    }
    
    // 3. 实现 InvocationHandler 接口
    public static class LogInvocationHandler implements InvocationHandler {
        
        private Object target;  // 目标对象
        
        public LogInvocationHandler(Object target) {
            this.target = target;
        }
        
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            // 前置通知
            System.out.println("[JDK Proxy] 方法执行前: " + method.getName());
            long start = System.currentTimeMillis();
            
            // 执行目标方法
            Object result = method.invoke(target, args);
            
            // 后置通知
            long end = System.currentTimeMillis();
            System.out.println("[JDK Proxy] 方法执行后: " + method.getName() + 
                             ", 耗时: " + (end - start) + "ms");
            
            return result;
        }
    }
    
    // 4. 创建代理对象
    public static void main(String[] args) {
        // 目标对象
        UserService target = new UserServiceImpl();
        
        // 创建代理对象
        UserService proxy = (UserService) Proxy.newProxyInstance(
            target.getClass().getClassLoader(),  // 类加载器
            target.getClass().getInterfaces(),   // 目标类实现的接口
            new LogInvocationHandler(target)     // InvocationHandler
        );
        
        // 调用代理方法
        proxy.addUser("李四");
        proxy.deleteUser(1);
        
        // 查看代理类信息
        System.out.println("\n代理类名称: " + proxy.getClass().getName());
        System.out.println("代理类父类: " + proxy.getClass().getSuperclass().getName());
    }
}
```

**输出结果：**

```
[JDK Proxy] 方法执行前: addUser
添加用户: 李四
[JDK Proxy] 方法执行后: addUser, 耗时: 1ms
[JDK Proxy] 方法执行前: deleteUser
删除用户: 1
[JDK Proxy] 方法执行后: deleteUser, 耗时: 0ms

代理类名称: com.sun.proxy.$Proxy0
代理类父类: java.lang.reflect.Proxy
```

### 3.2 JDK 动态代理原理

```java
/**
 * JDK 动态代理原理分析
 */
public class JdkProxyPrinciple {
    
    public void analysis() {
        // Proxy.newProxyInstance 内部做了什么？
        
        // 1. 生成代理类的字节码
        //    - 代理类继承 java.lang.reflect.Proxy
        //    - 实现目标类所实现的所有接口
        //    - 每个方法内部调用 InvocationHandler.invoke()
        
        // 2. 加载代理类
        //    - 使用传入的 ClassLoader 加载生成的代理类
        
        // 3. 创建代理类实例
        //    - 通过反射调用代理类的构造方法
        //    - 将 InvocationHandler 传入代理类
        
        // 生成的代理类大致结构：
        /*
        public final class $Proxy0 extends Proxy implements UserService {
            
            private static Method m1;  // addUser 方法
            private static Method m2;  // deleteUser 方法
            
            public $Proxy0(InvocationHandler h) {
                super(h);  // 调用 Proxy 的构造方法
            }
            
            public void addUser(String name) {
                try {
                    // 调用 InvocationHandler.invoke()
                    super.h.invoke(this, m1, new Object[]{name});
                } catch (Throwable t) {
                    // 异常处理
                }
            }
            
            public void deleteUser(int id) {
                try {
                    super.h.invoke(this, m2, new Object[]{id});
                } catch (Throwable t) {
                    // 异常处理
                }
            }
        }
        */
    }
    
    // JDK 动态代理的限制
    public void limitations() {
        // ❌ 目标类必须实现至少一个接口
        // ❌ 只能代理接口方法，不能代理类方法
        
        // 原因：代理类已经继承了 Proxy，Java 不支持多继承
        // 只能通过实现接口的方式来代理
    }
}
```

### 3.3 CGLIB 动态代理

CGLIB（Code Generation Library）：通过**继承**目标类实现动态代理，无需接口。

```java
/**
 * CGLIB 动态代理实现
 * 需要依赖：cglib 包
 * 核心类：Enhancer + MethodInterceptor
 */
public class CglibProxyDemo {
    
    // 1. 目标类（无需实现接口）
    public static class UserService {
        
        public void addUser(String name) {
            System.out.println("添加用户: " + name);
        }
        
        public void deleteUser(int id) {
            System.out.println("删除用户: " + id);
        }
        
        // final 方法不能被代理（无法被子类重写）
        public final void finalMethod() {
            System.out.println("final 方法不能被代理");
        }
        
        // static 方法不能被代理（不参与继承）
        public static void staticMethod() {
            System.out.println("static 方法不能被代理");
        }
    }
    
    // 2. 实现 MethodInterceptor 接口
    public static class LogMethodInterceptor implements MethodInterceptor {
        
        @Override
        public Object intercept(Object obj, Method method, Object[] args, 
                                MethodProxy proxy) throws Throwable {
            // 前置通知
            System.out.println("[CGLIB Proxy] 方法执行前: " + method.getName());
            long start = System.currentTimeMillis();
            
            // 执行目标方法（使用 MethodProxy 避免递归调用）
            Object result = proxy.invokeSuper(obj, args);
            
            // 后置通知
            long end = System.currentTimeMillis();
            System.out.println("[CGLIB Proxy] 方法执行后: " + method.getName() + 
                             ", 耗时: " + (end - start) + "ms");
            
            return result;
        }
    }
    
    // 3. 创建代理对象
    public static void main(String[] args) {
        // 创建 Enhancer 对象
        Enhancer enhancer = new Enhancer();
        
        // 设置父类（目标类）
        enhancer.setSuperclass(UserService.class);
        
        // 设置回调（MethodInterceptor）
        enhancer.setCallback(new LogMethodInterceptor());
        
        // 创建代理对象
        UserService proxy = (UserService) enhancer.create();
        
        // 调用代理方法
        proxy.addUser("王五");
        proxy.deleteUser(1);
        
        // 查看代理类信息
        System.out.println("\n代理类名称: " + proxy.getClass().getName());
        System.out.println("代理类父类: " + proxy.getClass().getSuperclass().getName());
    }
}
```

**输出结果：**

```
[CGLIB Proxy] 方法执行前: addUser
添加用户: 王五
[CGLIB Proxy] 方法执行后: addUser, 耗时: 0ms
[CGLIB Proxy] 方法执行前: deleteUser
删除用户: 1
[CGLIB Proxy] 方法执行后: deleteUser, 耗时: 0ms

代理类名称: com.example.UserService$$EnhancerByCGLIB$$12345678
代理类父类: com.example.UserService
```

### 3.4 CGLIB 动态代理原理

```java
/**
 * CGLIB 动态代理原理分析
 */
public class CglibProxyPrinciple {
    
    public void analysis() {
        // CGLIB 内部做了什么？
        
        // 1. 生成代理类的字节码
        //    - 代理类继承目标类
        //    - 重写所有非 final 方法
        //    - 每个方法内部调用 MethodInterceptor.intercept()
        
        // 2. FastClass 机制
        //    - 为代理类和目标类各生成一个 FastClass
        //    - FastClass 通过索引定位方法，比反射更快
        
        // 生成的代理类大致结构：
        /*
        public class UserService$$EnhancerByCGLIB$$12345678 extends UserService {
            
            private MethodInterceptor CGLIB$CALLBACK_0;
            
            // 重写父类方法
            @Override
            public void addUser(String name) {
                MethodInterceptor interceptor = CGLIB$CALLBACK_0;
                if (interceptor != null) {
                    // 调用 MethodInterceptor.intercept()
                    interceptor.intercept(this, method, args, proxy);
                } else {
                    super.addUser(name);
                }
            }
            
            @Override
            public void deleteUser(int id) {
                // 类似 addUser
            }
        }
        */
    }
    
    // CGLIB 的限制
    public void limitations() {
        // ❌ 不能代理 final 类（无法继承）
        // ❌ 不能代理 final 方法（无法重写）
        // ❌ 不能代理 static 方法（不参与继承）
        // ❌ 不能代理 private 方法（子类不可见）
    }
}
```

### 3.5 JDK vs CGLIB 对比

```java
/**
 * JDK 动态代理 vs CGLIB 动态代理
 */
public class ProxyCompare {
    
    /*
    ┌──────────────────┬─────────────────────────┬─────────────────────────┐
    │      特性         │     JDK 动态代理         │     CGLIB 动态代理       │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 实现原理          │ 接口实现                 │ 类继承                  │
    │ 是否需要接口       │ ✅ 必须实现接口          │ ❌ 无需接口              │
    │ 代理方式          │ 代理接口方法             │ 代理类方法（重写）        │
    │ 生成代理类         │ 实现接口                 │ 继承目标类               │
    │ final 限制        │ 无                       │ ❌ 不能代理 final        │
    │ 性能（JDK8 之前）  │ 较慢                     │ 较快                    │
    │ 性能（JDK8 之后）  │ 优化后接近 CGLIB         │ 较快                    │
    │ 生成代理类速度     │ 快                       │ 慢（生成 FastClass）      │
    │ 依赖              │ JDK 内置                 │ 需要引入 cglib 依赖      │
    │ Spring 默认       │ ✅ 有接口时使用          │ 无接口时使用             │
    └──────────────────┴─────────────────────────┴─────────────────────────┘
    */
}
```

---

## 📖 四、Spring AOP 与代理模式

### 4.1 Spring AOP 核心概念

```java
/**
 * Spring AOP 核心概念
 */
public class SpringAopConcepts {
    
    /*
    ┌─────────────────────────────────────────────────────────────┐
    │                      Spring AOP 术语                         │
    ├────────────────┬────────────────────────────────────────────┤
    │    JoinPoint   │ 连接点，程序执行的某个位置（方法调用、异常抛出）  │
    │                │ Spring AOP 中指方法的执行点                 │
    ├────────────────┼────────────────────────────────────────────┤
    │    Pointcut    │ 切入点，用于匹配连接点的谓词表达式            │
    │                │ 例如：execution(* com.example.service.*.*(..)) │
    ├────────────────┼────────────────────────────────────────────┤
    │     Advice     │ 通知/增强，拦截到连接点后执行的代码           │
    │                │ Before、After、AfterReturning、AfterThrowing │
    │                │ Around                                      │
    ├────────────────┼────────────────────────────────────────────┤
    │     Target     │ 目标对象，被代理的真实对象                    │
    ├────────────────┼────────────────────────────────────────────┤
    │    Weaving     │ 织入，将通知/增强应用到目标对象的过程          │
    │                │ 编译时织入、类加载时织入、运行时织入           │
    │                │ Spring AOP 使用运行时织入                    │
    ├────────────────┼────────────────────────────────────────────┤
    │     Aspect     │ 切面，Pointcut 和 Advice 的结合             │
    │                │ 告诉 AOP 在哪里做、做什么                    │
    └────────────────┴────────────────────────────────────────────┘
    
    通知类型（Advice Type）：
    ┌────────────────────┬─────────────────────────────────────────┐
    │       类型          │              说明                       │
    ├────────────────────┼─────────────────────────────────────────┤
    │ Before             │ 方法执行前执行                            │
    │ After              │ 方法执行后执行（无论是否异常）             │
    │ AfterReturning     │ 方法正常返回后执行                        │
    │ AfterThrowing      │ 方法抛出异常后执行                        │
    │ Around             │ 包围方法执行，可决定是否调用目标方法      │
    └────────────────────┴─────────────────────────────────────────┘
    */
}
```

### 4.2 Spring AOP 代理选择策略

```java
/**
 * Spring AOP 如何选择代理方式
 */
public class SpringProxyStrategy {
    
    public void analysis() {
        // Spring AOP 的代理选择规则：
        
        // 1. 如果目标类实现了接口
        //    → 默认使用 JDK 动态代理
        //    → 生成实现相同接口的代理类
        
        // 2. 如果目标类没有实现接口
        //    → 使用 CGLIB 动态代理
        //    → 生成继承目标类的代理类
        
        // 3. 配置强制使用 CGLIB
        //    → <aop:aspectj-autoproxy proxy-target-class="true" />
        //    → @EnableAspectJAutoProxy(proxyTargetClass = true)
        
        /*
        原理源码（Spring 5.x）：
        
        // DefaultAopProxyFactory.createAopProxy()
        public AopProxy createAopProxy(AdvisedSupport config) {
            // 配置了强制使用 CGLIB 或者没有实现接口
            if (config.isProxyTargetClass() || 
                hasNoUserSuppliedProxyInterfaces(config)) {
                return new CglibAopProxy(config);
            }
            // 否则使用 JDK 动态代理
            return new JdkDynamicAopProxy(config);
        }
        */
    }
    
    // Spring Boot 2.x 开始，默认 proxyTargetClass = true
    // 即默认使用 CGLIB 代理
    public void springBootDefault() {
        // Spring Boot 2.x+
        // 默认使用 CGLIB 代理（proxyTargetClass = true）
        
        // Spring Boot 1.x
        // 默认使用 JDK 动态代理（有接口时）
    }
}
```

### 4.3 Spring 事务的代理实现

```java
/**
 * Spring 声明式事务的代理实现原理
 */
public class TransactionProxyDemo {
    
    // 1. 开启事务注解
    // @Transactional
    public void transactionExample() {
        // Spring 会为带有 @Transactional 的方法创建代理
        // 在方法调用前后自动开启/提交/回滚事务
    }
    
    // 2. TransactionInterceptor 内部实现
    public void internalImplementation() {
        /*
        // TransactionInterceptor.invoke() 伪代码
        public Object invoke(MethodInvocation invocation) {
            // 1. 获取事务属性
            TransactionAttributeSource tas = getTransactionAttributeSource();
            TransactionAttribute ta = tas.getTransactionAttribute(
                invocation.getMethod(), invocation.getTargetClass()
            );
            
            // 2. 获取或创建事务
            TransactionInfo info = createTransactionIfNecessary(ta);
            
            try {
                // 3. 执行目标方法
                Object retVal = invocation.proceed();
                
                // 4. 提交事务
                commitTransactionAfterReturning(info);
                return retVal;
                
            } catch (Throwable ex) {
                // 5. 回滚事务
                rollbackTransactionOnThrowable(info, ex);
                throw ex;
            } finally {
                // 6. 清理事务信息
                cleanupTransactionInfo(info);
            }
        }
        */
    }
    
    // 3. DataSourceTransactionManager 核心方法
    public void transactionManager() {
        /*
        // 数据源事务管理器的核心操作
        
        // 获取连接
        Connection con = dataSource.getConnection();
        
        // 设置手动提交
        con.setAutoCommit(false);
        
        try {
            // 执行 SQL
            statement.execute(sql);
            
            // 提交
            con.commit();
            
        } catch (Exception e) {
            // 回滚
            con.rollback();
            
        } finally {
            con.close();
        }
        */
    }
    
    // 4. 事务传播行为
    public void propagation() {
        /*
        // @Transactional 的 propagation 属性
        
        REQUIRED      - 如果当前有事务，加入该事务（默认）
        REQUIRES_NEW  - 开启新事务，挂起当前事务
        SUPPORTS      - 如果当前有事务，加入该事务；否则无事务
        MANDATORY     - 必须在事务中执行，否则抛异常
        NOT_SUPPORTED - 无事务执行，挂起当前事务
        NEVER         - 必须无事务，否则抛异常
        NESTED        - 嵌套事务（ Savepoint ）
        */
    }
    
    // 5. 事务失效场景
    public void transactionFailure() {
        /*
        ⚠️ 事务可能失效的场景：
        
        1. 方法内部调用（自调用）
        ┌──────────────────────────────────────────────────┐
        │ @Service                                          │
        │ public class UserService {                        │
        │     public void methodA() {                       │
        │         // ❌ this.methodB() 不会走代理           │
        │         this.methodB();  // 事务不生效            │
        │     }                                             │
        │                                                   │
        │     @Transactional                                │
        │     public void methodB() { ... }                 │
        │ }                                                 │
        └──────────────────────────────────────────────────┘
        解决：从代理对象调用，或使用 AspectJ 编译时织入
        
        2. 非 public 方法
        ┌──────────────────────────────────────────────────┐
        │ @Transactional                                    │
        │ private void method() { ... }  // ❌ 事务不生效   │
        └──────────────────────────────────────────────────┘
        解决：改为 public 方法
        
        3. 异常被 catch 吞掉
        ┌──────────────────────────────────────────────────┐
        │ @Transactional                                    │
        │ public void method() {                           │
        │     try { ... } catch { /* 不抛异常 */ }         │
        │ }                                                │
        └──────────────────────────────────────────────────┘
        解决：不捕获异常，或手动回滚（TransactionInterceptor.currentTransactionStatus().setRollbackOnly()）
        
        4. 异常类型不匹配
        ┌──────────────────────────────────────────────────┐
        │ @Transactional(rollbackFor = Exception.class)    │
        │ public void method() throws IOException {        │
        │     throw new IOException(); // ❌ 默认不回滚     │
        │ }                                                │
        └──────────────────────────────────────────────────┘
        解决：指定 rollbackFor = IOException.class
        
        5. 异常被内层事务吞掉
        ┌──────────────────────────────────────────────────┐
        │ @Service A {                                     │
        │     @Transactional                               │
        │     public void a() {                            │
        │         b();  // b() 抛异常被 a() 捕获           │
        │     }                                             │
        │                                                   │
        │     @Transactional                               │
        │     public void b() { throw new RuntimeException(); }
        │ }                                                │
        └──────────────────────────────────────────────────┘
        */
    }
}
```

---

## 📖 五、代理模式 vs 装饰器模式

### 5.1 核心区别

```java
/**
 * 代理模式 vs 装饰器模式
 */
public class ProxyVsDecorator {
    
    /*
    ┌──────────────────┬─────────────────────────┬─────────────────────────┐
    │      维度         │      代理模式             │     装饰器模式           │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 设计目的          │ 控制对对象的访问          │ 给对象动态添加职责        │
    │                   │ （不修改）               │ （增强）                 │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 代码形式          │ 代理类持有真实对象引用    │ 装饰器类持有对象引用      │
    │                   │ 调用时控制访问           │ 调用时添加额外行为        │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 客户端感知        │ 客户端可能不知道代理存在  │ 客户端知道被装饰了        │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 典型场景          │ 远程代理、虚拟代理        │ I/O 流、缓冲输出流        │
    │                   │ 安全代理、延迟加载        │ BufferedInputStream      │
    ├──────────────────┼─────────────────────────┼─────────────────────────┤
    │ 实现方式          │ 组合（持有引用）          │ 组合（持有引用）          │
    └──────────────────┴─────────────────────────┴─────────────────────────┘
    
    本质上两者都是"组合"模式，只是目的不同：
    - 代理模式：控制访问，客户端可能不知道代理存在
    - 装饰器模式：增强功能，客户端知道被装饰了
    
    在 Java 中，两者的实现几乎一样！
    关键区别在于语义和使用场景。
    */
    
    // 装饰器模式示例（Java I/O）
    public void ioDecorator() {
        /*
        // BufferedInputStream 就是装饰器模式
        FileInputStream fis = new FileInputStream("test.txt");
        BufferedInputStream bis = new BufferedInputStream(fis);
        DataInputStream dis = new DataInputStream(bis);
        
        // 一层层包装，层层增强功能：
        // FileInputStream    → 文件读取
        // BufferedInputStream → 缓冲读取
        // DataInputStream    → 数据类型转换
        
        // 客户端知道所有装饰器的存在
        // 目的是增强，不是控制访问
        */
    }
    
    // 代理模式示例
    public void proxyExample() {
        /*
        // 虚拟代理：延迟加载大图片
        Image image = new LargeImageProxy("big.jpg");
        // 此时还没有加载图片，只是创建了代理
        
        image.display();  // 第一次调用时才真正加载
        
        // 客户端可能不知道背后是代理在加载
        // 目的是控制访问（延迟加载）
        */
    }
}
```

---

## 📖 六、实际应用场景

### 6.1 性能监控

```java
/**
 * 性能监控代理
 */
public class PerformanceMonitorProxy {
    
    // 动态代理实现
    public static Object createPerformanceProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                long start = System.nanoTime();
                Object result = method.invoke(target, args);
                long end = System.nanoTime();
                
                System.out.printf("[Performance] %s.%s() 耗时: %.2fms%n",
                    target.getClass().getSimpleName(),
                    method.getName(),
                    (end - start) / 1_000_000.0
                );
                
                return result;
            }
        );
    }
    
    // Spring AOP 实现
    /*
    @Aspect
    @Component
    public class PerformanceAspect {
        
        @Around("execution(* com.example.service.*.*(..))")
        public Object monitor(ProceedingJoinPoint point) throws Throwable {
            long start = System.currentTimeMillis();
            Object result = point.proceed();
            long end = System.currentTimeMillis();
            
            System.out.printf("方法: %s.%s, 耗时: %dms%n",
                point.getTarget().getClass().getSimpleName(),
                point.getSignature().getName(),
                end - start
            );
            
            return result;
        }
    }
    */
}
```

### 6.2 缓存代理

```java
/**
 * 缓存代理
 */
public class CacheProxy {
    
    private static final Map<String, Object> CACHE = new ConcurrentHashMap<>();
    
    public static Object createCacheProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                // 只对查询方法添加缓存
                if (!method.getName().startsWith("get")) {
                    return method.invoke(target, args);
                }
                
                // 生成缓存 key
                String cacheKey = method.getName() + ":" + Arrays.toString(args);
                
                // 命中缓存
                if (CACHE.containsKey(cacheKey)) {
                    System.out.println("[Cache] 命中缓存: " + cacheKey);
                    return CACHE.get(cacheKey);
                }
                
                // 未命中，执行方法并缓存
                Object result = method.invoke(target, args);
                CACHE.put(cacheKey, result);
                System.out.println("[Cache] 写入缓存: " + cacheKey);
                
                return result;
            }
        );
    }
    
    // 缓存清除注解
    /*
    @CacheEvict(value = "users", allEntries = true)
    public void deleteUser(Long id) {
        // 删除用户后自动清除缓存
    }
    */
}
```

### 6.3 远程代理（RPC）

```java
/**
 * 远程代理示例（简化版 RPC）
 */
public class RemoteProxyDemo {
    
    /*
    // Feign 远程调用
    @FeignClient(name = "user-service", url = "http://localhost:8080")
    public interface UserClient {
        @GetMapping("/user/{id}")
        User getUser(@PathVariable Long id);
    }
    
    // 使用时像本地接口一样调用
    @Autowired
    private UserClient userClient;
    
    public void getUser() {
        // 实际是 RPC 调用，但语法像本地调用
        User user = userClient.getUser(1L);
    }
    
    // 原理：Feign 会生成代理类
    // 代理类内部通过 HTTP 客户端调用远程服务
    */
}
```

### 6.4 安全控制

```java
/**
 * 安全控制代理
 */
public class SecurityProxy {
    
    public static Object createSecurityProxy(Object target) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            (proxy, method, args) -> {
                // 获取方法上的权限注解
                RequiresPermissions annotation = 
                    method.getAnnotation(RequiresPermissions.class);
                
                if (annotation != null) {
                    String[] permissions = annotation.value();
                    
                    // 检查用户权限
                    if (!hasPermissions(permissions)) {
                        throw new SecurityException("没有权限访问: " + method.getName());
                    }
                }
                
                return method.invoke(target, args);
            }
        );
    }
    
    private static boolean hasPermissions(String[] permissions) {
        // 实际应从 SecurityManager 获取当前用户权限
        // 这里简化处理
        return true;
    }
    
    // 使用注解
    /*
    public interface UserService {
        @RequiresPermissions("user:delete")
        void deleteUser(Long id);
        
        @RequiresPermissions("user:create")
        void createUser(User user);
    }
    */
}
```

---

## 📖 七、高频面试题

### Q1: JDK 动态代理和 CGLIB 有什么区别？

**答：**

| 区别 | JDK 动态代理 | CGLIB 动态代理 |
|------|------------|--------------|
| **实现原理** | 实现接口 | 继承类 |
| **是否需要接口** | 必须实现接口 | 不需要接口 |
| **生成方式** | Proxy.newProxyInstance | Enhancer.create |
| **代理类** | 继承 Proxy | 继承目标类 |
| **性能** | JDK8+ 优化后接近 CGLIB | 较快（有 FastClass） |
| **final 限制** | 无 | 不能代理 final 方法/类 |
| **Spring 默认** | 有接口时使用 | 无接口时使用 |

**追问：Spring 为什么默认用 JDK 代理？**

答：早期 JDK 动态代理性能差，Spring 默认用 CGLIB。Spring Boot 2.x 后默认 `proxyTargetClass=true`，强制使用 CGLIB，这样可以代理任何类而不限于接口。

---

### Q2: Spring AOP 的织入方式有哪几种？

**答：**

| 织入方式 | 说明 | 特点 |
|---------|------|------|
| **编译时织入** | 在编译时将切面织入字节码 | 需要特殊编译器（如 AspectJ） |
| **类加载时织入** | 在类加载时织入 | 需要 Java Agent |
| **运行时织入** | 在运行时创建代理 | Spring AOP 使用这种方式 |

Spring AOP 使用**运行时织入**，通过代理模式：
- JDK 动态代理：生成实现接口的代理类
- CGLIB 代理：生成继承目标类的代理类

**追问：运行时织入和编译时织入哪个性能更好？**

答：编译时织入性能更好，因为不需要在运行时生成字节码。但 Spring 选择运行时织入是为了保持简单性和灵活性，无需特殊编译器。

---

### Q3: 代理模式和装饰器模式有什么区别？

**答：**

**核心区别：**

| 维度 | 代理模式 | 装饰器模式 |
|------|---------|-----------|
| **目的** | 控制对对象的访问 | 给对象动态增加职责 |
| **客户端** | 可能不知道代理存在 | 明确知道被装饰 |
| **实现** | 几乎一样（组合+委托） | 几乎一样（组合+委托） |
| **典型场景** | 远程代理、虚拟代理、安全代理 | I/O 流包装 |

**本质：** 两者都是"结构型组合模式"，代码实现几乎相同，区别在于语义和使用目的。

**举例：**
- 代理模式：VPN 代理，客户以为在访问目标，实际是代理转发
- 装饰器模式：给咖啡加糖、加奶、加奶、加可可——层层叠加，咖啡本身没变，但功能增强了。

---

### Q4: `@Transactional` 事务注解在哪些情况下会失效？

**答：**

| 失效场景 | 原因 | 解决方案 |
|---------|------|---------|
| **方法内部调用** | 自调用不走代理 | 从代理对象调用或用 AspectJ |
| **非 public 方法** | Spring AOP 只支持 public 方法 | 改为 public 方法 |
| **异常被 catch** | 没有异常传播到代理层 | 重新抛出或手动回滚 |
| **异常类型不匹配** | 默认只回滚 RuntimeException | 设置 `rollbackFor = Exception.class` |
| **同类相互调用** | 同一个类中方法调用不走代理 | 使用 `self` 注入自己 |

**代码示例：**

```java
@Service
public class UserService {
    
    // ❌ 失效：内部调用不走代理
    public void methodA() {
        this.methodB();  // 不走代理，事务无效
    }
    
    @Transactional
    public void methodB() {
        // 事务无效
    }
    
    // ✅ 正确：注入自己，从代理对象调用
    @Autowired
    private UserService self;
    
    public void methodA() {
        self.methodB();  // 走代理，事务有效
    }
}
```

---

### Q5: Spring Boot 如何配置强制使用 CGLIB 代理？

**答：**

**方式一：注解配置（推荐）**

```java
@EnableAspectJAutoProxy(proxyTargetClass = true)
// proxyTargetClass = true  → 强制使用 CGLIB 代理
// proxyTargetClass = false → 优先使用 JDK 动态代理
```

**方式二：配置文件**

```yaml
spring:
  aop:
    proxy-target-class: true
```

**方式三：Spring Boot 默认行为**

Spring Boot 2.x 开始默认 `proxyTargetClass = true`，自动使用 CGLIB 代理。

**源码分析：**

```java
// DefaultAopProxyFactory.java
public AopProxy createAopProxy(AdvisedSupport config) {
    // 配置了 proxy-target-class="true" 或 没有实现接口
    if (config.isProxyTargetClass() || 
        hasNoUserSuppliedProxyInterfaces(config)) {
        
        if (targetClass.isInterface() || 
            Proxy.isProxyClass(targetClass)) {
            // 即使配置了 CGLIB，如果目标类是接口也用 JDK
            return new JdkDynamicAopProxy(config);
        }
        // 使用 CGLIB
        return new CglibAopProxy(config);
    }
    // 否则使用 JDK 动态代理
    return new JdkDynamicAopProxy(config);
}
```

---

## ⭐ 面试总结

### 核心要点速记

```
1. 代理模式 = 控制访问 + 组合委托
2. 静态代理：编译时确定，代码冗余
3. JDK 动态代理：必须实现接口，Proxy + InvocationHandler
4. CGLIB 动态代理：继承方式，Enhancer + MethodInterceptor
5. Spring AOP：有接口用 JDK，无接口用 CGLIB（Spring Boot 默认 CGLIB）
6. 织入方式：Spring AOP 用运行时织入
7. 事务失效：自调用、非 public、异常被吞
8. 代理 vs 装饰器：目的不同（控制 vs 增强）
```

### 面试加分项

- 了解 Spring AOP 和 AspectJ 的区别
- 知道 CGLIB 的 FastClass 机制
- 能画出示意图解释代理原理
- 了解事务传播行为的 7 种类型
- 知道 Spring 事务的隔离级别配置

---

**⭐ 重点：代理模式是 Spring AOP 的核心基础，必须掌握！**
