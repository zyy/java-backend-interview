# 适配器模式

> 接口转换

## 🎯 面试重点

- 适配器模式结构
- 使用场景

## 📖 实现

```java
/**
 * 适配器模式
 */
public class AdapterPattern {
    // 目标接口
    public interface Target { void request(); }
    
    // 被适配者
    public static class Adaptee {
        public void specificRequest() { System.out.println("specific"); }
    }
    
    // 适配器
    public static class Adapter implements Target {
        private Adaptee adaptee;
        public Adapter(Adaptee adaptee) { this.adaptee = adaptee; }
        public void request() { adaptee.specificRequest(); }
    }
}
```

## 📖 面试真题

### Q1: 适配器模式的优点？

**答：** 复用现有类、解耦、符合开闭原则。

---

**⭐ 重点：Arrays.asList() 是适配器模式**