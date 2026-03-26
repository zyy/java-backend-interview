---
layout: default
title: 分布式锁实现方案详解 ⭐⭐⭐
---
# 分布式锁实现方案详解 ⭐⭐⭐

## 🎯 面试题：如何实现分布式锁？Redis 分布式锁安全吗？

> 在分布式系统中，多个进程竞争同一个共享资源时，需要分布式锁来保证同一时刻只有一个进程能操作该资源。单机环境下 synchronized、ReentrantLock 可以解决问题，但分布式环境下必须引入分布式锁。

---

## 一、为什么需要分布式锁？

```
单机场景：
  Thread-A 获取锁 → 修改共享资源 → 释放锁
  Thread-B 在锁释放前无法进入 → 线程安全

分布式场景：
  Service-A (Node-1) 获取锁 → 修改共享资源 → 释放锁
  Service-B (Node-2) 无法感知 Node-1 的锁状态 → 两个节点同时修改 ❌
```

**常见应用场景：**
- 库存扣减（防止超卖）
- 分布式任务调度（防止任务重复执行）
- 幂等性保证
- 唯一 ID 生成（保证单机唯一）
- 缓存更新（防止缓存击穿）

---

## 二、分布式锁的实现方案对比

| 方案 | 可靠性 | 性能 | 实现复杂度 | 适用场景 |
|------|--------|------|-----------|---------|
| Redis SETNX | 高 | 极高 | 低 | 一般业务场景 |
| Redisson | 高 | 高 | 低 | 生产环境推荐 |
| ZooKeeper | 极高 | 中 | 中 | 高可靠性场景 |
| MySQL 悲观锁 | 中 | 低 | 低 | 低并发、对可靠性要求不高的场景 |
| Consul | 高 | 中 | 中 | 已有 Consul 基础设施 |

---

## 三、Redis 分布式锁：基础实现

### 最简单版本（不可用于生产）

```java
public class SimpleRedisLock {

    private RedisTemplate<String, String> redisTemplate;

    public boolean tryLock(String key, String value, long expireTime) {
        // SETNX + 过期时间
        return Boolean.TRUE.equals(
            redisTemplate.opsForValue()
                .setIfAbsent(key, value, Duration.ofSeconds(expireTime))
        );
    }

    public void unlock(String key, String value) {
        // 释放锁：判断是自己的锁才能释放
        String currentValue = redisTemplate.opsForValue().get(key);
        if (value.equals(currentValue)) {
            redisTemplate.delete(key);
        }
    }
}
```

### ⚠️ 问题一：原子性问题

```
错误流程：
  T1: GET key        → "uuid-1"（拿到了锁）
  T2: DEL key        → 删除成功
  T3: SETNX key uuid-2 → 设置成功（另一人拿到了锁）
  T4: DEL key        → uuid-1 删除 uuid-2 的锁 ❌

此时 uuid-1 的客户端把 uuid-2 的锁删掉了！
```

### 问题二：锁过期但业务未完成

```
场景：任务需要 30 秒，但锁只设置了 10 秒
T0:  客户端 A 获取锁（10s）
T10: 锁过期自动释放
T10: 客户端 B 获取锁
T10: 客户端 A 仍在执行（30s 才完成）
T10: 客户端 B 也在执行
→ 两个客户端同时操作共享资源 ❌
```

### 问题三：主从切换导致锁丢失

```
集群环境：
  T1: 客户端在 Master-1 获取锁
  T2: Master-1 宕机，Salve-1 晋升为新 Master
  T3: Salve-1 没有刚才的锁数据
  T4: 客户端 B 从新 Master 获取同一把锁
  → 两个客户端同时持有锁 ❌
```

---

## 四、Redisson：生产级分布式锁

### 为什么选择 Redisson？

```
Redisson 核心能力：
✅ 看门狗（Watchdog）：自动续期，防止锁提前释放
✅ 可重入锁：同线程可多次获取同一把锁
✅ 公平锁/读写锁/信号量/CountDownLatch 等工具
✅ RedLock 算法：多 Redis 实例加锁，解决主从切换问题
✅ 官方认可：Spring Boot Starter 集成
```

### 基本使用

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.25.0</version>
</dependency>
```

```yaml
spring:
  redis:
    redisson:
      config: |
        singleServerConfig:
          address: "redis://127.0.0.1:6379"
          database: 0
```

```java
@Service
public class OrderService {

    @Autowired
    private RedissonClient redissonClient;

