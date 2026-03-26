---
layout: default
title: Redis 集群方案详解
---
# Redis 集群方案详解：从主从复制到 Cluster ⭐⭐⭐

> Redis 分布式集群是大规模应用的必选方案。本文深入讲解主从复制、哨兵模式、Cluster 集群的原理、工作机制和面试高频题。

## 🎯 面试重点

- Redis 主从复制的全量同步和增量同步机制
- Redis Sentinel 哨兵的故障检测和自动切换原理
- Redis Cluster 的槽分片、节点通信、数据路由
- 集群模式下的高可用保证和客户端连接
- 主从切换期间的读写问题
- Java 客户端（Jedis/Lettuce）集群连接

---

## 第一部分：Redis 主从复制

### 一、主从复制的基本概念

**主从复制**是 Redis 实现高可用的基础。一个 Redis 实例（主节点）可以有多个副本（从节点），从节点会复制主节点的所有数据。

```
主从架构：
┌─────────────┐
│   Master    │  (主节点)
│  6379       │
└──────┬──────┘
       │ 复制数据
       │
   ┌───┴────┬──────────┐
   │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│Slave1│  │Slave2│  │Slave3│  (从节点)
│6380  │  │6381  │  │6382  │
└──────┘  └──────┘  └──────┘
```

**主从复制的作用：**
1. **数据备份**：从节点保存主节点的完整副本
2. **读写分离**：主节点处理写操作，从节点处理读操作
3. **高可用基础**：为故障转移提供基础

### 二、主从复制的工作原理

#### 2.1 复制过程的三个阶段

```
┌─────────────────────────────────────────────────────────┐
│ 从节点启动或重连主节点                                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  阶段1：建立连接         │
        │  从节点发送 PSYNC 命令   │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │  阶段2：全量同步（Full Resync）         │
        │  主节点生成 RDB 快照，发送给从节点      │
        │  从节点加载 RDB，恢复数据                │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │  阶段3：增量同步（Partial Resync）      │
        │  主节点将新命令发送给从节点              │
        │  从节点执行命令，保持数据一致            │
        └────────────────────────────────────────┘
```

#### 2.2 全量同步（Full Resync）

**触发条件：**
- 从节点首次连接主节点
- 从节点的 replication ID 与主节点不匹配
- 从节点的偏移量超出主节点的缓冲区范围

**全量同步流程：**

```java
/**
 * 全量同步流程
 * 
 * 1. 从节点发送 PSYNC ? -1
 *    表示：我是新从节点，请进行全量同步
 * 
 * 2. 主节点响应 +FULLRESYNC <replication_id> <offset>
 *    replication_id：主节点的唯一标识
 *    offset：主节点当前的复制偏移量
 * 
 * 3. 主节点执行 BGSAVE，生成 RDB 快照
 *    同时将新的写命令缓存到缓冲区
 * 
 * 4. 主节点将 RDB 文件发送给从节点
 *    从节点接收并保存为临时文件
 * 
 * 5. 从节点加载 RDB 文件
 *    恢复主节点的所有数据
 * 
 * 6. 主节点将缓冲区的命令发送给从节点
 *    从节点执行这些命令，完成同步
 */
```

**全量同步的性能影响：**
- 主节点执行 BGSAVE，占用 CPU 和内存
- 网络传输 RDB 文件，占用带宽
- 从节点加载 RDB，占用 CPU 和内存
- 同步期间，从节点无法提供服务

#### 2.3 增量同步（Partial Resync）

**触发条件：**
- 从节点重新连接主节点
- 从节点的 replication ID 与主节点匹配
- 从节点的偏移量在主节点的缓冲区范围内

**增量同步流程：**

```java
/**
 * 增量同步流程
 * 
 * 1. 从节点发送 PSYNC <replication_id> <offset>
 *    表示：我之前同步过，请从 offset 位置继续同步
 * 
 * 2. 主节点检查：
 *    - replication_id 是否匹配？
 *    - offset 是否在缓冲区范围内？
 * 
 * 3. 如果都匹配，主节点响应 +CONTINUE
 *    表示：可以进行增量同步
 * 
 * 4. 主节点将缓冲区中 offset 之后的命令发送给从节点
 *    从节点执行这些命令，完成同步
 * 
 * 5. 之后，主节点的每个写命令都会实时发送给从节点
 */
```

**增量同步的优势：**
- 只传输新增的命令，网络开销小
- 不需要重新生成 RDB，主节点压力小
- 同步速度快，数据延迟低

**缓冲区大小配置：**

```bash
# redis.conf
repl-backlog-size 1mb  # 默认 1MB，可根据需要调整

# 缓冲区大小计算：
# 假设主节点每秒产生 1MB 的写命令
# 从节点最多可能断线 60 秒
# 则缓冲区应该至少 60MB
```

### 三、主从复制的关键参数

```bash
# redis.conf 配置

# 从节点连接主节点
replicaof <master_ip> <master_port>

# 从节点是否只读
replica-read-only yes  # 默认只读，防止从节点被误写

# 复制缓冲区大小
repl-backlog-size 1mb

# 复制缓冲区保留时间
repl-backlog-ttl 3600  # 秒

# 从节点连接超时时间
repl-timeout 60  # 秒

# 从节点是否禁用 TCP_NODELAY
repl-disable-tcp-nodelay no  # 默认启用 TCP_NODELAY，降低延迟
```

### 四、主从复制的常见问题

#### 问题1：从节点数据不一致

```java
/**
 * 问题：主从复制是异步的，从节点的数据可能落后于主节点
 * 
 * 场景：
 * 1. 客户端写入数据到主节点
 * 2. 主节点立即返回成功
 * 3. 主节点异步发送命令给从节点
 * 4. 客户端立即从从节点读取数据
 * 5. 从节点还没收到命令，返回旧数据
 * 
 * 解决方案：
 * - 对于强一致性要求的数据，必须从主节点读取
 * - 使用 WAIT 命令等待从节点确认
 * - 使用 Redis Sentinel 或 Cluster 提高可用性
 */

// 使用 WAIT 命令
// WAIT numreplicas timeout
// 等待至少 numreplicas 个从节点确认写操作

// 示例：等待至少 1 个从节点确认，超时 1000ms
redis.set("key", "value");
redis.wait(1, 1000);  // 返回确认的从节点数
```

#### 问题2：主从切换期间的数据丢失

