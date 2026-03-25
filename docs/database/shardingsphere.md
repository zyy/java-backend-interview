# ShardingSphere 分库分表实战

> 阿里巴巴开源的分布式数据库中间件，提供分库分表、读写分离等能力

## 🎯 面试重点

- ShardingSphere 核心概念：分片键、分片算法、分片策略
- 分库分表的实现原理
- 读写分离的配置与实现
- 分布式事务处理

## 📖 ShardingSphere 架构

### 核心组件

```java
/**
 * ShardingSphere 核心组件
 * 
 * 1. Sharding-JDBC: 轻量级 Java 框架，提供 JDBC 增强
 * 2. Sharding-Proxy: 透明代理，支持多语言
 * 3. Sharding-Sidecar: 云原生边车模式
 */
public class ShardingSphereComponents {
    
    // Sharding-JDBC：应用层分片
    /*
     * 优点：性能高，部署简单
     * 缺点：需要代码依赖，不支持多语言
     */
    
    // Sharding-Proxy：数据库代理
    /*
     * 优点：支持多语言，无需代码改动
     * 缺点：性能损耗，需要额外部署
     */
}
```

### 核心概念

```java
/**
 * 分库分表核心概念
 */
public class ShardingConcepts {
    
    // 分片键（Sharding Key）
    /*
     * 用于路由到具体库表的字段
     * 例如：user_id、order_id、创建时间
     * 选择原则：数据分布均匀、查询高频
     */
    
    // 分片算法（Sharding Algorithm）
    /*
     * 1. 精确分片算法：=、IN
     * 2. 范围分片算法：BETWEEN
     * 3. 复合分片算法：多字段组合
     */
    
    // 分片策略（Sharding Strategy）
    /*
     * 1. 标准分片策略：单分片键
     * 2. 复合分片策略：多分片键
     * 3. 行表达式分片策略：Groovy表达式
     * 4. Hint 分片策略：强制路由
     */
}
```

## 📖 配置实战

### 分库分表示例

```yaml
# application-sharding.yml
spring:
  shardingsphere:
    datasource:
      names: ds0, ds1
      ds0:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/db0
        username: root
        password: 123456
      ds1:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/db1
        username: root
        password: 123456
    
    sharding:
      tables:
        # 用户表分片配置
        user:
          actual-data-nodes: ds$->{0..1}.user_$->{0..3}
          table-strategy:
            standard:
              sharding-column: user_id
              sharding-algorithm-name: user-table-sharding
          key-generator:
            column: id
            type: SNOWFLAKE
          # 分库策略
          database-strategy:
            standard:
              sharding-column: user_id
              sharding-algorithm-name: user-database-sharding
    
      # 分片算法定义
      sharding-algorithms:
        user-database-sharding:
          type: INLINE
          props:
            algorithm-expression: ds$->{user_id % 2}
        user-table-sharding:
          type: INLINE
          props:
            algorithm-expression: user_$->{user_id % 4}
    
    # 显示 SQL
    props:
      sql:
        show: true
```

### 读写分离配置

```yaml
# application-readwrite.yml
spring:
  shardingsphere:
    datasource:
      names: master, slave0, slave1
      master:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/master_db
        username: root
        password: 123456
      slave0:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3316/slave_db
        username: root
        password: 123456
      slave1:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3326/slave_db
        username: root
        password: 123456
    
    rules:
      readwrite-splitting:
        data-sources:
          readwrite_ds:
            type: Static
            props:
              write-data-source-name: master
              read-data-source-names: slave0, slave1
            load-balancer-name: round_robin
        
        load-balancers:
          round_robin:
            type: ROUND_ROBIN
```

## 📖 面试真题

### Q1: ShardingSphere 如何实现分库分表？

**答：**
1. **SQL 解析**：解析 SQL 语句，提取分片条件
2. **路由**：根据分片键计算目标库表
3. **改写**：将逻辑 SQL 改写为真实 SQL（如 `user` → `user_0`）
4. **执行**：在多个数据源上执行 SQL
5. **归并**：将多个结果集合并返回

### Q2: 分片键如何选择？

**答：**
- **数据均匀**：保证数据分布均衡，避免热点
- **查询高频**：高频查询条件作为分片键，避免跨库查询
- **业务相关**：如用户 ID、订单 ID、时间范围
- **避免修改**：分片键修改会导致数据迁移

### Q3: 跨库分页查询如何处理？

**答：**
1. **全局排序法**（不推荐）：查询所有数据在内存排序，性能差
2. **二次查询法**（推荐）：
   - 各分片查询，取前 N 条
   - 内存排序取前 M 条
   - 二次查询获取完整数据
3. **业务折中**：使用 ES 等搜索引擎

### Q4: 分布式事务如何解决？

**答：**
1. **柔性事务**（最终一致）：
   - **TCC**：Try-Confirm-Cancel，业务侵入强
   - **SAGA**：长事务，补偿机制
   - **消息事务**：MQ 事务消息
2. **刚性事务**（强一致）：
   - **XA 协议**：两阶段提交，性能低
   - **Seata AT 模式**：自动补偿

### Q5: 分库分表后 ID 生成方案？

**答：**
1. **Snowflake**：分布式自增 ID，ShardingSphere 默认
2. **UUID**：无序，索引效率低
3. **数据库分段**：多实例分段自增
4. **Redis 自增**：Redis 原子操作
5. **Leaf**：美团开源的分布式 ID 生成器

## 📖 最佳实践

### 1. 分片策略选择
- **水平分片**：数据量大时使用
- **垂直分片**：业务模块分离时使用
- **混合分片**：先垂直后水平

### 2. 分片数量规划
- 单表数据量控制在 1000 万以内
- 分片数 = 预估数据量 / 单表容量
- 预留 30% 扩展空间

### 3. 数据迁移方案
- **双写方案**：新旧库同时写入，数据同步
- **数据校验**：全量和增量数据校验
- **灰度切换**：逐步切流验证

### 4. 监控与运维
- **慢 SQL 监控**：跨库查询性能
- **数据倾斜监控**：分片数据分布
- **连接池监控**：数据源连接状态

## 📚 延伸阅读

- [ShardingSphere 官方文档](https://shardingsphere.apache.org/document/current/)
- [分布式数据库架构](https://time.geekbang.org/column/intro/100086001)
- [分库分表实战案例](https://github.com/apache/shardingsphere-example)

---

**⭐ 重点：分库分表是解决海量数据存储和查询的终极方案，必须掌握其原理和实践**