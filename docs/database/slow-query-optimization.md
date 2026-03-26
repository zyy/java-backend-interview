---
layout: default
title: MySQL 慢查询优化与性能调优
---

# MySQL 慢查询优化与性能调优

> 慢查询是生产环境最常见的问题，优化能力是高级开发的必备技能

## 🎯 面试重点

- 慢查询的排查与分析方法
- EXPLAIN 执行计划解读
- 索引优化策略
- SQL 改写技巧
- 参数调优

---

## 📖 一、慢查询排查

### 1.1 开启慢查询日志

```sql
-- 查看当前配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 开启慢查询日志（临时）
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 超过 1 秒视为慢查询
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 永久配置（my.cnf）
[mysqld]
slow_query_log = 1
long_query_time = 1
slow_query_log_file = /var/log/mysql/slow.log
log_queries_not_using_indexes = 1  -- 记录未使用索引的查询
```

### 1.2 分析慢查询日志

**mysqldumpslow 工具**：
```bash
# 查看最慢的 10 条 SQL
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

# 查看访问次数最多的 SQL
mysqldumpslow -s c -t 10 /var/log/mysql/slow.log
```

**pt-query-digest 工具（Percona）**：
```bash
# 详细分析报告
pt-query-digest /var/log/mysql/slow.log > slow_report.txt

# 分析结果包含：
# - 查询频率
# - 执行时间分布
# - 锁等待时间
# - 建议优化方案
```

### 1.3 实时慢查询监控

```sql
-- 查看正在执行的慢查询
SELECT * FROM information_schema.PROCESSLIST 
WHERE TIME > 10 AND COMMAND != 'Sleep';

-- 查看 InnoDB 事务状态
SELECT * FROM information_schema.INNODB_TRX;

-- 查看锁等待
SELECT * FROM information_schema.INNODB_LOCK_WAITS;
```

---

## 📖 二、EXPLAIN 执行计划

### 2.1 EXPLAIN 关键字段

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 100 AND status = 1;
```

| 字段 | 含义 | 优化建议 |
|-----|------|---------|
| **id** | 执行顺序 | id 相同从上往下，id 越大越先执行 |
| **select_type** | 查询类型 | SIMPLE（简单）、PRIMARY（最外层）、SUBQUERY（子查询） |
| **table** | 访问的表 | 注意派生表（derived） |
| **type** | 访问类型 | **system > const > eq_ref > ref > range > index > ALL** |
| **possible_keys** | 可能使用的索引 | 为 NULL 说明没有可用索引 |
| **key** | 实际使用的索引 | 为 NULL 说明全表扫描 |
| **rows** | 扫描行数 | 越小越好 |
| **Extra** | 额外信息 | Using index（覆盖索引）、Using where、Using filesort（需要排序优化） |

### 2.2 type 访问类型详解

```
system  >  const  >  eq_ref  >  ref  >  fulltext  >  ref_or_null  >  
index_merge  >  unique_subquery  >  index_subquery  >  range  >  
index  >  ALL

（从左到右，性能越来越差）
```

| 类型 | 说明 | 示例 |
|-----|------|------|
| **const** | 主键或唯一索引等值查询 | `WHERE id = 1` |
| **eq_ref** | 联表查询，主键或唯一索引关联 | `JOIN ON a.id = b.user_id`（b 表有主键） |
| **ref** | 非唯一索引等值查询 | `WHERE user_id = 100`（user_id 是普通索引） |
| **range** | 索引范围查询 | `WHERE id BETWEEN 1 AND 100` |
| **index** | 全索引扫描 | `SELECT id FROM table`（id 是索引） |
| **ALL** | 全表扫描 | 无索引或索引未命中 |

### 2.3 Extra 字段解读

| 值 | 含义 | 优化建议 |
|---|------|---------|
| **Using index** | 覆盖索引，无需回表 | 好现象，保持 |
| **Using where** | 使用 WHERE 过滤 | 正常 |
| **Using filesort** | 需要额外排序 | 添加索引或优化 ORDER BY |
| **Using temporary** | 需要临时表 | 优化 GROUP BY 或 DISTINCT |
| **Using join buffer** | 使用连接缓存 | 小表驱动大表 |
| **Impossible WHERE** | WHERE 条件永远为 false | 检查业务逻辑 |

---

## 📖 三、SQL 优化实战

### 3.1 索引优化

**案例 1：最左前缀原则**
```sql
-- 索引：INDEX idx_name_age (name, age)