```java
/**
 * 问题：主节点故障，从节点升级为主节点时，可能丢失数据
 * 
 * 场景：
 * 1. 主节点收到写命令，返回成功
 * 2. 主节点还没来得及发送给从节点
 * 3. 主节点故障宕机
 * 4. 从节点升级为主节点
 * 5. 这条命令永久丢失
 * 
 * 解决方案：
 * - 使用 Redis Sentinel 的 min-slaves-to-write 配置
 * - 主节点必须至少有 N 个从节点确认，才能接受写操作
 * - 这样可以保证数据不丢失
 */

// redis.conf
min-slaves-to-write 1      # 至少 1 个从节点
min-slaves-max-lag 10      # 从节点延迟不超过 10 秒

// 如果从节点数量不足或延迟过大，主节点拒绝写操作
```

---

## 第二部分：Redis Sentinel（哨兵）

### 一、Sentinel 的基本概念

**Redis Sentinel** 是 Redis 的高可用解决方案。它监控主从节点的健康状态，当主节点故障时，自动将从节点升级为主节点，实现自动故障转移。

```
Sentinel 架构：
┌──────────────┐
│  Sentinel 1  │
└──────┬───────┘
       │ 监控
       │
┌──────▼──────────────────────────┐
│                                  │
│  ┌─────────────┐                │
│  │   Master    │                │
│  │  6379       │                │
│  └──────┬──────┘                │
│         │ 复制                   │
│    ┌────┴────┐                  │
│    │          │                 │
│ ┌──▼──┐  ┌──▼──┐               │
│ │Slave1│  │Slave2│              │
│ │6380  │  │6381  │              │
│ └──────┘  └──────┘              │
│                                  │
└──────────────────────────────────┘

┌──────────────┐  ┌──────────────┐
│  Sentinel 2  │  │  Sentinel 3  │
└──────────────┘  └──────────────┘
```

**Sentinel 的三个核心功能：**
1. **监控（Monitoring）**：定期检查主从节点是否正常
2. **故障检测（Failure Detection）**：发现主节点故障
3. **自动转移（Automatic Failover）**：选举新主节点，更新配置

### 二、Sentinel 的工作原理

#### 2.1 故障检测机制

```java
/**
 * Sentinel 故障检测流程
 * 
 * 1. 定期发送 PING 命令
 *    Sentinel 每秒向主从节点发送 PING 命令
 * 
 * 2. 判断节点状态
 *    - 如果收到 PONG 或 LOADING 或 MASTERDOWN 响应，认为节点在线
 *    - 如果没有收到响应，认为节点可能故障
 * 
 * 3. 主观下线（Subjective Down）
 *    单个 Sentinel 认为节点故障
 *    条件：down-after-milliseconds 时间内没有收到有效响应
 * 
 * 4. 客观下线（Objective Down）
 *    多个 Sentinel 都认为节点故障
 *    条件：至少 quorum 个 Sentinel 认为节点故障
 * 
 * 5. 触发故障转移
 *    当主节点被判定为客观下线时，触发故障转移
 */

// sentinel.conf 配置
sentinel monitor mymaster 127.0.0.1 6379 2
// 监控主节点 mymaster，地址 127.0.0.1:6379
// quorum = 2，至少 2 个 Sentinel 认为故障才转移

sentinel down-after-milliseconds mymaster 30000
// 30 秒内没有收到响应，认为主观下线

sentinel parallel-syncs mymaster 1
// 故障转移时，最多 1 个从节点同时进行全量同步
```

#### 2.2 故障转移流程

```
故障转移的 5 个步骤：

┌─────────────────────────────────────────────────────────┐
│ 步骤1：发现主节点故障                                    │
│ 多个 Sentinel 认为主节点客观下线                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤2：选举 Leader Sentinel                             │
│ 使用 Raft 算法，选出一个 Sentinel 负责故障转移          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤3：选择新主节点                                      │
│ 从从节点中选择一个升级为主节点                          │
│ 选择标准：                                              │
│ 1. 从节点优先级（replica-priority）                    │
│ 2. 复制偏移量（offset）最大                            │
│ 3. 运行 ID 最小                                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤4：升级新主节点                                      │
│ 向选中的从节点发送 SLAVEOF NO ONE 命令                  │
│ 该从节点升级为主节点                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤5：更新其他从节点                                    │
│ 向其他从节点发送 SLAVEOF 命令                           │
│ 让它们复制新主节点                                      │
└────────────────────────────────────────────────────────┘
```

#### 2.3 新主节点的选择算法

```java
/**
 * 新主节点选择算法
 * 
 * 优先级1：replica-priority（从节点优先级）
 *   - 配置中指定，默认 100
 *   - 优先级越低越优先（0 最高）
 *   - 可以手动调整，让某个从节点优先成为主节点
 * 
 * 优先级2：复制偏移量（Replication Offset）
 *   - 从节点复制的数据越多，偏移量越大
 *   - 偏移量最大的从节点数据最新
 *   - 优先选择数据最新的从节点
 * 
 * 优先级3：运行 ID（Run ID）
 *   - Redis 实例启动时生成的唯一标识
 *   - 如果前两个条件相同，选择 ID 最小的
 */

// sentinel.conf 配置
sentinel replica-priority mymaster 100

// 调整从节点优先级
// 在从节点的 redis.conf 中配置
replica-priority 10  # 优先级 10，比默认 100 更高
```

### 三、Sentinel 的配置和部署

#### 3.1 Sentinel 配置文件

```bash
# sentinel.conf

# 监控主节点
sentinel monitor mymaster 127.0.0.1 6379 2

# 主节点故障判定时间（毫秒）
sentinel down-after-milliseconds mymaster 30000

# 故障转移超时时间（毫秒）
sentinel failover-timeout mymaster 180000

# 故障转移时，最多多少个从节点同时进行全量同步
sentinel parallel-syncs mymaster 1

# 从节点优先级
sentinel replica-priority mymaster 100

# 通知脚本（故障转移时执行）
sentinel notification-script mymaster /path/to/notification.sh

# 客户端重新配置脚本
sentinel client-reconfig-script mymaster /path/to/reconfig.sh

# 日志文件
logfile "/var/log/redis/sentinel.log"

# 工作目录
dir /var/lib/redis
```

#### 3.2 启动 Sentinel

