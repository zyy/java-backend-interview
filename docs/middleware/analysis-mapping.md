---
layout: default
title: ES 分词与映射
---
# ES 分词与映射

> Elasticsearch 分析器

## 🎯 面试重点

- 分词器类型
- Mapping 字段映射

## 📖 分词器

### 分词器类型

```java
/**
 * 分词器
 */
public class Analyzers {
    // standard
    /*
     * 默认分词器，按空格分
     */
    
    // ik_smart / ik_max_word
    /*
     * 中文分词
     */
    
    // keyword
    /*
     * 不分词
     */
}
```

## 📖 Mapping

```java
/**
 * 映射
 */
public class MappingDemo {
    /*
     * {
     *   "properties": {
     *     "title": {
     *       "type": "text",
     *       "analyzer": "ik_max_word"
     *     },
     *     "status": {
     *       "type": "keyword"
     *     }
     *   }
     * }
     */
}
```

## 📖 面试真题

### Q1: text 和 keyword 区别？

**答：** text 分词，keyword 不分词。

---

**⭐ 重点：分词是搜索的基础**