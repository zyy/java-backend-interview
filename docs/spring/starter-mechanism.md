---
layout: default
title: Spring Boot Starter 机制
---
# Spring Boot Starter 机制

> 自动配置的核心

## 🎯 面试重点

- Starter 的作用
- 自动配置原理
- 如何自定义 Starter

## 📖 Starter 机制

### 什么是 Starter？

```java
/**
 * Starter
 * 
 * 目的：简化配置，快速集成
 * 
 * 官方 Starter：
 * - spring-boot-starter-web
 * - spring-boot-starter-data-jpa
 * - spring-boot-starter-redis
 */
public class StarterConcept {}
```

### 自动配置

```java
/**
 * 自动配置原理
 */
public class AutoConfiguration {
    // 1. @SpringBootApplication
    /*
     * 包含：
     * - @SpringBootConfiguration
     * - @EnableAutoConfiguration
     * - @ComponentScan
     */
    
    // 2. @EnableAutoConfiguration
    /*
     * 扫描 META-INF/spring.factories
     * 或 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
     * 
     * 加载自动配置类
     */
    
    // 3. 条件装配
    /*
     * @ConditionalOnClass       - 类存在时生效
     * @ConditionalOnMissingBean - 不存在 Bean 时生效
     * @ConditionalOnProperty    - 配置存在时生效
     */
}
```

### 自定义 Starter

```java
/**
 * 自定义 Starter
 */
public class CustomStarter {
    // 1. 创建 autoconfigure 模块
    /*
     * - 自动配置类
     * - META-INF/spring.factories
     */
    
    // 2. 创建 starter 模块
    /*
     * 依赖 autoconfigure
     */
    
    // 示例
    /*
     * @Configuration
     * @ConditionalOnClass(HelloService.class)
     * public class HelloAutoConfiguration {
     *     @Bean
     *     @ConditionalOnMissingBean
     *     public HelloService helloService() {
     *         return new HelloService();
     *     }
     * }
     */
}
```

## 📖 面试真题

### Q1: Spring Boot 自动配置原理？

**答：** 
1. @SpringBootApplication 包含 @EnableAutoConfiguration
2. 自动扫描 META-INF/spring.factories
3. 根据条件装配生成 Bean

---

**⭐ 重点：理解 Starter 机制是理解 Spring Boot 的关键**