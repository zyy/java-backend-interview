# Spring 服务注册与发现

> Spring Cloud 服务治理

## 🎯 面试重点

- Spring Cloud 组件
- 服务注册与发现原理
- Nacos vs Eureka

## 📖 服务注册

### 服务注册

```java
/**
 * 服务注册
 */
public class ServiceRegistryDemo {
    // @EnableDiscoveryClient
    /*
     * Spring Boot 应用启动时
     * 自动向注册中心注册服务
     * 
     * 配置：
     * spring:
     *   cloud:
     *     nacos:
     *       discovery:
     *         server-addr: 127.0.0.1:8848
     */
}
```

### 服务发现

```java
/**
 * 服务发现
 */
public class ServiceDiscoveryDemo {
    // 方式1：RestTemplate
    /*
     * @Bean
     * @LoadBalanced
     * public RestTemplate restTemplate() {
     *     return new RestTemplate();
     * }
     * 
     * // 调用服务
     * restTemplate.getForObject("http://service-name/xxx", String.class);
     */
    
    // 方式2：Feign
    /*
     * @FeignClient("service-name")
     * public interface UserClient {
     *     @GetMapping("/user/{id}")
     *     User getUser(@PathVariable("id") Long id);
     * }
     */
    
    // 方式3：OpenFeign
    /*
     * Spring Cloud 2.x 后，Feign 改名为 OpenFeign
     */
}
```

## 📖 面试真题

### Q1: @LoadBalanced 的作用？

**答：** 让 RestTemplate 具有负载均衡能力，自动从注册中心获取服务地址。

---

**⭐ 重点：Spring Cloud 是微服务开发的基础**