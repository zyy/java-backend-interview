---
layout: default
title: Redis 7 新特性详解
---
# Redis 7 新特性详解

## 🎯 面试题：Redis 7 有哪些重要更新？

> Redis 7 是一个大版本更新，引入了 Functions、ACL v2、Sharded Pub/Sub 等重要特性，大幅提升了编程能力和运维能力。

---

## 一、Redis 7 主要特性总览

| 特性 | 说明 | 版本 |
|------|------|------|
| Redis Functions | 取代 EVAL 脚本，更好的脚本管理 | 7.0 |
| Sharded Pub/Sub | 分片 Pub/Sub，解决广播风暴 | 7.0 |
| ACL v2 | 更细粒度的权限控制 | 7.0 |
| Client Eviction | 连接数限制，自动断开空闲客户端 | 7.0 |
| Multi-part AOF | AOF 拆分为多个文件，加速重写 | 7.0 |
| CMD DOCS | 内置命令文档 | 7.0 |
| 去除旧版 Listpack | 统一使用 Listpack 替代 ZipList | 7.0 |
| Redis Stack | 模块化集成（搜索/JSON/时序/图） | 7.2 |

---

## 二、Redis Functions（取代 EVAL）

### 为什么取代 EVAL 脚本？

```
EVAL 脚本的问题：
  1. 脚本存储在客户端，不是服务端 → 部署时需要每个客户端维护脚本
  2. 版本管理困难 → 脚本更新需要重新加载
  3. 调试困难 → 无法查看服务端有哪些脚本
  4. 只能用 Lua → 不够灵活

Redis Functions 的优势：
  1. 作为库注册在服务端 → 函数持久化到 RDB/AOF
  2. 支持版本管理 → FUNCTION LIST / FUNCTION DELETE
  3. 内置调试 → 通过 Redis 日志查看
  4. 后续支持多语言（目前仍为 Lua）
```

### Functions 基本用法

```lua
-- mylib.lua
redis.register_function {
    function_name = 'deduct_stock',
    callback = function(keys, args)
        local stock_key = keys[1]
        local order_id = args[1]
        local quantity = tonumber(args[2])

        local stock = tonumber(redis.call('GET', stock_key) or '0')
        if stock < quantity then
            return {err = 'INSUFFICIENT_STOCK'}
        end

        redis.call('DECRBY', stock_key, quantity)
        redis.call('HSET', 'order:' .. order_id, 'status', 'stock_deducted')
        return {ok = 'SUCCESS', remaining = stock - quantity}
    end
}

redis.register_function {
    function_name = 'batch_get',
    callback = function(keys, args)
        local results = {}
        for i = 1, #keys do
            results[i] = redis.call('GET', keys[i])
        end
        return results
    end
}
```

```bash
# 注册函数库
redis-cli FUNCTION LOAD "#!lua name=mylib\n$(cat mylib.lua)"

# 调用函数
redis-cli FCALL deduct_stock 1 product:1001 order_001 5

# 查看已注册函数
redis-cli FUNCTION LIST

# 删除函数库
redis-cli FUNCTION DELETE mylib
```

### Functions vs EVAL 对比

| 特性 | EVAL | Functions |
|------|------|-----------|
| 存储位置 | 客户端 | 服务端（RDB/AOF 持久化） |
| 版本管理 | 无 | 库级别管理 |
| 调试 | 困难 | 日志 + 列表查看 |
| 传播 | 整个脚本 | 二进制表示（更高效） |
| 复制 | 传播脚本文本 | 传播效果（effects） |
| 适用场景 | 简单一次性脚本 | 长期使用的业务逻辑 |

---

## 三、Sharded Pub/Sub

### 解决什么问题？

```
传统 Pub/Sub 的问题：
  消息广播到 Cluster 中所有节点
  → 如果只有少量消费者订阅，大量消息被浪费
  → 在大规模集群中造成"广播风暴"

Sharded Pub/Sub：
  消息只发送到 key 所在的分片节点
  → 减少了不必要的消息传播
  → 适合大规模集群中的定向消息

# 传统 Pub/Sub（广播所有节点）
PUBLISH channel:orders "new_order_123"

# Sharded Pub/Sub（只发到 channel hash 所在分片）
SSUBSCRIBE shard_channel:orders
SPUBLISH shard_channel:orders "new_order_123"
```

---

## 四、ACL v2 细粒度权限

