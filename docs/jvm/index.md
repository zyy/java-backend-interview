# JVM 原理

> JVM 是区分初级和高级 Java 开发者的关键知识点
> **提示**：我们提供了两种访问方式：
> 1. **合并文档**：[jvm-combined.md](./jvm-combined.md) - 所有主题一文档
> 2. **独立文档**：下方链接指向具体主题的独立文档

## 📋 内容大纲

### 1. JVM 内存模型 ⭐⭐
- [运行时数据区](./jvm-combined.md#11-运行时数据区) | [独立文档](./runtime-data-areas.md)
- [对象内存布局](./jvm-combined.md#12-对象内存布局) | [独立文档](./object-memory-layout.md)
- [内存分配策略](./jvm-combined.md#13-内存分配策略) | [独立文档](./memory-allocation.md)

### 2. 垃圾回收 ⭐⭐⭐
- [垃圾回收算法详解](./jvm-combined.md#21-垃圾回收算法详解) | [独立文档](./gc-algorithms.md)
- [G1、ZGC、Shenandoah](./jvm-combined.md#22-g1zgc-shenandoah现代-gc) | [独立文档](./modern-gc.md)
- [GC 调优实战](./jvm-combined.md#23-gc-调优实战) | [独立文档](./gc-tuning.md)

### 3. 类加载机制 ⭐⭐
- [类加载过程](./jvm-combined.md#31-类加载过程) | [独立文档](./class-loading-process.md)
- [双亲委派模型](./jvm-combined.md#32-双亲委派模型) | [独立文档](./parent-delegation.md)
- [打破双亲委派](./jvm-combined.md#33-打破双亲委派) | [独立文档](./break-delegation.md)

### 4. 性能监控与调优 ⭐⭐⭐
- [常用监控工具](./jvm-combined.md#41-常用监控工具) | [独立文档](./monitoring-tools.md)
- [线上问题排查](./jvm-combined.md#42-线上问题排查) | [独立文档](./troubleshooting.md)
- [JVM 参数配置](./jvm-combined.md#43-jvm-参数配置) | [独立文档](./jvm-parameters.md)

## 🎯 面试高频题

1. **JVM 内存区域如何划分？各区域作用？** ([合并文档](./jvm-combined.md#11-运行时数据区) | [独立文档](./runtime-data-areas.md))
2. **[垃圾回收算法有哪些？各有什么优缺点？](./jvm-combined.md#21-垃圾回收算法详解) | [独立文档](./gc-algorithms.md)**
3. **CMS 和 G1 的区别？** ([合并文档](./jvm-combined.md#22-g1zgc-shenandoah现代-gc) | [独立文档](./modern-gc.md))
4. **类加载的双亲委派模型是什么？** ([合并文档](./jvm-combined.md#32-双亲委派模型) | [独立文档](./parent-delegation.md))
5. **线上出现 OOM 如何排查？** ([合并文档](./jvm-combined.md#42-线上问题排查) | [独立文档](./troubleshooting.md))

## 🎯 使用建议
- **系统学习**：使用合并文档 [jvm-combined.md](./jvm-combined.md)
- **专题深入**：点击独立文档链接查看详细内容
- **统一维护**：主要更新合并文档，保持一致性

## 📚 延伸阅读

- [JVM 规范](https://docs.oracle.com/javase/specs/jvms/se8/html/)
- [Java Performance](https://book.douban.com/subject/26740503/)
