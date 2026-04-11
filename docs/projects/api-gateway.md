---
layout: default
title: API 网关设计与实现
---

# API 网关设计与实现

> 分布式系统的统一入口，承担路由、认证、限流、协议转换等核心职责

---

## 一、网关核心职责

API 网关（API Gateway）是微服务架构中的**统一入口**，所有外部请求先经过网关，由网关进行路由转发。网关的七大核心职责：

### 1.1 路由转发（Routing）

根据请求路径、参数、Header 等信息，将请求精准路由到对应的后端服务。

```
请求入口                          后端服务
┌─────────────────┐              ┌──────────────┐
│  /api/user/*    │──────────────▶│  User Service │
│  /api/product/*│──────────────▶│ Product Svc   │
│  /api/order/*   │──────────────▶│  Order Svc   │
│  /api/pay/*     │──────────────▶│   Pay Svc    │
└─────────────────┘              └──────────────┘
         ▲ 认证/限流/日志/协议转换
       [API Gateway]
```

### 1.2 认证授权（Authentication & Authorization）

- **身份认证**：JWT Token 解析、Session 验证、OAuth2 令牌校验
- **权限控制**：RBAC 权限判断、接口级别鉴权
- **敏感信息过滤**：对响应中的敏感数据进行脱敏处理

### 1.3 限流熔断（Rate Limiting & Circuit Breaker）

- **限流**：保护后端服务不被突发流量冲垮
- **熔断**：当下游服务不可用时，快速失败，防止雪崩
- **降级**：核心功能优先，非核心功能暂时关闭

### 1.4 日志监控（Logging & Monitoring）

- 记录请求日志（路径、耗时、状态码、来源 IP）
- 链路追踪（OpenTelemetry、Zipkin、Jaeger）
- 监控告警（Prometheus + Grafana）

### 1.5 协议转换（Protocol Translation）

- REST → Dubbo / gRPC / SOAP
- HTTP → WebSocket
- 支持 GraphQL 适配层

### 1.6 缓存处理（Caching）

- 热点数据 Redis 缓存
- 浏览器缓存控制（Cache-Control、ETag）
- 响应结果 gzip 压缩

### 1.7 安全防护（Security）

- IP 黑名单 / 白名单
- 防 SQL 注入 / XSS
- CORS 跨域处理
- DDOS 防护

---

## 二、技术选型对比

### 2.1 主流网关技术栈

| 特性 | Nginx | Kong | Spring Cloud Gateway | APISIX |
|------|-------|------|---------------------|--------|
| **语言** | C | Lua | Java | Go/Lua |
| **性能** | 极高 | 高 | 中 | 极高 |
| **吞吐量** | 10万+/s | 5万+/s | 2万+/s | 10万+/s |
| **生态** | 成熟 | 插件丰富 | Spring 全家桶 | 云原生友好 |
| **配置方式** | 配置文件 | Admin API + DB | Java/YAML 配置 | YAML/Admin API |
| **动态路由** | reload 需要 reload | 支持 | 支持 | 支持 |
| **插件扩展** | C 模块开发 | Lua 插件 | Java Filter | Lua/Wasm/JS |
| **学习成本** | 中 | 中 | 低（Java 开发者友好） | 中 |
| **适用场景** | 中小型项目 | 中大型项目 | Spring Cloud 项目 | 云原生/多语言 |

### 2.2 如何选择？

- **Spring Cloud 项目** → 选 Spring Cloud Gateway，Java 开发者友好，与 Spring Boot 生态无缝集成
- **追求极致性能** → 选 Nginx / APISIX
- **需要丰富插件生态** → 选 Kong（插件市场成熟）
- **容器化 / Kubernetes 场景** → 选 APISIX（原生支持 K8s Ingress）

---

## 三、Spring Cloud Gateway 核心架构

