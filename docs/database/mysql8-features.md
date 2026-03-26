---
layout: default
title: MySQL 8.0 新特性详解
---

# MySQL 8.0 新特性详解

> MySQL 8.0 是重大版本升级，带来了众多新特性，面试常考

## 🎯 面试重点

- 数据字典的改进（InnoDB 替代 MyISAM）
- 窗口函数（Window Functions）
- 公共表表达式（CTE）
- 降序索引与不可见索引
- JSON 增强功能
- 性能与安全性提升

---

## 📖 一、架构改进

### 1.1 数据字典（Data Dictionary）

**MySQL 5.7 及之前**：
- 元数据分散存储：`.frm`（表结构）、`.par`（分区）、`db.opt`（数据库属性）
- 使用 MyISAM 存储元数据，容易损坏，不支持事务

**MySQL 8.0**：
- 统一使用 InnoDB 存储数据字典
- 支持事务，DDL 操作原子性（原子 DDL）
- 元数据存储在 `mysql` 数据库的隐藏表中

**好处**：
- DDL 操作可以回滚（如 `CREATE TABLE` 失败自动清理）
- 元数据一致性更好，崩溃恢复更可靠
- 支持快速 DDL（如 `INSTANT ADD COLUMN`）

### 1.2 原子 DDL（Atomic DDL）

```sql
-- MySQL 8.0 中，DDL 操作是原子的
-- 如果执行过程中崩溃，会自动回滚或完成，不会留下半成品

CREATE TABLE t1 (id INT);  -- 成功或失败，不会创建半成品表

-- 对比 5.7：
-- 如果 CREATE TABLE 过程中崩溃，可能留下 .frm 文件但无表数据
```

---

## 📖 二、SQL 增强

### 2.1 窗口函数（Window Functions）

**定义**：对一组行进行计算，返回每个行的结果（不像 GROUP BY 合并行）。

**常用窗口函数**：

| 函数 | 作用 |
|-----|------|
| `ROW_NUMBER()` | 行号（不重复） |
| `RANK()` | 排名（有并列，跳号） |
| `DENSE_RANK()` | 密集排名（有并列，不跳号） |
| `LEAD(col, n)` | 获取后第 n 行的值 |
| `LAG(col, n)` | 获取前第 n 行的值 |
| `SUM/AVG/COUNT OVER` | 累计求和/平均/计数 |

**使用示例**：

```sql
-- 1. 分组排名（每个部门工资排名前 3）
SELECT 
    name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank_in_dept
FROM employees;

-- 结果：
-- name  | department | salary | rank_in_dept
-- Alice | Tech       | 30000  | 1
-- Bob   | Tech       | 25000  | 2
-- Carol | Sales      | 28000  | 1

-- 2. 累计求和（按月累计销售额）
SELECT 
    month,
    amount,
    SUM(amount) OVER (ORDER BY month) as cumulative_amount
FROM sales;

-- 3. 获取前/后一行（计算环比增长）
SELECT 
    month,
    amount,
    LAG(amount, 1) OVER (ORDER BY month) as prev_month_amount,
    (amount - LAG(amount, 1) OVER (ORDER BY month)) / LAG(amount, 1) OVER (ORDER BY month) as growth_rate
FROM sales;
```

**对比传统写法**：
```sql
-- 5.7 中实现分组排名（复杂且性能差）
SELECT e1.name, e1.department, e1.salary,
       (SELECT COUNT(*) + 1 
        FROM employees e2 
        WHERE e2.department = e1.department 
        AND e2.salary > e1.salary) as rank_in_dept
FROM employees e1;

-- 8.0 窗口函数简洁高效
SELECT name, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank_in_dept
FROM employees;
```

### 2.2 公共表表达式（CTE）

**定义**：临时结果集，可在 SELECT 中多次引用，支持递归。

**非递归 CTE**：
```sql
-- 定义 CTE
WITH high_salary_employees AS (
    SELECT * FROM employees WHERE salary > 20000
),
tech_employees AS (
    SELECT * FROM employees WHERE department = 'Tech'
)
-- 使用 CTE
SELECT * FROM high_salary_employees
UNION
SELECT * FROM tech_employees;
```

