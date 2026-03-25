# Netty 基础

> 高性能网络编程框架

## 🎯 面试重点

- Netty 核心概念
- 线程模型
- 零拷贝

## 📖 核心概念

### 线程模型

```java
/**
 * Netty 线程模型
 */
public class NettyThreadModel {
    // Reactor 模型
    /*
     * Boss Group：处理连接
     * Worker Group：处理 IO
     * 
     * 步骤：
     * 1. Boss 接收连接
     * 2. 注册到 Worker
     * 3. Worker 处理读写
     */
}
```

### 核心组件

```java
/**
 * 核心组件
 */
public class NettyComponents {
    // Channel
    /*
     * 通道，封装 Socket
     */
    
    // EventLoop
    /*
     * 事件循环，处理 IO 事件
     */
    
    // ChannelPipeline
    /*
     * 处理器链
     */
    
    // ByteBuf
    /*
     * 字节缓冲区
     * 对比 ByteBuffer：
     * - 堆内存/直接内存
     * - 引用计数
     * - 动态扩容
     */
}
```

### 零拷贝

```java
/**
 * 零拷贝
 */
public class ZeroCopy {
    // Netty 零拷贝
    /*
     * 1. 使用 ByteBuf，堆外内存直接传输
     * 2. CompositeByteBuf 合并多个 Buffer
     * 3. 文件传输使用 sendfile
     */
}
```

## 📖 面试真题

### Q1: Netty 为什么快？

**答：** 零拷贝、I/O 多路复用、内存池、无锁化。

---

**⭐ 重点：Netty 是高性能网络编程的基础**