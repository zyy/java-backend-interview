---
layout: default
title: Kubernetes 核心概念与实战
---

# Kubernetes 核心概念与实战

## 目录
1. [工作负载资源对比](#工作负载资源对比)
2. [Service 服务暴露](#service-服务暴露)
3. [Ingress 域名路由](#ingress-域名路由)
4. [配置管理](#配置管理)
5. [持久化存储](#持久化存储)
6. [Helm 包管理](#helm-包管理)
7. [自动扩缩容 HPA](#自动扩缩容-hpa)
8. [滚动更新与回滚](#滚动更新与回滚)
9. [资源限制与配额](#资源限制与配额)
10. [命名空间隔离](#命名空间隔离)
11. [面试题精选](#面试题精选)

---

## 工作负载资源对比

### Pod

Pod 是 Kubernetes 中最小的可部署单元，一个 Pod 可以包含一个或多个紧密耦合的容器，它们共享网络命名空间和存储卷。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.20
    ports:
    - containerPort: 80
```

**特点：**
- Pod 是临时性的，控制器负责维护其生命周期
- 直接创建 Pod 不推荐，应使用控制器管理
- 同一 Pod 内的容器共享 IP 和端口空间

### Deployment

Deployment 是最常用的工作负载控制器，用于管理无状态应用，支持滚动更新和回滚。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
```

**核心特性：**
- **声明式更新**：通过修改 spec 触发滚动更新
- **版本控制**：保留历史版本用于回滚
- **自愈能力**：Pod 故障自动重新调度
- **扩缩容**：支持手动和自动扩缩容

### StatefulSet

StatefulSet 用于管理有状态应用，如数据库、消息队列等，提供稳定的网络标识和持久存储。

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-sts
spec:
  serviceName: mysql-headless
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

**与 Deployment 的关键区别：**

| 特性 | Deployment | StatefulSet |
|------|------------|-------------|
| 网络标识 | 随机 Pod 名 | 固定序号 Pod 名 (pod-0, pod-1) |
| 存储 | 共享或临时 | 每个 Pod 独立 PVC |
| 启动顺序 | 并行 | 有序启动/停止 |
| 使用场景 | Web 应用、API | 数据库、消息队列 |

### Job 和 CronJob

**Job** 用于执行一次性任务，确保任务成功完成指定次数。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 1
  parallelism: 1
  template:
    spec:
      containers:
      - name: migrate
        image: migrate-tool:latest
        command: ["./migrate.sh"]
      restartPolicy: OnFailure
```

**CronJob** 用于定时执行任务，类似于 Linux 的 crontab。

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"  # 每天凌晨2点执行
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tool:latest
            command: ["./backup.sh"]
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

---

## Service 服务暴露

Service 是 Kubernetes 中用于暴露 Pod 访问入口的抽象层，通过标签选择器将流量路由到后端 Pod。

### ClusterIP（集群内部访问）

默认类型，仅在集群内部暴露服务，适合微服务间通信。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
```

**特点：**
- 分配集群内部虚拟 IP
- 仅集群内可访问
- 支持负载均衡到多个 Pod

### NodePort（节点端口暴露）

在每个节点上开放一个端口，外部可通过 `<NodeIP>:<NodePort>` 访问服务。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # 范围 30000-32767
```

**使用场景：**
- 开发测试环境快速暴露服务
- 没有负载均衡器时的临时方案

### LoadBalancer（云厂商负载均衡）

在云环境中自动创建外部负载均衡器，分配公网 IP。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 443
    targetPort: 8080
```

**特点：**
- 云厂商自动创建负载均衡器
- 分配公网 IP 或域名
- 适合生产环境直接暴露服务

### 三种类型对比

| 类型 | 访问范围 | 适用场景 | 性能 |
|------|----------|----------|------|
| ClusterIP | 集群内部 | 微服务间通信 | 高 |
| NodePort | 节点 IP + 端口 | 测试/无 LB 环境 | 中 |
| LoadBalancer | 公网 | 生产环境暴露 | 依赖云厂商 |

---

## Ingress 域名路由

Ingress 是 Kubernetes 的 HTTP/HTTPS 路由规则集合，配合 Ingress Controller 实现七层负载均衡。

### 基础配置

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-v1
            port:
              number: 8080
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: api-v2
            port:
              number: 8080
```

### HTTPS 配置

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - secure.example.com
    secretName: tls-secret  # 包含证书和私钥的 Secret
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: secure-app
            port:
              number: 443
```

**创建 TLS Secret：**

```bash
kubectl create secret tls tls-secret \
  --cert=server.crt \
  --key=server.key
```

### 高级路由规则

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: advanced-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  rules:
  - host: shop.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
      - path: /static
        pathType: Prefix
        backend:
          service:
            name: static-service
            port:
              number: 80
```

---

## 配置管理

### ConfigMap

ConfigMap 用于存储非敏感的配置数据，如环境变量、配置文件等。

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # 键值对形式
  DATABASE_URL: "jdbc:mysql://mysql:3306/mydb"
  LOG_LEVEL: "INFO"
  
  # 文件形式
  application.properties: |
    server.port=8080
    spring.profiles.active=prod
```

**使用方式：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        # 从 ConfigMap 注入环境变量
        - name: DB_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_URL
        envFrom:
        # 注入所有键值对
        - configMapRef:
            name: app-config
        volumeMounts:
        # 挂载为文件
        - name: config-vol
          mountPath: /config
      volumes:
      - name: config-vol
        configMap:
          name: app-config
```

### Secret

Secret 用于存储敏感数据，如密码、Token、证书等，数据以 Base64 编码存储。

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  username: admin
  password: "P@ssw0rd123"
```

**常用 Secret 类型：**

| 类型 | 用途 |
|------|------|
| Opaque | 通用敏感数据 |
| kubernetes.io/tls | TLS 证书和私钥 |
| kubernetes.io/dockerconfigjson | 镜像仓库认证 |
| kubernetes.io/basic-auth | HTTP 基础认证 |

```yaml
# Docker 镜像仓库认证
apiVersion: v1
kind: Secret
metadata:
  name: regcred
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

---

## 持久化存储

### PV（PersistentVolume）

PV 是集群中的存储资源，由管理员预先配置或动态供应。

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  nfs:
    server: 192.168.1.100
    path: /exports/data
```

**访问模式：**

| 模式 | 说明 |
|------|------|
| ReadWriteOnce (RWO) | 单节点读写 |
| ReadOnlyMany (ROX) | 多节点只读 |
| ReadWriteMany (RWX) | 多节点读写 |
| ReadWriteOncePod (RWOP) | 单 Pod 读写（1.22+）|

### PVC（PersistentVolumeClaim）

PVC 是用户对存储资源的申请，Kubernetes 会自动绑定合适的 PV。

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

**在 Pod 中使用：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  template:
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-data
        persistentVolumeClaim:
          claimName: data-pvc
```

### StorageClass 动态供应

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
reclaimPolicy: Delete
allowVolumeExpansion: true
```

---

## Helm 包管理

Helm 是 Kubernetes 的包管理工具，使用 Chart 定义、安装和升级应用。

### Chart 结构

```
mychart/
├── Chart.yaml          # Chart 元数据
├── values.yaml         # 默认配置值
├── templates/          # 模板文件
│   ├── deployment.yaml
│   ├── service.yaml
│   └── _helpers.tpl    # 辅助模板
└── charts/             # 依赖 Chart
```

### 常用命令

```bash
# 添加仓库
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 搜索 Chart
helm search repo mysql

# 安装 Chart
helm install my-mysql bitnami/mysql --set auth.rootPassword=secret

# 查看已安装
helm list

# 升级
helm upgrade my-mysql bitnami/mysql --set replicaCount=3

# 回滚
helm rollback my-mysql 1

# 卸载
helm uninstall my-mysql
```

### 自定义 Chart 示例

```yaml
# Chart.yaml
apiVersion: v2
name: myapp
description: A Helm chart for my application
type: application
version: 1.0.0
appVersion: "1.0"
```

```yaml
# values.yaml
replicaCount: 2
image:
  repository: myapp
  tag: latest
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 8080
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

---

## 自动扩缩容 HPA

Horizontal Pod Autoscaler（HPA）根据 CPU、内存或自定义指标自动调整 Pod 副本数。

### 基于 CPU 的 HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 基于自定义指标的 HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: custom-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

---

## 滚动更新与回滚

### 滚动更新策略

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # 更新时可超出的最大 Pod 数
      maxUnavailable: 25%  # 更新时可不可用的最大 Pod 数
  template:
    spec:
      containers:
      - name: web
        image: web:v2
```

**策略说明：**

| 参数 | 说明 |
|------|------|
| maxSurge | 更新过程中可创建的额外 Pod 数量或百分比 |
| maxUnavailable | 更新过程中可容忍的不可用 Pod 数量或百分比 |

### 执行更新与回滚

```bash
# 更新镜像
kubectl set image deployment/web-app web=web:v3

# 查看更新状态
kubectl rollout status deployment/web-app

# 查看历史版本
kubectl rollout history deployment/web-app

# 回滚到上一个版本
kubectl rollout undo deployment/web-app

# 回滚到指定版本
kubectl rollout undo deployment/web-app --to-revision=2

# 暂停更新
kubectl rollout pause deployment/web-app

# 恢复更新
kubectl rollout resume deployment/web-app
```

---

## 资源限制与配额

### 容器资源限制

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-demo
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
        resources:
          requests:
            cpu: "100m"        # 100 millicores = 0.1 CPU
            memory: "128Mi"    # 128 MiB
          limits:
            cpu: "500m"        # 0.5 CPU
            memory: "512Mi"    # 512 MiB
```

**资源单位说明：**

| 资源 | 单位 | 示例 |
|------|------|------|
| CPU | millicores | 100m = 0.1 CPU |
| CPU | cores | 1 = 1 个 CPU 核心 |
| 内存 | Mi/Gi | 512Mi, 2Gi |
| 内存 | M/G | 512M, 2G (1000-based) |

### LimitRange

为命名空间内的容器设置默认资源限制。

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
  - max:
      cpu: "2"
      memory: "4Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
```

### ResourceQuota

限制命名空间的资源总量。

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-a
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
```

---

## 命名空间隔离

命名空间（Namespace）用于在集群内划分虚拟隔离环境，适合多团队或多环境场景。

### 常用命名空间策略

```bash
# 创建命名空间
kubectl create namespace production
kubectl create namespace development

# 查看命名空间
kubectl get namespaces

# 在指定命名空间操作
kubectl get pods -n production
kubectl apply -f app.yaml -n development
```

### 网络隔离（NetworkPolicy）

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### RBAC 权限控制

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: development
rules:
- apiGroups: ["", "apps"]
  resources: ["pods", "deployments", "services"]
  verbs: ["get", "list", "create", "update", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

---

## 面试题精选

### 1. Pod、Deployment、StatefulSet 有什么区别？分别在什么场景下使用？

**答案要点：**

| 资源类型 | 特点 | 适用场景 |
|----------|------|----------|
| Pod | 最小部署单元，无自愈能力 | 临时调试，学习测试 |
| Deployment | 无状态，随机名称，共享存储 | Web 应用、API 服务 |
| StatefulSet | 有序部署，固定网络标识，独立存储 | 数据库、消息队列、有状态服务 |

**关键区别：**
- StatefulSet 提供稳定的网络标识（pod-0, pod-1）和持久化存储
- Deployment 适合水平扩展的无状态应用
- StatefulSet 的 Pod 按序号有序启动和停止

### 2. Service 的三种类型 ClusterIP、NodePort、LoadBalancer 有什么区别？

**答案要点：**

- **ClusterIP**：默认类型，分配集群内部虚拟 IP，仅集群内可访问，适合微服务间通信
- **NodePort**：在每个节点上开放指定端口（30000-32767），外部通过 `<NodeIP>:<NodePort>` 访问
- **LoadBalancer**：在云环境中自动创建外部负载均衡器，分配公网 IP，适合生产环境

**选择建议：**
- 内部服务 → ClusterIP
- 开发测试 → NodePort
- 生产公网暴露 → LoadBalancer 或 Ingress

### 3. ConfigMap 和 Secret 有什么区别？如何安全地管理敏感配置？

**答案要点：**

**区别：**
- ConfigMap 存储非敏感配置，明文存储
- Secret 存储敏感数据，Base64 编码（非加密），可配置加密 at rest

**安全管理实践：**
1. 启用 etcd 加密（EncryptionConfiguration）
2. 使用外部密钥管理系统（Vault、AWS KMS）
3. 限制 Secret 的 RBAC 访问权限
4. 避免将 Secret 提交到 Git，使用 Sealed Secrets 或 External Secrets Operator
5. 定期轮换 Secret

### 4. HPA 的工作原理是什么？除了 CPU/内存，还支持哪些扩缩容指标？

**答案要点：**

**工作原理：**
1. HPA Controller 定期（默认 15s）采集指标
2. 计算期望副本数：`desiredReplicas = ceil[currentReplicas * (currentMetricValue / targetMetricValue)]`
3. 调整 Deployment 的副本数

**支持的指标类型：**
- Resource：CPU、内存利用率
- Pods：自定义 Pod 级指标（如 QPS、连接数）
- Object：Kubernetes 对象指标（如 Ingress 请求速率）
- External：外部系统指标（如消息队列长度）

### 5. 如何设计一个高可用的 Kubernetes 应用？需要考虑哪些方面？

**答案要点：**

**1. 应用层面：**
- 使用 Deployment 管理多副本 Pod
- 配置健康检查（livenessProbe、readinessProbe）
- 实现优雅关闭（preStop 钩子）

**2. 资源层面：**
- 设置合理的资源请求和限制
- 使用 PodDisruptionBudget 保证最小可用副本
- 配置反亲和性避免单点故障

**3. 存储层面：**
- 有状态应用使用 StatefulSet + PVC
- 配置存储的多可用区冗余

**4. 网络层面：**
- 使用 Service 做服务发现和负载均衡
- 配置 NetworkPolicy 实现网络隔离
- 生产环境使用 Ingress + HTTPS

**5. 运维层面：**
- 配置 HPA 自动扩缩容
- 设置监控告警（Prometheus + Grafana）
- 配置日志收集（ELK 或 Loki）
