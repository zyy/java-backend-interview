---
layout: default
title: 手写 RPC 框架：从原理到实现 ⭐⭐
---

# 手写 RPC 框架：从原理到实现 ⭐⭐

## 一、RPC 是什么？它解决了什么问题？

**RPC（Remote Procedure Call，远程过程调用）** 是一种计算机通信协议，允许程序像调用本地方法一样调用另一台计算机上的程序或服务。RPC 的目标是用简单透明的方式屏蔽网络通信的复杂性，让开发者无需关注数据如何序列化、如何通过网络传输、如何在另一端反序列化。

在微服务架构中，RPC 是服务间通信的基础设施。一个典型的 RPC 调用过程：

```java
// 像调用本地方法一样
User user = userService.getUserById(1001);

// 但实际上这是一次网络通信
// 数据经过：序列化 → 网络传输 → 服务端反序列化 → 方法执行
//         → 结果序列化 → 网络传输 → 客户端反序列化 → 返回结果
```

## 二、RPC vs HTTP/REST vs MQ

### 2.1 三种通信模式对比

| 特性 | RPC | HTTP/REST | MQ（消息队列） |
|---|---|---|---|
| **通信模式** | 请求-响应（同步） | 请求-响应（同步） | 发布-订阅（异步） |
| **调用方式** | 像调用本地方法 | 通过 HTTP 资源接口 | 生产者发送消息，消费者异步处理 |
| **性能** | 高（自定义协议，二进制序列化） | 中等（JSON/XML 序列化） | 高（异步不阻塞） |
| **适用场景** | 微服务内部调用、低延迟场景 | 跨语言、对外开放 API | 异步解耦、流量削峰、事件驱动 |
| **错误处理** | 超时、重试、熔断 | 依赖 HTTP 状态码 | 消息持久化、消费重试、死信队列 |
| **耦合性** | 服务间紧耦合（需要知道对方接口） | 松耦合（只需知道资源地址） | 完全解耦（通过消息主题） |
| **典型框架** | Dubbo、gRPC、Thrift | Spring MVC、Express | Kafka、RocketMQ、RabbitMQ |

### 2.2 RPC 与 HTTP/REST 的本质区别

**协议层面：** HTTP 是一种标准化的应用层协议，有明确的规范（Method、Header、Status Code）；RPC 可以基于 TCP 自定义协议，也可以基于 HTTP/2。

**序列化层面：** HTTP/REST 通常使用 JSON 或 XML，human-readable 但体积大、解析慢；RPC 通常使用二进制序列化（Protobuf、Hessian），体积小、解析快。

**性能层面：** 在高并发、低延迟场景下，RPC 框架通常比 REST API 快 3-10 倍。

**使用体验：** REST API 通过 HTTP URL 调用，RPC 像调用本地方法一样调用远程服务（通过 Stub/Proxy）。

### 2.3 何时用 RPC，何时用 MQ？

- **需要同步等待结果** → RPC
- **需要极低延迟（毫秒级）** → RPC
- **上下游处理速度不匹配，需要异步解耦** → MQ
- **下游服务可能不可用，需要流量削峰** → MQ
- **跨语言、对外开放接口** → HTTP/REST

## 三、RPC 的基本原理

### 3.1 核心组件

一个完整的 RPC 框架包含以下核心组件：

```
┌─────────────────────────────────────────────────────────┐
│                      RPC 框架                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Stub（客户端）│  │Skeleton(服务端)│  │ 注册中心(Registry) │  │
│  │  负责发起调用 │  │负责接收调用   │  │  服务注册与发现   │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
│         │                │                   │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌────────▼────────┐  │
│  │ 序列化(Serialize)│  │反序列化(Deserialize)│ │ 负载均衡(LoadBalance)│  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────┘  │
│         │                │                                │
│  ┌──────▼─────────────────▼────────────────────────────┐  │
│  │              传输层（Transport Layer）                │  │
│  │        TCP 长连接 / Netty / HTTP/2                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 调用流程详解

```
客户端                                              服务端
  │                                                    │
  │ 1. 调用本地 Stub 接口方法                            │
  │   userService.getUserById(1001)                    │
  │                                                    │
  │ 2. Stub 序列化请求参数                              │
  │   → 序列化: {method: "getUserById", args: [1001]}   │
  │                                                    │
  │ 3. Stub 通过传输层发送请求                          │
  │   ==========================================>        │
  │   (TCP 连接 + 序列化字节流)                         │
  │                                                    │
  │                     Skeleton 反序列化请求           │
  │                     根据方法名定位实现类             │
  │                     调用本地方法                     │
  │                     userService.getUserById(1001)  │
  │                                                    │
  │ 4. Skeleton 序列化返回值                            │
  │   ←==========================================       │
  │   (序列化: {result: User{id=1001, name="张三"}})     │
  │                                                    │
  │ 5. Stub 反序列化返回值                              │
  │   返回 User 对象给调用方                             │
