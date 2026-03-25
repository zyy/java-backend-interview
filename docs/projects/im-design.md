# 即时通讯系统设计

> 设计一个支持千万级用户的即时通讯系统

## 🎯 面试重点

- 消息推送架构
- 在线状态管理
- 消息可靠投递
- 系统扩展性设计

## 📖 需求分析

### 核心功能

```java
/**
 * 即时通讯系统核心功能
 */
public class IMRequirements {
    
    // 1. 基础通信
    /*
     * 一对一聊天
     * 群组聊天
     * 消息类型：文本、图片、语音、文件
     */
    
    // 2. 在线状态
    /*
     * 在线/离线状态显示
     * 最后在线时间
     * 隐身模式
     */
    
    // 3. 消息特性
    /*
     * 消息已读/未读状态
     * 消息撤回
     * 消息删除
     * 消息转发
     */
    
    // 4. 高级功能
    /*
     * 音视频通话
     * 屏幕共享
     * 消息漫游
     * 多端同步
     */
}
```

### 非功能需求

```java
/**
 * 非功能需求
 */
public class NonFunctionalRequirements {
    
    // 1. 性能指标
    /*
     * 消息延迟：< 200ms
     * 消息成功率：> 99.99%
     * 单机连接数：> 10万
     */
    
    // 2. 可用性
    /*
     * 系统可用性：99.99%
     * 故障恢复时间：< 5分钟
     * 数据持久化：消息不丢失
     */
    
    // 3. 扩展性
    /*
     * 支持水平扩展
     * 支持千万级用户
     * 支持百万级并发
     */
    
    // 4. 安全性
    /*
     * 端到端加密
     * 消息防篡改
     * 内容审核
     */
}
```

## 📖 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                       客户端 (App/Web)                        │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTPS/WebSocket
┌─────────────────────────────▼───────────────────────────────┐
│                    负载均衡器 (Nginx/LVS)                     │
└──────────────┬────────────────┬──────────────────────────────┘
               │                │
    ┌──────────▼──────┐ ┌──────▼──────────┐
    │   Gateway集群   │ │    API网关       │
    │  (WebSocket)    │ │  (HTTP REST)     │
    └──────────┬──────┘ └──────┬──────────┘
               │                │
    ┌──────────▼──────┐ ┌──────▼──────────┐
    │  消息推送服务    │ │   业务逻辑服务   │
    │  (Push Server)  │ │ (Message Service)│
    └──────────┬──────┘ └──────┬──────────┘
               │                │
    ┌──────────▼────────────────▼──────────┐
    │          消息队列 (Kafka)             │
    └─────────────────┬─────────────────────┘
                      │
    ┌─────────────────▼─────────────────────┐
    │            存储层                      │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │
    │  │  MySQL  │ │  Redis  │ │ MongoDB │ │
    │  │ (用户数据)│ │(在线状态)│ │(消息历史)│ │
    │  └─────────┘ └─────────┘ └─────────┘ │
    └───────────────────────────────────────┘
```

### 核心组件设计

```java
/**
 * 核心组件职责
 */
public class CoreComponents {
    
    // 1. 连接网关（Gateway）
    /*
     * 职责：维护WebSocket长连接
     * 特性：
     * - 无状态，可水平扩展
     * - 心跳检测，连接保活
     * - 连接认证，用户绑定
     * - 消息路由，负载均衡
     */
    
    // 2. 消息服务（Message Service）
    /*
     * 职责：处理业务逻辑
     * 功能：
     * - 消息存储
     * - 消息查询
     * - 群组管理
     * - 离线消息
     */
    
    // 3. 推送服务（Push Service）
    /*
     * 职责：消息实时推送
     * 实现：
     * - 在线推送：通过Gateway推送
     * - 离线推送：APNs/FCM推送
     * - 多端同步：多设备同时在线
     */
    
    // 4. 状态服务（Presence Service）
    /*
     * 职责：管理用户在线状态
     * 存储：
     * - Redis：在线状态，快速查询
     * - MySQL：最后在线时间，持久化
     */
}
```

## 📖 详细设计

### 1. 连接管理

```java
/**
 * WebSocket连接管理
 */
public class ConnectionManager {
    
    // 连接信息
    @Data
    public class ConnectionInfo {
        private String connectionId;    // 连接ID
        private String userId;          // 用户ID
        private String deviceId;        // 设备ID
        private String gatewayIp;       // Gateway IP
        private Long connectTime;       // 连接时间
        private Long lastHeartbeatTime; // 最后心跳时间
        private Map<String, Object> attributes; // 自定义属性
    }
    