```bash
# 方式1：指定配置文件启动
redis-sentinel /path/to/sentinel.conf

# 方式2：指定端口启动（使用默认配置）
redis-sentinel /path/to/sentinel.conf --port 26379

# 方式3：使用 redis-server 启动 Sentinel 模式
redis-server /path/to/sentinel.conf --sentinel
```

#### 3.3 监控 Sentinel 状态

```bash
# 连接 Sentinel
redis-cli -p 26379

# 查看监控的主节点信息
SENTINEL masters

# 查看主节点的从节点信息
SENTINEL slaves mymaster

# 查看 Sentinel 节点信息
SENTINEL sentinels mymaster

# 强制故障转移（测试用）
SENTINEL failover mymaster

# 查看 Sentinel 配置
SENTINEL get-master-addr-by-name mymaster
```

### 四、Sentinel 的常见问题

#### 问题1：脑裂（Split Brain）

```java
/**
 * 问题：网络分区导致 Sentinel 和主节点通信中断
 * 
 * 场景：
 * 1. 主节点和 Sentinel 之间网络中断
 * 2. Sentinel 认为主节点故障，触发故障转移
 * 3. 从节点升级为新主节点
 * 4. 网络恢复，原主节点仍然接受写操作
 * 5. 现在有两个主节点，数据不一致
 * 
 * 解决方案：
 * - 使用 min-slaves-to-write 和 min-slaves-max-lag
 * - 主节点必须至少有 N 个从节点确认，才能接受写操作
 * - 如果从节点数量不足或延迟过大，主节点拒绝写操作
 * - 这样可以防止脑裂时的数据不一致
 */

// redis.conf
min-slaves-to-write 1      # 至少 1 个从节点
min-slaves-max-lag 10      # 从节点延迟不超过 10 秒

// 如果从节点数量不足或延迟过大，主节点拒绝写操作
// 这样可以防止脑裂时的数据不一致
```

#### 问题2：Sentinel 本身故障

```java
/**
 * 问题：Sentinel 节点故障，无法进行故障转移
 * 
 * 解决方案：
 * - 部署多个 Sentinel 节点（通常 3 个或 5 个）
 * - 使用 Raft 算法选举 Leader Sentinel
 * - 只要大多数 Sentinel 正常，就能进行故障转移
 * - 推荐部署奇数个 Sentinel（3、5、7 等）
 */

// 部署 3 个 Sentinel 节点
// Sentinel 1: 127.0.0.1:26379
// Sentinel 2: 127.0.0.1:26380
// Sentinel 3: 127.0.0.1:26381

// 每个 Sentinel 的配置都相同
sentinel monitor mymaster 127.0.0.1 6379 2
```

---

## 第三部分：Redis Cluster（集群）

### 一、Cluster 的基本概念

**Redis Cluster** 是 Redis 的分布式集群方案。它将数据分片存储在多个节点上，每个节点负责一部分数据，实现水平扩展和高可用。

```
Cluster 架构（6 个节点，3 主 3 从）：

┌─────────────────────────────────────────────────────────┐
│                    Redis Cluster                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Master 1 │  │ Master 2 │  │ Master 3 │              │
│  │ 6379     │  │ 6380     │  │ 6381     │              │
│  │ 槽 0-5460│  │ 槽 5461- │  │ 槽 10923-│              │
│  │          │  │ 10922    │  │ 16383    │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                     │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐             │
│  │ Slave 1  │  │ Slave 2  │  │ Slave 3  │             │
│  │ 6382     │  │ 6383     │  │ 6384     │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                          │
│  节点之间通过 Gossip 协议通信                           │
│  每个节点都知道其他节点的状态                           │
└─────────────────────────────────────────────────────────┘
```

**Cluster 的核心特性：**
1. **数据分片**：16384 个槽分配到多个节点
2. **高可用**：每个主节点有从节点，故障自动转移
3. **水平扩展**：添加新节点，重新分配槽
4. **去中心化**：没有中心节点，任何节点都可以接收请求

### 二、槽分片（Slot Sharding）

#### 2.1 槽的基本概念

```java
/**
 * Redis Cluster 使用 16384 个槽来分片数据
 * 
 * 槽的计算方式：
 * slot = CRC16(key) % 16384
 * 
 * 其中：
 * - CRC16：循环冗余校验算法
 * - key：Redis 的键
 * - 16384：槽的总数（2^14）
 * 
 * 槽的分配：
 * - 每个主节点负责一部分槽
 * - 所有 16384 个槽都必须被分配
 * - 槽的分配可以动态调整
 */

// 计算 key 所在的槽
// 示例：key = "user:1000"
// slot = CRC16("user:1000") % 16384 = 5474

// 在 Redis 中查询 key 所在的槽
redis-cli cluster keyslot "user:1000"
// 输出：5474
```

#### 2.2 槽的分配策略

```bash
# 3 个主节点的槽分配

# Master 1: 0 - 5460
# Master 2: 5461 - 10922
# Master 3: 10923 - 16383

# 每个主节点负责 16384 / 3 ≈ 5461 个槽

# 槽的分配可以通过 CLUSTER ADDSLOTS 命令调整
redis-cli cluster addslots 0 1 2 3 4 5  # 添加槽
redis-cli cluster delslots 0 1 2 3 4 5  # 删除槽
```

### 三、Cluster 的数据路由

#### 3.1 MOVED 重定向

```java
/**
 * MOVED 重定向：当客户端请求的 key 不在当前节点时
 * 
 * 场景：
 * 1. 客户端连接到 Node A
 * 2. 请求 key "user:1000"
 * 3. 计算 slot = 5474
 * 4. Node A 发现 slot 5474 不在自己负责的范围内
 * 5. Node A 返回 MOVED 5474 127.0.0.1:6380
 *    表示：这个 slot 在 127.0.0.1:6380 上
 * 6. 客户端重定向到 Node B (127.0.0.1:6380)
 * 7. Node B 处理请求，返回结果
 * 
 * MOVED 表示：槽的位置已经确定，客户端应该更新路由表
 */

// 客户端收到 MOVED 响应后的处理
// 1. 更新本地的槽位映射表
// 2. 下次请求直接连接到正确的节点
// 3. 避免不必要的重定向
```

#### 3.2 ASK 重定向

