---
layout: default
title: MySQL 日志系统详解（Binlog、Redo Log、Undo Log）
---

# MySQL 日志系统详解

> MySQL 的日志系统是保障数据一致性和持久性的核心，也是面试高频考点

## 🎯 面试重点

- Binlog、Redo Log、Undo Log 的作用与区别
- 两阶段提交（2PC）原理
- 崩溃恢复机制
- 日志刷盘策略与性能权衡

---

## 📖 一、三种日志对比

| 特性 | Binlog | Redo Log | Undo Log |
|-----|--------|----------|----------|
| **作用** | 数据恢复、主从复制 | 崩溃恢复（持久性） | 事务回滚、MVCC |
| **记录内容** | SQL 语句或行数据变更 | 物理页修改（页号+偏移量+新值） | 逻辑回滚操作（旧值） |
| **存储位置** | 磁盘文件（mysql-bin.xxx） | InnoDB 表空间（ib_logfile0/1） | InnoDB 表空间（ibdata1 或 undo 表空间） |
| **写入方式** | 追加写 | 循环写（固定大小） | 随事务产生，定期清理 |
| **归属** | Server 层 | InnoDB 存储引擎 | InnoDB 存储引擎 |

---

## 📖 二、Binlog（二进制日志）

### 2.1 作用

1. **数据恢复**：基于时间点恢复（PITR）
2. **主从复制**：Master 将 Binlog 发送给 Slave 进行同步
3. **审计**：记录所有数据变更操作

### 2.2 格式

```sql
-- 查看 Binlog 格式
SHOW VARIABLES LIKE 'binlog_format';

-- 修改格式（全局）
SET GLOBAL binlog_format = 'ROW';
```

| 格式 | 记录内容 | 优点 | 缺点 |
|-----|---------|------|------|
| **STATEMENT** | 原始 SQL 语句 | 日志小，性能好 | 某些语句主从不一致（如 UUID()、NOW()） |
| **ROW** | 行数据变更（前像+后像） | 精确复制，无歧义 | 日志大（批量操作记录每行） |
| **MIXED** | 混合模式，自动选择 | 平衡 | 复杂 |

**推荐**：MySQL 5.7+ 使用 **ROW** 格式

### 2.3 查看 Binlog

```bash
# 查看 Binlog 文件列表
SHOW BINARY LOGS;

# 查看当前正在写入的 Binlog
SHOW MASTER STATUS;

# 使用 mysqlbinlog 工具解析
mysqlbinlog --base64-output=DECODE-ROWS -v mysql-bin.000001

# 查看特定时间段的 Binlog
mysqlbinlog --start-datetime="2024-01-01 00:00:00" \
            --stop-datetime="2024-01-01 12:00:00" \
            mysql-bin.000001
```

### 2.4 Binlog 写入机制

```
事务执行
   │
   ▼
Binlog Cache（内存）
   │
   ├── 事务提交时，一次性写入 Binlog File
   │
   ▼
FSYNC 到磁盘（由 sync_binlog 控制）
```

**sync_binlog 参数**：
```sql
-- 查看配置
SHOW VARIABLES LIKE 'sync_binlog';

-- 0：由 OS 决定何时刷盘（性能最好，可能丢数据）
-- 1：每次事务提交都刷盘（最安全，默认）
-- N：每 N 次事务刷盘一次（折中）
```

| 值 | 安全性 | 性能 | 说明 |
|---|-------|------|------|
| 0 | 低 | 高 | OS 控制刷盘，崩溃可能丢最后一个事务 |
| 1 | 高 | 低 | 每次事务刷盘，不丢数据 |
| 100 | 中 | 中 | 每 100 个事务刷盘一次 |

---

## 📖 三、Redo Log（重做日志）

### 3.1 作用

**保障事务的持久性（Durability）**：
- 事务提交时，先写 Redo Log，再刷数据页
- 崩溃恢复时，用 Redo Log 重放未持久化的修改