-- ✅ 使用索引
SELECT * FROM users WHERE name = '张三';
SELECT * FROM users WHERE name = '张三' AND age = 20;

-- ❌ 不使用索引（跳过 name）
SELECT * FROM users WHERE age = 20;

-- ✅ 使用索引（MySQL 5.6+ ICP 优化）
SELECT * FROM users WHERE name LIKE '张%' AND age = 20;
```

**案例 2：覆盖索引**
```sql
-- 索引：INDEX idx_user_status (user_id, status)

-- ✅ 覆盖索引，无需回表
SELECT user_id, status FROM orders WHERE user_id = 100;

-- ❌ 需要回表（查询了不在索引中的字段）
SELECT * FROM orders WHERE user_id = 100;
```

**案例 3：索引下推（ICP）**
```sql
-- MySQL 5.6+ 特性
-- 索引：INDEX idx_name_age (name, age)

-- 即使 name 是范围查询，age 也能使用索引过滤
SELECT * FROM users WHERE name LIKE '张%' AND age = 20;
-- 原理：在存储引擎层就过滤 age，减少回表次数
```

### 3.2 SQL 改写技巧

**技巧 1：避免 SELECT ***
```sql
-- ❌ 需要回表，增加 IO
SELECT * FROM orders WHERE user_id = 100;

-- ✅ 覆盖索引，性能更好
SELECT order_id, amount, status FROM orders WHERE user_id = 100;
```

**技巧 2：大分页优化**
```sql
-- ❌ 深度分页，越往后越慢
SELECT * FROM orders ORDER BY id LIMIT 1000000, 10;
-- 需要扫描 1000010 行，丢弃前 1000000 行

-- ✅ 延迟关联
SELECT * FROM orders o
JOIN (SELECT id FROM orders ORDER BY id LIMIT 1000000, 10) tmp
ON o.id = tmp.id;

-- ✅ 基于游标（推荐）
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 10;
```

**技巧 3：OR 改 UNION**
```sql
-- ❌ OR 条件可能导致索引失效
SELECT * FROM orders WHERE user_id = 100 OR status = 1;

-- ✅ 拆分为 UNION
SELECT * FROM orders WHERE user_id = 100
UNION ALL
SELECT * FROM orders WHERE status = 1;
```

**技巧 4：批量插入替代单条**
```sql
-- ❌ 循环单条插入，每次网络往返
for (Order order : orders) {
    insert(order);  -- 1000 次网络往返
}

-- ✅ 批量插入，一次网络往返
INSERT INTO orders (user_id, amount) VALUES 
(1, 100), (2, 200), (3, 300), ...;
```

**技巧 5：避免隐式转换**
```sql
-- 表结构：user_id VARCHAR(20)

-- ❌ 隐式转换，索引失效
SELECT * FROM orders WHERE user_id = 100;  -- 100 是数字

-- ✅ 类型一致
SELECT * FROM orders WHERE user_id = '100';
```

### 3.3 JOIN 优化

**小表驱动大表**：
```sql
-- 假设 users 表 1 万条，orders 表 1000 万条

-- ✅ 小表（users）驱动大表（orders）
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 1;

-- 优化器通常会自动选择，但复杂 SQL 建议明确指定
```

**避免笛卡尔积**：
```sql
-- ❌ 忘记 ON 条件，产生笛卡尔积
SELECT * FROM users u JOIN orders o;

