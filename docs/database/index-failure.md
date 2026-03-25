---
layout: default
title: MySQL 索引失效场景 ⭐⭐⭐
---
# MySQL 索引失效场景 ⭐⭐⭐

## 面试题：什么情况下索引会失效？

### 核心回答

索引失效是 MySQL 查询优化中的重要知识点，常见场景包括：违反最左前缀原则、使用函数/运算、隐式类型转换、LIKE 左边通配符等。

### 常见索引失效场景

| 序号 | 场景 | 是否失效 | 说明 |
|------|------|---------|------|
| 1 | 违反最左前缀原则 | ⚠️ 部分失效 | 联合索引必须从最左列开始 |
| 2 | LIKE %开头 | ⚠️ 失效 | "%abc" 导致全表扫描 |
| 3 | 使用 OR | ⚠️ 部分失效 | OR 两边都要有索引 |
| 4 | 对索引列运算 | ⚠️ 失效 | 使用函数或算术运算 |
| 5 | 隐式类型转换 | ⚠️ 失效 | 类型不匹配 |
| 6 | 负向查询 | ⚠️ 可能失效 | !=、NOT IN、IS NOT NULL |
| 7 | 使用 SELECT * | ⚠️ 可能失效 | 无法使用覆盖索引 |
| 8 | 数据量过小 | ⚠️ 不走索引 | 优化器选择全表扫描 |

### 场景详解

#### 1. 违反最左前缀原则

```sql
-- 创建联合索引
ALTER TABLE user ADD INDEX idx_name_age_city(name, age, city);

-- ✅ 有效：使用最左前缀
SELECT * FROM user WHERE name = '张三';
SELECT * FROM user WHERE name = '张三' AND age = 18;
SELECT * FROM user WHERE name = '张三' AND age = 18 AND city = '北京';

-- ⚠️ 部分有效：跳过中间列
SELECT * FROM user WHERE name = '张三' AND city = '北京';  -- 只用 name

-- ❌ 失效：违反最左前缀
SELECT * FROM user WHERE age = 18;
SELECT * FROM user WHERE age = 18 AND city = '北京';
SELECT * FROM user WHERE city = '北京';
```

**原理**：

```
索引 idx_name_age_city 的 B+ 树结构：

[name=张三, age=18, city=北京] → row1
[name=张三, age=20, city=上海] → row2
[name=李四, age=18, city=北京] → row3

查询 age=18 时：
- 无法快速定位，需要扫描整个索引
```

#### 2. LIKE 左边通配符

```sql
-- 创建索引
ALTER TABLE user ADD INDEX idx_name(name);

-- ✅ 有效：右侧通配符
SELECT * FROM user WHERE name LIKE '张%';    -- range 扫描
SELECT * FROM user WHERE name LIKE '张三%';  -- range 扫描

-- ❌ 失效：左侧通配符
SELECT * FROM user WHERE name LIKE '%三';    -- 全表扫描
SELECT * FROM user WHERE name LIKE '%张三';  -- 全表扫描

-- ❌ 失效：两侧通配符
SELECT * FROM user WHERE name LIKE '%张%';   -- 全表扫描
```

**原理**：

```
name 索引的 B+ 树按字典序排列：

张三 → row1
张四 → row2
李四 → row3

"张%"：可以定位到"张"开头的区间 → 使用索引
"%三"：无法定位区间 → 全表扫描
```

**优化方案**：

```sql
-- 方案1：使用覆盖索引
SELECT name FROM user WHERE name LIKE '%张%';  -- 使用索引

-- 方案2：使用全文索引
ALTER TABLE user ADD FULLTEXT INDEX idx_name_fulltext(name);
SELECT * FROM user WHERE MATCH(name) AGAINST('张三');

-- 方案3：使用 Elasticsearch
```

#### 3. OR 条件

