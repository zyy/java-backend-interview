---
layout: default
title: 订单超时自动取消与 Redis 延时任务实现 ⭐⭐⭐
---
# 订单超时自动取消与 Redis 延时任务实现 ⭐⭐⭐

## 🎯 面试题：订单超时未支付如何自动取消？Redis 延时任务是怎么实现的？

---

## 一、订单超时取消的业务场景

```
用户下单
    ↓
创建订单（状态：待支付）
    ↓
如果 15 分钟内未支付
    → 自动取消订单
    → 释放库存
    → 发送通知
```

**典型超时场景：**
- 电商订单：15 分钟 / 30 分钟超时未支付
- 优惠券领取：领券后 24 小时未使用自动退回
- 活动报名：报名后超时未支付自动释放名额
- 会议室预约：预约超时自动释放

---

## 二、实现方案对比

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **定时扫描** | 每秒查 DB 扫描超时订单 | 实现简单 | 浪费资源，有延迟 |
| **JDK DelayQueue** | 内存队列，只适合单机 | 零外部依赖 | 节点重启数据丢失 |
| **Redis ZSet** | 按到期时间戳排序，轮询获取到期任务 | 天然分布式，数据可靠 | 需要轮询 |
| **RabbitMQ 延时队列** | MQ 延时投递消息 | 成熟方案 | 需要额外部署 MQ |
| **RocketMQ 延时消息** | 消息延时投递 | 功能完善 | 特定版本支持 |
| **时间轮** | Netty HashedWheelTimer | 高精度 | 仅单机 |

---

## 三、Redis ZSet 延时队列原理

### 核心数据结构

```
ZSet = 有序集合
  member = 订单 ID
  score  = 超时时间戳（Unix 时间毫秒数）

ZREMRANGEBYSCORE 获取已到期的任务
ZRANGEBYSCORE   获取即将到期的任务
```

```
时间轴 ──────────────────────────────────────────────────▶
        │
        │ score = 1743000000000（未来）
        │ score = 1742999900000（未来）
        │ score = 1742999800000（未来）
        │
────────┼────────────────────────────────────────────────
  已到期的任务 score <= now
```

### 执行流程

```
1. 创建订单时
   ZADD order:delay:cancel {orderId} {超时时间戳}

2. 后台线程轮询（每 1 秒）
   ZRANGEBYSCORE order:delay:cancel 0 {now} LIMIT 0 100
   → 取出已到期的订单

3. 检查订单状态
   ├── 已是已支付/已取消 → 从 ZSet 删除
   └── 仍为待支付 → 执行取消逻辑
       ├── 更新订单状态
       ├── 释放库存
       ├── 发送取消通知
       └── 从 ZSet 删除

4. 删除已处理的任务
   ZREM order:delay:cancel {orderId}
```

---

## 四、完整代码实现

### 1. 订单服务（下单时注册延时任务）

```java
@Service
@Slf4j
public class OrderService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final String DELAY_QUEUE_KEY = "order:delay:cancel";
    private static final long ORDER_TIMEOUT_MS = 15 * 60 * 1000L; // 15 分钟

    /**
     * 创建订单 → 写入延时队列
     */
    @Transactional
    public Order createOrder(OrderCreateRequest request) {
        // 1. 创建订单
        Order order = new Order();
        order.setId(generateOrderId());
        order.setStatus(OrderStatus.PENDING_PAYMENT);
        order.setAmount(request.getAmount());
        order.setUserId(request.getUserId());
        order.setCreateTime(LocalDateTime.now());
        orderMapper.insert(order);

        // 2. 加入延时取消队列（超时时间 = 当前时间 + 15 分钟）
        long expireTime = System.currentTimeMillis() + ORDER_TIMEOUT_MS;
        redisTemplate.opsForZSet().add(
            DELAY_QUEUE_KEY,
            order.getId(),
            expireTime
        );

        // 3. 记录订单和超时时间的映射（便于取消时快速定位）
        String orderTimeKey = "order:expire:" + order.getId();
        redisTemplate.opsForValue().set(orderTimeKey, String.valueOf(expireTime));

        log.info("[Order] Created: orderId={}, expireTime={}", order.getId(), expireTime);
        return order;
    }

    /**
     * 用户支付成功 → 从延时队列移除
     */
    public void onOrderPaid(String orderId) {
        redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);
        log.info("[Order] Paid, removed from delay queue: orderId={}", orderId);
    }

    /**
     * 手动取消订单 → 从延时队列移除
     */
    public void cancelOrder(String orderId) {
        redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);
        // 执行取消逻辑...
        log.info("[Order] Cancelled: orderId={}", orderId);
    }
}
```

