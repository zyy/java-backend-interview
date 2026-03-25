---
layout: default
title: 熔断与降级
---
# 熔断与降级

> 系统保护的重要机制

## 🎯 面试重点

- 熔断和降级的区别
- 熔断器的工作原理
- 常用实现方案

## 📖 概念区别

### 熔断 vs 降级

```java
/**
 * 熔断（Circuit Breaker）
 * 
 * 概念：当下游服务故障时，暂时切断对下游的调用
 *      防止故障蔓延，保护系统
 * 
 * 触发条件：
 * - 错误率超过阈值
 * - 响应时间过长
 * 
 * 状态：
 * - Closed（关闭）：正常
 * - Open（打开）：熔断，快速失败
 * - Half-Open（半开）：尝试恢复
 */
public class CircuitBreaker {}

/**
 * 降级（Fallback）
 * 
 * 概念：当服务不可用时，返回备选方案
 *      保证核心功能可用
 * 
 * 实现方式：
 * - 返回默认值
 * - 返回缓存数据
 * - 返回友好提示
 */
public class Fallback {}
```

### 工作流程

```java
/**
 * 熔断器工作流程
 */
public class BreakerFlow {
    // 状态转换
    /*
     * ┌────────┐  失败率过高   ┌───────┐
     * │Closed  │ ───────────→ │ Open  │
     * │正常   │               │ 熔断  │
     * └────────┘               └──┬────┘
     *    ↑                         │
     *    │   探测成功              │  超时后
     *    │   重置                  │  尝试
     *    │                         ↓
     *    │                      ┌────────┐
     *    └─────────────────────│ Half-  │
     *         成功             │ Open   │
     *                          │ 半开   │
     *                          └────────┘
     */
}
```

## 📖 实现方案

### Sentinel

```java
/**
 * Sentinel 实现
 */
public class SentinelDemo {
    // 限流
    /*
     * @SentinelResource(value = "test", 
     *                   blockHandler = "handleBlock")
     * public String test() {
     *     return "正常";
     * }
     * 
     * public String handleBlock(BlockException e) {
     *     return "限流了";
     * }
     */
    
    // 熔断
    /*
     * @SentinelResource(value = "test", 
     *                   fallback = "handleFallback")
     * public String test() {
     *     // 业务逻辑
     * }
     * 
     * public String handleFallback() {
     *     return "降级了";
     * }
     */
}
```

### Hystrix（已停止维护）

```java
/**
 * Hystrix 实现
 */
public class HystrixDemo {
    // 命令模式
    /*
     * public class CommandHello extends HystrixCommand<String> {
     *     public CommandHello() {
     *         super(HystrixCommandGroupKey.Factory.asKey("Group"));
     *     }
     *     
     *     @Override
     *     protected String run() {
     *         return "Hello";
     *     }
     *     
     *     @Override
     *     protected String getFallback() {
     *         return "降级";
     *     }
     * }
     * 
     * // 调用
     * String result = new CommandHello().execute();
     */
}
```

## 📖 面试真题

### Q1: 熔断和降级的区别？

**答：** 
- 熔断：防止故障蔓延，暂时切断调用
- 降级：返回备选方案，保证核心功能

### Q2: 熔断器状态？

**答：** 
- Closed：正常状态，统计失败率
- Open：熔断状态，直接返回失败
- Half-Open：尝试恢复，探测服务是否可用

---

**⭐ 重点：熔断和降级是保障系统可用性的重要手段**