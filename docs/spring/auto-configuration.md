---
layout: default
title: Spring Boot 自动装配原理 ⭐⭐⭐
---
# Spring Boot 自动装配原理 ⭐⭐⭐

## 面试题：Spring Boot 自动装配原理是什么？

### 核心回答

Spring Boot 的**自动装配（Auto-Configuration）**是其核心特性，通过**约定大于配置**的思想，在启动时自动将符合条件的 Bean 加载到 IoC 容器中。

### 自动装配的核心注解

```java
@SpringBootApplication
    └── @SpringBootConfiguration  // 标记为配置类
    └── @EnableAutoConfiguration  // 开启自动装配（核心）
    └── @ComponentScan            // 组件扫描
```

### @EnableAutoConfiguration 详解

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@AutoConfigurationPackage
@Import(AutoConfigurationImportSelector.class)  // 关键：导入自动配置选择器
public @interface EnableAutoConfiguration {
    String ENABLED_OVERRIDE_PROPERTY = "spring.boot.enableautoconfiguration";
    Class<?>[] exclude() default {};
    String[] excludeName() default {};
}
```

### 自动装配的执行流程

```
1. 启动 Spring Boot 应用
    ↓
2. 解析 @SpringBootApplication
    ↓
3. @EnableAutoConfiguration 生效
    ↓
4. AutoConfigurationImportSelector.selectImports()
    ↓
5. 读取 META-INF/spring.factories
    ↓
6. 筛选符合条件的自动配置类（@Conditional）
    ↓
7. 加载自动配置类，注册 Bean 到 IoC 容器
```

### 源码解析

#### 1. AutoConfigurationImportSelector

```java
public class AutoConfigurationImportSelector implements DeferredImportSelector {
    
    @Override
    public String[] selectImports(AnnotationMetadata annotationMetadata) {
        // 1. 获取所有候选配置类
        List<String> configurations = getCandidateConfigurations(annotationMetadata, attributes);
        
        // 2. 去重
        configurations = removeDuplicates(configurations);
        
        // 3. 排除指定配置
        Set<String> exclusions = getExclusions(annotationMetadata, attributes);
        checkExcludedClasses(configurations, exclusions);
        configurations.removeAll(exclusions);
        
        // 4. 按条件过滤（@Conditional）
        configurations = getConfigurationClassFilter().filter(configurations);
        
        // 5. 返回最终配置类列表
        return StringUtils.toStringArray(configurations);
    }
    
    protected List<String> getCandidateConfigurations(AnnotationMetadata metadata, 
                                                       AnnotationAttributes attributes) {
        // 从 META-INF/spring.factories 加载配置
        List<String> configurations = SpringFactoriesLoader.loadFactoryNames(
            getSpringFactoriesLoaderFactoryClass(), getBeanClassLoader());
        return configurations;
    }
}
```

#### 2. spring.factories 文件

```properties
# META-INF/spring.factories（Spring Boot 2.7+ 已弃用，改用 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports）
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.springframework.boot.autoconfigure.web.servlet.DispatcherServletAutoConfiguration,\
org.springframework.boot.autoconfigure.web.servlet.ServletWebServerFactoryAutoConfiguration,\
org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration,\
...
```

### 条件装配注解（@Conditional）

Spring Boot 通过条件注解控制自动配置的加载时机：

| 注解 | 条件 |
|------|------|
| `@ConditionalOnClass` | 类路径存在指定类 |
| `@ConditionalOnMissingClass` | 类路径不存在指定类 |
| `@ConditionalOnBean` | 容器中存在指定 Bean |
| `@ConditionalOnMissingBean` | 容器中不存在指定 Bean |
| `@ConditionalOnProperty` | 指定属性满足条件 |
| `@ConditionalOnWebApplication` | 是 Web 应用 |
| `@ConditionalOnExpression` | SpEL 表达式为 true |

**示例**：
```java
@Configuration
@ConditionalOnClass({DataSource.class, JdbcTemplate.class})  // 类路径存在 DataSource 和 JdbcTemplate
@ConditionalOnSingleCandidate(DataSource.class)  // 容器中只有一个 DataSource
@AutoConfigureAfter(DataSourceAutoConfiguration.class)  // 在 DataSourceAutoConfiguration 之后加载
public class JdbcTemplateAutoConfiguration {
    
    @Bean
    @Primary
    @ConditionalOnMissingBean(JdbcOperations.class)  // 容器中不存在 JdbcOperations 时才创建
    public JdbcTemplate jdbcTemplate(DataSource dataSource) {
        return new JdbcTemplate(dataSource);
    }
}
```

### 自动装配示例：DispatcherServlet

```java
@AutoConfigureOrder(Ordered.HIGHEST_PRECEDENCE)
@Configuration
@ConditionalOnWebApplication(type = Type.SERVLET)  // 是 Servlet Web 应用
@ConditionalOnClass(DispatcherServlet.class)       // 类路径存在 DispatcherServlet
@AutoConfigureAfter(ServletWebServerFactoryAutoConfiguration.class)
public class DispatcherServletAutoConfiguration {
    
