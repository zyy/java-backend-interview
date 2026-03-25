# Redis 分布式锁

> 分布式环境下的锁实现

## 🎯 面试重点

- 分布式锁的实现方式
- Redis 分布式锁的问题

## 📖 实现方式

### SET NX

```java
/**
 * Redis 分布式锁
 */
public class DistributedLockRedis {
    // 简单实现
    /*
     * SET lock_key unique_value NX PX 30000
     * 
     * NX：不存在时设置
     * PX：过期时间（毫秒）
     * 
     * 释放锁：Lua 脚本比较并删除
     * if redis.call('get', KEYS[1]) == ARGV[1] then
     *     return redis.call('del', KEYS[1])
     * else
     *     return 0
     * end
     */
}
```

### Redisson

```java
/**
 * Redisson 实现
 */
public class RedissonLock {
    // 使用
    /*
     * RLock lock = redissonClient.getLock("lock_key");
     * lock.lock();
     * try {
     *     // 业务逻辑
     * } finally {
     *     lock.unlock();
     * }
     */
}
```

## 📖 面试真题

### Q1: 分布式锁的问题？

**答：** 
- 死锁：设置过期时间
- 误删：使用唯一标识
- 不可重入：可使用 Redisson

---

**⭐ 重点：分布式锁是分布式系统的基础**