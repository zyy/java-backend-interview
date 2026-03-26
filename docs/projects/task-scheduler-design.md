---
layout: default
title: 如何设计一个分布式任务调度平台？⭐⭐⭐
---
# 如何设计一个分布式任务调度平台？

## 🎯 面试题：如何实现一个分布式任务调度系统？

> 定时任务是后端开发的标配：数据同步、报表生成、优惠券过期清理、支付对账……从单机 Cron 到分布式调度，每个阶段都有不同的挑战。

---

## 一、为什么需要分布式调度？

```
单机 Cron 的问题：
  ❌ 节点挂了，任务停止调度
  ❌ 节点扩容，任务被重复执行
  ❌ 任务执行时间不可控，无法统一管理
  ❌ 无法动态修改任务参数
  ❌ 任务执行日志分散，难以追溯

分布式调度的目标：
  ✅ 高可用：任意节点故障，任务自动转移
  ✅ 可视化：统一管理所有定时任务
  ✅ 幂等执行：同一任务同一时刻只有一个实例在跑
  ✅ 实时修改：任务参数变更无需重启
  ✅ 执行日志集中：便于排查问题
```

---

## 二、整体架构设计

```
┌──────────────────────────────────────────────────────────┐
│                   分布式任务调度平台架构                      │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │  调度中心  │───▶│  执行器集群 │───▶│  任务存储        │   │
│  │ (Scheduler)│    │ (Executors)│    │  MySQL/Redis     │   │
│  └─────┬────┘    └──────────┘    └──────────────────┘   │
│        │                                                  │
│  ┌─────▼────┐    ┌──────────┐    ┌──────────────────┐   │
│  │  任务注册  │◀───│  Admin   │    │  执行日志        │   │
│  │  & 触发   │    │  Web 控制台│    │  链路追踪        │   │
│  └──────────┘    └──────────┘    └──────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

**核心组件：**
- **调度中心（Scheduler）**：负责任务的定时触发、调度策略下发
- **执行器（Executor）**：负责任务的实际执行，汇报执行结果
- **任务存储**：保存任务定义、调度时间、下次触发时间
- **执行日志**：记录每次执行的开始时间、结束时间、结果

---

## 三、任务调度核心原理

### 1. 轮询抢锁模式（抢任务）

```
所有执行器节点定时（比如每 10 秒）去抢以下一把"任务锁"：

  Redis:  SETNX lock:task:{taskId} {nodeId}  EX 30

抢到的节点获得执行权，执行完成后释放锁。
未抢到的节点继续轮询。
```

```java
@Component
@Slf4j
public class SchedulerService {

    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private TaskMapper taskMapper;
    @Autowired private TaskExecutor taskExecutor;

    // 调度器轮询间隔（ms）
    private static final long SCHEDULE_INTERVAL = 10_000L;
    // 任务锁过期时间（s）
    private static final long LOCK_EXPIRE = 30L;

    @Scheduled(fixedDelay = SCHEDULE_INTERVAL)
    public void scheduleLoop() {
        // 1. 查询到达触发时间的任务
        List<TaskDO> dueTasks = taskMapper.selectDueTasks(LocalDateTime.now());

        for (TaskDO task : dueTasks) {
            // 2. 尝试抢锁
            String lockKey = "task:lock:" + task.getId();
            Boolean acquired = redisTemplate.opsForValue()
                .setIfAbsent(lockKey, getCurrentNodeId(), Duration.ofSeconds(LOCK_EXPIRE));

            if (Boolean.TRUE.equals(acquired)) {
                log.info("[Scheduler] Acquired lock for task: {}", task.getId());
                // 3. 异步执行任务（不阻塞调度主循环）
                executeAsync(task);
            }
        }
    }

    private void executeAsync(TaskDO task) {
        CompletableFuture.runAsync(() -> {
            try {
                taskExecutor.execute(task);
                // 4. 更新下次触发时间
                LocalDateTime nextFireTime = calculateNextFireTime(task);
                taskMapper.updateNextFireTime(task.getId(), nextFireTime);
            } finally {
                // 5. 释放锁
                redisTemplate.delete("task:lock:" + task.getId());
            }
        });
    }
}
```

**抢锁模式的优点**：实现简单，无需选举协议  
**缺点**：所有节点都在轮询，有无效竞争（节点数越多浪费越多）

### 2. 调度中心选举模式（Leader 选举）

```
仅 Leader 节点负责任务调度，其他节点空闲。

选举方式：ZooKeeper / etcd / Redis 的 RedLock

实现：
  ZooKeeper 创建临时节点 /scheduler/master
  抢到节点的成为 Leader
  Leader 挂了，临时节点消失，其他节点自动补位
