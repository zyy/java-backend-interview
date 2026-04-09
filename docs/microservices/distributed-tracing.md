---
layout: default
title: 分布式链路追踪原理与实战
---

# 分布式链路追踪原理与实战

## 一、为什么需要分布式链路追踪？

在传统的单体应用中，一次请求的完整调用链路都在同一个进程中，排查问题相对简单——通过查看日志、调试器或性能分析工具即可定位问题。

然而，在微服务架构下，一个简单的用户请求可能涉及十几个甚至几十个服务的协同工作：

```
用户发起请求 → API Gateway → 订单服务 → 用户服务
                               ↓
                          库存服务 → 仓储服务
                               ↓
                          支付服务 → 第三方支付
```

当这样一个请求出现延迟或错误时，问题可能出在任何一个环节。在生产环境中，排查这种跨服务的问题无异于大海捞针。

**分布式链路追踪（Distributed Tracing）** 就是为了解决这一问题而诞生的。它能够：

- 记录一次请求在分布式系统中完整调用路径
- 精确测量每个环节的耗时
- 追踪错误和异常在调用链中的传播
- 帮助开发者快速定位性能瓶颈和故障根因

## 二、核心概念：Trace、Span 和 Annotation

### 2.1 Trace（追踪）

一个 Trace 代表一次完整的端到端请求，从用户发起请求到请求返回的整个过程。在分布式系统中，Trace 由多个 Span 组成，形成一棵调用树。

```
Trace: 请求从开始到结束的完整生命周期
├── Span: API Gateway 处理
│   ├── Span: 订单服务处理
│   │   ├── Span: 用户服务调用
│   │   └── Span: 库存服务调用
│   │       └── Span: 仓储服务调用
│   └── Span: 支付服务调用
└── Span: 响应返回
```

每个 Trace 都有一个全局唯一的标识符，称为 **TraceId**。

### 2.2 Span（跨度）

Span 是分布式追踪中的基本工作单元，代表一个具有耗时的工作单元。每个 Span 包含以下关键信息：

| 字段 | 说明 |
|---|---|
| **SpanId** | 当前 Span 的唯一标识 |
| **ParentSpanId** | 父 Span 的 ID（用于构建调用树） |
| **TraceId** | 所属 Trace 的全局唯一 ID |
| **ServiceName** | 服务名称 |
| **OperationName** | 操作名称（如 HTTP 方法 + URL 路径） |
| **StartTime** | 开始时间戳 |
| **Duration** | 持续时间 |
| **Tags** | 标签信息（如 HTTP 状态码、服务 IP 等） |
| **Logs** | 事件日志（如异常堆栈） |

Span 有四种状态：
- **CS**（Client Send）：客户端发送请求
- **SR**（Server Receive）：服务端接收请求
- **SS**（Server Send）：服务端发送响应
- **CR**（Client Receive）：客户端接收响应

### 2.3 Annotation（标注）

Annotation 用于记录 Span 中的关键事件或信息点。常见的 Annotation 类型包括：

- **CS/SR/SS/CR 事件**：记录请求和响应的发送/接收时刻
- **自定义 Annotation**：记录业务相关的事件，如"订单创建"、"支付回调"等
- **异常信息**：记录错误类型和堆栈信息

```java
// 手动埋点示例
Tracer tracer = ...;
Span span = tracer.buildSpan("mysql-query").start();
try {
    span.logEvent("query-start");
    // 执行 SQL 查询
    span.tag("db.statement", "SELECT * FROM orders WHERE id = ?");
    span.tag("db.type", "mysql");
    span.logEvent("query-end");
} catch (Exception e) {
    span.log(ObjectWrapper.of(e));
    span.setTag("error", true);
} finally {
    span.finish();
}
```

## 三、Dapper 论文：链路追踪的奠基之作

2010 年，Google 发表了著名的 Dapper 论文《Dapper, a Large-Scale Distributed Systems Tracing Infrastructure》，奠定了现代分布式链路追踪的理论基础。

### 3.1 Dapper 的核心设计原则

**1. 低开销（Low overhead）**
追踪系统本身不能对业务服务造成明显的性能影响。Google 要求 Dapper 的开销控制在 5% 以内。

**2. 应用级透明（Application-level transparency）**
对业务代码侵入性尽可能低。开发者不需要手动为每个方法添加追踪代码。Dapper 通过字节码插桩（bytecode instrumentation）自动完成大部分埋点工作。

