---
layout: default
title: Spring Boot 启动流程详解 ⭐⭐⭐
---
# Spring Boot 启动流程详解 ⭐⭐⭐

## 面试题：Spring Boot 是如何启动的？

### 核心回答

Spring Boot 的启动流程从 `SpringApplication.run()` 方法开始，经历环境准备、应用上下文创建、Bean 加载、内嵌服务器启动等多个阶段。整个流程通过 `SpringFactoriesLoader` 实现自动配置，最终完成应用的启动。

## 一、启动入口：SpringApplication.run()

### 1.1 启动方法概览

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 1.2 SpringApplication 构造过程

```java
public SpringApplication(Class<?>... primarySources) {
    this(null, primarySources);
}

public SpringApplication(ResourceLoader resourceLoader, Class<?>... primarySources) {
    this.resourceLoader = resourceLoader;
    Assert.notNull(primarySources, "PrimarySources must not be null");
    this.primarySources = new LinkedHashSet<>(Arrays.asList(primarySources));
    
    // 1. 推断应用类型（Servlet/Reactive/None）
    this.webApplicationType = WebApplicationType.deduceFromClasspath();
    
    // 2. 加载 Bootstrap 上下文初始化器
    this.bootstrapRegistryInitializers = getBootstrapRegistryInitializersFromSpringFactories();
    
    // 3. 加载 ApplicationContextInitializer
    setInitializers((Collection) getSpringFactoriesInstances(ApplicationContextInitializer.class));
    
    // 4. 加载 ApplicationListener
    setListeners((Collection) getSpringFactoriesInstances(ApplicationListener.class));
    
    // 5. 推断主类
    this.mainApplicationClass = deduceMainApplicationClass();
}
```

### 1.3 run() 方法核心流程

```java
public ConfigurableApplicationContext run(String... args) {
    // 0. 记录启动时间
    long startTime = System.nanoTime();
    
    // 1. 创建 Bootstrap 上下文
    DefaultBootstrapContext bootstrapContext = createBootstrapContext();
    
    ConfigurableApplicationContext context = null;
    try {
        // 2. 准备环境
        ConfigurableEnvironment environment = prepareEnvironment(listeners, bootstrapContext, applicationArguments);
        
        // 3. 创建应用上下文
        context = createApplicationContext();
        
        // 4. 准备上下文
        prepareContext(bootstrapContext, context, environment, listeners, applicationArguments, printedBanner);
        
        // 5. 刷新上下文（核心！）
        refreshContext(context);
        
        // 6. 刷新后处理
        afterRefresh(context, applicationArguments);
        
        // 7. 记录启动完成
        Duration timeTakenToStartup = Duration.ofNanos(System.nanoTime() - startTime);
    } catch (Throwable ex) {
        handleRunFailure(context, ex, listeners);
        throw new IllegalStateException(ex);
    }
    return context;
}
```

## 二、准备环境：ConfigurableEnvironment

### 2.1 环境准备流程

```
┌─────────────────────────────────────────────────────────────┐
│                    环境准备流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. createEnvironment()                                     │
│     └── 创建 StandardServletEnvironment                     │
│                                                             │
│  2. configureEnvironment()                                  │
│     ├── 配置 PropertySources                                │
│     └── 添加命令行参数                                       │
│                                                             │
│  3. ConfigurationPropertySources.attach()                   │
│     └── 附加配置属性源                                       │
│                                                             │
│  4. listeners.environmentPrepared()                         │
│     └── 发布 ApplicationEnvironmentPreparedEvent            │
│                                                             │
│  5. bindToSpringApplication()                               │
│     └── 绑定环境到 SpringApplication                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 环境配置加载顺序

```java
// 配置加载优先级（从高到低）
1. 命令行参数
2. JNDI 属性
3. Java 系统属性 (System.getProperties())
4. 操作系统环境变量
5. RandomValuePropertySource (random.*)
6. jar 包外的 application-{profile}.properties/yml
7. jar 包内的 application-{profile}.properties/yml
8. jar 包外的 application.properties/yml
9. jar 包内的 application.properties/yml
10. @PropertySource 注解
11. 默认属性
```

### 2.3 Environment 核心代码

```java
protected ConfigurableEnvironment prepareEnvironment(SpringApplicationRunListeners listeners,
                                                     DefaultBootstrapContext bootstrapContext,
                                                     ApplicationArguments applicationArguments) {
    // 创建环境对象
    ConfigurableEnvironment environment = getOrCreateEnvironment();
    
    // 配置环境
    configureEnvironment(environment, applicationArguments.getSourceArgs());
    
    // 附加配置属性源
    ConfigurationPropertySources.attach(environment);
    
    // 通知监听器环境已准备完成
    listeners.environmentPrepared(bootstrapContext, environment);
    
    // 绑定到 SpringApplication
    bindToSpringApplication(environment);
    
    return environment;
}
```

## 三、创建应用上下文

### 3.1 应用上下文类型推断

```java
protected ConfigurableApplicationContext createApplicationContext() {
    return this.applicationContextFactory.create(this.webApplicationType);
}

