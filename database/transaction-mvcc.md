# MySQL 事务与 MVCC 详解 ⭐⭐⭐

## 面试题：解释 MySQL 中的 ACID 属性，并说明 MVCC 的实现原理

### 核心回答

MySQL InnoDB 通过 **ACID 特性**保证事务的可靠性，通过 **MVCC（多版本并发控制）**实现高效的并发读写。

---

## 一、ACID 特性

### 1. 原子性（Atomicity）

**定义**：事务是一个不可分割的工作单位，要么全部成功，要么全部失败回滚。

**实现机制**：undo log（回滚日志）

```
事务执行过程：
1. 开始事务
2. 执行操作（同时记录 undo log）
   - 插入 → 记录删除操作
   - 删除 → 记录插入操作
   - 更新 → 记录旧值
3. 提交事务 → 清空 undo log
4. 回滚事务 → 执行 undo log 恢复数据
```

### 2. 一致性（Consistency）

**定义**：事务执行前后，数据库必须从一个一致性状态变为另一个一致性状态。

**保证方式**：
- 原子性 + 隔离性 + 持久性共同保证
- 数据库约束（外键、唯一约束等）
- 业务逻辑校验

### 3. 隔离性（Isolation）

**定义**：多个事务并发执行时，一个事务的执行不应影响其他事务。

**实现机制**：锁 + MVCC

### 4. 持久性（Durability）

**定义**：事务一旦提交，对数据库的修改就是永久的，即使系统故障也不会丢失。

**实现机制**：redo log（重做日志）

```
数据写入流程：
1. 修改内存中的数据页（Buffer Pool）
2. 写入 redo log（WAL 机制，先写日志再写磁盘）
3. 事务提交时，redo log 强制刷盘（fsync）
4. 后台线程异步将数据页刷盘

故障恢复：
- 重启时检查 redo log，将未刷盘的数据恢复
```

---

## 二、事务隔离级别

### 并发问题

| 问题 | 描述 | 示例 |
|------|------|------|
| **脏读** | 读到其他事务未提交的数据 | 事务 A 修改未提交，事务 B 读到修改后的值 |
| **不可重复读** | 同一事务内多次读取，结果不同 | 事务 A 两次读取之间，事务 B 修改并提交 |
| **幻读** | 同一事务内多次查询，结果集不同 | 事务 A 两次查询之间，事务 B 插入新记录 |

### 四种隔离级别

```sql
-- 查看隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 实现机制 |
|---------|------|-----------|------|---------|
| READ UNCOMMITTED | ✓ | ✓ | ✓ | 不加锁，直接读最新数据 |
| READ COMMITTED | ✗ | ✓ | ✓ | MVCC（每次查询生成新 ReadView） |
| REPEATABLE READ（默认） | ✗ | ✗ | ✓（部分解决） | MVCC（事务开始时生成 ReadView） |
| SERIALIZABLE | ✗ | ✗ | ✗ | 所有操作加排他锁 |

---

## 三、MVCC 多版本并发控制

### 核心思想

**读写不阻塞**：写操作生成新版本数据，读操作根据版本号读取历史版本。

```
数据存储结构（每行记录隐藏字段）：

| DB_TRX_ID | DB_ROLL_PTR | 列1 | 列2 | ... |
|-----------|-------------|-----|-----|-----|

- DB_TRX_ID：最后修改该记录的事务 ID
- DB_ROLL_PTR：回滚指针，指向 undo log
```

### undo log 版本链

```
事务 100：update age=20 → 事务 200：update age=30

当前记录：age=30, trx_id=200, roll_ptr → undo log
                                ↓
                         undo log：age=20, trx_id=100, roll_ptr → undo log
                                                ↓
                                          undo log：age=18, trx_id=null（初始值）
```

### ReadView（读视图）

**作用**：判断当前事务可见哪个版本的数据。

**结构**：
```
ReadView {
    m_ids: [100, 200]          // 生成 ReadView 时活跃的事务 ID 列表
    min_trx_id: 100            // 最小活跃事务 ID
    max_trx_id: 201            // 下一个分配的事务 ID（最大事务 ID + 1）
    creator_trx_id: 50         // 创建该 ReadView 的事务 ID
}
```

**可见性判断规则**：

对于某条记录的 trx_id：
1. **trx_id == creator_trx_id**：当前事务修改的，可见
2. **trx_id < min_trx_id**：在 ReadView 生成前已提交，可见
3. **trx_id >= max_trx_id**：在 ReadView 生成后启动，不可见
4. **min_trx_id <= trx_id < max_trx_id**：
   - 如果 trx_id 在 m_ids 中：未提交，不可见
   - 如果 trx_id 不在 m_ids 中：已提交，可见

### 不同隔离级别的 MVCC 实现

#### READ COMMITTED（读已提交）

**特点**：每次查询都生成新的 ReadView

```
事务 A（trx_id=100）：
    SELECT * FROM user WHERE id=1;  -- 生成 ReadView1，看到已提交数据
    
    -- 事务 B 修改并提交
    
    SELECT * FROM user WHERE id=1;  -- 生成 ReadView2，看到 B 修改后的数据（不可重复读）
