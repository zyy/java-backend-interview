---
layout: default
title: 如何设计一个秒杀系统？⭐⭐⭐
---
# 如何设计一个秒杀系统？⭐⭐⭐

## 🎯 面试题：如何设计一个秒杀系统？

> 秒杀是电商最典型的系统设计问题，核心挑战是：**极高并发、极低库存、防止超卖**。一个设计良好的秒杀系统，需要在架构每一层都做好防护。本题考察的是对高并发系统全链路的理解深度。

---

## 一、秒杀系统的业务特征

```
秒杀场景的特殊性：

1. 时间集中：秒杀开始的那几秒，大量用户同时涌入
2. 库存稀缺：1 万件商品，可能有 100 万人抢购
3. 读多写少（平时）：商品详情页高并发读取
4. 写多读少（秒杀时）：下单接口高并发写入
5. 资源浪费：平时系统资源利用率低，秒杀时系统压力大

核心矛盾：
  100 万人同时抢购 1 万件商品
  → 如果直接打数据库，数据库必挂
  → 必须层层削峰，把流量挡在数据库之前
```

---

## 二、秒杀系统架构全景图

```
用户端
  ↓
CDN（静态资源缓存）
  ↓
Nginx（接入层限流、负载均衡）
  ↓
网关层（风控、黑名单、验证码）
  ↓
秒杀服务集群（Redis 预减库存）
  ↓
MQ 消息队列（异步下单、削峰填谷）
  ↓
订单服务（落库、生成订单）
  ↓
MySQL（最终库存扣减，强一致）
```

---

## 三、前端层防护

### 1. 秒杀按钮防重复点击

```javascript
// 前端倒计时，秒杀开始前按钮不可点击
const startTime = new Date('2024-11-11 00:00:00').getTime();

// 定时器更新按钮状态
const timer = setInterval(() => {
    const now = Date.now();
    if (now < startTime) {
        btn.disabled = true;
        btn.textContent = `距离开抢 ${formatTime(startTime - now)}`;
    } else {
        btn.disabled = false;
        btn.textContent = '立即抢购';
        clearInterval(timer);
    }
}, 100);

// 抢购中：全局锁防止重复提交
let isSubmitting = false;
async function handleSeckill() {
    if (isSubmitting) return;
    isSubmitting = true;
    try {
        const res = await fetch('/api/seckill/do', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skuId, userId })
        });
        const data = await res.json();
        if (data.code === 200) {
            // 跳转到下单页
            location.href = '/order/confirm?orderId=' + data.orderId;
        } else {
            alert(data.msg);
        }
    } finally {
        isSubmitting = false;
    }
}
```

### 2. 验证码防护（防机器人）

```javascript
// 秒杀前做一道简单算术题，大幅减少机器人请求
const captcha = new Captcha({
    length: 4,
    fontSize: 48,
    content: ['1+1=?', '2+3=?', '3*2=?'],
    onSuccess(token) {
        // 验证通过后才放行
        verifyToken(token).then(() => doSeckill());
    }
});
```

---

## 四、CDN + Nginx 层

### 静态资源缓存

```nginx
# Nginx 配置：静态资源走 CDN/浏览器缓存
location ~* \.(js|css|png|jpg|jpeg|gif)$ {
    expires 7d;
    add_header Cache-Control "public, no-cache";
}

# 秒杀商品详情页：静态化处理
location /seckill/item/${itemId} {
    proxy_pass http://backend;
    proxy_cache seckill_page;
    proxy_cache_valid 200 10s;  # 秒杀开始前缓存 10 秒
}
```

### Nginx 限流

```nginx
# 令牌桶限流：限制每秒请求数
limit_req_zone $binary_remote_addr zone=seckill:10m rate=100r/s;

# 针对秒杀接口限流
location /api/seckill/do {
    limit_req zone=seckill burst=200 nodelay;
    proxy_pass http://seckill-backend;
}

# IP 黑名单
deny 10.0.0.0/8;
allow 192.168.0.0/16;
```

---

## 五、服务层：Redis 预减库存

### 核心流程

```
传统流程（直接打数据库）：
  用户请求 → 查询 MySQL 库存 → 扣库存 → 创建订单 → 返回
  问题：100 万并发同时查 MySQL，MySQL 必挂

Redis 预减流程（分层防护）：
  用户请求 → Redis DECR 扣库存（原子操作）→ 库存足够 → 发 MQ 消息
  → 用户下单页（异步）
  → 库存不足 → 直接返回"已售罄"

关键：把数据库的并发写入变成 Redis 的内存操作
  Redis 单机 QPS 10 万+，完全扛得住
```