```

**Stub（客户端存根）：** 将远程调用接口的方法调用，转化为网络请求。它负责序列化参数、发送请求、接收响应、反序列化结果。

**Skeleton（服务端存根）：** 接收网络请求，反序列化请求参数，调用本地服务实现类，获取结果后序列化返回。

## 四、动态代理实现 RPC 客户端

动态代理是 RPC 框架实现"像调用本地方法一样调用远程服务"的核心技术。通过动态代理，调用方持有的是一个代理对象，该对象的方法调用会被拦截并转化为网络请求。

### 4.1 JDK 动态代理

JDK 动态代理要求被代理的类实现接口。

```java
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class JdkRpcProxy<T> implements InvocationHandler {

    private Class<T> interfaceClass;
    private String serviceVersion;
    private LoadBalancer loadBalancer;
    private List<ServiceNode> serviceNodes;

    /**
     * 创建代理对象
     */
    @SuppressWarnings("unchecked")
    public T createProxy(Class<T> interfaceClass, String serviceVersion,
                        List<ServiceNode> nodes, LoadBalancer loadBalancer) {
        this.interfaceClass = interfaceClass;
        this.serviceVersion = serviceVersion;
        this.serviceNodes = nodes;
        this.loadBalancer = loadBalancer;

        // 使用 JDK 动态代理创建代理对象
        // 任何对 proxy 对象的方法调用都会触发 invoke 方法
        return (T) Proxy.newProxyInstance(
            interfaceClass.getClassLoader(),  // 类加载器
            new Class<?>[]{interfaceClass},    // 代理实现的接口
            this                               // InvocationHandler
        );
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        // 跳过 Object 类的方法（如 toString, hashCode 等）
        if (Object.class.equals(method.getDeclaringClass())) {
            return method.invoke(this, args);
        }

        // 构建 RPC 请求
        RpcRequest request = RpcRequest.builder()
            .interfaceName(interfaceClass.getName())
            .methodName(method.getName())
            .parameterTypes(method.getParameterTypes())
            .parameters(args)
            .serviceVersion(this.serviceVersion)
            .requestId(UUID.randomUUID().toString())
            .timestamp(System.currentTimeMillis())
            .build();

        // 选择服务节点（负载均衡）
        ServiceNode node = loadBalancer.select(serviceNodes);

        // 通过 Netty 发送请求并获取响应
        RpcResponse response = nettyClient.sendRequest(request, node);

        // 返回结果
        if (response.isError()) {
            throw response.getError();
        }
        return response.getResult();
    }
}
```

### 4.2 CGLIB 动态代理

CGLIB 通过字节码生成技术，可以代理没有实现接口的类，性能比 JDK 动态代理更好（因为生成了真正的子类，调用不走反射）。

```java
import net.sf.cglib.proxy.Enhancer;
import net.sf.cglib.proxy.MethodInterceptor;
import net.sf.cglib.proxy.MethodProxy;

public class CglibRpcProxy implements MethodInterceptor {

    private LoadBalancer loadBalancer;
    private List<ServiceNode> serviceNodes;
    private Class<?> targetClass;

    public Object createProxy(Class<?> targetClass, List<ServiceNode> nodes,
                              LoadBalancer loadBalancer) {
        this.targetClass = targetClass;
        this.serviceNodes = nodes;
        this.loadBalancer = loadBalancer;

        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(targetClass);         // 设置父类
        enhancer.setCallback(this);                  // 设置回调
        return enhancer.create();                    // 创建代理对象
    }

    @Override
    public Object intercept(Object obj, Method method, Object[] args,
                            MethodProxy methodProxy) throws Throwable {
        // 构建 RPC 请求（同 JDK 代理）
        RpcRequest request = RpcRequest.builder()
            .interfaceName(targetClass.getName())
            .methodName(method.getName())
            .parameterTypes(method.getParameterTypes())
            .parameters(args)
            .build();

        ServiceNode node = loadBalancer.select(serviceNodes);
        RpcResponse response = nettyClient.sendRequest(request, node);

        if (response.isError()) {
            throw response.getError();
        }
        return response.getResult();
    }
}
```

### 4.3 Javassist 字节码增强

Javassist 是另一个字节码操作库，比 CGLIB 更底层，可以直接操作字节码指令：

```java
import javassist.*;

public class JavassistRpcProxy {

