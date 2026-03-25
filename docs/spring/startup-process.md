---
layout: default
title: Spring Boot 启动流程
---
# Spring Boot 启动流程

> Spring Boot 应用启动过程

## 🎯 面试重点

- 启动流程的主要步骤
- 事件监听机制

## 📖 启动流程

### 主要步骤

```java
/**
 * Spring Boot 启动流程
 */
public class StartupProcess {
    // 1. SpringApplication 实例化
    /*
     * - 加载 ApplicationContextInitializer
     * - 加载 ApplicationListener
     * - 推断主类
     */
    
    // 2. run() 方法
    /*
     * 1. StopWatch 计时开始
     * 2. 创建并配置 Environment
     * 3. 打印 Banner
     * 4. 创建 ApplicationContext
     * 5. 准备 ApplicationContext（Bean 加载）
     * 6. 刷新 ApplicationContext
     * 7. 执行 ApplicationRunner/CommandLineRunner
     * 8. 回调所有 Listener
     */
}
```

### 关键阶段

```java
/**
 * 关键阶段
 */
public class KeyPhases {
    // Environment 准备
    /*
     * - 加载 application.yml/properties
     * - 处理 profile
     * - 属性覆盖
     */
    
    // ApplicationContext 准备
    /*
     * - BeanDefinition 加载
     * - BeanFactory 后置处理
     * - Bean 初始化
     */
    
    // 刷新
    /*
     * - Bean 实例化
     * - 依赖注入
     * - 初始化
     */
}
```

## 📖 面试真题

### Q1: Spring Boot 启动过程？

**答：** 创建 ApplicationContext → 加载配置 → 实例化 Bean → 依赖注入 → 初始化。

---

**⭐ 重点：理解启动流程有助于排查问题**