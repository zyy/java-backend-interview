# 数据库优化实战

> 从慢查询到高性能：数据库优化全链路指南

## 🎯 面试重点

- 数据库性能分析与监控
- SQL优化与执行计划解读
- 索引设计与优化策略
- 分库分表实战方案

## 📖 性能监控体系

### 1. 数据库监控指标

```sql
-- 1. 连接数监控
SHOW STATUS LIKE 'Threads_connected';     -- 当前连接数
SHOW VARIABLES LIKE 'max_connections';    -- 最大连接数
SHOW PROCESSLIST;                         -- 查看当前连接详情

-- 2. 查询性能监控
SHOW STATUS LIKE 'Slow_queries';          -- 慢查询数量
SHOW STATUS LIKE 'Questions';             -- 总查询数
SHOW STATUS LIKE 'Queries';               -- 所有语句数（含COM_*）
SHOW STATUS LIKE 'Innodb_rows_read';      -- InnoDB读取行数
SHOW STATUS LIKE 'Innodb_rows_inserted';  -- InnoDB插入行数

-- 3. 缓冲池监控
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';      -- 从磁盘读取次数
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'; -- 读取请求次数
-- 缓冲池命中率 = 1 - (reads / read_requests)

-- 4. 锁监控
SHOW STATUS LIKE 'Innodb_row_lock_current_waits'; -- 当前等待行锁数量
SHOW STATUS LIKE 'Innodb_row_lock_time';          -- 行锁总等待时间（ms）
SHOW STATUS LIKE 'Innodb_row_lock_time_avg';      -- 平均行锁等待时间
SHOW ENGINE INNODB STATUS\G;                      -- 详细InnoDB状态
```

### 2. 性能分析工具

```bash
# 1. 慢查询日志分析
# 开启慢查询日志
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;  # 超过1秒的查询
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

# 使用mysqldumpslow分析
mysqldumpslow -s t /var/log/mysql/slow.log  # 按总时间排序
mysqldumpslow -s c /var/log/mysql/slow.log  # 按出现次数排序

# 使用pt-query-digest（更强大）
pt-query-digest /var/log/mysql/slow.log

# 2. 实时性能监控
# 使用mysqladmin
mysqladmin -uroot -p extended-status -i 1  # 每秒刷新状态

# 使用innotop（类似top）
innotop --user root --password 123456

# 3. 表状态分析
ANALYZE TABLE users;      # 更新表统计信息
CHECK TABLE users;        # 检查表错误
OPTIMIZE TABLE users;     # 优化表（重建，释放空间）
```

## 📖 SQL优化实战

### 1. 执行计划深度解读

```sql
-- 示例查询
EXPLAIN SELECT 
    u.name, u.email, o.order_no, o.amount, p.product_name
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE u.created_at > '2023-01-01'
  AND o.status = 'PAID'
  AND p.category = 'electronics'
ORDER BY o.created_at DESC
LIMIT 100;

-- EXPLAIN结果分析
/**
 * | id | select_type | table | partitions | type  | possible_keys | key     | key_len | ref                     | rows | filtered | Extra |
 * |----|-------------|-------|------------|-------|---------------|---------|---------|-------------------------|------|----------|-------|
 * | 1  | SIMPLE      | u     | NULL       | range | idx_created   | idx_created | 5       | NULL                    | 5000 | 100.00   | Using where; Using index; Using temporary; Using filesort |
 * | 1  | SIMPLE      | o     | NULL       | ref   | idx_user_status | idx_user_status | 8       | db.u.id                | 10   | 10.00    | Using where |
 * | 1  | SIMPLE      | oi    | NULL       | ref   | idx_order     | idx_order | 4       | db.o.id                | 5    | 100.00   | Using index |
 * | 1  | SIMPLE      | p     | NULL       | ref   | idx_category  | idx_category | 62      | db.oi.product_id       | 100  | 100.00   | Using where |
 * 
 * 关键字段解读：
 * - type: 访问类型（const > eq_ref > ref > range > index > ALL）
 * - key: 实际使用的索引
 * - rows: 预估扫描行数（越小越好）
 * - filtered: 过滤比例（100%表示完全使用索引）
 * - Extra: 额外信息（Using index表示覆盖索引）
 */
```