**递归 CTE（查询树形结构）**：
```sql
-- 查询组织架构（员工及其所有下属）
WITH RECURSIVE subordinates AS (
    -- 锚点成员：从指定员工开始
    SELECT id, name, manager_id, 0 as level
    FROM employees
    WHERE id = 1  -- 从 CEO 开始
    
    UNION ALL
    
    -- 递归成员：查询下属
    SELECT e.id, e.name, e.manager_id, s.level + 1
    FROM employees e
    JOIN subordinates s ON e.manager_id = s.id
)
SELECT * FROM subordinates;

-- 结果：
-- id | name  | manager_id | level
-- 1  | CEO   | NULL       | 0
-- 2  | VP1   | 1          | 1
-- 3  | VP2   | 1          | 1
-- 4  | Mgr1  | 2          | 2
```

### 2.3 降序索引与不可见索引

**降序索引**：
```sql
-- 8.0 支持显式降序索引
CREATE INDEX idx_name ON orders (created_at DESC, amount ASC);

-- 优化 ORDER BY ... DESC 查询
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
-- 可以直接使用降序索引，无需反向扫描
```

**不可见索引（Invisible Index）**：
```sql
-- 创建不可见索引（优化器默认不使用）
CREATE INDEX idx_test ON orders (user_id) INVISIBLE;

-- 测试索引效果（仅当前会话可见）
SET SESSION optimizer_switch = 'use_invisible_indexes=on';
EXPLAIN SELECT * FROM orders WHERE user_id = 100;

-- 确认有效后，设置为可见
ALTER TABLE orders ALTER INDEX idx_test VISIBLE;
```

**用途**：
- 安全地测试新索引效果
- 不影响生产查询性能

---

## 📖 三、JSON 增强

### 3.1 JSON 表函数

**JSON_TABLE**：将 JSON 数据转换为关系表
```sql
-- 假设有订单表，其中 items 字段是 JSON 数组
CREATE TABLE orders (
    id INT PRIMARY KEY,
    items JSON  -- [{"product": "A", "qty": 2}, {"product": "B", "qty": 1}]
);

-- 使用 JSON_TABLE 展开 JSON 数组
SELECT 
    o.id,
    jt.product,
    jt.qty
FROM orders o,
JSON_TABLE(
    o.items,
    '$[*]' COLUMNS (
        product VARCHAR(50) PATH '$.product',
        qty INT PATH '$.qty'
    )
) AS jt;

-- 结果：
-- id | product | qty
-- 1  | A       | 2
-- 1  | B       | 1
```

### 3.2 JSON 聚合函数

```sql
-- JSON_OBJECTAGG：将行数据聚合为 JSON 对象
SELECT 
    department,
    JSON_OBJECTAGG(name, salary) as salary_map
FROM employees
GROUP BY department;

-- 结果：
-- department | salary_map
-- Tech       | {"Alice": 30000, "Bob": 25000}
-- Sales      | {"Carol": 28000}

-- JSON_ARRAYAGG：将行数据聚合为 JSON 数组
SELECT 
    department,
    JSON_ARRAYAGG(name) as members
FROM employees
GROUP BY department;

-- 结果：
-- department | members
-- Tech       | ["Alice", "Bob"]
```

### 3.3 JSON 合并与补丁

```sql
-- JSON_MERGE_PATCH：合并 JSON，后面覆盖前面
SELECT JSON_MERGE_PATCH(
    '{"a": 1, "b": 2}',
    '{"b": 3, "c": 4}'
);
-- 结果：{"a": 1, "b": 3, "c": 4}

-- JSON_MERGE_PRESERVE：合并 JSON，保留所有值（数组形式）
SELECT JSON_MERGE_PRESERVE(
    '{"a": 1, "b": 2}',
    '{"b": 3, "c": 4}'
);
-- 结果：{"a": 1, "b": [2, 3], "c": 4}
```

---

## 📖 四、性能与安全

### 4.1 性能提升

| 特性 | 说明 |
|-----|------|
| **临时表优化** | 临时表默认使用 InnoDB，支持压缩 |
| **自增列持久化** | 自增值持久化到 redo log，重启不丢失 |
| **快速 DDL** | `INSTANT ADD COLUMN` 秒级完成（不拷贝数据） |
| **并行查询** | 支持并行扫描（8.0.14+） |

**快速 DDL 示例**：
```sql
-- 8.0 中，添加列是瞬间完成的（仅修改元数据）
ALTER TABLE orders ADD COLUMN remark VARCHAR(100), ALGORITHM=INSTANT;

-- 限制：只能添加到末尾，不能是主键，不能是自增列
```

### 4.2 安全性增强

