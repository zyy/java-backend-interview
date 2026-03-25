---
layout: default
title: MySQL 存储引擎
---
# MySQL 存储引擎

> 选择合适的存储引擎是优化的第一步

## 🎯 面试重点

- InnoDB 和 MyISAM 的区别
- 各存储引擎的特点和适用场景
- 如何选择存储引擎

## 📖 存储引擎对比

### InnoDB

```java
/**
 * InnoDB 存储引擎
 * 
 * 特点：
 * - 支持事务（ACID）
 * - 支持行级锁
 * - 支持外键
 * - 支持崩溃恢复
 * - 使用 B+ 树索引
 * - MVCC 实现并发
 * 
 * 适用场景：
 * - 需要事务支持
 * - 高并发读写
 * - 数据完整性要求高
 */
public class InnoDBFeatures {
    // 创建 InnoDB 表
    /*
     * CREATE TABLE orders (
     *     id BIGINT PRIMARY KEY AUTO_INCREMENT,
     *     customer_id BIGINT,
     *     amount DECIMAL(10,2),
     *     created_at TIMESTAMP
     * ) ENGINE=InnoDB;
     */
}
```

### MyISAM

```java
/**
 * MyISAM 存储引擎
 * 
 * 特点：
 * - 不支持事务
 * - 支持表级锁
 * - 不支持外键
 * - 不支持崩溃恢复
 * - 使用 B+ 树索引
 * - 压缩表节省空间
 * - 全文索引支持
 * 
 * 适用场景：
 * - 只读/写少的场景
 * - 全文搜索
 * - 空间函数应用
 */
public class MyISAMFeatures {
    // 创建 MyISAM 表
    /*
     * CREATE TABLE articles (
     *     id INT PRIMARY KEY AUTO_INCREMENT,
     *     title VARCHAR(200),
     *     content TEXT,
     *     FULLTEXT(content)
     * ) ENGINE=MyISAM;
     */
}
```

### 对比

```java
/**
 * InnoDB vs MyISAM 对比
 */
public class EngineComparison {
    /*
     * | 特性           | InnoDB                  | MyISAM                   |
     * |----------------|-------------------------|--------------------------|
     * | 事务           | ✅ 支持（ACID）          | ❌ 不支持                 |
     * | 锁级别         | 🔒 行级锁                | 🔒 表级锁                |
     * | 外键           | ✅ 支持                  | ❌ 不支持                 |
     * | 崩溃恢复       | ✅ 支持（redo/undo log） | ❌ 不支持                 |
     * | 全文索引       | ✅ MySQL 5.6+ 支持        | ✅ 支持                   |
     * | 索引结构       | 🏗️ B+ 树（聚簇索引）      | 🏗️ B+ 树（非聚簇索引）     |
     * | 并发性能       | 🚀 高（MVCC）            | 🐌 低                    |
     * | 存储文件       | 📁 .ibd（数据+索引）      | 📁 .MYD（数据）/.MYI（索引）|
     * | 缓存机制       | 📊 缓冲池（Buffer Pool）  | 📊 键缓存（Key Cache）    |
     * | 压缩           | ✅ 支持                  | ✅ 支持                   |
     * | 空间函数       | ❌ 不支持                 | ✅ 支持                   |
     * | 主键           | 🔑 必须有                | 🔑 可以没有              |
     * | 数据行数统计   | 🎯 不精确（采样统计）     | 🎯 精确（计数器）         |
     * | 适用场景       | 💼 业务表、交易系统       | 📊 日志、配置、只读查询    |
     */
}
```

### 其他存储引擎

```java
/**
 * 其他存储引擎
 */
public class OtherEngines {
    // Memory (Heap)
    /*
     * 数据存储在内存中
     * 速度快，适合临时表
     * 数据丢失
     */
    
    // Archive
    /*
     * 压缩存储
     * 只支持 INSERT/SELECT
     * 适合日志、审计表
     */
    
    // CSV
    /*
     * CSV 格式存储
     * 适合数据导入导出
     */
    
    // Merge
    /*
     * 分区表的集合
     * 适合历史数据归档
     */
}
```