### 2. 延时队列消费者（后台轮询）

```java
@Component
@Slf4j
public class OrderDelayQueueConsumer {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private InventoryService inventoryService;
    @Autowired
    private NotificationService notificationService;

    private static final String DELAY_QUEUE_KEY = "order:delay:cancel";
    private static final int BATCH_SIZE = 100;  // 每批处理 100 条

    /**
     * 每秒轮询一次，取出已到期的订单
     */
    @Scheduled(fixedRate = 1000)
    public void pollExpiredOrders() {
        long now = System.currentTimeMillis();

        // 取出 score <= now 的所有成员（0 ~ now 区间）
        Set<String> expiredOrderIds = redisTemplate.opsForZSet()
            .rangeByScore(DELAY_QUEUE_KEY, 0, now, new RangeOptions().limit(0, BATCH_SIZE));

        if (expiredOrderIds == null || expiredOrderIds.isEmpty()) {
            return;
        }

        log.info("[DelayQueue] Polled {} expired orders at {}", expiredOrderIds.size(), now);

        for (String orderId : expiredOrderIds) {
            processExpiredOrder(orderId);
        }
    }

    private void processExpiredOrder(String orderId) {
        // 1. 原子抢锁，防止多节点重复处理
        String lockKey = "order:cancel:lock:" + orderId;
        Boolean acquired = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1", Duration.ofSeconds(30));

        if (!Boolean.TRUE.equals(acquired)) {
            // 已被其他节点处理，直接移除
            redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);
            return;
        }

        try {
            // 2. 查询订单状态
            Order order = orderMapper.selectById(orderId);
            if (order == null) {
                log.warn("[DelayQueue] Order not found: {}", orderId);
                redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);
                return;
            }

            // 3. 只有待支付状态才需要取消
            if (order.getStatus() != OrderStatus.PENDING_PAYMENT) {
                log.info("[DelayQueue] Order status changed, skip cancel: orderId={}, status={}",
                    orderId, order.getStatus());
                redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);
                return;
            }

            // 4. 执行取消（订单状态 + 库存释放 + 通知）
            executeCancel(order);

        } catch (Exception e) {
            log.error("[DelayQueue] Failed to cancel order: {}", orderId, e);
            // 失败时不删除 ZSet，下次重试（带退避）
            // 或者将 score 后移 N 秒后重试
            moveToRetry(orderId, 60_000); // 延后 1 分钟重试
        } finally {
            redisTemplate.delete(lockKey);
        }
    }

    private void executeCancel(Order order) {
        String orderId = order.getId();

        // 状态更新（乐观锁防并发）
        int updated = orderMapper.updateStatusWithVersion(
            orderId,
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.CANCELLED_TIMEOUT
        );

        if (updated == 0) {
            log.warn("[DelayQueue] Optimistic lock failed, order already processed: {}", orderId);
            return;
        }

        // 释放库存
        inventoryService.releaseStock(orderId);

        // 发送通知
        notificationService.sendOrderCancelledNotice(order);

        // 从延时队列移除
        redisTemplate.opsForZSet().remove(DELAY_QUEUE_KEY, orderId);

        log.info("[DelayQueue] Order cancelled: orderId={}, userId={}", orderId, order.getUserId());
    }

    /**
     * 取消失败后延后重试（避免立即重试还是失败）
     */
    private void moveToRetry(String orderId, long delayMs) {
        double newScore = System.currentTimeMillis() + delayMs;
        redisTemplate.opsForZSet().add(DELAY_QUEUE_KEY, orderId, newScore);
    }
}
```

### 3. 使用 Lua 脚本保证原子性

