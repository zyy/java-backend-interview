---
layout: default
title: Kubernetes 核心概念
---
# Kubernetes 核心概念

> 容器编排平台

## 🎯 面试重点

- Kubernetes 架构
- 核心资源

## 📖 架构

```java
/**
 * K8s 架构
 */
public class K8sArchitecture {
    // Master 节点
    /*
     * API Server：入口
     * Scheduler：调度
     * Controller Manager：控制
     * etcd：存储
     */
    
    // Worker 节点
    /*
     * kubelet：代理
     * kube-proxy：网络
     * Container Runtime：容器运行时
     */
}
```

## 📖 核心资源

```java
/**
 * 核心资源
 */
public class K8sResources {
    // Pod
    /*
     * 最小部署单元
     */
    
    // Service
    /*
     * 服务发现和负载均衡
     */
    
    // Deployment
    /*
     * 无状态应用部署
     */
    
    // StatefulSet
    /*
     * 有状态应用部署
     */
    
    // ConfigMap / Secret
    /*
     * 配置管理
     */
}
```

## 📖 面试真题

### Q1: K8s 的作用？

**答：** 容器编排、自动调度、弹性伸缩。

---

**⭐ 重点：K8s 是云原生的核心**