### 3.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                      Gateway Handler Mapping                │
│                   (根据 Predicate 匹配路由)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Gateway Web Handler                    │
│                   (入口处理器，统一请求入口)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Filter Chain (过滤器链)                   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  ① Global │  │  ② Global │  │  自定义   │  │  自定义   │   │
│  │  Filter A │→ │  Filter B │→ │  Filter C │→ │  Filter D │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│     (日志)        (认证)          (限流)       (路由)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Downstream Service                        │
│                    (最终转发的后端服务)                        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 三大核心组件

#### Route（路由）

路由是网关的基本组成单元，包含：ID、目标 URI、Predicate 集合、Filter 集合。

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service        # lb = LoadBalancer，支持负载均衡
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=1             # 去掉第一层路径 /api
```

#### Predicate（谓词）

Predicate 用于匹配 HTTP 请求，符合条件的请求才会被路由。

```yaml
predicates:
  # 路径匹配
  - Path=/api/user/**

  # Method 匹配
  - Method=GET,POST

  # Header 匹配（带正则）
  - Header=X-Request-Id, \d+

  # Query 参数匹配
  - Query=page, [0-9]+

  # Host 匹配
  - Host=**.example.com

  # 时间匹配（After/Before/Between）
  - After=2024-01-01T00:00:00+08:00[Asia/Shanghai]

  # Cookie 匹配
  - Cookie=session, abc.*
```

#### Filter（过滤器）

Filter 是请求处理的拦截器，分为**全局过滤器**（GlobalFilter）和**路由级别过滤器**（GatewayFilter）。

```yaml
filters:
  # StripPrefix：去掉 URL 前缀
  - StripPrefix=1

  # AddRequestHeader：添加请求头
  - AddRequestHeader=X-Gateway, SpringCloudGateway

  # AddResponseHeader：添加响应头
  - AddResponseHeader=X-Response-Time, -1

  # PrefixPath：添加前缀路径
  - PrefixPath=/api

  # Retry：重试机制
  - name: Retry
    args:
      retries: 3
      methods: GET
      series: SERVER_ERROR
```

---

## 四、路由配置详解

### 4.1 静态路由配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 用户服务
        - id: user-service
          uri: http://user-service:8080
          predicates:
            - Path=/user/**
          filters:
            - StripPrefix=1

        # 订单服务
        - id: order-service
          uri: http://order-service:8080
          predicates:
            - Path=/order/**
          filters:
            - StripPrefix=1

        # 商品服务（带负载均衡）
        - id: product-service
          uri: lb://product-service
          predicates:
            - Path=/product/**
          filters:
            - name: CircuitBreaker
              args:
                name: productCircuitBreaker
                fallbackUri: forward:/fallback/product
```

### 4.2 动态路由

动态路由通过配置中心（Nacos、Apollo、Consul）实现，无需重启即可更新路由规则。

```java
// 方式1：实现 RouteDefinitionRepository
@Component
public class DynamicRouteRepository implements RouteDefinitionRepository {

    @Autowired
    private RouteDefinitionWriter routeDefinitionWriter;

    @Autowired
    private ApplicationEventPublisher publisher;

    @Override
    public Flux<RouteDefinition> getRouteDefinitions() {
        // 从配置中心读取路由定义
        return Flux.fromIterable(loadFromConfigCenter());
    }

    @Override
    public Mono<RouteDefinition> save(Mono<RouteDefinition> route) {
        return route.flatMap(rd -> {
            routeDefinitionWriter.save(Mono.just(rd))
                .then(publisher.publishEvent(new RefreshRoutesEvent(rd)));
            return Mono.just(rd);
        });
    }

    @Override
    public Mono<Void> delete(Mono<String> routeId) {
        return routeId.flatMap(id -> {
            routeDefinitionWriter.delete(Mono.just(id))
                .then(publisher.publishEvent(new RefreshRoutesEvent(null)));
            return Mono.empty();
        });
    }
}
```

### 4.3 路由条件与动态权重

```java
// 动态权重路由：灰度发布
@Bean
public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
        .route("v1-route", r -> r
            .path("/api/product/**")
            .and()
            .weight("group1", 90)  // 90% 流量到 v1
            .filters(f -> f.stripPrefix(1).prefixPath("/v1"))
            .uri("lb://product-service"))
        .route("v2-route", r -> r
            .path("/api/product/**")
            .and()
            .weight("group1", 10)  // 10% 流量到 v2
            .filters(f -> f.stripPrefix(1).prefixPath("/v2"))
            .uri("lb://product-service"))
        .build();
}
```

---

## 五、过滤器详解

### 5.1 全局过滤器（GlobalFilter）

所有经过网关的请求都会执行全局过滤器：

```java
// 全局日志过滤器
@Component
@Order(-100)  // 数字越小越先执行
public class GlobalLoggingFilter implements GlobalFilter {

    private static final Logger log = LoggerFactory.getLogger(GlobalLoggingFilter.class);

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        String method = request.getMethod().name();
        String ip = getClientIp(request);

        long startTime = System.currentTimeMillis();
        log.info("[Gateway] 请求进入: {} {} from {}", method, path, ip);

        return chain.filter(exchange)
            .then(Mono.fromRunnable(() -> {
                long cost = System.currentTimeMillis() - startTime;
                int status = exchange.getResponse().getStatusCode().value();
                log.info("[Gateway] 响应返回: {} {} - {} ({}ms)",
                    method, path, status, cost);
            }));
    }

    private String getClientIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getHeaders().getFirst("X-Real-IP");
        }
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddress() != null ?
                request.getRemoteAddress().getAddress().getHostAddress() : "unknown";
        }
        return ip;
    }
}
```

### 5.2 认证过滤器（核心实现）

```java
@Component
public class AuthenticationFilter implements GlobalFilter {

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private WhiteListConfig whiteListConfig;

    // 白名单路径（无需认证）
    private static final List<String> WHITE_LIST = Arrays.asList(
        "/auth/login",
        "/auth/register",
        "/health",
        "/api/public/**"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();

        // 1. 检查白名单
        if (isWhiteListed(path)) {
            return chain.filter(exchange);
        }

        // 2. 获取 Token
        String token = extractToken(exchange.getRequest());
        if (token == null) {
            return unauthorized(exchange, "Missing token");
        }

        // 3. 验证 Token
        try {
            Claims claims = jwtUtil.parseToken(token);
            String userId = claims.getSubject();
            String username = claims.get("username", String.class);

            // 4. 权限检查
            String method = exchange.getRequest().getMethod().name();
            if (!hasPermission(userId, path, method)) {
                return forbidden(exchange, "No permission");
            }

            // 5. 将用户信息传递到下游服务（通过 Header）
            ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
                .header("X-User-Id", userId)
                .header("X-Username", username)
                .header("X-Token", token)
                .build();

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (ExpiredJwtException e) {
            return unauthorized(exchange, "Token expired");
        } catch (JwtException e) {
            return unauthorized(exchange, "Invalid token");
        }
    }

    private String extractToken(ServerHttpRequest request) {
        String bearerToken = request.getHeaders().getFirst("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }

    private boolean isWhiteListed(String path) {
        return WHITE_LIST.stream().anyMatch(pattern ->
            path.matches(pattern.replace("**", ".*")));
    }

    private boolean hasPermission(String userId, String path, String method) {
        // TODO: 从权限服务获取用户权限
        // 实际项目中应该查询 Redis 或权限服务
        return true;
    }

    private Mono<Void> unauthorized(ServerWebExchange exchange, String message) {
        exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);
        String body = "{\"code\": 401, \"message\": \"" + message + "\"}";
        DataBuffer buffer = exchange.getResponse().bufferFactory().wrap(body.getBytes());
        return exchange.getResponse().writeWith(Mono.just(buffer));
    }

    private Mono<Void> forbidden(ServerWebExchange exchange, String message) {
        exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);
        String body = "{\"code\": 403, \"message\": \"" + message + "\"}";
        DataBuffer buffer = exchange.getResponse().bufferFactory().wrap(body.getBytes());
        return exchange.getResponse().writeWith(Mono.just(buffer));
    }
}
```

### 5.3 自定义 GatewayFilter

```java
// 请求限流过滤器
@Component
public class RateLimitFilter implements GatewayFilter {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String ip = getClientIp(exchange.getRequest());
        String key = "rate_limit:" + ip;

        // 滑动窗口限流
        Long count = redisTemplate.opsForValue().increment(key);

        if (count == 1) {
            redisTemplate.expire(key, Duration.ofSeconds(60));
        }

        if (count > 100) {  // 每分钟最多 100 次
            exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
            return exchange.getResponse().setComplete();
        }

        // 添加限流信息到响应头
        exchange.getResponse().getHeaders().add("X-Rate-Limit-Remaining", String.valueOf(100 - count));
        return chain.filter(exchange);
    }

    private String getClientIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip == null) ip = request.getRemoteAddress().getAddress().getHostAddress();
        return ip;
    }
}
```

---

## 六、限流实现

### 6.1 Redis + Lua 令牌桶算法

```lua
--令牌桶算法：key=令牌桶名称，rate=每秒放入令牌数，capacity=桶容量
local key = KEYS[1]           -- 限流 key（如 "rate_limit:user:123"）
local capacity = tonumber(ARGV[1])   -- 桶容量
local rate = tonumber(ARGV[2])       -- 每秒补充令牌数
local now = tonumber(ARGV[3])       -- 当前时间戳（秒）
local requested = tonumber(ARGV[4]) -- 请求的令牌数

-- 获取当前令牌数
local last_tokens = tonumber(redis.call('get', key) or capacity)
local last_refreshed = tonumber(redis.call('get', key .. ':ts') or now)

-- 计算应该补充的令牌数
local delta = math.max(0, (now - last_refreshed) * rate)
local tokens = math.min(capacity, last_tokens + delta)

-- 检查是否允许通过
if tokens >= requested then
    tokens = tokens - requested
    redis.call('set', key, tokens)
    redis.call('set', key .. ':ts', now)
    redis.call('expire', key, 120)  -- 2分钟过期
    return 1  -- 允许
else
    return 0  -- 拒绝
end
```

### 6.2 Sentinel 自适应限流

```java
// 引入 Sentinel
<dependency>
    <groupId>com.alibaba.csp</groupId>
    <artifactId>sentinel-spring-cloud-gateway-adapter</artifactId>
</dependency>

@Configuration
public class SentinelConfig {

    @Bean
    public SentinelGatewayFilter sentinelGatewayFilter() {
        return new SentinelGatewayFilter();
    }

    @PostConstruct
    public void initRules() {
        // 定义限流规则
        GatewayFlowRule rule = new GatewayFlowRule("order-service")
            .setCount(100)           // QPS 阈值
            .setIntervalSec(1)       // 统计间隔（秒）
            .setControlBehavior(GatewayFlowControlBehavior.REJECT)
            .setMaxQueueingTimeoutMs(500); // 最大排队等待时间

        GatewayRuleManager.loadRules(Collections.singletonList(rule));
    }

    @PostConstruct
    public void initBlockHandler() {
        BlockRequestHandler handler = (exchange, ex) -> {
            Map<String, Object> result = new HashMap<>();
            result.put("code", 429);
            result.put("message", "请求过于频繁，请稍后重试");
            return Mono.just(ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .contentType(MediaType.APPLICATION_JSON)
                .body(result));
        };
        GatewayApiDefinitionManager.loadApiDefinitions(
            Collections.singleton(new ApiDefinition("order_api")
                .setPredicateItems(new HashSet<>(Arrays.asList(
                    new ApiPredicateItem().setPattern("/order/**")
                )))));
        // 注册降级处理器
        // ...
    }
}
```

---

## 七、熔断降级

### 7.1 Spring Cloud CircuitBreaker

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          filters:
            - name: CircuitBreaker
              args:
                name: userCircuitBreaker
                fallbackUri: forward:/fallback/user  # 降级回调
```

```java
// 熔断降级响应
@RestController
public class FallbackController {

    @GetMapping("/fallback/{service}")
    public Map<String, Object> fallback(@PathVariable String service,
                                         Throwable cause) {
        Map<String, Object> response = new HashMap<>();
        response.put("code", 503);
        response.put("service", service);
        response.put("message", "服务暂时不可用，请稍后重试");
        response.put("error", cause != null ? cause.getMessage() : "Unknown");
        return response;
    }
}
```

### 7.2 Resilience4j 熔断配置

```yaml
resilience4j:
  circuitbreaker:
    instances:
      userService:
        registerHealthIndicator: true
        slidingWindowSize: 10        # 滑动窗口大小
        minimumNumberOfCalls: 5      # 最小调用数
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
        waitDurationInOpenState: 10s # 熔断持续时间
        failureRateThreshold: 50      # 失败率阈值（50%）
        eventConsumerBufferSize: 10

  timelimiter:
    instances:
      userService:
        timeoutDuration: 3s          # 超时时间
        cancelRunningFuture: true
```

---

## 八、网关高可用

### 8.1 多节点部署

```
                    ┌──────────────────┐
                    │   Load Balancer   │
                    │  (Nginx/LVS)      │
                    └────────┬─────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Gateway Node1 │ │ Gateway Node2 │ │ Gateway Node3 │
    │  (无状态)      │ │  (无状态)      │ │  (无状态)      │
    └──────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌──────────────────┐
                    │  Redis Cluster   │
                    │  (Session/限流)   │
                    └──────────────────┘
```

### 8.2 健康检查

```yaml
# Spring Boot Actuator 配置
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,gateway
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true  # K8s probes
  health:
    circuitBreakers:
      enabled: true
    redis:
      enabled: true
```

```java
// 自定义健康检查
@Component
public class GatewayHealthIndicator implements ReactiveHealthIndicator {

    @Autowired
    private LoadBalancerExchangeFilterFunction lbFunction;

    @Override
    public Mono<Health> health() {
        return lbFunction.choose("user-service")
            .flatMap(response -> {
                if (response.statusCode() == HttpStatus.OK) {
                    return Mono.just(Health.up().build());
                } else {
                    return Mono.just(Health.down()
                        .withDetail("status", response.statusCode())
                        .build());
                }
            })
            .onErrorResume(e -> Mono.just(Health.down()
                .withDetail("error", e.getMessage()).build()));
    }
}
```

---

## 九、协议转换

### 9.1 REST → Dubbo

```java
// 网关收到 REST 请求，转换为 Dubbo 调用
@Configuration
public class DubboProxyConfig {

    @Bean
    public RouteLocator dubboRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("dubbo-user-route", r -> r
                .path("/rpc/user/**")
                .filters(f -> f.stripPrefix(1))
                .uri("dubbo://user-service"))
            .build();
    }
}

// 自定义过滤器处理 REST → Dubbo 转换
@Component
public class DubboProxyFilter implements GlobalFilter {

    @Autowired
    private DubboProxyProperties dubboProxyProperties;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 1. 解析 REST 请求为 Dubbo Invocation
        DubboInvocation invocation = parseRestRequest(exchange);

        // 2. 通过 RPC Client 调用 Dubbo 服务
        DubboResponse response = dubboClient.invoke(invocation);

        // 3. 将 Dubbo 响应转换回 HTTP 响应
        return writeResponse(exchange, response);
    }
}
```

### 9.2 GraphQL 适配

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: graphql-route
          uri: http://graphql-service:8080
          predicates:
            - Path=/graphql
```

```java
// GraphQL 请求代理
@Component
public class GraphQLProxyFilter implements GlobalFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        if (!request.getPath().value().equals("/graphql")) {
            return chain.filter(exchange);
        }

        // 转发 GraphQL 请求到 GraphQL 服务
        return webClient.post()
            .uri("http://graphql-service/graphql")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(request.getBody())
            .retrieve()
            .bodyToMono(String.class)
            .flatMap(body -> {
                exchange.getResponse().getHeaders().add("Content-Type", "application/json");
                DataBuffer buffer = exchange.getResponse().bufferFactory().wrap(body.getBytes());
                return exchange.getResponse().writeWith(Mono.just(buffer));
            });
    }
}
```

---

## 十、响应缓存

### 10.1 Redis 缓存热点接口

```java
@Component
public class ResponseCacheFilter implements GlobalFilter {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    private static final Duration CACHE_TTL = Duration.ofMinutes(5);

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 只缓存 GET 请求
        if (!"GET".equalsIgnoreCase(exchange.getRequest().getMethod().name())) {
            return chain.filter(exchange);
        }

        String cacheKey = buildCacheKey(exchange);
        String cached = redisTemplate.opsForValue().get(cacheKey);

        if (cached != null) {
            // 命中缓存，直接返回
            exchange.getResponse().getHeaders().add("X-Cache", "HIT");
            return writeJsonResponse(exchange, cached);
        }

        // 未命中，执行业务逻辑
        return chain.filter(exchange)
            .then(Mono.fromFuture(() -> {
                CachedResponse cachedResponse = extractResponse(exchange);
                if (cachedResponse != null) {
                    redisTemplate.opsForValue().set(
                        cacheKey,
                        cachedResponse.getBody(),
                        CACHE_TTL
                    );
                }
                return Mono.empty();
            }));
    }

    private String buildCacheKey(ServerWebExchange exchange) {
        String path = exchange.getRequest().getURI().getPath();
        String query = exchange.getRequest().getURI().getQuery();
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        return "gateway:cache:" + userId + ":" + path + (query != null ? "?" + query : "");
    }

    private Mono<Void> writeJsonResponse(ServerWebExchange exchange, String body) {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        DataBuffer buffer = exchange.getResponse().bufferFactory().wrap(bytes);
        exchange.getResponse().getHeaders().add("Content-Type", "application/json");
        return exchange.getResponse().writeWith(Mono.just(buffer));
    }
}
```

---

## 十一、面试高频题

### 面试题 1：网关的核心职责是什么？它解决了什么问题？

**参考答案：**

网关的七大核心职责：
1. **路由转发**：统一入口，根据规则路由到后端服务
2. **认证授权**：JWT 解析、Session 验证、权限控制
3. **限流熔断**：令牌桶、滑动窗口、Sentinel 保护后端
4. **日志监控**：链路追踪、耗时监控、告警
5. **协议转换**：REST ↔ Dubbo、HTTP ↔ WebSocket
6. **缓存处理**：Redis 缓存热点数据，减少后端压力
7. **安全防护**：IP 黑名单、防注入、CORS、DDOS 防护

**解决的问题：**
- 客户端直接对接多个服务导致耦合
- 后端服务暴露安全问题
- 跨域、日志分散等横切关注点无法统一处理

---

### 面试题 2：Spring Cloud Gateway 的工作流程是什么？

**参考答案：**

```
客户端请求
    ↓
Gateway Handler Mapping（Predicate 匹配路由）
    ↓
Gateway Web Handler（入口处理器）
    ↓
Filter Chain（过滤器链：全局 Filter → 路由 Filter）
    ↓
代理发送请求到 Downstream
    ↓
Filter Chain（倒序执行：路由 Filter → 全局 Filter）
    ↓
客户端响应
```

**核心组件：**
- **Route**：路由定义，包含 URI、Predicate、Filter
- **Predicate**：条件匹配（路径、Method、Header、时间等）
- **Filter**：请求/响应拦截处理（全局 Filter 全链路生效，路由 Filter 仅当前路由生效）

---

### 面试题 3：如何实现网关的限流？

**参考答案：**

**方案一：Redis + Lua 令牌桶**

```lua
-- Lua 脚本实现令牌桶原子操作
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local last_tokens = tonumber(redis.call('get', key) or capacity)
local last_refreshed = tonumber(redis.call('get', key..':ts') or now)
local delta = math.max(0, (now - last_refreshed) * rate)
local tokens = math.min(capacity, last_tokens + delta)

if tokens >= requested then
    redis.call('set', key, tokens - requested)
    redis.call('set', key..':ts', now)
    return 1
else
    return 0
end
```

**方案二：Sentinel 自适应限流**

通过引入 `sentinel-spring-cloud-gateway-adapter`，配置 QPS 阈值、并发线程数等规则。

**常见限流维度：**
- 按 IP（防止单 IP 刷接口）
- 按 UserID（防止单用户过度请求）
- 按接口维度（热点接口单独限流）
- 按 Gateway 集群全局维度

---

### 面试题 4：网关如何做认证？Token 如何传递到下游服务？

**参考答案：**

**认证流程：**
1. 客户端携带 JWT Token 访问网关
2. 全局认证 Filter 拦截请求，解析 Token
3. Token 有效 → 将用户信息放入 Header，转发到下游
4. Token 无效 → 直接返回 401

```java
// 将用户信息通过 Header 传递（不是 Body，避免影响业务）
ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
    .header("X-User-Id", userId)
    .header("X-Username", username)
    .header("X-Roles", roles)
    .build();
```

**下游服务通过 `@RequestHeader("X-User-Id")` 获取用户信息：**

```java
@GetMapping("/order")
public Order getOrder(@RequestHeader("X-User-Id") String userId) {
    return orderService.getByUserId(userId);
}
```

**安全注意：**
- 下游服务必须验证 Header 来源是网关（可在网关添加签名，下游验证）
- 敏感 Header 需要过滤（如 Authorization Token 可脱敏后传递）
- 生产环境使用 mTLS 双向认证确保服务间通信安全

---

### 面试题 5：如何设计一个高可用的网关架构？

**参考答案：**

**架构要点：**

1. **无状态部署**：网关本身不存储状态，Session/Token/限流数据存储在 Redis
2. **多节点负载均衡**：Nginx/LVS 负载均衡多个 Gateway 节点
3. **健康检查**：定期探测 Gateway 节点存活，自动剔除故障节点
4. **熔断降级**：当下游服务不可用时，返回预设降级响应
5. **限流保护**：网关层限流，保护后端不被突发流量冲垮
6. **配置中心**：路由规则、限流规则存放在 Nacos/Apollo，支持动态更新
7. **监控告警**：链路追踪（OpenTelemetry）、指标监控（Prometheus）、日志聚合

```
                        ┌────────────────┐
                        │   DNS / SLB    │
                        │  (高可用入口)   │
                        └───────┬────────┘
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌────────────┐   ┌────────────┐   ┌────────────┐
        │  Gateway 1 │   │  Gateway 2 │   │  Gateway 3 │
        │  (无状态)   │   │  (无状态)   │   │  (无状态)   │
        └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │    Redis Cluster     │
                    │  (共享状态/限流/缓存) │
                    └─────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ User Svc │    │ Order Svc│    │Product Svc│
        └──────────┘    └──────────┘    └──────────┘
```

---

## 十二、总结

API 网关是微服务架构的**必选项**，它的核心价值：

1. **统一入口**：客户端只需对接网关，后端服务变化对客户端透明
2. **横切关注点统一处理**：认证、限流、日志、安全都在网关层处理
3. **协议转换与适配**：支持多协议接入，适配异构系统
4. **防护与治理**：限流、熔断、降级保护系统稳定性

**Spring Cloud Gateway 是 Java 开发者最友好的选择**，掌握其 Route/Predicate/Filter 三大核心概念，就能应对大部分网关场景。

---

> 📚 **延伸阅读**
> - [Spring Cloud Gateway 官方文档](https://docs.spring.io/spring-cloud-gateway/docs/current/reference/html/)
> - [Sentinel 网关限流](https://github.com/alibaba/Sentinel/wiki/网关限流)
> - [APISIX 官方文档](https://apisix.apache.org/zh/docs/apisix/getting-started/)
> - [微服务架构设计：API Gateway](https://microservices.io/patterns/apigateway.html)