// 根据应用类型创建不同的上下文
public enum WebApplicationType {
    NONE,           // 非Web应用
    SERVLET,        // Servlet Web应用
    REACTIVE;       // 响应式Web应用
}

// 类型推断逻辑
static WebApplicationType deduceFromClasspath() {
    if (ClassUtils.isPresent(WEBFLUX_INDICATOR_CLASS, null) 
        && !ClassUtils.isPresent(WEBMVC_INDICATOR_CLASS, null)) {
        return WebApplicationType.REACTIVE;
    }
    for (String className : SERVLET_INDICATOR_CLASSES) {
        if (!ClassUtils.isPresent(className, null)) {
            return WebApplicationType.NONE;
        }
    }
    return WebApplicationType.SERVLET;
}
```

### 3.2 常见应用上下文类型

| 应用类型 | 上下文类 | 说明 |
|---------|---------|------|
| Servlet Web | AnnotationConfigServletWebServerApplicationContext | 传统 Spring MVC |
| Reactive | AnnotationConfigReactiveWebServerApplicationContext | WebFlux |
| Non-Web | AnnotationConfigApplicationContext | 纯后台应用 |

### 3.3 上下文创建流程

```
┌─────────────────────────────────────────────────────────────┐
│                 创建应用上下文流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 根据类型创建上下文实例                                     │
│     AnnotationConfigServletWebServerApplicationContext       │
│     ↓                                                       │
│  2. 注册 BeanFactoryPostProcessor                            │
│     ConfigurationClassPostProcessor                          │
│     AutowiredAnnotationBeanPostProcessor                     │
│     ↓                                                       │
│  3. 设置环境                                                 │
│     context.setEnvironment(environment)                      │
│     ↓                                                       │
│  4. 应用初始化器                                             │
│     applyInitializers(context)                               │
│     ↓                                                       │
│  5. 发布上下文准备事件                                       │
│     ApplicationContextInitializedEvent                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 四、刷新上下文：refresh()

### 4.1 refresh() 核心流程

```java
public void refresh() throws BeansException, IllegalStateException {
    synchronized (this.startupShutdownMonitor) {
        StartupStep contextRefresh = this.applicationStartup.start("spring.context.refresh");

        // 1. 准备刷新：记录启动时间、初始化属性源
        prepareRefresh();

        // 2. 获取 BeanFactory
        ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();

        // 3. 准备 BeanFactory：设置类加载器、添加后置处理器
        prepareBeanFactory(beanFactory);

        try {
            // 4. BeanFactory 后置处理（子类扩展点）
            postProcessBeanFactory(beanFactory);

            StartupStep beanPostProcess = this.applicationStartup.start("spring.context.beans.post-process");

            // 5. 调用 BeanFactoryPostProcessor
            invokeBeanFactoryPostProcessors(beanFactory);

            // 6. 注册 BeanPostProcessor
            registerBeanPostProcessors(beanFactory);

            beanPostProcess.end();

            // 7. 初始化 MessageSource（国际化）
            initMessageSource();

            // 8. 初始化事件广播器
            initApplicationEventMulticaster();

            // 9. 初始化特殊 Bean（子类扩展）
            onRefresh();

            // 10. 注册监听器
            registerListeners();

            // 11. 完成单例 Bean 实例化
            finishBeanFactoryInitialization(beanFactory);

            // 12. 完成刷新：发布事件、清理缓存
            finishRefresh();

        } catch (BeansException ex) {
            destroyBeans();
            cancelRefresh(ex);
            throw ex;
        }
    }
}
```

