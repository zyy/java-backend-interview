---
layout: default
title: 推荐系统设计
---
# 推荐系统设计

> 设计一个个性化推荐系统，实现千人千面的内容推荐

## 🎯 面试重点

- 推荐算法选型与组合
- 用户画像构建
- 实时推荐与离线推荐
- 推荐效果评估

## 📖 需求分析

### 业务场景

```java
/**
 * 推荐系统应用场景
 */
public class RecommendationScenarios {
    
    // 1. 电商推荐
    /*
     * 商品推荐："猜你喜欢"
     * 关联推荐："买了又买"
     * 相似推荐："看了又看"
     */
    
    // 2. 内容推荐
    /*
     * 新闻推荐：个性化资讯
     * 视频推荐：短视频feed流
     * 音乐推荐：每日推荐歌单
     */
    
    // 3. 社交推荐
    /*
     * 好友推荐："可能认识的人"
     * 群组推荐："你可能感兴趣的群"
     * 内容推荐：朋友圈动态
     */
    
    // 4. 广告推荐
    /*
     * 精准广告投放
     * 搜索广告推荐
     * 信息流广告
     */
}
```

### 核心指标

```java
/**
 * 推荐系统评估指标
 */
public class EvaluationMetrics {
    
    // 1. 用户满意度
    /*
     * 点击率（CTR）
     * 转化率（CVR）
     * 留存率（Retention）
     */
    
    // 2. 业务指标
    /*
     * 总点击量
     * 总销售额
     * 用户活跃度
     */
    
    // 3. 技术指标
    /*
     * 推荐响应时间
     * 推荐覆盖率
     * 新颖性（Novelty）
     * 多样性（Diversity）
     */
    
    // 4. 公平性指标
    /*
     * 马太效应控制
     * 长尾物品曝光
     * 新用户冷启动
     */
}
```

## 📖 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                          客户端                              │
│                    (App/Web/小程序)                         │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/API
┌─────────────────────────────▼───────────────────────────────┐
│                          API网关                             │
│                     (流量分发、认证)                         │
└──────────────┬────────────────┬──────────────────────────────┘
               │                │
    ┌──────────▼──────┐ ┌──────▼──────────┐
    │   实时推荐服务   │ │   离线推荐服务   │
    │  (Online)       │ │  (Offline)      │
    └──────────┬──────┘ └──────┬──────────┘
               │                │
    ┌──────────▼────────────────▼──────────┐
    │         推荐引擎 (Recall + Rank)       │
    └──────────┬─────────────────────────────┘
               │
    ┌──────────▼─────────────────────────────┐
    │           特征存储与计算                 │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
    │  │ 用户特征 │ │ 物品特征 │ │ 场景特征 │  │
    │  └─────────┘ └─────────┘ └─────────┘  │
    └──────────┬─────────────────────────────┘
               │
    ┌──────────▼─────────────────────────────┐
    │           数据源                         │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
    │  │ 用户行为 │ │ 物品信息 │ │ 上下文信息│  │
    │  └─────────┘ └─────────┘ └─────────┘  │
    └────────────────────────────────────────┘
```

### 推荐流程

```java
/**
 * 推荐系统核心流程
 */
public class RecommendationPipeline {
    
    // 1. 召回（Recall）
    /*
     * 从海量物品中筛选出几百个候选集
     * 策略：协同过滤、内容过滤、热门推荐
     * 目标：保证召回率，覆盖用户兴趣
     */
    
    // 2. 排序（Ranking）
    /*
     * 对召回结果进行精排序
     * 使用机器学习模型预测CTR
     * 策略：LR、GBDT、DNN、DeepFM
     */
    
    // 3. 重排（Re-ranking）
    /*
     * 考虑业务规则和多样性
     * 去重、打散、多样性控制
     * 插入广告、运营位
     */
    
    // 4. 展示与反馈
    /*
     * 推荐结果展示
     * 用户行为收集
     * 实时反馈学习
     */
}
```

## 📖 详细设计

### 1. 数据采集与处理

```java
/**
 * 用户行为数据采集
 */
public class DataCollection {
    
