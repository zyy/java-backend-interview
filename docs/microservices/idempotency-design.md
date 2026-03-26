---
layout: default
title: 接口幂等性方案详解 ⭐⭐⭐
---
# 接口幂等性方案详解 ⭐⭐⭐

## 🎯 面试题：如何保证接口幂等？重复提交怎么办？

> **幂等**：同一个操作执行一次和执行多次，效果完全相同。接口幂等是分布式系统中最容易被忽视、但一旦出问题就极其致命的问题——重复扣款、重复下单、重复发券，后果不堪设想。

---

## 一、为什么需要幂等？

```
❌ 没有幂等保障的典型事故：

用户点击支付 → 网络超时 → 前端重试
    ↓
请求 A：查询余额 1000 → 扣款 100 → 余额 900（还没来得及返回）
请求 B：查询余额 900  → 扣款 100 → 余额 800 ❌（扣了两次）

用户刷新页面 → 前端重复提交
    ↓
订单 A：创建订单 → 返回成功
订单 B：创建订单 → 又创建了一个订单 ❌
```

**幂等的核心价值：**
- 网络重试、页面刷新、消息重投不产生副作用
- 分布式系统局部失败后重试不导致数据不一致
- 金融、电商、库存等高风险场景的兜底保障

---

## 二、HTTP 方法的幂等性

| 方法 | 幂等 | 说明 |
|------|------|------|
| GET | ✅ | 只读取资源，无副作用 |
| PUT | ✅ | 替换为相同值，效果相同 |
| DELETE | ✅ | 删除已删除的资源，返回 404 仍算幂等 |
| POST | ❌ | 非幂等，如创建订单每次生成新 ID |
| PATCH | ❌ | 通常非幂等（除非增量操作）|

---

## 三、幂等方案全景图

```
┌────────────────────────────────────────────────────────────┐
│                    幂等方案选择矩阵                            │
│                                                              │
│  写请求      │ 读请求      │ 适用方案                         │
│  ────────────┼─────────────┼─────────────────────────────── │
│  创建资源     │             │  唯一 Token + 状态表             │
│  更新资源     │             │  乐观锁 / 唯一约束 / 去重 Key     │
│  删除资源     │             │  查询后删除（先查后删）            │
│  ────────────┼─────────────┼─────────────────────────────── │
│              │ 列表查询     │  不需要幂等（天然幂等）            │
│              │ 详情查询     │  不需要幂等（天然幂等）            │
└────────────────────────────────────────────────────────────┘
```

---

## 四、方案一：唯一 Token 机制（最通用）

### 核心思路

```
请求流程：
  客户端生成唯一 token（如 UUID）→ 随请求一起发送
  服务端以 token 为 key 写 Redis → setnx(token, "1")
  ── token 不存在 → 执行业务 → setnx 成功，写入成功标记
  ── token 已存在 → 直接返回成功，不重复执行

关键：token 需要客户端生成，前端保证
```

### 代码实现

```java
// ========== 注解定义 ==========
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Idempotent {
    /** Token 请求头名称 */
    String header() default "X-Idempotent-Token";
    /** 幂等有效时间（秒），默认 10 秒 */
    long expireSeconds() default 10;
}

// ========== 拦截器 ==========
@Component
@Slf4j
public class IdempotentInterceptor implements HandlerInterceptor {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) throws Exception {
        if (!(handler instanceof HandlerMethod)) return true;

        HandlerMethod hm = (HandlerMethod) handler;
        Idempotent anno = hm.getMethodAnnotation(Idempotent.class);
        if (anno == null) return true;

        String token = request.getHeader(anno.header());
        if (token == null || token.isBlank()) {
            response.setContentType("application/json;charset=utf-8");
            response.getWriter().write("{\"code\":400,\"msg\":\"缺少幂等 Token\"}");
            return false;
        }

        String key = "idempotent:" + token;
        // SETNX + TTL：原子操作，成功则允许执行业务
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent(key, "1", Duration.ofSeconds(anno.expireSeconds()));

        if (Boolean.TRUE.equals(success)) {
            // 第一次请求，放行
            return true;
        } else {
            // 重复请求，直接返回成功（不重复执行业务）
            response.setContentType("application/json;charset=utf-8");
            response.getWriter().write("{\"code\":200,\"msg\":\"请求已处理，请勿重复提交\"}");
            return false;
        }
    }
}

// ========== 前端调用示例 ==========
// POST /api/order/create
// Header: X-Idempotent-Token: 550e8400-e29b-41d4-a716-446655440000
```

### 前端实现

