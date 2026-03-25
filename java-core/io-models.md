# BIO、NIO、AIO 区别 ⭐⭐

## 面试题：说说 BIO、NIO、AIO 的区别

### 核心回答

BIO、NIO、AIO 是 Java 中三种不同的 I/O 模型，分别代表同步阻塞、同步非阻塞、异步非阻塞 I/O。

### 三种 I/O 模型对比

| 特性 | BIO | NIO | AIO |
|------|-----|-----|-----|
| **全称** | Blocking I/O | Non-blocking I/O | Asynchronous I/O |
| **JDK 版本** | 1.0 | 1.4 | 1.7 |
| **I/O 模型** | 同步阻塞 | 同步非阻塞 | 异步非阻塞 |
| **线程模型** | 一个连接一个线程 | 一个线程处理多个连接 | 回调驱动 |
| **适用场景** | 连接数少 | 连接数多、短连接 | 连接数多、长连接 |
| **API 位置** | java.io | java.nio | java.nio.channels |

### 同步 vs 异步，阻塞 vs 非阻塞

```
同步/异步：消息通知机制（被调用方是否主动通知）
阻塞/非阻塞：等待结果时的状态（是否挂起）

同步阻塞（BIO）：
  你去书店买书，问老板有没有《Java并发编程》
  老板说："我查一下"，你站着等，直到老板找到书

同步非阻塞（NIO）：
  你去书店买书，问老板有没有《Java并发编程》
  老板说："我查一下"，你去旁边玩手机，过一会儿来问一次

异步非阻塞（AIO）：
  你去书店买书，问老板有没有《Java并发编程》，留下电话号码
  老板说："找到了给你打电话"，你去干别的事
  老板找到后打电话通知你
```

### BIO（同步阻塞）

#### 工作原理

```
Client → Socket → ServerSocket → 新建线程处理

每个连接需要一个独立线程：
┌─────────┐     ┌─────────────┐     ┌─────────┐
│ Client1 │────→│ ServerSocket│────→│ Thread1 │
│ Client2 │────→│   监听端口   │────→│ Thread2 │
│ Client3 │────→│             │────→│ Thread3 │
└─────────┘     └─────────────┘     └─────────┘
```

#### 代码示例

```java
// 服务端
public class BIOServer {
    public static void main(String[] args) throws IOException {
        ServerSocket serverSocket = new ServerSocket(8080);
        
        while (true) {
            // 阻塞等待客户端连接
            Socket socket = serverSocket.accept();
            
            // 新建线程处理
            new Thread(() -> {
                try {
                    handle(socket);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }).start();
        }
    }
    
    private static void handle(Socket socket) throws IOException {
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(socket.getInputStream()));
        
        // 阻塞读取数据
        String line;
        while ((line = reader.readLine()) != null) {
            System.out.println("收到: " + line);
        }
    }
}
```

#### 缺点

1. **线程开销大**：每个连接需要一个线程
2. **阻塞等待**：线程大部分时间处于阻塞状态
3. **C10K 问题**：无法处理大量并发连接

### NIO（同步非阻塞）

#### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                         NIO                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Channel   │  │   Buffer    │  │    Selector     │ │
│  │  (双向通道)  │  │   (缓冲区)   │  │   (多路复用器)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 工作原理

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│ Client1 │────→│             │     │             │
│ Client2 │────→│   Selector  │────→│  单线程处理  │
│ Client3 │────→│  (轮询事件)  │     │             │
└─────────┘     └─────────────┘     └─────────────┘

Selector 可以监控多个 Channel 的事件：
- OP_ACCEPT：接受连接
- OP_CONNECT：连接建立
- OP_READ：可读
- OP_WRITE：可写
```

#### 代码示例

```java
// NIO 服务端
public class NIOServer {
    public static void main(String[] args) throws IOException {
        // 1. 创建 Selector
        Selector selector = Selector.open();
        
        // 2. 创建 ServerSocketChannel
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);  // 非阻塞模式
        
        // 3. 注册到 Selector
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);
        
        while (true) {
            // 4. 轮询事件（阻塞等待，直到有事件发生）
            selector.select();
            
            // 5. 获取就绪的事件
            Iterator<SelectionKey> keys = selector.selectedKeys().iterator();
            
            while (keys.hasNext()) {
                SelectionKey key = keys.next();
                keys.remove();
                
                if (key.isAcceptable()) {
                    // 接受新连接
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);
                } else if (key.isReadable()) {
                    // 读取数据
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    int read = client.read(buffer);
                    
                    if (read > 0) {
                        buffer.flip();
                        byte[] data = new byte[buffer.remaining()];
                        buffer.get(data);
                        System.out.println("收到: " + new String(data));
                    }
                }
            }
        }
    }
}
```

#### 零拷贝（Zero-Copy）

```
传统 I/O：
磁盘 → 内核缓冲区 → 用户缓冲区 → Socket 缓冲区 → 网卡
   （4 次拷贝，4 次上下文切换）

NIO 零拷贝（transferTo）：
磁盘 → 内核缓冲区 → 网卡
   （2 次拷贝，2 次上下文切换）

FileChannel.transferTo(position, count, targetChannel);
```

### AIO（异步非阻塞）

#### 工作原理

```
Client 发起请求 → 立即返回
                      ↓
              操作系统处理 I/O
                      ↓
         完成后回调 CompletionHandler
                      ↓
               应用程序处理结果