    // 用户行为类型
    public enum UserAction {
        VIEW,      // 浏览
        CLICK,     // 点击
        BUY,       // 购买
        COLLECT,   // 收藏
        SHARE,     // 分享
        COMMENT,   // 评论
        LIKE       // 点赞
    }
    
    // 行为日志格式
    @Data
    public class UserBehavior {
        private String userId;        // 用户ID
        private String itemId;        // 物品ID
        private UserAction action;    // 行为类型
        private Long timestamp;       // 时间戳
        private String scene;         // 场景：首页、详情页等
        private Map<String, Object> ext; // 扩展字段
    }
    
    // 数据采集方案
    public class CollectionStrategy {
        /*
         * 客户端埋点：SDK自动采集
         * 服务端日志：Nginx访问日志
         * 实时流：Kafka实时收集
         * 批量处理：HDFS存储，Spark处理
         */
    }
}
```

### 2. 特征工程

```java
/**
 * 特征体系构建
 */
public class FeatureEngineering {
    
    // 用户特征
    @Data
    public class UserFeatures {
        // 静态特征
        private String userId;
        private Integer age;
        private String gender;
        private String location;
        
        // 动态特征
        private List<String> recentViewedItems;  // 最近浏览
        private List<String> recentBoughtItems;  // 最近购买
        private Map<String, Integer> categoryPref; // 品类偏好
        private Double avgPricePref;             // 价格偏好
        
        // 统计特征
        private Integer totalOrders;             // 总订单数
        private Double avgOrderValue;            // 客单价
        private String favoriteBrand;            // 偏好品牌
    }
    
    // 物品特征
    @Data
    public class ItemFeatures {
        private String itemId;
        private String category;      // 品类
        private String brand;         // 品牌
        private Double price;         // 价格
        private List<String> tags;    // 标签
        private String title;         // 标题
        private String description;   // 描述
        
        // 统计特征
        private Integer totalSales;   // 总销量
        private Double avgRating;     // 平均评分
        private Integer viewCount;    // 浏览数
    }
    
    // 场景特征
    @Data
    public class ContextFeatures {
        private String scene;         // 场景：首页、搜索等
        private String timeOfDay;     // 时间段：早晨、中午等
        private String dayOfWeek;     // 周几
        private String season;        // 季节
        private String location;      // 地理位置
        private String network;       // 网络环境
    }
}
```

### 3. 召回策略

```java
/**
 * 多路召回策略
 */
public class RecallStrategies {
    
    // 1. 协同过滤（Collaborative Filtering）
    public class CollaborativeFiltering {
        /*
         * 用户协同过滤：找到相似用户，推荐他们喜欢的物品
         * 物品协同过滤：找到相似物品，推荐给用户
         * 实现：Spark MLlib ALS算法
         * 优势：发现用户潜在兴趣
         * 劣势：冷启动问题
         */
    }
    
    // 2. 内容过滤（Content-based）
    public class ContentBased {
        /*
         * 基于物品特征和用户历史偏好
         * 物品特征：品类、品牌、价格、标签
         * 用户画像：历史行为构建用户偏好
         * 相似度计算：余弦相似度、Jaccard相似度
         * 优势：解决冷启动，可解释性强
         */
    }
    
    // 3. 热门推荐（Popularity）
    public class Popularity {
        /*
         * 基于全局热门度
         * 策略：最近24小时热门、周热门、历史热门
         * 加权公式：热度 = 销量 * 0.5 + 浏览 * 0.3 + 收藏 * 0.2
         * 优势：解决冷启动，保证基础体验
         */
    }
    
    // 4. 实时推荐（Real-time）
    public class RealTimeRecall {
        /*
         * 基于用户实时行为
         * 策略：用户刚刚浏览的物品的相似物品
         * 实现：Redis存储实时行为，快速召回
         * 优势：捕捉实时兴趣变化
         */
    }
    
    // 5. 多样性召回
    public class DiversityRecall {
        /*
         * 保证推荐结果多样性
         * 策略：按品类、品牌、价格段等多维度召回
         * 实现：多路召回结果融合
         * 优势：避免信息茧房，探索用户兴趣
         */
    }
}
```

### 4. 排序模型

```java
/**
 * 排序模型演进
 */
