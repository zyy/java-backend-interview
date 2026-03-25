# Redis 缓存穿透、击穿、雪崩 ⭐⭐⭐

## 面试题：什么是缓存穿透、击穿、雪崩？如何解决？

### 核心回答

缓存穿透、击穿、雪崩是 Redis 缓存使用中的三大问题，分别由不同的原因导致，需要针对性的解决方案。

### 一、缓存穿透

#### 问题描述

**缓存穿透**：查询一个不存在的数据，缓存和数据库都没有命中，导致每次请求都打到数据库。

```
请求流程：
1. 客户端请求 key="不存在的数据"
2. 缓存中没有
3. 数据库中也没有
4. 返回空结果
5. 缓存中也不存储空结果
6. 下次请求继续穿透
```

**危害**：
- 大量无效请求打到数据库
- 数据库压力剧增
- 可能导致数据库宕机
- 常见于恶意攻击

#### 解决方案

##### 方案1：缓存空对象

```java
public String getData(String key) {
    // 1. 查询缓存
    String value = redis.get(key);
    
    if (value == null) {
        // 2. 查询数据库
        String dbValue = db.query(key);
        
        if (dbValue == null) {
            // 3. 缓存空对象，防止穿透
            redis.set(key, "", 60秒);
            return null;
        } else {
            redis.set(key, dbValue, 1小时);
            return dbValue;
        }
    }
    
    return value;
}
```

**优点**：实现简单
**缺点**：
- 存储无效数据，消耗内存
- 短期数据不一致

##### 方案2：布隆过滤器（推荐）

```java
// 布隆过滤器原理：
// 1. 初始化一个大数组（全为 0）
// 2. key 经过 3 次 hash，映射到数组下标，置为 1
// 3. 查询时，同样 hash 检查是否为 1

// 布隆过滤器特点：
// - 说存在，可能不存在（误判）
// - 说不存在，一定不存在
// - 空间效率高
```

```java
// 使用 Redisson 实现布隆过滤器
Config config = new Config();
config.useSingleServer().setAddress("redis://127.0.0.1:6379");

RedissonClient redisson = Redisson.create(config);
RBloomFilter<String> bloomFilter = redisson.getBloomFilter("user bloom");

// 初始化（预计插入 100000 个，误判率 0.03）
bloomFilter.tryInit(100000, 0.03);

// 添加元素
bloomFilter.add("user:1");
bloomFilter.add("user:2");

// 判断元素是否存在
boolean exists = bloomFilter.contains("user:1");  // true/false
```

```java
public User getUser(Long userId) {
    String key = "user:" + userId;
    
    // 1. 布隆过滤器检查
    if (!bloomFilter.contains(key)) {
        return null;  // 一定不存在
    }
    
    // 2. 查询缓存
    User user = redis.get(key);
    if (user != null) {
        return user;
    }
    
    // 3. 查询数据库
    user = db.findById(userId);
    if (user != null) {
        redis.set(key, user);
    }
    
    return user;
}
```

### 二、缓存击穿

#### 问题描述

**缓存击穿**：某个热点 key 在缓存中过期的瞬间，大量并发请求直接打到数据库。

```
时间轴：
T1: 热点 key 缓存存在
T2: 热点 key 过期
T3: 并发请求发现缓存过期
T4: 所有请求同时查询数据库  ← 数据库压力峰值
T5: 某个请求回填缓存
T6: 其他请求从缓存获取数据
```

**特点**：
- 针对热点 key
- 高并发 + key 过期
- 数据库瞬时压力过大

#### 解决方案

##### 方案1：互斥锁（分布式锁）

```java
public String getDataWithLock(String key) {
    // 1. 先查缓存
    String value = redis.get(key);
    if (value != null) {
        return value;
    }
    
    // 2. 获取锁
    String lockKey = "lock:" + key;
    String lockValue = UUID.randomUUID().toString();
    
    // SET key value NX EX seconds（原子操作）
    boolean locked = redis.set(lockKey, lockValue, 10, TimeUnit.SECONDS);
    
    if (locked) {
        try {
            // 3. 双重检查（可能其他线程已回填）
            value = redis.get(key);
            if (value != null) {
                return value;
            }
            
            // 4. 查询数据库
            value = db.query(key);
            
            // 5. 回填缓存
            redis.set(key, value, 1小时);
            
            return value;
        } finally {
            // 6. 释放锁
            redis.del(lockKey);
        }
    } else {
        // 7. 未获取到锁，短暂等待后重试
        Thread.sleep(50);
        return getDataWithLock(key);
    }
}
```

##### 方案2：热点数据永不过期

```java
// 使用逻辑过期，不设置实际过期时间

public class CacheWithLogicExpire {
    
    static class Data {
        private String value;
        private long expireTime;  // 逻辑过期时间
        
        public boolean isExpired() {
            return System.currentTimeMillis() > expireTime;
        }
    }
    
    public String getData(String key) {
        Data data = redis.get(key);
        
        if (data == null) {
            return null;
        }
        
        // 未过期，直接返回
        if (!data.isExpired()) {
            return data.getValue();
        }
        
        // 已过期，异步更新（使用其他线程，不阻塞）
        CompletableFuture.runAsync(() -> {
            String newValue = db.query(key);
            CacheWithLogicExpire.Data newData = new Data();
            newData.setValue(newValue);
            newData.setExpireTime(System.currentTimeMillis() + 30分钟);
            redis.set(key, newData);
        });
        
        // 返回旧数据（可能已过期，但基本可用）
        return data.getValue();
    }
}
```

