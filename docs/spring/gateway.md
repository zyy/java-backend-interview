# Spring Cloud 网关

> API Gateway

## 🎯 面试重点

- 网关作用
- Gateway 工作原理
- 过滤器

## 📖 Gateway

### 概念

```java
/**
 * Spring Cloud Gateway
 * 
 * 作用：
 * 1. 请求路由
 * 2. 负载均衡
 * 3. 权限校验
 * 4. 限流熔断
 * 5. 日志监控
 */
public class GatewayConcept {}
```

### 核心概念

```java
/**
 * 核心概念
 */
public class GatewayCore {
    // Route（路由）
    /*
     * 包含：id, uri, predicates, filters
     */
    
    // Predicate（断言）
    /*
     * 匹配请求条件
     * - Path=/api/**
     * - Method=GET
     * - Header=X-Request-Id, \d+
     */
    
    // Filter（过滤器）
    /*
     * 请求前后处理
     * - 认证
     * - 日志
     * - 限流
     */
}
```

### 配置示例

```java
/**
 * 配置示例
 */
public class GatewayConfig {
    // yml 配置
    /*
     * spring:
     *   cloud:
     *     gateway:
     *       routes:
     *         - id: user-service
     *           uri: lb://user-service
     *           predicates:
     *             - Path=/user/**
     *           filters:
     *             - StripPrefix=1
     */
}
```

## 📖 面试真题

### Q1: 网关的作用？

**答：** 请求路由、负载均衡、权限校验、限流熔断、日志监控。

---

**⭐ 重点：网关是微服务入口**