public class RankingModels {
    
    // 1. 逻辑回归（LR）
    /*
     * 优点：简单、可解释性强、训练快
     * 缺点：特征需要人工组合，无法学习非线性关系
     * 应用场景：基础排序模型
     */
    
    // 2. 梯度提升树（GBDT）
    /*
     * 优点：自动特征组合，非线性拟合能力强
     * 缺点：训练慢，模型大
     * 应用场景：主流排序模型
     */
    
    // 3. 因子分解机（FM）
    /*
     * 优点：自动学习特征交叉，稀疏数据表现好
     * 缺点：高阶特征交叉能力有限
     * 应用场景：推荐系统经典模型
     */
    
    // 4. 深度神经网络（DNN）
    /*
     * 优点：自动特征提取，拟合能力强
     * 缺点：需要大量数据，可解释性差
     * 应用场景：复杂特征场景
     */
    
    // 5. 深度因子分解机（DeepFM）
    /*
     * 优点：结合FM和DNN，兼顾记忆和泛化
     * 缺点：模型复杂，训练资源消耗大
     * 应用场景：CTR预测最优模型之一
     */
    
    // 6. 多任务学习（MMOE）
    /*
     * 优点：同时优化多个目标（点击、转化、时长）
     * 缺点：模型复杂，需要多目标数据
     * 应用场景：多目标优化场景
     */
}
```

### 5. 实时推荐架构

```java
/**
 * 实时推荐实现
 */
public class RealTimeRecommendation {
    
    // 实时特征计算
    public class RealTimeFeatures {
        /*
         * 用户实时行为特征（最近5分钟）
         * 物品实时热度特征
         * 上下文实时特征（时间、位置等）
         * 实现：Flink实时计算，Redis存储
         */
    }
    
    // 实时模型预测
    public class RealTimePrediction {
        /*
         * 在线模型服务（TensorFlow Serving）
         * 特征实时拼接
         * 模型实时推理
         * 响应时间要求：< 100ms
         */
    }
    
    // 实时反馈学习
    public class RealTimeLearning {
        /*
         * 用户行为实时反馈
         * 模型在线学习（Online Learning）
         * 特征权重实时调整
         * A/B测试实时分流
         */
    }
}
```

## 📖 关键技术实现

### 1. 协同过滤实现

```scala
// Spark ALS实现协同过滤
import org.apache.spark.ml.recommendation.ALS

val ratings = spark.read.parquet("hdfs://user_behavior.parquet")
  .select($"userId".cast("int"), $"itemId".cast("int"), $"rating".cast("float"))

// 训练ALS模型
val als = new ALS()
  .setMaxIter(10)
  .setRegParam(0.01)
  .setUserCol("userId")
  .setItemCol("itemId")
  .setRatingCol("rating")
  .setColdStartStrategy("drop")

val model = als.fit(ratings)

// 为用户推荐物品
val userRecs = model.recommendForAllUsers(10)
  .select($"userId", explode($"recommendations").as("rec"))
  .select($"userId", $"rec.itemId", $"rec.rating")

