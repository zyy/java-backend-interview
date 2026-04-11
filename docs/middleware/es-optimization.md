---
layout: default
title: Elasticsearch 性能优化实战
---

# Elasticsearch 性能优化实战

## 目录
1. [集群规划与分片设计](#集群规划与分片设计)
2. [Mapping 优化](#mapping-优化)
3. [写入优化](#写入优化)
4. [查询优化](#查询优化)
5. [JVM 配置](#jvm-配置)
6. [段合并](#段合并)
7. [监控工具](#监控工具)
8. [面试题精选](#面试题精选)

---

## 集群规划与分片设计

### 分片设计原则

分片（Shard）是 Elasticsearch 数据分布和并行处理的基本单位，合理的分片设计对集群性能至关重要。

#### 分片数量计算公式

```
分片数 = 数据总量 / 单分片建议大小

单分片建议大小：20-50GB（最大不超过 50GB）
```

**示例计算：**

| 数据总量 | 建议分片数 | 节点数 | 每节点分片 |
|----------|------------|--------|------------|
| 100GB | 3-5 | 3 | 1-2 |
| 500GB | 15-25 | 5 | 3-5 |
| 1TB | 30-50 | 10 | 3-5 |

#### 分片配置示例

```json
// 创建索引时指定分片数
PUT /products
{
  "settings": {
    "number_of_shards": 5,      // 主分片数，创建后不可修改
    "number_of_replicas": 1     // 副本分片数，可随时修改
  }
}

// 动态调整副本数
PUT /products/_settings
{
  "number_of_replicas": 2
}
```

### 节点角色规划

```yaml
# 主节点（Master-eligible）
node.roles: [master]
# 负责集群管理，不存储数据

# 数据节点（Data）
node.roles: [data]
# 存储数据，执行 CRUD 和搜索操作

# 协调节点（Coordinating）
node.roles: []
# 仅路由请求，聚合结果，适合高并发场景

# 冷热分离配置
# 热节点（新数据，高性能存储）
node.roles: [data_hot]
node.attr.box_type: hot

# 温节点（旧数据，普通存储）
node.roles: [data_warm]
node.attr.box_type: warm

# 冷节点（归档数据，廉价存储）
node.roles: [data_cold]
node.attr.box_type: cold
```

### 索引生命周期管理（ILM）

```json
// 创建 ILM 策略
PUT /_ilm/policy/logs_policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "1d",
            "max_docs": 100000000
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "require": {
              "box_type": "cold"
            }
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

---

## Mapping 优化

### 禁用不必要的字段

```json
PUT /logs
{
  "mappings": {
    "_source": {
      "excludes": ["internal_metadata"]  // 不存储某些字段到 _source
    },
    "properties": {
      "message": {
        "type": "text",
        "index": true,      // 建立倒排索引
        "store": false      // 不单独存储
      },
      "raw_log": {
        "type": "text",
        "index": false,     // 不建立索引，仅存储
        "doc_values": false // 不生成列式存储
      }
    }
  }
}
```

### 字段类型优化

```json
{
  "mappings": {
    "properties": {
      // 1. 使用 keyword 替代 text 做精确匹配
      "status": {
        "type": "keyword"
      },
      
      // 2. 数值类型选择合适的大小
      "age": {
        "type": "byte"  // 0-127，比 integer 节省空间
      },
      "view_count": {
        "type": "integer"
      },
      "total_bytes": {
        "type": "long"
      },
      
      // 3. 价格使用 scaled_float
      "price": {
        "type": "scaled_float",
        "scaling_factor": 100  // 精确到小数点后2位
      },
      
      // 4. 禁用 text 的 fielddata（避免内存溢出）
      "description": {
        "type": "text",
        "fielddata": false,  // 默认 false，不要开启
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      }
    }
  }
}
```

### Nested 类型优化

```json
// ❌ 不推荐：过多的 nested 字段
{
  "properties": {
    "items": {
      "type": "nested",
      "properties": {
        // 大量字段...
      }
    }
  }
}

// ✅ 推荐：限制 nested 文档数量
{
  "settings": {
    "index.mapping.nested_fields.limit": 50,      // 限制 nested 字段数
    "index.mapping.nested_objects.limit": 10000   // 限制单个文档 nested 对象数
  },
  "mappings": {
    "properties": {
      "items": {
        "type": "nested",
        "properties": {
          "product_id": { "type": "keyword" },
          "quantity": { "type": "short" },
          "price": { 
            "type": "scaled_float",
            "scaling_factor": 100
          }
        }
      }
    }
  }
}
```

---

## 写入优化

### Bulk 批量写入

批量写入比单条写入效率高得多。

```java
// Java 批量写入示例
BulkRequest.Builder br = new BulkRequest.Builder();

for (Product product : products) {
    br.operations(op -> op
        .index(idx -> idx
            .index("products")
            .id(product.getId())
            .document(product)
        )
    );
}

BulkResponse response = client.bulk(br.build());

// 处理失败项
for (BulkResponseItem item : response.items()) {
    if (item.error() != null) {
        logger.error("Failed to index document: {}", item.error().reason());
    }
}
```

**批量大小建议：**

| 文档大小 | 建议批量数 | 批量数据量 |
|----------|------------|------------|
| 小文档 (<1KB) | 5000-10000 | 5-15MB |
| 中文档 (1-10KB) | 1000-2000 | 10-20MB |
| 大文档 (>10KB) | 100-500 | 10-20MB |

### 调整 Refresh 间隔

```json
// 创建索引时设置
PUT /logs
{
  "settings": {
    "index.refresh_interval": "30s"  // 默认 1s，写入场景可调大
  }
}

// 批量写入时临时禁用刷新
PUT /logs/_settings
{
  "index.refresh_interval": "-1"  // 禁用自动刷新
}

// 写入完成后恢复
PUT /logs/_settings
{
  "index.refresh_interval": "1s"
}
```

### 调整 Translog 持久化策略

```json
PUT /logs/_settings
{
  "index.translog.durability": "async",      // 异步写入（默认 sync）
  "index.translog.sync_interval": "5s",      // 同步间隔
  "index.translog.flush_threshold_size": "1gb"  // 触发 flush 的阈值
}
```

### 使用多线程写入

```java
// 使用线程池并发写入
ExecutorService executor = Executors.newFixedThreadPool(8);
List<Future<?>> futures = new ArrayList<>();

for (List<Product> batch : batches) {
    futures.add(executor.submit(() -> bulkIndex(batch)));
}

// 等待所有任务完成
for (Future<?> future : futures) {
    future.get();
}
```

### 写入优化总结

| 优化项 | 配置 | 效果 |
|--------|------|------|
| Bulk 批量 | 1000-5000 条/批 | 减少网络往返 |
| Refresh 间隔 | 30s 或 -1 | 减少段生成 |
| Translog | async | 提高写入吞吐 |
| 副本数 | 批量写入时设为 0 | 减少复制开销 |
| 多线程 | CPU 核心数线程 | 提高并发 |

---

## 查询优化

### Filter 缓存利用

```json
// ✅ 推荐：使用 Filter 缓存
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "active" } },
        { "range": { "create_time": { "gte": "2024-01-01" } } }
      ]
    }
  }
}

// 相同的过滤条件会自动命中缓存
```

### 分页优化

```json
// ❌ 不推荐：深度分页
{
  "from": 10000,
  "size": 10
}

// ✅ 推荐：使用 search_after
{
  "size": 10,
  "sort": [
    { "create_time": "desc" },
    { "_id": "asc" }
  ],
  "search_after": [1699123200000, "doc_10000"]
}
```

### 聚合优化

```json
// ❌ 不推荐：大量桶的聚合
{
  "aggs": {
    "all_terms": {
      "terms": {
        "field": "user_id",
        "size": 100000  // 桶数过多
      }
    }
  }
}

// ✅ 推荐：限制桶数，使用采样
{
  "aggs": {
    "sampled": {
      "sampler": {
        "shard_size": 1000  // 每个分片采样
      },
      "aggs": {
        "top_terms": {
          "terms": {
            "field": "user_id",
            "size": 100
          }
        }
      }
    }
  }
}
```

### 预热索引

```json
// 注册预热查询
PUT /_warmer/products_warmer
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "active" } }
      ]
    }
  },
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category"
      }
    }
  }
}
```

---

## JVM 配置

### 堆内存配置

```bash
# elasticsearch.yml
# 堆内存应设置为物理内存的 50%，但不超过 32GB