    public static <T> T createProxy(Class<T> interfaceClass,
                                    List<ServiceNode> nodes,
                                    LoadBalancer loadBalancer) throws Exception {
        ClassPool pool = ClassPool.getDefault();
        
        // 创建类名: XxxServiceProxy
        CtClass proxyClass = pool.makeClass(
            interfaceClass.getName() + "Proxy"
        );

        // 添加接口实现
        proxyClass.addInterface(pool.get(interfaceClass.getName()));

        // 添加成员变量
        CtClass nettyClientClass = pool.get(NettyClient.class.getName());
        CtField clientField = new CtField(nettyClientClass, "client", proxyClass);
        proxyClass.addField(clientField);

        // 添加构造方法
        CtConstructor constructor = new CtConstructor(
            new CtClass[]{nettyClientClass}, proxyClass
        );
        constructor.setBody("{ this.client = $1; }");
        proxyClass.addConstructor(constructor);

        // 为每个接口方法生成方法体
        for (CtMethod interfaceMethod : pool.get(interfaceClass.getName()).getMethods()) {
            CtMethod method = new CtMethod(interfaceMethod, proxyClass);
            method.setBody(
                "{ // 构建并发送 RPC 请求\n" +
                "   RpcRequest request = new RpcRequest();\n" +
                "   request.setMethodName(\"" + method.getName() + "\");\n" +
                "   request.setParameters($args);\n" +
                "   RpcResponse response = client.send(request);\n" +
                "   return ($r)response.getResult();\n" +
                "}"
            );
            proxyClass.addMethod(method);
        }

        Class<?> clazz = proxyClass.toClass();
        return interfaceClass.cast(clazz.getConstructor(NettyClient.class)
            .newInstance(nettyClient));
    }
}
```

## 五、Netty 实现传输层

Netty 是 Java 领域最流行的异步事件驱动网络框架，基于 NIO（Non-blocking I/O），非常适合构建高性能 RPC 框架的传输层。

### 5.1 为什么选择 Netty？

- **高性能：** 基于 NIO，零拷贝，内存池，线程池优化
- **可扩展：** 丰富的 ChannelHandler 生态，灵活的编解码框架
- **高可靠性：** 重连机制、心跳检测、流量控制
- **易用性：** 封装了 JDK NIO 的复杂性

### 5.2 LengthFieldBasedFrameDecoder 解决粘包半包

在 TCP 网络编程中，由于 TCP 是流式协议，可能出现**粘包**（多个小包合并成一个包）和**半包**（一个大包被拆分成多个小包）问题。

Netty 提供了多种解码器来解决这个问题，其中最常用的是 `LengthFieldBasedFrameDecoder`：

```
LengthFieldBasedFrameDecoder 工作原理：
在每个数据包头部加上一个长度字段，告诉解码器这个包有多长。

┌──────────────────────────┐
│  Length (4字节) │ Data    │ ← 完整的数据包
└──────────────────────────┘
   ↑ 4字节表示 Data 部分的字节数
```

**Java 实现：**

```java
public class NettyClient {

    private EventLoopGroup group = new NioEventLoopGroup();
    private Bootstrap bootstrap = new Bootstrap();

    public RpcResponse sendRequest(RpcRequest request, InetSocketAddress address) {
        try {
            Channel channel = bootstrap.connect(address).sync().channel();

            // 创建 RPC 响应处理器，用于异步接收响应
            RpcFuture<RpcResponse> future = new RpcFuture<>();
            pendingRequests.put(request.getRequestId(), future);

            // 发送请求
            channel.writeAndFlush(request);

            // 等待响应（带超时）
            return future.get(3000, TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            throw new RpcException("RPC 调用失败: " + e.getMessage(), e);
        }
    }

    public void init() {
        bootstrap.group(group)
            .channel(NioSocketChannel.class)
            .handler(new ChannelInitializer<SocketChannel>() {
                @Override
                protected void initChannel(SocketChannel ch) {
                    ChannelPipeline pipeline = ch.pipeline();

                    // ========== 编码器 ==========
                    // 1. 先序列化对象为字节数组
                    // 2. 在字节数组前加上 4 字节长度字段
                    pipeline.addLast(new RpcEncoder());

                    // ========== 解码器 ==========
                    // maxFrameLength: 最大帧大小（防止畸形数据）
                    // lengthFieldOffset: 长度字段的偏移量
                    // lengthFieldLength: 长度字段本身占的字节数
                    // lengthAdjustment: 长度调整值
                    // initialBytesToStrip: 解析后从帧头部跳过的字节数
                    pipeline.addLast(new LengthFieldBasedFrameDecoder(
                        65535,     // maxFrameLength: 单帧最大 64KB
                        0,         // lengthFieldOffset: 长度字段在第 0 字节开始
                        4,         // lengthFieldLength: 长度字段占 4 字节
                        0,         // lengthAdjustment: 长度值就是 Body 长度，无需调整
                        4          // initialBytesToStrip: 解码后跳过前 4 字节（长度字段）
                    ));

                    // 解码后的字节数组 → RpcRequest/RpcResponse 对象
                    pipeline.addLast(new RpcDecoder());

                    // 业务处理器：处理接收到的响应
                    pipeline.addLast(new RpcClientHandler());
                }
            })
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 3000);
    }
}
```

### 5.3 服务端处理器

```java
public class NettyServer {

    private ServerBootstrap bootstrap = new ServerBootstrap();
    private EventLoopGroup bossGroup = new NioEventLoopGroup(1);
    private EventLoopGroup workerGroup = new NioEventLoopGroup();