### 4.2 refresh() 完整流程图

```
┌────────────────────────────────────────────────────────────────────┐
│                    refresh() 完整流程图                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  prepareRefresh()                                                  │
│  ├── 初始化状态标识                                                 │
│  ├── 校验必要属性                                                   │
│  └── 初始化早期监听器                                               │
│     ↓                                                              │
│  obtainFreshBeanFactory()                                          │
│  ├── 刷新 BeanFactory                                              │
│  └── 返回 BeanFactory 实例                                         │
│     ↓                                                              │
│  prepareBeanFactory(beanFactory)                                   │
│  ├── 设置类加载器                                                   │
│  ├── 添加 BeanPostProcessor                                        │
│  └── 注册默认环境 Bean                                              │
│     ↓                                                              │
│  postProcessBeanFactory(beanFactory)                               │
│  └── 子类扩展点（如 WebApplicationContext 注册 Scope）              │
│     ↓                                                              │
│  invokeBeanFactoryPostProcessors(beanFactory)                      │
│  ├── 执行 BeanDefinitionRegistryPostProcessor                      │
│  │   └── ConfigurationClassPostProcessor 扫描配置类                │
│  └── 执行 BeanFactoryPostProcessor                                 │
│     └── PropertySourcesPlaceholderConfigurer 解析占位符            │
│     ↓                                                              │
│  registerBeanPostProcessors(beanFactory)                           │
│  ├── 注册 PriorityOrdered BeanPostProcessor                        │
│  ├── 注册 Ordered BeanPostProcessor                                │
│  └── 注册普通 BeanPostProcessor                                     │
│     ↓                                                              │
│  initMessageSource()                                               │
│  └── 初始化国际化消息源                                              │
│     ↓                                                              │
│  initApplicationEventMulticaster()                                 │
│  └── 初始化事件广播器                                                │
│     ↓                                                              │
│  onRefresh()                                                       │
│  └── 创建内嵌 Web 服务器（Tomcat/Jetty/Undertow）                    │
│     ↓                                                              │
│  registerListeners()                                               │
│  ├── 注册静态监听器                                                 │
│  └── 注册早期事件                                                   │
│     ↓                                                              │
│  finishBeanFactoryInitialization(beanFactory)                      │
│  ├── 初始化 ConversionService                                      │
│  ├── 冻结 BeanDefinition                                          │
│  └── 实例化所有非懒加载单例 Bean                                     │
│     ↓                                                              │
│  finishRefresh()                                                   │
│  ├── 清理缓存                                                       │
│  ├── 初始化 LifecycleProcessor                                     │
│  └── 发布 ContextRefreshedEvent                                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 4.3 关键步骤详解

#### 4.3.1 invokeBeanFactoryPostProcessors

```java
protected void invokeBeanFactoryPostProcessors(ConfigurableListableBeanFactory beanFactory) {
    // 1. 执行 BeanDefinitionRegistryPostProcessor
    //    最重要的是 ConfigurationClassPostProcessor
    //    它负责解析 @Configuration、@ComponentScan、@Import 等注解
    
    // 执行顺序：
    // PriorityOrdered → Ordered → 普通
    
    // 2. 执行 BeanFactoryPostProcessor
    //    如 PropertySourcesPlaceholderConfigurer
    //    解析 ${...} 占位符
}
```

#### 4.3.2 registerBeanPostProcessors

```java
protected void registerBeanPostProcessors(ConfigurableListableBeanFactory beanFactory) {
    // 注册顺序：
    // 1. PriorityOrdered BeanPostProcessor
    //    - CommonAnnotationBeanPostProcessor (@PostConstruct, @PreDestroy)
    //    - AutowiredAnnotationBeanPostProcessor (@Autowired, @Value)
    
    // 2. Ordered BeanPostProcessor
    
    // 3. 普通 BeanPostProcessor
    //    - ApplicationContextAwareProcessor
    //    - ApplicationListenerDetector
    
    // 4. MergedBeanDefinitionPostProcessor
    //    - 收集 @Autowired 注解元数据
}
```

#### 4.3.3 onRefresh()

```java
// ServletWebServerApplicationContext
protected void onRefresh() {
    super.onRefresh();
    try {
        // 创建 Web 服务器
        createWebServer();
    } catch (Throwable ex) {
        throw new ApplicationContextException("Unable to start web server", ex);
    }
}