# jvm.options
-Xms16g
-Xmx16g
```

**JVM 堆内存原则：**

| 物理内存 | 建议堆内存 | 说明 |
|----------|------------|------|
| 8GB | 4GB | 50% |
| 16GB | 8GB | 50% |
| 32GB | 16GB | 50% |
| 64GB | 31GB | 不超过 32GB（压缩指针阈值）|
| 128GB | 31GB | 剩余给 Lucene 使用 |

### 为什么不超过 32GB？

JVM 使用压缩指针（Compressed Oops）来优化内存使用：
- 堆内存 < 32GB：使用压缩指针，对象引用只需 4 字节
- 堆内存 >= 32GB：禁用压缩指针，对象引用需要 8 字节

因此 31GB 堆内存的实际可用空间可能比 34GB 更多！

### Lucene 使用剩余内存

Elasticsearch 底层使用 Lucene 索引库，Lucene 大量使用文件系统缓存：

```
物理内存 = JVM 堆内存 + Lucene 文件系统缓存
```

文件系统缓存用于缓存索引段文件，对搜索性能至关重要。

### GC 配置

```bash
# jvm.options
# 使用 G1 垃圾收集器（JDK 11+ 默认）
-XX:+UseG1GC

# G1 调优参数
-XX:MaxGCPauseMillis=200  # 最大 GC 停顿时间
-XX:G1HeapRegionSize=16m  # 堆区域大小
```

---

## 段合并

### 什么是段（Segment）

Lucene 索引由多个段（Segment）组成，每个段是一个独立的倒排索引。写入操作会创建新段，过多的段会影响搜索性能。

### Force Merge（强制合并）

```bash
# 强制合并到 5 个段
POST /logs/_forcemerge?max_num_segments=5

