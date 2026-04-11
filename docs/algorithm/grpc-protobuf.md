---
layout: default
title: gRPC 与 Protobuf 高性能通信实战
---
# gRPC 与 Protobuf 高性能通信实战

## 🎯 面试题：gRPC 和 REST 有什么区别？Protobuf 为什么比 JSON 快？

> gRPC 是 Google 开源的高性能 RPC 框架，基于 HTTP/2 和 Protocol Buffers。微服务间通信的重要选型。

---

## 一、gRPC vs REST vs 消息队列

| 特性 | gRPC | REST | 消息队列 |
|------|------|------|----------|
| 协议 | HTTP/2 | HTTP/1.1 | TCP |
| 序列化 | Protobuf（二进制） | JSON（文本） | 二进制/文本 |
| 性能 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| 流式支持 | 四种流 | 不支持 | 不支持 |
| 代码生成 | 自动（多语言） | 手动或 Swagger | 手动 |
| 浏览器兼容 | 需要 gRPC-Web | ✅ 原生 | ❌ |
| 适用场景 | 微服务间通信 | 对外 API | 异步解耦 |

---

## 二、Protobuf 语法

```protobuf
syntax = "proto3";

package com.example.user;

// 定义消息（对应 Java 的 POJO）
message UserRequest {
  int64 user_id = 1;        // 字段编号，序列化用
  string username = 2;
  repeated string tags = 3; // 数组
  UserStatus status = 4;    // 枚举
}

message UserResponse {
  int64 user_id = 1;
  string username = 2;
  int64 created_at = 3;
  repeated Order orders = 4; // 嵌套消息
}

message Order {
  int64 order_id = 1;
  double amount = 2;
  string status = 3;
}

enum UserStatus {
  UNKNOWN = 0;   // proto3 枚举必须有默认值 0
  ACTIVE = 1;
  INACTIVE = 2;
  BANNED = 3;
}

// 定义服务
service UserService {
  // 一元调用
  rpc GetUser (UserRequest) returns (UserResponse);
  // 服务端流
  rpc StreamUsers (UserRequest) returns (stream UserResponse);
  // 客户端流
  rpc BatchCreate (stream UserRequest) returns (UserResponse);
  // 双向流
  rpc Chat (stream UserRequest) returns (stream UserResponse);
}
```

### 编译生成代码

```bash
# 生成 Java 代码
protoc --java_out=./src/main/java \
       --grpc-java_out=./src/main/java \
       user.proto

# 生成多语言
protoc --go_out=. --go-grpc_out=. user.proto    # Go
protoc --python_out=. user.proto                 # Python
```

---

## 三、Protobuf 编码原理

```
Protobuf 编码流程：
  .proto 定义 → 编译器 → 序列化（varint + 字段号 + 类型） → 二进制字节流

核心编码方式：Varint（变长整数）

Varint 编码：
  每字节 7 bit 表示数据，最高位 MSB 表示是否还有后续字节

  举例：300 的 Varint 编码
  300 = 100101100
  分组（7位一组）：10 0101100
  第一字节：1_0101100 = 0xAC（MSB=1，还有后续）
  第二字节：0_0000010 = 0x02（MSB=0，结束）
  结果：[0xAC, 0x02] — 仅 2 字节（int32 固定 4 字节）

Wire Type：
  0 = Varint（int32/int64/bool/enum）
  1 = 64-bit（double/fixed64）
  2 = Length-delimited（string/bytes/嵌套消息/repeated）
  5 = 32-bit（float/fixed32）

为什么比 JSON 快？
  1. 二进制编码，体积小（JSON 有大量引号/冒号/花括号）
  2. 编解码简单，无需解析器（JSON 需要词法分析）
  3. 字段用编号引用，不需要字段名（JSON 每个字段都要带名字）
  4. Schema 预编译，运行时零反射（JSON 需要反射）
```

---

## 四、HTTP/2 特性

```
HTTP/1.1 的问题：
  - 每个请求一个 TCP 连接（队头阻塞）
  - 请求头冗余（每次都要发 Cookie/Accept 等大量头）
  - 单向通信（服务端无法主动推送）

HTTP/2 的改进：
  ┌───────────────────────────────────────────────┐
  │ 1. 多路复用：一个 TCP 连接上并行多个请求         │
  │    Stream 1: [HEADERS][DATA][DATA]             │
  │    Stream 2: [HEADERS][DATA]                   │
  │    Stream 3: [HEADERS][DATA][DATA][DATA]        │
  │    → 消除队头阻塞                              │
  │                                               │
  │ 2. 头部压缩：HPACK 算法，减少 70-90% 头部大小    │
  │    静态表 + 动态表 + 哈夫曼编码                 │
  │                                               │
  │ 3. 二进制帧：请求/响应拆分为 Frame，更高效        │
  │                                               │
  │ 4. 服务端推送：服务端可以主动推送资源             │
  │    → gRPC 的服务端流利用了这个特性               │
  │                                               │
  │ 5. 流优先级：客户端可以设置流的优先级             │
  └───────────────────────────────────────────────┘
```

