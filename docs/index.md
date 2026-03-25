---
layout: default
title: Java 后端面试资料库
---

<style>
.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3rem 2rem;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 2rem;
}
.hero h1 { color: white; margin-bottom: 1rem; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}
.card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  text-decoration: none;
  color: #333;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
  display: block;
}
.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
  border-color: #667eea;
}
.card h3 { color: #667eea; margin-bottom: 0.5rem; }
.card p { color: #666; font-size: 0.9rem; margin: 0; }
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #667eea;
  color: white;
  border-radius: 20px;
  font-size: 0.75rem;
  margin-top: 0.5rem;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin: 2rem 0;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}
.stat { text-align: center; }
.stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
.stat-label { color: #666; font-size: 0.9rem; }
</style>

<div class="hero">
  <h1>📚 Java 后端面试资料库</h1>
  <p>一份系统、全面、持续更新的面试指南，帮助你斩获心仪的 Offer</p>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-number">118+</div>
    <div class="stat-label">面试专题</div>
  </div>
  <div class="stat">
    <div class="stat-number">200+</div>
    <div class="stat-label">高频面试题</div>
  </div>
  <div class="stat">
    <div class="stat-number">100+</div>
    <div class="stat-label">代码示例</div>
  </div>
</div>

## 🚀 快速导航

<div class="cards">

<a class="card" href="java-core/">
  <h3>☕ Java 核心</h3>
  <p>HashMap、线程池、CAS/AQS、并发编程、IO/NIO</p>
  <span class="badge">18 篇</span>
</a>

<a class="card" href="jvm/">
  <h3>⚙️ JVM 原理</h3>
  <p>内存模型、垃圾回收、类加载机制，调优</p>
  <span class="badge">14 篇</span>
</a>

<a class="card" href="spring/">
  <h3>🌱 Spring 框架</h3>
  <p>IoC/AOP、自动装配、循环依赖、事务</p>
  <span class="badge">14 篇</span>
</a>

<a class="card" href="database/">
  <h3>🗄️ 数据库</h3>
  <p>索引原理、事务隔离、MVCC、锁机制</p>
  <span class="badge">11 篇</span>
</a>

<a class="card" href="middleware/">
  <h3>🔧 中间件</h3>
  <p>Redis、MQ、Kafka、缓存问题</p>
  <span class="badge">18 篇</span>
</a>

<a class="card" href="design-patterns/">
  <h3>🎨 设计模式</h3>
  <p>单例、工厂、策略、观察者、代理</p>
  <span class="badge">10 篇</span>
</a>

<a class="card" href="algorithm/">
  <h3>🧮 算法</h3>
  <p>链表、树、排序、查找、动态规划</p>
  <span class="badge">15 篇</span>
</a>

<a class="card" href="microservices/">
  <h3>🏗️ 微服务</h3>
  <p>分布式、CAP/BASE、服务治理</p>
  <span class="badge">12 篇</span>
</a>

<a class="card" href="projects/">
  <h3>📂 项目实战</h3>
  <p>秒杀系统、短链接、简历亮点、面试技巧</p>
  <span class="badge">6 篇</span>
</a>

</div>

## 📖 使用建议

1. **系统学习**: 按模块顺序学习，建立完整知识体系
2. **重点突破**: ⭐⭐⭐ 标记的内容是高级面试重点
3. **代码实战**: 每个知识点都配有代码示例
4. **定期复习**: 面试前重点复习高频面试题

## 🎯 面试准备路线

```
基础阶段 (1-2周)
    ↓
Java核心 → 数据库基础 → 常用框架
    ↓
进阶阶段 (2-3周)
    ↓
JVM → 并发编程 → 性能优化
    ↓
高级阶段 (持续)
    ↓
分布式 → 微服务 → 架构设计
```

---

> 💡 **提示**: 点击上方卡片开始学习之旅！持续更新中...