**WAL（Write-Ahead Logging）机制**：
```
修改数据页之前，必须先写日志
即：先写日志，再写磁盘
```

### 3.2 为什么需要 Redo Log？

**直接刷数据页的问题**：
```
数据页大小：16KB
磁盘 IO：随机写，耗时约 10ms

如果每次事务提交都刷数据页：
- 性能极差（10ms/事务，仅 100 TPS）
- 随机 IO，磁盘寻道时间长
```

**Redo Log 的优势**：
```
Redo Log 大小：几十到几百字节
写入方式：顺序写，耗时约 1ms

事务提交时：
1. 写 Redo Log（顺序写，1ms）
2. 后台线程异步刷数据页

性能提升：10 倍以上
```

### 3.3 Redo Log 结构

```
ib_logfile0 / ib_logfile1（固定大小，循环写入）

┌─────────────────────────────────────────┐
│  Log Block 1  │  Log Block 2  │  ...    │
│  (512 bytes)  │  (512 bytes)  │         │
└─────────────────────────────────────────┘

每个 Log Block 包含：
- Block Header（12 bytes）
- Log Records（多个）
- Block Trailer（4 bytes）
```

**LSN（Log Sequence Number）**：
- 全局递增的日志序号
- 用于标记日志位置和检查点

### 3.4 Redo Log 写入流程

```
事务修改数据页
   │
   ▼
生成 Redo Log Record（物理日志）
   │
   ▼
写入 Redo Log Buffer（内存）
   │
   ├── 事务提交时，根据 innodb_flush_log_at_trx_commit 刷盘
   │
   ▼
Redo Log File（磁盘）
```

**innodb_flush_log_at_trx_commit 参数**：
```sql
-- 查看配置
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';

-- 0：每秒刷盘（性能最好，可能丢 1 秒数据）
-- 1：每次事务提交刷盘（最安全，默认）
-- 2：每次事务提交写入 OS 缓存（折中）
```

| 值 | 行为 | 安全性 | 性能 |
|---|------|-------|------|
| 0 | 每秒刷盘 | 低（崩溃丢 1 秒） | 最高 |
| 1 | 事务提交刷盘 | 高（不丢数据） | 最低 |
| 2 | 写 OS 缓存 | 中（OS 崩溃丢数据） | 中高 |

### 3.5 CheckPoint 机制

**作用**：标记哪些数据页已刷盘，减少崩溃恢复时间

```
LSN 1000 ──▶ 数据页已刷盘
LSN 1001-2000 ──▶ 数据页未刷盘（崩溃恢复时需要重放）

CheckPoint LSN = 1000
崩溃恢复时，只需重放 LSN > 1000 的日志
```

---

## 📖 四、Undo Log（回滚日志）

### 4.1 作用

1. **事务回滚**：记录数据修改前的状态，用于 ROLLBACK
2. **MVCC**：提供历史版本数据，实现非阻塞读

### 4.2 记录内容

**逻辑日志**：记录反向操作
```sql
-- 执行 INSERT
INSERT INTO users VALUES (1, 'Alice');
-- Undo Log 记录：DELETE FROM users WHERE id = 1;

-- 执行 UPDATE
UPDATE users SET name = 'Bob' WHERE id = 1;
-- Undo Log 记录：UPDATE users SET name = 'Alice' WHERE id = 1;

-- 执行 DELETE
DELETE FROM users WHERE id = 1;
-- Undo Log 记录：INSERT INTO users VALUES (1, 'Bob');
```

### 4.3 Undo Log 与 MVCC

**Read View 构建**：
```
事务 A（未提交）
  UPDATE users SET balance = 900 WHERE id = 1;  -- 原值 1000

事务 B（查询）
  SELECT balance FROM users WHERE id = 1;
  -- 通过 Undo Log 找到历史版本 1000，实现非阻塞读
```