    public void bind(int port) {
        bootstrap.group(bossGroup, workerGroup)
            .channel(NioServerSocketChannel.class)
            .childHandler(new ChannelInitializer<SocketChannel>() {
                @Override
                protected void initChannel(SocketChannel ch) {
                    ChannelPipeline pipeline = ch.pipeline();
                    pipeline.addLast(new LengthFieldBasedFrameDecoder(65535, 0, 4, 0, 4));
                    pipeline.addLast(new RpcDecoder());
                    pipeline.addLast(new RpcEncoder());
                    pipeline.addLast(new RpcServerHandler());  // 核心业务处理
                }
            })
            .option(ChannelOption.SO_BACKLOG, 128)
            .childOption(ChannelOption.SO_KEEPALIVE, true);

        ChannelFuture f = bootstrap.bind(port).sync();
        System.out.println("RPC Server started on port " + port);
    }
}

/**
 * 服务端处理器：接收请求、执行业务逻辑、返回响应
 */
public class RpcServerHandler extends ChannelInboundHandlerAdapter {

    @Autowired
    private ServiceRegistry registry;

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        RpcRequest request = (RpcRequest) msg;
        RpcResponse response = new RpcResponse();
        response.setRequestId(request.getRequestId());

        try {
            // 1. 根据服务名和方法名找到对应的实现
            Object service = registry.getService(request.getInterfaceName());
            if (service == null) {
                throw new RpcException("Service not found: " + request.getInterfaceName());
            }

            // 2. 反射调用方法
            Method method = service.getClass().getMethod(
                request.getMethodName(),
                request.getParameterTypes()
            );
            method.setAccessible(true);
            Object result = method.invoke(service, request.getParameters());

            // 3. 设置返回结果
            response.setResult(result);

        } catch (Exception e) {
            response.setError(e);
        }

        // 4. 发送响应给客户端
        ctx.writeAndFlush(response);
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        cause.printStackTrace();
        ctx.close();
    }
}
```

## 六、注册中心：服务的注册与发现

### 6.1 为什么需要注册中心？

在微服务架构中，服务提供者的地址（IP:Port）是动态变化的（机器重启、水平扩容、故障下线等）。注册中心的作用是：

- **服务注册：** 服务启动时自动将自己的地址（IP:Port）注册到注册中心
- **服务发现：** 消费者从注册中心拉取或被推送服务提供者列表
- **健康检查：** 定期检测服务提供者是否存活，自动剔除不健康节点
- **动态上下线：** 支持服务实例的动态增删

### 6.2 ZooKeeper 实现注册中心

ZooKeeper 是一个高可靠性的分布式协调服务，其树形数据结构非常适合做服务注册中心：

```
/rpc
  /user-service          (持久节点，服务名)
    /192.168.1.10:8080   (临时节点，实例地址)
      data: "version=1.0,weight=1"
    /192.168.1.11:8080
      data: "version=1.0,weight=1"
  /order-service
    /192.168.1.20:8081
      data: "version=1.0,weight=2"
```

**ZooKeeper 服务注册实现：**

```java
public class ZookeeperServiceRegistry implements ServiceRegistry {

    private static final String ZK_ROOT_PATH = "/rpc";
    private ZooKeeper zooKeeper;

    public ZookeeperServiceRegistry(String zkAddress) {
        this.zooKeeper = new ZooKeeper(zkAddress, 5000, watchedEvent -> {
            if (watchedEvent.getType() == Event.EventType.NodeChildrenChanged) {
                // 服务列表变更通知（可用于推送更新）
                System.out.println("服务列表发生变化，重新获取...");
            }
        });
    }

    @Override
    public void register(String serviceName, InetSocketAddress address) {
        try {
            String path = ZK_ROOT_PATH + "/" + serviceName;
            
            // 创建持久化服务节点
            if (zooKeeper.exists(path, false) == null) {
                zooKeeper.create(path, null, 
                    ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
            }

            // 创建临时节点（服务实例）
            String instancePath = path + "/" + address.getHostString() + ":" + address.getPort();
            zooKeeper.create(instancePath,
                (serviceName + ":" + System.currentTimeMillis()).getBytes(),
                ZooDefs.Ids.OPEN_ACL_UNSAFE,
                CreateMode.EPHEMERAL  // 关键：临时节点，连接断开自动删除
            );
            System.out.println("服务注册成功: " + instancePath);

        } catch (Exception e) {
            throw new RpcException("ZooKeeper 注册失败", e);
        }
    }

    @Override
    public List<InetSocketAddress> discover(String serviceName) {
        try {
            String path = ZK_ROOT_PATH + "/" + serviceName;
            List<String> children = zooKeeper.getChildren(path, true);

            return children.stream().map(child -> {
                String[] parts = child.split(":");
                return new InetSocketAddress(parts[0], Integer.parseInt(parts[1]));
            }).collect(Collectors.toList());

        } catch (Exception e) {
            return Collections.emptyList();
        }
    }
}
```

### 6.3 etcd / Nacos

**etcd** 是 CoreOS 开发的分布式键值存储，基于 Raft 协议保证一致性，被 Kubernetes 用于服务发现。相比 ZooKeeper，etcd 更轻量，提供了 HTTP/gRPC API。

**Nacos** 是阿里巴巴开源的服务发现与配置管理平台，支持 AP（最终一致）和 CP（强一致）两种模式，提供 Console 控制台，UI 友好，是国内使用最广泛的注册中心之一。

```java
// Nacos 注册示例（使用 nacos-spring-boot-starter）
@NacosInjected
private NamingService namingService;

public void register() throws NacosException {
    // 注册服务：服务名 + IP + 端口 + 集群名
    namingService.registerInstance("user-service", "192.168.1.10", 8080, "DEFAULT_GROUP");
}

public List<Instance> getInstances() throws NacosException {
    // 获取服务所有实例
    return namingService.selectInstances("user-service", true);
}
```

## 七、负载均衡策略

### 7.1 随机策略（Random）

最简单的策略，随机选择一个服务节点。实现简单，但无法保证请求均匀分布。

```java
public class RandomLoadBalancer implements LoadBalancer {

