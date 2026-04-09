---
layout: default
title: Elasticsearch 性能优化实战
---
# Elasticsearch 性能优化实战

## 🎯 面试题：Elasticsearch 查询很慢怎么排查？如何优化 ES 性能？

> ES 是分布式全文检索引擎，性能问题主要来自集群规划不当、写入压力过大、查询不合理。本题考察对 ES 底层原理和性能调优的理解。

---

## 一、集群规划与分片设计

### 分片数规划原则

```
分片（Shard）是 ES 数据存储和查询的最小单元：

公式：分片数 = 数据总量（GB）/ 节点数 / 30

举例：
  每天 100GB 数据，保留 30 天 = 3TB
  3 台数据节点 = 3000GB / 3 / 30 = 33 个分片

分片数过少：查询并行度低，吞吐上不去
分片数过多：管理开销大，每个分片消耗内存（segment + buffer）
每个分片推荐大小：30-50GB

副本数：
  高可用要求 ≥ 1
  读多写少：副本数 = 节点数 - 1（充分利用副本读）
  写入优先：副本数 = 1（减少写入放大）
```

### 冷热分离架构

```
┌─────────────────────────────────────────────────────┐
│ 热节点（Hot）         │ 温节点（Warm）   │ 冷节点（Cold）│
│ SSD，高写入高查询      │ HDD，中等负载     │ HDD，存档数据 │
│ 最近 7 天数据          │ 7-30 天数据       │ 30 天前      │
└─────────────────────────────────────────────────────┘
用 ILM（Index Lifecycle Management）自动迁移
```

---

## 二、Mapping 设计优化

### 字段类型选择

```json
PUT /my_index
{
  "mappings": {
    "properties": {
      // ✅ 能用 keyword 就不用 text（不建倒排索引，节省空间）
      "status":    { "type": "keyword" },        // 精确值
      "user_id":   { "type": "long" },           // 数字精确查询
      "created_at":{"type": "date" },             // 日期
      "title":     { "type": "text", "analyzer": "ik_max_word" },  // 全文检索
      "author":    { "type": "keyword" },          // 精确匹配不用 text
      
      // ❌ 避免：全部用 text（浪费空间）
      // "status": { "type": "text" }  ← 错！status 只需要精确匹配
      
      // nested 用于数组内对象关联查询
      "comments": {
        "type": "nested",
        "properties": {
          "user": { "type": "keyword" },
          "content": { "type": "text" }
        }
      }
    }
  }
}
```

### 关闭不必要的字段

```json
{
  "mappings": {
    "_source": {
      "enabled": false   // 如果不需要返回原始文档，可以关闭（节省存储）
    },
    "includes": ["title", "author", "created_at"],  // 只返回必要字段
    "excludes": ["content"]  // 排除大字段
  }
}
```

---

## 三、写入优化

### 批量写入

```java
// ❌ 单条写入：每次请求都有 HTTP 开销
for (Document doc : documents) {
    client.index(doc);  // 每条一次 HTTP 请求
}

// ✅ 批量写入：减少网络开销
BulkRequestBuilder bulkRequest = client.prepareBulk();
for (Document doc : documents) {
    bulkRequest.add(client.prepareIndex("my_index", "_doc")
        .setSource(doc));
}
BulkResponse bulkResponse = bulkRequest.get();
// 推荐批量大小：500-5000 条 / 次
```

### refresh_interval 调优

```json
PUT /my_index/_settings
{
  "settings": {
    // 默认 1 秒，实时写入可调大
    "refresh_interval": "30s",
    // translog 持久化策略
    "index.translog.durability": "async",    // 异步写，丢风险换性能
    "index.translog.sync_interval": "5s"
  }
}
```

### 副本策略

```json
PUT /my_index/_settings
{
  "settings": {
    "number_of_replicas": 0   // 写入期间关闭副本，写完后再开启
  }
}

// 写完后开启副本（自动复制）
POST /my_index/_close
PUT /my_index/_settings
{ "number_of_replicas": 1 }
POST /my_index/_open
```

---

## 四、查询优化

### filter vs query