```

#### REPEATABLE READ（可重复读）

**特点**：事务开始时生成 ReadView，整个事务期间复用

```
事务 A（trx_id=100）：
    START TRANSACTION;  -- 生成 ReadView
    
    SELECT * FROM user WHERE id=1;  -- 使用 ReadView，看到数据版本 V1
    
    -- 事务 B 修改并提交
    
    SELECT * FROM user WHERE id=1;  -- 仍使用 ReadView，看到数据版本 V1（可重复读）
```

### MVCC 解决幻读？

**快照读（普通 SELECT）**：MVCC 解决幻读
```sql
-- 事务 A
START TRANSACTION;
SELECT * FROM user WHERE age > 18;  -- 结果：3 条记录（生成 ReadView）

-- 事务 B 插入一条 age=20 的记录并提交

SELECT * FROM user WHERE age > 18;  -- 结果：仍是 3 条（使用相同 ReadView）
```

**当前读（SELECT FOR UPDATE）**：MVCC 不能解决幻读，需要 Gap Lock
```sql
-- 事务 A
START TRANSACTION;
SELECT * FROM user WHERE age > 18 FOR UPDATE;  -- 加间隙锁

-- 事务 B 插入 age=20 的记录 → 阻塞等待

SELECT * FROM user WHERE age > 18 FOR UPDATE;  -- 结果：4 条记录
```

---

## 四、锁机制

### 锁类型

#### 按粒度分

| 锁类型 | 描述 | 使用场景 |
|--------|------|---------|
| 行锁 | 锁定单行记录 | InnoDB 默认，高并发 |
| 表锁 | 锁定整个表 | MyISAM 默认，DDL 操作 |
| 页锁 | 锁定数据页 | BDB 存储引擎 |

#### 按功能分

| 锁类型 | 描述 | 兼容性 |
|--------|------|--------|
| 共享锁（S 锁） | 读锁，允许多个事务同时读 | 与 S 锁兼容，与 X 锁冲突 |
| 排他锁（X 锁） | 写锁，禁止其他事务读写 | 与 S 锁、X 锁都冲突 |

#### InnoDB 行锁算法

| 锁类型 | 描述 | 示例 |
|--------|------|------|
| Record Lock | 锁定单个记录 | `WHERE id = 1` |
| Gap Lock | 锁定索引间隙，防止幻读 | `WHERE id > 5 AND id < 10` |
| Next-Key Lock | Record Lock + Gap Lock | 默认行锁算法 |

### 锁兼容性矩阵

|  | S 锁 | X 锁 |
|--|------|------|
| S 锁 | 兼容 | 冲突 |
| X 锁 | 冲突 | 冲突 |

---

## 五、高频面试题

**Q1: ACID 的实现原理？**

| 特性 | 实现机制 |
|------|---------|
| 原子性 | undo log |
| 一致性 | 原子性 + 隔离性 + 持久性 + 约束 |
| 隔离性 | 锁 + MVCC |
| 持久性 | redo log |

**Q2: MVCC 解决了什么问题？**

1. **读写不阻塞**：读操作不需要加锁，提高并发性能
2. **实现非阻塞读**：SELECT 操作不会被写操作阻塞
3. **实现可重复读**：通过 ReadView 保证同一事务内多次读取结果一致

**Q3: 为什么 REPEATABLE READ 下还会幻读？**

- **快照读**：MVCC 解决幻读（使用 ReadView）
- **当前读**：`SELECT FOR UPDATE` 读取最新数据，需要 Gap Lock 解决幻读

**Q4: redo log 和 undo log 的区别？**

| 特性 | redo log | undo log |
|------|---------|---------|
| 作用 | 保证持久性，故障恢复 | 保证原子性，事务回滚 |
| 内容 | 物理日志，记录数据页修改 | 逻辑日志，记录反向操作 |
| 写入时机 | 事务执行过程中持续写入 | 事务执行过程中持续写入 |
| 清理时机 | 数据页刷盘后清理 | 事务提交后，无其他事务引用时清理 |

**Q5: 如何查看当前事务的锁情况？**

```sql
-- 查看锁等待
SELECT * FROM information_schema.INNODB_LOCK_WAITS;

-- 查看当前锁
SELECT * FROM information_schema.INNODB_LOCKS;

-- 查看事务状态
SELECT * FROM information_schema.INNODB_TRX;
```

---

**参考链接：**
- [MySQL事务的ACID详解-腾讯云](https://cloud.tencent.com/developer/article/2181381)
- [MySQL事务详解从ACID到MVCC-知乎](https://zhuanlan.zhihu.com/p/415377781)