**3. 可扩展性（Scalability）**
能够支持 Google 内部数十亿次请求的追踪需求。

**4. 低采样率（Low sampling rate）**
高流量系统不适合记录所有请求。通过采样（sampling）策略，只记录部分请求，从而控制数据量和存储成本。

### 3.2 Dapper 的跟踪树模型

Dapper 将每次请求建模为一棵带标注的调用树：

```
                    深度=0
        ┌─────────────────────────────┐
        │      user request           │
        │   TraceId: abc123           │
        └────────────┬─────────────────┘
                     │    depth=1
        ┌────────────▼─────────────────┐
        │   /home.do?userId=1           │
        │   frontend.google.com        │
        └────────────┬─────────────────┘
                     │    depth=2
        ┌────────────▼─────────────────┐
        │   Search.do?q=term           │
        │   query-server.google.com     │
        └───┬─────────────────┬────────┘
            │ depth=3         │ depth=3
    ┌───────▼──────┐    ┌─────▼───────┐
    │ Index Server │    │ Index Server│
    │ idx-0        │    │ idx-1       │
    └──────────────┘    └─────────────┘
```

每个节点记录了自己的耗时和元数据，并通过 ParentSpanId 构建出完整的调用树。

### 3.3 Dapper 的采样策略

Dapper 支持多种采样策略：

- ** Head-based Sampling（入口采样）**：在请求入口处决定是否采样，采样率固定的请求会被完整追踪。
- ** Tail-based Sampling（尾部采样）**：先收集所有数据，然后在后端根据条件（如包含错误、耗时超过阈值）进行选择性存储。

## 四、OpenTracing 标准

OpenTracing 是 CNCF（云原生计算基金会）提出的分布式追踪标准，旨在提供统一的数据模型和 API，让不同的追踪系统能够互操作。

### 4.1 核心接口

**Tracer**

Tracer 是创建 Span 的工厂，负责生成 TraceId 和 SpanId。

```java
// OpenTracing API 示例
Tracer tracer = ...;

// 创建根 Span
Span parentSpan = tracer.buildSpan("http-request")
    .withTag("http.method", "GET")
    .withTag("http.url", "/api/users")
    .start();

// 创建子 Span
Span childSpan = tracer.buildSpan("database-query")
    .asChildOf(parentSpan)
    .withTag("db.type", "mysql")
    .withTag("db.statement", "SELECT ...")
    .start();

try {
    // 业务逻辑
    childSpan.finish();
} catch (Exception e) {
    childSpan.log(ImmutableMap.of("event", "error", "error.object", e));
    parentSpan.setTag("error", true);
} finally {
    parentSpan.finish();
}
```

**SpanContext**

SpanContext 封装了 TraceId 和 SpanId，用于在跨进程通信中传递上下文。

```java
// 注入到 HTTP Header
Tracer tracer = ...;
Span span = ...;
SpanContext spanContext = span.context();

// 注入到 carrier（这里是 HttpHeaders）
HttpHeaders headers = new HttpHeaders();
tracer.inject(spanContext, Format.Builtin.HTTP_HEADERS, new HttpHeadersCarrier(headers));

// 在下游服务中提取
SpanContext extractedContext = tracer.extract(
    Format.Builtin.HTTP_HEADERS,
    new HttpHeadersCarrier(headers)
);
Span childSpan = tracer.buildSpan("downstream-call")
    .asChildOf(extractedContext)
    .start();
```

### 4.2 OpenTracing 数据模型

```
Trace: 整个请求链路，用 TraceId 标识
  └── Span: 单个服务/操作，用 SpanId 标识
        ├── SpanContext: 包含 TraceId + SpanId + Baggage
        ├── References: 与其他 Span 的关系（ChildOf / FollowsFrom）
        ├── Tags: 键值对标签（结构化元数据）
        └── Logs: 时间序列事件日志
```

### 4.3 OpenTracing vs OpenCensus vs OpenTelemetry

- **OpenTracing**：只定义了数据模型和 API 规范，不包含数据收集和传输机制。
- **OpenCensus**：Google 和 Microsoft 主导的项目，包含 API + SDK + 数据收集，支持多种后端。
- **OpenTelemetry**：OpenTracing 和 OpenCensus 合并后的产物，目前是 CNCF 的官方标准，整合了追踪（Tracing）、指标（Metrics）和日志（Logs）。

