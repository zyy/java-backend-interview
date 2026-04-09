---
layout: default
title: Redis 主从复制原理与哨兵模式
---
# Redis 主从复制原理与哨兵模式

## 一、主从复制的作用

```
主从复制架构：

        写操作
           ↓
    ┌──────────┐
    │  Master   │  ← 接收所有写请求
    └──┬───────┬─┘
       │       │  同步
   ┌───↓──┐ ┌──↓───┐
   │Slave1 │ │Slave2│  ← 处理读请求
   └───────┘ └──────┘

作用：
✅ 读写分离：读操作分散到多个从库
✅ 数据备份：每个从库都是完整数据副本
✅ 故障转移：从库可升级为主库
❌ 单点写入：只有主库能写入
```

---

## 二、同步原理

### 全量同步（PSYNC）

```
触发条件：Slave 首次连接 / Slave 断开太久（repl_backlog 缓冲区不够）

全量同步流程：

  Slave → PSYNC <runid> <offset>   ← 发送复制命令
  Master → +FULLRESYNC <runid> <offset>  ← 返回完整重同步
  
  Master → RDB 文件（bgsave 生成）     ← 主库生成 RDB 快照
  Master → 缓冲区中的增量命令           ← RDB 生成期间的写命令
  
  Slave → 清空本地数据
  Slave → 加载 RDB 文件                  ← 恢复数据
  Slave → 执行增量命令                   ← 追平复制进度
```

### 增量同步（PSYNC v2）

```
触发条件：Slave 短时断开，offset 仍在 repl_backlog 缓冲区中

Master 端维护一个固定长度的环形缓冲区（repl_backlog）：
┌──────────────────────────────────────────────────────┐
│ runid=abc │ runid=abc │ runid=abc │ ... │ ← 循环使用 │
└──────────────────────────────────────────────────────┘
                                    ↑ offset 指针

Slave 记录自己消费到的 offset：
  Slave → PSYNC <master_runid> <slave_offset>
  如果 master_runid 匹配且 slave_offset 在缓冲区范围内
  → Master 只发送 slave_offset 之后的增量命令
  
否则 → 触发全量同步
```

### PSYNC 命令详解

```bash
# 首次复制：Slave 不知道 master runid，发 -1
PSYNC ? -1

# 增量复制：Slave 知道 master runid 和自己的 offset
PSYNC <master_runid> <offset>

# Master 响应：
# +FULLRESYNC <runid> <offset>  → 全量同步
# +CONTINUE                       → 增量同步
# +ERR                             → 不支持 PSYNC，退化为 SYNC（全量）
```

### 配置参数

```bash
# Master 配置
repl-diskless-sync no           # 是否使用无磁盘复制（直接通过 socket 传 RDB）
repl-diskless-sync-delay 5       # 无磁盘复制延迟（等待多个 slave 一起同步）

# 复制缓冲区（repl_backlog）
repl-backlog-size 10mb           # 缓冲区大小，太小会导致增量同步失败
repl-backlog-ttl 3600           # 缓冲区空闲 N 秒后释放

# 从库配置
replicaof 127.0.0.1 6379        # 指向主库
replica-serve-stale-data yes    # 主库宕机时，从库是否返回旧数据
replica-read-only yes           # 从库只读
repl-ping-replica-period 10     # 从库向主库发送 ping 的间隔（秒）
```

---

## 三、主从复制的常见问题

### 数据延迟

```
问题：主库写 → 异步复制到从库 → 从库读取
                    ↓
            延迟：可能读到旧数据

原因：
1. 主库并发写入，从库串行重放（能力不对等）
2. 从库硬件差（CPU/磁盘）
3. 大事务（主库快，从库慢）

监控延迟：
  replica lagging seconds: 5   ← 从库延迟 5 秒

解决方案：
1. 关键读走主库（下单后立即查订单）
2. 监控延迟 > 阈值时降级读主库
3. 从库并行重放（replica-parallel-workers）
```

### 复制风暴

```
问题：一个 Master 有很多 Slave，同时做全量同步

Master
  │
  ├── Slave1 ──→ 全量同步（RDB bgsave）── CPU/IO 飙升
  ├── Slave2 ──→ 全量同步（RDB bgsave）── 再次 bgsave
  ├── Slave3 ──→ 全量同步（RDB bgsave）── ...
  └── Slave4 ──→ ...

解决：
1. 从库分批同步（修改 replicaof 的时间）
2. 使用 树莓派模式（中间层减少主库压力）
3. repl-diskless-sync yes（无磁盘，网络直接传 RDB）
```

---

## 四、哨兵（Sentinel）模式

### 为什么需要 Sentinel？

```
主从复制的问题：
  Master 宕机 → 需要人工介入 → 手动选从库 → 修改从库配置 → 恢复写入
  
Sentinel 的职责：
  1. 监控：检测主库是否存活
  2. 通知：主库下线时通知应用
  3. 自动故障转移：自动选新主库，通知其他从库切换
```

### Sentinel 工作流程