```javascript
// 发起请求时自动注入 Token
const idempotentToken = localStorage.getItem('idempotent-token') ||
    (localStorage.setItem('idempotent-token', crypto.randomUUID()), crypto.randomUUID());

fetch('/api/order/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Idempotent-Token': idempotentToken,
  },
  body: JSON.stringify(orderData)
})
```

### 进阶：结合数据库记录

```java
// 幂等表设计（用于需要持久化追踪的场景）
CREATE TABLE `idempotent_record` (
    `id`          BIGINT PRIMARY KEY AUTO_INCREMENT,
    `token`       VARCHAR(64) NOT NULL UNIQUE COMMENT '幂等 Token',
    `biz_type`    VARCHAR(32) NOT NULL COMMENT '业务类型: ORDER/PAYMENT/REFUND',
    `biz_id`      VARCHAR(64) NULL COMMENT '关联业务ID',
    `status`      TINYINT NOT NULL DEFAULT 1 COMMENT '1-处理中 2-成功 3-失败',
    `result`      TEXT NULL COMMENT '处理结果',
    `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_biz_type_token` (`biz_type`, `token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

// 查询幂等记录（防重复处理）
IdempotentRecord record = idempotentMapper.selectByToken(bizType, token);
if (record == null) {
    // 首次处理
    idempotentMapper.insert(bizType, token, IdempotentStatus.PROCESSING);
    try {
        // 执行业务
        String result = doBusiness(request);
        idempotentMapper.updateStatus(token, IdempotentStatus.SUCCESS, result);
        return result;
    } catch (Exception e) {
        idempotentMapper.updateStatus(token, IdempotentStatus.FAILED, e.getMessage());
        throw e;
    }
} else {
    // 非首次，幂等返回
    if (record.getStatus() == IdempotentStatus.SUCCESS) {
        return record.getResult(); // 返回之前的结果
    } else if (record.getStatus() == IdempotentStatus.PROCESSING) {
        throw new BizException("请求正在处理中，请稍候");
    }
}
```

---

## 五、方案二：基于唯一键约束（数据库幂等）

### 适用场景

```
订单号、支付流水号、退款单号 等业务 ID 可提前确定时
直接在数据库层面保证幂等
```

```java
// 订单创建：用业务 ID 作为唯一键
@Service
public class OrderService {

    @Autowired
    private OrderMapper orderMapper;

