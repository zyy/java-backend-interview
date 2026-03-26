---
layout: default
title: MySQL 主从复制与高可用
---

# MySQL 主从复制与高可用

> 主从复制是 MySQL 实现读写分离和高可用的基础，面试必考

## 🎯 面试重点

- 主从复制的原理与流程
- 复制模式：异步、半同步、组复制
- 主从延迟的原因与解决方案
- 主从切换与故障恢复
- 读写分离架构设计

---

## 📖 一、主从复制原理

### 1.1 复制流程

```
Master                      Slave
  │                          │
  │  1. 写操作（INSERT/UPDATE/DELETE）
  │                          │
  ▼                          │
Binlog（二进制日志）          │
  │                          │
  │  2. Dump Thread 发送 binlog
  │─────────────────────────▶│
  │                          │
  │                     3. I/O Thread 接收
  │                          │  写入 Relay Log
  │                          │
  │                     4. SQL Thread 重放
  │                          │  执行相同操作
  │                          ▼
  │                      数据同步完成
```

**核心组件**：
- **Binlog**：Master 上的二进制日志，记录所有写操作
- **Dump Thread**：Master 上的线程，负责发送 binlog 给 Slave
- **I/O Thread**：Slave 上的线程，负责接收 binlog 并写入 Relay Log
- **SQL Thread**：Slave 上的线程，负责读取 Relay Log 并执行

### 1.2 复制模式

#### 异步复制（Asynchronous）

```
Master 写入 Binlog ──▶ 立即返回客户端成功
         │
         └──（异步）──▶ Slave 拉取并执行
```

- **特点**：Master 不等待 Slave 确认，性能最好
- **缺点**：主从延迟期间，如果 Master 宕机，数据可能丢失
- **适用**：对数据一致性要求不高的场景

#### 半同步复制（Semi-Synchronous）

```
Master 写入 Binlog ──▶ 等待至少一个 Slave 确认收到 ──▶ 返回客户端成功
```

- **特点**：Master 等待至少一个 Slave 收到 binlog 后才返回成功
- **优点**：数据安全性提高，减少丢失风险
- **缺点**：性能略有下降，增加延迟
- **配置**：
```sql
-- Master
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
SET GLOBAL rpl_semi_sync_master_enabled = 1;

-- Slave
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
SET GLOBAL rpl_semi_sync_slave_enabled = 1;
```

#### 组复制（Group Replication）

- **特点**：多主架构，基于 Paxos 协议实现数据一致性
- **优点**：自动故障转移，强一致性
- **缺点**：配置复杂，性能开销大
- **适用**：金融级高可用场景

### 1.3 Binlog 格式

| 格式 | 记录内容 | 优点 | 缺点 |
|-----|---------|------|------|
| **STATEMENT** | SQL 语句 | 日志小，性能好 | 某些语句可能导致主从不一致（如 UUID、NOW()） |
| **ROW** | 行数据变更 | 精确复制，无歧义 | 日志大（批量操作） |
| **MIXED** | 混合模式 | 自动选择 | 复杂 |

**推荐**：MySQL 5.7+ 使用 **ROW** 格式
```sql
SET GLOBAL binlog_format = 'ROW';
```

---

## 📖 二、主从延迟

### 2.1 延迟原因

1. **Slave 性能不足**：Slave 配置低于 Master
2. **大事务**：Master 执行大事务，Slave 需要较长时间重放
3. **锁竞争**：Slave 上有查询操作，与 SQL Thread 锁竞争
4. **网络延迟**：Master 与 Slave 网络不稳定
5. **单线程复制**：MySQL 5.6 之前只有单线程 SQL Thread

### 2.2 延迟监控

```sql
-- 查看 Slave 状态
SHOW SLAVE STATUS\G

-- 关键字段
Seconds_Behind_Master: 10    -- 延迟秒数
Slave_IO_Running: Yes         -- I/O 线程状态
Slave_SQL_Running: Yes        -- SQL 线程状态
Last_IO_Error:               -- I/O 错误信息
Last_SQL_Error:              -- SQL 错误信息
```

### 2.3 解决方案

#### 1. 并行复制（MySQL 5.6+）

```sql
-- 基于库的并行复制（5.6）
SET GLOBAL slave_parallel_workers = 4;
SET GLOBAL slave_parallel_type = 'DATABASE';

-- 基于事务组的并行复制（5.7+）
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
SET GLOBAL slave_parallel_workers = 8;
```

#### 2. 读写分离 + 延迟容忍

```java
@Service
public class OrderService {
    
    @Autowired
    @Qualifier("masterDataSource")
    private DataSource masterDataSource;
    
    @Autowired
    @Qualifier("slaveDataSource")
    private DataSource slaveDataSource;
    
    // 写操作：走 Master
    @Transactional
    public void createOrder(Order order) {
        // 强制走 Master
        orderMapper.insert(order);
    }
    
    // 读操作：走 Slave，但注意延迟
    public Order getOrder(Long orderId) {
        // 默认走 Slave
        Order order = orderMapper.selectById(orderId);
        
        // 如果读不到（可能延迟），降级到 Master
        if (order == null) {
            order = orderMapper.selectByIdFromMaster(orderId);
        }
        
        return order;
    }
    
    // 关键读操作：强制走 Master
    public Order getOrderForUpdate(Long orderId) {
        // 支付状态查询，必须最新数据
        return orderMapper.selectByIdFromMaster(orderId);
    }
}
```