    // 心跳机制
    public class Heartbeat {
        // 客户端每30秒发送心跳
        // 服务端60秒未收到心跳则断开连接
        // 心跳包内容：{type: "heartbeat", timestamp: 1630000000000}
    }
    
    // 连接认证
    public class Authentication {
        // 1. 客户端连接时携带Token
        // 2. Gateway验证Token有效性
        // 3. 建立userId -> connectionId映射
        // 4. 存储到Redis：user:connections:{userId}
    }
}
```

### 2. 消息投递

```java
/**
 * 消息可靠投递
 */
public class MessageDelivery {
    
    // 消息格式
    @Data
    public class Message {
        private String messageId;      // 消息ID（雪花算法）
        private String fromUserId;     // 发送者
        private String toUserId;       // 接收者（或群ID）
        private MessageType type;      // 消息类型：TEXT、IMAGE、VOICE
        private String content;        // 消息内容
        private Long timestamp;        // 时间戳
        private Map<String, Object> ext; // 扩展字段
        
        // 消息状态
        private DeliveryStatus status; // SENT、DELIVERED、READ
        private String deviceId;       // 发送设备ID
    }
    
    // 投递流程
    public class DeliveryProcess {
        /*
         * 1. 客户端A发送消息到Gateway
         * 2. Gateway转发到Message Service
         * 3. Message Service存储消息到数据库
         * 4. Message Service发布消息到Kafka
         * 5. Push Service消费消息，查询接收者在线状态
         * 6. 在线：通过对应Gateway推送
         * 7. 离线：存储离线消息，推送通知
         * 8. 接收者确认收到，更新消息状态
         */
    }
    
    // 消息确认机制
    public class AckMechanism {
        // 发送方发送消息，携带messageId
        // 接收方收到消息后返回ACK
        // 发送方未收到ACK则重发（最多3次）
        // 消息去重：根据messageId去重
    }
}
```

### 3. 在线状态管理

```java
/**
 * 用户在线状态
 */
public class PresenceService {
    
    // 状态定义
    public enum UserStatus {
        ONLINE,     // 在线
        OFFLINE,    // 离线
        AWAY,       // 离开
        BUSY,       // 忙碌
        INVISIBLE   // 隐身
    }
    
    // Redis存储设计
    public class RedisSchema {
        /*
         * Key: user:presence:{userId}
         * Value: {
         *   "status": "ONLINE",
         *   "lastSeen": 1630000000000,
         *   "device": "iPhone-123",
         *   "gateway": "10.0.0.1:8080"
         * }
         * 
         * Key: online:users
         * Type: Set
         * Value: [userId1, userId2, ...]  # 所有在线用户
         * 
         * Key: user:connections:{userId}
         * Type: Set
         * Value: [connId1, connId2, ...]  # 用户的所有连接
         */
    }
    
    // 状态同步
    public class StatusSync {
        // 用户登录：更新为ONLINE
        // 用户登出：更新为OFFLINE
        // 心跳超时：更新为OFFLINE
        // 多端在线：合并状态
        // 状态变更通知好友
    }
}
```

## 📖 关键技术实现

### 1. WebSocket网关

```java
@Component
@ServerEndpoint("/ws/{token}")
public class WebSocketGateway {
    
    // 连接建立
    @OnOpen
    public void onOpen(Session session, @PathParam("token") String token) {
        // 1. 验证Token
        UserInfo user = authService.validateToken(token);
        
        // 2. 创建连接信息
        ConnectionInfo conn = new ConnectionInfo();
        conn.setConnectionId(generateConnectionId());
        conn.setUserId(user.getId());
        conn.setDeviceId(user.getDeviceId());
        conn.setGatewayIp(getLocalIp());
        
        // 3. 存储连接信息
        connectionManager.addConnection(conn);
        redisService.addUserConnection(user.getId(), conn.getConnectionId());
        
        // 4. 更新在线状态
        presenceService.userOnline(user.getId(), conn);
        
        // 5. 同步离线消息
        offlineService.syncOfflineMessages(user.getId(), conn.getConnectionId());
    }
    