### 2. 常见SQL优化模式

```sql
-- 模式1：分页查询优化
-- 优化前：深度分页性能差
SELECT * FROM orders ORDER BY id LIMIT 1000000, 20;  -- 扫描1000020行

-- 优化方案1：使用覆盖索引 + 子查询
SELECT * FROM orders 
WHERE id >= (SELECT id FROM orders ORDER BY id LIMIT 1000000, 1)
ORDER BY id LIMIT 20;  -- 扫描20行

-- 优化方案2：记录上一页最后ID
SELECT * FROM orders 
WHERE id > 1000000  -- 上一页最后ID
ORDER BY id LIMIT 20;

-- 优化方案3：业务折中，限制最大分页
IF page_num > 100 THEN RETURN error("超出最大分页限制");

-- 模式2：IN查询优化
-- 优化前：IN子查询性能差
SELECT * FROM products 
WHERE category_id IN (SELECT id FROM categories WHERE level = 1);

-- 优化后：使用JOIN
SELECT p.* FROM products p
JOIN categories c ON p.category_id = c.id
WHERE c.level = 1;

-- 或者使用EXISTS
SELECT * FROM products p
WHERE EXISTS (
    SELECT 1 FROM categories c 
    WHERE c.id = p.category_id AND c.level = 1
);

-- 模式3：OR条件优化
-- 优化前：OR导致索引失效
SELECT * FROM users 
WHERE age > 30 OR salary > 10000;  -- 可能全表扫描

-- 优化后：使用UNION
SELECT * FROM users WHERE age > 30
UNION
SELECT * FROM users WHERE salary > 10000;

-- 或者添加复合索引
ALTER TABLE users ADD INDEX idx_age_salary (age, salary);

-- 模式4：LIKE查询优化
-- 优化前：前导通配符导致索引失效
SELECT * FROM products WHERE name LIKE '%手机%';  -- 全表扫描

-- 优化方案1：使用全文索引
ALTER TABLE products ADD FULLTEXT INDEX idx_name_ft (name);
SELECT * FROM products WHERE MATCH(name) AGAINST('手机');

-- 优化方案2：使用反向查询（特定场景）
SELECT * FROM products WHERE REVERSE(name) LIKE REVERSE('机手%');

-- 优化方案3：使用搜索引擎（Elasticsearch）
```

### 3. 索引优化策略

```sql
-- 策略1：最左前缀原则
-- 创建复合索引
CREATE INDEX idx_city_age_name ON users(city, age, name);

-- 能使用索引的查询
SELECT * FROM users WHERE city = '北京';                    -- ✅ 使用索引
SELECT * FROM users WHERE city = '北京' AND age > 20;       -- ✅ 使用索引
SELECT * FROM users WHERE city = '北京' AND age > 20 AND name LIKE '张%'; -- ✅ 使用索引

-- 不能使用完整索引的查询
SELECT * FROM users WHERE age > 20;                         -- ❌ 缺少city
SELECT * FROM users WHERE city = '北京' AND name LIKE '张%'; -- ✅ 但只用city部分

-- 策略2：覆盖索引优化
-- 查询：SELECT id, name FROM users WHERE age > 20;
-- 普通索引：需要回表查询name
-- 覆盖索引：索引包含所有查询字段
CREATE INDEX idx_age_name_id ON users(age, name, id);  -- id是主键，会自动包含

-- 策略3：索引下推（ICP）
-- MySQL 5.6+ 默认开启
-- 查询：SELECT * FROM users WHERE age > 20 AND name LIKE '张%';
-- 无ICP：存储引擎返回所有age>20的记录，Server层过滤name
-- 有ICP：存储引擎同时过滤age>20 AND name LIKE '张%'，减少回表

-- 策略4：索引合并
-- 多个单列索引的合并
CREATE INDEX idx_age ON users(age);
CREATE INDEX idx_city ON users(city);

-- 查询：SELECT * FROM users WHERE age > 25 OR city = '北京';
-- MySQL可能使用Index Merge优化

-- 但更好的方案是复合索引
CREATE INDEX idx_age_city ON users(age, city);
```