##### 方案3：Redisson 分布式锁（推荐）

```java
@Autowired
private RedissonClient redisson;

public String getData(String key) {
    // 1. 先查缓存
    String value = redis.get(key);
    if (value != null) {
        return value;
    }
    
    // 2. 获取分布式锁
    RLock lock = redisson.getLock("lock:" + key);
    lock.lock(10, TimeUnit.SECONDS);
    
    try {
        // 3. 双重检查
        value = redis.get(key);
        if (value != null) {
            return value;
        }
        
        // 4. 查询数据库
        value = db.query(key);
        redis.set(key, value, 30, TimeUnit.MINUTES);
        
        return value;
    } finally {
        lock.unlock();
    }
}
```

### 三、缓存雪崩

#### 问题描述

**缓存雪崩**：大量缓存同时过期 或 Redis 故障，导致大量请求直接打到数据库。

```
场景1：大量缓存同时过期
T1: 大量 key 集中过期
T2: 所有请求打到数据库
T3: 数据库压力剧增

场景2：Redis 故障
T1: Redis 服务不可用
T2: 所有请求打到数据库
T3: 数据库宕机
```

#### 解决方案

##### 方案1：过期时间随机化

```java
// 给缓存设置随机的过期时间，避免集中过期

public void setCache(String key, String value) {
    // 基础过期时间 1 小时
    int baseExpire = 3600;
    // 随机增加 0-30 分钟
    int randomExpire = new Random().nextInt(1800);
    
    redis.set(key, value, baseExpire + randomExpire);
}
```

##### 方案2：热点数据预加载

```java
// 系统启动时，预加载热点数据
@PostConstruct
public void init() {
    // 查询热点数据
    List<HotData> hotList = hotDataService.getHotList();
    
    for (HotData hot : hotList) {
        redis.set("hot:" + hot.getId(), hot, 24小时);
    }
}
```

##### 方案3：Redis 高可用架构

```bash
# Redis Cluster 集群
# Redis Sentinel 主从哨兵

# 主从复制 + 自动故障转移
# 某个节点故障，哨兵自动选举新主节点
```

##### 方案4：服务降级和限流

```java
// 使用 Hystrix/Sentinel 实现限流和降级

@HystrixCommand(fallbackMethod = "getDataFallback")
public String getData(String key) {
    return cacheService.getData(key);
}

// 降级方法：数据库直接查询
public String getDataFallback(String key) {
    return db.query(key);
}
```

### 四、三种问题对比

| 问题 | 原因 | 特点 | 解决方案 |
|------|------|------|---------|
| **穿透** | 查询不存在的数据 | 数据本身不存在 | 布隆过滤器、缓存空对象 |
| **击穿** | 热点 key 过期瞬间 | 高并发 + 单 key | 互斥锁、逻辑过期 |
| **雪崩** | 大量 key 同时过期/Redis 故障 | 批量失效/服务不可用 | 随机过期、高可用、降级限流 |

### 五、完整解决方案示例

```java
@Service
public class CacheService {
    
    @Autowired
    private RedissonClient redisson;
    
    @Autowired
    private RBloomFilter<String> bloomFilter;
    
    public String getData(String key) {
        // 1. 布隆过滤器检查（防止穿透）
        if (!bloomFilter.contains(key)) {
            return null;
        }
        
        // 2. 查询缓存
        String value = redis.get(key);
        if (value != null) {
            return value;
        }
        
        // 3. 获取分布式锁（防止击穿）
        RLock lock = redisson.getLock("lock:" + key);
        lock.lock(10, TimeUnit.SECONDS);
        
        try {
            // 4. 双重检查
            value = redis.get(key);
            if (value != null) {
                return value;
            }
            
            // 5. 查询数据库
            String dbValue = db.query(key);
            
            if (dbValue != null) {
                // 6. 缓存结果（随机过期时间，防止雪崩）
                int expire = 3600 + new Random().nextInt(1800);
                redis.setex(key, expire, dbValue);
                
                // 7. 加入布隆过滤器
                bloomFilter.add(key);
            } else {
                // 8. 缓存空值（防止穿透，但过期时间短）
                redis.setex(key, 60, "");
            }
            
            return dbValue;
        } finally {
            lock.unlock();
        }
    }
}
```

### 六、高频面试题

**Q1: 布隆过滤器的误判率如何计算？**

```
布隆过滤器的误判率公式：

P = (1 - e^(-kn/m))^k

其中：
- m：bit 数组长度
- k：hash 函数个数
- n：插入元素个数

最优 hash 函数个数：k = (m/n) * ln2

空间节省：比存储原始数据小得多
```

**Q2: 如何选择解决方案？**

```
缓存穿透：数据确定不存在
- 布隆过滤器（推荐）：内存占用少，效率高
- 缓存空对象：简单，但占内存

缓存击穿：热点 key 高并发
- 分布式锁（推荐）：保证只有一个请求查库
- 逻辑过期：性能好，但返回可能过期数据

缓存雪崩：批量失效/故障
- 随机过期：简单有效
- 高可用架构：从根本上解决问题
```

---

**参考链接：**
- [Redis缓存穿透、击穿、雪崩-阿里云](https://developer.aliyun.com/article/1282146)
- [Redis经典面试题-腾讯云](https://cloud.tencent.com/developer/article/2388083)