    /**
     * 幂等创建订单：业务 ID 已确定（如客户端生成的 UUID）
     */
    public Order createOrder(OrderCreateRequest request) {
        try {
            Order order = new Order();
            order.setOrderNo(request.getOrderNo()); // 客户端生成，确保唯一
            order.setUserId(request.getUserId());
            order.setAmount(request.getAmount());
            order.setStatus(OrderStatus.PENDING_PAYMENT);
            orderMapper.insertSelective(order);
            return order;
        } catch (DuplicateKeyException e) {
            // 唯一键冲突 → 订单已存在，查询返回
            log.info("订单已存在，直接返回: orderNo={}", request.getOrderNo());
            return orderMapper.selectByOrderNo(request.getOrderNo());
        }
    }
}
```

### 防重表（专门用于幂等的辅助表）

```sql
-- 防重表设计
CREATE TABLE `dedup_log` (
    `dedup_key`   VARCHAR(128) PRIMARY KEY,
    `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `expire_at`   DATETIME NOT NULL COMMENT '过期时间，TTL 自动清理',
    INDEX `idx_expire` (`expire_at`)
);

-- 订单创建时使用
INSERT INTO dedup_log (dedup_key, expire_at)
VALUES (#{dedupKey}, DATE_ADD(NOW(), INTERVAL 7 DAY))
ON DUPLICATE KEY UPDATE dedup_key = dedup_key;
-- ON DUPLICATE KEY：插入失败说明已存在，幂等返回
```

```java
public void createOrderWithDedup(OrderCreateRequest request) {
    String dedupKey = "order:create:" + request.getUserId() + ":" + request.getProductId();

    int affected = deduplicationMapper.insertDedup(dedupKey,
        LocalDateTime.now().plusDays(7));

    if (affected == 0) {
        throw new BizException("订单正在处理中，请勿重复提交");
    }

    // 执行业务逻辑...
}
```

---

## 六、方案三：乐观锁（更新场景）

### 适用场景

```
余额扣减、库存扣减、数量更新等「读取-修改-写入」场景

原理：通过 version 字段检测并发冲突
```

```java
// ❌ 不安全：先查后改，非原子
Account account = accountMapper.selectByUserId(userId);
account.setBalance(account.getBalance() - amount);
accountMapper.updateById(account);

// ✅ 乐观锁：WHERE version = ? → version + 1
@Service
public class AccountService {

    @Autowired
    private AccountMapper accountMapper;

    /**
     * 幂等扣款：同一个 version 只能更新成功一次
     */
    public boolean deductBalance(Long userId, BigDecimal amount) {
        int affected = accountMapper.deductWithVersion(userId, amount);
        // UPDATE account SET balance = balance - #{amount}, version = version + 1
        // WHERE id = #{userId} AND balance >= #{amount} AND version = #{expectedVersion}

        if (affected == 0) {
            // version 不匹配或余额不足，说明被并发修改，扣款失败
            return false;
        }
        return true;
    }
}
```

### 库存扣减的乐观锁

```java
// 防超卖：扣减库存
public boolean deductStock(Long skuId, int count) {
    // 方式一：SQL 层面保证幂等（扣减数量为负时不更新）
    int affected = stockMapper.updateStockWithVersion(
        skuId, count,
        "version = version + 1",
        "stock >= " + count
    );
    // UPDATE stock SET stock = stock - #{count}, version = version + 1
    // WHERE sku_id = #{skuId} AND stock >= #{count} AND version = #{version}

    return affected > 0;
}
```

---

## 七、方案四：Redis 去重 Key（最轻量）

### 适用场景

```
接口响应时间敏感、不需要持久化的幂等
基于请求特征（用户 ID + 业务类型 + 时间窗口）生成去重 key
```

```java
@Service
@Slf4j
public class RedisIdempotentService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    private static final String IDEMPOTENT_PREFIX = "idempotent:";

    /**
     * 通用幂等检查
     * @param bizKey  业务标识，如 "payment", "order"
     * @param requestId 请求 ID，如 orderId, paymentId
     * @param ttlSeconds 防重有效期
     * @return true=首次请求可继续，false=重复请求
     */
    public boolean tryAcquire(String bizKey, String requestId, long ttlSeconds) {
        String key = IDEMPOTENT_PREFIX + bizKey + ":" + requestId;
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent(key, "processing", Duration.ofSeconds(ttlSeconds));

        if (Boolean.TRUE.equals(success)) {
            return true; // 首次
        }

        // 检查是否已完成（可记录结果）
        String value = redisTemplate.opsForValue().get(key);
        if ("processing".equals(value)) {
            return false; // 正在处理中（上一个请求还没完成）
        }
        // value 可能是 "success" 或具体结果，说明已完成，直接返回
        return false;
    }

    /**
     * 标记处理完成，可记录结果
     */
    public void markDone(String bizKey, String requestId, String result) {
        String key = IDEMPOTENT_PREFIX + bizKey + ":" + requestId;
        redisTemplate.opsForValue().set(key, "done:" + result);
    }

    /**
     * 基于时间窗口的去重（如每用户每分钟只能提交一次）
     */
    public boolean checkTimeWindow(Long userId, String action, int windowSeconds) {
        String key = String.format("idempotent:window:%d:%s", userId, action);
        Long count = redisTemplate.opsForValue().increment(key, 1);
        if (count == 1) {
            redisTemplate.expire(key, windowSeconds, TimeUnit.SECONDS);
        }
        return count != null && count <= 1;
    }
}
```

### 使用示例

```java
@PostMapping("/pay")
public Result pay(@RequestBody PayRequest request) {
    // 幂等检查
    if (!idempotentService.tryAcquire("pay", request.getPaymentId(), 300)) {
        return Result.error("订单正在支付中，请勿重复提交");
    }

    try {
        PaymentResult result = paymentService.processPay(request);
        idempotentService.markDone("pay", request.getPaymentId(), result.toString());
        return Result.success(result);
    } catch (Exception e) {
        // 异常时不删除 key，下次重试仍可执行
        throw e;
    }
}
```

---

## 八、MQ 消费幂等（高频场景）

### 问题

```
消息队列重投机制 → 同一消息可能被消费多次

MQ 消费幂等 = 消息去重

常见场景：
  - 支付成功消息被重复消费 → 重复发货
  - 库存扣减消息被重复消费 → 库存扣多次
```

### 方案一：消息表 + 唯一消息 ID

```java
// 消费者
@RabbitListener(queues = "payment.success.queue")
public void handlePaymentSuccess(PaymentMessage msg) {
    String msgId = msg.getMessageId();

    // 1. 先查消息处理记录
    MessageLog log = messageLogMapper.selectByMsgId(msgId);
    if (log != null) {
        log.info("消息已处理，跳过: msgId={}", msgId);
        return;
    }

    // 2. 记录处理中
    messageLogMapper.insert(MessageLog.processing(msgId));

    try {
        // 3. 执行业务
        orderService.confirmOrder(msg.getOrderId());
        messageLogMapper.updateStatus(msgId, MessageStatus.SUCCESS);
    } catch (Exception e) {
        messageLogMapper.updateStatus(msgId, MessageStatus.FAILED);
        throw e; // 重新入队重试
    }
}
```

### 方案二：Redis 消息去重

```java
@RabbitListener(queues = "payment.success.queue")
public void handlePaymentSuccess(PaymentMessage msg) {
    String msgId = msg.getMessageId();
    String key = "mq:consumed:" + msgId;

    // SETNX 原子操作，防止重复消费
    Boolean success = redisTemplate.opsForValue()
        .setIfAbsent(key, "1", Duration.ofHours(24));

    if (!Boolean.TRUE.equals(success)) {
        log.info("消息已消费，跳过: msgId={}", msgId);
        return;
    }

    // 执行业务
    orderService.confirmOrder(msg.getOrderId());
}
```

---

## 九、分布式幂等的终极挑战

### 问题：Redis + MySQL 双写一致性

```
场景：幂等检查在 Redis，但最终结果写 MySQL

时序问题：
  T1: Redis SETNX → 成功（通过幂等检查）
  T2: MySQL INSERT → 失败（唯一键冲突）

结果：Redis 说可以执行，MySQL 说不可以

解决：把幂等结果也写 Redis（不只是标记"正在处理"）
```

```java
public Result createOrder(OrderCreateRequest request) {
    String dedupKey = "order:dedup:" + request.getOrderNo();

    // 1. 检查 Redis
    String cachedResult = redisTemplate.opsForValue().get(dedupKey);
    if (cachedResult != null) {
        log.info("幂等返回: orderNo={}", request.getOrderNo());
        return JSON.parseObject(cachedResult, Result.class);
    }

    // 2. 写入 Redis（标记处理中）
    redisTemplate.opsForValue().setIfAbsent(dedupKey + ":lock", "1", Duration.ofSeconds(10));

    try {
        // 3. 执行业务
        Order order = doCreateOrder(request);

        // 4. 结果写入 Redis（下次幂等返回）
        Result result = Result.success(order);
        redisTemplate.opsForValue().set(dedupKey, JSON.toJSONString(result), Duration.ofDays(7));

        return result;
    } catch (DuplicateKeyException e) {
        // MySQL 唯一键冲突，说明已存在
        Order existing = orderMapper.selectByOrderNo(request.getOrderNo());
        Result result = Result.success(existing);
        redisTemplate.opsForValue().set(dedupKey, JSON.toJSONString(result), Duration.ofDays(7));
        return result;
    }
}
```

---

## 十、高频面试题

**Q1: 幂等和防重有什么区别？**
> 幂等是**执行一次和执行多次效果相同**，防重是**防止同一个请求被提交多次**。防重是手段，幂等是目标。防重通过 Token、去重 Key 等实现，最终目的是达到幂等。

**Q2: GET 请求需要幂等吗？**
> 不需要。GET 是只读操作，本身天然幂等，多次读取不会改变资源状态。真正需要幂等的是 POST、PUT、DELETE 等写操作。

**Q3: 幂等 key 过期了怎么办？**
> 取决于业务容忍度。方案一：Redis key 过期时间设为业务允许的最大重试窗口（如 5 分钟）；方案二：结果也存 Redis（不只是状态），key 过期时从 MySQL 查结果回填；方案三：用防重表 + 定期清理任务。

**Q4: 乐观锁和悲观锁哪个更适合幂等？**
> 两者互补，不是替代关系。**乐观锁**适合读多写少、冲突不多的场景（不阻塞，高并发友好）；**悲观锁**（select for update）适合冲突频繁、对一致性要求极高的场景（会阻塞）。幂等更多用乐观锁实现。

**Q5: MQ 消费幂等为什么不直接在 MQ 层做？**
> 大多数 MQ（Kafka、RocketMQ）本身只保证"至少一次"投递（At Least Once），不保证"恰好一次"（Exactly Once）。幂等消费需要在业务层自己实现——通过消息 ID 去重、幂等表、Redis 等手段。

**Q6: 前端防重和后端幂等哪个更重要？**
> **两个都重要，缺一不可**。前端防重提升用户体验（避免用户看到重复提示）；后端幂等是安全的兜底（防止绕过前端直接调用接口、MQ 重投、网络重试）。后端幂等是安全防线，不能省。

---

**参考链接：**
- [RESTful API 幂等性设计](https://www.rfc-editor.org/rfc/rfc9110.html)
- [MQ 消费幂等最佳实践](https://help.aliyun.com/document_detail/159285.html)