    // 接收消息
    @OnMessage
    public void onMessage(String message, Session session) {
        // 解析消息
        Message msg = JsonUtils.parse(message, Message.class);
        
        // 消息路由
        if (msg.getType() == MessageType.HEARTBEAT) {
            // 更新心跳
            connectionManager.updateHeartbeat(msg.getFromUserId());
        } else {
            // 转发到消息服务
            kafkaProducer.send("message-topic", msg);
        }
    }
    
    // 连接关闭
    @OnClose
    public void onClose(Session session) {
        // 清理连接信息
        String connectionId = getConnectionId(session);
        String userId = connectionManager.getUserId(connectionId);
        
        connectionManager.removeConnection(connectionId);
        redisService.removeUserConnection(userId, connectionId);
        
        // 如果用户所有连接都断开，更新为离线
        if (!redisService.hasActiveConnections(userId)) {
            presenceService.userOffline(userId);
        }
    }
}
```

### 2. 消息存储设计

```sql
-- 消息表设计
CREATE TABLE messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    message_id VARCHAR(64) NOT NULL UNIQUE COMMENT '消息唯一ID',
    from_user_id VARCHAR(64) NOT NULL COMMENT '发送者',
    to_target_id VARCHAR(64) NOT NULL COMMENT '接收者（用户ID或群ID）',
    target_type TINYINT NOT NULL COMMENT '1:用户 2:群组',
    message_type TINYINT NOT NULL COMMENT '消息类型',
    content TEXT NOT NULL COMMENT '消息内容',
    status TINYINT DEFAULT 0 COMMENT '0:已发送 1:已送达 2:已读',
    created_at BIGINT NOT NULL COMMENT '创建时间',
    updated_at BIGINT NOT NULL COMMENT '更新时间',
    INDEX idx_from_user(from_user_id, created_at),
    INDEX idx_to_target(to_target_id, created_at),
    INDEX idx_message_id(message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 消息已读状态表
CREATE TABLE message_read_status (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    message_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    read_at BIGINT NOT NULL,
    UNIQUE KEY uk_message_user(message_id, user_id),
    INDEX idx_user_read(user_id, read_at)
);

-- 群组成员表
CREATE TABLE group_members (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    role TINYINT DEFAULT 0 COMMENT '0:成员 1:管理员 2:群主',
    joined_at BIGINT NOT NULL,
    UNIQUE KEY uk_group_user(group_id, user_id),
    INDEX idx_user_groups(user_id)
);
```

### 3. 离线消息处理

```java
@Service
public class OfflineMessageService {
    
    // 存储离线消息
    public void storeOfflineMessage(String userId, Message message) {
        // Redis存储（Sorted Set）
        String key = "offline:messages:" + userId;
        redisTemplate.opsForZSet().add(
            key, 
            JsonUtils.toJson(message),
            message.getTimestamp()
        );
        
        // 设置过期时间（7天）
        redisTemplate.expire(key, 7, TimeUnit.DAYS);
        
        // 发送推送通知
        pushService.sendPushNotification(userId, message);
    }
    
    // 同步离线消息
    public void syncOfflineMessages(String userId, String connectionId) {
        String key = "offline:messages:" + userId;
        
        // 获取所有离线消息
        Set<String> messages = redisTemplate.opsForZSet().range(key, 0, -1);
        
        // 通过WebSocket发送
        for (String msgJson : messages) {
            Message message = JsonUtils.parse(msgJson, Message.class);
            webSocketGateway.sendMessage(connectionId, message);
            
            // 更新消息状态为已送达
            messageService.updateStatus(message.getMessageId(), DeliveryStatus.DELIVERED);
        }
        
        // 清空离线消息
        redisTemplate.delete(key);
    }
}
```

## 📖 性能优化

### 1. 连接优化

```java
/**
 * WebSocket连接优化
 */
public class ConnectionOptimization {
    
    // 1. 使用Netty替代Tomcat WebSocket
    /*
     * Netty性能更好，内存占用更低
     * 支持自定义协议
     * 更好的连接管理
     */
    
    // 2. 连接复用
    /*
     * 同一用户多设备共享连接
     * 心跳包合并发送
     * 消息批量发送
     */
    
    // 3. 资源控制
    /*
     * 限制单个IP连接数
     * 限制单个用户连接数
     * 连接超时自动关闭
     */
}
```

### 2. 消息优化

```java
/**
 * 消息处理优化
 */
public class MessageOptimization {
    
    // 1. 消息压缩
    /*
     * 文本消息Gzip压缩
     * 图片视频使用缩略图
     * 消息体精简字段
     */
    
    // 2. 消息合并
    /*
     * 短时间内多条消息合并发送
     * 离线消息批量同步
     * 消息确认批量处理
     */
    
    // 3. 缓存优化
    /*
     * 热点消息缓存
     * 用户信息缓存
     * 群组信息缓存
     */
}
```

### 3. 存储优化

```java
/**
 * 存储层优化
 */
public class StorageOptimization {
    
    // 1. 数据库分表
    /*
     * 消息表按用户ID分表
     * 群组消息按群ID分表
     * 历史消息归档
     */
    
    // 2. 读写分离
    /*
     * 写操作：主库
     * 读操作：从库
     * 实时消息：Redis
     */
    
    // 3. CDN加速
    /*
     * 图片、视频文件使用CDN
     * 静态资源缓存
     * 边缘节点加速
     */
}
```

## 📖 监控与运维

### 1. 监控指标

```yaml
# 监控指标体系
metrics:
  connection:
    active_connections: 活跃连接数
    connection_rate: 连接建立速率
    heartbeat_success_rate: 心跳成功率
    
  message:
    send_rate: 消息发送速率
    deliver_latency: 消息投递延迟
    deliver_success_rate: 投递成功率
    
  system:
    cpu_usage: CPU使用率
    memory_usage: 内存使用率
    gc_time: GC时间
    
  business:
    online_users: 在线用户数
    daily_messages: 日消息量
    group_count: 群组数量
```

### 2. 告警规则

```java
/**
 * 关键告警规则
 */
public class AlertRules {
    
    // 连接异常
    /*
     * 活跃连接数突降 > 30%
     * 心跳成功率 < 95%
     * 单Gateway连接数 > 10万
     */
    
    // 消息异常
    /*
     * 消息投递延迟 > 1秒
     * 消息失败率 > 1%
     * 消息积压数量 > 10万
     */
    
    // 系统异常
    /*
     * CPU使用率 > 80%
     * 内存使用率 > 85%
     * 磁盘使用率 > 90%
     */
}
```

## 📖 面试真题

### Q1: 如何设计一个支持千万级用户的IM系统？

**答：**
1. **架构分层**：客户端、网关层、业务层、存储层
2. **连接管理**：WebSocket长连接，网关集群，心跳保活
3. **消息投递**：消息队列解耦，可靠投递，状态同步
4. **状态管理**：Redis存储在线状态，实时更新
5. **存储设计**：消息分表，冷热分离，读写分离
6. **扩展性**：无状态设计，水平扩展，负载均衡

### Q2: 如何保证消息不丢失？

**答：**
1. **发送确认**：客户端发送后等待服务端ACK
2. **消息持久化**：收到消息立即存储到数据库
3. **消息队列**：使用Kafka保证消息不丢
4. **接收确认**：接收方返回已读回执
5. **离线消息**：离线消息存储，上线后同步
6. **重试机制**：投递失败自动重试

### Q3: 如何处理海量连接？

**答：**
1. **网关集群**：多个网关分担连接压力
2. **连接复用**：同一用户多设备共享连接
3. **资源限制**：限制单机连接数，防DDOS
4. **心跳优化**：合理设置心跳间隔，减少空耗
5. **连接池**：使用连接池管理数据库连接
6. **异步处理**：I/O多路复用，非阻塞处理

### Q4: 如何实现多端消息同步？

**答：**
1. **消息多播**：一条消息推送到用户所有在线设备
2. **消息去重**：基于messageId去重，避免重复
3. **状态同步**：已读状态同步到所有设备
4. **时间同步**：消息按时间戳排序，保证顺序
5. **冲突解决**：最后写入优先，或用户手动解决
6. **增量同步**：只同步增量消息，减少流量

### Q5: 如何设计群聊功能？

**答：**
1. **群组管理**：建群、加人、踢人、解散
2. **消息扩散**：群消息推送给所有成员
3. **@功能**：支持@特定成员
4. **群公告**：群主发布公告
5. **消息屏蔽**：支持屏蔽某些群成员
6. **群权限**：不同角色不同权限

## 📚 延伸阅读

- [WebSocket协议](https://tools.ietf.org/html/rfc6455)
- [Netty实战](https://book.douban.com/subject/27038538/)
- [IM系统架构设计](https://time.geekbang.org/column/intro/100026301)
- [微信架构设计](https://cloud.tencent.com/developer/article/1004988)

---

**⭐ 重点：IM系统是典型的高并发实时系统，需要深入理解网络编程、消息队列、分布式存储等技术**