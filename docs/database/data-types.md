# MySQL 数据类型选择

> 合理选择数据类型提高性能和可维护性

## 🎯 面试重点

- 数据类型选择原则
- 常见数据类型的使用场景
- 数据类型对性能的影响

## 📖 选择原则

### 基本原则

```java
/**
 * 数据类型选择原则
 */
public class DataTypePrinciples {
    // 1. 越小越好
    /*
     * 使用最小的数据类型
     * TINYINT vs INT：节省 3 字节/行
     */
    
    // 2. 简单就好
    /*
     * 用内置类型不用字符串
     * DATE vs CHAR(10)
     * INT vs VARCHAR
     */
    
    // 3. 避免 NULL
    /*
     * 可为 NULL 使索引和统计更复杂
     * 设置 NOT NULL DEFAULT ''
     */
    
    // 4. 避免过度设计
    /*
     * 不要预留太多空间
     * VARCHAR(100) vs VARCHAR(255)
     */
}
```

### 整数类型

```java
/**
 * 整数类型
 */
public class IntegerTypes {
    /*
     * | 类型      | 字节  | 范围                      |
     * |-----------|-------|---------------------------|
     * | TINYINT   | 1     | -128 ~ 127                |
     * | SMALLINT  | 2     | -32768 ~ 32767            |
     * | MEDIUMINT | 3     | -8388608 ~ 8388607        |
     * | INT       | 4     | -21亿 ~ 21亿              |
     * | BIGINT    | 8     | -9223372036854775808     |
     * 
     * 无符号：UNSIGNED，范围翻倍
     * 
     * 选择：
     * - 年龄：TINYINT
     * - 数量：INT
     * - ID：BIGINT
     */
}
```

### 字符串类型

```java
/**
 * 字符串类型
 */
public class StringTypes {
    // CHAR vs VARCHAR
    /*
     * CHAR(N)：固定长度，0-255
     * VARCHAR(N)：可变长度，0-65535
     * 
     * CHAR：
     * - 存储定长（如手机号、MD5）
     * - 存储效率高
     * 
     * VARCHAR：
     * - 存储变长数据
     * - 需要额外空间存储长度
     */
    
    // TEXT 类型
    /*
     * TINYTEXT：255 字节
     * TEXT：65535 字节
     * MEDIUMTEXT：16MB
     * LONGTEXT：4GB
     * 
     * 注意：TEXT 不能建索引（可以指定前N个字符）
     */
}
```

### 日期类型

```java
/**
 * 日期类型
 */
public class DateTypes {
    // DATE vs DATETIME vs TIMESTAMP
    /*
     * DATE：日期，'2024-01-01'
     * DATETIME：日期时间，'2024-01-01 12:00:00'
     * TIMESTAMP：时间戳，自动时区转换
     * 
     * DATETIME：
     * - 8 字节
     * - 范围：'1000-01-01 00:00:00' ~ '9999-12-31 23:59:59'
     * 
     * TIMESTAMP：
     * - 4 字节
     * - 范围：'1970-01-01 00:00:01' ~ '2038-01-19 03:14:07'
     * - 自动转换为 Unix 时间戳
     */
    
    // 推荐
    /*
     * 存储时间：DATETIME
     * 存储时间戳：INT/BIGINT（Unix 时间戳）
     */
}
```

## 📖 面试真题

### Q1: INT(1) 和 INT(10) 的区别？

**答：** 没有区别，都是 4 字节的 INT。括号内的数字只是显示宽度，不影响存储范围。

### Q2: VARCHAR(100) 和 VARCHAR(255) 的区别？

**答：** VARCHAR 是可变长度，实际存储 1-2 字节 + 实际字符。255 以下用 1 字节存储长度，256 及以上用 2 字节。但实际性能差异不大。

---

**⭐ 重点：合理的数据类型选择是优化的基础**