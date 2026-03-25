---
layout: default
title: 建造者模式
---
# 建造者模式

> 复杂对象的构建

## 🎯 面试重点

- 建造者模式结构
- 使用场景

## 📖 实现

```java
/**
 * 建造者模式
 */
public class BuilderPattern {
    public static class User {
        private String name;
        private int age;
        private String email;
        
        private User(Builder builder) {
            this.name = builder.name;
            this.age = builder.age;
            this.email = builder.email;
        }
        
        public static class Builder {
            private String name;
            private int age;
            private String email;
            
            public Builder name(String name) {
                this.name = name;
                return this;
            }
            
            public Builder age(int age) {
                this.age = age;
                return this;
            }
            
            public Builder email(String email) {
                this.email = email;
                return this;
            }
            
            public User build() {
                return new User(this);
            }
        }
    }
    
    // 使用
    // User user = new User.Builder()
    //     .name("Tom")
    //     .age(20)
    //     .build();
}
```

## 📖 面试真题

### Q1: 建造者模式的优点？

**答：** 分步构建、参数可选、链式调用。

---

**⭐ 重点：StringBuilder、Lombok @Builder 都是建造者模式**