---
layout: default
title: Spring Cloud Gateway 核心原理与实战 ⭐⭐⭐
---
# Spring Cloud Gateway 核心原理与实战 ⭐⭐⭐

## 面试题：Spring Cloud Gateway 是如何工作的？

### 核心回答

Spring Cloud Gateway 是 Spring Cloud 生态系统的 API 网关，基于 Spring 5、Spring Boot 2 和 Project Reactor 构建。它通过路由、断言、过滤器三个核心概念，实现了请求转发、负载均衡、限流熔断、安全认证等功能。

## 一、Gateway vs Zuul 对比

### 1.1 架构差异

```
┌─────────────────────────────────────────────────────────────┐
│                    Zuul 1.x 架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HTTP Request                                               │
│      ↓                                                      │
│  Zuul Servlet (阻塞式)                                       │
│      ↓                                                      │
│  Zuul Filter Chain                                          │
│  ├── Pre Filters                                            │
│  ├── Route Filters                                          │
│  ├── Post Filters                                           │
│  └── Error Filters                                          │
│      ↓                                                      │
│  后端服务 (同步调用)                                          │
│      ↓                                                      │
│  HTTP Response                                              │
│                                                             │
│  特点：基于 Servlet，阻塞式 IO，线程池模型                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Spring Cloud Gateway 架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HTTP Request                                               │
│      ↓                                                      │
│  Reactor Netty (非阻塞)                                      │
│      ↓                                                      │
│  DispatcherHandler                                          │
│      ↓                                                      │
│  RoutePredicateHandlerMapping                               │
│      ↓                                                      │
│  FilteringWebHandler                                        │
│  ├── Global Filters                                         │
│  └── Gateway Filters                                        │
│      ↓                                                      │
│  后端服务 (异步调用)                                          │
│      ↓                                                      │
│  HTTP Response                                              │
│                                                             │
│  特点：基于 Reactor，非阻塞 IO，事件驱动模型                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 性能对比

| 特性 | Zuul 1.x | Spring Cloud Gateway |
|------|---------|---------------------|
| 实现方式 | Servlet 阻塞式 | Reactor 非阻塞式 |
| IO 模型 | BIO | NIO |
| 性能 | 较低 | 较高（约 Zuul 的 1.6 倍） |
| 并发能力 | 受线程池限制 | 高并发支持 |
| 长连接 | 支持 | 支持 |
| WebSocket | 不支持 | 支持 |
| Spring 生态集成 | 一般 | 深度集成 |
| 维护状态 | 维护模式 | 活跃开发 |

### 1.3 性能测试数据

```
场景：1000 并发请求，平均响应时间测试

Zuul 1.x:
- 平均响应时间：50ms
- 吞吐量：约 20000 req/s
- CPU 使用率：较高

Spring Cloud Gateway:
- 平均响应时间：30ms
- 吞吐量：约 32000 req/s
- CPU 使用率：较低
```

## 二、核心概念

### 2.1 Route（路由）

路由是网关的基本构建块，由 ID、目标 URI、断言集合和过滤器集合组成。

```java
@Configuration
public class GatewayConfig {
    
    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("user-service", r -> r
                .path("/api/user/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .addRequestHeader("X-Request-Id", UUID.randomUUID().toString()))
                .uri("lb://user-service"))
            .route("order-service", r -> r
                .path("/api/order/**")
                .filters(f -> f.stripPrefix(1))
                .uri("lb://order-service"))
            .build();
    }
}
```

```yaml
# application.yml 配置方式
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=1
            - AddRequestHeader=X-Request-Id, ${value}
