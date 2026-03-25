# equals 与 hashCode

> Java 对象比较的核心方法

## 🎯 面试重点

- equals 和 == 的区别
- hashCode 的作用
- 为什么重写 equals 必须重写 hashCode

## 📖 equals vs ==

### == 比较

```java
/**
 * == 比较
 * 
 * 基本类型：比较值
 * 引用类型：比较内存地址
 */
public class CompareDemo {
    // 基本类型
    int a = 10;
    int b = 10;
    System.out.println(a == b);  // true
    
    // 引用类型
    String s1 = new String("hello");
    String s2 = new String("hello");
    System.out.println(s1 == s2);  // false（内存地址不同）
    System.out.println(s1 == "hello");  // false
    
    // 字符串常量池
    String s3 = "hello";
    String s4 = "hello";
    System.out.println(s3 == s4);  // true（常量池）
}
```

### equals 方法

```java
/**
 * equals 方法
 * 
 * Object 默认实现：和 == 一样（比较地址）
 * 通常需要重写为比较内容
 */
public class EqualsDemo {
    // String equals 重写
    String s1 = new String("hello");
    String s2 = new String("hello");
    System.out.println(s1.equals(s2));  // true（比较内容）
    
    // 自定义类重写 equals
    class Person {
        String name;
        int age;
        
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            Person person = (Person) o;
            return age == person.age && 
                   Objects.equals(name, person.name);
        }
    }
}
```

## 📖 hashCode

### 作用

```java
/**
 * hashCode 的作用
 * 
 * 用于哈希表（HashMap, HashSet）快速定位
 * 
 * 规则：
 * 1. 同一对象多次调用 hashCode 返回相同值
 * 2. 相等对象必须有相等的 hashCode
 */
public class HashCodeDemo {
    // HashMap 使用
    /*
     * HashMap 的 get 操作：
     * 1. 计算 key 的 hashCode
     * 2. 定位到数组位置
     * 3. 遍历链表/红黑树，调用 equals 比较
     */
}
```

### 重写规则

```java
/**
 * 重写 equals 必须重写 hashCode
 * 
 * 原因：HashMap/HashSet 用 hashCode 定位
 */
public class EqualsHashCodeRule {
    // 示例
    /*
     * class Person {
     *     String name;
     *     
     *     // 只重写 equals
     *     public boolean equals(Object o) { ... }
     *     // 没有重写 hashCode
     * }
     * 
     * Person p1 = new Person("Tom");
     * Person p2 = new Person("Tom");
     * 
     * HashSet<Person> set = new HashSet<>();
     * set.add(p1);
     * set.add(p2);  // 可以添加成功！（因为 hashCode 不同）
     * 
     * set.contains(p1);  // 可能返回 false
     */
}
```

### 最佳实践

```java
/**
 * 最佳实践：使用 IDE 自动生成
 */
public class BestPractice {
    // 使用 Objects.hash()
    /*
     * @Override
     * public int hashCode() {
     *     return Objects.hash(name, age);
     * }
     */
    
    // 使用 Lombok
    /*
     * @EqualsAndHashCode
     * class Person { ... }
     */
    
    // 注意
    /*
     * 1. 相同的对象必须有相同的 hashCode
     * 2. 不同对象的 hashCode 可以相同（哈希冲突）
     * 3. 尽量让 hashCode 分布均匀
     */
}
```

## 📖 面试真题

### Q1: == 和 equals 的区别？

**答：** == 基本类型比较值，引用类型比较地址；equals 默认比较地址，通常重写为比较内容。

### Q2: 为什么重写 equals 必须重写 hashCode？

**答：** HashMap/HashSet 用 hashCode 定位元素，如果不重写，可能导致相同对象被当作不同元素，或者无法正确找到元素。

### Q3: String 的 equals 和 hashCode？

**答：** String 重写了 equals 比较内容，hashCode 也根据内容计算。相同内容的 String 有相同的 hashCode。

---

**⭐ 重点：理解 equals 和 hashCode 是理解 Java 集合框架的基础**