```
第一阶段：主观下线（SDOWN）
  Sentinel 每秒向主库发送 PING
  如果超过 down-after-milliseconds 没响应
  → Sentinel 认为该库主观下线

第二阶段：客观下线（ODOWN）
  超过 quorum 个 Sentinel 都认为主库主观下线
  → 该主库进入客观下线状态

第三阶段：选举领头 Sentinel
  所有 Sentinel 参与 Raft 算法投票
  得票最多的成为领头 Sentinel
  负责执行故障转移

第四阶段：故障转移
  1. 从从库中选出一个新的主库
  2. 其他从库改为向新主库复制
  3. 旧主库重新上线后变为从库
```

### 领头 Sentinel 选举算法

```
Raft 简化版选举：

1. 每个 Sentinel 有一个 runid
2. 每个 Sentinel 向其他 Sentinel 发请求：
   SENTINEL is-master-down-by-addr
3. 得票最多的 Sentinel 当选领头
4. 领头 Sentinel 执行故障转移

投票规则：
  - 每个 Sentinel 只能投一票
  - 先到先得
  - 得票 > 总数/2 才算当选
```

### 新主库选择标准

```
选择优先级从高到低：

1. 优先级（replica-priority）最高的
   replica-priority 100  ← 默认值，越高越优先

2. offset 最接近主库的（数据最新）
   SELECT Replication offset 最接近

3. runid 最小的（字典序）
   纯理论上的 tie-breaker
```

### Sentinel 配置

```bash
# sentinel.conf
sentinel monitor mymaster 127.0.0.1 6379 2
  # 监控 mymaster，主库地址 127.0.0.1:6379
  # quorum=2：至少 2 个 Sentinel 同意才客观下线

sentinel down-after-milliseconds mymaster 30000
  # 30 秒没响应认为主观下线

sentinel parallel-syncs mymaster 1
  # 故障转移时，同时向新主库同步的从库数量
  # 设为 1：逐个同步，避免新主库压力过大

sentinel failover-timeout mymaster 180000
  # 故障转移超时时间：3 分钟
```

### Java 客户端集成

```java
// Jedis SentinelPool
JedisPoolConfig poolConfig = new JedisPoolConfig();
poolConfig.setMaxTotal(200);
poolConfig.setMaxIdle(50);

Set<String> sentinels = new HashSet<>();
sentinels.add("192.168.1.101:26379");
sentinels.add("192.168.1.102:26379");
sentinels.add("192.168.1.103:26379");

JedisSentinelPool pool = new JedisSentinelPool(
    "mymaster",           // 监控的主库名称
    sentinels,
    poolConfig,
    3000,                 // connectionTimeout
    3000                  // soTimeout
);

// 使用方式和普通 JedisPool 完全一样
// Sentinel 会自动处理主库切换
try (Jedis jedis = pool.getResource()) {
    jedis.set("key", "value");
}
```

---

## 五、面试高频题

**Q1: Redis 主从复制的原理是什么？**
> 主从复制基于 binlog 实现：Master 执行写操作后写入 binlog；从库 IO Thread 连接主库，拉取 binlog 并写入 relay log（中继日志）；然后从库 SQL Thread 读取 relay log，在本地重放 SQL。首次连接做全量同步（PSYNC ? -1），之后做增量同步（PSYNC <runid> <offset>）。增量同步依赖 repl_backlog 环形缓冲区，offset 在缓冲区范围内就直接发增量命令。

**Q2: 全量同步和增量同步的区别是什么？**
> 全量同步在从库首次连接或 offset 超出缓冲区时触发：Master 执行 bgsave 生成 RDB 文件，通过网络发送给从库，从库清空本地数据后加载 RDB 并执行缓冲区中的增量命令。增量同步在从库短时断开且 offset 仍在缓冲区时触发：Master 只发送 offset 之后的增量命令。区分点在于从库记录的 offset 是否在 repl_backlog 缓冲区内。

**Q3: Sentinel 如何实现自动故障转移？**
> Sentinel 通过多轮投票实现：首先每个 Sentinel 每秒向主库发送 PING，超过 down-after-milliseconds 没响应则主观下线；然后超过 quorum 个 Sentinel 都认为主观下线则进入客观下线；接着所有 Sentinel 用 Raft 简化版算法投票选出领头 Sentinel；最后由领头 Sentinel 从从库中选数据最新的作为新主库，其他从库改为向新主库复制，旧主库重新上线后变为从库。

**Q4: 主从延迟怎么监控和解决？**
> 监控：`INFO replication` 中的 `seconds_behind_master` 显示延迟秒数，`replica_lag_seconds` 字段。解决：① 关键读走主库（下单后立即查订单）；② 延迟超过阈值时降级读主库；③ 从库开启多线程并行重放（replica-parallel-workers）；④ 大事务拆小，减少单次操作的延迟。

**Q5: 为什么主从复制不能保证强一致性？**
> 因为复制是异步的：主库写入后立即返回客户端，不等待从库确认。如果主库宕机，从库还没同步的写操作会丢失。这就是 CAP 理论中的 AP 模型（可用性 + 分区容忍，但牺牲了强一致性）。如果需要强一致，需要用同步复制（WAIT 命令）或 Raft 协议的 Redis Cluster（6.2+ 支持）。
