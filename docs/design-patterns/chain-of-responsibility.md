---
layout: default
title: 责任链模式（Chain of Responsibility）：请求在链中传递
---
# 责任链模式（Chain of Responsibility）：请求在链中传递

## 🎯 面试题：什么是责任链模式？Spring 中有哪些应用？

> 责任链模式让请求沿着处理者链传递，直到被某个处理器处理。它的核心思想是「解耦发送者和接收者」，是 Spring 框架中 Filter、Interceptor、AOP 等功能的基础。

---

## 一、核心思想

```
责任链模式结构：

  请求 ──→ Handler1 ──→ Handler2 ──→ Handler3 ──→ 结束
              ↓             ↓             ↓
           处理/拒绝      处理/拒绝      处理/拒绝

核心：每个处理器只知道自己的下一个处理器
     请求从链头传到链尾，直到被处理
     任何一个处理器处理后，链就停止传递
```

### 生活类比

```
医院挂号 → 分诊台 → 专科医生 → 专家会诊 → 出院

每个环节都在自己的职责范围内处理
无法处理就交给下一个环节
不需要病人自己去找具体科室
```

---

## 二、模式结构

```java
// 抽象处理器
public abstract class Handler {
    protected Handler next;  // 下一个处理器

    public void setNext(Handler next) {
        this.next = next;
    }

    // 模板方法：定义处理流程
    public final void handle(Request request) {
        if (canHandle(request)) {
            doHandle(request);
        } else if (next != null) {
            next.handle(request);
        } else {
            // 没有处理器处理
            onUnhandled(request);
        }
    }

    // 子类实现：判断能否处理
    protected abstract boolean canHandle(Request request);

    // 子类实现：实际处理逻辑
    protected abstract void doHandle(Request request);

    protected void onUnhandled(Request request) {
        throw new UnsupportedOperationException("No handler for: " + request);
    }
}

// 具体处理器 A
public class HandlerA extends Handler {
    @Override
    protected boolean canHandle(Request request) {
        return request.getType() == Request.Type.A; // 只处理 A 类请求
    }

    @Override
    protected void doHandle(Request request) {
        System.out.println("HandlerA 处理了: " + request);
        // 处理完成后可选继续传递给下一个
        // if (next != null) next.handle(request);
    }
}

// 具体处理器 B
public class HandlerB extends Handler {
    @Override
    protected boolean canHandle(Request request) {
        return request.getType() == Request.Type.B;
    }

    @Override
    protected void doHandle(Request request) {
        System.out.println("HandlerB 处理了: " + request);
    }
}
```

---

## 三、Spring 中的责任链

### 1. FilterChain（Servlet 过滤器链）

```java
// Filter 接口就是责任链中的 Handler
public interface Filter {
    void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException;
}

// FilterChain 实现：维护 Filter 列表，按序调用
public interface FilterChain {
    void doFilter(ServletRequest request, ServletResponse response) throws IOException, ServletException;
}

// Spring Security 的过滤器链示例
// DelegatingFilterProxy → SecurityFilterChain → FilterChainProxy → 各个安全过滤器

@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .addFilterBefore(new CsrfFilter(), BasicAuthenticationFilter.class)
            .addFilterBefore(new SessionFixationFilter(), BasicAuthenticationFilter.class)
            .addFilterBefore(new HeaderWriterFilter(), BasicAuthenticationFilter.class)
            .addFilterBefore(new LogoutFilter(), BasicAuthenticationFilter.class)
            .addFilterBefore(new UsernamePasswordAuthenticationFilter(), LogoutFilter.class)
            .addFilterAfter(new RememberMeFilter(), UsernamePasswordAuthenticationFilter.class)
            .addFilterAfter(new SessionManagementFilter(), RememberMeFilter.class);
        return http.build();
    }
}
```

### 2. HandlerInterceptorChain（Spring MVC 拦截器链）

