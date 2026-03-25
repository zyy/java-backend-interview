---
layout: default
title: Spring 配置中心
---
# Spring 配置中心

> Spring Cloud Config

## 🎯 面试重点

- 配置中心的概念
- Nacos Config
- 配置热刷新

## 📖 配置中心

### Nacos Config

```java
/**
 * Nacos 配置中心
 */
public class NacosConfigDemo {
    // 1. 引入依赖
    /*
     * <dependency>
     *     <groupId>com.alibaba.cloud</groupId>
     *     <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
     * </dependency>
     */
    
    // 2. 配置 bootstrap.yml
    /*
     * spring:
     *   cloud:
     *     nacos:
     *       config:
     *         server-addr: 127.0.0.1:8848
     *         namespace: dev
     *         group: DEFAULT_GROUP
     *         file-extension: yml
     */
    
    // 3. 使用配置
    /*
     * @Value("${config.name}")
     * private String name;
     */
}
```

### 热刷新

```java
/**
 * 配置热刷新
 */
public class HotRefresh {
    // 方式1：@RefreshScope
    /*
     * @RestController
     * @RefreshScope
     * public class Controller {
     *     @Value("${config.name}")
     *     private String name;
     * }
     */
    
    // 方式2：@ConfigurationProperties
    /*
     * @Component
     * @ConfigurationProperties(prefix = "config")
     * public class Config {
     *     private String name;
     * }
     */
}
```

## 📖 面试真题

### Q1: 配置中心的好处？

**答：** 统一管理配置、动态刷新、不重启应用。

---

**⭐ 重点：配置中心是微服务的基础设施**