### Redis Lua 原子扣减

```lua
-- seckill.lua：Lua 脚本保证库存扣减原子性
-- KEYS[1] = 库存 key，如 seckill:stock:{skuId}
-- ARGV[1] = 要扣减的数量（通常为 1）
-- 返回值：>0=扣减成功（剩余库存）；0=库存不足；<0=错误

local stock = redis.call('GET', KEYS[1])
if stock == false then
    return -1  -- 库存 key 不存在
end

stock = tonumber(stock)
local deduct = tonumber(ARGV[1])

if stock < deduct then
    return 0  -- 库存不足
end

stock = stock - deduct
redis.call('SET', KEYS[1], stock)

-- 如果库存低于阈值，发警告
if stock < 100 then
    redis.call('PUBLISH', 'seckill:alert', KEYS[1])
end

return stock  -- 返回剩余库存
```

### Java 代码实现

```java
@Service
@Slf4j
public class SeckillService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 秒杀 Redis Key
    private static final String STOCK_KEY = "seckill:stock:";
    private static final String USER_KEY = "seckill:user:";

    /**
     * 秒杀接口：Redis 预减库存 + MQ 异步下单
     */
    public Result<Long> doSeckill(SeckillRequest request) {
        Long skuId = request.getSkuId();
        Long userId = request.getUserId();

        // 1. 用户维度限流：每人每秒最多请求 1 次
        String userRateKey = "seckill:rate:user:" + userId;
        Long count = stringRedisTemplate.opsForValue().increment(userRateKey);
        if (count != null && count > 1) {
            return Result.error("请求过于频繁，请稍后再试");
        }
        stringRedisTemplate.expire(userRateKey, 1, TimeUnit.SECONDS);

        // 2. 检查用户是否已购买过
        String userBoughtKey = USER_KEY + skuId + ":" + userId;
        if (Boolean.TRUE.equals(stringRedisTemplate.hasKey(userBoughtKey))) {
            return Result.error("您已购买过该秒杀商品");
        }

        // 3. Lua 脚本原子扣减库存
        String stockKey = STOCK_KEY + skuId;
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        script.setScriptText(
            "local stock = redis.call('GET', KEYS[1]) " +
            "if stock == false then return -1 end " +
            "stock = tonumber(stock) " +
            "if stock < 1 then return 0 end " +
            "stock = stock - 1 " +
            "redis.call('SET', KEYS[1], stock) " +
            "return stock"
        );
        script.setResultType(Long.class);

        Long remainStock = stringRedisTemplate.execute(script, List.of(stockKey));

        if (remainStock == null || remainStock < 0) {
            return Result.error("商品不存在");
        }
        if (remainStock == 0) {
            return Result.error("已售罄");
        }

        // 4. 库存扣减成功，发送 MQ 消息异步创建订单
        SeckillMessage message = new SeckillMessage(skuId, userId, remainStock);
        rocketMQTemplate.asyncSend("seckill-order-topic", message, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("秒杀消息发送成功: {}", sendResult);
            }
            @Override
            public void onException(Throwable e) {
                log.error("秒杀消息发送失败，回补库存: skuId={}", skuId, e);
                // 发送失败，回补 Redis 库存
                stringRedisTemplate.opsForValue().increment(stockKey);
            }
        });

        // 5. 记录用户购买标记
        stringRedisTemplate.opsForValue().set(userBoughtKey, "1", 24, TimeUnit.HOURS);

        return Result.success("抢购成功，请稍后刷新订单页面", remainStock);
    }
}
```

---

## 六、MQ 异步下单

### 为什么用 MQ？

```
同步下单的问题：
  用户点击 → 库存扣减 → 订单落库 → 支付 → 返回
  全链路耗时 500ms+
  1 万并发 = 5000 QPS 的数据库写入

MQ 异步下单：
  用户点击 → 库存扣减（10ms）→ 发 MQ 消息 → 返回"抢购成功"（50ms）
  后台 Consumer → 订单落库（异步）
  大幅降低接口响应时间，减少用户等待
```

### 消费者：异步创建订单

