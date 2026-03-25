# 分布式一致性

> 分布式系统的一致性问题

## 🎯 面试重点

- 一致性模型
- Paxos / Raft

## 📖 一致性模型

```java
/**
 * 一致性模型
 */
public class ConsistencyModels {
    // 强一致性
    /*
     * 任何时刻所有节点看到相同数据
     * 例如：Zookeeper 的写操作
     */
    
    // 最终一致性
    /*
     * 一段时间后数据一致
     * 例如：DNS
     */
    
    // 因果一致性
    /*
     * 有因果关系的操作顺序一致
     */
}
```

## 📖 共识算法

```java
/**
 * Paxos
 */
public class Paxos {
    /*
     * 角色：
     * - Proposer 提议者
     * - Acceptor 接受者
     * - Learner 学习者
     */
}

/**
 * Raft
 */
public class Raft {
    /*
     * 角色：
     * - Leader 领导者
     * - Follower 跟随者
     * - Candidate 候选者
     */
}
```

## 📖 面试真题

### Q1: 强一致性和最终一致性的区别？

**答：** 强一致需要同步确认，最终一致允许暂时不一致。

---

**⭐ 重点：分布式一致性是分布式系统的核心问题**