-- ✅ 明确关联条件
SELECT * FROM users u JOIN orders o ON u.id = o.user_id;
```

---

## 📖 四、参数调优

### 4.1 内存参数

```ini
[mysqld]
# InnoDB 缓冲池（最重要，通常设置为物理内存的 50-70%）
innodb_buffer_pool_size = 4G

# 缓冲池实例数（高并发时增加，减少锁竞争）
innodb_buffer_pool_instances = 4

# 连接缓冲区
join_buffer_size = 256K
sort_buffer_size = 256K
read_buffer_size = 128K
read_rnd_buffer_size = 256K
```

### 4.2 InnoDB 参数

```ini
# 日志文件大小（大一点减少 checkpoint 频率）
innodb_log_file_size = 512M
innodb_log_files_in_group = 2

# 刷新策略（性能 vs 安全权衡）
# 0：每秒刷新（性能最好，可能丢 1 秒数据）
# 1：每次提交刷新（最安全，默认）
# 2：每次提交写入 OS 缓存（折中）
innodb_flush_log_at_trx_commit = 2

# 刷新方式
# O_DIRECT：绕过 OS 缓存，减少双重缓冲
innodb_flush_method = O_DIRECT

# IO 线程数
innodb_read_io_threads = 4
innodb_write_io_threads = 4
```

### 4.3 连接参数

```ini
# 最大连接数
max_connections = 500

# 连接超时
wait_timeout = 600
interactive_timeout = 600

# 连接池建议（应用层）
# HikariCP: minimum-idle=10, maximum-pool-size=50
```

---

## 📖 五、面试真题

### Q1: 如何排查慢查询？

**答：** 排查慢查询的步骤：

1. **开启慢查询日志**：设置 `long_query_time = 1`，记录超过 1 秒的 SQL
2. **分析慢查询日志**：使用 `mysqldumpslow` 或 `pt-query-digest` 工具
3. **EXPLAIN 分析**：查看执行计划，关注 type、key、rows、Extra 字段
4. **查看执行频率**：某些 SQL 单次不快，但执行次数多，累计慢
5. **实时监控**：`SHOW PROCESSLIST` 查看正在执行的慢查询

### Q2: EXPLAIN 中 type 为 ALL 怎么办？

**答：** type = ALL 表示全表扫描，需要优化：

1. **添加索引**：为 WHERE 条件字段添加索引
2. **检查索引是否生效**：可能是隐式转换、函数操作导致索引失效
3. **优化 SQL**：避免 `SELECT *`，减少返回数据量
4. **分页优化**：深度分页使用延迟关联或游标方式
5. **考虑归档**：大表历史数据归档，减少扫描范围

### Q3: 大表分页查询如何优化？

**答：** 大表分页（LIMIT 1000000, 10）越往后越慢，优化方案：

1. **延迟关联**：先查 id，再关联详情
   ```sql
   SELECT * FROM orders o
   JOIN (SELECT id FROM orders ORDER BY id LIMIT 1000000, 10) tmp
   ON o.id = tmp.id;
   ```

2. **游标分页（推荐）**：基于上一页最后一条记录查询
   ```sql
   SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 10;
   ```

3. **搜索引擎**：使用 Elasticsearch 做分页查询

4. **业务优化**：限制最大分页数（如只能查看前 100 页）

### Q4: 如何优化 COUNT(*) 查询？

**答：** `COUNT(*)` 在大表上很慢，优化方案：

1. **近似值**：`SHOW TABLE STATUS` 或 `INFORMATION_SCHEMA` 快速估算
2. **缓存计数**：Redis 缓存总记录数，增删时更新
3. **汇总表**：定时任务维护计数表
4. **覆盖索引**：`COUNT(id)` 利用索引快速统计
5. **避免频繁 COUNT**：产品设计上减少实时统计需求

---

## 📚 延伸阅读

- [MySQL 性能优化官方文档](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
- [高性能 MySQL（书籍）](https://book.douban.com/subject/23008813/)
- [Percona Toolkit 文档](https://www.percona.com/doc/percona-toolkit/3.0/)