```java
@Component
public class OrderDelayQueueLua {

    private final RedisScript<List> pollAndRemoveScript;

    public OrderDelayQueueLua() {
        this.pollAndRemoveScript = new DefaultRedisScript<>( // ⚠️ 实际应存 .lua 文件
            "local expired = redis.call('ZRANGEBYSCORE', KEYS[1], 0, ARGV[1], 'LIMIT', 0, ARGV[2])\n" +
            "if #expired > 0 then\n" +
            "  redis.call('ZREM', KEYS[1], unpack(expired))\n" +
            "end\n" +
            "return expired",
            List.class
        );
    }

    /**
     * ZRANGEBYSCORE + ZREM 合并为原子操作
     * 避免取出数据后在删除前就被其他节点处理
     */
    public List<String> pollExpiredAtomically(String key, long now, int limit) {
        return redisTemplate.execute(
            pollAndRemoveScript,
            List.of(key),
            String.valueOf(now),
            String.valueOf(limit)
        );
    }
}
```

---

## 五、延时队列的进阶问题

### 1. 多节点并发安全问题

```
问题：两个节点同时查到同一个过期订单，都去取消，导致重复取消

解决：分布式锁 + 乐观锁双重保险

分布式锁：SETNX lock:order:cancel:{orderId} 1 EX 30
  → 抢到的才执行
  → 没抢到的直接从 ZSet 移除（已被处理）

乐观锁：UPDATE order SET status=?, version=version+1
  WHERE id=? AND status=? AND version=?
  → 状态已变则不更新，说明已被处理
```

### 2. 订单超时时间动态化

```
问题：订单创建时不知道具体超时时间

解决：ZSet score 存的是绝对时间戳，而非相对时间

如果需要修改已有订单的超时时间：
  ZREM old_key orderId  → 删除旧的
  ZADD new_key orderId newScore  → 添加新的
```

### 3. 批量取消优化

```java
// 单个订单逐个处理：N 次 DB 操作
for (String orderId : expiredOrders) {
    processExpiredOrder(orderId); // 每个都有 DB 查询 + 更新
}

// 批量处理：减少 DB 交互次数
public void batchCancelOrders(List<String> orderIds) {
    if (orderIds.isEmpty()) return;

    // 1. 批量查询订单（IN 查询）
    List<Order> orders = orderMapper.selectByIds(orderIds);

    // 2. 过滤出待支付的
    List<Order> toCancel = orders.stream()
        .filter(o -> o.getStatus() == OrderStatus.PENDING_PAYMENT)
        .toList();

    if (toCancel.isEmpty()) return;

    // 3. 批量更新状态
    orderMapper.batchUpdateStatus(
        toCancel.stream().map(Order::getId).toList(),
        OrderStatus.CANCELLED_TIMEOUT
    );

    // 4. 批量释放库存
    inventoryService.batchReleaseStock(
        toCancel.stream().map(Order::getId).toList()
    );

    // 5. 批量发送通知
    notificationService.batchSendCancelledNotice(toCancel);
}
```

### 4. 监控告警

```yaml
# 关键监控指标
- order_delay_queue_size: ZSet 长度（积压监控）
- order_cancel_count: 每分钟取消订单数
- order_cancel_failed_count: 取消失败数
- order_cancel_latency: 从超时到实际取消的延迟（应 < 5 秒）

# 告警规则
alert: OrderDelayQueueBacklog
  expr: order_delay_queue_size > 10000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "延时队列积压严重，请检查消费者是否正常"
```

### 5. 数据持久化与恢复

```
Redis 挂了怎么办？

方案一：订单创建时同时写 MySQL（超时时间字段）
       Redis 故障后，从 MySQL 扫描超时订单重建队列

方案二：开启 Redis AOF 持久化（fsync=everysec）
       故障恢复后自动加载数据

方案三：延时任务存 MySQL，Redis 仅作加速
       消费者先查 Redis，miss 后查 MySQL
```

```java
// 启动时从 MySQL 重建 Redis 延时队列
@PostConstruct
public void rebuildDelayQueue() {
    // 查找所有待支付且已超时的订单
    List<Order> expiredOrders = orderMapper.selectExpiredPendingOrders();
    if (expiredOrders.isEmpty()) return;

    Set<ZSetOperations.TypedTuple<String>> tuples = expiredOrders.stream()
        .map(o -> ZSetOperations.TypedTuple.of(
            o.getId(),
            (double) o.getCreateTime().plusMinutes(15).toInstant(ZoneOffset.of("+8")).toEpochMilli()
        ))
        .collect(Collectors.toSet());

    redisTemplate.opsForZSet().add(DELAY_QUEUE_KEY, tuples);
    log.info("[DelayQueue] Rebuilt from DB: {} orders", expiredOrders.size());
}
```

