---
layout: default
title: 数据库读写分离方案详解 ⭐⭐⭐
---
# 数据库读写分离方案详解 ⭐⭐⭐

## 🎯 面试题：如何实现数据库读写分离？如何解决主从延迟问题？

> 读写分离是解决数据库读性能瓶颈最直接、最成熟的方案。面试中不仅会问原理，更会深挖主从延迟、数据一致性问题以及实际落地选型。

---

## 一、为什么需要读写分离

```
单体架构的问题：
  ┌─────────────────┐
  │   应用服务器     │
  │   100 台        │
  └────────┬────────┘
           │ 10000 QPS
           ↓
  ┌─────────────────┐
  │   MySQL 单机     │ ← 瓶颈：单机 QPS 上限 3000~5000
  └─────────────────┘

读写分离后的架构：
  ┌─────────────────┐     ┌──────────────┐
  │   写请求 (10%)   │────→│  MySQL 主库  │
  └─────────────────┘     └──────┬───────┘
                                 │ 同步
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │ MySQL 从1 │  │ MySQL 从2 │  │ MySQL 从3 │
            └────┬─────┘  └────┬─────┘  └────┬─────┘
                 ↓              ↓              ↓
  ┌─────────────────────────────┐
  │   读请求 (90%) 均衡分发     │
  └─────────────────────────────┘
```

**核心价值：**
- 主库承担写请求（INSERT/UPDATE/DELETE）
- 多个从库分担读请求（SELECT）
- 单机 MySQL 的读 QPS 从 3000 提升到 3×3000 = 9000

---

## 二、MySQL 主从复制原理

### binlog 三种格式

| 格式 | 内容 | 优点 | 缺点 |
|------|------|------|------|
| **ROW** | 记录每行数据变化（完整行数据） | 精确，无主从数据不一致 | binlog 大，复制慢 |
| **STATEMENT** | 记录 SQL 语句 | binlog 小，逻辑清晰 | 函数/存储过程可能不一致 |
| **MIXED** | 智能选择 ROW 或 STATEMENT | 平衡 | - |

```sql
-- 查看当前 binlog 格式
SHOW VARIABLES LIKE 'binlog_format';

-- 推荐使用 ROW 格式（数据一致性最好）
SET GLOBAL binlog_format = 'ROW';
```

### 主从复制流程（异步）

```
主库侧：
  1. 事务提交 → 写 binlog（顺序写磁盘，性能高）
  2. 事务提交 → 返回客户端

从库侧（IO Thread）：
  3. 从库连接主库，告知从哪个 position 开始拉取
  4. 主库收到拉取请求，从 binlog 读取对应内容发送给从库
  5. 从库 IO Thread 接收，写入 relay log（中继日志）

从库侧（SQL Thread）：
  6. 从库 SQL Thread 读取 relay log
  7. 在从库上重放（执行）SQL
  8. 更新从库数据
```

### GTID 模式（推荐）

```sql
-- GTID = Global Transaction Identifier
-- 格式：server_uuid:transaction_id
-- 示例：3E11FA47-71CA-11E1-9E33-C80AA9429562:23

-- GTID 优势：自动找位点，不需要手动指定 binlog position
-- 配置 GTID
server-id = 1
gtid_mode = ON
enforce_gtid_consistency = ON
```

### 半同步复制（保证数据不丢）

```
异步复制的问题：
  主库提交 → 写 binlog → 返回客户端
  从库还没同步 → 主库挂了 → 数据丢失 ❌

半同步复制：
  主库提交 → 写 binlog → 等待至少 1 个从库 ACK → 返回客户端
  从库没 ACK → 主库提交失败 → 返回错误
  
配置：
  INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
  SET GLOBAL rpl_semi_sync_master_enabled = 1;
```

---

## 三、主从延迟问题

### 延迟原因

```
主从延迟的三大原因：

1. 主库并发写入，从库串行重放
   → 写入快，重放慢，造成积压

2. 大事务
   → 主库一个事务操作 10 万行
   → 从库也要执行 10 万行
   → 主库秒完，从库可能要 10 秒

3. 从库硬件差（CPU/磁盘性能差）
   → 重放速度跟不上

监控延迟：
  SHOW SLAVE STATUS\G
  Seconds_Behind_Master: 5  ← 延迟 5 秒
```

