---
layout: default
title: ES 分词器与 Mapping 设计实战
---

# ES 分词器与 Mapping 设计实战

## 目录
1. [分词流程概述](#分词流程概述)
2. [内置分词器详解](#内置分词器详解)
3. [中文分词方案](#中文分词方案)
4. [Mapping 设计原则](#mapping-设计原则)
5. [Dynamic Mapping](#dynamic-mapping)
6. [字段类型选择](#字段类型选择)
7. [分词器测试 API](#分词器测试-api)
8. [面试题精选](#面试题精选)

---

## 分词流程概述

Elasticsearch 的分词过程由三个核心组件组成：字符过滤器（Character Filter）、分词器（Tokenizer）和 Token 过滤器（Token Filter）。

### 分词流程图

```
原始文本
    ↓
[Character Filter]  字符过滤（如去除 HTML 标签）
    ↓
[Tokenizer]         分词（将文本切分为词条）
    ↓
[Token Filter]      Token 过滤（如转小写、去停用词）
    ↓
Token 流（倒排索引存储）
```

### 各组件说明

#### 1. Character Filter（字符过滤器）

在分词之前对原始文本进行预处理，可以添加、删除或替换字符。

**常见字符过滤器：**

| 过滤器 | 功能 |
|--------|------|
| `html_strip` | 去除 HTML 标签 |
| `mapping` | 字符映射替换 |
| `pattern_replace` | 正则替换 |

```json
// 示例：去除 HTML 标签
{
  "char_filter": {
    "html_strip": {
      "type": "html_strip"
    }
  }
}
```

#### 2. Tokenizer（分词器）

将文本切分为独立的词条（Token），是分词流程的核心。

**常见分词器：**

| 分词器 | 特点 |
|--------|------|
| `standard` | 标准分词器，按词切分，去除标点 |
| `whitespace` | 按空白字符切分 |
| `keyword` | 不分词，整体作为一个词条 |
| `pattern` | 按正则表达式切分 |
| `path_hierarchy` | 按路径层级切分 |

#### 3. Token Filter（Token 过滤器）

对分词后的词条进行加工处理。

**常见 Token 过滤器：**

| 过滤器 | 功能 |
|--------|------|
| `lowercase` | 转小写 |
| `stop` | 去除停用词 |
| `synonym` | 同义词处理 |
| `stemmer` | 词干提取 |
| `edge_ngram` | 边缘 N-gram |

### 自定义 Analyzer 示例

```json
PUT /my_index
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_custom_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  }
}
```

---

## 内置分词器详解

### 1. Standard Analyzer（标准分词器）

**默认分词器**，适用于大多数西方语言。

**特点：**
- 按词边界切分
- 去除标点符号
- 转小写
- 去除停用词（默认关闭）

```json
// 测试标准分词器
POST /_analyze
{
  "analyzer": "standard",
  "text": "The Quick Brown Fox jumps! 你好世界"
}

// 结果：[the, quick, brown, fox, jumps, 你, 好, 世, 界]
```

### 2. Simple Analyzer（简单分词器）

**特点：**
- 按非字母字符切分
- 转小写
- 不处理停用词

```json
POST /_analyze
{
  "analyzer": "simple",
  "text": "The Quick. Brown-Fox jumps!"
}

// 结果：[the, quick, brown, fox, jumps]
```

### 3. Whitespace Analyzer（空白分词器）

**特点：**
- 仅按空白字符切分
- 保留大小写
- 保留标点

```json
POST /_analyze
{
  "analyzer": "whitespace",
  "text": "The Quick. Brown-Fox jumps!"
}

// 结果：[The, Quick., Brown-Fox, jumps!]
```

### 4. Keyword Analyzer（关键字分词器）

**特点：**
- 不分词，整体作为一个 Token
- 常用于精确匹配场景

```json
POST /_analyze
{
  "analyzer": "keyword",
  "text": "The Quick Brown Fox"
}

// 结果：[The Quick Brown Fox]
```

### 5. Pattern Analyzer（模式分词器）

**特点：**
- 按正则表达式切分
- 可自定义分隔模式

```json
PUT /pattern_index
{
  "settings": {
    "analysis": {
      "analyzer": {
        "csv_analyzer": {
          "type": "pattern",
          "pattern": ",",
          "lowercase": false
        }
      }
    }
  }
}

POST /pattern_index/_analyze
{
  "analyzer": "csv_analyzer",
  "text": "apple,banana,orange"
}

// 结果：[apple, banana, orange]
```

### 内置分词器对比

| 分词器 | 切分方式 | 转小写 | 去标点 | 适用场景 |
|--------|----------|--------|--------|----------|
| standard | 词边界 | ✓ | ✓ | 通用场景 |
| simple | 非字母 | ✓ | ✓ | 简单英文 |
| whitespace | 空白字符 | ✗ | ✗ | 保留原格式 |
| keyword | 不分词 | ✗ | ✗ | 精确匹配 |
| pattern | 正则 | 可选 | 可选 | 结构化数据 |

---

## 中文分词方案

### 1. IK 分词器

最流行的中文分词插件，支持细粒度切分和智能切分两种模式。

#### 安装

```bash
# 下载对应版本的 IK 插件
./bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v7.17.0/elasticsearch-analysis-ik-7.17.0.zip
```

#### 分词模式

**ik_max_word（细粒度）：** 将文本做最细粒度拆分

```json
POST /_analyze
{
  "analyzer": "ik_max_word",
  "text": "中华人民共和国国歌"
}

// 结果：[中华人民共和国, 中华人民, 中华, 华人, 人民共和国, 人民, 共和国, 共和, 国, 国歌]
```

**ik_smart（智能）：** 做最粗粒度拆分，适合搜索场景

```json
POST /_analyze
{
  "analyzer": "ik_smart",
  "text": "中华人民共和国国歌"
}

// 结果：[中华人民共和国, 国歌]
```

#### 自定义词典

```bash
# 在 config/analysis-ik 目录下创建自定义词典
custom.dic:
王者荣耀
Elasticsearch

# 配置 IKAnalyzer.cfg.xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
<properties>
  <comment>IK Analyzer 扩展配置</comment>
  <entry key="ext_dict">custom.dic</entry>
  <entry key="ext_stopwords">stopword.dic</entry>
</properties>
```

### 2. 结巴分词（Jieba）

Python 生态中流行的中文分词库，也有 Elasticsearch 插件版本。

**特点：**
- 支持三种分词模式：精确模式、全模式、搜索引擎模式
- 支持繁体分词
- 支持自定义词典
- 基于前缀词典和动态规划实现

```json
// 使用 jieba 分词器
POST /_analyze
{
  "analyzer": "jieba_index",
  "text": "我来到北京清华大学"
}

// 结果：[我, 来到, 北京, 清华大学, 清华, 华大, 大学]
```

### 3. 中文分词器对比

| 特性 | IK 分词器 | 结巴分词 |
|------|-----------|----------|
| 性能 | 高 | 中 |
| 词典维护 | 方便 | 方便 |
| 新词识别 | 一般 | 较好 |
| 繁体支持 | 需配置 | 原生支持 |
| 社区活跃度 | 高 | 中 |

---

## Mapping 设计原则

### 什么是 Mapping

Mapping 定义了索引中字段的类型和分词方式，类似于关系型数据库的表结构定义。

```json
PUT /products
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "price": {
        "type": "float"
      },
      "create_time": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time||epoch_millis"
      }
    }
  }
}
```

### text vs keyword 类型

这是 Mapping 设计中最关键的选择。

#### text 类型

- 用于全文搜索字段
- 会被分词器处理
- 支持模糊匹配、相关性评分
- 不适用于排序和聚合

```json
{
  "description": {
    "type": "text",
    "analyzer": "standard"
  }
}
```

#### keyword 类型

- 用于精确值字段
- 不会被分词，整体存储
- 支持排序、聚合、精确匹配
- 支持前缀搜索

```json
{
  "status": {
    "type": "keyword"
  }
}
```

#### 多字段映射（Multi-fields）

一个字段同时支持全文搜索和精确匹配：

```json
{
  "title": {
    "type": "text",
    "analyzer": "ik_max_word",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    }
  }
}

// 使用方式：
// title 用于全文搜索
// title.keyword 用于排序、聚合、精确匹配
```

### nested 类型

用于存储对象数组，保持数组中每个对象的独立性。

```json
{
  "order_items": {
    "type": "nested",
    "properties": {
      "product_id": { "type": "keyword" },
      "product_name": { "type": "text" },
      "price": { "type": "float" },
      "quantity": { "type": "integer" }
    }
  }
}

// 查询 nested 字段
{
  "query": {
    "nested": {
      "path": "order_items",
      "query": {
        "bool": {
          "must": [
            { "match": { "order_items.product_name": "iPhone" } },
            { "range": { "order_items.price": { "gte": 5000 } } }
          ]
        }
      }
    }
  }
}
```

### geo 类型

用于地理位置数据存储和搜索。

```json
{
  "location": {
    "type": "geo_point"
  },
  "delivery_area": {
    "type": "geo_shape"
  }
}

// 数据格式
{
  "location": {
    "lat": 39.9042,
    "lon": 116.4074
  }
}
```

**geo_point 支持的距离查询：**

```json
{
  "query": {
    "geo_distance": {
      "distance": "1km",
      "location": {
        "lat": 39.9042,
        "lon": 116.4074
      }
    }
  }
}
```

---

## Dynamic Mapping

### 什么是 Dynamic Mapping

当向索引中添加未定义的字段时，Elasticsearch 会自动推断字段类型。

### 动态映射规则

| JSON 数据类型 | ES 字段类型 |
|---------------|-------------|
| null | 不添加字段 |
| true/false | boolean |
| 浮点数 | float |
| 整数 | long |
| 包含日期格式的字符串 | date |
| 其他字符串 | text + keyword |
| 对象 | object |
| 数组 | 由数组中第一个非空值决定 |

### 动态映射配置

```json
PUT /my_index
{
  "mappings": {
    "dynamic": "strict",  // 严格模式，禁止未知字段
    "properties": {
      "title": {
        "type": "text"
      }
    }
  }
}
```

**dynamic 参数选项：**

| 值 | 说明 |
|----|------|
| `true` | 动态添加新字段（默认） |
| `false` | 忽略新字段，不索引但存储在 `_source` |
| `strict` | 遇到未知字段抛出异常 |
| `runtime` | 将新字段作为 runtime 字段 |

### 动态模板（Dynamic Templates）

自定义动态映射规则：

```json
PUT /my_index
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "longs_as_integers": {
          "match_mapping_type": "long",
          "mapping": {
            "type": "integer"
          }
        }
      },
      {
        "en_text": {
          "match": "*_en",
          "mapping": {
            "type": "text",
            "analyzer": "english"
          }
        }
      }
    ]
  }
}
```

### Dynamic Mapping 优缺点

**优点：**
- 快速原型开发
- 减少配置工作
- 灵活适应数据结构变化

**缺点：**
- 字段类型推断可能不准确
- text 类型默认会创建 keyword 子字段，造成存储浪费
- 生产环境建议显式定义 Mapping

---

## 字段类型选择

### 常见字段类型速查

| 类型 | 说明 | 示例 |
|------|------|------|
| `text` | 全文搜索，会被分词 | 文章标题、描述 |
| `keyword` | 精确值，不分词 | 状态、标签、ID |
| `long` | 64位整数 | 计数、ID |
| `integer` | 32位整数 | 年龄、数量 |
| `short` | 16位整数 | 小范围整数 |
| `byte` | 8位整数 | 开关、标志位 |
| `float` | 32位浮点 | 价格、评分 |
| `double` | 64位浮点 | 高精度数值 |
| `boolean` | 布尔值 | 是否有效 |
| `date` | 日期时间 | 创建时间、更新时间 |
| `object` | 嵌套对象 | 用户信息 |
| `nested` | 嵌套对象数组 | 订单商品列表 |
| `geo_point` | 地理坐标 | 店铺位置 |
| `geo_shape` | 地理形状 | 配送范围 |
| `ip` | IP 地址 | 访问者 IP |

### 字段类型选择最佳实践

#### 1. 不要全部使用 text

```json
// ❌ 不推荐：所有字段都用 text
{
  "user_id": { "type": "text" },
  "status": { "type": "text" },
  "created_at": { "type": "text" }
}

// ✅ 推荐：根据用途选择类型
{
  "user_id": { 
    "type": "keyword"  // 精确匹配、聚合
  },
  "status": { 
    "type": "keyword"  // 精确匹配、过滤
  },
  "created_at": { 
    "type": "date"     // 时间范围查询
  },
  "description": { 
    "type": "text"     // 全文搜索
  }
}
```

#### 2. 数值类型的选择

```json
{
  "age": { "type": "byte" },           // 0-127，节省空间
  "view_count": { "type": "integer" }, // 普通计数
  "total_bytes": { "type": "long" },   // 大数值
  "price": { "type": "scaled_float",   // 精确小数
             "scaling_factor": 100 }
}
```

#### 3. 日期类型配置

```json
{
  "create_time": {
    "type": "date",
    "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
  }
}
```

#### 4. 禁用 `_all` 字段（ES 6.x+ 已移除）

```json
// ES 5.x 配置
{
  "_all": { "enabled": false }
}

// ES 6.x+ 使用 copy_to 替代
{
  "properties": {
    "title": {
      "type": "text",
      "copy_to": "full_text"
    },
    "content": {
      "type": "text",
      "copy_to": "full_text"
    },
    "full_text": {
      "type": "text"
    }
  }
}
```

---

## 分词器测试 API

### Analyze API

Elasticsearch 提供 `_analyze` API 用于测试分词效果。

#### 基本用法

```json
// 测试内置分词器
POST /_analyze
{
  "analyzer": "standard",
  "text": "Hello World! 你好世界"
}

// 测试结果
{
  "tokens": [
    { "token": "hello", "start_offset": 0, "end_offset": 5, "type": "<ALPHANUM>", "position": 0 },
    { "token": "world", "start_offset": 6, "end_offset": 11, "type": "<ALPHANUM>", "position": 1 },
    { "token": "你", "start_offset": 13, "end_offset": 14, "type": "<IDEOGRAPHIC>", "position": 2 },
    { "token": "好", "start_offset": 14, "end_offset": 15, "type": "<IDEOGRAPHIC>", "position": 3 },
    { "token": "世", "start_offset": 15, "end_offset": 16, "type": "<IDEOGRAPHIC>", "position": 4 },
    { "token": "界", "start_offset": 16, "end_offset": 17, "type": "<IDEOGRAPHIC>", "position": 5 }
  ]
}
```

#### 测试自定义分词器

```json
POST /_analyze
{
  "tokenizer": "standard",
  "filter": ["lowercase", "stop"],
  "text": "The Quick Brown Fox jumps over the lazy dog"
}

// 结果：[quick, brown, fox, jumps, over, lazy, dog]（去除了 the）
```

#### 在指定索引上测试

```json
// 使用索引中定义的分词器
POST /products/_analyze
{
  "field": "title",
  "text": "iPhone 15 Pro Max"
}
```

### 常用测试场景

#### 1. 验证中文分词效果

```json
POST /_analyze
{
  "analyzer": "ik_max_word",
  "text": "王者荣耀是一款非常流行的手机游戏"
}
```

#### 2. 测试同义词

```json
POST /_analyze
{
  "tokenizer": "standard",
  "filter": [
    {
      "type": "synonym",
      "synonyms": ["quick,fast", "jump,leap,hop"]
    }
  ],
  "text": "quick fox jumps"
}
```

#### 3. 测试 N-gram

```json
POST /_analyze
{
  "tokenizer": "standard",
  "filter": [
    {
      "type": "edge_ngram",
      "min_gram": 2,
      "max_gram": 10
    }
  ],
  "text": "Elasticsearch"
}

// 结果：[El, Els, Elas, Elast, Elasti, Elastic, Elasticse, Elasticsear, Elasticsearch]
```

---

## 面试题精选

### 1. Elasticsearch 的分词流程是怎样的？Character Filter、Tokenizer、Token Filter 分别起什么作用？

**答案要点：**

**分词流程：**
1. **Character Filter**：预处理原始文本，如去除 HTML 标签、替换字符
2. **Tokenizer**：核心分词，将文本切分为词条
3. **Token Filter**：后处理，如转小写、去停用词、同义词处理

**各组件作用：**
- Character Filter：文本清洗，在分词前执行
- Tokenizer：文本切分，决定如何拆分文本
- Token Filter：词条加工，优化搜索结果

### 2. text 和 keyword 类型有什么区别？如何选择？

**答案要点：**

| 特性 | text | keyword |
|------|------|---------|
| 分词 | 是 | 否 |
| 用途 | 全文搜索 | 精确匹配、排序、聚合 |
| 存储 | 分词后的词条 | 原始值 |
| 支持操作 | match、query_string | term、terms、排序、聚合 |

**选择原则：**
- 需要全文搜索 → text
- 需要精确匹配、过滤、排序、聚合 → keyword
- 两者都需要 → 使用 multi-fields（text + keyword）

### 3. IK 分词器的 ik_max_word 和 ik_smart 有什么区别？

**答案要点：**

- **ik_max_word**：细粒度切分，会将文本切分到最细，索引时使用，提高召回率
- **ik_smart**：智能切分，做最粗粒度的拆分，搜索时使用，提高精确度

**最佳实践：**
```json
{
  "title": {
    "type": "text",
    "analyzer": "ik_max_word",      // 索引时使用细粒度
    "search_analyzer": "ik_smart"   // 搜索时使用智能模式
  }
}
```

### 4. 什么是 nested 类型？什么时候需要使用它？

**答案要点：**

**nested 类型：**
- 用于存储对象数组
- 保持数组中每个对象的独立性
- 避免对象数组的扁平化问题

**使用场景：**
当需要独立查询对象数组中的字段时，如订单中的商品列表：

```json
// 不使用 nested（有问题）
{ "items": [{"name": "A", "price": 100}, {"name": "B", "price": 200}] }
// 查询 name=A AND price=200 会错误匹配

// 使用 nested（正确）
{ "items": [{"name": "A", "price": 100}, {"name": "B", "price": 200}] }
// nested 查询确保匹配同一对象内的字段
```

### 5. Dynamic Mapping 有什么优缺点？生产环境如何使用？

**答案要点：**

**优点：**
- 快速开发，无需预先定义字段
- 自动推断字段类型
- 适应数据结构变化

**缺点：**
- 类型推断可能不准确（如字符串默认是 text + keyword）
- 可能造成存储浪费
- 字段爆炸问题（mapping 过大）

**生产环境建议：**
1. 显式定义核心字段的 mapping
2. 使用 `dynamic: strict` 防止意外字段
3. 或使用 Dynamic Templates 自定义映射规则
4. 定期审查索引 mapping，优化字段类型
