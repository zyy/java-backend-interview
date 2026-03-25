---
layout: default
title: JVM 原理
---
# JVM 原理

> JVM 是区分初级和高级 Java 开发者的关键知识点

## 📋 内容大纲

### 1. JVM 内存模型 ⭐⭐
- [运行时数据区](./runtime-data-areas.md) ⭐⭐
- [对象内存布局](./object-memory-layout.md)
- [内存分配策略](./memory-allocation.md)

### 2. 类加载机制 ⭐⭐
- [类加载过程](./class-loading-process.md) ⭐⭐
- [双亲委派模型](./parent-delegation.md)
- [打破双亲委派](./break-delegation.md)

### 3. 垃圾回收 ⭐⭐⭐
- [垃圾回收算法详解](./gc-algorithms.md) ⭐⭐⭐
- [G1、ZGC、Shenandoah](./modern-gc.md)
- [GC 调优实战](./gc-tuning.md)

### 4. 性能监控与调优 ⭐⭐⭐
- [常用监控工具](./monitoring-tools.md)
- [线上问题排查](./troubleshooting.md)
- [JVM 参数配置](./jvm-parameters.md)

## 🎯 面试高频题

1. **[JVM 内存区域如何划分？各区域作用？](./runtime-data-areas.md)**
2. **[垃圾回收算法有哪些？各有什么优缺点？](./gc-algorithms.md)**
3. **[CMS 和 G1 的区别？](./modern-gc.md)**
4. **[类加载的双亲委派模型是什么？](./parent-delegation.md)**
5. **[线上出现 OOM 如何排查？](./troubleshooting.md)**

## 📚 延伸阅读

- [JVM 规范](https://docs.oracle.com/javase/specs/jvms/se8/html/)
- [Java Performance](https://book.douban.com/subject/26740503/)