    public static final String DEFAULT_DISPATCHER_SERVLET_BEAN_NAME = "dispatcherServlet";
    
    @Bean(name = DEFAULT_DISPATCHER_SERVLET_BEAN_NAME)
    @ConditionalOnMissingBean(name = DEFAULT_DISPATCHER_SERVLET_BEAN_NAME)
    public DispatcherServlet dispatcherServlet(HttpProperties httpProperties, 
                                                WebMvcProperties webMvcProperties) {
        DispatcherServlet dispatcherServlet = new DispatcherServlet();
        dispatcherServlet.setDispatchOptionsRequest(webMvcProperties.isDispatchOptionsRequest());
        // ... 其他配置
        return dispatcherServlet;
    }
    
    @Bean
    @ConditionalOnBean(name = DEFAULT_DISPATCHER_SERVLET_BEAN_NAME)
    public DispatcherServletRegistrationBean dispatcherServletRegistration(
            DispatcherServlet dispatcherServlet,
            WebMvcProperties webMvcProperties,
            ObjectProvider<MultipartConfigElement> multipartConfig) {
        // 注册 DispatcherServlet 到 Servlet 容器
        DispatcherServletRegistrationBean registration = new DispatcherServletRegistrationBean(
                dispatcherServlet, webMvcProperties.getServlet().getPath());
        registration.setName(DEFAULT_DISPATCHER_SERVLET_BEAN_NAME);
        registration.setLoadOnStartup(webMvcProperties.getServlet().getLoadOnStartup());
        multipartConfig.ifAvailable(registration::setMultipartConfig);
        return registration;
    }
}
```

### 自定义 Starter

#### 1. 创建自动配置类

```java
@Configuration
@ConditionalOnClass(MyService.class)
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration {
    
    @Autowired
    private MyProperties properties;
    
    @Bean
    @ConditionalOnMissingBean  // 用户未自定义时才创建
    public MyService myService() {
        MyService service = new MyService();
        service.setName(properties.getName());
        return service;
    }
}
```

#### 2. 配置属性类

```java
@ConfigurationProperties(prefix = "my.service")
public class MyProperties {
    private String name = "default";
    private boolean enabled = true;
    // getter/setter
}
```

#### 3. 创建 spring.factories

```properties
# META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.autoconfigure.MyAutoConfiguration
```

#### 4. 使用自定义 Starter

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>my-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
# application.yml
my:
  service:
    name: custom-name
    enabled: true
```

### 自动装配的排除与定制

```java
// 方式1：排除特定自动配置
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})

// 方式2：通过配置排除
spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration

// 方式3：自定义配置覆盖自动配置
@Bean
@Primary
public DataSource dataSource() {
    // 自定义 DataSource
}
```

### Spring Boot 2.7+ 的变化

```
旧方式：META-INF/spring.factories
新方式：META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports

文件内容：
com.example.MyAutoConfiguration
com.example.OtherAutoConfiguration
```

### 高频面试题

**Q0: Spring Boot 自动装配原理？**

**答：** Spring Boot 自动装配（Auto-Configuration）的核心原理是基于条件化配置和约定优于配置的思想。

#### 1. 核心机制
- **@EnableAutoConfiguration**：启动自动装配的核心注解。
- **META-INF/spring.factories**：早期版本（Spring Boot 2.7 前）存放自动配置类的文件。
- **META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports**：Spring Boot 2.7+ 使用此文件。
- **@Conditional 系列注解**：条件化加载配置。

#### 2. 工作流程
```
1. Spring Boot 启动 → 2. 加载 @SpringBootApplication
3. @SpringBootApplication 包含 @EnableAutoConfiguration
4. @EnableAutoConfiguration 通过 AutoConfigurationImportSelector
5. 加载 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
6. 过滤条件（@Conditional） → 7. 注册符合条件的配置类
```

#### 3. 关键源码分析
```java
// AutoConfigurationImportSelector 核心方法
public String[] selectImports(AnnotationMetadata annotationMetadata) {
    // 1. 检查是否启用自动装配
    if (!isEnabled(annotationMetadata)) {
        return NO_IMPORTS;
    }
    
    // 2. 获取自动配置类
    AutoConfigurationEntry autoConfigurationEntry = getAutoConfigurationEntry(annotationMetadata);
    
    // 3. 返回符合条件的配置类
    return StringUtils.toStringArray(autoConfigurationEntry.getConfigurations());
}

// 获取自动配置条目
protected AutoConfigurationEntry getAutoConfigurationEntry(AnnotationMetadata annotationMetadata) {
    // 获取所有配置类
    List<String> configurations = getCandidateConfigurations(annotationMetadata, attributes);
    
    // 去重
    configurations = removeDuplicates(configurations);
    
    // 排除指定的类
    Set<String> exclusions = getExclusions(annotationMetadata, attributes);
    checkExcludedClasses(configurations, exclusions);
    configurations.removeAll(exclusions);
    
    // 条件过滤
    configurations = getConfigurationClassFilter().filter(configurations);
    
    // 触发自动配置导入事件
    fireAutoConfigurationImportEvents(configurations, exclusions);
    
    return new AutoConfigurationEntry(configurations, exclusions);
}
```

