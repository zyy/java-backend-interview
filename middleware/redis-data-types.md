# Redis 数据类型

> Redis 核心数据结构

## 🎯 面试重点

- 各数据类型的应用场景
- 底层实现原理

## 📖 数据类型

### String

```java
/**
 * String 类型
 * 
 * 场景：
 * - 缓存
 * - 计数器
 * - 分布式锁（SETNX）
 * 
 * 命令：
 * SET key value
 * GET key
 * INCR counter
 * SETEX key 10 value
 */
```

### List

```java
/**
 * List 类型
 * 
 * 场景：
 * - 消息队列（LPUSH + BRPOP）
 * - 列表/时间线
 * 
 * 命令：
 * LPUSH/RPUSH key value
 * LRANGE key 0 -1
 */
```

### Hash

```java
/**
 * Hash 类型
 * 
 * 场景：
 * - 对象存储
 * - 购物车
 * 
 * 命令：
 * HSET key field value
 * HGET key field
 * HGETALL key
 */
```

### Set

```java
/**
 * Set 类型
 * 
 * 场景：
 * - 交集/并集/差集（共同好友）
 * - 去重
 * 
 * 命令：
 * SADD key member
 * SMEMBERS key
 * SINTER set1 set2
 */
```

### ZSet

```java
/**
 * ZSet（有序集合）
 * 
 * 场景：
 * - 排行榜
 * - 延迟队列
 * 
 * 命令：
 * ZADD key score member
 * ZRANGE key 0 10
 * ZRANK key member
 */
```

## 📖 面试真题

### Q1: Redis 为什么快？

**答：** 内存存储、单线程避免了锁竞争、I/O 多路复用。

---

**⭐ 重点：理解各类型的应用场景**