```java
@Service
@Slf4j
public class SeckillOrderConsumer {

    @Autowired
    private OrderService orderService;

    @Autowired
    private StockService stockService;

    @RocketMQMessageListener(
        topic = "seckill-order-topic",
        consumerGroup = "seckill-order-consumer-group",
        maxReconsumeTimes = 3  // 最多重试 3 次
    )
    public void handleSeckillOrder(SeckillMessage message, Acknowledgment ack) {
        Long skuId = message.getSkuId();
        Long userId = message.getUserId();

        try {
            // 1. 幂等检查：防止消息重复消费
            String dedupKey = "seckill:order:dedup:" + skuId + ":" + userId;
            Boolean success = redisTemplate.opsForValue()
                .setIfAbsent(dedupKey, "1", Duration.ofHours(1));

            if (!Boolean.TRUE.equals(success)) {
                log.info("订单已存在，跳过: skuId={}, userId={}", skuId, userId);
                ack.acknowledge();
                return;
            }

            // 2. MySQL 乐观锁扣减库存（最终一致性保障）
            boolean stockOk = stockService.deductStockWithVersion(skuId);
            if (!stockOk) {
                log.error("MySQL 库存不足: skuId={}", skuId);
                throw new BizException("库存不足");
            }

            // 3. 创建订单
            Order order = orderService.createSeckillOrder(skuId, userId);

            // 4. 发消息通知用户
            notifyService.sendOrderSuccessNotification(userId, order.getOrderId());

            // 5. 手动 ACK
            ack.acknowledge();
            log.info("秒杀订单创建成功: orderId={}", order.getOrderId());

        } catch (Exception e) {
            log.error("秒杀订单创建失败: skuId={}, userId={}", skuId, userId, e);
            // 不 ACK，消息会进入重试队列
            throw e;
        }
    }
}
```

---

## 七、数据库层：MySQL 乐观锁扣减

```java
@Service
public class StockService {

    @Autowired
    private StockMapper stockMapper;

    /**
     * 乐观锁扣减库存：防止超卖
     * SQL: UPDATE stock SET stock = stock - #{count}, version = version + 1
     *      WHERE sku_id = #{skuId} AND stock >= #{count} AND version = #{version}
     */
    @Transactional(rollbackFor = Exception.class)
    public boolean deductStockWithVersion(Long skuId) {
        // 1. 查询当前库存和版本号
        Stock stock = stockMapper.selectBySkuId(skuId);
        if (stock == null || stock.getStock() <= 0) {
            return false;
        }

        // 2. 乐观锁扣减：where 条件包含 version，只有版本匹配才更新
        int affected = stockMapper.deductWithOptimisticLock(
            skuId, 1, stock.getVersion()
        );

        if (affected == 0) {
            log.warn("乐观锁冲突，库存扣减失败: skuId={}", skuId);
            return false;
        }

        return true;
    }
}
```

```sql
-- StockMapper.xml
<update id="deductWithOptimisticLock">
    UPDATE stock
    SET stock = stock - #{count},
        version = version + 1,
        updated_at = NOW()
    WHERE sku_id = #{skuId}
      AND stock >= #{count}
      AND version = #{version}
</update>
```

---

## 八、完整秒杀链路时序图

```
用户浏览器                              秒杀系统                              Redis                    MQ                 MySQL
   │                                      │                                    │                      │                    │
   │──── 点击抢购 ──────────────────────→│                                    │                      │                    │
   │                                      │──── Redis Lua 扣库存 ─────────────→│                      │                    │
   │                                      │←─── 剩余库存 ────────────────────│                      │                    │
   │                                      │   (库存 > 0)                       │                      │                    │
   │                                      │                                    │                      │                    │
   │                                      │──── 发送秒杀消息 ──────────────────────────────────────→│                    │
   │                                      │←─── 发送成功 ─────────────────────────────────────────│                    │
   │                                      │                                    │                      │                    │
   │←─── 抢购成功，请去下单 ────────────│                                    │                      │                    │
   │                                      │                                    │   Consumer ─────────→│                    │
   │                                      │                                    │   幂等检查 ─────────────────────────────→│
   │                                      │                                    │   乐观锁扣库存 ──────────────────────────→│
   │                                      │                                    │   创建订单 ──────────────────────────────────→│
   │                                      │                                    │                      │                    │
   │──── 刷新订单页 ─────────────────────→│                                    │                      │                    │
   │←─── 订单详情 ──────────────────────│                                    │                      │                    │
```

---

## 九、常见问题与应对

### 超卖问题

```lua
-- 错误写法：先查后减，非原子
local stock = redis.call('GET', 'stock')
if stock > 0 then
    redis.call('DECR', 'stock')  -- 并发时可能 stock 已经变成 0
end

-- 正确写法：Lua 脚本一步完成
if tonumber(stock) >= 1 then
    redis.call('DECR', 'stock')
    return 1
else
    return 0
end
```