```java
/**
 * ASK 重定向：当槽正在迁移时
 * 
 * 场景：
 * 1. 集群正在进行槽迁移
 * 2. slot 5474 从 Node A 迁移到 Node B
 * 3. 迁移过程中，slot 5474 既在 Node A，也在 Node B
 * 4. 客户端请求 key "user:1000"（slot 5474）
 * 5. Node A 发现 slot 5474 正在迁移
 * 6. Node A 返回 ASK 5474 127.0.0.1:6380
 *    表示：这个 slot 正在迁移，请尝试连接到新节点
 * 7. 客户端发送 ASKING 命令，然后重试请求
 * 8. Node B 处理请求，返回结果
 * 
 * ASK 表示：槽的位置临时改变，客户端应该尝试新节点
 * 与 MOVED 不同，ASK 不会更新路由表
 */

// MOVED vs ASK
// MOVED：槽的位置已经确定，更新路由表
// ASK：槽正在迁移，临时重定向，不更新路由表
```

#### 3.3 客户端路由实现

```java
/**
 * Redis Cluster 客户端路由实现
 * 
 * 1. 初始化：获取集群的槽位映射表
 *    CLUSTER SLOTS 命令返回所有槽的分配情况
 * 
 * 2. 请求处理：
 *    a. 计算 key 所在的槽
 *    b. 查询本地槽位映射表，找到对应的节点
 *    c. 连接到该节点，发送请求
 * 
 * 3. 处理重定向：
 *    a. 如果收到 MOVED 响应，更新槽位映射表
 *    b. 如果收到 ASK 响应，发送 ASKING 命令，重试请求
 * 
 * 4. 定期更新：
 *    a. 定期执行 CLUSTER SLOTS 命令
 *    b. 更新本地的槽位映射表
 *    c. 应对集群拓扑变化
 */

// 获取集群的槽位映射表
redis-cli cluster slots

// 输出示例：
// 1) 1) (integer) 0
//    2) (integer) 5460
//    3) 1) "127.0.0.1"
//       2) (integer) 6379
//    4) 1) "127.0.0.1"
//       2) (integer) 6382
// 2) 1) (integer) 5461
//    2) (integer) 10922
//    3) 1) "127.0.0.1"
//       2) (integer) 6380
//    4) 1) "127.0.0.1"
//       2) (integer) 6383
// ...
```

### 四、Cluster 的槽迁移和数据重平衡

#### 4.1 槽迁移的流程

```
槽迁移的 6 个步骤：

┌─────────────────────────────────────────────────────────┐
│ 步骤1：设置源节点为迁移状态                              │
│ 源节点标记 slot 为 MIGRATING 状态                       │
│ 表示：这个 slot 正在迁移出去                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤2：设置目标节点为导入状态                            │
│ 目标节点标记 slot 为 IMPORTING 状态                     │
│ 表示：这个 slot 正在迁移进来                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤3：迁移数据                                          │
│ 源节点将 slot 中的所有 key 迁移到目标节点               │
│ 使用 MIGRATE 命令逐个迁移 key                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤4：更新集群配置                                      │
│ 集群管理工具（如 redis-cli）发送 CLUSTER SETSLOT 命令  │
│ 通知所有节点：slot 的所有权已转移                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤5：清除源节点的 slot 标记                            │
│ 源节点删除 MIGRATING 标记                               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 步骤6：清除目标节点的 slot 标记                          │
│ 目标节点删除 IMPORTING 标记                             │
│ 迁移完成                                                │
└────────────────────────────────────────────────────────┘
```

#### 4.2 槽迁移的命令

```bash
# 查看集群节点信息
redis-cli cluster nodes

# 查看集群槽位分配
redis-cli cluster slots

# 设置 slot 为 MIGRATING 状态（源节点）
redis-cli cluster setslot <slot> migrating <target_node_id>

# 设置 slot 为 IMPORTING 状态（目标节点）
redis-cli cluster setslot <slot> importing <source_node_id>

# 迁移单个 key
redis-cli migrate <target_host> <target_port> <key> 0 5000

# 设置 slot 的所有权（集群管理工具）
redis-cli cluster setslot <slot> node <node_id>

# 使用 redis-cli 进行集群扩展
redis-cli --cluster add-node <new_node> <existing_node>
redis-cli --cluster reshard <node>
```

#### 4.3 数据重平衡

```java
/**
 * 数据重平衡：当添加或删除节点时，重新分配槽
 * 
 * 场景1：添加新节点
 * 1. 新节点加入集群，初始没有槽
 * 2. 使用 redis-cli --cluster reshard 命令
 * 3. 从其他节点迁移一些槽到新节点
 * 4. 新节点开始处理请求
 * 
 * 场景2：删除节点
 * 1. 使用 redis-cli --cluster reshard 命令
 * 2. 将该节点的所有槽迁移到其他节点
 * 3. 节点变为空，可以安全删除
 */

// 添加新节点到集群
redis-cli --cluster add-node 127.0.0.1:6385 127.0.0.1:6379

// 重新分配槽（交互式）
redis-cli --cluster reshard 127.0.0.1:6379

// 删除节点
redis-cli --cluster del-node 127.0.0.1:6379 <node_id>
```

### 五、Cluster 的高可用

#### 5.1 故障转移

```java
/**
 * Cluster 的故障转移机制
 * 
 * 1. 故障检测：
 *    - 每个节点定期向其他节点发送 PING 命令
 *    - 如果没有收到 PONG 响应，认为节点可能故障
 * 
 * 2. 故障确认：
 *    - 多个节点都认为某个节点故障
 *    - 该节点被标记为 FAIL 状态
 * 
 * 3. 从节点升级：
 *    - 故障主节点的从节点发起选举
 *    - 使用 Raft 算法选出新主节点
 * 
 * 4. 配置更新：
 *    - 新主节点接管故障主节点的槽
 *    - 集群配置更新，通知所有节点
 */

// 查看集群节点状态
redis-cli cluster nodes

// 输出示例：
// 07c37dfeb235213a872192d90877d0cd55635b91 127.0.0.1:6379@16379 master - 0 1234567890 1 connected 0-5460
// 0f8c9b8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c 127.0.0.1:6380@16380 master - 0 1234567890 2 connected 5461-10922
// ...

// 节点状态说明：
// - connected：节点正常
// - disconnected：节点断开连接
// - fail：节点故障
// - handshake：节点握手中
```

#### 5.2 从节点选举