### 延迟的解决方案

```
方案一：关键读走主库
  业务判断：下单后立即查订单 → 强制读主库
  代码：@ReadOnly(false) 或 Hints.forceMasterRead()

方案二：延迟检测 + 降级
  延迟 < 1s → 读从库
  延迟 > 1s → 降级读主库
  
方案三：读写多线程并行重放
  从库 SQL Thread → 多个 Worker Thread 并行重放
  配置：slave_parallel_workers = 8

方案四：缓存补偿
  写操作后 → 写缓存 → 读操作先查缓存
  缓存有数据 → 直接返回（绕过从库延迟）
```

---

## 四、ShardingSphere-JDBC 读写分离

### 为什么选 ShardingSphere-JDBC？

```
方案对比：

代理模式（MyCat/Codis）：
  应用 → MyCat → MySQL
  缺点：多一跳网络，需要独立部署，维护复杂

ShardingSphere-JDBC（推荐）：
  应用（含 JDBC 插件） → MySQL
  优点：无额外网络开销，对应用透明，可无缝升级到分库分表
  
ShardingSphere-Proxy：
  应用 → ShardingSphere-Proxy → MySQL
  优点：多语言支持（Python/Go），缺点：多一跳
```

### 完整配置

```yaml
spring:
  shardingsphere:
    datasource:
      ds-master:
        url: jdbc:mysql://192.168.1.1:3306/seckill?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
        username: root
        password: xxx
        driver-class-name: com.mysql.cj.jdbc.Driver
      ds-slave-1:
        url: jdbc:mysql://192.168.1.2:3306/seckill?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
        username: root
        password: xxx
        driver-class-name: com.mysql.cj.jdbc.Driver
      ds-slave-2:
        url: jdbc:mysql://192.168.1.3:3306/seckill?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
        username: root
        password: xxx
        driver-class-name: com.mysql.cj.jdbc.Driver

    rules:
      readwrite-splitting:
        data-sources:
          readwrite_ds:
            type: Static
            props:
              write-data-source-name: ds-master
              read-data-source-names: ds-slave-1, ds-slave-2
            load-balancer:
              type: ROUND_ROBIN  # 轮询负载均衡
              # 可选：RANDOM / WEIGHT
```

### 强制读主库场景

```java
// 场景一：下单后立即查订单（必须读主库，否则可能查到旧数据）
@Service
public class OrderService {

    // 方法一：注解强制主库
    @Transactional
    public Order createOrder(OrderRequest request) {
        // 先创建订单（写主库）
        Order order = orderMapper.insert(request);

        // 立即查询订单详情（强制读主库，防止主从延迟）
        HintManager.getInstance().setWriteRouteOnly();
        return orderMapper.selectById(order.getId());
    }

    // 方法二：手动 Hint
    public Order getOrderDirectly(Long orderId) {
        HintManager hm = HintManager.getInstance();
        hm.setWriteRouteOnly(); // 强制主库
        try {
            return orderMapper.selectById(orderId);
        } finally {
            hm.close();
        }
    }
}

// 场景二：读从库（默认行为）
public List<Item> listItems(Long categoryId) {
    // 不做特殊处理，默认走从库（负载均衡）
    return itemMapper.selectByCategoryId(categoryId);
}
```

---

## 五、主从复制延迟监控

```java
// 监控从库延迟，超过阈值触发告警
@Service
public class ReplicationMonitor {

    @Autowired
    private DataSource dataSource;

    @Scheduled(fixedDelay = 30000)  // 每 30 秒检查一次
    public void checkReplicationLag() {
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SHOW SLAVE STATUS")) {

            if (rs.next()) {
                long lagSeconds = rs.getLong("Seconds_Behind_Master");
                String slaveIO = rs.getString("Slave_IO_Running");
                String slaveSQL = rs.getString("Slave_SQL_Running");

                // 告警条件
                if (lagSeconds > 5 || !"Yes".equals(slaveIO)) {
                    sendAlert(lagSeconds, slaveIO, slaveSQL);
                }

                log.info("从库延迟: {}秒, IO: {}, SQL: {}",
                    lagSeconds, slaveIO, slaveSQL);
            }
        } catch (SQLException e) {
            log.error("监控从库延迟失败", e);
        }
    }
}
```