private void createWebServer() {
    WebServer webServer = null;
    ServletContextInitializer servletContextInitializer = 
        this.selfInitializer;
    
    if (this.factory != null) {
        // 获取 WebServerFactory（Tomcat/Jetty/Undertow）
        webServer = getWebServer(servletContextInitializer);
    }
    
    this.webServer = webServer;
}
```

#### 4.3.4 finishBeanFactoryInitialization

```java
protected void finishBeanFactoryInitialization(ConfigurableListableBeanFactory beanFactory) {
    // 1. 初始化 ConversionService
    if (beanFactory.containsBean(CONVERSION_SERVICE_BEAN_NAME)) {
        beanFactory.getBean(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class);
    }
    
    // 2. 冻结 BeanDefinition（不允许再修改）
    beanFactory.freezeConfiguration();
    
    // 3. 实例化所有非懒加载单例 Bean
    beanFactory.preInstantiateSingletons();
}
```

### 4.4 Bean 实例化流程

```java
public void preInstantiateSingletons() throws BeansException {
    // 遍历所有 BeanDefinition
    for (String beanName : beanNames) {
        RootBeanDefinition bd = getMergedLocalBeanDefinition(beanName);
        
        // 非抽象、单例、非懒加载
        if (!bd.isAbstract() && bd.isSingleton() && !bd.isLazyInit()) {
            if (isFactoryBean(beanName)) {
                // FactoryBean 处理
                Object bean = getBean(FACTORY_BEAN_PREFIX + beanName);
            } else {
                // 普通 Bean
                getBean(beanName);
            }
        }
    }
}

// getBean() 核心流程
protected <T> T doGetBean(String name, Class<T> requiredType, 
                          Object[] args, boolean typeCheckOnly) {
    // 1. 转换 Bean 名称
    String beanName = transformedBeanName(name);
    
    // 2. 检查单例缓存
    Object sharedInstance = getSingleton(beanName);
    if (sharedInstance != null) {
        return (T) getObjectForBeanInstance(sharedInstance, name, beanName, null);
    }
    
    // 3. 检查原型作用域循环依赖
    if (isPrototypeCurrentlyInCreation(beanName)) {
        throw new BeanCurrentlyInCreationException(beanName);
    }
    
    // 4. 检查父工厂
    BeanFactory parentBeanFactory = getParentBeanFactory();
    if (parentBeanFactory != null && !containsBeanDefinition(beanName)) {
        return parentBeanFactory.getBean(nameToLookup, requiredType);
    }
    
    // 5. 标记 Bean 正在创建
    if (!typeCheckOnly) {
        markBeanAsCreated(beanName);
    }
    
    try {
        // 6. 获取 BeanDefinition
        RootBeanDefinition mbd = getMergedLocalBeanDefinition(beanName);
        
        // 7. 先实例化依赖 Bean
        String[] dependsOn = mbd.getDependsOn();
        for (String dep : dependsOn) {
            getBean(dep);
        }
        
        // 8. 创建 Bean 实例
        if (mbd.isSingleton()) {
            sharedInstance = getSingleton(beanName, () -> {
                return createBean(beanName, mbd, args);
            });
            bean = getObjectForBeanInstance(sharedInstance, name, beanName, mbd);
        }
    } finally {
        // 9. 清理
    }
    
    return (T) bean;
}
```

## 五、SpringFactoriesLoader 与自动配置

### 5.1 SpringFactoriesLoader 原理

```java
public final class SpringFactoriesLoader {
    