```java
/**
 * Cluster 从节点选举算法
 * 
 * 1. 选举条件：
 *    - 主节点被标记为 FAIL
 *    - 从节点的主节点是 FAIL 状态
 * 
 * 2. 选举过程：
 *    - 从节点向其他节点发送 CLUSTER FAILOVER 命令
 *    - 其他节点投票
 *    - 获得大多数投票的从节点成为新主节点
 * 
 * 3. 选举优先级：
 *    - 复制偏移量最大（数据最新）
 *    - 从节点优先级（replica-priority）
 *    - 运行 ID 最小
 */

// 手动触发故障转移（测试用）
redis-cli cluster failover

// 强制故障转移（不等待主节点确认）
redis-cli cluster failover force

// 故障转移超时配置
// cluster-node-timeout 15000  # 毫秒
```

### 六、Cluster 的 Gossip 协议

#### 6.1 Gossip 协议的基本概念

```java
/**
 * Gossip 协议：集群节点之间的通信协议
 * 
 * 特点：
 * 1. 去中心化：没有中心节点，所有节点平等
 * 2. 最终一致性：信息最终会传播到所有节点
 * 3. 容错性强：即使某些节点故障，集群仍能正常工作
 * 
 * 工作原理：
 * 1. 每个节点定期选择随机节点发送 PING 消息
 * 2. 接收节点返回 PONG 消息
 * 3. 消息中包含节点的状态信息
 * 4. 节点根据收到的信息更新自己的状态
 * 5. 信息逐步传播到所有节点
 */

// Gossip 消息的内容：
// 1. 节点 ID
// 2. 节点地址和端口
// 3. 节点状态（master/slave/fail）
// 4. 节点的槽位分配
// 5. 节点的配置版本
// 6. 其他节点的信息
```

#### 6.2 Gossip 协议的配置

```bash
# redis.conf

# 集群节点超时时间（毫秒）
cluster-node-timeout 15000

# 集群故障转移超时时间（毫秒）
cluster-failover-timeout 180000

# 集群从节点迁移延迟（毫秒）
cluster-replica-validity-factor 10

# 集群从节点最少连接数
cluster-min-replicas-to-write 0

# 集群从节点最大延迟（秒）
cluster-min-replicas-max-lag 10
```

---

## 第四部分：客户端连接集群

### 一、Jedis 连接集群

```java
import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisCluster;
import java.util.HashSet;
import java.util.Set;

public class JedisClusterExample {
    
    public static void main(String[] args) {
        // 1. 创建集群节点集合
        Set<HostAndPort> nodes = new HashSet<>();
        nodes.add(new HostAndPort("127.0.0.1", 6379));
        nodes.add(new HostAndPort("127.0.0.1", 6380));
        nodes.add(new HostAndPort("127.0.0.1", 6381));
        
        // 2. 创建 JedisCluster 实例
        JedisCluster cluster = new JedisCluster(nodes);
        
        // 3. 使用集群
        cluster.set("key1", "value1");
        String value = cluster.get("key1");
        System.out.println(value);  // 输出：value1
        
        // 4. 关闭连接
        cluster.close();
    }
}
```

### 二、Lettuce 连接集群

```java
import io.lettuce.core.RedisURI;
import io.lettuce.core.cluster.RedisClusterClient;
import io.lettuce.core.cluster.api.StatefulRedisClusterConnection;
import io.lettuce.core.cluster.api.sync.RedisAdvancedClusterCommands;

public class LettuceClusterExample {
    
    public static void main(String[] args) {
        // 1. 创建集群 URI
        RedisURI uri1 = RedisURI.create("redis://127.0.0.1:6379");
        RedisURI uri2 = RedisURI.create("redis://127.0.0.1:6380");
        RedisURI uri3 = RedisURI.create("redis://127.0.0.1:6381");
        
        // 2. 创建集群客户端
        RedisClusterClient client = RedisClusterClient.create(
            Arrays.asList(uri1, uri2, uri3)
        );
        
        // 3. 获取连接
        StatefulRedisClusterConnection<String, String> connection = 
            client.connect();
        
        // 4. 获取同步命令接口
        RedisAdvancedClusterCommands<String, String> commands = 
            connection.sync();
        
        // 5. 使用集群
        commands.set("key1", "value1");
        String value = commands.get("key1");
        System.out.println(value);  // 输出：value1
        
        // 6. 关闭连接
        connection.close();
        client.shutdown();
    }
}
```

### 三、Spring Data Redis 连接集群

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisClusterConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.StringRedisSerializer;

@Configuration
public class RedisClusterConfig {
    
    @Bean
    public RedisClusterConfiguration redisClusterConfiguration() {
        RedisClusterConfiguration config = new RedisClusterConfiguration();
        config.clusterNode("127.0.0.1", 6379);
        config.clusterNode("127.0.0.1", 6380);
        config.clusterNode("127.0.0.1", 6381);
        return config;
    }
    
    @Bean
    public LettuceConnectionFactory connectionFactory(
            RedisClusterConfiguration config) {
        return new LettuceConnectionFactory(config);
    }
    
    @Bean
    public RedisTemplate<String, String> redisTemplate(
            LettuceConnectionFactory factory) {
        RedisTemplate<String, String> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        
        // 设置序列化器
        StringRedisSerializer serializer = new StringRedisSerializer();
        template.setKeySerializer(serializer);
        template.setValueSerializer(serializer);
        
        return template;
    }
}

// 使用示例
@Service
public class RedisService {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    public void set(String key, String value) {
        redisTemplate.opsForValue().set(key, value);
    }
    
    public String get(String key) {
        return redisTemplate.opsForValue().get(key);
    }
}
```

---

## 第五部分：主从切换期间的读写问题

### 一、主从切换的时间线

```
主从切换的完整时间线：

T0: 主节点正常运行
    - 客户端可以正常读写
    - 从节点正常复制数据

T1: 主节点故障
    - 主节点无法响应请求
    - 客户端请求超时

T2: 故障检测（30 秒）
    - Sentinel 发现主节点故障
    - 标记为主观下线

T3: 故障确认（30 秒）
    - 多个 Sentinel 确认故障
    - 标记为客观下线

T4: 故障转移开始（1 秒）
    - 选举 Leader Sentinel
    - 选择新主节点

T5: 从节点升级（5 秒）
    - 从节点升级为主节点
    - 其他从节点重新连接

T6: 故障转移完成（1 秒）
    - 集群配置更新
    - 客户端重新连接

