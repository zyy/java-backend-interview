# Redis 持久化与过期策略 ⭐⭐⭐

## 面试题：Redis 的持久化方式有哪些？过期策略是什么？

### 核心回答

Redis 提供两种持久化方式：**RDB**（数据快照）和 **AOF**（命令日志），以及 **过期策略**（惰性删除+定期删除）和 **内存淘汰策略**。

### 一、RDB 持久化

#### 原理

RDB（Redis Database）通过创建数据快照的方式，将内存中的所有数据写入磁盘。

```
RDB 文件生成过程：
1. Redis fork 一个子进程
2. 子进程遍历内存，生成 RDB 文件
3. 替换旧的 RDB 文件
```

#### 触发方式

```bash
# 手动触发
SAVE  # 阻塞 Redis，直到 RDB 文件生成完成
BGSAVE  # 后台异步生成 RDB 文件

# 自动触发（配置在 redis.conf）
save 900 1      # 900 秒内至少 1 个 key 变化
save 300 10     # 300 秒内至少 10 个 key 变化
save 60 10000   # 60 秒内至少 10000 个 key 变化
```

#### 优点

1. **恢复速度快**：RDB 是紧凑的二进制文件，恢复大量数据时比 AOF 快
2. **性能影响小**：fork 的子进程完成持久化，不影响主进程
3. **适合备份**：可以定时备份 RDB 文件

#### 缺点

1. **可能丢失数据**：最后一次快照之后的数据会丢失
2. **fork 开销**：数据量大时，fork 可能阻塞

### 二、AOF 持久化

#### 原理

AOF（Append Only File）通过记录每个写命令来保存数据。

```
AOF 工作流程：
1. 命令执行 → 结果写入 aof_buf
2. 触发刷盘 → aof_buf 写入 AOF 文件
3. 重写 → 压缩 AOF 文件
```

#### 配置

```bash
# 开启 AOF
appendonly yes

# 刷盘策略
appendfsync always     # 每次写命令都刷盘（慢，但最安全）
appendfsync everysec   # 每秒刷盘一次（默认，推荐）
appendfsync no         # 由操作系统决定何时刷盘（快，但可能丢数据）
```

#### AOF 重写

```bash
# 手动触发
BGREWRITEAOF

# 自动触发
auto-aof-rewrite-percentage 100  # 文件大小达到上次重写时的 100% 时触发
auto-aof-rewrite-min-size 64mb  # 文件至少达到 64MB 时才触发
```

**重写原理**：
```bash
# 重写不是读取旧 AOF 文件
# 而是直接读取当前内存数据，生成写命令

# 例如：
SET name "张三"
SET name "李四"
SET name "王五"
# 重写后只保留：SET name "王五"
```

### 三、RDB vs AOF

| 特性 | RDB | AOF |
|------|------|-----|
| **数据安全性** | 可能有丢失 | 可配置（每秒/每次） |
| **恢复速度** | 快 | 慢（需重放命令） |
| **文件大小** | 小（紧凑） | 大（包含所有命令） |
| **CPU 开销** | fork 开销 | 需要重写 |
| **适用场景** | 备份、恢复 | 数据安全要求高 |

### 四、Redis 过期策略

#### 设置过期时间

```bash
# 设置过期时间
EXPIRE key 60        # 60 秒后过期
EXPIREAT key 1234567890  # 设置过期时间戳
PEXPIRE key 60000    # 毫秒

# 查看剩余时间
TTL key
PTTL key

# 移除过期时间（永不过期）
PERSIST key
```

#### 三种过期策略

```java
// 1. 定时删除
// 为每个 key 创建定时器，过期立即删除
// 优点：内存友好，及时释放
// 缺点：CPU 开销大，大量定时器影响性能

// 2. 惰性删除
// 访问 key 时才判断是否过期，过期则删除
// 优点：CPU 友好
// 缺点：内存不友好，过期 key 可能堆积

// 3. 定期删除
// 每隔一段时间，扫描一定数量的 key，删除过期的
// 折中方案：平衡 CPU 和内存
```

#### Redis 采用的策略

Redis 采用 **惰性删除 + 定期删除** 的组合策略：

