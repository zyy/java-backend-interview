# ES 性能优化

> Elasticsearch 调优

## 🎯 面试重点

- 索引优化
- 查询优化

## 📖 索引优化

```java
/**
 * 索引优化
 */
public class ESIndexOptimization {
    // 分片数量
    /*
     * 主分片：每个节点 1-2 个
     * 副本：至少 1 个
     */
    
    // 批量写入
    /*
     * 使用 bulk API
     */
    
    // 刷新间隔
    /*
     * index.refresh_interval: 30s
     */
}
```

## 📖 查询优化

```java
/**
 * 查询优化
 */
public class ESQueryOptimization {
    // 使用 filter
    /*
     * filter 不计算得分，可缓存
     */
    
    // 避免深分页
    /*
     * 使用 scroll 或 search_after
     */
}
```

## 📖 面试真题

### Q1: 深分页问题？

**答：** 使用 scroll 或 search_after 替代 from/size。

---

**⭐ 重点：ES 优化影响搜索性能**