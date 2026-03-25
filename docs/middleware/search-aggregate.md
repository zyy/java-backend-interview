---
layout: default
title: ES 搜索与聚合
---
# ES 搜索与聚合

> Elasticsearch 查询

## 🎯 面试重点

- 查询语法
- 聚合分析

## 📖 查询

### 查询语法

```java
/**
 * 查询
 */
public class ESSearch {
    // match_all
    /*
     * 查询所有
     */
    
    // match
    /*
     * 全文搜索
     * {
     *   "query": {
     *     "match": { "title": "java" }
     *   }
     * }
     */
    
    // term
    /*
     * 精确匹配
     */
    
    // bool
    /*
     * 组合查询
     * must / should / must_not
     */
}
```

## 📖 聚合

```java
/**
 * 聚合
 */
public class ESAggregation {
    // terms
    /*
     * 分组统计
     */
    
    // avg / sum / max / min
    /*
     * 数值计算
     */
    
    // date_histogram
    /*
     * 时间分布
     */
}
```

## 📖 面试真题

### Q1: match 和 term 区别？

**答：** match 分词后匹配，term 精确匹配。

---

**⭐ 重点：ES 查询是搜索系统的核心**