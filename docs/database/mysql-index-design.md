---
layout: default
title: MySQL 索引设计规范与最佳实践
---
# MySQL 索引设计规范与最佳实践

## 🎯 面试题：联合索引的最左前缀原则是什么？什么情况下索引会失效？

> 索引设计是 MySQL 面试的核心考点，直接影响查询性能。

---

## 一、索引设计原则

```
1. 选择区分度高的列建索引
   区分度 = 不同值数量 / 总行数
   性别（区分度 0.5）→ 不适合建索引
   用户 ID（区分度 ≈ 1）→ 非常适合建索引

2. 频繁出现在 WHERE/ORDER BY/GROUP BY 的列
   WHERE user_id = ? → user_id 建索引
   ORDER BY created_at → created_at 建索引

3. 覆盖索引优先
   SELECT id, name FROM user WHERE age = 25
   → 建 (age, id, name) 联合索引，避免回表

4. 前缀索引（长字符串）
   ALTER TABLE user ADD INDEX idx_email(email(20));
   → 只索引前 20 个字符，节省空间

5. 不要过多索引
   每个索引都会增加写入开销（INSERT/UPDATE/DELETE 需要维护索引）
   一张表索引数量建议 ≤ 5 个
```

---

## 二、最左前缀匹配原则

```sql
-- 联合索引 (a, b, c)
-- 等价于建了三个索引：(a)、(a, b)、(a, b, c)

-- ✅ 能用到索引
WHERE a = 1                    -- 用到 (a)
WHERE a = 1 AND b = 2          -- 用到 (a, b)
WHERE a = 1 AND b = 2 AND c = 3 -- 用到 (a, b, c)
WHERE a = 1 AND c = 3          -- 用到 (a)，c 跳过了 b
WHERE a > 1 AND b = 2          -- 用到 (a)，范围查询后的列不走索引

-- ❌ 不能用到索引
WHERE b = 2                    -- 没有 a，不满足最左前缀
WHERE b = 2 AND c = 3          -- 没有 a，不满足最左前缀
WHERE c = 3                    -- 没有 a，不满足最左前缀

-- 特殊情况：MySQL 优化器会自动调整顺序
WHERE b = 2 AND a = 1          -- 等价于 WHERE a = 1 AND b = 2，能用到 (a, b)
```

### 联合索引列顺序设计

```sql
-- 原则：区分度高的列放前面，等值查询的列放前面，范围查询的列放后面

-- 场景：查询 status = 'active' AND age > 18 AND city = 'Beijing'
-- 区分度：city > age > status

-- ✅ 推荐：(city, status, age)
-- 等值查询 city 和 status 放前面，范围查询 age 放后面
CREATE INDEX idx_city_status_age ON user(city, status, age);

-- ❌ 不推荐：(age, city, status)
-- age 是范围查询，放前面会导致后面的列无法使用索引
```

---

## 三、索引失效场景

```sql
-- 1. 对索引列使用函数
-- ❌ 失效
SELECT * FROM user WHERE YEAR(created_at) = 2024;
-- ✅ 改写
SELECT * FROM user WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- 2. 隐式类型转换
-- ❌ 失效（phone 是 VARCHAR，传入 INT 会隐式转换）
SELECT * FROM user WHERE phone = 13800138000;
-- ✅ 正确
SELECT * FROM user WHERE phone = '13800138000';

-- 3. LIKE 前导通配符
-- ❌ 失效（前导 % 无法利用 B+ 树有序性）
SELECT * FROM user WHERE name LIKE '%张%';
-- ✅ 后缀通配符可以用索引
SELECT * FROM user WHERE name LIKE '张%';

-- 4. OR 连接非索引列
-- ❌ 失效（age 没有索引，导致整个 OR 不走索引）
SELECT * FROM user WHERE name = '张三' OR age = 25;
-- ✅ 改写为 UNION
SELECT * FROM user WHERE name = '张三'
UNION
SELECT * FROM user WHERE age = 25;

-- 5. NOT IN / NOT EXISTS
-- ❌ 通常不走索引
SELECT * FROM user WHERE id NOT IN (1, 2, 3);
-- ✅ 改写为 LEFT JOIN
SELECT u.* FROM user u LEFT JOIN exclude_ids e ON u.id = e.id WHERE e.id IS NULL;

-- 6. 不等于（!=、<>）
-- ❌ 通常不走索引（数据量大时）
SELECT * FROM user WHERE status != 'deleted';
-- ✅ 改写为范围查询
SELECT * FROM user WHERE status IN ('active', 'inactive');

-- 7. IS NULL / IS NOT NULL
-- 视情况而定，MySQL 8.0 对 IS NULL 有优化
SELECT * FROM user WHERE deleted_at IS NULL;  -- 可能走索引
```