    private final Random random = new Random();

    @Override
    public ServiceNode select(List<ServiceNode> nodes) {
        if (nodes == null || nodes.isEmpty()) {
            throw new RpcException("无可用服务节点");
        }
        int index = random.nextInt(nodes.size());
        return nodes.get(index);
    }
}
```

### 7.2 轮询策略（Round Robin）

按顺序依次选择每个节点，适合节点性能相近的场景。

```java
public class RoundRobinLoadBalancer implements LoadBalancer {

    private final AtomicInteger counter = new AtomicInteger(0);

    @Override
    public ServiceNode select(List<ServiceNode> nodes) {
        if (nodes == null || nodes.isEmpty()) {
            throw new RpcException("无可用服务节点");
        }
        int index = Math.abs(counter.getAndIncrement()) % nodes.size();
        return nodes.get(index);
    }
}
```

### 7.3 一致性哈希（Consistent Hash）

一致性哈希是分布式缓存和负载均衡中非常重要的算法。核心思想是：将每个节点映射到哈希环上，请求也映射到环上，沿着环顺时针找到第一个节点。

```
        0°
         │
         │
    300° ─┼─ 60°
         │    \
    240°──●     \
      ↑   │      \
   节点A   │       \    节点B
           │        \
      节点C ●    120°─┼── ● 节点D
                    /
    180° ─────────

请求 key 落在 节点A 和 节点B 之间 → 路由到节点B
```

**优点：**
- 增删节点时，只有少部分请求需要重新路由
- 可以加入虚拟节点解决节点负载不均的问题

```java
public class ConsistentHashLoadBalancer implements LoadBalancer {

    private final TreeMap<Long, ServiceNode> virtualNodes = new TreeMap<>();
    private static final int VIRTUAL_NODES = 160;  // 每个物理节点的虚拟节点数

    public ConsistentHashLoadBalancer(List<ServiceNode> nodes) {
        for (ServiceNode node : nodes) {
            addNode(node);
        }
    }

    private void addNode(ServiceNode node) {
        for (int i = 0; i < VIRTUAL_NODES; i++) {
            // 虚拟节点名：物理节点 + 序号
            String virtualNodeName = node.getHost() + ":" + node.getPort() + "-VN" + i;
            long hash = hash(virtualNodeName);
            virtualNodes.put(hash, node);
        }
    }

    private long hash(String key) {
        // 使用 MurmurHash 保证哈希分布均匀
        MurmurHash128 murmurHash = new MurmurHash128();
        long[] h = murmurHash.hash(key);
        return h[0];
    }

    @Override
    public ServiceNode select(List<ServiceNode> nodes, String key) {
        if (virtualNodes.isEmpty()) {
            throw new RpcException("无可用服务节点");
        }
        // 计算 key 的哈希值，查找第一个 >= keyHash 的虚拟节点
        long keyHash = hash(key);
        Map.Entry<Long, ServiceNode> entry = virtualNodes.ceilingEntry(keyHash);
        // 如果 keyHash 大于环上最后一个虚拟节点，则取第一个
        if (entry == null) {
            entry = virtualNodes.firstEntry();
        }
        return entry.getValue();
    }
}
```

## 八、超时与重试机制

### 8.1 超时处理

RPC 调用必须设置合理的超时时间，避免无限等待。

```java
public class NettyRpcClient {

    private static final int DEFAULT_TIMEOUT = 3000; // 默认 3 秒超时