## 五、SkyWalking 架构详解

SkyWalking 是 Apache 基金会的顶级项目，是目前最流行的开源分布式追踪系统之一，特别适合 Java 技术栈。

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    SkyWalking UI                         │
│                  (Web 界面 / 查询)                       │
└───────────────────────┬─────────────────────────────────┘
                        │ gRPC / HTTP
┌───────────────────────▼─────────────────────────────────┐
│                    SkyWalking OAP                        │
│     (Observability Analysis Platform，观察分析平台)      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Trace Handler │ │ Metric Handler│ │  Alarm Handler   │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │ Kafka / H2 / Elasticsearch / ...
┌───────────────────────▼─────────────────────────────────┐
│                   数据存储层                              │
│     (Elasticsearch / H2 / MySQL / TiDB / ShardingSphere)│
└─────────────────────────────────────────────────────────┘

┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Java Agent│ │Go Agent │ │Node Agent│ │ .NET Agent│
│  (自动埋点)│ │(手动埋点)│ │(手动埋点)│ │(自动埋点) │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                       │
              上报数据到 OAP
```

### 5.2 SkyWalking Agent

SkyWalking Agent 基于 Java Agent 技术，在不修改业务代码的情况下完成字节码增强（ByteBuddy / Java Agent）：

- **自动拦截**：自动拦截常见的 HTTP 框架（Tomcat、Spring MVC）、数据库驱动（JDBC）、RPC 框架（Dubbo、gRPC）、MQ（Kafka、RabbitMQ）等组件。
- **无侵入**：不需要在业务代码中添加任何追踪相关注解或代码。
- **插件化**：通过插件机制支持更多框架的自动埋点。

**Agent 启动方式：**

```bash
java -javaagent:/path/to/skywalking-agent.jar
    -Dskywalking.agent.service_name=order-service
    -Dskywalking.collector.backend_service=127.0.0.1:11800
    -jar order-service.jar
```

**手动埋点（可选）：**

```java
import org.apache.skywalking.apm.toolkit.trace.ActiveSpan;
import org.apache.skywalking.apm.toolkit.trace.Trace;

@Trace
@Tag(key = "orderId", value = "${args[0].getOrderId()}")
public Order createOrder(OrderRequest request) {
    // 业务逻辑
    
    // 在追踪中记录异常
    ActiveSpan.error("创建订单失败");
    ActiveSpan.log(e);
    
    return order;
}
```

### 5.3 SkyWalking OAP 核心功能

OAP（Observability Analysis Platform）负责接收、聚合和分析来自 Agent 的数据：

- **Trace 处理**：解析和存储调用链数据
- **指标计算**：基于 Trace 数据计算 QPS、响应时间、错误率等指标
- **拓扑分析**：根据服务间的调用关系自动生成服务拓扑图
- **告警**：基于预置或自定义规则触发告警

### 5.4 SkyWalking 界面

SkyWalking UI 提供了以下核心功能：

- **拓扑图（Topology）**：可视化服务间的依赖关系
- **追踪列表（Trace）**：查看具体的调用链详情
- **服务仪表盘（Dashboard）**：查看服务性能指标
- **告警记录（Alarm）**：查看和配置告警规则
- **日志关联**：将 TraceId 和日志进行关联分析

## 六、Zipkin 架构详解

Zipkin 是 Twitter 开源的分布式追踪系统，因其简单易用、轻量级而广泛应用。

### 6.1 整体架构

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Service A│   │ Service B│   │ Service C│   │ Service D│
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐
│ Collector│   │ Collector│   │ Collector│   │ Collector│
│ (HTTP)   │   │ (HTTP)   │   │ (HTTP)   │   │ (HTTP)   │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │   Kafka     │
                    │  (消息队列) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Storage   │
                    │  (ES/MySQL) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Zipkin UI │
                    │   (Web界面) │
                    └─────────────┘
```

### 6.2 Zipkin 核心组件

| 组件 | 功能 |
|---|---|
| **Collector** | 接收来自各个服务上报的追踪数据 |
| **Storage** | 存储追踪数据（支持 Cassandra、Elasticsearch、MySQL、内存） |
| **API** | 提供查询接口，供 UI 调用 |
| **Web UI** | 提供 Web 界面查看追踪数据 |

