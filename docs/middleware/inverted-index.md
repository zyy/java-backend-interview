---
layout: default
title: 倒排索引原理
---
# 倒排索引原理

> ES 核心数据结构

## 🎯 面试重点

- 倒排索引结构
- 与正排索引的区别

## 📖 原理

### 正排 vs 倒排

```java
/**
 * 正排索引
 */
public class ForwardIndex {
    /*
     * document -> terms
     * doc1 -> [hello, world]
     * doc2 -> [hello, java]
     */
}

/**
 * 倒排索引
 */
public class InvertedIndex {
    /*
     * term -> documents
     * hello -> [doc1, doc2]
     * world -> [doc1]
     * java -> [doc2]
     */
}
```

## 📖 面试真题

### Q1: 倒排索引的优点？

**答：** 查询快，时间复杂度 O(1)。

---

**⭐ 重点：倒排索引是搜索引擎的核心**