    public static final String FACTORIES_RESOURCE_LOCATION = "META-INF/spring.factories";
    
    public static <T> List<T> loadFactories(Class<T> factoryType, ClassLoader classLoader) {
        // 1. 加载类名
        List<String> factoryImplementationNames = loadFactoryNames(factoryType, classLoader);
        
        // 2. 实例化
        List<T> result = new ArrayList<>(factoryImplementationNames.size());
        for (String factoryImplementationName : factoryImplementationNames) {
            result.add(instantiateFactory(factoryImplementationName, factoryType, classLoader));
        }
        
        return result;
    }
    
    public static List<String> loadFactoryNames(Class<?> factoryType, ClassLoader classLoader) {
        String factoryTypeName = factoryType.getName();
        
        // 加载所有 META-INF/spring.factories 文件
        Enumeration<URL> urls = classLoader.getResources(FACTORIES_RESOURCE_LOCATION);
        
        Properties properties = new Properties();
        while (urls.hasMoreElements()) {
            URL url = urls.nextElement();
            properties.load(url.openStream());
        }
        
        // 返回指定类型的实现类名
        return Arrays.asList(properties.getProperty(factoryTypeName, "").split(","));
    }
}
```

### 5.2 spring.factories 示例

```properties
# org/springframework/boot/spring-boot-autoconfigure/3.x/spring.factories

# Initializers
org.springframework.context.ApplicationContextInitializer=\
org.springframework.boot.autoconfigure.SharedMetadataReaderFactoryContextInitializer

# Listeners
org.springframework.context.ApplicationListener=\
org.springframework.boot.autoconfigure.BackgroundApplicationInitializer

# Auto Configure
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.springframework.boot.autoconfigure.web.servlet.WebMvcAutoConfiguration,\
org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration,\
org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration
```

### 5.3 自动配置流程

```
┌─────────────────────────────────────────────────────────────┐
│                    自动配置流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  @SpringBootApplication                                     │
│  └── @EnableAutoConfiguration                              │
│      └── @Import(AutoConfigurationImportSelector.class)    │
│          ↓                                                  │
│  AutoConfigurationImportSelector                           │
│  ├── getAutoConfigurationEntry()                           │
│  │   └── getCandidateConfigurations()                      │
│  │       └── SpringFactoriesLoader.loadFactoryNames()      │
│  │           └── 读取 META-INF/spring.factories            │
│  ↓                                                          │
│  过滤自动配置类                                              │
│  ├── @ConditionalOnClass                                   │
│  ├── @ConditionalOnBean                                    │
│  ├── @ConditionalOnMissingBean                             │
│  └── @ConditionalOnProperty                                │
│  ↓                                                          │
│  注册生效的自动配置类                                         │
│  └── BeanDefinition 注册到 BeanFactory                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 @EnableAutoConfiguration 详解

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@AutoConfigurationPackage
@Import(AutoConfigurationImportSelector.class)
public @interface EnableAutoConfiguration {
    
    String ENABLED_OVERRIDE_PROPERTY = "spring.boot.enableautoconfiguration";
    
    // 排除特定的自动配置类
    Class<?>[] exclude() default {};
    
    // 通过名称排除
    String[] excludeName() default {};
}
```

### 5.5 条件注解机制

```java
// 条件注解示例
@Configuration
@ConditionalOnClass({ Servlet.class, ServletRegistration.class })
@ConditionalOnWebApplication(type = Type.SERVLET)
@EnableConfigurationProperties(ServerProperties.class)
public class WebMvcAutoConfiguration {
    
    @Bean
    @ConditionalOnMissingBean
    public InternalResourceViewResolver defaultViewResolver() {
        InternalResourceViewResolver resolver = new InternalResourceViewResolver();
        resolver.setPrefix(this.mvcProperties.getView().getPrefix());
        resolver.setSuffix(this.mvcProperties.getView().getSuffix());
        return resolver;
    }
}

