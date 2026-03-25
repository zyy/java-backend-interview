---
layout: default
title: 手写线程池
---
# 手写线程池

> 线程池实现原理

## 🎯 面试重点

- 线程池核心参数
- 实现原理

## 📖 简化实现

```java
/**
 * 简化线程池
 */
public class MyThreadPool {
    private BlockingQueue<Runnable> taskQueue;
    private List<Worker> workers;
    private volatile boolean isShutdown = false;
    
    public MyThreadPool(int poolSize, int queueSize) {
        this.taskQueue = new ArrayBlockingQueue<>(queueSize);
        this.workers = new ArrayList<>();
        for (int i = 0; i < poolSize; i++) {
            Worker worker = new Worker();
            workers.add(worker);
            worker.start();
        }
    }
    
    public void execute(Runnable task) {
        if (isShutdown) {
            throw new IllegalStateException("Pool is shutdown");
        }
        taskQueue.offer(task);
    }
    
    public void shutdown() {
        isShutdown = true;
        for (Worker worker : workers) {
            worker.interrupt();
        }
    }
    
    private class Worker extends Thread {
        public void run() {
            while (!isShutdown || !taskQueue.isEmpty()) {
                try {
                    Runnable task = taskQueue.take();
                    task.run();
                } catch (InterruptedException e) {
                    break;
                }
            }
        }
    }
}
```

## 📖 面试真题

### Q1: 线程池核心参数？

**答：** corePoolSize, maximumPoolSize, workQueue, keepAliveTime, handler。

---

**⭐ 重点：理解线程池原理**