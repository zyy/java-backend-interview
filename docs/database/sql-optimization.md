---
layout: default
title: SQL 优化技巧
---
# SQL 优化技巧

> 写出高性能的 SQL 是后端工程师的核心能力

## 🎯 面试重点

- SQL 执行计划解读
- 索引优化策略
- 查询优化技巧
- 分页查询优化

## 📖 SQL 执行计划

### EXPLAIN 命令详解

```sql
-- 查看 SQL 执行计划
EXPLAIN SELECT * FROM users WHERE age > 20 AND name LIKE '张%';

-- EXPLAIN 结果字段说明
/**
 * | id | select_type | table | partitions | type | possible_keys | key | key_len | ref | rows | filtered | Extra |
 * |----|-------------|-------|------------|------|---------------|-----|---------|-----|------|----------|-------|
 * 
 * 重要字段：
 * - type: 访问类型（ALL、index、range、ref、eq_ref、const）
 * - key: 实际使用的索引
 * - rows: 预估扫描行数
 * - Extra: 额外信息（Using where、Using index、Using filesort）
 */
```

### 访问类型（type）详解

```java
/**
 * MySQL 访问类型（性能从好到坏）
 */
public class AccessType {
    
    // const：主键或唯一索引等值查询
    /*
     * EXPLAIN SELECT * FROM user WHERE id = 1;
     * type: const, rows: 1
     */
    
    // eq_ref：关联查询，主键/唯一索引关联
    /*
     * EXPLAIN SELECT * FROM user JOIN order ON user.id = order.user_id;
     * type: eq_ref, rows: 1
     */
    
    // ref：非唯一索引等值查询
    /*
     * EXPLAIN SELECT * FROM user WHERE phone = '13800138000';
     * type: ref, rows: 1
     */
    
    // range：索引范围查询
    /*
     * EXPLAIN SELECT * FROM user WHERE age BETWEEN 20 AND 30;
     * type: range, rows: 1000
     */
    
    // index：全索引扫描
    /*
     * EXPLAIN SELECT id FROM user;
     * type: index, rows: 10000
     */
    
    // ALL：全表扫描（需要优化）
    /*
     * EXPLAIN SELECT * FROM user WHERE email LIKE '%@gmail.com';
     * type: ALL, rows: 10000
     */
}
```

## 📖 索引优化策略

### 1. 最左前缀原则

```sql
-- 创建复合索引
CREATE INDEX idx_name_age_city ON users(name, age, city);

-- 能使用索引的查询
SELECT * FROM users WHERE name = '张三';                    -- ✅ 使用索引
SELECT * FROM users WHERE name = '张三' AND age = 25;       -- ✅ 使用索引
SELECT * FROM users WHERE name = '张三' AND age = 25 AND city = '北京'; -- ✅ 使用索引
SELECT * FROM users WHERE age = 25 AND city = '北京';       -- ❌ 不能使用索引（缺少name）
SELECT * FROM users WHERE name = '张三' AND city = '北京';  -- ✅ 使用索引（但只用name部分）
```

### 2. 覆盖索引优化

```sql
-- 普通查询（需要回表）
SELECT * FROM users WHERE age > 20;  -- ❌ 需要回表

-- 覆盖索引查询（不需要回表）
SELECT id, age FROM users WHERE age > 20;  -- ✅ 覆盖索引
SELECT COUNT(*) FROM users WHERE age > 20; -- ✅ 覆盖索引

-- 创建覆盖索引
CREATE INDEX idx_age_name ON users(age, name);
SELECT name, age FROM users WHERE age > 20;  -- ✅ 覆盖索引
```

### 3. 索引下推（ICP）

```sql
-- MySQL 5.6+ 支持索引下推
-- 查询：SELECT * FROM users WHERE name LIKE '张%' AND age > 20;

-- 无 ICP：存储引擎返回所有 name LIKE '张%' 的记录，Server 层过滤 age > 20
-- 有 ICP：存储引擎同时过滤 name LIKE '张%' AND age > 20，减少回表次数

-- 查看 ICP 状态
SHOW VARIABLES LIKE 'optimizer_switch';
-- 开启 ICP（默认开启）
SET optimizer_switch = 'index_condition_pushdown=on';
```

## 📖 查询优化技巧

### 1. 避免 SELECT *

```sql
-- 不推荐
SELECT * FROM users WHERE age > 20;

-- 推荐：只查询需要的字段
SELECT id, name, age FROM users WHERE age > 20;
```

### 2. 避免在 WHERE 子句中对字段进行运算或函数操作

```sql
-- 不推荐
SELECT * FROM users WHERE YEAR(create_time) = 2023;
SELECT * FROM users WHERE age + 1 > 20;

-- 推荐
SELECT * FROM users WHERE create_time >= '2023-01-01' AND create_time < '2024-01-01';
SELECT * FROM users WHERE age > 19;
```

### 3. 使用 EXISTS 替代 IN

```sql
-- IN 子查询（可能性能差）
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);

-- EXISTS（通常性能更好）
SELECT * FROM users u WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 1000
);
```

### 4. 分页查询优化

