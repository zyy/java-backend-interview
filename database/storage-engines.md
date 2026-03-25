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
     * | 特性           | InnoDB      | MyISAM     |
     * |----------------|-------------|------------|
     * | 事务           | 支持        | 不支持     |
     * | 锁级别         | 行级        | 表级       |
     * | 外键           | 支持        | 不支持     |
     * | 崩溃恢复       | 支持        | 不支持     |
     * | 全文索引       | 5.6+ 支持   | 支持       |
     * | 索引结构       | B+ 树       | B+ 树      |
     * | 并发           | 高          | 低         |
     * | 适用场景       | 业务表      | 日志、配置 |
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

## 📖 面试真题

### Q1: InnoDB 和 MyISAM 的区别？

**答：**
- InnoDB 支持事务、行级锁、外键、崩溃恢复
- MyISAM 不支持事务、表级锁，不支持崩溃恢复
- InnoDB 支持 MVCC 高并发，MyISAM 不支持

### Q2: 什么场景使用 MyISAM？

**答：**
- 只读场景
- 全文搜索场景
- 不需要事务的小型应用

### Q3: InnoDB 为什么推荐使用自增主键？

**答：**
- 插入时顺序写入，避免 B+ 树的页分裂
- 减少随机 IO，提高插入性能

---

**⭐ 重点：InnoDB 是 MySQL 的默认存储引擎，必须掌握其特点**