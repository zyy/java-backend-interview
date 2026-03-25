# 负载均衡策略

> 分发流量的核心策略

## 🎯 面试重点

- 常见负载均衡算法
- 各算法的适用场景
- 实际使用示例

## 📖 负载均衡算法

### 随机

```java
/**
 * 随机算法
 * 
 * 优点：实现简单
 * 缺点：不考虑服务器状态
 */
public class RandomLB {
    // 实现
    /*
     * int index = (int) (Math.random() * servers.size());
     * return servers.get(index);
     */
}
```

### 轮询

```java
/**
 * 轮询算法
 * 
 * 优点：请求均匀分布
 * 缺点：不考虑服务器性能差异
 */
public class RoundRobinLB {
    // 实现
    /*
     * int index = counter.getAndIncrement() % servers.size();
     * return servers.get(index);
     * 
     * 权重轮询：
     * int index = currentIndex;
     * while (true) {
     *     index = (index + 1) % servers.size();
     *     if (servers.get(index).getWeight() > 0) {
     *         return servers.get(index);
     *     }
     * }
     */
}
```

### 加权轮询

```java
/**
 * 加权轮询
 * 
 * 根据服务器性能分配权重
 */
public class WeightedRoundRobin {
    // 示例
    /*
     * Server A: weight=3
     * Server B: weight=2
     * Server C: weight=1
     * 
     * 分配：A-A-A-B-B-C
     */
}
```

### 最少连接

```java
/**
 * 最少连接算法
 * 
 * 选择连接数最少的服务器
 * 适用于长连接场景
 */
public class LeastConnection {
    // 实现
    /*
     * Server min = null;
     * for (Server s : servers) {
     *     if (min == null || s.getActiveConnections() < min.getActiveConnections()) {
     *         min = s;
     *     }
     * }
     * return min;
     */
}
```

### 一致性哈希

```java
/**
 * 一致性哈希
 * 
 * 相同请求路由到相同服务器
 * 适合缓存场景
 */
public class ConsistentHash {
    // 实现
    /*
     * HashRing ring = new HashRing();
     * ring.add(serverA, 100);
     * ring.add(serverB, 100);
     * 
     * Server server = ring.get(hash(request));
     */
}
```

## 📖 实际使用

### Ribbon

```java
/**
 * Ribbon 使用
 */
public class RibbonDemo {
    // 负载均衡策略
    /*
     * IRule:
     * - RoundRobinRule：轮询
     * - RandomRule：随机
     * - WeightedResponseTimeRule：响应时间加权
     * - BestAvailableRule：选择最空闲
     */
    
    // 配置
    /*
     * service-provider:
     *   ribbon:
     *     NFLoadBalancerRuleClassName: com.netflix.loadbalancer.RandomRule
     */
}
```

## 📖 面试真题

### Q1: Nginx 负载均衡策略？

**答：** 轮询、加权轮询、IP 哈希、最少连接、一致性哈希。

### Q2: Ribbon 的主要策略？

**答：** 轮询、随机、响应时间加权、最空闲优先。

---

**⭐ 重点：负载均衡是分布式系统的基础组件**