总耗时：约 60-70 秒
```

### 二、主从切换期间的读写问题

```java
/**
 * 问题1：写操作丢失
 * 
 * 场景：
 * T1: 客户端写入数据到主节点
 * T2: 主节点返回成功
 * T3: 主节点还没来得及发送给从节点
 * T4: 主节点故障
 * T5: 从节点升级为主节点
 * T6: 这条写操作永久丢失
 * 
 * 解决方案：
 * - 使用 min-slaves-to-write 和 min-slaves-max-lag
 * - 主节点必须至少有 N 个从节点确认，才能接受写操作
 * - 如果从节点数量不足或延迟过大，主节点拒绝写操作
 */

// redis.conf
min-slaves-to-write 1      # 至少 1 个从节点
min-slaves-max-lag 10      # 从节点延迟不超过 10 秒

// 如果从节点数量不足或延迟过大，主节点拒绝写操作
// 这样可以保证数据不丢失
```

```java
/**
 * 问题2：读操作返回旧数据
 * 
 * 场景：
 * T1: 客户端从从节点读取数据
 * T2: 从节点返回旧数据（还没同步最新数据）
 * T3: 主节点故障，从节点升级为主节点
 * T4: 客户端读取的是旧数据
 * 
 * 解决方案：
 * - 对于强一致性要求的数据，必须从主节点读取
 * - 使用 WAIT 命令等待从节点确认
 * - 接受最终一致性，允许短期数据不一致
 */

// 方案1：从主节点读取
String value = redisTemplate.opsForValue().get(key);

// 方案2：使用 WAIT 命令
redis.set("key", "value");
redis.wait(1, 1000);  // 等待至少 1 个从节点确认，超时 1000ms

// 方案3：接受最终一致性
// 从节点可能返回旧数据，但最终会一致
```

```java
/**
 * 问题3：脑裂导致数据不一致
 * 
 * 场景：
 * T1: 主节点和 Sentinel 之间网络中断
 * T2: Sentinel 认为主节点故障，触发故障转移
 * T3: 从节点升级为新主节点
 * T4: 网络恢复，原主节点仍然接受写操作
 * T5: 现在有两个主节点，数据不一致
 * 
 * 解决方案：
 * - 使用 min-slaves-to-write 和 min-slaves-max-lag
 * - 主节点必须至少有 N 个从节点确认，才能接受写操作
 * - 如果从节点数量不足或延迟过大，主节点拒绝写操作
 * - 这样可以防止脑裂时的数据不一致
 */

// redis.conf
min-slaves-to-write 1      # 至少 1 个从节点
min-slaves-max-lag 10      # 从节点延迟不超过 10 秒

// 脑裂时，原主节点无法连接到从节点
// 因此拒绝写操作，防止数据不一致
```

---

## 第六部分：代理模式 vs 直连模式

### 一、直连模式（Direct Connection）

```
直连模式架构：

┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 直接连接
       │
   ┌───┴────┬──────────┐
   │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│Node1 │  │Node2 │  │Node3 │
└──────┘  └──────┘  └──────┘

优点：
- 性能最高，没有代理开销
- 支持 Cluster 的所有特性
- 客户端直接与 Redis 通信

缺点：
- 客户端需要实现路由逻辑
- 需要处理 MOVED 和 ASK 重定向
- 集群拓扑变化时需要更新路由表
```

### 二、代理模式（Proxy Mode）

#### 2.1 Twemproxy

```
Twemproxy 架构：

┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 连接代理
       │
┌──────▼──────────┐
│   Twemproxy     │  (代理层)
│   6379          │
└──────┬──────────┘
       │ 路由请求
       │
   ┌───┴────┬──────────┐
   │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│Node1 │  │Node2 │  │Node3 │
└──────┘  └──────┘  └──────┘

优点：
- 客户端无需实现路由逻辑
- 支持多种 Redis 集群方案
- 可以进行请求转发和优化

缺点：
- 代理层增加延迟
- 代理本身是单点故障
- 需要部署和维护代理
```

#### 2.2 Codis

```
Codis 架构：

┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 连接代理
       │
┌──────▼──────────┐
│   Codis Proxy   │  (代理层)
│   6379          │
└──────┬──────────┘
       │ 路由请求
       │
   ┌───┴────┬──────────┐
   │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│Node1 │  │Node2 │  │Node3 │
└──────┘  └──────┘  └──────┘

┌──────────────────┐
│  Codis Dashboard │  (管理界面)
│  Zookeeper       │  (配置中心)
└──────────────────┘

优点：
- 支持在线扩容和缩容
- 支持自动故障转移
- 提供管理界面
- 支持多个代理实例

缺点：
- 代理层增加延迟
- 需要部署 Zookeeper
- 配置复杂
```

#### 2.3 Sentinel 代理模式

```
Sentinel 代理模式架构：

┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 连接 Sentinel
       │
   ┌───┴────┬──────────┐
   │         │          │
┌──▼──┐  ┌──▼──┐  ┌──▼──┐
│Sent1 │  │Sent2 │  │Sent3 │  (Sentinel 集群)
└──────┘  └──────┘  └──────┘
   │         │          │
   └────┬────┴────┬─────┘
        │         │
    ┌───▼──┐  ┌──▼───┐
    │Master │  │Slave │  (主从集群)
    └───────┘  └──────┘

优点：
- 自动故障转移
- 高可用
- 客户端无需实现故障转移逻辑

缺点：
- 只支持主从模式，不支持分片
- 不能水平扩展
- 读写分离需要客户端实现
```

### 三、模式对比

| 特性 | 直连模式 | Twemproxy | Codis | Sentinel |
|------|---------|-----------|-------|----------|
| 性能 | 最高 | 中等 | 中等 | 中等 |
| 延迟 | 最低 | 较高 | 较高 | 较高 |
| 分片 | 支持 | 支持 | 支持 | 不支持 |
| 故障转移 | 自动 | 不支持 | 支持 | 支持 |
| 在线扩容 | 支持 | 不支持 | 支持 | 不支持 |
| 客户端复杂度 | 高 | 低 | 低 | 低 |
| 代理开销 | 无 | 有 | 有 | 有 |
| 推荐场景 | 大规模应用 | 小规模应用 | 中等规模 | 主从模式 |

---

## 第七部分：集群模式下的高可用保证

### 一、数据冗余

```java
/**
 * 数据冗余：每个主节点都有从节点
 * 
 * 优势：
 * 1. 主节点故障，从节点可以升级为主节点
 * 2. 数据不会丢失
 * 3. 服务不会中断
 * 
 * 配置：
 * - 每个主节点至少有 1 个从节点
 * - 可以配置多个从节点，提高可用性
 */