---

## 六、其他延时任务实现方案

### 1. RabbitMQ 延时队列

```
Exchange 类型：x-delayed-message（需要 rabbitmq_delayed_message_exchange 插件）
              或使用 TTL + DLX（死信队列）模拟

消息 TTL = 超时时间差

订单超时 15 分钟：
  发送消息，TTL = 15 * 60 * 1000
  → 15 分钟后消息投递到消费者
  → 消费者检查订单状态，执行取消
```

```java
// RabbitMQ 延时消息
rabbitTemplate.convertAndSend(
    "order.delay.exchange",
    "order.cancel",
    orderId,
    message -> {
        message.getMessageProperties().setDelay(15 * 60 * 1000); // 15 分钟
        return message;
    }
);
```

### 2. Netty 时间轮（仅适合单机高精度场景）

```
适用：支付网关超时、大量短时延时任务（毫秒级）

原理：
  tickDuration = 100ms（每格走一次）
  ticksPerWheel = 60（一轮 6 秒）
  wheel 数组 = 60 个双向链表
  
  任务按到期时间挂在对应格子上
  时钟每走一格检查格子是否有到期任务
```

### 3. Redisson RDelayedQueue（推荐）

```
封装了 Redis ZSet，提供更简洁的 API
```

```java
@Autowired
private RedissonClient redisson;

public void scheduleOrderCancel(String orderId, long delayMs) {
    RDelayedQueue<String> queue = redisson.getDelayedQueue(
        redisson.getQueue("order:delay:cancel")
    );
    // delayMs 毫秒后自动弹出
    queue.offer(orderId, delayMs, TimeUnit.MILLISECONDS);
}

// 消费者
new Thread(() -> {
    RDelayedQueue<String> queue = redisson.getDelayedQueue(
        redisson.getQueue("order:delay:cancel")
    );
    while (true) {
        String orderId = queue.poll(10, TimeUnit.SECONDS);
        if (orderId != null) {
            processExpiredOrder(orderId);
        }
    }
}).start();
```

---

## 七、高频面试题

**Q1: Redis ZSet 延时队列的执行流程是什么？**
> ① 下单时 ZADD 写入，score = 当前时间 + 超时时间；② 后台线程每秒轮询 ZRANGEBYSCORE 取 score <= now 的订单；③ 取到后先抢分布式锁，确保持有唯一执行权；④ 检查订单状态是否仍为待支付；⑤ 状态正确则执行取消逻辑，ZREM 从队列移除。

**Q2: 如何防止重复取消同一个订单？**
> 两层保险：① 分布式锁 SETNX，抢到的才执行，没抢到的直接移除；② 乐观锁 UPDATE WHERE status=?，状态已变说明已被处理，UPDATE 影响行数为 0 时跳过。

**Q3: Redis 挂了延时任务会丢失吗？**
> 有风险。通过三种手段缓解：① 开启 Redis AOF 持久化（everysec）；② 订单表存超时时间，启动时从 MySQL 扫描超时订单重建 Redis 队列；③ 核心业务用 DB 定时扫描兜底（不依赖 Redis）。

**Q4: ZRANGEBYSCORE 会阻塞吗？性能如何？**
> 不会阻塞，读操作 O(log N + M)。N = 集合大小，M = 取出元素数量。只要集合大小可控（百万级以内），单次查询毫秒级。可通过分 key 方案（按时间分桶）进一步优化。

**Q5: 延时任务能否精确到秒？**
> Redis ZSet 的精确度是毫秒级，受轮询间隔影响。实际取消延迟 = 轮询间隔 + 处理耗时。如果需要更高精度，可缩短轮询间隔（如 100ms），但会增加 Redis 压力。Netty 时间轮可实现毫秒级精度，但仅适合单机。

---

**参考链接：**
- [Redisson 延时队列文档](https://github.com/redisson/redisson/wiki)
- [RabbitMQ 延时消息方案](https://www.rabbitmq.com/)
- [美团订单超时处理实践](https://tech.meituan.com/2018/01/19/order-system-design.html)