# 只合并删除文档（较安全）
POST /logs/_forcemerge?only_expunge_deletes=true
```

**注意事项：**
- Force Merge 会消耗大量 I/O 和 CPU
- 执行期间会阻塞写入（旧版本）或影响性能
- 建议在低峰期执行

### 合并策略配置

```json
PUT /logs/_settings
{
  "index.merge.policy": {
    "max_merge_at_once": 10,           // 单次合并最多段数
    "segments_per_tier": 10,           // 每层段数阈值
    "max_merged_segment": "5gb"        // 最大合并后段大小
  }
}
```

### 段合并最佳实践

1. **不要频繁 Force Merge**：让后台合并线程自动处理
2. **只读索引可以合并到 1 个段**：提高查询性能
3. **监控段数量**：
```bash
GET /_cat/segments/logs?v&s=index:desc
```

---

## 监控工具

### Elasticsearch Head

浏览器插件，提供直观的集群管理界面。

**功能：**
- 查看集群健康状态
- 浏览索引和文档
- 执行查询和聚合
- 查看分片分布

**安装：**
```bash
# Chrome 插件商店搜索 "Elasticsearch Head"
# 或使用 Docker 运行
docker run -p 9100:9100 mobz/elasticsearch-head:5
```

### Kibana

官方可视化工具，功能最全面。

**主要功能：**
- **Discover**：搜索和过滤数据
- **Visualize**：创建图表
- **Dashboard**：组合可视化
- **Dev Tools**：执行 DSL 查询
- **Stack Monitoring**：集群监控

```yaml
# kibana.yml 配置
elasticsearch.hosts: ["http://localhost:9200"]
server.port: 5601
```

### Cerebro

轻量级的集群监控工具。

```bash
# Docker 运行
docker run -p 9000:9000 lmenezes/cerebro
```

**功能：**
- 集群健康监控
- 索引管理
- 节点状态
- 分片分配

### 关键监控指标

```bash
# 集群健康
GET /_cluster/health