### 6.3 Zipkin 安装和启动

```bash
# Docker 快速启动
docker run -d -p 9411:9411 openzipkin/zipkin

# 下载 jar 包启动
curl -sSL https://zipkin.io/quickstart.sh | bash -s
java -jar zipkin.jar
```

访问 `http://localhost:9411` 即可打开 Zipkin Web 界面。

## 七、代码埋点 vs 字节码埋点

### 7.1 手动代码埋点

手动埋点需要开发者显式地在代码中添加追踪逻辑：

**HTTP 入口埋点（使用 OpenTracing）：**

```java
@RestController
public class OrderController {

    @Autowired
    private Tracer tracer;

    @PostMapping("/orders")
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest request) {
        // 在 Controller 层创建 Span
        Span span = tracer.buildSpan("POST /orders")
            .withTag("http.method", "POST")
            .withTag("http.url", "/orders")
            .withTag("user.id", request.getUserId())
            .start();

        try (Scope scope = tracer.activateSpan(span)) {
            Order order = orderService.createOrder(request);
            span.tag("http.status_code", "200");
            return ResponseEntity.ok(order);
        } catch (Exception e) {
            span.setTag("error", true);
            span.log(ImmutableMap.of("event", "error", "error.kind", e.getClass().getName()));
            throw e;
        } finally {
            span.finish();
        }
    }
}
```

**RPC 调用埋点：**

```java
@Service
public class OrderServiceImpl {

    @Autowired
    private Tracer tracer;

    @Autowired
    private UserClient userClient;

    public Order createOrder(OrderRequest request) {
        Span span = tracer.buildSpan("call-user-service")
            .withTag("rpc.system", "grpc")
            .withTag("rpc.method", "getUser")
            .start();

        try (Scope scope = tracer.activateSpan(span)) {
            // 注入 SpanContext 到 RPC 请求 Header
            SpanContext spanContext = span.context();
            Metadata metadata = new Metadata();
            tracer.inject(spanContext, Format.Builtin.HTTP_HEADERS,
                new RequestHeaderCarrier(metadata));

            User user = userClient.getUser(request.getUserId(), metadata);
            span.tag("rpc.user.id", user.getId());
            return orderMapper.create(request);
        } finally {
            span.finish();
        }
    }
}
```

**数据库查询埋点：**

```java
@Repository
public class OrderDao {

    @Autowired
    private Tracer tracer;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    public List<Order> findByUserId(Long userId) {
        Span span = tracer.buildSpan("db:select:orders")
            .withTag("db.type", "mysql")
            .withTag("db.instance", "ecommerce")
            .withTag("db.statement", "SELECT * FROM orders WHERE user_id = ?")
            .start();

        try (Scope scope = tracer.activateSpan(span)) {
            List<Order> orders = jdbcTemplate.query(
                "SELECT * FROM orders WHERE user_id = ?",
                new Object[]{userId},
                new OrderRowMapper()
            );
            span.tag("db.rows", orders.size());
            return orders;
        } finally {
            span.finish();
        }
    }
}
```

### 7.2 字节码自动埋点

字节码埋点通过在编译期或运行期修改字节码，自动完成大部分常见框架的埋点，开发者几乎不需要写任何追踪代码。

**原理：**

```
源代码 (.java)
     ↓ 编译
  Java 字节码 (.class)
     ↓ Agent 字节码插桩
增强后的字节码
     ↓ 类加载
  JVM 执行（自动收集追踪数据）
```

**SkyWalking Agent 插桩示例：**

以 Spring MVC 为例，SkyWalking Agent 会自动拦截 `DispatcherServlet.doDispatch()` 方法，在方法执行前后自动创建 Span 并记录关键信息。

类似的自动拦截还包括：
- JDBC: `PreparedStatement.executeQuery()` 等方法
- HTTP Client: `HttpClient.execute()`, `OkHttpClient.call()` 等
- RPC: Dubbo `Invoker.invoke()`, gRPC `ClientCall.start()` 等
- MQ: Kafka `Producer.send()`, `Consumer.poll()` 等

**Brave（Zipkin 的 Java 库）也支持注解埋点：**

```java
@SpanName("create-order")
class OrderService {

    @NewSpan
    @SpanTag(key = "order.type")
    public void createOrder(@SpanTag("order.id") String orderId) {
        // 自动创建名为 "create-order" 的 Span
        // 自动记录 orderId 作为标签
    }
}
```