**默认认证插件**：
```sql
-- 8.0 默认使用 caching_sha2_password（更安全）
-- 5.7 使用 mysql_native_password

-- 创建用户
CREATE USER 'app'@'%' IDENTIFIED WITH caching_sha2_password BY 'password';

-- 如果客户端不支持，可降级为 mysql_native_password
CREATE USER 'app'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
```

**角色（Role）**：
```sql
-- 创建角色
CREATE ROLE 'app_read', 'app_write';

-- 授予权限
GRANT SELECT ON database.* TO 'app_read';
GRANT SELECT, INSERT, UPDATE, DELETE ON database.* TO 'app_write';

-- 将角色授予用户
GRANT 'app_read' TO 'user1'@'%';
GRANT 'app_write' TO 'user2'@'%';

-- 用户激活角色
SET DEFAULT ROLE 'app_read' TO 'user1'@'%';
```

**密码管理**：
```sql
-- 密码历史（防止重复使用旧密码）
CREATE USER 'app'@'%' PASSWORD HISTORY 5;

-- 密码过期策略
CREATE USER 'app'@'%' PASSWORD EXPIRE INTERVAL 90 DAY;

-- 失败登录锁定
CREATE USER 'app'@'%' FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 3;
```

---

## 📖 五、面试真题

### Q1: MySQL 8.0 相比 5.7 有哪些重大改进？

**答：** MySQL 8.0 的重大改进包括：

1. **数据字典**：元数据统一使用 InnoDB 存储，支持原子 DDL
2. **窗口函数**：支持 `ROW_NUMBER()`、`RANK()`、`LEAD()`/`LAG()` 等
3. **CTE**：公共表表达式，支持递归查询树形结构
4. **JSON 增强**：`JSON_TABLE` 函数、聚合函数、合并补丁
5. **索引优化**：降序索引、不可见索引
6. **性能提升**：快速 DDL（`INSTANT ADD COLUMN`）、自增持久化
7. **安全性**：默认 `caching_sha2_password`、角色管理、密码策略

### Q2: 窗口函数和 GROUP BY 有什么区别？

**答：** 

| 特性 | GROUP BY | 窗口函数 |
|-----|----------|---------|
| 输出行数 | 合并为组 | 保持原行数 |
| 使用场景 | 聚合统计 | 排名、累计、前后行比较 |
| 示例 | `SUM(salary) GROUP BY dept` | `SUM(salary) OVER (PARTITION BY dept)` |

**窗口函数优势**：
- 可以在不减少行数的情况下进行分组计算
- 支持累计求和、移动平均等复杂分析
- 实现排名、同比环比等报表需求

### Q3: 什么是原子 DDL？有什么好处？

**答：** 原子 DDL 是指 DDL 操作（如 `CREATE`、`DROP`、`ALTER`）要么完全成功，要么完全失败，不会留下中间状态。

**好处**：
1. **数据一致性**：不会因为 DDL 中断导致元数据损坏
2. **自动清理**：DDL 失败时自动清理临时文件
3. **崩溃安全**：DDL 过程中崩溃，重启后自动回滚或完成

**示例**：
```sql
-- 8.0 中，以下操作是原子的
CREATE TABLE t1 (id INT);  -- 失败时不会留下半成品
DROP TABLE t1, t2;         -- 两张表要么都删除，要么都不删除
```

### Q4: 递归 CTE 有什么使用场景？

**答：** 递归 CTE 主要用于查询树形或层级结构数据：

1. **组织架构**：查询员工及其所有下属
2. **分类树**：查询商品分类及其所有子分类
3. **路径查询**：查询图中的最短路径
4. **账单层级**：查询多级分销的佣金关系

**示例**：查询员工的所有下属（包括间接下属）
```sql
WITH RECURSIVE subordinates AS (
    SELECT id, name, manager_id, 0 as level
    FROM employees WHERE id = 1  -- CEO
    UNION ALL
    SELECT e.id, e.name, e.manager_id, s.level + 1
    FROM employees e
    JOIN subordinates s ON e.manager_id = s.id
)
SELECT * FROM subordinates;
```

---

## 📚 延伸阅读

- [MySQL 8.0 官方文档](https://dev.mysql.com/doc/refman/8.0/en/)
- [MySQL 8.0 新特性白皮书](https://www.mysql.com/products/enterprise/database/)
- [高性能 MySQL 第4版](https://book.douban.com/subject/35167240/)
