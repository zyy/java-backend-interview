# 手写 RPC 框架

> RPC 核心原理

## 🎯 面试重点

- RPC 调用流程
- 核心组件

## 📖 核心流程

```java
/**
 * RPC 调用流程
 * 
 * 1. 服务提供者注册服务
 * 2. 服务消费者订阅服务
 * 3. 消费者调用代理对象
 * 4. 代理序列化请求，网络传输
 * 5. 服务端反序列化，执行方法
 * 6. 返回结果
 */
public class RPCFlow {}
```

## 📖 简化实现

```java
/**
 * 服务端
 */
public class RPCServer {
    public static void main(String[] args) throws Exception {
        ServerSocket server = new ServerSocket(8080);
        while (true) {
            Socket socket = server.accept();
            ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
            String methodName = ois.readUTF();
            Class<?>[] paramTypes = (Class<?>[]) ois.readObject();
            Object[] args1 = (Object[]) ois.readObject();
            
            // 反射调用
            Method method = UserService.class.getMethod(methodName, paramTypes);
            Object result = method.invoke(new UserServiceImpl(), args1);
            
            ObjectOutputStream oos = new ObjectOutputStream(socket.getOutputStream());
            oos.writeObject(result);
        }
    }
}

/**
 * 客户端代理
 */
public class RPCProxy {
    @SuppressWarnings("unchecked")
    public static <T> T create(Class<T> interfaceClass) {
        return (T) Proxy.newProxyInstance(
            interfaceClass.getClassLoader(),
            new Class<?>[]{interfaceClass},
            (proxy, method, args) -> {
                Socket socket = new Socket("localhost", 8080);
                ObjectOutputStream oos = new ObjectOutputStream(socket.getOutputStream());
                oos.writeUTF(method.getName());
                oos.writeObject(method.getParameterTypes());
                oos.writeObject(args);
                
                ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());
                return ois.readObject();
            }
        );
    }
}
```

## 📖 面试真题

### Q1: RPC 核心组件？

**答：** 注册中心、代理、序列化、网络传输。

---

**⭐ 重点：RPC 是分布式系统的基础**