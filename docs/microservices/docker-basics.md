# Docker 基础

> 容器化技术

## 🎯 面试重点

- Docker 核心概念
- 常用命令

## 📖 核心概念

```java
/**
 * Docker 概念
 */
public class DockerConcepts {
    // 镜像（Image）
    /*
     * 只读模板，包含运行环境
     */
    
    // 容器（Container）
    /*
     * 镜像的运行实例
     */
    
    // 仓库（Repository）
    /*
     * 存储镜像
     */
}
```

## 📖 常用命令

```java
/**
 * 常用命令
 */
public class DockerCommands {
    // 镜像
    /*
     * docker pull nginx
     * docker images
     * docker rmi nginx
     */
    
    // 容器
    /*
     * docker run -d -p 80:80 nginx
     * docker ps
     * docker stop container_id
     * docker logs container_id
     */
}
```

## 📖 面试真题

### Q1: Docker 和虚拟机的区别？

**答：** Docker 共享内核，启动快，占用小。

---

**⭐ 重点：Docker 是容器化的基础**