// 查看集群节点信息
redis-cli cluster nodes

// 输出示例：
// 07c37dfeb235213a872192d90877d0cd55635b91 127.0.0.1:6379@16379 master - 0 1234567890 1 connected 0-5460
// 0f8c9b8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c 127.0.0.1:6382@16382 slave 07c37dfeb235213a872192d90877d0cd55635b91 0 1234567890 1 connected
```

### 二、故障检测和转移

```java
/**
 * 故障检测和转移：
 * 
 * 1. 故障检测：
 *    - 每个节点定期向其他节点发送 PING 命令
 *    - 如果没有收到 PONG 响应，认为节点可能故障
 * 
 * 2. 故障确认：
 *    - 多个节点都认为某个节点故障
 *    - 该节点被标记为 FAIL 状态
 * 
 * 3. 从节点升级：
 *    - 故障主节点的从节点发起选举
 *    - 使用 Raft 算法选出新主节点
 * 
 * 4. 配置更新：
 *    - 新主节点接管故障主节点的槽
 *    - 集群配置更新，通知所有节点
 */

// 配置参数
// cluster-node-timeout 15000  # 节点超时时间（毫秒）
// cluster-failover-timeout 180000  # 故障转移超时时间（毫秒）
```

### 三、槽的完整性

```java
/**
 * 槽的完整性：所有 16384 个槽都必须被分配
 * 
 * 如果某个槽没有被分配，集群会进入 FAIL 状态
 * 所有请求都会被拒绝
 * 
 * 场景：
 * 1. 节点故障，该节点的槽无法访问
 * 2. 槽迁移过程中，槽暂时无法访问
 * 3. 集群配置错误，某个槽没有被分配
 * 
 * 解决方案：
 * - 确保每个主节点都有从节点
 * - 故障转移时，从节点升级为主节点
 * - 槽迁移完成后，更新集群配置
 */

// 查看集群状态
redis-cli cluster info

// 输出示例：
// cluster_state:ok  # 集群状态正常
// cluster_slots_assigned:16384  # 已分配的槽数
// cluster_slots_ok:16384  # 正常的槽数
// cluster_slots_pfail:0  # 可能故障的槽数
// cluster_slots_fail:0  # 故障的槽数
```

---

## 第八部分：高频面试题

### Q1: Redis 主从复制的全量同步和增量同步有什么区别？

**答：**

**全量同步（Full Resync）：**
- 触发条件：从节点首次连接主节点，或 replication ID 不匹配，或偏移量超出缓冲区
- 流程：主节点生成 RDB 快照，发送给从节点，从节点加载 RDB，然后执行缓冲区中的命令
- 性能影响：主节点执行 BGSAVE，占用 CPU 和内存；网络传输 RDB 文件，占用带宽；从节点加载 RDB，占用 CPU 和内存
- 适用场景：从节点首次连接，或长时间断线后重新连接

**增量同步（Partial Resync）：**
- 触发条件：从节点重新连接主节点，replication ID 匹配，偏移量在缓冲区范围内
- 流程：主节点直接发送缓冲区中偏移量之后的命令给从节点
- 性能影响：只传输新增的命令，网络开销小；主节点压力小；同步速度快
- 适用场景：从节点短时间断线后重新连接

**关键参数：**
- `repl-backlog-size`：复制缓冲区大小，默认 1MB
- `repl-backlog-ttl`：复制缓冲区保留时间，默认 3600 秒

---

### Q2: Redis Sentinel 如何实现自动故障转移？

**答：**

**故障检测：**
1. Sentinel 每秒向主从节点发送 PING 命令
2. 如果没有收到响应，认为节点主观下线
3. 多个 Sentinel 都认为节点故障，该节点被标记为客观下线

**故障转移流程：**
1. 选举 Leader Sentinel：使用 Raft 算法，选出一个 Sentinel 负责故障转移
2. 选择新主节点：从从节点中选择一个升级为主节点，选择标准是优先级、复制偏移量、运行 ID
3. 升级新主节点：向选中的从节点发送 SLAVEOF NO ONE 命令
4. 更新其他从节点：向其他从节点发送 SLAVEOF 命令，让它们复制新主节点
5. 更新客户端配置：通知客户端新主节点的地址

**关键配置：**
- `sentinel monitor`：监控的主节点
- `sentinel down-after-milliseconds`：故障判定时间
- `sentinel parallel-syncs`：故障转移时最多多少个从节点同时进行全量同步
- `min-slaves-to-write`：主节点必须至少有 N 个从节点确认，才能接受写操作

---

### Q3: Redis Cluster 的槽分片是如何工作的？

**答：**

**槽的基本概念：**
- Redis Cluster 使用 16384 个槽来分片数据
- 槽的计算方式：`slot = CRC16(key) % 16384`
- 每个主节点负责一部分槽，所有 16384 个槽都必须被分配

**槽的分配：**
- 3 个主节点的槽分配：Master 1: 0-5460，Master 2: 5461-10922，Master 3: 10923-16383
- 每个主节点负责约 5461 个槽
- 槽的分配可以通过 CLUSTER ADDSLOTS 和 CLUSTER DELSLOTS 命令调整

**数据路由：**
1. 客户端计算 key 所在的槽
2. 查询本地槽位映射表，找到对应的节点
3. 连接到该节点，发送请求
4. 如果收到 MOVED 响应，更新槽位映射表
5. 如果收到 ASK 响应，发送 ASKING 命令，重试请求

**MOVED vs ASK：**
- MOVED：槽的位置已经确定，更新路由表
- ASK：槽正在迁移，临时重定向，不更新路由表

---

### Q4: Redis Cluster 如何进行槽迁移和数据重平衡？

**答：**

**槽迁移的流程：**
1. 设置源节点为 MIGRATING 状态：表示这个槽正在迁移出去
2. 设置目标节点为 IMPORTING 状态：表示这个槽正在迁移进来
3. 迁移数据：源节点将槽中的所有 key 迁移到目标节点，使用 MIGRATE 命令
4. 更新集群配置：发送 CLUSTER SETSLOT 命令，通知所有节点槽的所有权已转移
5. 清除源节点的 MIGRATING 标记
6. 清除目标节点的 IMPORTING 标记

**数据重平衡：**
- 添加新节点：使用 `redis-cli --cluster add-node` 命令，然后使用 `redis-cli --cluster reshard` 命令重新分配槽
- 删除节点：使用 `redis-cli --cluster reshard` 命令将该节点的所有槽迁移到其他节点，然后使用 `redis-cli --cluster del-node` 命令删除节点

**关键命令：**
- `CLUSTER SLOTS`：查看槽位分配
- `CLUSTER NODES`：查看集群节点信息
- `CLUSTER SETSLOT`：设置槽的状态
- `MIGRATE`：迁移 key

---

### Q5: Redis Cluster 中 MOVED 和 ASK 重定向有什么区别？

**答：**

**MOVED 重定向：**
- 场景：槽的位置已经确定，客户端请求的 key 不在当前节点
- 响应：`MOVED slot node_address`
- 客户端处理：更新本地的槽位映射表，下次请求直接连接到正确的节点
- 含义：槽的所有权已经转移，不会再改变

**ASK 重定向：**
- 场景：槽正在迁移，客户端请求的 key 可能在源节点或目标节点
- 响应：`ASK slot node_address`
- 客户端处理：发送 ASKING 命令，然后重试请求，但不更新槽位映射表
- 含义：槽的位置临时改变，迁移完成后会恢复

**区别总结：**
| 特性 | MOVED | ASK |
|------|-------|-----|
| 触发场景 | 槽的所有权已转移 | 槽正在迁移 |
| 是否更新路由表 | 是 | 否 |
| 是否发送 ASKING | 否 | 是 |
| 是否临时 | 否 | 是 |

---

### Q6: 如何使用 Jedis 连接 Redis Cluster？

**答：**

```java
import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.JedisPoolConfig;
import java.util.HashSet;
import java.util.Set;