---

## 四、覆盖索引

```sql
-- 覆盖索引：查询的所有列都在索引中，无需回表
-- EXPLAIN 中 Extra 显示 "Using index"

-- 场景：查询用户列表（只需要 id, name, age）
-- ❌ 回表查询
SELECT id, name, age FROM user WHERE age = 25;
-- 索引只有 (age)，需要回表查 name

-- ✅ 覆盖索引
CREATE INDEX idx_age_name ON user(age, name);
SELECT id, name, age FROM user WHERE age = 25;
-- 索引包含 age, name，id 是主键自动包含，无需回表

-- 覆盖索引的限制：
-- 1. 索引列不能太多（索引体积大）
-- 2. 不适合频繁更新的列（维护开销大）
-- 3. 适合读多写少的场景
```

---

## 五、索引下推（ICP）

```sql
-- 索引下推（Index Condition Pushdown）：MySQL 5.6+
-- 在存储引擎层过滤数据，减少回表次数

-- 联合索引 (name, age)
-- 查询：WHERE name LIKE '张%' AND age = 25

-- 没有 ICP：
-- 1. 存储引擎：找到所有 name LIKE '张%' 的记录（回表）
-- 2. Server 层：过滤 age = 25

-- 有 ICP：
-- 1. 存储引擎：找到 name LIKE '张%' 的记录，同时检查 age = 25
-- 2. 只有满足两个条件的记录才回表
-- → 减少了大量不必要的回表

-- EXPLAIN 中 Extra 显示 "Using index condition"
EXPLAIN SELECT * FROM user WHERE name LIKE '张%' AND age = 25;
```

---

## 六、EXPLAIN 分析

```sql
EXPLAIN SELECT * FROM user WHERE age = 25 AND city = 'Beijing';

-- 关键字段：
-- type：访问类型（从好到差）
--   system > const > eq_ref > ref > range > index > ALL
--   const：主键或唯一索引等值查询
--   ref：非唯一索引等值查询
--   range：范围查询
--   ALL：全表扫描（需要优化）

-- key：实际使用的索引
-- key_len：索引使用的字节数（越大说明用到的索引列越多）
-- rows：预估扫描行数（越小越好）
-- Extra：
--   Using index：覆盖索引（好）
--   Using where：Server 层过滤（中）
--   Using filesort：文件排序（需要优化）
--   Using temporary：临时表（需要优化）
--   Using index condition：索引下推（好）
```

---

## 七、面试高频题

**Q1: 联合索引的最左前缀原则是什么？**
> 联合索引 (a, b, c) 相当于建了 (a)、(a,b)、(a,b,c) 三个索引。查询时必须从最左列开始，不能跳过中间列。等值查询可以乱序（优化器会调整），但范围查询之后的列无法使用索引。设计原则：区分度高的列放前面，等值查询的列放前面，范围查询的列放后面。

**Q2: 什么情况下索引会失效？**
> 六种常见失效场景：① 对索引列使用函数（`YEAR(created_at)`）；② 隐式类型转换（字符串列传入数字）；③ LIKE 前导通配符（`LIKE '%张'`）；④ OR 连接非索引列；⑤ NOT IN / NOT EXISTS；⑥ 不等于（`!=`）。根本原因：这些操作破坏了 B+ 树的有序性，无法利用索引的二分查找特性。

**Q3: 什么是覆盖索引？有什么好处？**
> 覆盖索引是指查询的所有列都包含在索引中，无需回表查询主键索引。好处：① 减少 IO（不需要回表）；② 减少随机 IO（索引是顺序存储）；③ EXPLAIN 中 Extra 显示 "Using index"。设计时可以将高频查询的列加入联合索引，实现覆盖索引。注意：索引列不能太多，否则索引体积大，维护开销高。