# 节点统计
GET /_nodes/stats

# 索引统计
GET /_stats

# 热点线程
GET /_nodes/hot_threads

# 慢查询日志
GET /_cluster/settings?include_defaults=true&filter_path=**.search
```

**核心指标：**

| 指标 | 健康阈值 | 说明 |
|------|----------|------|
| Cluster Status | green | green/yellow/red |
| JVM Heap | < 75% | 堆内存使用率 |
| CPU | < 80% | CPU 使用率 |
| Disk | < 85% | 磁盘使用率 |
| Search Latency | < 100ms | 查询延迟 |
| Indexing Rate | - | 写入速率 |

---

## 面试题精选

### 1. 如何设计 Elasticsearch 的分片策略？分片数设置过大或过小会有什么影响？

**答案要点：**

**分片设计原则：**
- 单分片大小控制在 20-50GB
- 分片数 = 数据总量 / 单分片建议大小
- 每个节点分片数不宜过多（建议 < 20 个/GB 堆内存）

**分片数过大的影响：**
- 每个分片都有资源开销（文件句柄、内存）
- 查询时需要聚合更多分片结果
- 增加集群管理开销

**分片数过小的影响：**
- 单分片数据量过大，影响查询性能
- 无法充分利用集群并行处理能力
- 数据倾斜问题

### 2. Elasticsearch 写入性能如何优化？

**答案要点：**

**写入优化策略：**

1. **Bulk 批量写入**：减少网络往返，建议每批 1000-5000 条
2. **调整 Refresh 间隔**：写入场景调大至 30s 或临时禁用
3. **调整 Translog**：改为 async 模式
4. **减少副本数**：批量写入时临时设为 0
5. **多线程写入**：提高并发度
6. **使用自动生成的 ID**：避免版本检查开销

```json
// 批量写入优化配置
PUT /logs/_settings
{
  "index.refresh_interval": "-1",
  "index.translog.durability": "async",
  "index.number_of_replicas": 0
}
```

### 3. 为什么建议给 Lucene 预留 50% 的物理内存？JVM 堆内存为什么不能设置太大？

**答案要点：**

**Lucene 内存使用：**
- Lucene 使用文件系统缓存（OS File Cache）缓存索引段文件
- 文件系统缓存对搜索性能至关重要
- 预留 50% 物理内存给 Lucene 使用

**JVM 堆内存限制：**
- 不超过 32GB（压缩指针阈值）
- 超过 32GB 后，对象引用从 4 字节变为 8 字节
- 31GB 堆内存可能比 34GB 实际可用空间更多

### 4. Filter 查询为什么比 Query 快？Filter 缓存是如何工作的？

**答案要点：**

**Filter 更快的原因：**
1. 不计算相关性评分（_score）
2. 结果可被缓存
3. 可跳过评分阶段，直接过滤

**Filter 缓存机制：**
- 使用 Bitset 缓存过滤结果
- 相同的过滤条件直接返回缓存的 Bitset
- 缓存以段（Segment）为单位
- 段合并后缓存失效

```json
// 利用 Filter 缓存
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "active" } },
        { "range": { "price": { "gte": 100 } } }
      ]
    }
  }
}
```

### 5. 什么是段合并？什么时候需要 Force Merge？有什么风险？

**答案要点：**

**段合并：**
- Lucene 索引由多个段（Segment）组成
- 写入操作创建新段，后台线程自动合并小段为大段
- 合并过程会删除已标记删除的文档

**Force Merge 适用场景：**
- 只读索引，合并到 1 个段提高查询性能
- 删除大量文档后，清理空间

**风险：**
- 消耗大量 I/O 和 CPU
- 旧版本会阻塞写入
- 生成大段后，后续合并成本更高
- 建议只在低峰期对只读索引执行

```bash
# 强制合并到 1 个段（只读索引）
POST /old_logs/_forcemerge?max_num_segments=1
```
