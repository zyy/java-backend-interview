---
layout: default
title: 一致性哈希（Consistent Hashing）
---

# 一致性哈希（Consistent Hashing）

> 一致性哈希是分布式系统中解决数据分片和负载均衡的核心算法，面试高频考点

## 🎯 面试重点

- 传统哈希取模的问题
- 一致性哈希的原理与实现
- 虚拟节点解决数据倾斜
- 实际应用场景（Redis、Nginx、分布式存储）

---

## 📖 一、传统哈希的问题

### 1.1 哈希取模算法

```java
// 传统方式：hash(key) % N
int serverIndex = hash(key) % serverCount;
String server = servers.get(serverIndex);
```

**问题：服务器数量变化时，几乎所有数据都要迁移**

```
初始：3 台服务器（N=3）
  key1 → hash(key1) % 3 = 0 → Server0
  key2 → hash(key2) % 3 = 1 → Server1
  key3 → hash(key3) % 3 = 2 → Server2
  key4 → hash(key4) % 3 = 0 → Server0

扩容：增加 1 台（N=4）
  key1 → hash(key1) % 4 = 1 → Server1 ❌（从 Server0 迁移）
  key2 → hash(key2) % 4 = 2 → Server2 ❌（从 Server1 迁移）
  key3 → hash(key3) % 4 = 3 → Server3 ❌（从 Server2 迁移）
  key4 → hash(key4) % 4 = 0 → Server0 ✅
  
结果：75% 的数据需要迁移！
```

### 1.2 问题总结

| 场景 | 影响 |
|-----|------|
| 服务器扩容 | 大量数据迁移，服务不可用 |
| 服务器缩容 | 大量数据迁移，缓存穿透 |
| 数据分布不均 | 某些服务器压力过大 |

---

## 📖 二、一致性哈希原理

### 2.1 核心思想

将数据和服务器都映射到一个**哈希环**上：

```
                    0 (2^32-1)
                    │
        Server A ●  │  ● Server D
                   │
    ● key1         │         ● key3
                   │
        Server B ●─┼─● Server C
                   │
              ● key2
                   │
```

**数据定位规则**：
- 计算 `hash(key)`，在环上顺时针找到第一个服务器
- 该服务器就是数据的存储位置

### 2.2 服务器变化时的影响

```
初始状态：
                    0
                    │
        Server A ●  │  ● Server C
              ↗     │     ↖
    ● key1 ─────────┼─────────● key3
                    │
        Server B ●──┼──● key2
                    │

Server B 宕机：
                    0
                    │
        Server A ●  │  ● Server C
              ↗     │     ↖
    ● key1 ─────────┼─────────● key3
                    │
           (B 宕机) │
                    │
              ● key2 → 顺时针找到 Server C
                    │

结果：只有 key2 需要迁移（从 B 到 C），其他数据不动！
```

**优势**：服务器变化时，只影响相邻节点的数据，大部分数据无需迁移。

### 2.3 数学证明

假设：
- 哈希环大小为 M（如 2^32）
- 有 N 台服务器
- 数据均匀分布

**传统哈希**：服务器变化时，迁移率 ≈ (N-1)/N → 接近 100%

**一致性哈希**：
- 每台服务器负责环上 1/N 的区域
- 增加/删除一台服务器，只影响 1/N 的数据
- 迁移率 ≈ 1/N → 如 10 台服务器，仅 10% 数据迁移

---

## 📖 三、一致性哈希实现

### 3.1 基础实现

```java
public class ConsistentHash {
    
    // 哈希环：TreeMap 自动排序
    private TreeMap<Integer, String> circle = new TreeMap<>();
    
    // 虚拟节点数（解决数据倾斜）
    private int virtualNodes = 150;
    
    // 添加服务器
    public void addServer(String server) {
        for (int i = 0; i < virtualNodes; i++) {
            // 每个服务器对应多个虚拟节点
            String virtualNode = server + "#" + i;
            int hash = hash(virtualNode);
            circle.put(hash, server);
        }
    }
    
    // 移除服务器
    public void removeServer(String server) {
        for (int i = 0; i < virtualNodes; i++) {
            String virtualNode = server + "#" + i;
            int hash = hash(virtualNode);
            circle.remove(hash);
        }
    }
    
    // 获取数据所在服务器
    public String getServer(String key) {
        if (circle.isEmpty()) {
            return null;
        }
        
        int hash = hash(key);
        
        // 顺时针找到第一个大于等于 hash 的节点
        Map.Entry<Integer, String> entry = circle.ceilingEntry(hash);
        
        // 如果没有，回到环的开头（第一个节点）
        if (entry == null) {
            entry = circle.firstEntry();
        }
        
        return entry.getValue();
    }
    
    // FNV1_32_HASH 算法
    private int hash(String key) {
        final int p = 16777619;
        int hash = (int) 2166136261L;
        for (int i = 0; i < key.length(); i++) {
            hash = (hash ^ key.charAt(i)) * p;
        }
        hash += hash << 13;
        hash ^= hash >> 7;
        hash += hash << 3;
        hash ^= hash >> 17;
        hash += hash << 5;
        
        // 确保非负
        if (hash < 0) {
            hash = Math.abs(hash);
        }
        return hash;
    }
}
```