// 常用条件注解
@ConditionalOnClass        // 类路径存在指定类
@ConditionalOnMissingClass // 类路径不存在指定类
@ConditionalOnBean         // 容器中存在指定 Bean
@ConditionalOnMissingBean  // 容器中不存在指定 Bean
@ConditionalOnProperty     // 配置属性满足条件
@ConditionalOnWebApplication // 是 Web 应用
@ConditionalOnExpression   // SpEL 表达式为 true
```

## 六、嵌入式 Web 服务器创建

### 6.1 Web 服务器工厂

```java
// Tomcat
public class TomcatServletWebServerFactory implements ServletWebServerFactory {
    
    @Override
    public WebServer getWebServer(ServletContextInitializer... initializers) {
        Tomcat tomcat = new Tomcat();
        
        // 设置基础目录
        File baseDir = (this.baseDirectory != null) ? this.baseDirectory : createTempDir("tomcat");
        tomcat.setBaseDir(baseDir.getAbsolutePath());
        
        // 创建 Connector
        Connector connector = new Connector(this.protocol);
        connector.setPort(this.port);
        tomcat.getService().addConnector(connector);
        
        // 创建 Context
        Context context = tomcat.addContext("", getDocumentBase());
        
        // 配置 Servlet
        configureContext(context, initializers);
        
        // 启动 Tomcat
        return getTomcatWebServer(tomcat);
    }
}
```

### 6.2 Web 服务器启动流程

```
┌─────────────────────────────────────────────────────────────┐
│                Web 服务器启动流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  onRefresh()                                                │
│  └── createWebServer()                                      │
│      └── ServletWebServerFactory.getWebServer()             │
│          ↓                                                  │
│  TomcatServletWebServerFactory                              │
│  ├── 创建 Tomcat 实例                                        │
│  ├── 配置 Connector（端口、协议）                            │
│  ├── 创建 Context（应用上下文）                              │
│  └── 返回 TomcatWebServer                                   │
│      ↓                                                      │
│  TomcatWebServer.start()                                    │
│  ├── tomcat.start()                                         │
│  ├── 初始化 Servlet                                         │
│  └── 启动监听线程                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 内嵌服务器配置

```yaml
# application.yml
server:
  port: 8080
  servlet:
    context-path: /api
  tomcat:
    max-threads: 200
    min-spare-threads: 10
    accept-count: 100
    max-connections: 10000
  undertow:
    io-threads: 16
    worker-threads: 256
    buffer-size: 1024
```

```java
@Configuration
public class TomcatConfig {
    
    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> 
        tomcatCustomizer() {
        return factory -> {
            factory.setPort(8081);
            factory.setContextPath("/app");
            
            TomcatConnectorCustomizer connectorCustomizer = connector -> {
                Http11NioProtocol protocol = (Http11NioProtocol) connector.getProtocolHandler();
                protocol.setMaxThreads(200);
                protocol.setConnectionTimeout(30000);
            };
            factory.addConnectorCustomizers(connectorCustomizer);
        };
    }
}
```

