---
layout: default
title: Docker 容器化基础实战
---
# Docker 容器化基础实战

## 🎯 面试题：Docker 和虚拟机有什么区别？Docker 的底层原理是什么？

> Docker 是云原生和微服务的基础设施。面试中常考容器与虚拟机的区别、Dockerfile 编写、Docker Compose 编排等。

---

## 一、Docker vs 虚拟机

```
┌──────────────────────────────────────────────────────────┐
│                     虚拟机架构                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │  App1   │  │  App2   │  │  App3   │                │
│  ├─────────┤  ├─────────┤  ├─────────┤                │
│  │ GuestOS │  │ GuestOS │  │ GuestOS │                │
│  ├─────────┤  ├─────────┤  ├─────────┤                │
│  │ Hypervisor │  │         │         │                │
│  ├─────────────────────────────────────────────────┤    │
│  │              Host OS (Linux/Windows)             │    │
│  └─────────────────────────────────────────────────┘    │
│  缺点：每个虚拟机都要装 Guest OS，体积大（GB级），启动慢（分钟级）│
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     Docker 容器架构                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │  App1   │  │  App2   │  │  App3   │                │
│  ├─────────┤  ├─────────┤  ├─────────┤                │
│  │  libs   │  │  libs   │  │  libs   │                │
│  ├─────────┤  ├─────────┤  ├─────────┤                │
│  │ Container│  │ Container│  │ Container│                │
│  └─────────────────────────────────────────────────┘    │
│  │              Docker Engine（共享宿主机内核）         │    │
│  ├─────────────────────────────────────────────────┤    │
│  │              Host OS (Linux)                     │    │
│  └─────────────────────────────────────────────────┘    │
│  优点：共享内核，体积小（MB级），启动快（秒级）            │
└──────────────────────────────────────────────────────────┘
```

| 维度 | Docker | 虚拟机 |
|------|--------|--------|
| 启动速度 | 秒级 | 分钟级 |
| 体积 | MB 级 | GB 级 |
| 隔离性 | 进程级隔离 | 硬件级隔离（更强） |
| 性能开销 | ~2-3% | ~10-15% |
| 资源利用率 | 高 | 中 |

---

## 二、Docker 核心概念

```
镜像（Image）：只读模板，类似于 Java 的类
容器（Container）：镜像的实例，类似于 Java 的对象
仓库（Registry）：存储和分发镜像的地方（Docker Hub、私有仓库）

关系：
  Dockerfile → 镜像 → 容器（多个容器）
                ↑
             Docker Registry（Harbor/阿里云ACR）
```

---

## 三、Dockerfile 编写

```dockerfile
# 多阶段构建（减少最终镜像体积）
# 阶段一：构建
FROM maven:3.8-openjdk-8 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline       # 下载依赖（利用缓存）
COPY src ./src
RUN mvn package -DskipTests        # 构建 jar

# 阶段二：运行（只复制 jar，不包含 Maven）
FROM openjdk:8-jre-slim
WORKDIR /app
COPY --from=builder /app/target/myapp.jar app.jar

# 非 root 用户运行（安全最佳实践）
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# 环境变量
ENV JAVA_OPTS="-Xmx512m"

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### 最佳实践

```dockerfile
# ❌ 错误：每次代码修改都重新下载依赖
COPY . .
RUN mvn package

# ✅ 正确：利用 Docker 层缓存，先复制依赖再复制代码
COPY pom.xml .
RUN mvn dependency:go-offline       # 这一层可以被缓存
COPY src ./src
RUN mvn package

# ❌ 错误：Dockerfile 放项目根目录
# ✅ 正确：Dockerfile 放在项目子目录
```

---

## 四、Docker Compose 编排

```yaml
# docker-compose.yml
version: "3.8"
services:
  # 微服务
  order-service:
    build: ./order-service
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - NACOS_SERVER_ADDR=nacos:8848
    depends_on:
      - nacos
      - mysql
      - redis
    networks:
      - backend

  user-service:
    build: ./user-service
    ports:
      - "8081:8080"
    depends_on:
      - nacos
      - mysql
    networks:
      - backend

  # 基础设施
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: order_db
    volumes:
      - mysql-data:/var/lib/mysql
    ports:
      - "3306:3306"
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass redis123
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - backend

  nacos:
    image: nacos/nacos-server:v2.2.0
    environment:
      MODE: standalone
    ports:
      - "8848:8848"
    networks:
      - backend

volumes:
  mysql-data:
  redis-data:

networks:
  backend:
    driver: bridge
```

---

## 五、数据持久化与网络

```yaml
# 数据卷（Volume）
volumes:
  mysql-data:/var/lib/mysql
  # 匿名卷：容器删除后自动删除
  # 具名卷：容器删除后保留
  # 绑定挂载：映射宿主机目录

# 网络模式
# bridge（默认）：容器间通信
# host：容器直接使用宿主机网络
# overlay：跨主机容器通信（Docker Swarm）
# none：禁用网络
```

---

## 六、高频面试题

**Q1: Docker 和虚拟机的区别？**
> 核心区别是是否需要 Guest OS。虚拟机每个实例都需要完整的操作系统（Guest OS），虚拟化硬件，占用 GB 级空间，启动分钟级。Docker 共享宿主机内核，容器是进程级隔离，占用 MB 级空间，启动秒级。Docker 隔离性弱于虚拟机（虚拟机之间完全隔离），但性能更高、资源利用率更高。

**Q2: Docker 容器的生命周期？**
> Docker 容器有 7 种状态：created（已创建但未启动）、running（运行中）、paused（暂停，CPU 冻结）、restarting（重启中）、exited（已停止）、dead（故障状态）、removing（删除中）。`docker run` 创建并启动，`docker pause` 暂停，`docker stop` 优雅停止（SIGTERM），`docker kill` 强制停止（SIGKILL）。

**Q3: Docker 如何实现容器间网络通信？**
> Docker 提供四种网络模式：bridge（默认，网桥 docker0，容器通过 NAT 通信）、host（直接用宿主机网络栈，容器和宿主机端口不冲突）、overlay（跨主机通信，用于 Docker Swarm）、none（无网络）。同 bridge 网络下的容器可以通过容器名互相通信，Docker 内置 DNS 会解析容器名。