### 3.2 使用示例

```java
public class ConsistentHashDemo {
    public static void main(String[] args) {
        ConsistentHash ch = new ConsistentHash();
        
        // 添加服务器
        ch.addServer("192.168.1.1");
        ch.addServer("192.168.1.2");
        ch.addServer("192.168.1.3");
        
        // 查看数据分布
        String[] keys = {"user:1", "user:2", "user:3", "user:4", "user:5"};
        for (String key : keys) {
            System.out.println(key + " → " + ch.getServer(key));
        }
        
        // 输出：
        // user:1 → 192.168.1.2
        // user:2 → 192.168.1.1
        // user:3 → 192.168.1.3
        // user:4 → 192.168.1.2
        // user:5 → 192.168.1.1
        
        // 移除一台服务器
        System.out.println("\n移除 192.168.1.2 后：");
        ch.removeServer("192.168.1.2");
        
        for (String key : keys) {
            System.out.println(key + " → " + ch.getServer(key));
        }
        
        // 输出：
        // user:1 → 192.168.1.3  (变了)
        // user:2 → 192.168.1.1  (没变)
        // user:3 → 192.168.1.3  (没变)
        // user:4 → 192.168.1.3  (变了)
        // user:5 → 192.168.1.1  (没变)
        // 只有 2/5 的数据需要迁移！
    }
}
```

---

## 📖 四、虚拟节点（Virtual Nodes）

### 4.1 数据倾斜问题

```
没有虚拟节点时：
                    0
                    │
        Server A ●  │
                    │
    ● key1          │
    ● key2          │
    ● key3          │
    ● key4          │
    ● key5          │
                    │
        Server B ●──┼──● Server C
                    │
                    │

问题：Server A 负责了 5 个 key，B 和 C 几乎没有 → 数据倾斜！
```

### 4.2 虚拟节点解决方案

```
使用虚拟节点（每台服务器 3 个虚拟节点）：
                    0
                    │
        A#0 ●       │       ● A#1
                    │
    ● key1          │         ● key3
                    │
        B#0 ●───────┼───────● B#1
              ● key2│
        C#0 ●       │       ● C#1
                    │
              ● key4│
                    │

结果：key1→A, key2→B, key3→A, key4→C  分布更均匀！
```

### 4.3 虚拟节点数量选择

| 场景 | 虚拟节点数 | 说明 |
|-----|-----------|------|
| 服务器少（<10） | 150-200 | 增加分布均匀性 |
| 服务器多（>50） | 50-100 | 减少内存占用 |
| 超大规模 | 10-50 | 平衡性能和均匀性 |

**经验公式**：虚拟节点数 × 服务器数 ≈ 1000-10000

---

## 📖 五、实际应用场景

### 5.1 Redis Cluster

```
Redis Cluster 使用一致性哈希的变种：哈希槽（Hash Slot）

- 固定 16384 个哈希槽（0-16383）
- 每个 key 通过 CRC16(key) % 16384 映射到槽
- 每个节点负责一部分槽
- 槽可以在线迁移，不影响其他槽

优势：
- 槽数量固定，不随节点变化
- 槽迁移粒度细，数据迁移更灵活
```

### 5.2 Nginx 负载均衡

```nginx
# Nginx 一致性哈希模块
upstream backend {
    consistent_hash $request_uri;  # 按 URL 哈希
    
    server 192.168.1.1:8080;
    server 192.168.1.2:8080;
    server 192.168.1.3:8080;
}

server {
    location / {
        proxy_pass http://backend;
    }
}

优势：
- 相同 URL 总是路由到同一台服务器（缓存友好）
- 服务器增减时，大部分请求路由不变
```

### 5.3 Dubbo 负载均衡

```java
// Dubbo 一致性哈希负载均衡
@Reference(loadbalance = "consistenthash")
private UserService userService;

// 相同参数的请求总是路由到同一提供者
// 适合有状态服务或缓存场景
```

### 5.4 分布式存储（Ceph、Cassandra）

```
Ceph CRUSH 算法：
- 基于一致性哈希
- 考虑物理拓扑（机架、机房）
- 数据自动平衡和故障迁移
```

---