## 七、完整启动流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Spring Boot 完整启动流程图                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  main()                                                             │
│  └── SpringApplication.run()                                        │
│      ↓                                                              │
│  【阶段一：创建 SpringApplication】                                   │
│  ├── 推断应用类型 (Servlet/Reactive/None)                           │
│  ├── 加载 ApplicationContextInitializer                             │
│  ├── 加载 ApplicationListener                                       │
│  └── 推断主类                                                       │
│      ↓                                                              │
│  【阶段二：运行 SpringApplication】                                   │
│  ├── 创建 BootstrapContext                                          │
│  ├── 准备环境 (ConfigurableEnvironment)                             │
│  │   ├── 加载配置文件 (application.yml)                             │
│  │   └── 绑定环境属性                                               │
│  ├── 打印 Banner                                                    │
│  └── 创建 ApplicationContext                                        │
│      ↓                                                              │
│  【阶段三：准备上下文】                                               │
│  ├── 设置环境                                                       │
│  ├── 执行 ApplicationContextInitializer                             │
│  ├── 发布 ApplicationContextInitializedEvent                        │
│  └── 加载 BeanDefinition                                           │
│      ↓                                                              │
│  【阶段四：刷新上下文】                                               │
│  ├── prepareRefresh()                                               │
│  ├── obtainFreshBeanFactory()                                       │
│  ├── prepareBeanFactory()                                           │
│  ├── invokeBeanFactoryPostProcessors()                              │
│  │   ├── ConfigurationClassPostProcessor                            │
│  │   │   ├── 解析 @Configuration                                    │
│  │   │   ├── 解析 @ComponentScan                                    │
│  │   │   ├── 解析 @Import                                          │
│  │   │   └── 注册 BeanDefinition                                   │
│  │   └── 处理自动配置                                               │
│  ├── registerBeanPostProcessors()                                   │
│  ├── initMessageSource()                                            │
│  ├── initApplicationEventMulticaster()                              │
│  ├── onRefresh()                                                    │
│  │   └── 创建内嵌 Web 服务器                                        │
│  ├── registerListeners()                                            │
│  ├── finishBeanFactoryInitialization()                              │
│  │   └── 实例化所有单例 Bean                                        │
│  └── finishRefresh()                                                │
│      └── 发布 ContextRefreshedEvent                                 │
│      ↓                                                              │
│  【阶段五：启动完成】                                                 │
│  ├── 执行 CommandLineRunner                                         │
│  ├── 执行 ApplicationRunner                                         │
│  ├── 发布 ApplicationStartedEvent                                   │
│  └── 应用就绪                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 八、启动扩展点

### 8.1 ApplicationContextInitializer

```java
public class MyInitializer implements ApplicationContextInitializer<ConfigurableApplicationContext> {
    
    @Override
    public void initialize(ConfigurableApplicationContext applicationContext) {
        // 在上下文刷新之前执行
        ConfigurableEnvironment env = applicationContext.getEnvironment();
        env.getSystemProperties().put("my.property", "value");
    }
}

// 注册方式
// 1. spring.factories
org.springframework.context.ApplicationContextInitializer=\
com.example.MyInitializer

// 2. SpringApplication.addInitializers()
SpringApplication app = new SpringApplication(Application.class);
app.addInitializers(new MyInitializer());
```

### 8.2 ApplicationListener

```java
public class MyListener implements ApplicationListener<ApplicationStartedEvent> {
    
    @Override
    public void onApplicationEvent(ApplicationStartedEvent event) {
        System.out.println("应用启动完成！");
    }
}

// 常用事件
ApplicationStartingEvent          // 启动开始
ApplicationEnvironmentPreparedEvent // 环境准备完成
ApplicationContextInitializedEvent // 上下文初始化
ApplicationPreparedEvent          // 上下文准备完成
ApplicationStartedEvent           // 启动完成
ApplicationReadyEvent             // 就绪
```

### 8.3 CommandLineRunner / ApplicationRunner

```java
@Component
public class MyRunner implements CommandLineRunner {
    
    @Override
    public void run(String... args) throws Exception {
        // 应用启动后执行
        System.out.println("执行初始化任务...");
    }
}

@Component
public class MyAppRunner implements ApplicationRunner {
    
    @Override
    public void run(ApplicationArguments args) throws Exception {
        // 支持解析命令行参数
        List<String> files = args.getOptionValues("file");
    }
}
```

## 📖 高频面试题

### Q1: Spring Boot 启动流程是怎样的？

**答：** Spring Boot 启动流程分为以下几个阶段：

#### 1. 创建 SpringApplication
- 推断应用类型（Servlet/Reactive/None）
- 加载 ApplicationContextInitializer
- 加载 ApplicationListener
- 推断主类

#### 2. 运行 SpringApplication
- 创建 Bootstrap 上下文
- 准备环境（加载配置文件）
- 打印 Banner
- 创建 ApplicationContext

#### 3. 准备上下文
- 设置环境
- 执行初始化器
- 发布事件