## 📖 表设计与优化

### 1. 数据类型选择

```sql
-- 原则1：使用最小合适类型
-- 不推荐
CREATE TABLE users (
    id INT(11) NOT NULL AUTO_INCREMENT,  -- INT足够，不需要(11)
    age TINYINT UNSIGNED,                -- 年龄0-255，TINYINT足够
    phone CHAR(11),                      -- 可变长度用VARCHAR
    status ENUM('active', 'inactive'),   -- 状态少可用TINYINT
    created_at TIMESTAMP,                -- 时间戳用DATETIME更通用
    PRIMARY KEY (id)
);

-- 推荐
CREATE TABLE users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,  -- 无符号INT，范围更大
    age TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- 明确默认值
    phone VARCHAR(20) NOT NULL DEFAULT '',    -- VARCHAR节省空间
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1:active, 0:inactive',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_phone (phone),
    KEY idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 原则2：避免NULL值
-- NULL需要额外空间存储，且索引效率低
-- 使用NOT NULL DEFAULT '' 或 NOT NULL DEFAULT 0

-- 原则3：选择合适字符串类型
-- CHAR：定长，适合短字符串（如MD5、UUID）
-- VARCHAR：变长，适合大部分场景
-- TEXT：长文本，避免在WHERE中频繁使用
```

### 2. 规范化与反规范化

```sql
-- 完全规范化（3NF）
-- 优点：数据冗余少，更新一致性好
-- 缺点：查询需要多表JOIN

CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE departments (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    manager_id INT,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- 查询用户及部门信息需要JOIN
SELECT u.name, d.name as dept_name 
FROM users u 
JOIN departments d ON u.dept_id = d.id;

-- 适度反规范化
-- 优点：减少JOIN，提高查询性能
-- 缺点：数据冗余，更新需要同步

CREATE TABLE users_denormalized (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    dept_id INT,
    dept_name VARCHAR(50),  -- 冗余字段
    manager_id INT,
    manager_name VARCHAR(50)  -- 冗余字段
);

-- 查询时不需要JOIN
SELECT name, dept_name, manager_name FROM users_denormalized;

-- 混合策略：基础表规范化，查询表反规范化
-- 基础表（写操作）
CREATE TABLE users_normalized (...);
CREATE TABLE departments_normalized (...);

-- 物化视图/查询表（读操作）
CREATE TABLE user_summary (
    user_id INT PRIMARY KEY,
    user_name VARCHAR(50),
    dept_name VARCHAR(50),
    manager_name VARCHAR(50),
    total_orders INT,
    total_amount DECIMAL(10,2),
    INDEX idx_dept (dept_name)
);

-- 定期更新物化视图
CREATE EVENT update_user_summary
ON SCHEDULE EVERY 1 HOUR
DO
    INSERT INTO user_summary (...)
    SELECT ... FROM users_normalized u
    JOIN departments_normalized d ON u.dept_id = d.id
    ON DUPLICATE KEY UPDATE ...;
```

## 📖 高并发场景优化

### 1. 热点更新问题

```sql
-- 场景：秒杀库存扣减
-- 问题：大量并发更新同一行，导致行锁竞争

-- 方案1：应用层排队
-- 使用Redis分布式锁或消息队列缓冲请求

-- 方案2：数据库乐观锁
CREATE TABLE inventory (
    product_id INT PRIMARY KEY,
    stock INT NOT NULL DEFAULT 0,
    version INT NOT NULL DEFAULT 0  -- 版本号
);

-- 更新时检查版本
UPDATE inventory 
SET stock = stock - 1, version = version + 1
WHERE product_id = 1001 
  AND stock > 0
  AND version = #{oldVersion};  -- 检查版本

-- 方案3：库存分段
-- 将库存拆分为多个分段，减少锁竞争
CREATE TABLE inventory_segments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    segment_no INT NOT NULL,  -- 分段编号
    stock INT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_product_segment (product_id, segment_no)
);

-- 随机选择一个分段扣减
UPDATE inventory_segments 
SET stock = stock - 1
WHERE product_id = 1001 
  AND segment_no = FLOOR(RAND() * 10)  -- 10个分段
  AND stock > 0;

-- 方案4：批量扣减 + 预扣库存
-- 应用层维护预扣库存，批量写入数据库
```