```java
// HandlerInterceptor 接口
public interface HandlerInterceptor {
    // 目标方法执行前调用，返回 false = 阻止后续执行
    default boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) throws Exception {
        return true;
    }

    // 目标方法执行后调用（异常时不会调用）
    default void postHandle(HttpServletRequest request, HttpServletResponse response,
                           Object handler, @Nullable ModelAndView modelAndView) throws Exception {
    }

    // 请求完成后调用（始终调用，用于清理资源）
    default void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                 Object handler, @Nullable Exception ex) throws Exception {
    }
}

// DispatcherServlet 中的调用流程
public class DispatcherServlet {
    protected void doDispatch(HttpServletRequest request, HttpServletResponse response) {
        HandlerExecutionChain mappedHandler = getHandler(request);
        HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());

        // 责任链执行顺序：
        // preHandle → Controller → postHandle → afterCompletion

        if (!mappedHandler.applyPreHandle(request, response)) return;

        mv = ha.handle(processedRequest, response, mappedHandler.getHandler());

        mappedHandler.applyPostHandle(request, response, mv);

        // 渲染视图...

        mappedHandler.triggerAfterCompletion(request, response, null);
    }
}
```

### 3. MyBatis 插件链

```java
// MyBatis 的插件机制也是责任链
@Intercepts({
    @Signature(type = Executor.class, method = "query",
               args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class}),
    @Signature(type = Executor.class, method = "update",
               args = {MappedStatement.class, Object.class})
})
public class MyPlugin implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        // 在这里添加逻辑：分页、SQL 拦截、数据脱敏...
        Object result = invocation.proceed(); // 继续调用下一个插件
        return result;
    }
}

// 多个插件按顺序形成责任链
// Plugin1 → Plugin2 → Plugin3 → 实际 Executor 方法 → Plugin3 → Plugin2 → Plugin1
```

---

## 四、实际业务场景

### 场景一：登录校验链

```java
// 校验项接口
public interface AuthCheck {
    boolean check(LoginRequest request);
    default boolean checkNext(LoginRequest request, AuthCheck next) {
        return next == null || next.check(request);
    }
}

// 校验器实现
@Component
public class CaptchaCheck implements AuthCheck {
    @Override
    public boolean check(LoginRequest request) {
        if (StringUtils.isBlank(request.getCaptchaToken())) {
            throw new BizException("请先完成验证码");
        }
        return checkNext(request, getNext());
    }
}

@Component
public class BlacklistCheck implements AuthCheck {
    @Override
    public boolean check(LoginRequest request) {
        if (blacklistService.isBlackIp(request.getIp())) {
            throw new BizException("当前 IP 已被禁用");
        }
        return checkNext(request, getNext());
    }
}

@Component
public class RateLimitCheck implements AuthCheck {
    @Override
    public boolean check(LoginRequest request) {
        String key = "login:rate:" + request.getIp();
        Long count = redisTemplate.opsForValue().increment(key);
        if (count != null && count > 10) {
            throw new BizException("登录过于频繁，请稍后再试");
        }
        redisTemplate.expire(key, 1, TimeUnit.MINUTES);
        return checkNext(request, getNext());
    }
}

// 责任链组装
@Service
public class AuthChainFactory {
    @Autowired private CaptchaCheck captchaCheck;
    @Autowired private BlacklistCheck blacklistCheck;
    @Autowired private RateLimitCheck rateLimitCheck;

    public AuthCheck buildChain() {
        captchaCheck.setNext(blacklistCheck);
        blacklistCheck.setNext(rateLimitCheck);
        return captchaCheck;
    }
}

// 使用
@Service
public class LoginService {
    @Autowired private AuthChainFactory chainFactory;

    public void login(LoginRequest request) {
        chainFactory.buildChain().check(request);
        // 通过所有校验后继续登录逻辑...
    }
}
```

### 场景二：日志链路追踪

```java
// 日志上下文传递
public class TraceHandler {
    public void handle(RequestContext ctx) {
        String traceId = ctx.getTraceId();
        if (traceId == null) {
            traceId = UUID.randomUUID().toString();
            ctx.setTraceId(traceId);
        }
        ctx.addLog("处理开始");
        // 传递给下一个处理器
        next(ctx);
        ctx.addLog("处理完成");
    }
}
```

### 场景三：审批流程

