---
layout: default
title: Raft 一致性协议详解 ⭐⭐⭐
---
# Raft 一致性协议详解 ⭐⭐⭐

## 🎯 面试题：什么是 Raft？它是如何工作的？

> Raft 是用于管理日志复制的一致性算法，核心目标是**易于理解**。通过领导者（Leader）、追随者（Follower）、候选者（Candidate）三种角色实现分布式一致性。相比 Paxos，Raft 更易于工程实现，是 etcd、Kubernetes 等主流系统的共识基础。

---

## 一、Raft 三种角色

```
┌──────────────────────────────────────────────────────────┐
│                    Raft 集群角色状态机                      │
│                                                          │
│   Follower ←───── election timeout ──────→ Candidate    │
│      ↑                                    ↘              │
│      │                                    ↘  赢得多数票   │
│      │                                  ↘               │
│      ←─────── 心跳或新 Leader ────────── Leader          │
│                                                          │
│  Follower  ：被动接收请求，只响应 Leader 和 Candidate     │
│  Candidate ：发起选举时角色，可升级为 Leader              │
│  Leader    ：处理所有客户端请求，向 Follower 同步日志     │
└──────────────────────────────────────────────────────────┘
```

### 角色职责

| 角色 | 职责 | 关键词 |
|------|------|-------|
| **Leader** | 接收客户端请求，日志复制 | 唯一处理写请求 |
| **Follower** | 被动响应，超时发起选举 | 投票、接收日志 |
| **Candidate** | 选举中的临时角色 | 争取多数票 |

---

## 二、领导人选举（Leader Election）

### 触发条件

```
Follower 在 election timeout（150~300ms 随机）内
没收到 Leader 的心跳 → 认为自己 leader 不存在
→ 发起选举，转为 Candidate
```

### 选举流程

```
1. Candidate  term + 1（term 任期号递增）
2. 给自己投票
3. 向所有节点发送 RequestVote RPC
4. 等待响应：

   情况 A：收到多数票
          → 成为新的 Leader
          → 立即向所有节点发送心跳（AppendEntries 空日志）
          → 阻止新选举

   情况 B：收到任期更新的 Leader 的心跳
          → 发现对方 term >= 自己 term
          → 承认对方为 Leader，自己退回 Follower

   情况 C：选举超时无人胜出（split vote 平票）
          → term + 1，重新发起选举
          → 随机退避避免再次平票
```

### 投票规则（Vote）

```
能投票给 Candidate 的条件（必须同时满足）：
  ① 没投过票（每个 term 最多投一票）
  ② Candidate 的 lastLogTerm > 自己的 lastLogTerm
     或 Candidate 的 lastLogTerm == 自己的 lastLogTerm
     且 Candidate 的 lastLogIndex >= 自己的 lastLogIndex
```

**这两条规则保证了：选举出的 Leader 一定包含所有已提交的日志。**

### 选举超时（Election Timeout）

```
随机范围：150ms ~ 300ms
随机目的：避免多个 Follower 同时发起选举导致 split vote

心跳间隔（heartbeat interval）：
  通常 = election timeout 的 1/10 ~ 1/5
  Leader 定期发送心跳维持领导地位
```

### Java 实现简版

```java
public class RaftNode {

    private final int nodeId;
    private volatile RaftRole role = RaftRole.FOLLOWER;
    private volatile long currentTerm = 0;
    private volatile Integer votedFor = null;         // 投给了谁
    private volatile long lastHeartbeat = 0;          // 最后心跳时间

    // 选举超时时间（随机 150~300ms）
    private final Random random = new Random();
    private long electionTimeoutMs;

    @Scheduled(fixedRate = 10)
    public void tick() {
        if (role == RaftRole.LEADER) {
            // Leader 发送心跳
            sendHeartbeat();
        } else {
            // 检查选举超时
            if (System.currentTimeMillis() - lastHeartbeat > electionTimeoutMs) {
                startElection();
            }
        }
    }

    private void startElection() {
        currentTerm++;
        role = RaftRole.CANDIDATE;
        votedFor = nodeId;          // 给自己投一票
        int votes = 1;               // 自己的票

        // 并行向所有节点发 RequestVote
        for (int peerId : peers) {
            CompletableFuture<Boolean> future = sendRequestVote(peerId);
            future.thenAccept(granted -> {
                if (granted) votes++;
                if (votes > peers.size() / 2) {
                    // 赢得选举
                    becomeLeader();
                }
            });
        }
    }

    private void becomeLeader() {
        role = RaftRole.LEADER;
        System.out.println("Node " + nodeId + " became Leader, term=" + currentTerm);
        // 立即发心跳，阻止其他节点发起新选举
        sendHeartbeat();
    }

    // 处理 RequestVote RPC
    public boolean handleRequestVote(int term, int candidateId,
                                      long lastLogTerm, long lastLogIndex) {
        if (term > currentTerm) {
            currentTerm = term;
            role = RaftRole.FOLLOWER;
            votedFor = null;
        }

        boolean canVote = (votedFor == null || votedFor == candidateId)
                && (lastLogTerm > getLastLogTerm()
                   || (lastLogTerm == getLastLogTerm() && lastLogIndex >= getLastLogIndex()));

        if (canVote) {
            votedFor = candidateId;
            return true;
        }
        return false;
    }
}
```