    public RpcResponse sendRequest(RpcRequest request, ServiceNode node) {
        RpcFuture<RpcResponse> future = new RpcFuture<>();
        pendingRequests.put(request.getRequestId(), future);

        channel.writeAndFlush(request);

        try {
            // 等待响应，超时则抛出异常
            return future.get(DEFAULT_TIMEOUT, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            pendingRequests.remove(request.getRequestId());
            throw new RpcException("RPC 调用超时: " + request.getMethodName());
        }
    }
}
```

### 8.2 重试机制

网络抖动或服务端短暂不可用时，应该支持自动重试。

```java
public class RpcClientWithRetry {

    private int maxRetries = 3;
    private long retryDelay = 100; // 重试间隔（毫秒）

    public RpcResponse sendRequestWithRetry(RpcRequest request, List<ServiceNode> nodes,
                                           LoadBalancer balancer) {
        RpcException lastException = null;

        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                ServiceNode node = balancer.select(nodes);
                return nettyClient.sendRequest(request, node);
            } catch (RpcException e) {
                lastException = e;
                if (attempt < maxRetries) {
                    try {
                        Thread.sleep(retryDelay * (attempt + 1)); // 指数退避
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }

        throw new RpcException("RPC 调用重试 " + maxRetries + " 次后仍然失败",
            lastException);
    }
}
```

**重试的注意事项：**
- 幂等性：只有幂等操作（如 GET、只读的查询）才能安全重试
- 指数退避：避免重试风暴
- 熔断机制：失败率达到阈值后停止重试，快速失败

## 九、序列化协议对比

### 9.1 常见序列化协议

| 协议 | 序列化效率 | 可读性 | 跨语言 | 体积 | 典型场景 |
|---|---|---|---|---|---|
| **JSON** | 低 | 高 | 强 | 大 | Web API、配置文件 |
| **Hessian** | 中等 | 低 | 中等 | 中等 | Dubbo 默认 |
| **Protobuf** | 高 | 低 | 强 | 极小 | gRPC、高性能场景 |
| **FastJSON** | 中等 | 低 | 强 | 中等 | 国内 Java 生态 |
| **Kryo** | 高 | 低 | 弱 | 小 | 游戏、大数据 |
| **FST** | 很高 | 低 | 弱 | 小 | 高性能 Java 内通信 |

### 9.2 Protobuf 示例

Protocol Buffers 是 Google 主导的二进制序列化协议，性能极佳，是 gRPC 的默认协议。

**定义 .proto 文件：**

```protobuf
syntax = "proto3";

package rpc;

option java_package = "com.example.rpc.protobuf";
option java_outer_classname = "UserProto";

// 用户服务
service UserService {
    rpc GetUserById (GetUserRequest) returns (UserResponse);
    rpc CreateUser (CreateUserRequest) returns (UserResponse);
}

// 请求和响应消息
message GetUserRequest {
    int64 user_id = 1;
}

message UserResponse {
    int64 id = 1;
    string name = 2;
    string email = 3;
    int32 age = 4;
}
```

**Java 使用示例：**

```java
// 序列化
UserProto.GetUserRequest request = UserProto.GetUserRequest.newBuilder()
    .setUserId(1001)
    .build();
byte[] bytes = request.toByteArray();

// 反序列化
UserProto.GetUserRequest parsed = UserProto.GetUserRequest.parseFrom(bytes);
```

### 9.3 Kryo 示例

Kryo 是 Java 专用的高性能序列化库，序列化速度是 JDK 的 10 倍以上。

```java
public class KryoSerializer implements Serializer {

    private static final ThreadLocal<Kryo> kryo = ThreadLocal.withInitial(() -> {
        Kryo k = new Kryo();
        k.setRegistrationRequired(false);  // 允许未注册类
        k.setReferences(true);
        return k;
    });

    @Override
    public byte[] serialize(Object obj) {
        Kryo k = kryo.get();
        try (ByteArrayOutputStream baos = new ByteArrayOutputStream();
             Output output = new Output(baos)) {
            k.writeObject(output, obj);
            return output.toBytes();
        }
    }

    @Override
    public <T> T deserialize(byte[] bytes, Class<T> clazz) {
        Kryo k = kryo.get();
        try (Input input = new Input(bytes)) {
            return k.readObject(input, clazz);
        }
    }
}
```

## 十、简单 RPC 框架代码实现

### 10.1 整体项目结构

```
rpc-framework/
├── pom.xml
└── src/main/java/com/example/rpc/
    ├── api/                    # API 接口定义
    │   └── HelloService.java
    ├── model/                  # 数据模型
    │   ├── RpcRequest.java
    │   ├── RpcResponse.java
    │   └── ServiceNode.java
    ├── codec/                  # 编解码器
    │   ├── RpcEncoder.java
    │   └── RpcDecoder.java
    ├── transport/             # 网络传输层
    │   ├── NettyServer.java
    │   └── NettyClient.java
    ├── proxy/                  # 动态代理
    │   ├── RpcProxy.java
    │   └── RpcProxyFactory.java
    ├── registry/              # 注册中心
    │   ├── ServiceRegistry.java
    │   └── ZookeeperServiceRegistry.java
    ├── loadbalancer/          # 负载均衡
    │   ├── LoadBalancer.java
    │   ├── RandomLoadBalancer.java
    │   └── ConsistentHashLoadBalancer.java
    ├── client/                # RPC 客户端
    │   └── RpcClient.java
    ├── server/                 # RPC 服务端
    │   └── RpcServer.java
    └── exception/             # 异常定义
        └── RpcException.java
```

### 10.2 核心模型类

```java
@Data
@Builder
public class RpcRequest implements Serializable {
    private static final long serialVersionUID = 1L;
    