#### 3. 延迟阈值告警

```java
@Component
public class ReplicationMonitor {
    
    @Scheduled(fixedDelay = 60000)  // 每分钟检查
    public void checkReplicationLag() {
        Integer lag = jdbcTemplate.queryForObject(
            "SHOW SLAVE STATUS", 
            (rs, rowNum) -> rs.getInt("Seconds_Behind_Master")
        );
        
        if (lag != null && lag > 10) {  // 延迟超过 10 秒
            alertService.sendAlert("MySQL 主从延迟: " + lag + " 秒");
        }
    }
}
```

---

## 📖 三、高可用架构

### 3.1 主从切换

**手动切换**：
```sql
-- 1. 在 Slave 上停止复制
STOP SLAVE;

-- 2. 重置主从关系
RESET SLAVE ALL;

-- 3. 提升为 Master（如果有其他 Slave，需要重新指向）
-- 其他 Slave 执行：
CHANGE MASTER TO 
    MASTER_HOST='new_master_host',
    MASTER_USER='repl',
    MASTER_PASSWORD='password',
    MASTER_LOG_FILE='mysql-bin.000001',
    MASTER_LOG_POS=154;
START SLAVE;
```

**自动切换（MHA）**：
```bash
# MHA（Master High Availability）架构
# 1. Manager 监控 Master 健康
# 2. Master 宕机时，自动选择最新 Slave 提升为 Master
# 3. 其他 Slave 自动重新指向新 Master
# 4. VIP 漂移，应用无感知
```

### 3.2 常见高可用方案

| 方案 | 架构 | 切换方式 | 适用场景 |
|-----|------|---------|---------|
| **MHA** | 1主多从 | 自动 | 中小型系统 |
| **MGR** | 多主 | 自动 | 金融级高可用 |
| **Orchestrator** | 可视化 | 自动/手动 | 大规模集群 |
| **ProxySQL** | 代理层 | 自动 | 读写分离 |

---

## 📖 四、面试真题

### Q1: MySQL 主从复制的原理是什么？

**答：** MySQL 主从复制基于 Binlog 实现：

1. **Master 端**：所有写操作记录到 Binlog
2. **Slave 端**：
   - I/O Thread 连接 Master，拉取 Binlog 写入 Relay Log
   - SQL Thread 读取 Relay Log，重放 SQL 语句

**关键点**：
- 异步复制：Master 不等待 Slave，性能好但可能丢数据
- 半同步复制：Master 等待至少一个 Slave 确认，数据更安全
- 并行复制：MySQL 5.6+ 支持多线程 SQL Thread，减少延迟

### Q2: 主从延迟如何解决？

**答：** 主从延迟是生产常见问题，解决方案：

1. **硬件升级**：Slave 配置不低于 Master
2. **并行复制**：开启 `slave_parallel_workers`，多线程重放
3. **拆分大事务**：避免一次性更新大量数据
4. **读写分离 + 延迟容忍**：
   - 非关键读走 Slave
   - 关键读（如支付后查询）强制走 Master
5. **缓存补偿**：写入 Master 后，缓存一份数据，读时先查缓存

### Q3: 如何实现读写分离？

**答：** 读写分离有两种实现方式：

**方式一：应用层实现**
```java
// 使用 Spring 动态数据源
@Configuration
public class DataSourceConfig {
    
    @Bean
    public DataSource routingDataSource() {
        DynamicRoutingDataSource routing = new DynamicRoutingDataSource();
        Map<Object, Object> targets = new HashMap<>();
        targets.put("master", masterDataSource());
        targets.put("slave", slaveDataSource());
        routing.setTargetDataSources(targets);
        return routing;
    }
}

// 注解标记
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface ReadOnly {
}

// AOP 拦截
@Aspect
@Component
public class DataSourceAspect {
    
    @Before("@annotation(ReadOnly)")
    public void setSlaveDataSource() {
        DataSourceContextHolder.setDataSource("slave");
    }
}
```

**方式二：中间件实现（推荐）**
- **ProxySQL**：自动路由读写，支持延迟检测
- **MyCat**：国产分库分表中间件
- **ShardingSphere**：Apache 开源，功能丰富

### Q4: 主库宕机如何快速恢复？

**答：** 快速恢复需要完善的预案：

1. **自动切换**：使用 MHA/MGR 实现秒级切换
2. **数据补偿**：
   - 如果 Binlog 未同步到从库，需要从备份恢复
   - 或使用 `pt-table-checksum` 工具校验数据一致性
3. **业务降级**：
   - 切换期间，写操作降级为只读
   - 或切换到备用系统
4. **事后复盘**：
   - 分析宕机原因（硬件/软件/人为）
   - 完善监控和告警

---

## 📚 延伸阅读

- [MySQL 官方复制文档](https://dev.mysql.com/doc/refman/8.0/en/replication.html)
- [MHA 高可用方案](https://github.com/yoshinorim/mha4mysql-manager)
- [ProxySQL 读写分离](https://proxysql.com/documentation/)