```java
// 惰性删除：在 get 时检查
def get(key):
    if key in db:
        if key.is_expired():
            db.delete(key)
            return None
        return key.value
    return None

// 定期删除：每 100ms 扫描
def active_expire_cycle():
    # 随机取 20 个带过期时间的 key
    keys = random_select(db.expires, 20)
    
    for key in keys:
        if key.is_expired():
            db.delete(key)
    
    # 如果过期 key 超过 25%，继续扫描
    if expired_count > 20 * 0.25:
        active_expire_cycle()
```

### 五、内存淘汰策略

当 Redis 内存达到上限时，需要淘汰一些 key：

```bash
# 配置最大内存
maxmemory 2gb

# 淘汰策略
maxmemory-policy allkeys-lru
```

#### 八种淘汰策略

| 策略 | 说明 |
|------|------|
| **noeviction** | 不淘汰，返回错误（默认） |
| **volatile-lru** | 从设置过期时间的 key 中，淘汰最近最少使用的 |
| **allkeys-lru** | 从所有 key 中，淘汰最近最少使用的 |
| **volatile-lfu** | 从设置过期时间的 key 中，淘汰使用频率最低的 |
| **allkeys-lfu** | 从所有 key 中，淘汰使用频率最低的 |
| **volatile-random** | 从设置过期时间的 key 中，随机淘汰 |
| **allkeys-random** | 从所有 key 中，随机淘汰 |
| **volatile-ttl** | 从设置过期时间的 key 中，淘汰 TTL 最小的 |

#### LRU vs LFU

```bash
# LRU：Least Recently Used，最近最少使用
# 淘汰最长时间没被访问的 key

# LFU：Least Frequently Used，最不经常使用
# 淘汰访问频率最低的 key
```

### 六、高频面试题

**Q1: Redis 持久化方式如何选择？**

```
推荐方案：

1. 同时开启 RDB 和 AOF
   - RDB 用于备份和快速恢复
   - AOF 用于数据安全

2. 数据恢复优先级
   - AOF 优先（数据更完整）
   - 如果 AOF 文件损坏，用 redis-check-aof 修复

3. 性能考虑
   - RDB fork 开销大，适合低峰期
   - AOF 每秒刷盘，对性能有一定影响
```

**Q2: AOF 和 RDB 可以同时启用吗？**

```
可以！Redis 启动时会优先加载 AOF（数据更完整）

AOF + RDB 组合：
- 数据恢复：优先使用 AOF
- 备份：RDB 文件更紧凑，适合备份
- 性能：主进程只负责写，持久化由子进程完成
```

**Q3: 过期 key 对持久化的影响？**

```bash
# RDB：生成快照时，已过期的 key 不会被写入
# 但从 RDB 恢复时，会正常加载

# AOF：
# 1. key 过期后，AOF 记录 DEL 命令
# 2. 重写时，已过期的 key 不会被写入新的 AOF 文件
```

**Q4: 如何实现 Redis 缓存和数据库双写一致？**

```java
// 方案1：Cache Aside（旁路缓存）
// 读：缓存优先，没有就读数据库，再写缓存
public User getUser(Long id) {
    User user = redis.get("user:" + id);
    if (user == null) {
        user = db.findById(id);
        if (user != null) {
            redis.set("user:" + id, user, 1小时);
        }
    }
    return user;
}

// 写：先写数据库，再删缓存
public void updateUser(User user) {
    db.update(user);
    redis.del("user:" + user.getId());  // 删除而非更新
}

// 方案2：延时双删
// 1. 先删缓存
// 2. 写数据库
// 3. 延时一段时间，再删缓存（处理并发问题）
```

### 七、最佳实践

```bash
# 生产环境配置示例
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

maxmemory 2gb
maxmemory-policy allkeys-lru

# RDB 自动保存
save 900 1
save 300 10
save 60 10000
```

```java
// Java 客户端使用建议
// 1. 给缓存设置合理的 TTL
redisTemplate.opsForValue().set("key", value, 1, TimeUnit.HOURS);

// 2. 热点数据预热
// 系统启动时，将热点数据加载到缓存

// 3. 监控内存使用
Jedis jedis = new Jedis("localhost", 6379);
String info = jedis.info("memory");
System.out.println(info);
```

---

**参考链接：**
- [Redis持久化详解-牛客网](https://www.nowcoder.com/discuss/593133629157494784)
- [Redis过期策略-腾讯云](https://cloud.tencent.com/developer/article/2332581)