    public void createOrder(OrderRequest request) {
        // 获取锁（默认 30 秒锁自动释放，看门狗每 10 秒续期一次）
        RLock lock = redissonClient.getLock("order:lock:" + request.getUserId());

        try {
            // 尝试加锁，最多等待 5 秒，锁定后 30 秒自动释放
            boolean locked = lock.tryLock(5, 30, TimeUnit.SECONDS);
            if (!locked) {
                throw new BizException("系统繁忙，请稍后重试");
            }

            // 业务逻辑
            doCreateOrder(request);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new BizException("系统异常");
        } finally {
            // 必须在 finally 中释放锁
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

---

## 五、看门狗机制（Watchdog）

### 自动续期原理

```
Redisson 看门狗工作流程：

锁被获取时：
  1. 记录 leaseTime（默认 30s）
  2. 启动定时任务，每 (leaseTime/3) = 10s 执行一次
  3. 定时任务执行：延长锁的过期时间 + leaseTime

锁被释放时：
  4. 定时任务被取消

如果显式传入 leaseTime：
  → 不启动看门狗，到期自动释放
  → 适用场景：业务执行时间可预估

如果不传 leaseTime（默认 -1）：
  → 启动看门狗，自动续期
  → 适用场景：业务执行时间不可预估
```

```java
// 使用看门狗（推荐）：锁自动续期，业务完成后再释放
RLock lock = redissonClient.getLock("resource:key");
lock.lock(); // 不传参数，看门狗自动续期

// 不使用看门狗：显式指定过期时间，业务执行完立刻释放
RLock lock = redissonClient.getLock("resource:key");
lock.lock(10, TimeUnit.SECONDS); // 10秒后自动释放，不续期
```

---

## 六、可重入锁原理

### 为什么需要可重入？

```
场景：外层方法加锁 → 调用的内层方法也要加同一把锁

❌ 不可重入：外层拿锁 → 内层阻塞等待 → 死锁
✅ 可重入：外层拿锁 → 内层检查锁持有者 → 同线程直接进入 → 不死锁
```

### Redisson 可重入实现

```java
// 可重入计数器记录在 hash 结构中
// KEYS[1] = 锁名称
// HASH_KEY = 线程 ID
// HASH_VALUE = 重入次数

// 加锁时
if (exists(lockKey)) {
    // 锁已存在，检查是否是同一线程
    if (threadId == hexists(lockKey, threadId)) {
        hincrby(lockKey, threadId, 1); // 重入次数 +1
        expire(lockKey, 30s);          // 续期
        return true;
    }
} else {
    // 首次加锁
    hset(lockKey, threadId, 1);
    expire(lockKey, 30s);
    return true;
}
```

```java
// Java 使用示例
public void outer() {
    RLock lock = redissonClient.getLock("shared-resource");
    lock.lock();
    try {
        // 外层逻辑
        inner(); // 递归调用同一把锁
    } finally {
        lock.unlock();
    }
}

public void inner() {
    RLock lock = redissonClient.getLock("shared-resource");
    lock.lock(); // 可重入，同线程直接通过
    try {
        // 内层逻辑
    } finally {
        lock.unlock();
    }
}
```

---

## 七、公平锁（Fair Lock）

```java
// 普通锁：不保证先到先得，高并发下可能产生饥饿
RLock lock = redissonClient.getLock("resource");

// 公平锁：按请求顺序排队，先到先得
RLock fairLock = redissonClient.getFairLock("resource");

fairLock.lock(10, TimeUnit.SECONDS);
// 内部实现：用 Redis 的有序集合（ZSET）记录请求顺序
```

---

## 八、RedLock：多实例分布式锁

### 为什么需要 RedLock？

```
单 Redis 实例的问题：
  Master 宕机 → 锁丢失 → 多客户端同时操作

RedLock 方案：
  在 N 个独立的 Redis 实例上加锁
  超过 N/2+1 个实例加锁成功，才认为获取了锁
  即使部分实例宕机，锁仍然有效
```

### Redisson 实现

```java
// 3 个独立 Redis 实例
RedissonClient redisson1 = Redisson.create(config1);
RedissonClient redisson2 = Redisson.create(config2);
RedissonClient redisson3 = Redisson.create(config3);

RedissonRedLock redLock = new RedissonRedLock(
    redisson1.getLock("resource"),
    redisson2.getLock("resource"),
    redisson3.getLock("resource")
);

try {
    // 尝试获取锁，最多等待 10s，锁定后 30s 自动释放
    redLock.tryLock(10, 30, TimeUnit.SECONDS);

    // 业务逻辑

} finally {
    redLock.unlock();
}
```

### RedLock 的争议

```
Claude Bernardin（Redis 作者） vs Redisson：

Redisson 观点：RedLock 更安全，少数实例宕机不影响
Redis 作者观点：
  - RedLock 不是完全可靠的（依赖时钟）
  - 单实例足够简单，RedLock 增加复杂度
  - 如果需要高可靠，用 Raft 协议的 ZooKeeper

结论：大多数业务场景，单实例 Redis 锁足够用。
      金融级场景建议用 ZooKeeper 或 etcd。
```

---

## 九、Redis vs ZooKeeper 对比

| 维度 | Redis | ZooKeeper |
|------|-------|-----------|
| 可靠性 | 主从切换可能丢锁 | ZAB 协议保证，强一致 |
| 性能 | 极高（内存操作） | 中（持久化 + 投票） |
| 实现复杂度 | 低 | 中 |
| 锁类型 | 独占锁、公平锁、读写锁 | 临时有序节点 |
| 过期机制 | TTL 自动过期 | 临时节点 + 心跳 |
| 宕机恢复 | 主从切换有窗口期 | 节点消失，立即感知 |
| 适用场景 | 高并发、一般可靠性 | 高可靠性、低并发 |

### ZooKeeper 分布式锁实现原理

```
锁创建流程（基于临时有序节点）：

/locks
  /order-0000000001  ← 最小，获得锁
  /order-0000000002
  /order-0000000003

Client-1 创建 order-0000000001 → 成为锁持有者 ✅
Client-2 创建 order-0000000002 → 监听 order-0000000001
Client-3 创建 order-0000000003 → 监听 order-0000000002

Client-1 完成 → 删除 order-0000000001
Client-2 收到通知 → 成为新的锁持有者 ✅
```

---

## 十、MySQL 分布式锁（兜底方案）

```sql
-- 方案一：利用唯一索引
CREATE TABLE distributed_lock (
    lock_key VARCHAR(64) PRIMARY KEY,
    lock_value VARCHAR(128) NOT NULL,
    expire_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lock_key (lock_key)
);

-- 获取锁
INSERT INTO distributed_lock (lock_key, lock_value, expire_at)
VALUES (#{lockKey}, #{lockValue}, DATE_ADD(NOW(), INTERVAL 30 SECOND))
ON DUPLICATE KEY UPDATE lock_value = lock_value; -- 幂等获取
```

```java
public boolean tryLock(String lockKey, String lockValue, int expireSeconds) {
    try {
        Lock record = new Lock();
        record.setLockKey(lockKey);
        record.setLockValue(lockValue);
        record.setExpireAt(LocalDateTime.now().plusSeconds(expireSeconds));
        lockMapper.insert(record);
        return true; // 成功（之前没有记录）
    } catch (DuplicateKeyException e) {
        return false; // 锁已被占用
    }
}

public void unlock(String lockKey, String lockValue) {
    // 只删除自己的锁
    lockMapper.deleteByKeyAndValue(lockKey, lockValue);
}
```

---

## 十一、高频面试题

**Q1: Redis 分布式锁有哪些坑？**
> 1. **锁误删**：释放锁时没判断锁持有者，并发释放了他人的锁 → 用 Lua 脚本保证原子性
> 2. **锁过期业务未完成**：锁 10s 但业务需 30s → 用 Redisson 看门狗自动续期
> 3. **主从切换丢锁**：单实例宕机 → 用 RedLock 或 Redisson 的多点锁
> 4. **可重入问题**：递归方法重复加锁 → 用 hash 记录线程 ID 和重入次数

**Q2: Redisson 的看门狗机制是什么？**
> 看门狗是 Redisson 实现的可重入锁续期机制。默认锁超时 30 秒，但 Redisson 每隔 10 秒检测一次锁是否还被持有，如果是则自动将 TTL 重置为 30 秒。这个过程直到锁被显式释放才停止。这样即使业务执行时间超过锁 TTL，也不会出现锁提前释放的问题。

**Q3: 为什么释放锁要用 Lua 脚本？**
> 释放锁需要先判断「这把锁是不是我加的」再删除，普通代码是两步操作，不是原子的。在并发场景下，判断和删除之间可能被其他线程插入，导致误删。Lua 脚本在 Redis 中执行是原子的：

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
```

**Q4: RedLock 有什么争议？**
> Redis 作者 antirez（Salvatore Sanfilippo）认为 RedLock 不可靠，因为它依赖分布式系统的时钟，而时钟漂移会导致锁失效。但大多数业务场景，单实例 Redis 锁 + Redisson 看门狗已经足够。金融级高可靠场景建议使用基于 Raft 协议的 ZooKeeper 或 etcd。

**Q5: 如何实现一个可重入的分布式锁？**
> 锁的数据结构用 Redis Hash，key 是锁名，field 是线程 ID，value 是重入次数。获取锁时：如果锁不存在，set field=1；如果锁存在且 field 等于当前线程 ID，field+1 并续期；否则返回失败。释放锁时：field-1，如果 field=0 则删除锁。整个过程用 Lua 脚本保证原子性。

**Q6: 分布式锁和分布式事务有什么区别？**
> 分布式锁解决的是「互斥」问题——同一时刻只有一个节点能操作共享资源。分布式事务解决的是「一致」问题——多个节点的操作要么全部成功，要么全部失败。两者解决的问题不同，但经常配合使用（比如在 TCC 事务中，Try 阶段用分布式锁保证资源预留的互斥性）。