### 2. 大批量数据操作

```sql
-- 批量插入优化
-- 不推荐：单条插入
INSERT INTO logs (user_id, action, created_at) VALUES (1, 'login', NOW());
INSERT INTO logs (user_id, action, created_at) VALUES (2, 'login', NOW());

-- 推荐：批量插入
INSERT INTO logs (user_id, action, created_at) VALUES
(1, 'login', NOW()),
(2, 'login', NOW()),
(3, 'login', NOW());

-- 更优：使用LOAD DATA INFILE
LOAD DATA INFILE '/tmp/logs.csv'
INTO TABLE logs
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(user_id, action, created_at);

-- 批量更新优化
-- 不推荐：循环更新
UPDATE users SET score = score + 10 WHERE id = 1;
UPDATE users SET score = score + 10 WHERE id = 2;

-- 推荐：批量更新
UPDATE users 
SET score = score + 10 
WHERE id IN (1, 2, 3, 4, 5);

-- 或者使用CASE WHEN
UPDATE users 
SET score = CASE id
    WHEN 1 THEN score + 10
    WHEN 2 THEN score + 20
    ELSE score
END
WHERE id IN (1, 2);

-- 大批量删除优化
-- 问题：DELETE操作会锁表，产生大量undo日志

-- 方案1：分批次删除
DELETE FROM logs 
WHERE created_at < '2023-01-01'
LIMIT 1000;  -- 每次删除1000条

-- 循环执行直到删除完成

-- 方案2：创建新表 + 重命名
-- 1. 创建新表（只保留需要的数据）
CREATE TABLE logs_new LIKE logs;
INSERT INTO logs_new SELECT * FROM logs WHERE created_at >= '2023-01-01';

-- 2. 重命名
RENAME TABLE logs TO logs_old, logs_new TO logs;

-- 3. 删除旧表（可安排在低峰期）
DROP TABLE logs_old;

-- 方案3：使用分区表
-- 按时间分区，直接删除分区
ALTER TABLE logs DROP PARTITION p202201;
```

## 📖 分库分表实战

### 1. 分片策略选择

```java
/**
 * 分片策略对比
 */
public class ShardingStrategy {
    
    // 1. 范围分片（Range）
    /*
     * 按ID范围分片：1-1000万在DB1，1000万-2000万在DB2
     * 优点：易于扩容，范围查询效率高
     * 缺点：可能产生热点（新数据集中在最新分片）
     * 适用：时间序列数据、有自然顺序的数据
     */
    
    // 2. 哈希分片（Hash）
    /*
     * 对分片键取模：hash(user_id) % 4
     * 优点：数据分布均匀
     * 缺点：扩容复杂（需要数据迁移），范围查询困难
     * 适用：用户数据、订单数据等
     */
    
    // 3. 一致性哈希（Consistent Hash）
    /*
     * 解决哈希分片扩容问题
     * 添加节点时只影响部分数据
     * 实现复杂，需要维护哈希环
     */
    
    // 4. 地理位置分片（Geo）
    /*
     * 按地区分片：华北、华东、华南
     * 优点：符合业务场景，查询本地数据快
     * 缺点：数据分布可能不均衡
     */
    
    // 5. 复合分片（Composite）
    /*
     * 多种策略结合：先按用户分库，再按时间分表
     * 优点：灵活，适应复杂场景
     * 缺点：实现和维护复杂
     */
}
```

### 2. 分库分表示例