---

## 三、日志复制（Log Replication）

### 日志结构

```
每个节点维护一个日志数组：

Index:   1    2    3    4    5    6    7    8
Term:    1    1    1    2    2    3    3    3
Cmd:   cmdA cmdB cmdC cmdD cmdE cmdF cmdG cmdH
        ↑                        ↑
     已复制到多数节点            已提交(committed)
     但未提交                    ✅

已提交 = 被多数节点复制过的日志，Leader 可以安全执行
```

### AppendEntries RPC

```
客户端请求 → Leader 追加本地日志
           → 并行发 AppendEntries RPC 给所有 Follower
           → 等待多数节点响应成功
           → Leader 本地提交（applied）
           → 通知 Follower 提交

Leader 同时维护 nextIndex[] 和 matchIndex[]：
  nextIndex[i]：下一个要发送给 Follower i 的日志索引
  matchIndex[i]：Follower i 已复制的最高日志索引
```

### 日志一致性与修复

```
问题：Follower 日志可能出现"空洞"或"冲突"

┌─────────────────────────────────────────┐
│ Leader 日志: [1,1] [2,1] [3,2] [4,2]    │
│ Follower:  [1,1] [2,1]     [4,2] [5,2] │ ← 缺少 [3,2]，多了 [5,2]
│                                              冲突：位置3对应不同命令
└─────────────────────────────────────────┘

解决：Leader 通过递减 nextIndex[i] 找到冲突点，
      然后从该点起覆盖 Follower 的日志

具体过程：
  1. Leader 发 AppendEntries(prevIndex=3, prevTerm=2, entries=[4,2])
  2. Follower 发现位置 3 的 term 不匹配，拒绝
  3. Leader nextIndex[Follower]-- → nextIndex=3
  4. 重试，直到成功
```

```java
// Leader 向 Follower 同步日志
public void replicateToFollower(int followerId) {
    long nextIdx = nextIndex.get(followerId);
    long prevLogIndex = nextIdx - 1;
    long prevLogTerm = getLogTerm(prevLogIndex);

    List<LogEntry> entries = logs.subList((int)nextIdx, logs.size());

    AppendEntriesRpc rpc = AppendEntriesRpc.builder()
        .term(currentTerm)
        .leaderId(nodeId)
        .prevLogIndex(prevLogIndex)
        .prevLogTerm(prevLogTerm)
        .entries(entries)
        .leaderCommit(commitIndex)
        .build();

    boolean success = sendAppendEntries(followerId, rpc);

    if (success) {
        // 同步成功，推进 matchIndex
        nextIndex.put(followerId, nextIdx + entries.size());
        matchIndex.put(followerId, nextIdx + entries.size() - 1);
    } else {
        // 日志不一致，退回重试
        nextIndex.put(followerId, nextIndex.get(followerId) - 1);
    }
}

// Follower 处理 AppendEntries RPC
public boolean handleAppendEntries(AppendEntriesRpc rpc) {
    // 1. 任期检查
    if (rpc.getTerm() < currentTerm) return false;
    if (rpc.getTerm() > currentTerm) {
        currentTerm = rpc.getTerm();
        becomeFollower();
    }

    // 2. 日志匹配检查
    if (rpc.getPrevLogIndex() > 0) {
        LogEntry entry = getLog(rpc.getPrevLogIndex());
        if (entry == null || entry.term != rpc.getPrevLogTerm()) {
            return false; // 一致性检查失败
        }
    }

    // 3. 覆盖冲突日志
    for (LogEntry entry : rpc.getEntries()) {
        long idx = rpc.getPrevLogIndex() + 1 + rpc.getEntries().indexOf(entry);
        if (idx < logs.size() && logs.get((int)idx).term != entry.term) {
            logs.subList((int)idx, logs.size()).clear(); // 删除冲突日志
        }
        if (idx >= logs.size()) {
            logs.add(entry);
        }
    }

    // 4. 更新 commitIndex
    if (rpc.getLeaderCommit() > commitIndex) {
        commitIndex = Math.min(rpc.getLeaderCommit(), logs.size() - 1);
    }
    return true;
}
```