```

#### 代码示例

```java
// AIO 服务端
public class AIOServer {
    public static void main(String[] args) throws IOException, InterruptedException {
        // 创建异步通道组
        AsynchronousChannelGroup group = AsynchronousChannelGroup.withThreadPool(
            Executors.newFixedThreadPool(4));
        
        // 创建异步服务端 Socket
        AsynchronousServerSocketChannel server = 
            AsynchronousServerSocketChannel.open(group);
        server.bind(new InetSocketAddress(8080));
        
        // 接受连接（异步）
        server.accept(null, new CompletionHandler<AsynchronousSocketChannel, Void>() {
            @Override
            public void completed(AsynchronousSocketChannel client, Void attachment) {
                // 继续接受下一个连接
                server.accept(null, this);
                
                // 读取数据（异步）
                ByteBuffer buffer = ByteBuffer.allocate(1024);
                client.read(buffer, buffer, new CompletionHandler<Integer, ByteBuffer>() {
                    @Override
                    public void completed(Integer result, ByteBuffer buffer) {
                        buffer.flip();
                        byte[] data = new byte[buffer.remaining()];
                        buffer.get(data);
                        System.out.println("收到: " + new String(data));
                    }
                    
                    @Override
                    public void failed(Throwable exc, ByteBuffer buffer) {
                        exc.printStackTrace();
                    }
                });
            }
            
            @Override
            public void failed(Throwable exc, Void attachment) {
                exc.printStackTrace();
            }
        });
        
        // 保持主线程运行
        Thread.sleep(Long.MAX_VALUE);
    }
}
```

### 三种模型对比图示

```
BIO（同步阻塞）：
┌──────┐     ┌──────┐     ┌──────┐
│ 用户 │────→│ 内核 │────→│ 设备 │
│ 线程 │←────│ 等待 │←────│      │
└──────┘     └──────┘     └──────┘
   全程阻塞

NIO（同步非阻塞）：
┌──────┐     ┌──────┐     ┌──────┐
│ 用户 │────→│ 内核 │────→│ 设备 │
│ 线程 │←────│ 就绪 │←────│      │
└──────┘     └──────┘     └──────┘
   轮询检查就绪状态

AIO（异步非阻塞）：
┌──────┐     ┌──────┐     ┌──────┐
│ 用户 │────→│ 内核 │────→│ 设备 │
│ 线程 │     │ 处理 │     │      │
└──────┘     └──────┘     └──────┘
      ↓ 回调通知
   ┌──────────┐
   │ 处理结果  │
   └──────────┘
```

### 使用场景

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 连接数 < 1000 | BIO | 代码简单，性能足够 |
| 连接数 > 1000，短连接 | NIO | 高并发，节省线程 |
| 连接数 > 1000，长连接 | AIO | 异步处理，最高效 |
| 文件传输 | NIO | 零拷贝，高性能 |
| 实时通信 | NIO/AIO | 非阻塞，响应快 |

### Netty 的选择

```
Netty 使用 NIO 而非 AIO，原因：

1. Linux 下 AIO 实现不完善
   - Linux AIO 是基于线程池模拟的
   - 性能不如 NIO + epoll

2. NIO 已经足够高效
   - epoll 可以处理百万级连接
   - 代码更成熟稳定

3. 跨平台考虑
   - NIO 在各平台表现一致
   - AIO 在 Windows 和 Linux 差异大
```

### 高频面试题

**Q1: NIO 为什么是同步而不是异步？**

```
NIO 的"同步"体现在：
- 用户线程需要主动调用 select() 检查 I/O 状态
- 数据读写需要用户线程自己执行

真正的异步（AIO）：
- 用户线程发起 I/O 后立即返回
- 操作系统完成 I/O 后通知用户线程
- 用户线程只需处理结果
```

**Q2: Selector 的 select() 会阻塞吗？**

```java
// 会阻塞，直到有就绪的 Channel
selector.select();

// 设置超时时间
selector.select(1000);  // 阻塞 1 秒

// 立即返回，不阻塞
selector.selectNow();
```

**Q3: NIO 的 Buffer 为什么要 flip()？**

```java
ByteBuffer buffer = ByteBuffer.allocate(1024);

// 写模式（默认）
channel.read(buffer);  // 数据写入 buffer

// 切换为读模式
buffer.flip();
// position = 0, limit = 之前 position 的位置

// 读取数据
while (buffer.hasRemaining()) {
    byte b = buffer.get();
}

// 清空，重新变为写模式
buffer.clear();
// position = 0, limit = capacity
```

**Q4: 什么是多路复用？**

```
多路复用（Multiplexing）：
一个线程同时监控多个 I/O 通道，哪个有数据就处理哪个。

Linux 实现：
- select/poll：遍历所有 fd，O(n)
- epoll：事件驱动，O(1)

Java NIO 在 Linux 下使用 epoll
```

### 最佳实践

```java
// 1. NIO 使用 DirectBuffer（堆外内存）
ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024);
// 优点：减少一次内存拷贝
// 缺点：分配和回收成本高

// 2. 使用线程池处理 NIO 业务逻辑
ExecutorService workerPool = Executors.newFixedThreadPool(4);
selector.select();
for (SelectionKey key : selector.selectedKeys()) {
    if (key.isReadable()) {
        workerPool.submit(() -> process(key));
    }
}

// 3. 注意 ByteBuffer 的复用
// 使用 ThreadLocal 或对象池避免频繁创建
```

---

**参考链接：**
- [Java 中的 BIO、NIO 和 AIO 区别-CSDN](https://blog.csdn.net/2202_75481735/article/details/145969931)
- [BIO,NIO,AIO 的区别-博客园](https://www.cnblogs.com/chenlei210162701002/p/18434486)