// 保存推荐结果
userRecs.write.parquet("hdfs://user_recommendations.parquet")
```

### 2. 特征存储设计

```sql
-- 用户特征表
CREATE TABLE user_features (
    user_id VARCHAR(64) PRIMARY KEY,
    age INT,
    gender VARCHAR(10),
    location VARCHAR(100),
    category_pref JSON COMMENT '品类偏好 {category: weight}',
    price_pref DECIMAL(10,2) COMMENT '价格偏好',
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_update(last_update)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 物品特征表  
CREATE TABLE item_features (
    item_id VARCHAR(64) PRIMARY KEY,
    category_id VARCHAR(32),
    brand_id VARCHAR(32),
    price DECIMAL(10,2),
    tags JSON COMMENT '标签数组',
    total_sales INT DEFAULT 0,
    avg_rating DECIMAL(3,2),
    view_count INT DEFAULT 0,
    INDEX idx_category(category_id),
    INDEX idx_brand(brand_id),
    INDEX idx_sales(total_sales)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户实时行为表（Redis）
/*
Key: user:recent:{userId}
Type: List
Value: [itemId1:action1:timestamp1, itemId2:action2:timestamp2, ...]
Expire: 7 days
*/
```

### 3. 实时特征计算（Flink）

```java
public class RealTimeFeatureJob {
    
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // 消费用户行为Kafka
        DataStream<UserBehavior> behaviorStream = env
            .addSource(new FlinkKafkaConsumer<>("user-behavior", 
                new SimpleStringSchema(), properties))
            .map(json -> JsonUtils.parse(json, UserBehavior.class));
        
        // 实时特征计算
        DataStream<UserFeature> featureStream = behaviorStream
            .keyBy(UserBehavior::getUserId)
            .window(SlidingProcessingTimeWindows.of(Time.minutes(5), Time.minutes(1)))
            .process(new ProcessWindowFunction<UserBehavior, UserFeature, String, TimeWindow>() {
                @Override
                public void process(String userId, Context context, 
                    Iterable<UserBehavior> behaviors, Collector<UserFeature> out) {
                    
                    UserFeature feature = new UserFeature();
                    feature.setUserId(userId);
                    feature.setTimestamp(System.currentTimeMillis());
                    
                    // 计算5分钟内行为统计
                    Map<String, Integer> actionCounts = new HashMap<>();
                    List<String> recentItems = new ArrayList<>();
                    
                    for (UserBehavior behavior : behaviors) {
                        actionCounts.merge(behavior.getAction().name(), 1, Integer::sum);
                        recentItems.add(behavior.getItemId());
                    }
                    
                    feature.setRecentActions(actionCounts);
                    feature.setRecentItems(recentItems);
                    
                    out.collect(feature);
                }
            });
        
        // 写入Redis
        featureStream.addSink(new RedisSink<>(
            new FlinkJedisPoolConfig.Builder().setHost("redis").build(),
            new RedisMapper<UserFeature>() {
                @Override
                public RedisCommandDescription getCommandDescription() {
                    return new RedisCommandDescription(RedisCommand.HSET);
                }
                
                @Override
                public String getKeyFromData(UserFeature feature) {
                    return "user:realtime:" + feature.getUserId();
                }
                
                @Override
                public String getValueFromData(UserFeature feature) {
                    return JsonUtils.toJson(feature);
                }
            }
        ));
        
        env.execute("Real-time Feature Computation");
    }
}
```

### 4. 模型服务（TensorFlow Serving）

```python
# 模型训练
import tensorflow as tf

# 构建DeepFM模型
def build_deepfm_model(user_features, item_features, context_features):
    # FM部分
    fm_user_emb = tf.keras.layers.Embedding(user_vocab_size, embedding_dim)(user_features)
    fm_item_emb = tf.keras.layers.Embedding(item_vocab_size, embedding_dim)(item_features)
    
    # 特征交叉
    fm_cross = tf.reduce_sum(fm_user_emb * fm_item_emb, axis=1, keepdims=True)
    
    # DNN部分
    concat_features = tf.keras.layers.Concatenate()([user_features, item_features, context_features])
    dnn_output = tf.keras.layers.Dense(128, activation='relu')(concat_features)
    dnn_output = tf.keras.layers.Dense(64, activation='relu')(dnn_output)
    dnn_output = tf.keras.layers.Dense(32, activation='relu')(dnn_output)
    
    # 合并FM和DNN
    combined = tf.keras.layers.Concatenate()([fm_cross, dnn_output])
    output = tf.keras.layers.Dense(1, activation='sigmoid')(combined)
    
    model = tf.keras.Model(inputs=[user_features, item_features, context_features], 
                          outputs=output)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    return model

# 保存模型
model.save('/models/deepfm/1', save_format='tf')

# 启动TensorFlow Serving
# docker run -p 8501:8501 --mount type=bind,source=/models,target=/models -e MODEL_NAME=deepfm tensorflow/serving
```

```java
// 客户端调用模型服务
public class ModelClient {
    
    public double predictCTR(String userId, String itemId, Context context) {
        // 准备特征
        Map<String, Object> features = new HashMap<>();
        features.put("user_id", userId);
        features.put("item_id", itemId);
        features.put("time_of_day", context.getTimeOfDay());
        features.put("category", getItemCategory(itemId));
        
        // 调用TensorFlow Serving
        String url = "http://tf-serving:8501/v1/models/deepfm:predict";
        Map<String, Object> request = Map.of("instances", List.of(features));
        
        ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
        List<List<Double>> predictions = (List<List<Double>>) response.getBody().get("predictions");
        
        return predictions.get(0).get(0);  // CTR概率
    }
}
```

## 📖 效果评估与优化

### 1. A/B测试框架

```java
/**
 * A/B测试实现
 */
public class ABTestFramework {
    
    // 实验配置
    @Data
    public class Experiment {
        private String experimentId;      // 实验ID
        private String name;              // 实验名称
        private List<Variant> variants;   // 实验变体
        private String targetMetric;      // 目标指标：CTR、CVR等
        private Date startTime;           // 开始时间
        private Date endTime;             // 结束时间
        private Double trafficRatio;      // 流量比例
    }
    
    // 实验变体
    @Data
    public class Variant {
        private String variantId;         // 变体ID
        private String name;              // 变体名称
        private Double trafficRatio;      // 流量分配比例
        private Map<String, Object> params; // 参数配置
    }
    
    // 流量分配
    public class TrafficAllocation {
        /*
         * 基于用户ID哈希分流
         * 保证同一用户始终进入同一变体
         * 支持多实验层叠（正交实验）
         */
        public String assignVariant(String userId, String experimentId) {
            String hashKey = userId + ":" + experimentId;
            int hash = Math.abs(hashKey.hashCode()) % 100;
            
            // 根据流量比例分配
            if (hash < 50) return "control";      // 50%对照组
            else if (hash < 75) return "variant_a"; // 25%变体A
            else return "variant_b";               // 25%变体B
        }
    }
}
```

### 2. 评估指标计算

```sql
-- CTR计算
SELECT 
    experiment_id,
    variant_id,
    COUNT(DISTINCT user_id) as user_count,
    SUM(IF(action = 'click', 1, 0)) as click_count,
    SUM(IF(action = 'view', 1, 0)) as view_count,
    SUM(IF(action = 'click', 1, 0)) / SUM(IF(action = 'view', 1, 0)) as ctr
FROM user_behavior_logs
WHERE date = '2023-10-01'
    AND experiment_id = 'rec_algorithm_v2'
GROUP BY experiment_id, variant_id;

-- 显著性检验（t检验）
WITH stats AS (
    SELECT 
        variant_id,
        AVG(ctr) as mean_ctr,
        STDDEV(ctr) as std_ctr,
        COUNT(*) as sample_size
    FROM user_daily_ctr
    WHERE experiment_id = 'rec_algorithm_v2'
    GROUP BY variant_id
)
SELECT 
    a.variant_id as variant_a,
    b.variant_id as variant_b,
    -- t统计量
    ABS(a.mean_ctr - b.mean_ctr) / 
        SQRT(POWER(a.std_ctr, 2)/a.sample_size + POWER(b.std_ctr, 2)/b.sample_size) as t_stat
FROM stats a CROSS JOIN stats b
WHERE a.variant_id != b.variant_id;
```

## 📖 冷启动解决方案

### 1. 用户冷启动

```java
/**
 * 新用户推荐策略
 */
public class NewUserStrategy {
    
    // 策略1：热门推荐
    public List<String> recommendByPopularity(String userId) {
        // 返回全局热门物品
        return redisService.zrevrange("global:popular:items", 0, 9);
    }
    
    // 策略2：地域推荐
    public List<String> recommendByLocation(String userId, String location) {
        // 返回同地域热门物品
        return redisService.zrevrange("location:popular:" + location, 0, 9);
    }
    
    // 策略3：人口统计推荐
    public List<String> recommendByDemographics(UserProfile profile) {
        // 基于年龄、性别等 demographic 信息推荐
        String key = String.format("demo:rec:%s:%s:%s", 
            profile.getAgeGroup(), profile.getGender(), profile.getLocation());
        return redisService.zrevrange(key, 0, 9);
    }
    
    // 策略4：探索式推荐
    public List<String> exploreRecommendation() {
        // 推荐多样化的物品，探索用户兴趣
        List<String> recommendations = new ArrayList<>();
        recommendations.addAll(getPopularItems());          // 热门
        recommendations.addAll(getNewItems());              // 新品
        recommendations.addAll(getDiverseCategories());     // 多品类
        return recommendations;
    }
}
```

### 2. 物品冷启动

```java
/**
 * 新物品推荐策略
 */
public class NewItemStrategy {
    
    // 基于内容相似度
    public List<String> findSimilarItems(Item newItem) {
        // 基于品类、品牌、价格、标签等特征
        return contentBasedService.findSimilar(newItem, 10);
    }
    
    // 探索性曝光
    public void exploreExposure(String itemId, double exploreRatio) {
        // 将新物品混入推荐列表中
        // 探索比例：5%流量用于探索新物品
    }
    
    // 运营扶持
    public void operationalSupport(String itemId) {
        // 运营手动配置曝光
        // 新物品专区展示
        // 新手优惠券引导
    }
}
```

## 📖 面试真题

### Q1: 推荐系统的主要模块有哪些？

**答：**
1. **数据层**：用户行为采集、特征存储
2. **召回层**：从海量物品中快速筛选候选集（协同过滤、内容过滤、热门召回等）
3. **排序层**：对候选集精排序（CTR预估模型）
4. **重排层**：业务规则调整、多样性控制
5. **评估层**：A/B测试、效果评估、模型迭代

### Q2: 协同过滤有哪些类型？各有什么优缺点？

**答：**
1. **用户协同过滤**：
   - 优点：发现用户潜在兴趣
   - 缺点：用户矩阵稀疏，计算量大
   
2. **物品协同过滤**：
   - 优点：物品矩阵相对稠密，可离线计算
   - 缺点：难以应对物品冷启动

3. **矩阵分解（MF）**：
   - 优点：解决稀疏性问题，可扩展性好
   - 缺点：可解释性差，需要定期重训

4. **深度学习协同过滤**：
   - 优点：自动特征学习，效果好
   - 缺点：计算资源消耗大，可解释性差

### Q3: 如何处理推荐系统的冷启动问题？

**答：**
**用户冷启动：**
1. 基于热门推荐
2. 基于地域推荐
3. 基于人口统计信息推荐
4. 引导用户明确兴趣（标签选择）
5. 探索式推荐

**物品冷启动：**
1. 基于内容相似度推荐
2. 探索性曝光（Epsilon-Greedy）
3. 运营扶持（人工曝光）
4. 结合用户反馈快速学习

### Q4: 如何评估推荐系统的效果？

**答：**
1. **离线评估**：
   - 准确率：Precision、Recall、F1-score
   - 覆盖率：Coverage
   - 多样性：Intra-list Diversity
   - 新颖性：Novelty

2. **在线评估**：
   - 业务指标：CTR、CVR、GMV
   - 用户指标：留存率、使用时长
   - A/B测试：统计显著性检验

3. **长期评估**：
   - 用户满意度调研
   - 生态健康度（马太效应）
   - 系统可扩展性

### Q5: 推荐系统如何保证多样性？

**答：**
1. **召回阶段**：多路召回（不同策略保证多样性）
2. **排序阶段**：在损失函数中加入多样性正则项
3. **重排阶段**：
   - MMR（Maximal Marginal Relevance）算法
   - 品类打散（同一品类不超过2个）
   - 价格段分布（高、中、低均衡）
   - 时间新鲜度（新旧内容混合）
4. **探索机制**：ε-greedy、Thompson Sampling、Bandit算法

## 📚 延伸阅读

- [推荐系统实践](https://book.douban.com/subject/10769749/)
- [深度学习推荐系统](https://book.douban.com/subject/35013197/)
- [Recommender Systems Handbook](https://www.springer.com/gp/book/9781489976369)
- [Netflix推荐系统](https://research.netflix.com/research-area/recommendations)

---

**⭐ 重点：推荐系统是数据驱动和算法驱动的典型应用，需要平衡准确性、多样性、新颖性和实时性**