### 提交规则

```
已提交日志必须满足：
  ① 被多数节点写入本地日志
  ② 所在 term 的 Leader 已提交

⚠️ 注意：
  Leader 不能仅通过"多数节点确认"就提交上一任期的日志！
  必须等待当前任期的日志被复制到多数节点后才能提交。

证明：如果 Leader 只看了多数节点就提交上一 term 日志，
      可能因网络分区导致被覆盖，违反一致性。
```

---

## 四、安全性保证

### Raft 的 5 条安全性规则

```
规则 1：选举约束（Election Restriction）
  Follower 只投票给比自己日志新的 Candidate
  → 保证新 Leader 包含所有已提交日志

规则 2：Leader 只追加日志（Append-Only）
  Leader 永远不会覆盖或删除自己的日志
  → 只能追加

规则 3：日志匹配（Log Matching）
  如果两个节点的日志在某个索引相同 → 之前所有条目也相同
  → 通过 AppendEntries 一致性检查保证

规则 4：Leader 完整性（Leader Completeness）
  如果一条日志在某个 term 被提交 → 所有后续 Leader 都包含该日志
  → 由规则 1 和规则 3 共同保证

规则 5：状态机安全（State Machine Safety）
  如果节点已应用了某个索引的日志 → 其他节点不会在同一索引应用不同日志
  → 保证了所有节点执行相同序列的状态机命令
```

### 任期（Term）的意义

```
Term = 逻辑时钟，递增整数

作用：
  ① 判断谁是最新 Leader（term 更大优先）
  ② 识别过期请求
  ③ 区分不同选举轮次

通信时附上 term：
  - 如果节点 term < 对方 term → 立即更新自己的 term
  - 如果 Leader/Candidate term < Follower term → 退回 Follower
```

---

## 五、成员变更（Joint Consensus）

### 问题：直接切换配置有风险

```
旧配置：3 节点 {A, B, C}
新配置：3 节点 {A, B, D}

如果出现 {A, B} 和 {C} 两个多数派同时存在？
→ 可能选出两个 Leader，脑裂

┌──────────────────────────────────────────┐
│  时间线：                                │
│  t1: 旧配置 {A,B,C}                      │
│  t2: C 被添加到配置 {A,B,C,D}            │
│      但 D 还没同步配置                    │
│      如果此时 C 认为 A,B,D 是多数派？     │
│      就可能选出第二个 Leader ❌           │
└──────────────────────────────────────────┘
```

### 解决方案：两阶段成员变更（Joint Consensus）

```
阶段一：Cold ∪ Cnew（过渡配置）
  所有节点使用 Cold ∪ Cnew 配置
  新节点以 LogEntry 形式写入日志，异步同步配置
  多数派 = Cold∩多数 ∪ Cnew∩多数（重叠保证）

阶段二：Cnew（最终配置）
  新配置生效
  旧节点可以下线
```

```
配置变更流程：
  Leader 收到成员变更请求
    ↓
  追加 Cold∪Cnew 日志，广播给所有节点
    ↓
  收到 Cold∪Cnew 多数确认 → 追加 Cnew 日志
    ↓
  收到 Cnew 多数确认 → 新配置生效

期间如果 Leader 挂了，新 Leader 可能是 Cold 或 Cnew 节点，
最终都会收敛到 Cnew。
```

---

## 六、日志压缩与快照（Log Compaction）

### 问题

```
日志无限增长 → 内存耗尽、重启太慢

解决方案：快照（Snapshot）
  将已提交的状态机数据写入快照文件
  删除快照之前的日志
```

### 快照内容

```
快照文件 = 状态机数据 + 最后日志 term + 最后日志 index

快照后的状态：
  已持久化：快照文件
  已应用：0 ~ snapshotIndex
  未应用：snapshotIndex ~ commitIndex
  未复制：commitIndex ~ lastIndex
```

### 快照同步