### 7.3 两种埋点方式对比

| 特性 | 手动代码埋点 | 字节码自动埋点 |
|---|---|---|
| 侵入性 | 高（需要在业务代码中写追踪代码） | 低（无侵入或仅需注解） |
| 覆盖度 | 可精确控制关键业务节点 | 覆盖常见框架，自动处理 |
| 灵活性 | 可以添加丰富的业务上下文信息 | 上下文信息有限 |
| 工作量 | 大（每个接口都需要添加） | 小（一次配置即可） |
| 维护成本 | 高（追踪代码与业务代码耦合） | 低（框架升级时可能需要同步更新插件） |
| 适用场景 | 关键业务流程、需要详细上下文 | 通用框架层、快速接入 |

## 八、TraceId 的生成与传播

### 8.1 TraceId 的要求

一个优秀的 TraceId 应该满足：

- **全局唯一性**：在分布式环境中跨时间、跨机器都不会冲突
- **足够的长度**：防止被猜测或碰撞
- **可排序性**（可选）：便于按时间范围查询
- **包含时间信息**（可选）：方便人工识别和调试

### 8.2 常见的 TraceId 生成方案

**方案一：UUID**

最简单直接，但 UUID v4 是纯随机的，没有时间信息，可读性差。

```
550e8400-e29b-41d4-a716-446655440000
```

**方案二：Snowflake 算法**

Twitter 的 Snowflake 算法，生成 64 位整数，包含时间戳、机器 ID 和序列号：

```
  1位符号   41位时间戳   10位机器ID   12位序列号
    0    1111111111   0000000001    000000000000
```

在 Java 中可以使用 Twitter 的 `twitter-server` 包：

```java
import com.twitter.service.snowflake.IdWorker;

long traceId = IdWorker.getInstance().nextId();
```

**方案三：High UUID（推荐）**

在 UUID v1 的基础上改进，加入时间戳和随机数：

```java
public static String generateTraceId() {
    // 格式：时间戳-随机字符（Base62 编码）
    long timestamp = System.currentTimeMillis() * 1000;
    Random random = new Random();
    String randomPart = Base62.encode(random.nextLong());
    return timestamp + "-" + randomPart;
}
```

### 8.3 TraceId 的跨进程传播

TraceId 需要在 HTTP、RPC、MQ 等所有跨进程调用中传递，确保整个调用链共享同一个 TraceId。

**HTTP 传播（通过 Header）：**

```
请求头 Header: 
  X-Request-Id: abc123-def456-ghi789
  X-B3-TraceId: abc123def456ghi789    (Zipkin/B3 格式)
  X-Trace-Id: abc123-def456-ghi789    (SkyWalking 格式)
  uber-trace-id: abc123-def456-ghi789-1  (Jaeger 格式)
```

**RPC 传播（通过 Metadata/Context）：**

```java
// 发送方
Span span = tracer.activeSpan();
SpanContext spanContext = span.context();
Map<String, String> metadata = new HashMap<>();
tracer.inject(spanContext, Format.Builtin.TEXT_MAP, new TextMapAdapter(metadata));
rpcCall.setMetadata(metadata);

// 接收方
TextMapExtractAdapter carrier = new TextMapExtractAdapter(receivedMetadata);
SpanContext parentContext = tracer.extract(Format.Builtin.TEXT_MAP, carrier);
Span childSpan = tracer.buildSpan("rpc-handler")
    .asChildOf(parentContext)
    .start();
```

**MQ 传播（通过消息 Header）：**

```java
// 生产者：注入 TraceId 到消息 Header
ProducerRecord<String, String> record = new ProducerRecord<>("topic", "message");
Span span = tracer.activeSpan();
SpanContext spanContext = span.context();
record.headers().add("X-Trace-Id", spanContext.traceId().getBytes());
kafkaTemplate.send(record);

// 消费者：从消息 Header 提取 TraceId
ConsumerRecord<String, String> record = ...;
SpanContext spanContext = tracer.extract(
    Format.Builtin.TEXT_MAP,
    new RecordHeadersCarrier(record.headers())
);
Span span = tracer.buildSpan("kafka-consume")
    .asChildOf(spanContext)
    .start();
```

## 九、Spring Cloud Sleuth + Zipkin 实战

### 9.1 快速集成

