# Spring 熔断与限流

> Spring Cloud Circuit Breaker

## 🎯 面试重点

- 熔断器模式
- Hystrix / Sentinel
- 降级处理

## 📖 熔断器

### Hystrix

```java
/**
 * Hystrix 熔断
 */
public class HystrixCircuitBreaker {
    // 基础使用
    /*
     * @HystrixCommand(fallbackMethod = "fallback")
     * public String call() {
     *     // 远程调用
     * }
     * 
     * public String fallback() {
     *     return "降级返回";
     * }
     */
    
    // 配置
    /*
     * @HystrixCommand(
     *     fallbackMethod = "fallback",
     *     commandProperties = {
     *         @HystrixProperty(name = "circuitBreaker.requestVolumeThreshold", value = "10"),
     *         @HystrixProperty(name = "circuitBreaker.sleepWindowInMilliseconds", value = "10000")
     *     }
     * )
     */
}
```

### Sentinel

```java
/**
 * Sentinel 熔断
 */
public class SentinelCircuitBreaker {
    // 限流
    /*
     * @SentinelResource(value = "test", blockHandler = "handleBlock")
     * public String test() {
     *     return "正常";
     * }
     * 
     * public String handleBlock(BlockException e) {
     *     return "限流";
     * }
     */
}
```

## 📖 面试真题

### Q1: 熔断器的工作原理？

**答：** 
- 关闭状态：正常调用，统计失败率
- 打开状态：快速失败，直接返回降级
- 半开状态：尝试恢复，允许少量请求通过

---

**⭐ 重点：熔断是保护系统的关键机制**