## 📖 六、一致性哈希的变种

### 6.1 带权重的一致性哈希

```java
public class WeightedConsistentHash {
    
    // 根据服务器权重分配虚拟节点数
    public void addServer(String server, int weight) {
        int virtualNodes = weight * 100;  // 权重 1 = 100 个虚拟节点
        
        for (int i = 0; i < virtualNodes; i++) {
            String virtualNode = server + "#" + i;
            int hash = hash(virtualNode);
            circle.put(hash, server);
        }
    }
}

// 使用：高性能服务器权重高，低性能服务器权重低
ch.addServer("Server-A", 5);  // 高性能
ch.addServer("Server-B", 3);  // 中性能
ch.addServer("Server-C", 1);  // 低性能
```

### 6.2 跳跃一致性哈希（Jump Consistent Hash）

```java
// Google 提出的算法，无虚拟节点，内存占用极低
public class JumpConsistentHash {
    
    public static int jumpHash(long key, int numBuckets) {
        long b = -1;
        long j = 0;
        
        while (j < numBuckets) {
            b = j;
            key = key * 2862933555777941757L + 1;
            j = (long) ((b + 1) * (2147483648.0 / ((key >>> 33) + 1)));
        }
        
        return (int) b;
    }
}

优势：
- 无需内存存储哈希环
- 计算复杂度 O(log n)
- 适合超大规模集群

缺点：
- 不支持权重
- 不支持删除节点（只能添加）
```

---

## 📖 七、面试真题

### Q1: 一致性哈希解决了什么问题？

**答：** 一致性哈希解决了传统哈希取模在服务器动态增减时的**大量数据迁移问题**。

**传统哈希**：`hash(key) % N`，N 变化时，几乎所有数据位置都变（迁移率 ≈ (N-1)/N）

**一致性哈希**：
- 将数据和服务器映射到哈希环
- 数据顺时针找到最近的服务器
- 服务器变化只影响相邻节点的数据（迁移率 ≈ 1/N）

### Q2: 什么是虚拟节点？为什么需要？

**答：**

**虚拟节点**：一台物理服务器在哈希环上对应多个虚拟节点。

**为什么需要**：
- **解决数据倾斜**：没有虚拟节点时，服务器分布可能不均匀，导致某些服务器负载过高
- **提高均匀性**：虚拟节点越多，数据分布越均匀
- **灵活权重**：通过调整虚拟节点数量实现服务器权重

**典型配置**：每台服务器 150 个虚拟节点。

### Q3: 一致性哈希在 Redis Cluster 中是如何应用的？

**答：** Redis Cluster 使用**哈希槽（Hash Slot）**机制，是一致性哈希的变种：

1. **固定 16384 个哈希槽**（0-16383）
2. **Key 映射**：`CRC16(key) % 16384`
3. **槽分配**：每个节点负责一部分槽（如 Node1 负责 0-5460）
4. **槽迁移**：槽可以在线迁移，不影响其他槽的数据

**优势**：
- 槽数量固定，不随节点变化，简化实现
- 槽迁移粒度细，数据迁移更灵活
- 支持在线扩容缩容

### Q4: 一致性哈希有什么缺点？如何优化？

**答：**

**缺点**：
1. **数据倾斜**：服务器哈希值分布不均时，某些服务器负载过高
2. **节点增减时的波动**：相邻节点负载变化大
3. **查询复杂度**：O(log n)，需要有序数据结构

**优化方案**：
1. **虚拟节点**：每台服务器多个虚拟节点，提高均匀性
2. **权重支持**：根据服务器性能配置不同权重
3. **缓存哈希环**：减少重复计算
4. **Jump Consistent Hash**：无虚拟节点，内存占用低

### Q5: 实现一致性哈希需要注意什么？

**答：**

1. **哈希算法选择**：
   - 选择分布均匀的哈希算法（如 MurmurHash、FNV）
   - 避免分布不均的算法（如简单取模）

2. **虚拟节点数量**：
   - 太少：数据倾斜
   - 太多：内存占用高，查询慢
   - 建议：100-200 个/服务器

3. **并发安全**：
   - 服务器增减时加锁或使用 CopyOnWrite
   - 查询可以无锁

4. **故障处理**：
   - 节点故障时自动剔除
   - 节点恢复时自动加入

---

## 📚 延伸阅读

- [一致性哈希原始论文](https://dl.acm.org/doi/10.1145/258533.258660)
- [Jump Consistent Hash](https://arxiv.org/abs/1406.2294)
- [Redis Cluster 规范](https://redis.io/docs/management/scaling/)
- [Dubbo 负载均衡](https://dubbo.apache.org/zh/docs3-v2/java-sdk/advanced-features-and-usage/performance/loadbalance/)