**Undo Log 链**：
```
当前行数据（最新）
   │
   ├── Undo Pointer ──▶ 上一版本（事务 A 修改前）
   │                      │
   │                      ├── Undo Pointer ──▶ 上一版本（事务 B 修改前）
   │                      │                      │
   │                      │                      └── ...
```

### 4.4 Undo Log 清理

**Purge 线程**：
- 事务提交后，Undo Log 不能立即删除（可能有其他事务需要读取历史版本）
- Purge 线程定期清理不再需要的 Undo Log

**问题**：长事务导致 Undo Log 堆积
```sql
-- 查看长事务
SELECT * FROM information_schema.INNODB_TRX 
WHERE TIME_TO_SEC(timediff(now(),trx_started)) > 60;

-- 查看 Undo 表空间大小
SELECT table_name, (data_length + index_length) / 1024 / 1024 AS size_mb
FROM information_schema.tables 
WHERE table_name LIKE '%undo%';
```

---

## 📖 五、两阶段提交（2PC）

### 5.1 为什么需要两阶段提交？

**问题**：Binlog 和 Redo Log 是两个独立的日志，如何保证一致性？

```
场景：事务提交时，先写 Redo Log，再写 Binlog

1. 写 Redo Log 成功
2. 写 Binlog 失败（崩溃）
3. 崩溃恢复：Redo Log 重放，数据恢复
4. 但 Binlog 缺失，主从复制时 Slave 缺少这条数据

结果：主从数据不一致！
```

### 5.2 两阶段提交流程

```
        事务提交
           │
           ▼
    ┌─────────────┐
    │  Prepare 阶段 │
    │             │
    │ 1. 写 Redo Log（状态：PREPARE）│
    │ 2. 刷盘 Redo Log              │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  Commit 阶段  │
    │             │
    │ 3. 写 Binlog                │
    │ 4. 刷盘 Binlog              │
    │ 5. 写 Redo Log（状态：COMMIT）│
    └─────────────┘
           │
           ▼
        提交完成
```

### 5.3 崩溃恢复分析

**情况 1：Prepare 阶段崩溃**
```
Redo Log：PREPARE
Binlog：未写入

恢复：回滚事务（Redo Log 未标记 COMMIT，且 Binlog 不存在）
```

**情况 2：Commit 阶段崩溃（Binlog 已写入）**
```
Redo Log：PREPARE
Binlog：已写入

恢复：提交事务（Binlog 存在，需要保持主从一致）
```

**判断依据**：
```
崩溃恢复时，扫描最后一个 Binlog 文件：
- 如果 Redo Log 是 PREPARE，且 Binlog 中存在这条事务：提交
- 如果 Redo Log 是 PREPARE，且 Binlog 中不存在：回滚
```

---

## 📖 六、日志刷盘策略总结

### 6.1 性能与安全的权衡

| 参数 | 建议值 | 说明 |
|-----|-------|------|
| `innodb_flush_log_at_trx_commit` | 1（金融）/ 2（互联网） | Redo Log 刷盘策略 |
| `sync_binlog` | 1（金融）/ 100（互联网） | Binlog 刷盘策略 |

**金融级配置（数据安全第一）**：
```ini
[mysqld]
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
```

**互联网配置（性能优先）**：
```ini
[mysqld]
innodb_flush_log_at_trx_commit = 2
sync_binlog = 100
```

### 6.2 组提交（Group Commit）

**问题**：每次事务都刷盘，磁盘 IO 成为瓶颈

**优化**：多个事务合并为一次刷盘
```
事务 A ──┐
事务 B ──┼──▶ 合并刷盘（减少 IO 次数）
事务 C ──┘
```

**参数**：
```ini
binlog_group_commit_sync_delay = 100      # 延迟 100 微秒，等待更多事务
binlog_group_commit_sync_no_delay_count = 10  # 最多等待 10 个事务
```