## 📖 详细对比分析

### 1. 存储结构差异

**InnoDB**：
- 数据和索引存储在一个文件（.ibd）
- 使用**聚簇索引**：数据按主键顺序存储，叶节点存储完整数据行
- 支持表空间管理：共享表空间 vs 独立表空间

**MyISAM**：
- 数据（.MYD）和索引（.MYI）分开存储
- 使用**非聚簇索引**：索引叶节点存储数据指针（行号）
- 支持压缩表：节省存储空间

### 2. 锁机制对比

**InnoDB 行级锁**：
```sql
-- 行锁示例
BEGIN;
SELECT * FROM orders WHERE id = 1 FOR UPDATE; -- 对 id=1 加行锁
-- 其他事务不能修改 id=1 的行，但可以修改其他行
UPDATE orders SET amount = 100 WHERE id = 1;
COMMIT;
```

**MyISAM 表级锁**：
```sql
-- 表锁示例（自动加锁）
UPDATE myisam_table SET col1 = 'value' WHERE id = 1;
-- 整个表被锁定，其他写操作需要等待
```

### 3. 事务与崩溃恢复

**InnoDB 事务日志**：
- **redo log**（重做日志）：保证事务持久性
- **undo log**（撤销日志）：实现事务回滚和 MVCC
- **崩溃恢复**：重启时通过 redo log 恢复未提交事务

**MyISAM 无事务**：
- 写操作直接修改数据文件
- 崩溃后可能数据不一致
- 需要定期使用 `myisamchk` 修复表

### 4. 性能差异

**读写性能**：
- **InnoDB**：写性能优秀，适合读写混合场景
- **MyISAM**：读性能极佳，写性能较差（全表锁）

**并发性能**：
- **InnoDB**：高并发（MVCC + 行锁）
- **MyISAM**：低并发（表锁，读写互斥）

**内存使用**：
- **InnoDB**：需要较大缓冲池（Buffer Pool）
- **MyISAM**：需要键缓存（Key Cache）

### 5. 特殊功能

**MyISAM 优势**：
- 全文索引（FULLTEXT）
- 空间数据类型和索引（GIS）
- 表压缩（myisampack）
- 延迟索引更新

**InnoDB 优势**：
- 在线 DDL（5.6+）
- 热备份（ibbackup）
- 多版本控制（MVCC）
- 自适应哈希索引

## 📖 面试真题

### Q1: InnoDB 和 MyISAM 的区别？

**答：**
1. **事务支持**：InnoDB 支持事务（ACID），MyISAM 不支持
2. **锁级别**：InnoDB 行级锁，MyISAM 表级锁
3. **外键约束**：InnoDB 支持，MyISAM 不支持
4. **崩溃恢复**：InnoDB 通过 redo/undo log 恢复，MyISAM 容易损坏
5. **索引结构**：InnoDB 聚簇索引，MyISAM 非聚簇索引
6. **并发能力**：InnoDB MVCC 高并发，MyISAM 读写互斥
7. **全文索引**：MyISAM 原生支持，InnoDB 5.6+ 支持

### Q2: 什么场景使用 MyISAM？

**答：**
- **只读/读多写少**：如数据仓库、报表系统
- **全文搜索**：老版本 MySQL 全文搜索需求
- **GIS 应用**：需要空间函数和索引
- **临时表**：MySQL 内部临时表使用
- **日志表**：写入后很少修改的表

### Q3: InnoDB 为什么推荐使用自增主键？

**答：**
- **顺序写入**：自增 ID 保证数据按顺序插入，减少 B+ 树分裂
- **减少碎片**：避免随机插入导致的页分裂和空间碎片
- **性能优化**：顺序 IO 比随机 IO 快很多
- **缓存友好**：相邻数据可能在同一页，提高缓存命中率

### Q4: MyISAM 表损坏如何处理？

**答：**
1. 使用 `CHECK TABLE table_name` 检查表状态
2. 使用 `REPAIR TABLE table_name` 尝试修复
3. 使用命令行工具 `myisamchk -r table_name`
4. 从备份恢复，或使用 `mysqlcheck` 工具
5. 建议定期使用 `OPTIMIZE TABLE` 整理碎片