```sql
-- 分库分表配置示例（使用ShardingSphere）

-- 用户表：按user_id分库，每库16张表
-- 分库规则：user_id % 4（4个库）
-- 分表规则：user_id % 16（每库16表）

CREATE TABLE user_00 (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(50),
    email VARCHAR(100),
    created_at DATETIME,
    INDEX idx_user_id(user_id)
) ENGINE=InnoDB;

-- 订单表：按user_id分库，按order_id分表
-- 分库规则：user_id % 4
-- 分表规则：order_id % 32（每库32表）

CREATE TABLE order_00 (
    id BIGINT PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2),
    status VARCHAR(20),
    created_at DATETIME,
    UNIQUE KEY uk_order_id(order_id),
    INDEX idx_user_created(user_id, created_at)
) ENGINE=InnoDB;

-- 全局表（字典表）：每个库都有完整数据
CREATE TABLE product_category (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    parent_id INT,
    level INT,
    INDEX idx_parent(parent_id)
) ENGINE=InnoDB;
```

### 3. 分布式ID生成

```java
/**
 * 分布式ID生成方案
 */
public class DistributedIdGenerator {
    
    // 方案1：Snowflake（Twitter）
    /*
     * 64位ID = 1位符号位 + 41位时间戳 + 10位机器ID + 12位序列号
     * 优点：趋势递增，不依赖数据库
     * 缺点：时钟回拨问题
     */
    public class SnowflakeIdGenerator {
        private final long twepoch = 1288834974657L;  // 起始时间戳
        private final long workerIdBits = 10L;        // 机器ID位数
        private final long sequenceBits = 12L;        // 序列号位数
        
        public synchronized long nextId() {
            long timestamp = timeGen();
            if (timestamp < lastTimestamp) {
                throw new RuntimeException("时钟回拨");
            }
            
            if (lastTimestamp == timestamp) {
                sequence = (sequence + 1) & sequenceMask;
                if (sequence == 0) {
                    timestamp = tilNextMillis(lastTimestamp);
                }
            } else {
                sequence = 0L;
            }
            
            lastTimestamp = timestamp;
            
            return ((timestamp - twepoch) << timestampLeftShift)
                | (workerId << workerIdShift)
                | sequence;
        }
    }
    
    // 方案2：数据库号段（Leaf-segment）
    /*
     * 数据库维护号段：current_max_id = 1000, step = 1000
     * 应用内存中分配：1001-2000
     * 优点：简单，性能好
     * 缺点：数据库单点
     */
    
    // 方案3：Redis自增
    /*
     * INCR key 原子操作
     * 优点：性能好，简单
     * 缺点：Redis持久化问题，重启可能丢失
     */
    
    // 方案4：UUID
    /*
     * 通用唯一识别码
     * 优点：全球唯一，无需协调
     * 缺点：太长（36字符），无序，索引效率低
     */
}
```

## 📖 备份与恢复

### 1. 备份策略

```bash
# 1. 逻辑备份（mysqldump）
# 全量备份
mysqldump -uroot -p --single-transaction --master-data=2 \
  --routines --events --triggers --all-databases > full_backup.sql

# 单库备份
mysqldump -uroot -p db_name > db_backup.sql

# 2. 物理备份（Percona XtraBackup）
# 全量备份
xtrabackup --backup --target-dir=/backup/full --user=root --password=123456

# 增量备份
xtrabackup --backup --target-dir=/backup/inc1 \
  --incremental-basedir=/backup/full --user=root --password=123456

# 3. 备份恢复
# 逻辑备份恢复
mysql -uroot -p < full_backup.sql

# 物理备份恢复
# 准备备份
xtrabackup --prepare --target-dir=/backup/full
# 恢复
xtrabackup --copy-back --target-dir=/backup/full
```

### 2. 主从复制