```

### 2.2 Predicate（断言）

断言用于匹配 HTTP 请求，决定是否走某个路由。

```
┌─────────────────────────────────────────────────────────────┐
│                     Predicate 类型                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  路径匹配：                                                   │
│  ├── Path=/api/user/**        匹配路径                       │
│  └── Path=/api/order/**,/api/pay/**  多路径匹配              │
│                                                             │
│  请求方法：                                                   │
│  ├── Method=GET               只匹配 GET 请求                │
│  └── Method=GET,POST          匹配 GET 和 POST               │
│                                                             │
│  请求头：                                                     │
│  ├── Header=X-Request-Id, \d+  Header 值匹配正则             │
│  └── Header=Content-Type, application/json                  │
│                                                             │
│  请求参数：                                                   │
│  ├── Query=token              存在 token 参数                │
│  └── Query=name, test.        name 值匹配正则                │
│                                                             │
│  Cookie：                                                    │
│  └── Cookie=session, abc.     Cookie 匹配                    │
│                                                             │
│  时间相关：                                                   │
│  ├── After=2024-01-01T00:00:00+08:00[Asia/Shanghai]         │
│  ├── Before=2024-12-31T23:59:59+08:00[Asia/Shanghai]        │
│  └── Between=...                                             │
│                                                             │
│  远程地址：                                                   │
│  └── RemoteAddr=192.168.1.1/24  IP 地址匹配                  │
│                                                             │
│  权重：                                                       │
│  └── Weight=group1, 80        80% 流量走此路由               │
│                                                             │
│  组合使用：                                                   │
│  predicates:                                                 │
│    - Path=/api/user/**                                       │
│    - Method=GET                                              │
│    - Header=Authorization, Bearer .*                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Filter（过滤器）

过滤器用于修改请求和响应。

```
┌─────────────────────────────────────────────────────────────┐
│                     Filter 类型                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pre Filter（请求前）：                                       │
│  ├── AddRequestHeader        添加请求头                      │
│  ├── AddRequestParameter     添加请求参数                    │
│  ├── StripPrefix             去除路径前缀                    │
│  ├── PrefixPath              添加路径前缀                    │
│  ├── RewritePath             重写路径                        │
│  └── SetPath                 设置路径                        │
│                                                             │
│  Post Filter（响应后）：                                      │
│  ├── AddResponseHeader       添加响应头                      │
│  ├── SetResponseHeader       设置响应头                      │
│  ├── SetStatus               设置响应状态码                  │
│  └── RemoveResponseHeader    移除响应头                      │
│                                                             │
│  功能 Filter：                                               │
│  ├── RequestRateLimiter      限流                            │
│  ├── CircuitBreaker          熔断                            │
│  ├── Retry                   重试                            │
│  └── RedirectTo              重定向                          │
│                                                             │
│  Global Filter（全局过滤器）：                                │
│  └── 对所有路由生效                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 三、请求处理流程

### 3.1 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                  Gateway 核心组件                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DispatcherHandler                                          │
│  └── WebFlux 核心分发器                                      │
│      ↓                                                      │
│  RoutePredicateHandlerMapping                               │
│  └── 路由映射，匹配 Predicate                                │
│      ↓                                                      │
│  GatewayHandlerAdapter                                      │
│  └── 适配器，执行 Handler                                    │
│      ↓                                                      │
│  FilteringWebHandler                                        │
│  └── 过滤器链执行                                            │
│      ├── 加载 GlobalFilter                                  │
│      ├── 加载 GatewayFilter                                 │
│      └── 按 Order 排序执行                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 完整请求流程图

```
┌────────────────────────────────────────────────────────────────────┐
│                    Gateway 请求处理流程                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  HTTP Request                                                      │
│      ↓                                                             │
│  Reactor Netty Server                                              │
│      ↓                                                             │
│  DispatcherHandler                                                 │
│      ↓                                                             │
│  RoutePredicateHandlerMapping                                      │
│  ├── 遍历所有 Route                                                │
│  ├── 执行 Predicate 匹配                                           │
│  │   ├── Path 匹配                                                 │
│  │   ├── Method 匹配                                               │
│  │   ├── Header 匹配                                               │
│  │   └── ...                                                       │
│  └── 返回匹配的 Route                                              │
│      ↓                                                             │
│  GatewayHandlerAdapter                                             │
│      ↓                                                             │
│  FilteringWebHandler                                               │
│  ├── 加载所有 GlobalFilter                                         │
│  ├── 加载 Route 配置的 GatewayFilter                               │
│  ├── 按 Order 排序                                                 │
│  └── 执行过滤器链                                                   │
│      ↓                                                             │
│  【Pre Filter 阶段】                                                │
│  ├── 认证过滤器                                                    │
│  │   └── 验证 Token，无效则返回 401                               │
│  ├── 限流过滤器                                                    │
│  │   └── 检查限流，超限则返回 429                                  │
│  ├── 日志过滤器                                                    │
│  │   └── 记录请求信息                                              │
│  ├── StripPrefix                                                  │
│  │   └── 去除路径前缀                                              │
│  └── AddRequestHeader                                             │
│      └── 添加请求头                                                │
│      ↓                                                             │
│  【路由转发】                                                       │
│  LoadBalancerClientFilter                                         │
│  ├── 解析 lb:// 协议                                               │
│  ├── 从注册中心获取服务实例                                        │
│  ├── 负载均衡选择实例                                              │
│  └── 发送请求到后端服务                                            │
│      ↓                                                             │
│  【后端服务处理】                                                   │
│      ↓                                                             │
│  【Post Filter 阶段】                                               │
│  ├── AddResponseHeader                                            │
│  │   └── 添加响应头                                                │
│  ├── SetStatus                                                    │
│  │   └── 设置状态码                                                │
│  └── 日志过滤器                                                    │
│      └── 记录响应信息                                              │
│      ↓                                                             │
│  HTTP Response                                                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 3.3 源码分析

#### DispatcherHandler

```java
public class DispatcherHandler implements WebHandler {
    
    @Override
    public Mono<Void> handle(ServerWebExchange exchange) {
        // 遍历 HandlerMapping
        return Flux.fromIterable(this.handlerMappings)
            .concatMap(mapping -> mapping.getHandler(exchange))
            .next()
            .switchIfEmpty(createNotFoundError())
            .flatMap(handler -> invokeHandler(exchange, handler))
            .onErrorResume(ex -> handleResultError(ex, exchange));
    }
}
```

#### RoutePredicateHandlerMapping

```java
public class RoutePredicateHandlerMapping extends AbstractHandlerMapping {
    
    @Override
    protected Mono<?> getHandlerInternal(ServerWebExchange exchange) {
        // 查找匹配的路由
        return lookupRoute(exchange)
            .flatMap(route -> {
                exchange.getAttributes().put(GATEWAY_ROUTE_ATTR, route);
                return Mono.just(webHandler);
            });
    }
    
    protected Mono<Route> lookupRoute(ServerWebExchange exchange) {
        return getRouteLocator().getRoutes()
            .concatMap(route -> Mono.just(route)
                .filterWhen(r -> r.getPredicate().apply(exchange))
                .doOnNext(r -> exchange.getAttributes().put(GATEWAY_ROUTE_ATTR, r)))
            .next();
    }
}
```

#### FilteringWebHandler

```java
public class FilteringWebHandler implements WebHandler {
    
    private final List<GatewayFilter> globalFilters;
    
    @Override
    public Mono<Void> handle(ServerWebExchange exchange) {
        Route route = exchange.getRequiredAttribute(GATEWAY_ROUTE_ATTR);
        
        // 合并 GlobalFilter 和 Route 的 GatewayFilter
        List<GatewayFilter> gatewayFilters = route.getFilters();
        List<GatewayFilter> combined = new ArrayList<>(globalFilters);
        combined.addAll(gatewayFilters);
        
        // 按 Order 排序
        AnnotationAwareOrderComparator.sort(combined);
        
        // 创建过滤器链
        return new DefaultGatewayFilterChain(combined).filter(exchange);
    }
}

// 过滤器链执行
public class DefaultGatewayFilterChain {
    
    public Mono<Void> filter(ServerWebExchange exchange) {
        return Mono.defer(() -> {
            if (this.index < filters.size()) {
                GatewayFilter filter = filters.get(this.index);
                return filter.filter(exchange, this.next);
            }
            return Mono.empty();
        });
    }
}
```

## 四、内置 Predicate 详解

### 4.1 Path 路径匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 简单路径匹配
        - id: path-route
          uri: lb://user-service
          predicates:
            - Path=/api/user
        
        # 通配符匹配
        - id: wildcard-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
        
        # 多路径匹配
        - id: multi-path-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**,/api/users/**
        
        # 路径变量
        - id: path-variable-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/{id}
```

```java
// 路径变量获取
@Component
public class UserIdFilter implements GlobalFilter {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 获取路径变量
        String userId = exchange.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE)
            .get("id");
        // 使用变量...
        return chain.filter(exchange);
    }
}
```

### 4.2 Method 方法匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 单方法匹配
        - id: get-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
            - Method=GET
        
        # 多方法匹配
        - id: post-put-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
            - Method=POST,PUT
```

### 4.3 Header 请求头匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 存在 Header
        - id: header-exist-route
          uri: lb://user-service
          predicates:
            - Header=X-Request-Id
        
        # Header 值匹配正则
        - id: header-regex-route
          uri: lb://user-service
          predicates:
            - Header=X-Request-Id, \d+  # 数字
        
        # 认证 Header
        - id: auth-route
          uri: lb://user-service
          predicates:
            - Path=/api/secure/**
            - Header=Authorization, Bearer .+
```

### 4.4 Query 参数匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 存在参数
        - id: query-exist-route
          uri: lb://user-service
          predicates:
            - Query=token
        
        # 参数值匹配正则
        - id: query-regex-route
          uri: lb://user-service
          predicates:
            - Query=name, test.  # test 开头
        
        # 组合参数
        - id: multi-query-route
          uri: lb://user-service
          predicates:
            - Query=token
            - Query=version,v1
```

### 4.5 Cookie 匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # Cookie 匹配
        - id: cookie-route
          uri: lb://user-service
          predicates:
            - Cookie=session, ^[a-z0-9]+$
```

### 4.6 时间匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 指定时间之后
        - id: after-route
          uri: lb://user-service
          predicates:
            - After=2024-01-01T00:00:00+08:00[Asia/Shanghai]
        
        # 指定时间之前
        - id: before-route
          uri: lb://user-service
          predicates:
            - Before=2024-12-31T23:59:59+08:00[Asia/Shanghai]
        
        # 时间区间
        - id: between-route
          uri: lb://user-service
          predicates:
            - Between=2024-01-01T00:00:00+08:00[Asia/Shanghai], 2024-12-31T23:59:59+08:00[Asia/Shanghai]
```

### 4.7 RemoteAddr 地址匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 单个 IP
        - id: ip-route
          uri: lb://user-service
          predicates:
            - RemoteAddr=192.168.1.100
        
        # IP 段
        - id: ip-segment-route
          uri: lb://user-service
          predicates:
            - RemoteAddr=192.168.1.0/24
        
        # 多个 IP 段
        - id: multi-ip-route
          uri: lb://user-service
          predicates:
            - RemoteAddr=192.168.1.0/24,10.0.0.0/8
```

### 4.8 Weight 权重匹配

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 80% 流量
        - id: weight-high-route
          uri: lb://user-service-v2
          predicates:
            - Weight=group1, 80
        
        # 20% 流量
        - id: weight-low-route
          uri: lb://user-service-v1
          predicates:
            - Weight=group1, 20
```

## 五、内置 Filter 详解

### 5.1 请求头相关

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: header-filter-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            # 添加请求头
            - AddRequestHeader=X-Request-Foo, Bar
            - AddRequestHeader=X-Request-Time, ${time}
            
            # 设置请求头（覆盖）
            - SetRequestHeader=X-Request-Id, ${value}
            
            # 移除请求头
            - RemoveRequestHeader=X-Request-Unwanted
            
            # 添加请求参数
            - AddRequestParameter=foo, bar
            
            # 移除请求参数
            - RemoveRequestParameter=unwanted
```

### 5.2 路径相关

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: path-filter-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            # 去除路径前缀
            # /api/user/list -> /user/list
            - StripPrefix=1
            
            # 添加路径前缀
            # /list -> /api/user/list
            - PrefixPath=/api/user
            
            # 重写路径
            # /api/user/(?<segment>.*) -> /${segment}
            - RewritePath=/api/user/(?<segment>.*), /${segment}
            
            # 设置路径
            - SetPath=/api/user/{segment}
```

### 5.3 响应头相关

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: response-filter-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            # 添加响应头
            - AddResponseHeader=X-Response-Foo, Bar
            
            # 设置响应头
            - SetResponseHeader=X-Response-Time, ${time}
            
            # 移除响应头
            - RemoveResponseHeader=X-Response-Unwanted
            
            # 设置状态码
            - SetStatus=200
```

### 5.4 重定向

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 302 重定向
        - id: redirect-route
          uri: lb://user-service
          predicates:
            - Path=/old-path
          filters:
            - RedirectTo=302, https://example.com/new-path
```

### 5.5 重试机制

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: retry-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: Retry
              args:
                retries: 3                    # 重试次数
                statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE  # 触发重试的状态码
                methods: GET,POST             # 触发重试的方法
                backoff:
                  firstBackoff: 100ms         # 首次重试等待时间
                  maxBackoff: 500ms           # 最大等待时间
                  factor: 2                   # 退避因子
                  basedOnPreviousValue: false
```

## 六、自定义 GlobalFilter

### 6.1 认证过滤器

```java
@Component
@Slf4j
public class AuthGlobalFilter implements GlobalFilter, Ordered {
    
    @Value("${auth.enabled:true}")
    private boolean authEnabled;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().value();
        
        // 白名单路径
        if (isWhitePath(path)) {
            return chain.filter(exchange);
        }
        
        // 获取 Token
        String token = request.getHeaders().getFirst("Authorization");
        if (StringUtils.isEmpty(token)) {
            return unauthorized(exchange, "缺少认证信息");
        }
        
        // 验证 Token
        try {
            // 去除 Bearer 前缀
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }
            
            // JWT 验证
            Claims claims = JwtUtil.parseToken(token);
            String userId = claims.getSubject();
            
            // 将用户信息放入 Header
            ServerHttpRequest newRequest = request.mutate()
                .header("X-User-Id", userId)
                .header("X-User-Name", claims.get("name", String.class))
                .build();
            
            return chain.filter(exchange.mutate().request(newRequest).build());
            
        } catch (ExpiredJwtException e) {
            return unauthorized(exchange, "Token 已过期");
        } catch (Exception e) {
            log.error("Token 验证失败", e);
            return unauthorized(exchange, "Token 无效");
        }
    }
    
    private boolean isWhitePath(String path) {
        List<String> whiteList = Arrays.asList(
            "/api/auth/login",
            "/api/auth/register",
            "/api/health",
            "/actuator/**"
        );
        return whiteList.stream().anyMatch(path::startsWith);
    }
    
    private Mono<Void> unauthorized(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        
        Map<String, Object> result = new HashMap<>();
        result.put("code", 401);
        result.put("message", message);
        result.put("timestamp", System.currentTimeMillis());
        
        byte[] bytes = JSON.toJSONString(result).getBytes(StandardCharsets.UTF_8);
        DataBuffer buffer = response.bufferFactory().wrap(bytes);
        
        return response.writeWith(Mono.just(buffer));
    }
    
    @Override
    public int getOrder() {
        return -100;  // 高优先级
    }
}
```

### 6.2 日志过滤器

```java
@Component
@Slf4j
public class RequestLogGlobalFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        
        // 记录请求开始时间
        long startTime = System.currentTimeMillis();
        exchange.getAttributes().put("startTime", startTime);
        
        // 记录请求信息
        String requestId = UUID.randomUUID().toString();
        exchange.getAttributes().put("requestId", requestId);
        
        log.info("[{}] Request: {} {} from {}",
            requestId,
            request.getMethod(),
            request.getPath(),
            request.getRemoteAddress()
        );
        
        // 响应后记录日志
        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            Long start = exchange.getAttribute("startTime");
            if (start != null) {
                long duration = System.currentTimeMillis() - start;
                ServerHttpResponse response = exchange.getResponse();
                
                log.info("[{}] Response: {} {}ms",
                    requestId,
                    response.getStatusCode(),
                    duration
                );
            }
        }));
    }
    
    @Override
    public int getOrder() {
        return -200;  // 最高优先级
    }
}
```

### 6.3 跨域过滤器

```java
@Component
public class CorsGlobalFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        ServerHttpResponse response = exchange.getResponse();
        
        HttpHeaders headers = response.getHeaders();
        headers.add("Access-Control-Allow-Origin", "*");
        headers.add("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS");
        headers.add("Access-Control-Allow-Headers", "*");
        headers.add("Access-Control-Max-Age", "3600");
        
        // OPTIONS 请求直接返回
        if (request.getMethod() == HttpMethod.OPTIONS) {
            response.setStatusCode(HttpStatus.OK);
            return response.setComplete();
        }
        
        return chain.filter(exchange);
    }
    
    @Override
    public int getOrder() {
        return -300;
    }
}
```

## 七、自定义 PredicateFactory

### 7.1 自定义时间范围断言

```java
@Component
public class TimeBetweenRoutePredicateFactory extends AbstractRoutePredicateFactory<TimeBetweenConfig> {
    
    public TimeBetweenRoutePredicateFactory() {
        super(TimeBetweenConfig.class);
    }
    
    @Override
    public Predicate<ServerWebExchange> apply(TimeBetweenConfig config) {
        return exchange -> {
            LocalTime now = LocalTime.now();
            return now.isAfter(config.getStartTime()) && now.isBefore(config.getEndTime());
        };
    }
    
    @Override
    public List<String> shortcutFieldOrder() {
        return Arrays.asList("startTime", "endTime");
    }
    
    public static class TimeBetweenConfig {
        private LocalTime startTime;
        private LocalTime endTime;
        
        // getter/setter
    }
}
```

```yaml
# 使用自定义断言
spring:
  cloud:
    gateway:
      routes:
        - id: time-route
          uri: lb://user-service
          predicates:
            - TimeBetween=08:00,18:00  # 只在 8:00-18:00 生效
```

## 八、限流：RequestRateLimiter

### 8.1 令牌桶算法原理

```
┌─────────────────────────────────────────────────────────────┐
│                     令牌桶算法                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │           令牌桶 (Token Bucket)          │               │
│  │                                         │               │
│  │   ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐       │               │
│  │   │ T │ │ T │ │ T │ │   │ │   │       │               │
│  │   └───┘ └───┘ └───┘ └───┘ └───┘       │               │
│  │                                         │               │
│  │   当前令牌数: 3   桶容量: 5             │               │
│  └─────────────────────────────────────────┘               │
│                     ↑                                       │
│            按固定速率生成令牌                                  │
│            (replenishRate: 10/s)                            │
│                                                             │
│  请求到达:                                                   │
│  ├── 有令牌 → 取走令牌 → 请求通过                            │
│  └── 无令牌 → 请求被拒绝 → 返回 429                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 基于内存的限流

```java
@Configuration
public class RateLimiterConfig {
    
    @Bean
    public KeyResolver ipKeyResolver() {
        // 按 IP 限流
        return exchange -> Mono.just(
            exchange.getRequest()
                .getRemoteAddress()
                .getAddress()
                .getHostAddress()
        );
    }
    
    @Bean
    public KeyResolver userKeyResolver() {
        // 按用户限流
        return exchange -> Mono.just(
            exchange.getRequest()
                .getHeaders()
                .getFirst("X-User-Id")
        );
    }
    
    @Bean
    public KeyResolver apiKeyResolver() {
        // 按 API 路径限流
        return exchange -> Mono.just(
            exchange.getRequest().getPath().value()
        );
    }
}
```

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: rate-limit-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: RequestRateLimiter
              args:
                # 每秒生成令牌数
                replenishRate: 10
                # 桶容量
                burstCapacity: 20
                # 每次请求消耗令牌数
                requestedTokens: 1
                # KeyResolver Bean 名称
                key-resolver: "#{@ipKeyResolver}"
```

### 8.3 基于 Redis 的分布式限流

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
</dependency>
```

```yaml
spring:
  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD}
  cloud:
    gateway:
      routes:
        - id: redis-rate-limit-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
                redis-rate-limiter.requestedTokens: 1
                key-resolver: "#{@ipKeyResolver}"
```

```java
// 自定义限流配置
@Bean
public RedisRateLimiter customRedisRateLimiter() {
    return new RedisRateLimiter(10, 20);
}
```

### 8.4 限流响应处理

```java
@Component
public class RateLimiterExceptionHandler implements WebExceptionHandler {
    
    @Override
    public Mono<Void> handle(ServerWebExchange exchange, Throwable ex) {
        if (ex instanceof RequestNotPermittedException) {
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
            response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
            
            Map<String, Object> result = new HashMap<>();
            result.put("code", 429);
            result.put("message", "请求过于频繁，请稍后再试");
            result.put("timestamp", System.currentTimeMillis());
            
            byte[] bytes = JSON.toJSONString(result).getBytes(StandardCharsets.UTF_8);
            DataBuffer buffer = response.bufferFactory().wrap(bytes);
            
            return response.writeWith(Mono.just(buffer));
        }
        return Mono.error(ex);
    }
}
```

## 九、熔断：CircuitBreaker

### 9.1 添加依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-circuitbreaker-reactor-resilience4j</artifactId>
</dependency>
```

### 9.2 配置熔断

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: circuit-breaker-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: CircuitBreaker
              args:
                name: userServiceCircuitBreaker
                fallbackUri: forward:/fallback/user

# Resilience4j 配置
resilience4j:
  circuitbreaker:
    configs:
      default:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        failureRateThreshold: 50
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 3
    instances:
      userServiceCircuitBreaker:
        baseConfig: default
```

### 9.3 降级处理

```java
@RestController
@RequestMapping("/fallback")
public class FallbackController {
    
    @GetMapping("/user")
    public Mono<Map<String, Object>> userFallback() {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 503);
        result.put("message", "用户服务暂时不可用，请稍后再试");
        result.put("timestamp", System.currentTimeMillis());
        return Mono.just(result);
    }
    
    @GetMapping("/order")
    public Mono<Map<String, Object>> orderFallback() {
        Map<String, Object> result = new HashMap<>();
        result.put("code", 503);
        result.put("message", "订单服务暂时不可用，请稍后再试");
        result.put("timestamp", System.currentTimeMillis());
        return Mono.just(result);
    }
}
```

## 📖 高频面试题

### Q1: Spring Cloud Gateway 的核心组件有哪些？

**答：**

#### 1. Route（路由）
- 网关的基本构建块
- 包含 ID、URI、Predicate、Filter
- 配置方式：YAML 或 Java API

#### 2. Predicate（断言）
- 匹配 HTTP 请求
- 决定请求是否走某个路由
- 内置：Path、Method、Header、Query、Cookie、After/Before、RemoteAddr、Weight

#### 3. Filter（过滤器）
- 修改请求和响应
- 分类：GatewayFilter（路由级别）、GlobalFilter（全局）
- 执行阶段：Pre Filter、Post Filter

#### 4. 核心处理器
- RoutePredicateHandlerMapping：路由匹配
- FilteringWebHandler：过滤器链执行
- LoadBalancerClientFilter：负载均衡

### Q2: Gateway 和 Zuul 的区别？

**答：**

| 特性 | Zuul 1.x | Spring Cloud Gateway |
|------|---------|---------------------|
| 架构 | Servlet 阻塞式 | Reactor 非阻塞式 |
| IO 模型 | BIO | NIO |
| 性能 | 较低 | 较高 |
| 并发能力 | 受线程池限制 | 高并发支持 |
| WebSocket | 不支持 | 支持 |
| 线程模型 | 每请求一线程 | 事件驱动 |
| 背压支持 | 不支持 | 支持 |

### Q3: Gateway 如何实现限流？

**答：**

#### 1. 内置 RequestRateLimiter
- 基于令牌桶算法
- 支持内存和 Redis 两种模式

#### 2. 配置方式
```yaml
filters:
  - name: RequestRateLimiter
    args:
      redis-rate-limiter.replenishRate: 10  # 每秒生成令牌数
      redis-rate-limiter.burstCapacity: 20  # 桶容量
      key-resolver: "#{@ipKeyResolver}"     # 限流 Key
```

#### 3. KeyResolver
- IP 限流：按客户端 IP
- 用户限流：按用户 ID
- API 限流：按请求路径

### Q4: Gateway 如何实现熔断？

**答：**

#### 1. 集成 Resilience4j
```yaml
filters:
  - name: CircuitBreaker
    args:
      name: myCircuitBreaker
      fallbackUri: forward:/fallback
```

#### 2. 熔断状态
- Closed：正常状态
- Open：熔断状态，直接返回降级
- Half Open：半开状态，尝试恢复

#### 3. 降级处理
- 配置 fallbackUri
- 编写降级接口

### Q5: Gateway 如何实现认证？

**答：**

#### 1. 自定义 GlobalFilter
```java
@Component
public class AuthGlobalFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 1. 白名单检查
        // 2. Token 获取和验证
        // 3. 用户信息传递
        // 4. 无效则返回 401
    }
}
```

#### 2. 配置顺序
- Order 值越小，优先级越高
- 认证过滤器应该高优先级

#### 3. 安全配置
- 白名单路径
- Token 黑名单
- 权限校验

---

**参考链接：**
- [Spring Cloud Gateway 官方文档](https://docs.spring.io/spring-cloud-gateway/docs/current/reference/html/)
- [Gateway 核心原理-掘金](https://juejin.cn/post/7232856790361280571)
- [Gateway 限流详解-CSDN](https://blog.csdn.net/zhengwenbo/article/details/108531239)