```java
// ✅ filter：不计算相关度评分，结果可缓存
BoolQueryBuilder query = QueryBuilders.boolQuery()
    .filter(QueryBuilders.termQuery("status", "active"))     // filter 不评分
    .filter(QueryBuilders.rangeQuery("price").gte(100))   // filter 不评分
    .must(QueryBuilders.matchQuery("title", "Java"));      // must 参与评分

// ❌ must 替代 filter：白白浪费评分计算
.must(QueryBuilders.termQuery("status", "active"))        // 不需要评分
```

### 避免通配符前缀

```java
// ❌ 前缀通配符：从第一个字符开始匹配，无法利用倒排索引，全表扫描
QueryBuilders.wildcardQuery("code", "*ABC")

// ✅ 优化：用 keyword + prefix 查询
QueryBuilders.boolQuery()
    .must(QueryBuilders.termQuery("code.prefix", "ABC"))  // 需要配置 prefix 字段

// ✅ 或者：前缀搜索用 matchPhrasePrefix
QueryBuilders.matchPhrasePrefixQuery("title", "Java 设计")  // 前缀匹配
```

### 分页优化

```java
// ❌ from + size 深分页：最大 10000 条，且越翻越慢
searchRequest.source().from(9900).size(100);  // 翻到第 100 页极慢

// ✅ search_after：基于游标的深分页，O(1) 复杂度
// 第一页
SearchResponse r1 = client.search(searchRequest
    .source(new SearchSourceBuilder()
        .sort("_id")           // 必须有唯一排序字段
        .size(10));
// 取最后一行的 sort 值
Object[] lastSort = r1.getHits().getHits()[9].getSortValues();

// 第二页
searchRequest.source().searchAfter(lastSort);

// ✅ scroll：大批量导出（适合离线批处理，不适合在线）
SearchScrollRequest scrollRequest = new SearchScrollRequest(scrollId);
scrollRequest.scroll(new TimeValue(600000));
```

---

## 五、JVM 与内存优化

```yaml
# jvm.options
# 不要超过 32GB，否则 JVM 关闭压缩普通对象指针（OOP）
-Xms16g
-Xmx16g

# 堆内存分配原则：50% 给 ES，50% 给系统缓存
# Lucene segment 数据缓存在系统页缓存，不在 JVM 堆内
```

### 熔断机制

```json
PUT /_cluster/settings
{
  "transient": {
    "indices.breaker.total.use_real_memory": false,
    "indices.breaker.request.limit": "60%"   // 断路器阈值
  }
}
```

---

## 六、监控与问题排查

### 健康检查

```bash
# 集群健康
GET /_cluster/health
{
  "status": "green/yellow/red",
  "number_of_nodes": 3,
  "active_shards": 30
}

# 分片分配
GET /_cat/shards?v

# 节点资源
GET /_cat/nodes?v&h=heap,heap.percent,ram,ram.percent,cpu,load_1m
```

### 慢查询日志

```json
PUT /my_index/_settings
{
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.search.slowlog.threshold.query.warn": "10s"
}
```

---

## 七、高频面试题

**Q1: ES 查询很慢怎么排查？**
> 排查步骤：① 查看集群健康 `GET /_cluster/health`；② 查看分片分配 `GET /_cat/shards`；③ 用 `_profile` 分析查询耗时 `GET /_search {"profile": true }`；④ 检查是否用了通配符前缀查询；⑤ 检查分页深度（from+size 深分页很慢）；⑥ 看是否大量 filter 被误用为 must（不必要地计算评分）。常见原因：mapping 设计不当（用 text 做精确查询）、深分页、查询未命中分片缓存。

**Q2: 如何优化 ES 的写入性能？**
> 四个方向：① 批量写入（BulkRequest），每次 500-5000 条；② 调大 `refresh_interval` 到 30s-1m；③ 写入期间关闭副本（`number_of_replicas: 0`），写完再开启；④ translog 设置为 async 持久化。核心思想是在写入时减少 ES 的内部开销（合并 segment、刷新、复制）。

**Q3: ES 深分页问题怎么解决？**
> 两种方案：① `search_after`（推荐）：基于游标的分页，O(1) 复杂度，性能稳定，需要有唯一排序字段；② `scroll`：适合离线大批量导出，不适合在线，会创建快照消耗资源。`from + size` 最大只能到 10000 条，越深越慢（需要 merge 多个 shard 结果）。
