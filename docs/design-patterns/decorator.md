# 装饰器模式

> 动态扩展对象功能

## 🎯 面试重点

- 装饰器模式结构
- 与代理模式区别

## 📖 实现

```java
/**
 * 装饰器模式
 */
public class DecoratorPattern {
    public interface Component { void operation(); }
    
    public static class ConcreteComponent implements Component {
        public void operation() { System.out.println("base"); }
    }
    
    public static abstract class Decorator implements Component {
        protected Component component;
        public Decorator(Component c) { this.component = c; }
    }
    
    public static class ConcreteDecorator extends Decorator {
        public ConcreteDecorator(Component c) { super(c); }
        public void operation() {
            System.out.println("before");
            component.operation();
            System.out.println("after");
        }
    }
}
```

## 📖 面试真题

### Q1: 装饰器和代理的区别？

**答：** 装饰器强调增强功能，代理强调控制访问。

---

**⭐ 重点：Java IO 使用装饰器模式**