#### 4. 条件注解（@Conditional）
- **@ConditionalOnClass**：类路径下存在指定类时生效。
- **@ConditionalOnMissingClass**：类路径下不存在指定类时生效。
- **@ConditionalOnBean**：容器中存在指定 Bean 时生效。
- **@ConditionalOnMissingBean**：容器中不存在指定 Bean 时生效。
- **@ConditionalOnProperty**：配置文件中存在指定属性时生效。
- **@ConditionalOnResource**：存在指定资源文件时生效。
- **@ConditionalOnWebApplication**：Web 应用时生效。
- **@ConditionalOnNotWebApplication**：非 Web 应用时生效。

#### 5. 自动配置示例
```java
@Configuration
@ConditionalOnClass({ DataSource.class, EmbeddedDatabaseType.class })
@EnableConfigurationProperties(DataSourceProperties.class)
@Import({ DataSourcePoolMetadataProvidersConfiguration.class, 
          DataSourceInitializationConfiguration.class })
public class DataSourceAutoConfiguration {
    
    @Configuration
    @Conditional(EmbeddedDatabaseCondition.class)
    @ConditionalOnMissingBean({ DataSource.class, XADataSource.class })
    @Import(EmbeddedDataSourceConfiguration.class)
    protected static class EmbeddedDatabaseConfiguration {
    }
    
    @Configuration
    @Conditional(PooledDataSourceCondition.class)
    @ConditionalOnMissingBean({ DataSource.class, XADataSource.class })
    @Import({ DataSourceConfiguration.Hikari.class, 
              DataSourceConfiguration.Tomcat.class,
              DataSourceConfiguration.Dbcp2.class,
              DataSourceConfiguration.Generic.class })
    protected static class PooledDataSourceConfiguration {
    }
}
```

#### 6. 自定义 Starter
1. 创建 `xxx-spring-boot-autoconfigure` 模块。
2. 创建 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 文件。
3. 编写自动配置类，使用 `@Conditional` 注解。
4. 创建 `xxx-spring-boot-starter` 模块，依赖自动配置模块。

#### 7. 调试技巧
- **查看加载的自动配置**：`debug=true` 或 `logging.level.org.springframework.boot.autoconfigure=DEBUG`。
- **排除特定自动配置**：`@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})`。
- **查看条件评估报告**：`debug=true` 会在启动时打印条件匹配报告。

**总结**：Spring Boot 自动装配通过条件化配置和约定优于配置的原则，大大简化了 Spring 应用的配置工作。

**Q1: Spring Boot 自动装配和 Spring 的 XML 配置有什么区别？**

| 特性 | XML 配置 | 自动装配 |
|------|---------|---------|
| 配置方式 | 手动编写 XML | 约定大于配置 |
| 灵活性 | 完全可控 | 可覆盖定制 |
| 维护成本 | 高 | 低 |
| 开发效率 | 低 | 高 |

**Q2: 如何查看当前应用加载了哪些自动配置？**

```yaml
# application.yml
debug: true
```

或在启动类添加：
```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        ConfigurableApplicationContext context = SpringApplication.run(Application.class, args);
        // 打印所有 Bean
        String[] beanNames = context.getBeanDefinitionNames();
        Arrays.sort(beanNames);
        for (String beanName : beanNames) {
            System.out.println(beanName);
        }
    }
}
```

**Q3: @ConditionalOnProperty 的使用场景？**

```java
@Configuration
@ConditionalOnProperty(
    prefix = "my.feature",  // 属性前缀
    name = "enabled",       // 属性名
    havingValue = "true",   // 期望的值
    matchIfMissing = false  // 属性不存在时是否匹配
)
public class MyFeatureConfiguration {
    // 只有当 my.feature.enabled=true 时才加载
}
```

**Q4: 为什么 Spring Boot 的自动配置类要加 @Configuration？**

- `@Configuration` 标记这是一个配置类
- 会被 Spring 的 `ConfigurationClassPostProcessor` 处理
- 支持 `@Bean` 方法的代理（保证单例）

---

**参考链接：**
- [Spring Boot 自动装配详解](https://www.iotword.com/41410.html)
- [深入剖析 SpringBoot3 自动装配原理-阿里云](https://developer.aliyun.com/article/1646602)
