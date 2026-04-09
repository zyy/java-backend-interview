---
layout: default
title: ES 搜索与聚合查询实战
---

# ES 搜索与聚合查询实战

## 目录
1. [Query DSL 基础](#query-dsl-基础)
2. [过滤 vs 查询](#过滤-vs-查询)
3. [全文检索](#全文检索)
4. [聚合分析](#聚合分析)
5. [深度分页方案](#深度分页方案)
6. [关联查询](#关联查询)
7. [面试题精选](#面试题精选)

---

## Query DSL 基础

Query DSL（Domain Specific Language）是 Elasticsearch 提供的 JSON 风格的查询语言，用于构建复杂的搜索请求。

### Match 查询

Match 是最常用的全文搜索查询，会对查询文本进行分词后再搜索。

```json
// 基础 match 查询
{
  "query": {
    "match": {
      "title": "Elasticsearch 入门"
    }
  }
}

// 指定操作符
{
  "query": {
    "match": {
      "title": {
        "query": "Elasticsearch 入门",
        "operator": "and"  // 默认是 or
      }
    }
  }
}

// 最小匹配度
{
  "query": {
    "match": {
      "title": {
        "query": "Elasticsearch 入门 教程",
        "minimum_should_match": "75%"
      }
    }
  }
}
```

### Term 查询

Term 用于精确值匹配，不会对查询文本进行分词。

```json
// 精确匹配 keyword 字段
{
  "query": {
    "term": {
      "status": "published"
    }
  }
}

// 多值精确匹配
{
  "query": {
    "terms": {
      "tag": ["java", "python", "go"]
    }
  }
}
```

**注意：** Term 查询 text 字段通常得不到预期结果，因为 text 字段会被分词存储。

```json
// ❌ 错误：查询 text 字段
{ "term": { "title": "Hello World" } }  // 可能匹配不到

// ✅ 正确：查询 keyword 子字段
{ "term": { "title.keyword": "Hello World" } }
```

### Range 查询

用于范围查询，支持数字、日期等类型。

```json
// 数字范围
{
  "query": {
    "range": {
      "price": {
        "gte": 100,
        "lte": 500
      }
    }
  }
}

// 日期范围
{
  "query": {
    "range": {
      "create_time": {
        "gte": "2024-01-01",
        "lte": "2024-12-31",
        "format": "yyyy-MM-dd"
      }
    }
  }
}

// 相对时间
{
  "query": {
    "range": {
      "create_time": {
        "gte": "now-7d/d",  // 7天前
        "lte": "now/d"      // 今天
      }
    }
  }
}
```

**范围操作符：**

| 操作符 | 含义 |
|--------|------|
| gt | 大于 |
| gte | 大于等于 |
| lt | 小于 |
| lte | 小于等于 |

### Bool 查询

Bool 查询用于组合多个查询条件，是构建复杂查询的核心。

```json
{
  "query": {
    "bool": {
      "must": [        // 必须满足，参与评分
        { "match": { "title": "Elasticsearch" } },
        { "match": { "content": "搜索引擎" } }
      ],
      "should": [      // 应该满足，提高评分
        { "match": { "tag": "tutorial" } },
        { "match": { "category": "tech" } }
      ],
      "must_not": [    // 必须不满足
        { "term": { "status": "deleted" } }
      ],
      "filter": [      // 必须满足，不参与评分，可缓存
        { "range": { "create_time": { "gte": "2024-01-01" } } },
        { "term": { "is_public": true } }
      ]
    }
  }
}
```

**Bool 子句说明：**

| 子句 | 作用 | 评分 | 缓存 |
|------|------|------|------|
| must | 必须匹配 | 参与 | 否 |
| should | 应该匹配 | 参与 | 否 |
| must_not | 必须不匹配 | 不参与 | 是 |
| filter | 必须匹配 | 不参与 | 是 |

---

## 过滤 vs 查询

### 核心区别

| 特性 | Query | Filter |
|------|-------|--------|
| 目的 | 全文搜索，计算相关性 | 精确过滤，筛选数据 |
| 评分 | 计算 _score | 不计算，统一为 0 |
| 性能 | 较慢 | 快（可缓存） |
| 适用 | 文本搜索 | 精确值、范围过滤 |

### 使用建议

```json
// ❌ 不推荐：用 match 做精确过滤
{
  "query": {
    "match": { "status": "active" }
  }
}

// ✅ 推荐：用 filter 做精确过滤
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "active" } }
      ]
    }
  }
}

// ✅ 推荐：query + filter 组合
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "Elasticsearch" } }  // 全文搜索，参与评分
      ],
      "filter": [
        { "term": { "category": "tech" } },         // 精确过滤，不评分
        { "range": { "price": { "lte": 100 } } }
      ]
    }
  }
}
```

### Filter 缓存机制

Filter 查询结果会被自动缓存，相同的过滤条件直接返回缓存结果，大幅提升性能。

```json
// 复杂的过滤条件组合
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "shop_id": 123 } },
        { "range": { "price": { "gte": 100, "lte": 500 } } },
        { "terms": { "status": ["on_sale", "promotion"] } }
      ]
    }
  }
}
```

---

## 全文检索

### Match Phrase 查询

Match Phrase 用于短语匹配，要求词条顺序一致。

```json
// 短语匹配
{
  "query": {
    "match_phrase": {
      "title": "Elasticsearch 入门"
    }
  }
}

// 允许词条间隔
{
  "query": {
    "match_phrase": {
      "title": {
        "query": "Elasticsearch 入门",
        "slop": 2  // 允许中间有2个其他词条
      }
    }
  }
}
```

**slop 参数：** 允许短语中词条的最大间隔数。

### 多字段匹配

#### Multi Match 查询

在多个字段中搜索同一查询词。

```json
// 基础多字段匹配
{
  "query": {
    "multi_match": {
      "query": "Elasticsearch 搜索",
      "fields": ["title", "content", "tags"]
    }
  }
}

// 指定字段权重
{
  "query": {
    "multi_match": {
      "query": "Elasticsearch",
      "fields": ["title^3", "content^2", "tags"]  // title 权重3倍
    }
  }
}

// 使用 best_fields 类型（默认）
{
  "query": {
    "multi_match": {
      "query": "Elasticsearch 入门",
      "type": "best_fields",  // 使用最佳匹配字段的评分
      "fields": ["title", "content"]
    }
  }
}

// 使用 cross_fields 类型
{
  "query": {
    "multi_match": {
      "query": "Elasticsearch 入门",
      "type": "cross_fields",  // 跨字段匹配，如 first_name + last_name
      "fields": ["title", "content"]
    }
  }
}
```

**Multi Match 类型：**

| 类型 | 说明 |
|------|------|
| best_fields | 默认，使用最佳匹配字段的评分 |
| most_fields | 合并所有匹配字段的评分 |
| cross_fields | 跨字段分析，适合姓名字段 |
| phrase | 短语匹配 |
| phrase_prefix | 短语前缀匹配 |

### Query String 查询

支持 Lucene 语法的复杂查询。

```json
{
  "query": {
    "query_string": {
      "query": "(Elasticsearch OR Solr) AND 搜索引擎",
      "fields": ["title^2", "content"],
      "default_operator": "AND"
    }
  }
}

// 更复杂的语法
{
  "query": {
    "query_string": {
      "query": "title:Elasticsearch AND (tag:java OR tag:python) AND price:[100 TO 500]"
    }
  }
}
```

**Query String 语法：**

| 语法 | 含义 |
|------|------|
| `field:value` | 指定字段搜索 |
| `AND/OR/NOT` | 布尔操作 |
| `*` `?` | 通配符 |
| `~` | 模糊匹配 |
| `^` | 权重提升 |
| `[]` `{}` | 范围查询 |

### Simple Query String

Query String 的简化版，语法错误不抛异常。

```json
{
  "query": {
    "simple_query_string": {
      "query": "Elasticsearch +搜索引擎 -Lucene",
      "fields": ["title", "content"],
      "default_operator": "OR"
    }
  }
}
```

---

## 聚合分析

聚合（Aggregation）是 Elasticsearch 强大的数据分析功能，用于统计、分组、计算指标等。

### 聚合类型

**Bucket 聚合（桶聚合）：**
- 将文档分组到不同的桶中
- 类似 SQL 的 GROUP BY

**Metric 聚合（指标聚合）：**
- 对文档进行数学计算
- 类似 SQL 的 COUNT、SUM、AVG 等

### Terms 聚合

按字段值分组统计，最常用的聚合类型。

```json
// 按状态统计文章数量
{
  "aggs": {
    "status_count": {
      "terms": {
        "field": "status",
        "size": 10  // 返回前10个桶
      }
    }
  }
}

// 结果
{
  "aggregations": {
    "status_count": {
      "buckets": [
        { "key": "published", "doc_count": 150 },
        { "key": "draft", "doc_count": 50 },
        { "key": "deleted", "doc_count": 10 }
      ]
    }
  }
}
```

### Top Hits 聚合

在每个桶中返回最匹配的文档。

```json
// 按分类分组，每组返回评分最高的3篇文章
{
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category"
      },
      "aggs": {
        "top_articles": {
          "top_hits": {
            "size": 3,
            "sort": [
              { "_score": "desc" }
            ],
            "_source": ["title", "author", "create_time"]
          }
        }
      }
    }
  }
}
```

### Date Histogram 聚合

按时间区间分组统计。

```json
// 按月统计订单数量
{
  "aggs": {
    "orders_over_time": {
      "date_histogram": {
        "field": "order_time",
        "calendar_interval": "month",  // 按月聚合
        "format": "yyyy-MM"
      }
    }
  }
}

// 时间间隔选项
{
  "aggs": {
    "orders_by_day": {
      "date_histogram": {
        "field": "order_time",
        "fixed_interval": "1d"  // 固定1天间隔
      }
    }
  }
}
```

**时间间隔类型：**

| 类型 | 示例 | 说明 |
|------|------|------|
| calendar_interval | 1m, 1h, 1d, 1w, 1M, 1q, 1y | 日历间隔 |
| fixed_interval | 1d, 2h, 30m | 固定间隔 |

### Metric 聚合

```json
// 统计价格指标
{
  "aggs": {
    "price_stats": {
      "stats": {
        "field": "price"
      }
    }
  }
}

// 结果
{
  "aggregations": {
    "price_stats": {
      "count": 1000,
      "min": 10.0,
      "max": 9999.0,
      "avg": 500.5,
      "sum": 500500.0
    }
  }
}

// 单独统计
{
  "aggs": {
    "avg_price": { "avg": { "field": "price" } },
    "max_price": { "max": { "field": "price" } },
    "min_price": { "min": { "field": "price" } },
    "sum_price": { "sum": { "field": "price" } },
    "total_orders": { "value_count": { "field": "order_id" } }
  }
}

// 去重统计
{
  "aggs": {
    "unique_users": {
      "cardinality": {
        "field": "user_id"
      }
    }
  }
}
```

### 嵌套聚合

```json
// 按分类统计，每个分类再按标签统计
{
  "aggs": {
    "by_category": {
      "terms": {
        "field": "category"
      },
      "aggs": {
        "by_tag": {
          "terms": {
            "field": "tag"
          }
        },
        "avg_price": {
          "avg": {
            "field": "price"
          }
        }
      }
    }
  }
}
```

### Pipeline 聚合

对聚合结果进行二次计算。

```json
// 计算每月销售额的移动平均线
{
  "aggs": {
    "sales_per_month": {
      "date_histogram": {
        "field": "order_time",
        "calendar_interval": "month"
      },
      "aggs": {
        "total_sales": {
          "sum": {
            "field": "amount"
          }
        },
        "moving_avg": {
          "moving_avg": {
            "buckets_path": "total_sales",
            "window": 3
          }
        }
      }
    }
  }
}
```

---

## 深度分页方案

### From/Size 分页

最简单的分页方式，但不适合深度分页。

```json
// 第1页，每页10条
{
  "from": 0,
  "size": 10
}

// 第100页，每页10条
{
  "from": 990,
  "size": 10
}
```

**限制：**
- `from + size` 不能超过 `index.max_result_window`（默认 10000）
- 深度分页性能差，需要对所有分片排序

### Scroll 游标分页

适合批量导出大量数据。

```json
// 初始化 scroll
POST /products/_search?scroll=1m
{
  "size": 1000,
  "query": {
    "match_all": {}
  }
}

// 返回结果包含 _scroll_id
{
  "_scroll_id": "DXF1ZXJ5QW5kRmV0Y2gB...",
  "hits": { ... }
}

// 获取下一批数据
POST /_search/scroll
{
  "scroll": "1m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gB..."
}

// 清除 scroll 上下文
DELETE /_search/scroll
{
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gB..."
}
```

**特点：**
- 保持搜索上下文，适合批量导出
- 不适合实时搜索（数据可能不是最新的）
- 需要及时清理 scroll 上下文

### Search After 分页

适合实时搜索的深度分页。

```json
// 第一页查询
{
  "size": 10,
  "sort": [
    { "create_time": "desc" },
    { "_id": "asc" }  // 必须包含唯一字段作为 tiebreaker
  ]
}

// 后续页查询，使用上一页最后一条数据的 sort 值
{
  "size": 10,
  "sort": [
    { "create_time": "desc" },
    { "_id": "asc" }
  ],
  "search_after": [1699123200000, "doc_10010"]
}
```

### 分页方案对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| from/size | 浅分页（<10000条） | 简单、实时 | 深度分页性能差 |
| scroll | 批量导出 | 适合大量数据 | 非实时、资源占用 |
| search_after | 深度分页 | 实时、性能好 | 只能下一页，不能跳页 |

---

## 关联查询

Elasticsearch 是文档型数据库，不像关系型数据库支持 JOIN 操作。但提供了以下关联方案：

### Nested 类型关联

适合一对多关系，数据存储在同一个文档中。

```json
// 定义 nested 类型
PUT /orders
{
  "mappings": {
    "properties": {
      "order_id": { "type": "keyword" },
      "items": {
        "type": "nested",
        "properties": {
          "product_id": { "type": "keyword" },
          "product_name": { "type": "text" },
          "price": { "type": "float" },
          "quantity": { "type": "integer" }
        }
      }
    }
  }
}

// nested 查询
{
  "query": {
    "nested": {
      "path": "items",
      "query": {
        "bool": {
          "must": [
            { "match": { "items.product_name": "iPhone" } },
            { "range": { "items.price": { "gte": 5000 } } }
          ]
        }
      }
    }
  }
}

// nested 聚合
{
  "aggs": {
    "items_stats": {
      "nested": {
        "path": "items"
      },
      "aggs": {
        "total_quantity": {
          "sum": {
            "field": "items.quantity"
          }
        }
      }
    }
  }
}
```

### Parent-Child 关联（Join 类型）

适合数据独立更新的一对多关系。

```json
// 定义 join 类型
PUT /company
{
  "mappings": {
    "properties": {
      "name": { "type": "text" },
      "department_to_employee": {
        "type": "join",
        "relations": {
          "department": "employee"
        }
      }
    }
  }
}

// 创建父文档（部门）
POST /company/_doc/1
{
  "name": "技术部",
  "department_to_employee": "department"
}

// 创建子文档（员工）
POST /company/_doc/2?routing=1
{
  "name": "张三",
  "department_to_employee": {
    "name": "employee",
    "parent": "1"
  }
}

// 查询父文档下的子文档
{
  "query": {
    "parent_id": {
      "type": "employee",
      "id": "1"
    }
  }
}

// has_child 查询
{
  "query": {
    "has_child": {
      "type": "employee",
      "query": {
        "match": { "name": "张三" }
      }
    }
  }
}
```

### 应用层关联

最灵活的方式，在应用层实现关联。

```java
// 1. 查询订单
SearchResponse<Order> orderResponse = client.search(s -> s
    .index("orders")
    .query(q -> q.term(t -> t.field("order_id").value("ORDER_001")))
, Order.class);

// 2. 提取商品ID列表
List<String> productIds = orderResponse.hits().hits().stream()
    .flatMap(hit -> hit.source().getItems().stream())
    .map(Item::getProductId)
    .distinct()
    .collect(Collectors.toList());

// 3. 批量查询商品详情
SearchResponse<Product> productResponse = client.search(s -> s
    .index("products")
    .query(q -> q.terms(t -> t.field("product_id").terms(productIds)))
, Product.class);

// 4. 在应用层组装数据
Map<String, Product> productMap = productResponse.hits().hits().stream()
    .collect(Collectors.toMap(
        hit -> hit.source().getProductId(),
        Hit::source
    ));
```

### 关联方案选择

| 方案 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| Nested | 数据一起更新的一对多 | 查询性能好 | 更新子文档需重建整个文档 |
| Parent-Child | 数据独立更新的一对多 | 独立更新 | 查询性能较差 |
| 应用层关联 | 复杂关联 | 最灵活 | 多次查询 |
| 数据冗余 | 读多写少 | 查询最快 | 数据一致性维护困难 |

---

## 面试题精选

### 1. Match 和 Term 查询有什么区别？分别在什么场景下使用？

**答案要点：**

| 特性 | Match | Term |
|------|-------|------|
| 分词 | 对查询词分词 | 不分词 |
| 适用字段 | text | keyword |
| 匹配方式 | 倒排索引匹配 | 精确值匹配 |

**使用场景：**
- Match：全文搜索场景，如搜索文章标题、内容
- Term：精确匹配场景，如按状态、ID、标签过滤

**常见错误：**
```json
// 错误：用 term 查询 text 字段
{ "term": { "title": "Hello World" } }  // 可能匹配不到，因为 title 被分词存储

// 正确：用 match 查询 text 字段
{ "match": { "title": "Hello World" } }
```

### 2. Filter 和 Query 有什么区别？为什么 Filter 性能更好？

**答案要点：**

**区别：**
- Query：计算相关性评分（_score），用于全文搜索
- Filter：不计算评分，用于精确过滤

**Filter 性能更好的原因：**
1. **不计算评分**：省去相关性计算开销
2. **结果可缓存**：相同的过滤条件直接返回缓存结果
3. **可跳过评分阶段**：在倒排索引层面快速过滤

**使用建议：**
- 精确值过滤、范围过滤使用 Filter
- 全文搜索使用 Query
- 两者组合时，Filter 条件放在 bool.filter 中

### 3. Elasticsearch 有哪些深度分页方案？各有什么优缺点？

**答案要点：**

| 方案 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| from/size | 跳过前 N 条 | 简单、实时 | 深度分页性能差 | 浅分页（<10000） |
| scroll | 保持搜索上下文 | 适合大量数据导出 | 非实时、资源占用 | 批量导出 |
| search_after | 基于排序值定位 | 实时、性能好 | 不能跳页 | 深度分页 |

**深度分页问题：**
- from/size 需要对所有分片排序，深度分页时内存消耗大
- scroll 保持上下文会占用资源
- search_after 只能一页一页翻

### 4. Terms 聚合和 Date Histogram 聚合分别适用于什么场景？

**答案要点：**

**Terms 聚合：**
- 按字段值分组统计
- 适用场景：按状态统计、按分类统计、按标签统计
- 特点：自动按文档数排序，可指定 size 限制返回桶数

**Date Histogram 聚合：**
- 按时间区间分组统计
- 适用场景：按天/周/月统计订单量、用户增长趋势
- 特点：支持日历间隔和固定间隔

```json
// Terms：按状态统计订单
{ "aggs": { "by_status": { "terms": { "field": "status" } } } }

// Date Histogram：按天统计订单
{ "aggs": { "by_day": { "date_histogram": { "field": "order_time", "calendar_interval": "day" } } } }
```

### 5. Nested 类型和 Parent-Child 关联有什么区别？如何选择？

**答案要点：**

| 特性 | Nested | Parent-Child |
|------|--------|--------------|
| 存储方式 | 内嵌文档 | 独立文档 |
| 更新 | 需重建整个文档 | 可独立更新 |
| 查询性能 | 好 | 较差 |
| 适用数据量 | 少量子文档 | 大量子文档 |

**选择建议：**
- 子文档数量少，且经常一起更新 → Nested
- 子文档数量多，需要独立更新 → Parent-Child
- 关联复杂，查询性能要求高 → 应用层关联或数据冗余