### 热点数据问题

```java
// 秒杀商品详情页：多级缓存
public ItemVO getItemDetail(Long skuId) {
    String cacheKey = "item:detail:" + skuId;

    // L1: 本地缓存（Caffeine），扛热点读
    ItemVO cached = localCache.getIfPresent(cacheKey);
    if (cached != null) return cached;

    // L2: Redis 缓存
    String redisValue = redisTemplate.opsForValue().get(cacheKey);
    if (redisValue != null) {
        ItemVO vo = JSON.parseObject(redisValue, ItemVO.class);
        localCache.put(cacheKey, vo);
        return vo;
    }

    // L3: MySQL
    ItemVO vo = itemMapper.selectBySkuId(skuId);
    redisTemplate.opsForValue().set(cacheKey, JSON.toJSONString(vo), 1, TimeUnit.HOURS);
    localCache.put(cacheKey, vo);
    return vo;
}
```

### 库存回滚

```java
// 订单超时未支付，自动回补库存
@Scheduled(cron = "0/10 * * * * ?")
public void rollbackExpiredOrders() {
    List<Order> expiredOrders = orderMapper.selectExpiredUnpaidOrders();

    for (Order order : expiredOrders) {
        try {
            // 1. 取消订单
            orderMapper.updateStatus(order.getOrderId(), OrderStatus.CANCELLED);

            // 2. 回补 Redis 库存
            String stockKey = "seckill:stock:" + order.getSkuId();
            stringRedisTemplate.opsForValue().increment(stockKey);

            // 3. 回补 MySQL 库存
            stockMapper.incrementStock(order.getSkuId(), 1);

            log.info("订单超时取消，库存回补: orderId={}, skuId={}",
                order.getOrderId(), order.getSkuId());
        } catch (Exception e) {
            log.error("库存回补失败: orderId={}", order.getOrderId(), e);
        }
    }
}
```

---

## 十、高频面试题

**Q1: 秒杀系统的核心难点是什么？**
> 三个核心难点：① **高并发写**：百万 QPS 同时打数据库，数据库扛不住，需要 Redis 预减库存把写请求拦截在数据库之前；② **超卖**：多个请求同时读到库存为 1，都认为自己能买，需要 Lua 脚本或乐观锁保证原子性；③ **资源浪费**：平时流量低、秒杀时流量爆炸，需要弹性扩缩容配合。

**Q2: Redis 预减库存的具体流程是什么？**
> 流程：① 用户发起秒杀请求；② Redis 执行 Lua 脚本原子扣减库存，返回剩余数量；③ 库存充足时，发送 MQ 消息异步创建订单，立即返回用户"抢购成功"；④ MQ 消费者异步消费，创建真实订单并落库；⑤ 库存不足时直接返回"已售罄"。Redis 是内存操作，单机 QPS 可达 10 万+，完全扛得住秒杀流量。

**Q3: 如何防止超卖？**
> 两层防超卖：① **Redis 层**：Lua 脚本 `if stock >= 1 then stock = stock - 1 end` 原子扣减，任何并发情况下都不会超卖；② **MySQL 层**：乐观锁 `UPDATE stock SET stock = stock - 1 WHERE sku_id = ? AND stock >= 1`，即使 Redis 层被绕过，MySQL 也能兜底拦截超卖请求。

**Q4: 秒杀系统如何做限流？**
> 分四层限流：① **前端**：验证码 + 按钮防抖 + 请求间隔限制；② **Nginx**：令牌桶限流，针对 IP 和接口限流；③ **网关层**：用户维度限流（每人每秒最多请求 1 次），黑名单过滤；④ **服务层**：Redis 计数器限流，热点商品维度单独限流。多层叠加，层层过滤。

**Q5: MQ 消息丢失了怎么办？**
> RocketMQ 的事务消息可以保证：① 发送半消息（对消费者不可见）；② 执行本地事务（创建订单）；③ 根据事务结果提交或回滚半消息。即使 RocketMQ 宕机，半消息也不会丢失（持久化在 Broker）。消费者端也要用手动 ACK，在业务处理完成后才提交 offset。

**Q6: 如何保证秒杀活动的公平性？**
> 公平性的核心是「先到先得」：① 前端加验证码防机器人；② 严格按请求到达顺序处理（Redis DECR 保证）；③ 库存为 0 后立刻返回售罄，不再接受请求；④ 同一用户限购一件（Redis SETNX 标记用户购买记录）。不能保证绝对公平，但能保证「早到早得」。