```sql
-- 创建索引
ALTER TABLE user ADD INDEX idx_name(name);
ALTER TABLE user ADD INDEX idx_age(age);

-- ⚠️ 失效：一边有索引，一边没有
SELECT * FROM user WHERE name = '张三' OR age = 18;
-- age 没有索引，导致全表扫描

-- ✅ 有效：两边都有索引（MySQL 5.0+）
SELECT * FROM user WHERE name = '张三' OR age = 18;
-- 可以使用索引合并

-- ❌ 失效：两边都没有索引
SELECT * FROM user WHERE name = '张三' OR phone = '138';
```

**替代方案**：

```sql
-- 使用 UNION 替代 OR
SELECT * FROM user WHERE name = '张三'
UNION
SELECT * FROM user WHERE age = 18;

-- 使用 IN 替代 OR
SELECT * FROM user WHERE name IN ('张三', '李四');
```

#### 4. 对索引列使用函数或运算

```sql
-- 创建索引
ALTER TABLE user ADD INDEX idx_create_time(create_time);

-- ❌ 失效：使用函数
SELECT * FROM user WHERE YEAR(create_time) = 2024;
SELECT * FROM user WHERE DATE_FORMAT(create_time, '%Y') = '2024';
SELECT * FROM user WHERE DAYOFMONTH(create_time) = 15;

-- ❌ 失效：使用运算
SELECT * FROM user WHERE price * 1.1 > 100;
SELECT * FROM user WHERE id + 1 = 10;

-- ✅ 正确：使用范围查询
SELECT * FROM user WHERE create_time >= '2024-01-01' AND create_time < '2025-01-01';
SELECT * FROM user WHERE price > 100 / 1.1;
```

**原理**：

```
索引按原值排序：
create_time: 2024-01-01, 2024-02-01, 2024-03-01, ...

使用 YEAR(create_time) 时：
- 需要对每一行计算函数值
- 无法使用索引的有序性
```

#### 5. 隐式类型转换

```sql
-- phone 是 VARCHAR 类型
ALTER TABLE user ADD INDEX idx_phone(phone);

-- ⚠️ 失效：整数传给字符串列
SELECT * FROM user WHERE phone = 13800138000;
-- 隐式转换为：WHERE phone = '13800138000'

-- ✅ 正确：使用字符串
SELECT * FROM user WHERE phone = '13800138000';

-- age 是 INT 类型
-- ⚠️ 失效：字符串传给整数列
SELECT * FROM user WHERE age = '18';
-- 字符串转整数：WHERE age = 18
-- 可能导致全表扫描或索引失效
```

**原则**：确保查询参数类型与列类型一致

#### 6. 负向查询

```sql
-- 创建索引
ALTER TABLE user ADD INDEX idx_status(status);

-- ⚠️ 可能失效：负向查询
SELECT * FROM user WHERE status != 1;
SELECT * FROM user WHERE status <> 1;
SELECT * FROM user WHERE status NOT IN (1, 2);
SELECT * FROM user WHERE status IS NOT NULL;

-- ✅ 优化：使用正向查询
SELECT * FROM user WHERE status IN (2, 3, 4);
SELECT * FROM user WHERE status > 1;

-- 对于 IS NOT NULL
-- 如果列有默认值，MySQL 可能仍使用索引
-- 如果列大量为 NULL，可能全表扫描更好
```

**注意**：MySQL 优化器会根据数据分布决定是否使用索引

#### 7. 使用 SELECT *

```sql
-- 创建联合索引
ALTER TABLE user ADD INDEX idx_name_age(name, age);

-- ✅ 有效：使用覆盖索引
SELECT name, age FROM user WHERE name = '张三';
-- 索引包含所有需要的数据，无需回表

-- ⚠️ 失效：需要回表
SELECT * FROM user WHERE name = '张三';
-- 虽然能用 name 索引，但需要回表获取其他字段

-- ⚠️ 部分失效：索引列不在 WHERE 中
SELECT name, age FROM user WHERE age = 18;
-- 违反最左前缀，无法使用索引
```

#### 8. 数据量过小

```sql
-- 当数据量很小时，MySQL 优化器可能选择全表扫描
-- 因为索引需要额外的 IO 操作

-- 验证是否使用索引
EXPLAIN SELECT * FROM user WHERE name = '张三';

-- type = ALL 表示全表扫描
-- type = ref 或 range 表示使用索引
```