    private String requestId;       // 请求唯一 ID
    private String interfaceName;  // 接口全名
    private String methodName;      // 方法名
    private Class<?>[] parameterTypes; // 参数类型列表
    private Object[] parameters;    // 参数值
    private String serviceVersion; // 服务版本
    private long timestamp;        // 时间戳
}

@Data
@Builder
public class RpcResponse implements Serializable {
    private static final long serialVersionUID = 1L;
    
    private String requestId;       // 对应请求的 ID
    private Object result;          // 返回结果
    private Throwable error;         // 错误信息
    private long duration;          // 耗时
    
    public boolean isError() {
        return error != null;
    }
}
```

### 10.3 服务启动与调用示例

**定义服务接口：**

```java
public interface HelloService {
    String sayHello(String name);
    User getUser(Long id);
}

@Data
class User implements Serializable {
    private Long id;
    private String name;
    private String email;
}
```

**实现服务：**

```java
@Service
public class HelloServiceImpl implements HelloService {
    @Override
    public String sayHello(String name) {
        return "Hello, " + name + "!";
    }
    
    @Override
    public User getUser(Long id) {
        return new User(id, "User-" + id, "user" + id + "@example.com");
    }
}
```

**启动 RPC 服务端：**

```java
public class RpcServerBootstrap {
    public static void main(String[] args) {
        // 创建并启动 RPC 服务端，监听 8080 端口
        RpcServer server = new RpcServer("127.0.0.1", 8080);
        
        // 注册服务
        server.register(HelloService.class, new HelloServiceImpl());
        
        // 启动
        server.start();
        System.out.println("RPC Server started on port 8080");
    }
}
```

**客户端调用：**

```java
public class RpcClientBootstrap {
    public static void main(String[] args) {
        // 创建 RPC 代理（消费者端）
        RpcClient rpcClient = new RpcClient();
        
        // 通过 JDK 动态代理获取服务代理对象
        HelloService helloService = rpcClient.createProxy(
            HelloService.class,          // 接口类型
            "1.0",                        // 服务版本
            "127.0.0.1:8080"             // 服务地址
        );
        
        // 像调用本地方法一样调用远程服务
        String result = helloService.sayHello("张三");
        System.out.println(result);  // 输出: Hello, 张三!
        
        User user = helloService.getUser(1001L);
        System.out.println(user);     // 输出: User(id=1001, name=User-1001, ...)
    }
}
```

## 十一、高频面试题

### 面试题 1：RPC 的调用流程是怎样的？核心组件有哪些？

**参考答案：**

RPC 调用流程如下：

1. **客户端调用 Stub 方法：** 调用方调用 `userService.getUserById(1001)`，实际调用的是 Stub（代理对象）的方法。
2. **序列化请求：** Stub 将方法名、参数类型、参数值打包成 RpcRequest，并序列化（Protobuf/Hessian）为字节数组。
3. **网络传输：** 字节数组通过网络（TCP/Netty）发送到服务端。
4. **服务端接收：** Skeleton 接收字节数组，反序列化为 RpcRequest 对象。
5. **定位并调用服务：** Skeleton 根据方法名在服务注册表中找到对应的实现类，通过反射调用本地方法。
6. **序列化响应：** Skeleton 将执行结果序列化为 RpcResponse 字节数组。
7. **网络返回：** 字节数组返回给客户端。
8. **客户端处理：** Stub 反序列化响应，返回结果给调用方。

核心组件：**Stub（客户端代理）**、**Skeleton（服务端处理）**、**序列化/反序列化模块**、**网络传输层（Netty）**、**注册中心（ZooKeeper/Nacos）**。

---

### 面试题 2：Netty 为什么适合做 RPC 框架的传输层？什么是粘包半包？

**参考答案：**

Netty 适合做 RPC 传输层的原因：
- 基于 NIO（非阻塞 I/O），支持高并发连接
- 零拷贝、内存池，减少 GC 压力
- 支持长连接复用，避免每次请求都建立 TCP 连接
- 丰富的编解码器（如 LengthFieldBasedFrameDecoder）
- 线程模型高效（Reactor 多线程模型）
- 成熟的生态，被 Dubbo、RocketMQ 等大量使用

**粘包：** 多个独立的请求包被 TCP 合并成一个大的数据包发送。
**半包：** 一个大的请求包被 TCP 拆分成多个小的数据包分批接收。

解决粘包半包的方案：
- **固定长度法：** 每个包固定 N 字节，不足补空格（浪费带宽）
- **分隔符法：** 每个包用换行符或特殊字符分隔（如 HTTP 的空行）
- **LengthFieldBasedFrameDecoder（推荐）：** 在包头部加 4 字节长度字段，Netty 自动按长度切分

---

### 面试题 3：动态代理在 RPC 中起什么作用？有哪几种实现方式？

**参考答案：**

动态代理的核心作用是：**让调用方像调用本地方法一样调用远程服务，而不需要关心网络通信的细节。**

调用方持有的是一个代理对象（Stub），任何方法调用都被代理拦截，转化为网络请求。开发者只需定义接口，不用写任何网络代码。

三种实现方式：

**JDK 动态代理：** 要求接口必须有实现类，通过 `Proxy.newProxyInstance()` 创建代理，需要实现 `InvocationHandler`。优点是 JDK 内置，缺点是只能代理接口。

**CGLIB：** 通过继承被代理类生成子类，使用 `MethodInterceptor` 回调。优点是可以代理没有接口的类，性能更好；缺点是需要引入第三方库。

**Javassist：** 直接操作字节码，最底层最灵活，但代码复杂度高。一般用于框架层面的字节码增强。

生产环境 Dubbo 默认使用 Javassist，Spring AOP 默认使用 CGLIB。

---

### 面试题 4：ZooKeeper 和 Nacos 作为注册中心有什么区别？

**参考答案：**

| 维度 | ZooKeeper | Nacos |
|---|---|---|
| **一致性模型** | CP（强一致性） | AP + CP 双模式可选 |
| **协议** | ZAB 协议（Paxos 变种） | Raft 协议 |
| **注册数据量** | 万级以下 | 十万级 |
| **性能** | 中等 | 较高 |
| **使用复杂度** | 需要自行集成 | 开箱即用，有控制台 |
| **健康检查** | TCP 长连接探活 | 多种探测方式（TCP/HTTP/MySQL） |
| **国内生态** | 一般 | 非常活跃，社区活跃 |

**选择建议：** 中小规模系统推荐 Nacos，简单易用。大规模高并发系统可以考虑 ZooKeeper 或 Consul。

---

### 面试题 5：Dubbo 和 Spring Cloud 有什么区别？

**参考答案：**

| 维度 | Dubbo | Spring Cloud |
|---|---|---|
| **定位** | RPC 框架 + 服务治理 | 微服务完整解决方案 |
| **通信协议** | Dubbo RPC（自定义二进制协议，基于 Netty）| HTTP/REST（Feign + Ribbon）|
| **序列化** | Hessian/Protobuf 等高效序列化 | JSON |
| **服务注册发现** | ZooKeeper/Nacos/Redis | Eureka/Consul/Nacos |
| **负载均衡** | 内置 Random/RoundRobin/Weighted/ConsistentHash | Ribbon（客户端负载均衡）|
| **熔断器** | Sentinel（阿里巴巴）| Hystrix / Resilience4j |
| **网关** | 无官方网关（可选 Spring Cloud Gateway）| Spring Cloud Gateway |
| **配置中心** | Apollo/Nacos | Spring Cloud Config / Nacos |
| **性能** | 高（Dubbo 协议，二进制序列化）| 中等（HTTP JSON）|
| **生态完整性** | 需要自行整合 | 生态完整，开箱即用 |

**选择建议：**
- 对性能要求极高、服务间调用频繁 → Dubbo
- 追求快速开发、生态完整 → Spring Cloud
- 两者也可以混合使用，开放 API 层用 Spring Cloud，内部服务调用用 Dubbo

---

### 面试题 6：一致性哈希算法在 RPC 负载均衡中的原理是什么？解决了什么问题？

**参考答案：**

一致性哈希的核心思想是将每个服务节点映射到哈希环上，请求也映射到环上，请求落在哪个节点的哈希范围内，就由哪个节点处理。

**算法流程：**
1. 将所有服务节点通过哈希函数映射到 [0, 2^32-1] 的哈希环上
2. 将请求的 key 通过同样的哈希函数映射到环上
3. 沿环顺时针方向找到第一个服务节点，该节点处理请求

**解决的问题：**
- **普通哈希取模（hash(key) % N）：** 当节点数量变化（增删节点）时，几乎所有请求的路由目标都会改变，导致缓存大量失效。
- **一致性哈希：** 增删节点时，只有该节点附近的请求需要重新路由，其他请求不受影响。

**虚拟节点：** 为每个物理节点创建多个虚拟节点，均匀分布在哈希环上，解决物理节点性能不一致导致的负载不均问题。例如：节点 A 创建 "A-VN1"、"A-VN2"..."A-VN100" 共 100 个虚拟节点。

**典型应用：** 分布式缓存（Redis Cluster 的 slot 机制）、负载均衡（Dubbo 的一致性哈希负载均衡策略）、CDN。