```sql
-- 主库配置
-- my.cnf
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog-format = ROW
binlog-row-image = minimal

-- 创建复制用户
CREATE USER 'repl'@'%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

-- 查看主库状态
SHOW MASTER STATUS;
-- 记下 File: mysql-bin.000001, Position: 107

-- 从库配置
-- my.cnf
[mysqld]
server-id = 2
relay-log = mysql-relay-bin
read-only = 1  -- 从库只读

-- 配置复制
CHANGE MASTER TO
  MASTER_HOST='master_ip',
  MASTER_USER='repl',
  MASTER_PASSWORD='repl_password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=107;

-- 启动复制
START SLAVE;

-- 查看复制状态
SHOW SLAVE STATUS\G;
-- 关注：Slave_IO_Running: Yes, Slave_SQL_Running: Yes
```

## 📖 面试真题

### Q1: 如何分析SQL性能问题？

**答：**
1. **开启慢查询日志**：找到执行时间长的SQL
2. **使用EXPLAIN分析**：查看执行计划，关注type、key、rows、Extra
3. **检查索引使用**：是否使用正确索引，是否回表查询
4. **分析锁情况**：使用SHOW ENGINE INNODB STATUS查看锁信息
5. **监控服务器资源**：CPU、内存、磁盘IO、网络
6. **使用性能分析工具**：pt-query-digest、innotop等
7. **压测验证**：修改后重新压测，验证优化效果

### Q2: 什么情况下索引会失效？

**答：**
1. **违反最左前缀原则**：复合索引未使用最左列
2. **对索引列进行计算或函数操作**：WHERE YEAR(create_time) = 2023
3. **使用OR条件**：OR两侧未都使用索引
4. **LIKE以通配符开头**：WHERE name LIKE '%张三'
5. **类型转换**：字符串字段使用数字查询 WHERE phone = 13800138000
6. **使用!=或<>**：WHERE status != 'active'
7. **索引列使用IS NULL或IS NOT NULL**：需要额外处理
8. **数据量太少**：MySQL可能选择全表扫描

### Q3: 如何设计一个高性能的数据库架构？

**答：**
1. **合理分库分表**：根据业务场景选择分片策略
2. **读写分离**：主库写，从库读，增加多个从库
3. **缓存层**：Redis缓存热点数据，减少数据库压力
4. **连接池优化**：合理配置连接池参数
5. **索引优化**：创建合适的索引，定期维护
6. **SQL优化**：避免N+1查询，使用JOIN优化
7. **硬件优化**：使用SSD，增加内存，优化网络
8. **监控告警**：实时监控数据库性能，快速响应问题

### Q4: 如何解决数据库死锁？

**答：**
1. **预防死锁**：
   - 按相同顺序访问多张表
   - 减少事务大小和持有锁时间
   - 使用较低的事务隔离级别（如READ COMMITTED）
   - 使用索引，减少锁范围

2. **检测死锁**：
   - 监控InnoDB状态：SHOW ENGINE INNODB STATUS
   - 设置死锁超时：innodb_lock_wait_timeout = 50
   - 开启死锁日志：innodb_print_all_deadlocks = ON

3. **解决死锁**：
   - MySQL自动检测并回滚代价较小的事务
   - 应用层重试机制
   - 使用SELECT ... FOR UPDATE NOWAIT（立即失败，不等待）

### Q5: 如何进行数据库容量规划？

**答：**
1. **数据增长预测**：分析历史数据，预测未来增长
2. **存储计算**：数据量 × 增长系数 + 索引空间 + 预留空间
3. **性能需求**：根据QPS、TPS计算需要的IOPS和吞吐量
4. **高可用规划**：主从复制、集群部署需要的机器数量
5. **备份规划**：备份空间 = 数据量 × 备份保留天数 × 每日增量
6. **监控告警**：设置磁盘使用率、连接数等阈值告警
7. **扩容方案**：垂直扩容（升级硬件）和水平扩容（分库分表）方案

## 📚 延伸阅读

- [高性能MySQL](https://book.douban.com/subject/23008813/)
- [MySQL技术内幕](https://book.douban.com/subject/24708143/)
- [数据库索引设计与优化](https://book.douban.com/subject/26419771/)
- [MySQL官方文档](https://dev.mysql.com/doc/)

---

**⭐ 重点：数据库优化是系统工程，需要从SQL、索引、架构、硬件等多个层面综合考虑，持续监控和调优**