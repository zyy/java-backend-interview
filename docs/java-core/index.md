# Java 核心基础

> Java 基础是后端面试的重中之重，务必扎实掌握
> **提示**：我们提供了两种访问方式：
> 1. **合并文档**：[java-core-combined.md](./java-core-combined.md) - 所有主题一文档
> 2. **独立文档**：下方链接指向具体主题的独立文档

## 📋 内容大纲

### 1. 基础语法 ⭐
- [数据类型与包装类](./java-core-combined.md#11-数据类型与包装类) | [独立文档](./basic-types.md)
- [String、StringBuilder、StringBuffer](./java-core-combined.md#12-stringstringbuilderstringbuffer) | [独立文档](./string.md)
- [equals 与 hashCode](./java-core-combined.md#13-equals-与-hashcode) | [独立文档](./equals-hashcode.md)
- [泛型机制](./java-core-combined.md#14-泛型机制) | [独立文档](./generics.md)
- [注解与反射](./java-core-combined.md#15-注解与反射) | [独立文档](./annotation-reflection.md)

### 2. 集合框架 ⭐⭐
- [ArrayList vs LinkedList](./java-core-combined.md#21-arraylist-vs-linkedlist) | [独立文档](./list.md)
- [HashMap 原理详解](./java-core-combined.md#22-hashmap-原理详解) | [独立文档](./hashmap.md)
- [ConcurrentHashMap](./java-core-combined.md#23-concurrenthashmap) | [独立文档](./concurrent-hashmap.md)
- [其他集合类对比](./java-core-combined.md#24-其他集合类对比) | [独立文档](./collections-compare.md)

### 3. 并发编程 ⭐⭐⭐
- [线程池核心参数详解](./java-core-combined.md#31-线程池核心参数详解) | [独立文档](./thread-pool.md)
- [synchronized 与锁升级](./java-core-combined.md#32-synchronized-与锁升级) | [独立文档](./synchronized.md)
- [volatile 与内存屏障](./java-core-combined.md#33-volatile-与内存屏障) | [独立文档](./volatile.md)
- [CAS 与 AQS 原理](./java-core-combined.md#34-cas-与-aqs-原理) | [独立文档](./cas-aqs.md)
- [ThreadLocal 原理与内存泄漏](./java-core-combined.md#35-threadlocal-原理与内存泄漏) | [独立文档](./threadlocal.md)

### 4. IO/NIO ⭐⭐
- [BIO、NIO、AIO 区别](./java-core-combined.md#41-bionioaio-区别) | [独立文档](./io-models.md)
- [Netty 基础](./java-core-combined.md#42-netty-基础) | [独立文档](./netty-basics.md)

## 🎯 面试高频题

1. **[HashMap 的 put 流程是怎样的？](./java-core-combined.md#22-hashmap-原理详解) | [独立文档](./hashmap.md)**
2. **[ConcurrentHashMap 如何保证线程安全？](./java-core-combined.md#23-concurrenthashmap) | [独立文档](./concurrent-hashmap.md)**
3. **[线程池的核心参数有哪些？如何合理配置？](./java-core-combined.md#31-线程池核心参数详解) | [独立文档](./thread-pool.md)**
4. **[String、StringBuilder、StringBuffer 的区别？](./java-core-combined.md#12-stringstringbuilderstringbuffer) | [独立文档](./string.md)**
5. **[synchronized 的锁升级过程？](./java-core-combined.md#32-synchronized-与锁升级) | [独立文档](./synchronized.md)**
6. **[volatile 能保证原子性吗？为什么？](./java-core-combined.md#33-volatile-与内存屏障) | [独立文档](./volatile.md)**
7. **[ArrayList 和 LinkedList 的区别？](./java-core-combined.md#21-arraylist-vs-linkedlist) | [独立文档](./list.md)**
8. **[ThreadLocal 为什么会内存泄漏？如何解决？](./java-core-combined.md#35-threadlocal-原理与内存泄漏) | [独立文档](./threadlocal.md)**
9. **[CAS 和 AQS 的原理？](./java-core-combined.md#34-cas-与-aqs-原理) | [独立文档](./cas-aqs.md)**
10. **[BIO、NIO、AIO 的区别？](./java-core-combined.md#41-bionioaio-区别) | [独立文档](./io-models.md)**

## 🎯 使用建议
- **快速查阅**：使用合并文档 [java-core-combined.md](./java-core-combined.md)
- **深入学习**：点击独立文档链接查看详细内容
- **后期维护**：主要更新合并文档，独立文档作为参考备份

## 📚 延伸阅读

- [Java 官方文档](https://docs.oracle.com/javase/8/docs/)
- [深入理解 Java 虚拟机](https://book.douban.com/subject/34907497/)