public class JedisClusterExample {
    
    public static void main(String[] args) {
        // 1. 配置连接池
        JedisPoolConfig config = new JedisPoolConfig();
        config.setMaxTotal(100);  // 最大连接数
        config.setMaxIdle(50);    // 最大空闲连接数
        config.setMinIdle(10);    // 最小空闲连接数
        config.setTestOnBorrow(true);  // 获取连接时测试
        
        // 2. 创建集群节点集合
        Set<HostAndPort> nodes = new HashSet<>();
        nodes.add(new HostAndPort("127.0.0.1", 6379));
        nodes.add(new HostAndPort("127.0.0.1", 6380));
        nodes.add(new HostAndPort("127.0.0.1", 6381));
        
        // 3. 创建 JedisCluster 实例
        JedisCluster cluster = new JedisCluster(nodes, config);
        
        // 4. 使用集群
        cluster.set("key1", "value1");
        String value = cluster.get("key1");
        System.out.println(value);  // 输出：value1
        
        // 5. 关闭连接
        cluster.close();
    }
}
```

**关键特性：**
- 自动路由：Jedis 自动计算 key 所在的槽，连接到正确的节点
- 自动重定向：处理 MOVED 和 ASK 重定向
- 连接池：支持连接池，提高性能
- 故障转移：支持自动故障转移

---

### Q7: 主从切换期间可能出现哪些问题？如何解决？

**答：**

**问题1：写操作丢失**
- 场景：主节点收到写操作，返回成功，但还没发送给从节点就故障了
- 解决方案：使用 `min-slaves-to-write` 和 `min-slaves-max-lag` 配置，主节点必须至少有 N 个从节点确认，才能接受写操作

**问题2：读操作返回旧数据**
- 场景：从节点返回旧数据，主节点故障，从节点升级为主节点
- 解决方案：对于强一致性要求的数据，必须从主节点读取；或使用 WAIT 命令等待从节点确认

**问题3：脑裂导致数据不一致**
- 场景：网络分区导致主节点和从节点通信中断，Sentinel 触发故障转移，原主节点仍然接受写操作
- 解决方案：使用 `min-slaves-to-write` 和 `min-slaves-max-lag` 配置，防止脑裂时的数据不一致

**配置示例：**
```bash
# redis.conf
min-slaves-to-write 1      # 至少 1 个从节点
min-slaves-max-lag 10      # 从节点延迟不超过 10 秒

# 如果从节点数量不足或延迟过大，主节点拒绝写操作
```

---

### Q8: Redis Cluster 和 Redis Sentinel 有什么区别？

**答：**

| 特性 | Cluster | Sentinel |
|------|---------|----------|
| 数据分片 | 支持（16384 个槽） | 不支持 |
| 水平扩展 | 支持 | 不支持 |
| 故障转移 | 自动 | 自动 |
| 高可用 | 支持 | 支持 |
| 客户端复杂度 | 高（需要实现路由） | 低 |
| 部署复杂度 | 高 | 低 |
| 适用场景 | 大规模应用，需要分片 | 中小规模应用，主从模式 |
| 读写分离 | 支持 | 支持 |
| 性能 | 高（分片提高吞吐量） | 中等 |

**选择建议：**
- 小规模应用（单机 Redis 无法满足）：使用 Sentinel
- 大规模应用（需要分片提高吞吐量）：使用 Cluster
- 需要在线扩容：使用 Cluster
- 需要简单部署：使用 Sentinel

---

## 总结

**Redis 集群方案的演进：**
1. **主从复制**：基础的数据备份和读写分离
2. **Sentinel**：自动故障转移，提高可用性
3. **Cluster**：数据分片，水平扩展，完整的高可用方案

**选择建议：**
- 小规模应用：主从复制 + Sentinel
- 中等规模应用：Sentinel 或 Cluster
- 大规模应用：Cluster

**关键要点：**
- 理解主从复制的全量同步和增量同步机制
- 理解 Sentinel 的故障检测和自动转移原理
- 理解 Cluster 的槽分片和数据路由机制
- 理解主从切换期间的读写问题和解决方案
- 选择合适的客户端库（Jedis/Lettuce）连接集群

---

**参考链接：**
- [Redis 官方文档 - Replication](https://redis.io/docs/management/replication/)
- [Redis 官方文档 - Sentinel](https://redis.io/docs/management/sentinel/)
- [Redis 官方文档 - Cluster](https://redis.io/docs/management/cluster-tutorial/)
- [Jedis GitHub](https://github.com/redis/jedis)
- [Lettuce GitHub](https://github.com/lettuce-io/lettuce-core)