---

## 六、主从架构选型

### 一主一从（最小配置）

```
适用：小规模系统，低成本方案

主库：承担写 + 大部分读
从库：承担读 + 备份

问题：主库挂了需要手动切换
```

### 一主多从（最常用）

```
适用：中等规模，读请求占比 > 80%

优点：读能力线性扩展
缺点：主库仍是单点

建议：从库数量 2~3 个（太多管理复杂）
```

### 双主双从（高可用）

```
适用：大规模系统，写请求也较高

主1 ←→ 主2（互为主从）
从1（跟随主1）从2（跟随主2）

写入分散到两个主库
读取分散到四个从库

优点：写入也可扩展，无单点
缺点：架构复杂，双向同步需处理冲突
```

---

## 七、MHA 高可用方案

### MHA 工作原理

```
MySQL 主库宕机：
  MHA Manager 监控到主库不可达
  → 自动从从库中选择最新的一个
  → 将差异的 binlog 从其他从库拉过来补齐
  → 将新主库切换为可写
  → 将其他从库指向新主库
  → 整个过程 30 秒内完成
  
配置示例（manager.cnf）：
  [server default]
  manager_workdir=/var/log/mha/app1/
  manager_log=/var/log/mha/app1/manager.log
  remote_root=root
  ssh_user=root
  
  [server1]
  hostname=192.168.1.1
  candidate_master=1
  
  [server2]
  hostname=192.168.1.2
  candidate_master=1
```

---

## 八、高频面试题

**Q1: MySQL 主从复制的原理是什么？**
> 核心依赖 binlog：主库事务提交时将变更写入 binlog；从库 IO Thread 连接主库，拉取 binlog 并写入 relay log；然后从库 SQL Thread 读取 relay log，在从库上重放 SQL。三种 binlog 格式：STATEMENT（记录 SQL）、ROW（记录行变化）、MIXED（混合）。推荐用 GTID 模式，自动追踪位点，避免手动管理 binlog position。

**Q2: 主从延迟是怎么产生的？如何解决？**
> 延迟产生原因：① 主库并发写入，从库串行重放，能力不对等；② 大事务，一个事务改 10 万行，主库秒完从库要 10 秒；③ 从库硬件差。解决方案：① 关键读走主库（下单后查订单）；② 监控延迟，超过阈值降级读主库；③ 从库开启多线程并行重放（并行度 = CPU 核数）；④ 写操作后同步写缓存，读操作优先读缓存。

**Q3: ShardingSphere-JDBC 和 ShardingSphere-Proxy 有什么区别？**
> ShardingSphere-JDBC 是一个 JDBC 增强包，集成在应用中，直接拦截 JDBC 调用，无需独立部署，对应用透明，适合 Java 技术栈。ShardingSphere-Proxy 是独立部署的中间件服务，应用通过普通 JDBC 连接它，再由它连接 MySQL，支持多语言，适合异构系统或不想改代码的场景。中小型项目推荐 JDBC 方案。

**Q4: 如何保证读写分离后的数据一致性？**
> 完全实时一致无法保证（主从复制本身有延迟）。实际做法：① 主从延迟 < 1 秒的普通场景，直接读从库，接受短暂不一致；② 写操作后需要立即读到结果的场景，用 HintManager 强制读主库；③ 数据一致性要求极高的场景（如支付），不用读写分离，直接读主库。

**Q5: 为什么从库比主库性能更好能扛更多读请求？**
> 主库承担写操作，事务提交、锁等待、binlog 写入都会消耗资源，而且写入需要维护索引；而从库只有纯读取操作，没有锁冲突，可以配置更大的 buffer pool 而且可以关闭 binlog 日志。多个从库分担读请求，总读能力等于各从库之和，可以线性扩展。