```

```java
@Component
public class LeaderElectionService {

    @Autowired private ZooKeeper zkClient;

    private static final String MASTER_PATH = "/scheduler/master";
    private static final byte[] MASTER_DATA = getCurrentNodeId().getBytes();

    @PostConstruct
    public void elect() {
        try {
            // 尝试创建临时节点，只有一个能成功
            zkClient.create(MASTER_PATH, MASTER_DATA,
                ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.EPHEMERAL);
            log.info("[Scheduler] This node {} became leader", getCurrentNodeId());
        } catch (KeeperException.NodeExistsException e) {
            log.info("[Scheduler] Another node is leader, watching...");
            // 注册 Watcher，Leader 挂了时重新选举
            zkClient.exists(MASTER_PATH, new LeaderWatcher());
        } catch (Exception e) {
            log.error("Failed to elect leader", e);
        }
    }

    private class LeaderWatcher implements Watcher {
        @Override
        public void process(WatchedEvent event) {
            if (event.getType() == Event.EventType.NodeDeleted) {
                elect(); // Leader 挂了，重新竞争
            }
        }
    }
}
```

### 3. 任务分片（并行执行）

```
场景：数据导出任务，单机太慢，需要分片并行处理

实现思路：
  将任务按维度分 N 片，每片由一个执行器节点处理
  调度中心下发分片参数给各节点