---

## 📖 七、面试真题

### Q1: Binlog、Redo Log、Undo Log 的区别是什么？

**答：**

| 日志 | 作用 | 记录内容 | 归属 |
|-----|------|---------|------|
| **Binlog** | 数据恢复、主从复制 | SQL 语句或行数据变更 | Server 层 |
| **Redo Log** | 崩溃恢复（持久性） | 物理页修改（页号+偏移+新值） | InnoDB |
| **Undo Log** | 事务回滚、MVCC | 逻辑回滚操作（旧值） | InnoDB |

**协作关系**：
```
事务执行 ──▶ 修改数据页
   │
   ├── 生成 Undo Log（用于回滚和 MVCC）
   │
   ├── 生成 Redo Log（用于崩溃恢复）
   │
   └── 事务提交时，写 Binlog（用于主从复制）
```

### Q2: 为什么 Redo Log 比直接刷数据页快？

**答：**

1. **写入方式**：
   - 数据页：随机写（16KB），磁盘寻道时间长
   - Redo Log：顺序写（几十到几百字节），磁盘顺序写快

2. **写入量**：
   - 数据页：即使修改 1 个字节，也要刷 16KB 整页
   - Redo Log：只记录变更内容，体积小

3. **WAL 机制**：
   - 事务提交时，只需保证 Redo Log 刷盘
   - 数据页可以异步刷盘，由后台线程完成

**性能对比**：
```
直接刷数据页：约 10ms/次（100 TPS）
写 Redo Log：约 1ms/次（1000 TPS）
```

### Q3: 什么是两阶段提交？为什么需要它？

**答：**

**定义**：事务提交分为 Prepare 和 Commit 两个阶段：
1. **Prepare 阶段**：写 Redo Log（状态 PREPARE）并刷盘
2. **Commit 阶段**：写 Binlog 并刷盘，再更新 Redo Log 状态为 COMMIT

**目的**：保证 Binlog 和 Redo Log 的一致性，用于崩溃恢复。

**必要性**：
- Binlog 用于主从复制，Redo Log 用于崩溃恢复
- 如果两者不一致，会导致主从数据不一致
- 两阶段提交通过状态标记，确保崩溃后能判断事务是否需要提交

### Q4: innodb_flush_log_at_trx_commit = 0/1/2 的区别？

**答：**

| 值 | 行为 | 安全性 | 性能 | 适用场景 |
|---|------|-------|------|---------|
| 0 | 每秒刷盘 | 低（崩溃丢 1 秒） | 最高 | 非核心数据 |
| 1 | 事务提交刷盘 | 高（不丢数据） | 最低 | 金融级 |
| 2 | 写 OS 缓存 | 中（OS 崩溃丢） | 中高 | 互联网 |

**生产建议**：
- 金融系统：`= 1`
- 互联网应用：`= 2` 或 `= 0`（配合半同步复制）

### Q5: Undo Log 在 MVCC 中起什么作用？

**答：**

Undo Log 为 MVCC 提供历史版本数据：

1. **行版本链**：每行数据通过 Undo Pointer 链接多个历史版本
2. **Read View**：事务启动时创建一致性视图，通过 Undo Log 找到可见版本
3. **非阻塞读**：读取时不需要加锁，直接读取 Undo Log 中的历史版本

**示例**：
```
事务 A（未提交）：UPDATE balance = 900（原值 1000）
事务 B（查询）：SELECT balance
   │
   └── 看到 1000（从 Undo Log 读取历史版本）
```

---

## 📚 延伸阅读

- [MySQL 官方文档 - 日志](https://dev.mysql.com/doc/refman/8.0/en/server-logs.html)
- [InnoDB 事务日志](https://dev.mysql.com/doc/refman/8.0/en/innodb-redo-log.html)
- [MySQL 技术内幕：InnoDB 存储引擎](https://book.douban.com/subject/24708143/)