```sql
-- 传统分页（大数据量时性能差）
SELECT * FROM users ORDER BY id LIMIT 1000000, 20;  -- 扫描 1000020 行

-- 优化方案1：使用覆盖索引
SELECT id FROM users ORDER BY id LIMIT 1000000, 20;  -- 只扫描索引
-- 再根据 id 查询详情
SELECT * FROM users WHERE id IN (/* 上一步的 id 列表 */);

-- 优化方案2：使用游标分页
SELECT * FROM users WHERE id > 1000000 ORDER BY id LIMIT 20;  -- 需要记住上一页最后 id

-- 优化方案3：延迟关联
SELECT * FROM users u 
JOIN (SELECT id FROM users ORDER BY id LIMIT 1000000, 20) tmp 
ON u.id = tmp.id;
```

### 5. JOIN 优化

```sql
-- 小表驱动大表
-- users: 10000行，orders: 1000000行

-- 不推荐：大表驱动小表
SELECT * FROM orders o JOIN users u ON o.user_id = u.id;

-- 推荐：小表驱动大表
SELECT * FROM users u JOIN orders o ON u.id = o.user_id;

-- 确保关联字段有索引
CREATE INDEX idx_user_id ON orders(user_id);
```

## 📖 数据批量操作优化

### 批量插入

```sql
-- 不推荐：多次单条插入
INSERT INTO users(name, age) VALUES ('张三', 25);
INSERT INTO users(name, age) VALUES ('李四', 30);
INSERT INTO users(name, age) VALUES ('王五', 28);

-- 推荐：批量插入
INSERT INTO users(name, age) VALUES 
('张三', 25),
('李四', 30), 
('王五', 28);
```

### 批量更新

```sql
-- 使用 CASE WHEN 批量更新
UPDATE users SET 
    score = CASE id
        WHEN 1 THEN 100
        WHEN 2 THEN 95
        WHEN 3 THEN 90
    END,
    level = CASE id
        WHEN 1 THEN 'A'
        WHEN 2 THEN 'B'
        WHEN 3 THEN 'C'
    END
WHERE id IN (1, 2, 3);
```

## 📖 数据库设计优化

### 1. 字段类型选择

```sql
-- 选择合适的数据类型
-- 不推荐：VARCHAR(255) 存储 IP 地址
-- 推荐：INT UNSIGNED（使用 INET_ATON 转换）
CREATE TABLE logs (
    ip INT UNSIGNED,
    -- 查询：WHERE ip = INET_ATON('192.168.1.1')
);

-- 不推荐：TEXT 存储短字符串
-- 推荐：VARCHAR 够用时不用 TEXT
```

### 2. 规范化与反规范化

```sql
-- 规范化（减少冗余）
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE departments (
    id INT PRIMARY KEY,
    name VARCHAR(50)
);

-- 反规范化（提高查询性能）
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    dept_id INT,
    dept_name VARCHAR(50)  -- 冗余字段，避免 JOIN
);
```

## 📖 面试真题

### Q1: 如何分析 SQL 性能？

**答：**
1. 使用 `EXPLAIN` 查看执行计划
2. 关注 `type`（访问类型），避免 ALL 全表扫描
3. 关注 `key`（使用索引），确保使用合适索引
4. 关注 `rows`（扫描行数），越少越好
5. 关注 `Extra`，避免 Using filesort、Using temporary

### Q2: 什么情况下索引会失效？

**答：**
1. 违反最左前缀原则
2. 对索引字段进行运算或函数操作
3. 使用 `!=`、`<>`、`NOT IN`、`NOT EXISTS`
4. 使用 `LIKE '%value'` 前导通配符
5. 类型转换（如字符串字段使用数字查询）
6. OR 条件未全部使用索引
7. 数据量少时，MySQL 可能选择全表扫描

### Q3: 如何优化大表的分页查询？

**答：**
1. **覆盖索引**：先查主键，再关联查详情
2. **游标分页**：使用 `WHERE id > last_id LIMIT n`
3. **延迟关联**：子查询查主键，外层关联查详情
4. **业务折中**：限制深度分页，或使用搜索引擎

### Q4: COUNT(*) 和 COUNT(1) 哪个快？

**答：**
- 性能基本相同，MySQL 对两者优化相同
- `COUNT(*)` 是 SQL 标准写法
- `COUNT(column)` 会跳过 NULL 值，性能稍差
- `COUNT(*)` 推荐使用，语义清晰

### Q5: 数据库连接池如何配置？

**答：**
1. **初始连接数**：根据应用启动需求设置
2. **最大连接数**：根据服务器资源和并发量设置
3. **超时时间**：避免连接泄漏
4. **验证连接**：定期检查连接有效性
5. **监控统计**：监控连接池使用情况

## 📚 延伸阅读

- [MySQL 性能优化](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
- [高性能 MySQL](https://book.douban.com/subject/23008813/)
- [SQL 优化案例](https://github.com/zhisheng17/awesome-sql-optimization)

---

**⭐ 重点：SQL 优化是数据库性能的关键，必须掌握执行计划分析和索引优化技巧**