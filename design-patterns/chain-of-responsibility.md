# 责任链模式

> 请求链式处理

## 🎯 面试重点

- 责任链结构
- 使用场景

## 📖 实现

```java
/**
 * 责任链模式
 */
public class ChainOfResponsibility {
    public abstract static class Handler {
        protected Handler next;
        
        public Handler setNext(Handler next) {
            this.next = next;
            return next;
        }
        
        public abstract void handle(String request);
    }
    
    public static class HandlerA extends Handler {
        public void handle(String request) {
            System.out.println("A: " + request);
            if (next != null) next.handle(request);
        }
    }
    
    public static class HandlerB extends Handler {
        public void handle(String request) {
            System.out.println("B: " + request);
            if (next != null) next.handle(request);
        }
    }
    
    // 使用
    // Handler chain = new HandlerA();
    // chain.setNext(new HandlerB());
    // chain.handle("test");
}
```

## 📖 面试真题

### Q1: 责任链的应用场景？

**答：** 过滤器、拦截器、审批流程。

---

**⭐ 重点：Servlet Filter、Spring Interceptor 使用责任链**