```
新节点加入时，Leader 通过 InstallSnapshot RPC 发送快照

Follower 收到快照后：
  1. 如果快照覆盖自己的日志 → 清空本地日志
  2. 加载快照数据到状态机
  3. 更新 commitIndex 和 lastApplied
```

---

## 七、与 Paxos 对比

| 维度 | Raft | Paxos |
|------|------|-------|
| **易理解性** | ✅ 强项，拆分清晰 | ❌ 难以理解 |
| **角色划分** | Leader/Follower/Candidate 明确 | 无固定角色 |
| **日志复制** | 强 Leader，线性复制 | 多 Paxos 实例 |
| **成员变更** | 两阶段 Joint Consensus | 理论完善但难实现 |
| **工程落地** | ✅ etcd、Kubernetes、RocketMQ | Chubby、ZooKeeper |
| **效率** | 与 Raft 相当 | 相当 |
| **正确性证明** | 论文有完整证明 | 原始论文过于简洁 |

---

## 八、高频面试题

**Q1: Raft 如何保证选出的 Leader 一定包含所有已提交日志？**
> 通过选举限制（Election Restriction）：Follower 只投票给比自己日志新的 Candidate。"更新"的标准是 lastLogTerm 更大，或 lastLogTerm 相同但 lastLogIndex 更长。如果 Candidate 缺少已提交日志，它的 lastLog 就不够新，无法获得多数票，因此不可能当选。

**Q2: 什么是脑裂？如何避免？**
> 脑裂是网络分区导致多个节点同时认为自己是 Leader。Raft 通过任期号（Term）解决：Term 小的 Leader 自动降级为 Follower。分区中 Term 较小的 Leader 因无法获得多数票确认，无法提交任何日志，不会产生数据冲突。当网络恢复后，Term 较大的新 Leader 上台，旧的 Leader 检测到 term 更低，自动退位。

**Q3: Raft 的日志提交和普通日志复制有什么区别？**
> 普通日志复制只是把日志复制到 Follower（AppendEntries 成功），此时日志是"已复制但未提交"。只有当 Leader 确认某条日志被**多数节点**写入后，这条日志才是"已提交"（committed），Leader 才能执行并通知 Follower 应用。更关键的是，Leader 不能通过多数确认来提交前任期的日志，必须等当前任期的日志被复制后才能提交。

**Q4: Leader 挂了，新 Leader 是怎么选出来的？**
> Follower 超时 → 发起选举（term+1），向所有节点发 RequestVote。节点收到请求后按投票规则决定是否投票。Candidate 获得多数票 → 成为新 Leader，立即发心跳阻止其他节点发起新选举。如果没人拿到多数票，选举超时后 term 再递增，重新发起选举。

**Q5: 日志不一致时 Raft 如何修复？**
> Leader 通过递减 nextIndex 重试 AppendEntries。Follower 收到 AppendEntries 后做一致性检查（prevLogIndex 和 prevLogTerm 是否匹配），不匹配就拒绝。Leader 收到拒绝后 nextIndex--，重发直到成功。成功后就从冲突点开始覆盖 Follower 的日志，保证两者最终一致。

**Q6: 为什么 Raft 不用 Paxos？**
> Paxos 的论文晦涩难懂，工程实现极难（Chubby 作者曾说"实现 Paxos 很难"）。Raft 将问题拆解为三个独立子问题（领导选举、日志复制、安全性），每一步都有明确的操作指引，更容易正确实现。etcd、Kubernetes 等项目都选择 Raft 而非 Paxos。

**Q7: Raft 能做到线性一致（Linearizable）吗？**
> 可以。Raft 本身保证了线性一致的日志复制，但客户端交互需要额外保证：① 客户端每次请求带上唯一序列号，防止 Leader 响应延迟导致重复执行；② Leader 记录已处理的序列号，重复请求直接返回之前的结果而不重新执行；③ 客户端在发现 Leader 变更后，要重新查询当前 Leader。

**Q8: 日志压缩（快照）的触发时机是什么？**
> 两种触发方式：① 按日志长度：当日志大小超过阈值（如 64MB 或 10 万条）触发快照；② 按时间：定期触发（如每小时）。快照生成时写入磁盘，之后删除快照点之前的日志，重启时加载快照 + 重放之后的日志即可恢复状态。

---

**参考链接：**
- [Raft 论文（In Search of an Understandable Consensus Algorithm）](https://raft.github.io/raft.pdf)
- [Raft 可视化动画](https://thesecretlivesofdata.com/raft/)
- [etcd Raft 实现解析](https://blog.heptio.com/raft/)