### Q5: 如何从 MyISAM 迁移到 InnoDB？

**答：**
1. **备份数据**：`mysqldump` 全量备份
2. **修改引擎**：`ALTER TABLE table_name ENGINE=InnoDB;`
3. **参数调整**：增加 `innodb_buffer_pool_size`
4. **测试验证**：功能测试和性能测试
5. **灰度切换**：逐步迁移，监控性能

## 🎯 选择建议

### 选择 InnoDB 的情况：
- 需要事务支持（银行、电商）
- 高并发读写（在线系统）
- 数据完整性要求高（外键约束）
- 需要崩溃恢复能力
- MySQL 5.5+ 默认引擎

### 选择 MyISAM 的情况：
- 只读或读多写少（数据仓库）
- 需要全文搜索（5.6 前版本）
- 空间/GIS 应用
- 内存有限的小型应用
- 临时表、日志表

### 混合使用策略：
- 核心业务表使用 InnoDB
- 日志、配置表使用 MyISAM
- 全文搜索表使用 MyISAM（5.6 前）或 InnoDB（5.6+）

## 📖 面试真题

### Q1: InnoDB 和 MyISAM 的区别？

**答：** InnoDB 和 MyISAM 是 MySQL 两种主要的存储引擎，主要区别如下：

#### 1. 事务支持
- **InnoDB**：支持事务（ACID），具有提交、回滚和崩溃恢复能力。
- **MyISAM**：不支持事务，适合只读或读多写少的场景。

#### 2. 锁机制
- **InnoDB**：支持行级锁，并发写性能高，减少锁冲突。
- **MyISAM**：只支持表级锁，写操作会锁住整个表，并发性能差。

#### 3. 外键约束
- **InnoDB**：支持外键约束，保证数据完整性。
- **MyISAM**：不支持外键，需要应用层维护数据一致性。

#### 4. 索引结构
- **InnoDB**：使用聚集索引，数据文件本身就是索引文件，主键查询快。
- **MyISAM**：使用非聚集索引，索引和数据文件分离，主键查询需要两次查找。

#### 5. 崩溃恢复
- **InnoDB**：有崩溃恢复机制（redo log），数据安全性高。
- **MyISAM**：无崩溃恢复，表损坏后需要修复。

#### 6. 存储方式
- **InnoDB**：表空间管理，所有表共享一个或多个表空间文件。
- **MyISAM**：每个表三个文件：`.frm`（表结构）、`.MYD`（数据）、`.MYI`（索引）。

#### 7. 全文索引
- **InnoDB**：MySQL 5.6 后支持全文索引。
- **MyISAM**：原生支持全文索引，5.6 前常用。

#### 8. 缓存
- **InnoDB**：缓存数据和索引，使用缓冲池（buffer pool）提高性能。
- **MyISAM**：只缓存索引，数据依赖操作系统缓存。

**总结对比表**：
| 特性 | InnoDB | MyISAM |
|------|--------|--------|
| 事务 | ✅ 支持 | ❌ 不支持 |
| 锁级别 | 行级锁 | 表级锁 |
| 外键 | ✅ 支持 | ❌ 不支持 |
| 崩溃恢复 | ✅ 有 redo log | ❌ 无 |
| 全文索引 | ✅ 5.6+ | ✅ 原生 |
| 索引类型 | 聚集索引 | 非聚集索引 |
| 缓存 | 数据和索引 | 仅索引 |
| 适用场景 | OLTP（高并发写） | OLAP（读多写少） |

**选择建议**：
- 需要事务、高并发写、数据完整性 → **InnoDB**
- 只读查询、数据仓库、全文搜索（5.6前）→ **MyISAM**
- MySQL 5.5+ 默认使用 InnoDB，无特殊需求建议使用 InnoDB。

---

**⭐ 重点：InnoDB 是 MySQL 的默认存储引擎，从 MySQL 5.5 开始全面替代 MyISAM**