---

## 五、gRPC 四种调用方式

### 1. 一元调用（Unary）

```java
// 服务端
@GrpcService
public class UserServiceImpl extends UserServiceGrpc.UserServiceImplBase {
    @Override
    public void getUser(UserRequest request, StreamObserver<UserResponse> observer) {
        User user = userService.findById(request.getUserId());
        UserResponse response = UserResponse.newBuilder()
            .setUserId(user.getId())
            .setUsername(user.getName())
            .build();
        observer.onNext(response);
        observer.onCompleted();
    }
}

// 客户端
UserServiceGrpc.UserServiceBlockingStub stub = UserServiceGrpc.newBlockingStub(channel);
UserResponse response = stub.getUser(UserRequest.newBuilder()
    .setUserId(1001)
    .build());
```

### 2. 服务端流（Server Streaming）

```java
// 服务端：推送用户列表
@Override
public void streamUsers(UserRequest request, StreamObserver<UserResponse> observer) {
    List<User> users = userService.findAll();
    for (User user : users) {
        observer.onNext(convert(user));  // 逐条推送
    }
    observer.onCompleted();
}

// 客户端
Iterator<UserResponse> responses = stub.streamUsers(request);
while (responses.hasNext()) {
    UserResponse r = responses.next();
    System.out.println(r.getUsername());
}
```

### 3. 客户端流（Client Streaming）

```java
// 服务端：接收批量数据
@Override
public StreamObserver<UserRequest> batchCreate(StreamObserver<UserResponse> observer) {
    return new StreamObserver<UserRequest>() {
        private int count = 0;
        @Override
        public void onNext(UserRequest request) {
            userService.create(convert(request));
            count++;
        }
        @Override
        public void onError(Throwable t) { observer.onError(t); }
        @Override
        public void onCompleted() {
            observer.onNext(UserResponse.newBuilder().setMessage("Created " + count).build());
            observer.onCompleted();
        }
    };
}
```

### 4. 双向流（Bidirectional）

```java
// 服务端：聊天
@Override
public StreamObserver<ChatMessage> chat(StreamObserver<ChatMessage> observer) {
    return new StreamObserver<ChatMessage>() {
        @Override
        public void onNext(ChatMessage msg) {
            // 收到消息后回复
            observer.onNext(ChatMessage.newBuilder()
                .setFrom("server").setContent("Echo: " + msg.getContent())
                .build());
        }
        @Override public void onError(Throwable t) { }
        @Override public void onCompleted() { observer.onCompleted(); }
    };
}
```

---

## 六、拦截器

```java
// 服务端拦截器：鉴权
@Order(1)
public class AuthInterceptor implements ServerInterceptor {
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers,
            ServerCallHandler<ReqT, RespT> next) {
        String token = headers.get(Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER));
        if (token == null || !jwtUtil.validate(token)) {
            call.close(Status.UNAUTHENTICATED.withDescription("Token invalid"), headers);
            return new ServerCall.Listener<>() {};
        }
        return next.startCall(call, headers);
    }
}

// 客户端拦截器：添加 Token
public class TokenInterceptor implements ClientInterceptor {
    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
            MethodDescriptor<ReqT, RespT> method, CallOptions callOptions, Channel next) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                headers.put(Metadata.Key.of("authorization", Metadata.ASCII_STRING_MARSHALLER), "Bearer " + token);
                super.start(responseListener, headers);
            }
        };
    }
}
```

---

## 七、面试高频题

**Q1: gRPC 和 REST 有什么区别？**
> gRPC 基于 HTTP/2 + Protobuf，REST 基于 HTTP/1.1 + JSON。gRPC 支持四种流式调用、自动生成客户端 SDK、二进制序列化性能更高（体积小 3-10 倍、速度快 5-20 倍）。REST 更通用，浏览器原生支持。gRPC 适合微服务间通信，REST 适合对外 API。浏览器端需要 gRPC-Web 适配。

**Q2: Protobuf 为什么比 JSON 快？**
> 四个原因：① 二进制编码，没有 JSON 的引号、冒号、花括号等冗余字符，体积小 3-10 倍；② Varint 编码，小数字只占 1 字节；③ 不携带字段名，用编号引用字段；④ Schema 预编译生成代码，序列化/反序列化是直接字段赋值，无需反射和语法解析。缺点是可读性差、需要 IDL 定义。

**Q3: HTTP/2 如何解决 HTTP/1.1 的队头阻塞？**
> HTTP/1.1 的队头阻塞是因为多个请求共用一个 TCP 连接时，前一个请求的响应未返回会阻塞后续请求。HTTP/2 通过多路复用解决：在一个 TCP 连接上建立多个 Stream（帧流），每个 Stream 独立传输，互不阻塞。但 HTTP/2 仍有 TCP 层的队头阻塞（丢包会阻塞所有 Stream），HTTP/3 用 QUIC 协议（基于 UDP）彻底解决这个问题。
