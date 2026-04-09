---
layout: default
title: ES 搜索与聚合查询实战
---
# ES 搜索与聚合查询实战

## 🎯 面试题：ES 的查询 DSL 有哪些？聚合查询怎么用？

> ES 的查询能力和聚合分析能力是面试考察的重点。需要掌握 Query DSL、过滤与查询的区别、聚合分组、深分页解决方案等。

---

## 一、Query DSL

### 全文检索

```json
// match：分词后检索
GET /my_index/_search
{
  "query": {
    "match": {
      "title": "Java 面试"
    }
  }
}

// match_phrase：短语匹配（按顺序出现）
GET /my_index/_search
{
  "query": {
    "match_phrase": {
      "title": {
        "query": "Java 工程师",
        "slop": 1   // 允许词之间有1个间隔
      }
    }
  }
}

// multi_match：多字段匹配
GET /my_index/_search
{
  "query": {
    "multi_match": {
      "query": "Spring Boot",
      "fields": ["title^2", "content"],  // title 加权 2 倍
      "type": "best_fields"             // 最佳字段
    }
  }
}
```

### 精确值查询

```json
// term：精确匹配（不分词）
GET /my_index/_search
{
  "query": {
    "term": { "status": "published" }
  }
}

// terms：多值精确匹配
GET /my_index/_search
{
  "query": {
    "terms": { "status": ["published", "active"] }
  }
}

// range：范围查询
GET /my_index/_search
{
  "query": {
    "range": {
      "price": {
        "gte": 100,
        "lte": 500,
        "boost": 2.0   // 加权
      }
    }
  }
}
```

### Bool 查询

```json
GET /my_index/_search
{
  "query": {
    "bool": {
      "must": [       // 必须匹配，参与评分
        { "match": { "title": "Java" } }
      ],
      "should": [     // 加分项，满足越多得分越高
        { "term": { "is_top": true } },
        { "range": { "views": { "gte": 1000 } } }
      ],
      "must_not": [   // 必须不匹配
        { "term": { "status": "deleted" } }
      ],
      "filter": [     // 必须满足，不参与评分（更快）
        { "term": { "category": "backend" } },
        { "range": { "price": { "lte": 500 } } }
      ]
    }
  }
}
```

---

## 二、Filter vs Query

```
┌──────────────────────────────────────────────────┐
│ Query（相关性查询）：                                 │
│   - 计算相关度评分（BM25）                           │
│   - 结果会被缓存                                    │
│   - 适合需要排序的场景                              │
│                                                    │
│ Filter（过滤查询）：                                 │
│   - 不计算评分，性能更高                             │
│   - 自动缓存                                       │
│   - 适合精确匹配、范围查询                           │
└──────────────────────────────────────────────────┘

规则：
  - 精确匹配（term/terms/range）→ filter
  - 全文搜索（match） → must
  - 既要精确又要排序 → fields: { field: { type: text } + field.keyword }
```

---

## 三、聚合查询

### Bucket（桶聚合）

```json
// terms：按字段值分组
GET /order_index/_search
{
  "size": 0,   // 不返回文档，只返回聚合结果
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category",
        "size": 10,       // 返回前 10 个分组
        "shard_size": 20  // 每个分片取 20 个再聚合
      },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } }
      }
    }
  }
}
```

### Metric（指标聚合）

```json
// 多指标聚合
GET /order_index/_search
{
  "size": 0,
  "aggs": {
    "stats": {
      "stats": { "field": "price" }
    },
    "max_price": { "max": { "field": "price" } },
    "min_price": { "min": { "field": "price" } },
    "avg_price": { "avg": { "field": "price" } },
    "cardinality": { "cardinality": { "field": "user_id" } }
  }
}
```

### 嵌套聚合

```json
// 按月统计，每天平均订单数
GET /order_index/_search
{
  "size": 0,
  "aggs": {
    "by_month": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "month"
      },
      "aggs": {
        "daily_avg": { "avg": { "field": "amount" } },
        "total_amount": { "sum": { "field": "amount" } },
        "top_users": {
          "top_hits": {
            "size": 3,
            "sort": [{ "amount": "desc" }]
          }
        }
      }
    }
  }
}
```

---

## 四、深分页问题

```
三种分页方式对比：

┌──────────────┬───────────┬─────────────┬────────────┐
│              │ from/size │ scroll      │ search_after │
├──────────────┼───────────┼─────────────┼────────────┤
│ 深度分页     │ 支持但慢   │ 支持         │ 支持（最优） │
│ 最大数据量    │ 10000     │ 无限制       │ 无限制       │
│ 性能          │ O(from+size)│ O(scroll_id)│ O(1)        │
│ 适用场景     │ 在线浅翻页  │ 离线大批量   │ 在线深翻页   │
│ 实时性       │ 实时       │ 快照（开启时）│ 实时        │
│ 资源消耗     │ 高         │ 中           │ 低           │
└──────────────┴───────────┴─────────────┴────────────┘

search_after（推荐）：
  1. 第一页：正常查询，用 sort + tie_breaker 取最后一条
  2. 后续页：用上一页最后一条的 sort values 作为 search_after 参数
```

---

## 五、关联查询

### nested 对象查询

```json
// nested 用于数组内对象需要关联查询时
PUT /forum
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
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

// 查询：回复内容包含"Redis"且用户为"Alice"
GET /forum/_search
{
  "query": {
    "nested": {
      "path": "comments",
      "query": {
        "bool": {
          "must": [
            { "match": { "comments.content": "Redis" } },
            { "term": { "comments.user": "Alice" } }
          ]
        }
      }
    }
  }
}
```

---

## 六、面试高频题

**Q1: ES 有哪些查询类型？**
> 主要分两类：精确值查询（term/terms/range）和全文检索（match/match_phrase/multi_match）。bool 查询可以组合它们：must（必须匹配，参与评分）、should（加分项）、must_not（必须不匹配）、filter（必须满足，不评分，更快）。

**Q2: filter 和 query 的区别是什么？**
> 核心区别：query 计算相关度评分（BM25），filter 不计算评分。filter 自动缓存结果，性能更高。规则：精确匹配用 filter（term/range），全文检索用 query（match），既需要精确又需要评分时配合使用。ES 底层会识别 bool.filter 中的 term 查询并自动缓存。

**Q3: ES 深分页有哪些解决方案？**
> 三种：① `from + size`：最大 10000 条，越深越慢（需要 merge 多个 shard 结果）；② `scroll`：适合离线大批量导出，通过 scroll_id 维持查询快照，不适合实时场景；③ `search_after`（推荐）：基于游标的分页，性能恒定 O(1)，需要有一个唯一排序字段（推荐 _id），支持实时翻页。