```

```java
// 任务定义时声明分片参数
@XxlJob("dataExportJob")
public ReturnT<String> execute(ShardingVO shardingVO) {
    int index = shardingVO.getIndex();   // 当前分片编号
    int total = shardingVO.getTotal();    // 总分片数

    // 按分片维度处理数据
    // 比如：导出用户表 100 万数据
    // 分片 0: 处理 ID % 4 == 0 的用户（0, 4, 8...）
    // 分片 1: 处理 ID % 4 == 1 的用户（1, 5, 9...）
    List<User> users = userMapper.selectByModulo(index, total);

    for (User user : users) {
        exportUserData(user);
    }

    return ReturnT.SUCCESS;
}
```

---

## 四、任务存储设计

### MySQL 表结构

```sql
-- 任务定义表
CREATE TABLE `scheduled_task` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `task_name`       VARCHAR(128) NOT NULL COMMENT '任务名称',
    `task_key`        VARCHAR(128) NOT NULL UNIQUE COMMENT '任务唯一标识',
    `cron_expression` VARCHAR(64)  NOT NULL COMMENT 'Cron 表达式',
    `route_strategy`  VARCHAR(32)  NOT NULL DEFAULT 'FIRST' COMMENT '路由策略: FIRST/RANDOM/ROUND',
    `sharding_count`  INT          NOT NULL DEFAULT 1 COMMENT '分片数',
    `executor_key`    VARCHAR(64)  NOT NULL COMMENT '执行器标识',
    `handler_class`   VARCHAR(255) NOT NULL COMMENT '任务处理类',
    `params`          TEXT NULL COMMENT '任务参数(JSON)',
    `misfire_policy`  VARCHAR(16)  NOT NULL DEFAULT 'FIRE_ONCE' COMMENT '错过策略: FIRE_ONCE/DISCARD/SFIRE_NEXT',
    `status`          TINYINT       NOT NULL DEFAULT 1 COMMENT '1-启用 0-禁用',
    `next_fire_time`  DATETIME NULL COMMENT '下次触发时间',
    `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_next_fire` (`next_fire_time`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 执行日志表
CREATE TABLE `task_execution_log` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `task_id`         BIGINT NOT NULL,
    `executor_node`   VARCHAR(64) NOT NULL COMMENT '执行的节点ID',
    `sharding_index`  INT NOT NULL DEFAULT 0 COMMENT '分片编号',
    `status`          TINYINT NOT NULL COMMENT '0-进行中 1-成功 2-失败',
    `start_time`      DATETIME NOT NULL,
    `end_time`        DATETIME NULL,
    `duration_ms`     INT NULL COMMENT '执行耗时(ms)',
    `result`          TEXT NULL COMMENT '执行结果/错误信息',
    `created_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_task_time` (`task_id`, `start_time`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 任务执行器注册表
CREATE TABLE `task_executor` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT,
    `node_id`         VARCHAR(64) NOT NULL UNIQUE COMMENT '节点唯一ID',
    `host`            VARCHAR(64) NOT NULL COMMENT 'IP',
    `port`            INT NOT NULL COMMENT 'RPC 端口',
    `heartbeat_time`  DATETIME NOT NULL,
    `status`          TINYINT NOT NULL DEFAULT 1 COMMENT '1-在线 0-离线',
    INDEX `idx_heartbeat` (`heartbeat_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 五、调度中心实现

### Cron 表达式解析

```java
// 使用 Quartz 的 CronExpression 解析
import org.quartz.CronExpression;

public class CronParser {
    /**
     * 解析 Cron 表达式，计算下次触发时间
     */
    public static LocalDateTime getNextFireTime(String cron, LocalDateTime from) {
        try {
            CronExpression ce = new CronExpression(cron);
            ce.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));
            java.util.Date next = ce.getNextValidTimeAfter(
                Timestamp.valueOf(from)
            );
            return next != null ? next.toInstant()
                .atZone(ZoneId.systemDefault()).toLocalDateTime() : null;
        } catch (ParseException e) {
            throw new IllegalArgumentException("Invalid cron: " + cron, e);
        }
    }

    /**
     * 校验 Cron 表达式的合法性
     */
    public static boolean isValid(String cron) {
        try {
            new CronExpression(cron);
            return true;
        } catch (ParseException e) {
            return false;
        }
    }
}
```

### 任务路由策略

```java
public enum RouteStrategy {
    /**
     * 第一个在线的执行器
     */
    FIRST {
        @Override
        public String select(List<TaskExecutor> executors) {
            return executors.get(0).getNodeId();
        }
    },

    /**
     * 随机选择一个在线执行器
     */
    RANDOM {
        @Override
        public String select(List<TaskExecutor> executors) {
            return executors.get(new Random().nextInt(executors.size())).getNodeId();
        }
    },

    /**
     * 轮询选择
     */
    ROUND {
        private final AtomicInteger idx = new AtomicInteger(0);

        @Override
        public String select(List<TaskExecutor> executors) {
            int i = idx.getAndIncrement() % executors.size();
            return executors.get(i).getNodeId();
        }
    },

    /**
     * 哈希选择（同一任务参数 → 同一执行器）
     */
    CONSISTENT_HASH {
        @Override
        public String select(List<TaskExecutor> executors, String taskKey) {
            int hash = taskKey.hashCode();
            int idx = Math.abs(hash % executors.size());
            return executors.get(idx).getNodeId();
        }
    }
}
```

---

## 六、执行器集群心跳

```
执行器启动时注册，运行时定时心跳，宕机后超时自动剔除。

心跳间隔：10 秒
心跳超时：30 秒（超过 30 秒没收到心跳，调度中心认为该节点离线）
```

```java
@Component
@Slf4j
public class ExecutorHeartbeat {

    @Autowired private TaskMapper taskMapper;
    @Autowired private RedisTemplate<String, String> redisTemplate;

    private static final String HEARTBEAT_KEY = "executor:heartbeat:";
    private static final long HEARTBEAT_TTL = 30L;

    /**
     * 执行器启动时注册
     */
    public void register(String nodeId, String host, int port) {
        TaskExecutor executor = new TaskExecutor();
        executor.setNodeId(nodeId);
        executor.setHost(host);
        executor.setPort(port);
        executor.setHeartbeatTime(LocalDateTime.now());
        taskMapper.insertOrUpdateExecutor(executor);

        // Redis TTL 保证自动清理离线节点
        redisTemplate.opsForValue().set(
            HEARTBEAT_KEY + nodeId,
            String.valueOf(System.currentTimeMillis()),
            Duration.ofSeconds(HEARTBEAT_TTL * 2)
        );

        log.info("[Executor] Registered: nodeId={}, host={}:{}", nodeId, host, port);
    }

    /**
     * 定时心跳上报
     */
    @Scheduled(fixedRate = 10_000)
    public void heartbeat() {
        String nodeId = getCurrentNodeId();
        redisTemplate.opsForValue().set(
            HEARTBEAT_KEY + nodeId,
            String.valueOf(System.currentTimeMillis()),
            Duration.ofSeconds(HEARTBEAT_TTL)
        );
    }
}
```

---

## 七、任务执行保障

### 1. 失败重试

```java
@Slf4j
public class TaskExecutionService {

    // 最多重试 3 次，间隔 1 分钟、5 分钟、30 分钟
    private static final int MAX_RETRY = 3;
    private static final long[] RETRY_INTERVALS = {60_000, 300_000, 1_800_000};

    public void execute(TaskDO task) {
        int retryCount = 0;
        Exception lastException = null;

        while (retryCount <= MAX_RETRY) {
            try {
                // 执行任务
                executeInternal(task);
                log.info("[Task] Success: taskId={}, attempt={}", task.getId(), retryCount + 1);
                return;
            } catch (Exception e) {
                lastException = e;
                retryCount++;
                log.warn("[Task] Failed: taskId={}, attempt={}, msg={}",
                    task.getId(), retryCount, e.getMessage());

                if (retryCount <= MAX_RETRY) {
                    try {
                        Thread.sleep(RETRY_INTERVALS[retryCount - 1]);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        }

        // 全部重试失败，告警 + 记录
        alertFailure(task, lastException);
    }
}
```

### 2. 任务超时控制

```java
public class TaskExecutionService {

    private static final long DEFAULT_TIMEOUT_MS = 30 * 60 * 1000; // 30 分钟

    public ExecutionResult executeWithTimeout(TaskDO task, long timeoutMs) {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<ExecutionResult> future = executor.submit(() -> executeInternal(task));

        try {
            return future.get(timeoutMs, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            future.cancel(true);
            log.error("[Task] Timeout: taskId={}, timeout={}ms", task.getId(), timeoutMs);
            throw new TaskTimeoutException("Task execution timeout: " + task.getId());
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            executor.shutdown();
        }
    }
}
```

### 3. 幂等执行

```
任务执行前，先在 Redis 写一个"执行中"的标记
SETNX task:running:{taskId} {startTime} EX 任务超时时间

如果标记已存在，说明上一次还没执行完，跳过本次（防止重复触发）
```

```java
public boolean tryAcquire(TaskDO task) {
    String key = "task:running:" + task.getId();
    Boolean success = redisTemplate.opsForValue()
        .setIfAbsent(key, String.valueOf(System.currentTimeMillis()),
            Duration.ofSeconds(task.getTimeoutSeconds()));
    return Boolean.TRUE.equals(success);
}

public void release(TaskDO task) {
    redisTemplate.delete("task:running:" + task.getId());
}
```

---

## 八、业界方案对比

| 方案 | 特点 | 适用场景 |
|------|------|---------|
| **XXL-Job** | 轻量、支持分片、社区活跃、Web UI 完善 | 中小型公司首选 |
| **PowerJob** | 支持 DAG 任务流、MapReduce、Java SDK 友好 | 复杂任务编排 |
| **ElasticJob** |  基于 ShardingSphere，轻量级 | 简单分片任务 |
| **Quartz** | Java 原生，依赖 DB + 集群节点抢锁 | 需要深度定制 |
| **自研** | 完全可控，定制化强 | 特殊业务需求 |

**XXL-Job 架构（最常用）：**

```
调度中心（Admin Web）
    │
    ├─ 读取任务配置，计算触发时间
    ├─ 通过 RPC 调度执行器
    └─ 管理执行日志

执行器集群（执行 JobHandler）
    │
    ├─ 注册到调度中心
    ├─ 接收调度指令
    └─ 汇报执行结果
```

---

## 九、高频面试题

**Q1: 分布式调度和单机 Cron 的核心区别是什么？**
> 单机 Cron 由 OS 触发，节点挂了任务就停了。分布式调度通过抢锁或选举机制保证任务不重复执行，任意节点可接替，且有统一的任务管理、执行日志和监控告警。

**Q2: 如何保证任务不重复执行？**
> ① 调度前抢 Redis 分布式锁（SETNX + TTL），抢到的才执行；② 任务执行前写"执行中"标记（幂等控制）；③ 执行完成后才释放锁。锁过期时间要大于任务最大执行时间。

**Q3: 任务挂了怎么办？**
> 失败重试机制：默认重试 3 次，间隔递增（1min → 5min → 30min）。重试全部失败后告警，任务状态标记失败，等待人工介入或下次调度。

**Q4: 分片任务如何保证每个分片都执行？**
> 调度中心将任务按分片数 N 拆成 N 个子任务，分别触发。每个执行器节点收到自己的分片参数后，只处理对应维度的数据。通过 Redis Set 记录每个分片的完成状态，全部完成才算成功。

**Q5: 为什么基于数据库的调度有性能瓶颈？**
> 所有节点轮询查询"哪些任务到时间了"，DB 压力大。而且轮询间隔受限于 DB 性能（最短 1-2 秒）。推荐用 Redis Sorted Set，按触发时间排序，轮询改为 ZRANGEBYSCORE 取最小时间戳，减少 DB 压力。

---

**参考链接：**
- [XXL-Job 官方文档](https://www.xuxueli.com/xxl-job/)
- [PowerJob 官方文档](https://www.yuque.com/powerjob/guidence)
- [分布式任务调度设计思路](https://tech.meituan.com/2018/10/17/distributed-task-scheduling-platform.html)