Spring Cloud Sleuth 为 Spring Boot 应用提供了开箱即用的分布式追踪支持，与 Zipkin 无缝集成。

**Maven 依赖：**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-zipkin</artifactId>
</dependency>
```

**application.yml 配置：**

```yaml
spring:
  zipkin:
    base-url: http://localhost:9411        # Zipkin Server 地址
    discovery-client-enabled: false         # 是否通过服务发现找 Zipkin
    sender:
      type: web                             # 发送方式：web / rabbitmq / kafka
  sleuth:
    sampler:
      probability: 1.0                       # 采样率（1.0 = 100%）
      rate: 100                              # 限流：每秒最多采样 100 个请求
```

**引入依赖后，自动完成以下工作：**

- 为所有 HTTP 请求、RestTemplate、WebClient、Feign、Async 等自动创建 Span
- 自动将 TraceId 和 SpanId 添加到 MDC（Mapped Diagnostic Context，日志框架的线程上下文）
- 自动将追踪数据上报到 Zipkin Server

### 9.2 MDC 日志集成

Spring Cloud Sleuth 的一个重要功能是将 TraceId 和 SpanId 自动注入到日志中：

```
2024-01-15 10:30:15.123 [http-nio-8080-exec-1] INFO  [order-service,abc123def456,7a8b9c]
2024-01-15 10:30:15.124 [http-nio-8080-exec-1] INFO  用户服务调用完成: userId=1001
2024-01-15 10:30:15.130 [http-nio-8080-exec-1] INFO  订单创建成功: orderId=ORDER-20240115-001
```

日志格式：`[服务名,TraceId,SpanId]`

这样，即使请求分散在多个微服务中，通过 TraceId 就可以串联起完整的日志链路。

### 9.3 手动 Sleuth 埋点

```java
import org.springframework.cloud.sleuth.Span;
import org.springframework.cloud.sleuth.Tracer;

@Service
public class OrderServiceImpl {

    @Autowired
    private Tracer tracer;

    public Order processOrder(OrderRequest request) {
        Span span = tracer.nextSpan().name("processOrder").start();
        
        try (Tracer.SpanInScope scope = tracer.withSpan(span)) {
            span.tag("order.type", request.getType());
            span.tag("user.id", String.valueOf(request.getUserId()));
            
            // 业务逻辑
            Order order = createOrder(request);
            
            span.tag("order.id", order.getId());
            span.tag("order.amount", String.valueOf(order.getAmount()));
            
            return order;
        } catch (Exception e) {
            span.error(e);
            throw e;
        } finally {
            span.end();
        }
    }
}
```

### 9.4 使用 Brave + OpenTelemetry

对于更灵活的需求，可以直接使用 Brave（Zipkin 的追踪库）或 OpenTelemetry：

```java
// 使用 Brave 手动埋点
Tracing tracing = Tracing.newBuilder()
    .localServiceName("payment-service")
    .sampler(Sampler.alwaysTrue())
    .spanReporter(ZipkinSpanReporter.create("http://localhost:9411/api/v2/spans"))
    .build();

Tracer tracer = tracing.getTracer();