### 复杂场景分析

#### 场景1：多个条件组合

```sql
-- 创建联合索引
ALTER TABLE user ADD INDEX idx_a_b_c(a, b, c);

-- ❌ 完全失效
SELECT * FROM user WHERE b = 2;

-- ✅ 使用 a 列
SELECT * FROM user WHERE a = 1 AND b = 2;

-- ⚠️ 使用 a、b 列
SELECT * FROM user WHERE a = 1 AND c = 3;

-- ✅ 完全使用
SELECT * FROM user WHERE a = 1 AND b = 2 AND c = 3;

-- ✅ 使用 a 列，b 范围查询
SELECT * FROM user WHERE a = 1 AND b > 2 AND c = 3;
-- 使用 a, b，c 无法使用（b 是范围）
```

#### 场景2：索引列参与计算

```sql
-- 创建索引
ALTER TABLE orders ADD INDEX idx_amount(amount);

-- ❌ 失效
SELECT * FROM orders WHERE amount + 10 > 100;

-- ✅ 正确
SELECT * FROM orders WHERE amount > 90;

-- ❌ 失效
SELECT * FROM orders WHERE SUBSTRING(name, 1, 2) = '张';

-- ✅ 正确
SELECT * FROM orders WHERE name LIKE '张%';
```

#### 场景3：字符集不一致

```sql
-- 表使用 utf8mb4
-- 查询参数使用 latin1
SELECT * FROM user WHERE name = '张三';  -- 可能失效

-- 解决方案
SET NAMES utf8mb4;
SELECT * FROM user WHERE name = '张三';
```

### EXPLAIN 分析索引使用

```sql
-- 查看执行计划
EXPLAIN SELECT * FROM user WHERE name = '张三';

-- 关键字段
-- type: 查询类型（ALL=全表, ref=索引, range=范围）
-- key: 实际使用的索引
-- rows: 扫描行数
-- Extra: 额外信息（Using index=覆盖索引, Using where=条件过滤）
```

**type 值从好到差**：
```
system > const > eq_ref > ref > range > index > ALL
```

### 高频面试题

**Q1: 为什么 LIKE "%abc" 会导致索引失效？**

```
索引按值排序，如：张三、李四、王五

"张三%"：可以找到"张"开头的范围
"%三"：无法确定范围，必须逐个比较
```

**Q2: OR 一定失效吗？**

```
不一定：
1. MySQL 5.0+ 支持索引合并（Index Merge）
2. OR 两边都有索引时，可能使用索引合并
3. 如果优化器认为全表扫描更快，则不使用索引
```

**Q3: 为什么建议使用覆盖索引？**

```
减少回表操作：
1. 索引树包含所有需要的数据
2. 无需访问主表
3. 减少磁盘 IO
```

**Q4: 如何优化 LIKE "%abc%" 查询？**

```sql
-- 1. 使用覆盖索引
SELECT id, name FROM articles WHERE name LIKE '%MySQL%';

-- 2. 使用全文索引
ALTER TABLE articles ADD FULLTEXT INDEX idx_name(name);
SELECT * FROM articles WHERE MATCH(name) AGAINST('MySQL');

-- 3. 使用搜索引擎
-- Elasticsearch、MongoDB Atlas Search
```

### 最佳实践

```sql
-- 1. 创建合理的联合索引
ALTER TABLE orders ADD INDEX idx_user_status_time(user_id, status, create_time);

-- 2. 按需创建索引，考虑查询模式
-- 分析慢查询日志，找出高频查询

-- 3. 使用 EXPLAIN 验证索引
EXPLAIN SELECT * FROM orders WHERE user_id = 1 AND status = 1;

-- 4. 避免过多索引
-- 每个索引都会增加写操作开销

-- 5. 定期分析表
ANALYZE TABLE user;
OPTIMIZE TABLE user;
```

---

**参考链接：**
- [MySQL索引失效场景-CSDN](https://blog.csdn.net/sinat_28789467/article/details/116886992)
- [MySQL索引失效场景验证-知乎](https://zhuanlan.zhihu.com/p/372205724)
