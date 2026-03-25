# Spring 负载均衡

> Spring Cloud 负载均衡

## 🎯 面试重点

- 负载均衡策略
-Ribbon 组件
- 负载均衡原理

## 📖 负载均衡策略

### Ribbon 内置策略

```java
/**
 * Ribbon 负载均衡策略
 */
public class RibbonStrategy {
    // 常见策略
    /*
     * - RoundRobinRule：轮询（默认）
     * - RandomRule：随机
     * - WeightedResponseTimeRule：响应时间加权
     * - BestAvailableRule：选择最空闲
     * - AvailabilityFilteringRule：过滤故障实例
     */
}
```

### 配置方式

```java
/**
 * 配置方式
 */
public class RibbonConfig {
    // 1. 全局配置
    /*
     * service-provider:
     *   ribbon:
     *     NFLoadBalancerRuleClassName: com.netflix.loadbalancer.RandomRule
     */
    
    // 2. Java 配置
    /*
     * @Bean
     * public IRule randomRule() {
     *     return new RandomRule();
     * }
     */
}
```

## 📖 面试真题

### Q1: Ribbon 的工作原理？

**答：** 
1. 拦截 RestTemplate 请求
2. 从注册中心获取服务列表
3. 根据负载均衡策略选择服务
4. 发起调用

---

**⭐ 重点：理解负载均衡策略和原理**