#### 4. 刷新上下文（核心）
- prepareRefresh：准备刷新
- obtainFreshBeanFactory：获取 BeanFactory
- prepareBeanFactory：准备 BeanFactory
- invokeBeanFactoryPostProcessors：执行后置处理器
- registerBeanPostProcessors：注册后置处理器
- initMessageSource：初始化消息源
- initApplicationEventMulticaster：初始化事件广播器
- onRefresh：创建内嵌 Web 服务器
- registerListeners：注册监听器
- finishBeanFactoryInitialization：实例化单例 Bean
- finishRefresh：完成刷新

#### 5. 启动完成
- 执行 Runner
- 发布就绪事件

### Q2: @EnableAutoConfiguration 是如何工作的？

**答：**

#### 1. 工作原理
```java
@EnableAutoConfiguration
  └── @Import(AutoConfigurationImportSelector.class)
      └── selectImports()
          └── SpringFactoriesLoader.loadFactoryNames()
              └── 读取 META-INF/spring.factories
```

#### 2. 加载过程
- 从所有 jar 包的 `META-INF/spring.factories` 文件中读取 `EnableAutoConfiguration` 配置
- 获取所有自动配置类的全限定名
- 通过条件注解过滤，只保留生效的配置类

#### 3. 条件注解
- `@ConditionalOnClass`：类路径存在指定类
- `@ConditionalOnBean`：容器中存在指定 Bean
- `@ConditionalOnMissingBean`：容器中不存在指定 Bean
- `@ConditionalOnProperty`：配置属性满足条件

#### 4. 排除自动配置
```java
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
// 或
@EnableAutoConfiguration(exclude = {DataSourceAutoConfiguration.class})
// 或
spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
```

### Q3: Spring Boot 如何创建内嵌 Tomcat？

**答：**

#### 1. 触发时机
- 在 `refresh()` 的 `onRefresh()` 阶段创建

#### 2. 创建流程
```java
// ServletWebServerApplicationContext
protected void onRefresh() {
    createWebServer();
}

private void createWebServer() {
    ServletWebServerFactory factory = getWebServerFactory();
    this.webServer = factory.getWebServer(this.selfInitializer);
}
```

#### 3. 工厂选择
- `TomcatServletWebServerFactory`
- `JettyServletWebServerFactory`
- `UndertowServletWebServerFactory`

#### 4. 条件判断
- 通过 `@ConditionalOnClass` 判断类路径是否存在 Tomcat 类
- 存在则使用 Tomcat，否则尝试其他服务器

### Q4: SpringFactoriesLoader 的作用？

**答：**

#### 1. 作用
- 加载 `META-INF/spring.factories` 文件中的配置
- 实现 SPI（Service Provider Interface）机制
- 解耦接口与实现

#### 2. 使用场景
- 自动配置：加载 `EnableAutoConfiguration`
- 监听器：加载 `ApplicationListener`
- 初始化器：加载 `ApplicationContextInitializer`

#### 3. 文件格式
```properties
# key = 接口全限定名
# value = 实现类全限定名（多个用逗号分隔）
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.springframework.boot.autoconfigure.web.servlet.WebMvcAutoConfiguration
```

#### 4. Spring Boot 2.7+ 变化
- 新增 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`
- 每行一个自动配置类
- 推荐使用新格式

### Q5: Spring Boot 如何实现零配置？

**答：**

#### 1. 约定优于配置
- 默认配置文件路径：`application.yml`
- 默认端口：8080
- 默认静态资源路径：`static/`

#### 2. 自动配置
- 根据类路径自动配置
- 根据已有 Bean 自动配置
- 通过条件注解控制

#### 3. Starter 机制
- 一键引入依赖
- 自动配置相关组件
- 开箱即用

#### 4. 配置覆盖
- 外部配置覆盖内部配置
- 命令行参数优先级最高

---

**参考链接：**
- [Spring Boot 启动流程详解-掘金](https://juejin.cn/post/7232856790361280570)
- [SpringApplication 启动过程-官方文档](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.spring-application)
- [Spring Factories Loader 机制-CSDN](https://blog.csdn.net/zhengwenbo/article/details/108531239)