// 在方法中创建 Span
Span span = tracer.newTrace().name("processPayment").start();
try (Scope scope = tracer.withSpanInScope(span)) {
    span.tag("payment.method", "alipay");
    span.annotate("支付回调开始处理");
    
    // 业务逻辑
    paymentService.processCallback();
    
    span.annotate("支付回调处理完成");
} finally {
    span.finish();
}
```

## 十、高频面试题

### 面试题 1：说说你对分布式链路追踪的理解，以及它解决了什么问题？

**参考答案：**

分布式链路追踪是一种观测性技术，用于记录和可视化分布式系统中一次请求的完整调用路径。它解决了微服务架构下的两个核心问题：

**可观测性缺失问题：** 在微服务架构中，单个请求可能跨越十几个服务，出现问题时很难知道是哪一步出了问题。链路追踪提供了"端到端"的可见性。

**性能分析困难问题：** 当系统出现延迟时，很难定位瓶颈在哪。链路追踪通过记录每个环节的耗时，可以精确找到性能瓶颈。

核心概念包括 Trace（一次完整请求）、Span（单个工作单元）、Annotation（事件标注）。通过 TraceId 将整个调用链串联起来，通过 ParentSpanId 构建调用树。

---

### 面试题 2：OpenTracing 和 OpenTelemetry 有什么区别？

**参考答案：**

OpenTracing 只定义了追踪的数据模型和 API 规范，是一个"只读规范"，不负责数据收集和传输。具体使用哪种传输协议、存储什么后端，需要使用者自己实现。

OpenTracing 的核心接口：Tracer（创建 Span）、Span（记录操作）、SpanContext（上下文信息）。

OpenTelemetry 是 OpenTracing 和 OpenCensus 合并后的产物，是 CNCF 的官方标准。它不仅包含追踪（Tracing），还整合了指标（Metrics）和日志（Logs），提供了完整可观测性解决方案。OpenTelemetry 提供 SDK、API 和Collector，支持多种导出协议（OTLP、Jaeger、Zipkin 等），是目前的主流选择。

简单来说：OpenTracing 是"规范"，OpenTelemetry 是"规范+实现+生态"。

---

### 面试题 3：如何保证 TraceId 的全局唯一性？有哪些生成方案？

**参考答案：**

TraceId 需要在跨机器、跨时间的情况下保持唯一。常见方案：

**UUID v4：** 122 位随机数，碰撞概率极低（2^122 分之一），但纯随机无规律，可读性差。

**Snowflake 算法：** 64 位 long，包含 41 位时间戳（毫秒，约69年）、10 位机器 ID、12 位序列号。能够生成趋势递增的 ID，但需要独立的机器 ID 分配机制。

**复合 ID：** 将时间戳 + 随机数 + 机器标识组合，如 `1642305123000-7f9a-B2c3`。可读性好，便于按时间范围查询。

**美团的 Leaf 算法：** 融合了 Snowflake 和号段模式，支持高并发下的唯一 ID 生成，且不依赖 ZooKeeper 等协调组件。

在 RPC、HTTP、MQ 等跨进程调用中，需要通过 Header 或 Metadata 将 TraceId 传递下去，确保整个调用链共享同一个 TraceId。

---

### 面试题 4：SkyWalking 和 Zipkin 有什么区别？各自适用于什么场景？

**参考答案：**

| 维度 | SkyWalking | Zipkin |
|---|---|---|
| **架构复杂度** | 较重（OAP + UI + Agent） | 轻量（Collector + Storage + UI） |
| **数据存储** | ES/MySQL/TiDB/HSQL 等多种后端 | Cassandra/ES/MySQL/内存 |
| **Agent 能力** | 强大的字节码插桩，自动埋点覆盖广 | 主要依赖手动埋点或 Brave |
| **查询能力** | 强大，支持聚合分析、拓扑分析 | 基础，支持按 TraceId 查询 |
| **告警功能** | 内置告警引擎 | 需要额外集成 |
| **语言支持** | 多语言（Java/Go/Node/.NET/PHP/Python） | 多语言社区支持 |
| **适合场景** | 大型企业级应用、微服务治理需求强 | 快速接入、小型团队、简单需求 |

如果团队规模大、微服务多、需要完整的 APM 能力，选 SkyWalking。如果追求轻量、快速接入，选 Zipkin。

---

### 面试题 5：采样率（Sampling）策略有哪些？为什么要做采样？

**参考答案：**

**采样必要性：** 高流量系统（如每秒数万请求）如果记录所有追踪数据，数据量会非常庞大，对存储和计算造成巨大压力，同时也会影响服务性能。因此需要对追踪数据进行采样。

**常见采样策略：**

1. **固定比例采样（Probabilistic Sampling）：** 每个请求以固定概率（如 10%）被采样。简单但可能导致重要请求（错误请求、慢请求）被遗漏。

2. **头部采样（Head-based Sampling）：** 在请求入口处立即决定是否采样，采样后完整追踪该请求所有 Span。缺点是可能遗漏尾部的重要请求。

3. **尾部采样（Tail-based Sampling）：** 先处理所有请求，根据后端聚合结果（如发现耗时 > 1s 或包含错误），再决定是否保存该追踪数据。需要额外的基础设施支持，但能确保重要请求不遗漏。

4. **自适应采样：** 根据系统负载动态调整采样率，低峰期提高采样率，高峰期降低采样率。

5. **优先级采样：** 错误请求、慢请求自动提升采样率或强制采样，确保这类重要数据不丢失。

生产环境推荐：尾部采样 + 错误请求强制采样，可以兼顾数据完整性和存储成本。