```bash
# Redis 7 ACL 增强：支持对 Key 选择器的权限控制

# 用户只能访问 order: 前缀的 key
ACL SETUSER app_user on +@all ~order:* -@dangerous

# 按命令分类授权
ACL SETUSER readonly on +@read +@connection ~*

# Key 选择器支持模式
ACL SETUSER cache_user on +@all ~cache:* ~session:* -@admin

# Channel 权限（Pub/Sub）
ACL SETUSER pub_user on +@all &order_events:* &user_events:*

# 多种权限组合
ACL SETUSER dev_user on +@all ~dev:* -DEBUG -CONFIG -SHUTDOWN

# 查看用户权限
ACL LIST
ACL WHOAMI
ACL GETUSER app_user
```

---

## 五、Multi-part AOF

```
传统 AOF 问题：
  - AOF 重写时需要 fork 子进程，大数据量时耗时较长
  - 重写期间大量增量数据需要写入缓冲区
  - AOF 文件过大，加载慢

Redis 7 Multi-part AOF：
  ┌─────────────────────────────────────────────┐
  │ AOF 目录结构：                               │
  │   appendonlydir/                             │
  │     appendonly.aof.1.base.rdb    # 基础文件(RDB格式) │
  │     appendonly.aof.1.incr.aof   # 增量文件(AOF格式) │
  │     appendonly.aof.manifest      # 清单文件         │
  │                                              │
  │ 重写流程：                                    │
  │   1. 生成新的 base 文件（RDB 快照）           │
  │   2. 生成新的 incr 文件                       │
  │   3. 更新 manifest 清单                      │
  │   4. 后台异步删除旧文件                       │
  └─────────────────────────────────────────────┘

优势：
  - 重写更快（RDB 快照 + 增量 AOF）
  - 加载更安全（manifest 保证一致性）
  - 可组合多个增量文件
```

---

## 六、Client Eviction（客户端驱逐）

```bash
# 当客户端连接数超过 maxclients 时自动断开最空闲的客户端
# Redis 7 新增：不再直接拒绝连接，而是断开空闲客户端

CONFIG SET maxclients 10000
CONFIG SET maxmemory-clients 512mb  # 限制客户端总内存

# 查看客户端内存使用
CLIENT INFO
CLIENT LIST
```

---

## 七、Redis Stack

```
Redis Stack = Redis 7 + 四大模块：

┌─────────────────────────────────────────────┐
│ Redis Stack                                  │
│  ├── RedisSearch    → 全文搜索（替代 ES 轻量）│
│  ├── RedisJSON      → 原生 JSON 支持          │
│  ├── RedisTimeSeries → 时序数据               │
│  └── RedisGraph     → 图数据库（7.2 后逐步移除）│
└─────────────────────────────────────────────┘

# RedisJSON 示例
JSON.SET user:1001 $ '{"name":"Alice","age":30}'
JSON.GET user:1001 $.name
JSON.SET user:1001 $.age 31

# RedisSearch 示例
FT.CREATE products ON JSON PREFIX 1 product: SCHEMA $.name TEXT $.price NUMERIC
FT.SEARCH products "@name:Java"
```

---

## 八、面试高频题

**Q1: Redis 7 的 Functions 和 EVAL 脚本有什么区别？**
> 核心区别：① 存储位置：EVAL 脚本在客户端，Functions 在服务端（持久化到 RDB/AOF）；② 版本管理：Functions 支持库级别管理（FUNCTION LIST/DELETE），EVAL 没有；③ 传播方式：EVAL 传播整个脚本文本，Functions 传播二进制效果，更高效；④ 复制一致性：Functions 在主从复制中传播效果而非脚本，避免 Lua 随机性问题。推荐新项目使用 Functions。

**Q2: Sharded Pub/Sub 解决了什么问题？**
> 传统 Pub/Sub 将消息广播到 Cluster 中所有节点，大规模集群中大量消息被浪费，造成"广播风暴"。Sharded Pub/Sub 基于 Channel 名的 hash slot 路由，消息只发送到 Channel 所在的分片节点，减少了不必要的网络开销。使用 `SSUBSCRIBE`/`SPUBLISH` 命令。适合需要定向消息传递的场景。

**Q3: Redis 7 的 Multi-part AOF 有什么优势？**
> 传统 AOF 是单个文件，重写时 fork + 写入新文件，大数据量时耗时较长。Multi-part AOF 将 AOF 拆分为 manifest 清单 + base 文件（RDB 格式快照）+ incr 文件（增量 AOF）。重写只需生成新的 base + incr，更新 manifest 即可，旧文件后台异步删除。优势：重写更快、加载更安全、增量可合并。
