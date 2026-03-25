---
layout: default
title: 分布式链路追踪
---
# 分布式链路追踪

> 微服务调用链追踪

## 🎯 面试重点

- 链路追踪原理
- 主流方案

## 📖 核心概念

```java
/**
 * 核心概念
 */
public class TracingConcepts {
    // Trace
    /*
     * 一次请求的完整调用链
     */
    
    // Span
    /*
     * 一次调用过程
     */
    
    // Annotation
    /*
     * 时间点标记
     * cs: client send
     * sr: server receive
     * ss: server send
     * cr: client receive
     */
}
```

## 📖 主流方案

```java
/**
 * 主流方案
 */
public class TracingSolutions {
    // Zipkin
    /*
     * Twitter 开源
     */
    
    // SkyWalking
    /*
     * 国产 APM，无侵入
     */
    
    // Jaeger
    /*
     * Uber 开源
     */
}
```

## 📖 面试真题

### Q1: 链路追踪的作用？

**答：** 问题定位、性能分析、依赖分析。

---

**⭐ 重点：链路追踪是微服务治理的基础**