```java
// 审批处理器
public abstract class Approver {
    protected Approver next;

    public void setNext(Approver next) {
        this.next = next;
    }

    public final void approve(LeaveRequest request) {
        if (canApprove(request)) {
            doApprove(request);
        }
        if (next != null) {
            next.approve(request);
        }
    }

    protected abstract boolean canApprove(LeaveRequest request);
    protected abstract void doApprove(LeaveRequest request);
}

// 组长审批
@Component
public class TeamLeaderApprover extends Approver {
    @Override
    protected boolean canApprove(LeaveRequest request) {
        return request.getDays() <= 3; // 3 天以内组长审批
    }

    @Override
    protected void doApprove(LeaveRequest request) {
        request.approve(this.getClass().getSimpleName());
    }
}

// 经理审批
@Component
public class ManagerApprover extends Approver {
    @Override
    protected boolean canApprove(LeaveRequest request) {
        return request.getDays() <= 7; // 7 天以内经理审批
    }

    @Override
    protected void doApprove(LeaveRequest request) {
        request.approve(this.getClass().getSimpleName());
    }
}
```

---

## 五、责任链 vs 策略 vs 装饰器

| 维度 | 责任链 | 策略模式 | 装饰器 |
|------|--------|---------|--------|
| **目的** | 请求在链中传递，被第一个匹配的处理器处理 | 替换算法/策略，不传递 | 给对象动态添加职责 |
| **选择方式** | 链中每个处理器自己判断是否处理 | 外部选择具体策略 | 层层包装，叠加功能 |
| **链结构** | 链状，请求依次向后传 | 无链，策略独立 | 层层嵌套，递归调用 |
| **终止条件** | 某个处理器处理后停止 | 选择即执行，无停止问题 | 所有装饰器调用完 |
| **适用场景** | 多条件校验、审批流、过滤器链 | 算法替换、支付方式选择 | IO 流增强、日志/缓存增强 |

```
责任链：
  请求 ──→ Validator1 ──→ Validator2 ──→ Validator3
            ↓              ↓              ↓
          处理/通过       通过/拒绝       通过/拒绝
          （停止）


策略模式：
  请求 ──→ [StrategyA / StrategyB / StrategyC]
           由外部根据情况选择其中一个执行

装饰器：
  client ──→ Decorator3 ──→ Decorator2 ──→ Decorator1 ──→ RealComponent
              ↓              ↓              ↓              ↓
            增强3          增强2          增强1          原始功能
           （层层叠加）    （递归调用）   （递归调用）    （最终执行）
```

---

## 六、优缺点分析

### 优点

- **解耦**：发送者和接收者解耦，发送者不需要知道谁来处理
- **可扩展**：新增处理器只需新增类，符合 OCP
- **灵活性**：可以动态调整处理器顺序和数量
- **单一职责**：每个处理器只关注自己的处理逻辑

### 缺点

- **性能开销**：请求可能遍历整个链，性能敏感场景注意
- **调试困难**：链较长时，难以追踪哪个处理器处理了请求
- **请求未被处理**：如果链配置不当，请求可能无人处理

---

## 七、高频面试题

**Q1: 责任链模式和策略模式有什么区别？**
> 核心区别在于「选择方式」：策略模式由外部根据条件选择一个策略执行，多个策略互斥，一次只选一个；责任链模式请求在链中传递，每个处理器自己判断是否处理，请求可能被多个处理器处理或被第一个匹配的处理器处理后就停止。策略模式解决「用哪个算法」，责任链解决「经过哪些处理器」。

**Q2: Spring MVC 中 Interceptor 和 Filter 的区别是什么？**
> 两者都是责任链的应用，但层级不同。Filter 是在 Servlet 容器层，处理所有请求（包括静态资源）；Interceptor 是 Spring MVC 层，只处理进入 DispatcherServlet 的请求。Filter 依赖 Servlet API，Interceptor 依赖 Spring 容器。执行顺序：Filter → Interceptor → Controller。

**Q3: 责任链模式如何实现中途停止？**
> 两种方式：① 在处理器中处理后不调用 `next.handle()` 停止传递；② 在处理器中抛出一个特定异常（如业务异常），后续处理器捕获到这个异常后停止。Spring Security 就是用异常机制中断 Filter 链的（FilterSecurityInterceptor 抛异常）。

**Q4: MyBatis 插件链是如何工作的？**
> MyBatis 用 JDK 动态代理包装被拦截对象，每个插件都是一层代理。多个插件按配置顺序形成嵌套代理链：`target = Plugin.wrap(target, plugin1)` → `target = Plugin.wrap(target, plugin2)` → 执行时从外到内递归调用：`plugin2.intercept(() → plugin1.intercept(() → realMethod()))`。
