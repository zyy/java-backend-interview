---
layout: default
title: Java 8/11/17 新特性详解 ⭐⭐⭐
---
# Java 8/11/17 新特性详解 ⭐⭐⭐

## 🎯 面试题：Java 8 有哪些新特性？Stream 和 Lambda 的原理是什么？

> Java 8 是历史上最重要的版本更新，引入了 Lambda 表达式、Stream API、Optional 等革命性特性，至今仍是面试的核心考点。Java 17 作为新的 LTS 版本，带来了 Sealed Classes、Records、Pattern Matching 等新特性。

---

## 一、Lambda 表达式

### 核心概念

```java
// 匿名内部类 → Lambda 表达式
// 之前：冗长的匿名类
Runnable r1 = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello");
    }
};

// 之后：简洁的 Lambda
Runnable r2 = () -> System.out.println("Hello");

// 语法规则：
// (参数列表) -> { 方法体 }
Runnable r = () -> {};                    // 无参数
Consumer<String> c = s -> {};             // 单参数（括号可省略）
BiFunction<A, B, R> f = (a, b) -> {};    // 多参数
Supplier<T> s = () -> new T();            // 返回值
```

### 函数式接口

```java
// @FunctionalInterface 注解：只有一个抽象方法的接口
@FunctionalInterface
public interface Predicate<T> {
    boolean test(T t);
    // 其他方法可以是 default 或 static
    default Predicate<T> and(Predicate<? super T> other) { ... }
    static <T> Predicate<T> isEqual(Object targetRef) { ... }
}

// Java 8 内置的四大核心函数式接口：
// 1. Consumer<T>      void accept(T t)
// 2. Supplier<T>       T get()
// 3. Function<T,R>     R apply(T t)
// 4. Predicate<T>      boolean test(T t)

// 还有变体：BiConsumer, BiFunction, BiPredicate, UnaryOperator, BinaryOperator
```

### 方法引用

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

// 三种方法引用：
// 1. 静态方法引用：ClassName::staticMethod
Function<String, Integer> parser = Integer::parseInt;

// 2. 实例方法引用：instance::method
String str = "Hello";
Supplier<Integer> len = str::length;

// 3. 构造方法引用：ClassName::new
Supplier<ArrayList<String>> listFactory = ArrayList::new;
Function<Integer, ArrayList<String>> listWithCapacity = ArrayList::new;

// 实际应用
names.stream()
    .map(String::toUpperCase)          // 实例方法引用
    .forEach(System.out::println);      // println 是 println(obj) 形式
```

---

## 二、Stream API

### 核心概念

```
Stream vs Collection：

Collection：存储数据的容器，遍历是外部迭代（for-each）
Stream：    计算数据的视图，遍历是内部迭代

┌──────────────────────────────────────────────────┐
│                   Stream 流水线                   │
│                                                  │
│  数据源 ──→ 中间操作 ──→ 中间操作 ──→ ... ──→ 终止操作 │
│  List     filter()     map()           forEach()│
│  Set      distinct()    limit()          collect()│
│  Array    sorted()     flatMap()        reduce() │
│  Map      skip()       peek()           findFirst()│
│           limit()                               │
└──────────────────────────────────────────────────┘

关键特性：
  1. 不存储数据
  2. 不修改数据源
  3. 惰性求值（只有遇到终止操作才执行）
```

### 常用操作

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

// 中间操作（返回 Stream，可以链式调用）
List<Integer> result = numbers.stream()
    .filter(n -> n % 2 == 0)      // 过滤偶数
    .map(n -> n * n)               // 平方
    .distinct()                     // 去重
    .limit(3)                      // 取前 3 个
    .collect(Collectors.toList());

// 排序
List<String> sorted = names.stream()
    .sorted(Comparator.comparing(String::length).reversed())
    .collect(Collectors.toList());

// 分组
Map<String, List<Person>> byCity = people.stream()
    .collect(Collectors.groupingBy(Person::getCity));

// 分区（按条件分为两组）
Map<Boolean, List<Person>> adults = people.stream()
    .collect(Collectors.partitioningBy(p -> p.getAge() >= 18));

// 多级分组
Map<String, Map<String, List<Person>>> byCityAndGender =
    people.stream()
        .collect(Collectors.groupingBy(
            Person::getCity,
            Collectors.groupingBy(Person::getGender)
        ));
```

### 终止操作

```java
// collect - 收集
List<String> list = stream().collect(Collectors.toList());
Set<String> set = stream().collect(Collectors.toSet());
Map<K, V> map = stream().collect(Collectors.toMap(k, v));

// reduce - 聚合
Optional<Integer> sum = numbers.stream().reduce(Integer::sum);
int total = numbers.stream().reduce(0, Integer::sum);

// max / min
Optional<Integer> max = numbers.stream().max(Integer::compareTo);
Optional<Integer> min = numbers.stream().min(Integer::compareTo);

// findAny / findFirst
Optional<String> first = names.stream().findFirst(); // 有序 stream 返回第一个

// allMatch / anyMatch / noneMatch
boolean allPositive = numbers.stream().allMatch(n -> n > 0);
boolean hasEven = numbers.stream().anyMatch(n -> n % 2 == 0);

// forEach
stream().forEach(System.out::println);

// count
long count = stream().count();

// 并行流
List<Integer> result = numbers.parallelStream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * n)
    .collect(Collectors.toList());
// parallelStream() 默认使用 ForkJoinPool.commonPool()
```

### 常用收集器

```java
// toList / toSet / toCollection
stream().collect(Collectors.toList());

// joining - 拼接字符串
String joined = names.stream()
    .collect(Collectors.joining(", ", "[", "]")); // [Alice, Bob, Charlie]

// counting / summingInt / averagingInt
long count = stream().collect(Collectors.counting());
int sum = stream().collect(Collectors.summingInt(Integer::intValue));
double avg = stream().collect(Collectors.averagingInt(Integer::intValue));

// summarizingInt - 一次性获取 count/sum/avg/min/max
IntSummaryStatistics stats = numbers.stream()
    .collect(Collectors.summarizingInt(Integer::intValue));
System.out.println(stats.getSum());   // 总和
System.out.println(stats.getAverage());// 平均值
System.out.println(stats.getMin());    // 最小值
System.out.println(stats.getMax());    // 最大值
```

---

## 三、Optional

### 为什么需要 Optional？

```java
// 空指针的噩梦
String city = user.getAddress().getCity().getName();
// 如果任何一个环节返回 null，立即 NPE

// Optional 解决方案
// 链式调用，安全地处理空值
Optional<String> city = Optional.ofNullable(user)
    .map(User::getAddress)
    .map(Address::getCity)
    .map(City::getName);

// 类似于
Optional<String> city = Optional.ofNullable(user)
    .flatMap(User::getAddress)
    .flatMap(Address::getCity)
    .map(City::getName); // City::getName 返回 String，不是 Optional
                        // 而 flatMap 用于返回 Optional 的方法
```

### 核心方法

```java
// 创建
Optional<String> empty = Optional.empty();
Optional<String> nonNull = Optional.of("value"); // null 抛 NPE
Optional<String> nullable = Optional.ofNullable(null); // 安全

// 判断
optional.isPresent();     // 是否有值
optional.isEmpty();       // Java 11+，是否为空

// 获取值
optional.get();                    // 空则抛 NoSuchElementException
optional.orElse("default");         // 空则返回默认值
optional.orElseGet(() -> "computed"); // 空则计算（惰性）
optional.orElseThrow();              // 空则抛异常（可自定义）

// 链式调用
optional.map(String::toUpperCase);    // 有值则转换
optional.flatMap(opt -> opt.isEmpty() ? Optional.empty() : ...); // 返回 Optional
optional.filter(s -> s.length() > 3); // 过滤

// ifPresent
optional.ifPresent(v -> System.out.println(v)); // 有值才执行
optional.ifPresentOrElse(v -> {}, () -> {});   // Java 9+，有值/无值分别处理

// stream() - Java 9+
List<String> names = optional.stream()
    .filter(...)
    .collect(Collectors.toList());
```

### 实战应用

```java
// 场景一：方法返回值用 Optional
public Optional<User> findById(Long id) {
    return Optional.ofNullable(userRepository.findById(id));
}

// 场景二：避免 if-null 判断
String city = userRepository.findById(id)
    .map(User::getAddress)
    .map(Address::getCity)
    .map(City::getName)
    .orElse("未知");

// 场景三：默认值
String defaultValue = optional.orElse("N/A");

// 场景四：进阶用法 - Optional 作为方法参数（不推荐滥用）
public void process(Optional<String> name) {
    name.ifPresent(n -> System.out.println(n));
}
```

---

## 四、接口默认方法与静态方法

```java
public interface A {
    // 默认方法：实现类可以不重写
    default void defaultMethod() {
        System.out.println("A 的默认实现");
    }

    // 静态方法：属于接口，不属于实现类
    static void staticMethod() {
        System.out.println("A 的静态方法");
    }
}

public class B implements A {
    // B 可以直接使用默认方法
    // B 也可以重写默认方法
}

public class C implements A {
    @Override
    public void defaultMethod() {
        System.out.println("C 的重写实现");
    }
}
```

---

## 五、新的日期时间 API

```java
// ❌ 旧 API 的问题：线程不安全、API 混乱、时区处理复杂
Date date = new Date();
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd"); // 线程不安全！

// ✅ Java 8 新 API：线程安全、API 清晰、ISO 8601 标准
LocalDate date = LocalDate.now();                    // 2024-01-15
LocalTime time = LocalTime.now();                    // 14:30:00
LocalDateTime dt = LocalDateTime.now();             // 2024-01-15T14:30:00
ZonedDateTime zdt = ZonedDateTime.now();            // 带时区

// 格式化
String formatted = dt.format(DateTimeFormatter.ofPattern("yyyy年MM月dd日 HH:mm:ss"));

// 计算
LocalDate nextWeek = date.plusWeeks(1);
LocalDate lastMonth = date.minusMonths(1);
long daysBetween = java.time.temporal.ChronoUnit.DAYS.between(start, end);

// 解析
LocalDate parsed = LocalDate.parse("2024-01-15");
LocalDate parsed2 = LocalDate.parse("2024/01/15", DateTimeFormatter.ofPattern("yyyy/MM/dd"));

// 时区转换
ZonedDateTime tokyo = ZonedDateTime.of(dt, ZoneId.of("Asia/Tokyo"));
ZonedDateTime utc = tokyo.withZoneSameInstant(ZoneOffset.UTC);

// Duration vs Period
Duration duration = Duration.between(start, end);        // 时间间隔（秒/纳秒）
Period period = Period.between(startDate, endDate);    // 日期间隔（天/月/年）
```

---

## 六、CompletableFuture

```java
// ❌ Future 的局限：无法组合、无法链式调用
Future<String> future = executor.submit(() -> {
    return callRemoteService();
});
String result = future.get(); // 阻塞

// ✅ CompletableFuture：强大的异步编程
public CompletableFuture<String> fetchUser(Long id) {
    return CompletableFuture.supplyAsync(() -> {
        return userRepository.findById(id); // 异步执行
    });
}

// 链式调用
CompletableFuture.supplyAsync(() -> fetchUser(1L))
    .thenApply(User::getName)                        // 转换
    .thenCompose(name -> fetchAddress(name))        // 返回 CompletableFuture 的函数
    .thenCombine(otherFuture, (addr1, addr2) -> ...)// 合并两个
    .exceptionally(ex -> "错误: " + ex.getMessage()) // 异常处理
    .thenAccept(result -> System.out.println(result)); // 最终处理

// 并行执行多个任务
CompletableFuture.allOf(f1, f2, f3).join(); // 等待所有完成
CompletableFuture.anyOf(f1, f2, f3).join(); // 任意一个完成即可

// 超时控制
CompletableFuture.supplyAsync(() -> call())
    .orTimeout(3, TimeUnit.SECONDS)        // 3 秒超时
    .exceptionally(ex -> "默认值");          // 超时后返回
```

---

## 七、Java 11 新特性

### ZGC（低延迟垃圾回收器）

```bash
# 开启 ZGC，停顿时间控制在亚毫秒级
java -XX:+UseZGC -Xmx16g -jar app.jar

# ZGC 的特点：
# 1. 并发执行，大多数阶段和应用线程并发
# 2. 分区管理：小型(≤256KB)、中型(≤4MB)、大型(>4MB)
# 3. 停顿时间不超过 1ms（而 G1 可能达到 100ms+）
```

### String 增强

```java
"  hello  ".isBlank();           // true（空白字符）
"  hello  ".strip();            // "hello"（去除首尾空白）
"  hello  ".stripLeading();     // "hello  "（只去头部）
"  hello  ".stripTrailing();    // "  hello"（只去尾部）
"abc".repeat(3);                // "abcabcabc"
"line1\nline2".lines().count(); // 2，按换行分割
```

### HTTP Client（标准 API）

```java
// Java 11 标准 HTTP Client（取代 HttpURLConnection）
HttpClient client = HttpClient.newHttpClient();

// 同步
HttpResponse<String> response = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/data"))
    .GET()
    .build()
    .send();
System.out.println(response.body());

// 异步
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/data"))
    .POST(HttpRequest.BodyPublishers.ofString(json))
    .build();

client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println);
```

### var 局部类型推断

```java
// Java 10 引入，局部变量可以用 var
var list = new ArrayList<String>();  // 推断为 ArrayList<String>
var stream = list.stream();          // 推断为 Stream<String>
var map = new HashMap<String, Integer>();

// 注意：var 不是关键字，是保留类型名
// 不能用于：字段、方法参数、返回值
```

---

## 八、Java 17 新特性（LTS）

### Records（不可变数据类）

```java
// ❌ 传统的 POJO：大量样板代码
public class Point {
    private final int x;
    private final int y;
    public Point(int x, int y) { this.x = x; this.y = y; }
    public int getX() { return x; }
    public int getY() { return y; }
    // 还要 equals, hashCode, toString...
}

// ✅ Records：自动生成 constructor, getters, equals, hashCode, toString
public record Point(int x, int y) {}

// 自动生成的方法：
// Point(int x, int y) - 构造方法
// int x() / int y()    - getter（不是 getX()）
// equals, hashCode, toString

Point p = new Point(1, 2);
System.out.println(p.x());      // 1
System.out.println(p);          // Point[x=1, y=2]

// 可以添加约束
public record Point(int x, int y) {
    public Point { // 紧凑构造方法
        if (x < 0 || y < 0) throw new IllegalArgumentException();
    }
}

// 可以添加额外方法
public record Point(int x, int y) {
    public double distanceFromOrigin() {
        return Math.sqrt(x * x + y * y);
    }
}
```

### Sealed Classes（密封类）

```java
// 限制类的继承层级：哪些类可以继承，哪些不可以
public sealed class Shape permits Circle, Rectangle, Square {}

// Circle 和 Rectangle 可以是 final、sealed 或 non-sealed
public final class Circle extends Shape { }
public sealed class Rectangle extends Shape permits ColoredRectangle { }
public non-sealed class Square extends Shape { } // 允许被任意类继承

// 使用场景：模式匹配（Java 21 Pattern Matching 更强大）
sealed interface Expr permits NumExpr, AddExpr, VarExpr { }
record NumExpr(int n) implements Expr { }
record AddExpr(Expr left, Expr right) implements Expr { }
record VarExpr(String name) implements Expr { }

String eval(Expr e) {
    return switch (e) {
        case NumExpr(int n) -> String.valueOf(n);
        case AddExpr(var l, var r) -> eval(l) + "+" + eval(r);
        case VarExpr(String name) -> name;
    };
}
```

### Pattern Matching for switch（预览）

```java
// Java 21 正式版
String formatted(Object obj) {
    return switch (obj) {
        case Integer i -> String.format("int %d", i);
        case String s && s.length() > 5 -> "Long string: " + s;
        case String s -> "String: " + s;
        case null, default -> "Other";
    };
}
```

---

## 九、高频面试题

**Q1: Java 8 的 Stream 和 for-each 循环有什么区别？**
> 三个核心区别：① Stream 是内部迭代（Stream 库控制迭代），for-each 是外部迭代（自己控制循环）；② Stream 支持链式操作（filter/map/reduce），代码更简洁；③ Stream 支持并行流（parallelStream），自动利用多核并行处理。for-each 适合简单的遍历和修改集合本身，Stream 适合对数据的转换、过滤、聚合等计算密集型操作。

**Q2: Lambda 表达式的原理是什么？**
> Lambda 表达式在运行时会生成一个对应函数式接口的匿名内部类，或者在 JVM 层面生成 `invokedynamic` 指令。编译时，Lambda 表达式被翻译成 `invokedynamic` 调用点，第一次执行时由 `LambdaMetafactory.metafactory` 生成一个实现了函数式接口的内部类（可能用方法引用或直接执行 Lambda 体）。方法引用比 Lambda 更高效，因为可能直接指向已有的方法而不是生成新的类。

**Q3: Optional 的正确用法和误区？**
> 正确用法：① 作为方法返回值替代 null；② 链式调用替代多层 if-null 判断；③ `orElseGet` 惰性计算默认值。误区：① 不要用 `get()` + `isPresent()`（和 if-null 一样啰嗦）；② 不要把 Optional 作为字段或方法参数（滥用）；③ 不要用 `Optional.of(null)`（会抛 NPE），用 `Optional.ofNullable()`。

**Q4: Java 17 和 Java 8 最大的区别是什么？**
> 核心区别：① **语法层面**：Records（不可变数据类）、Sealed Classes（限制继承）、Pattern Matching（简化 switch）、text blocks；② **性能层面**：ZGC（亚毫秒停顿的 GC）、G1 成为默认 GC、字符串底层优化（UTF-16 → byte[]）；③ **API 层面**：标准 HTTP Client、新的日期时间 API 完善、Files 新增方法；④ **安全层面**：移除 Security Manager、移除 Applet、密封类增强类型安全。

**Q5: CompletableFuture 和 Future 的区别？**
> Future 的局限：只能通过 `get()` 阻塞获取结果，无法组合多个 Future，无法链式调用。CompletableFuture 的优势：① 支持**链式调用**（thenApply/thenCompose/thenCombine）；② 支持**并行组合**（allOf/anyOf）；③ 支持**异常处理**（exceptionally）；④ 支持**超时控制**（orTimeout）；⑤ 支持**手动完成**（complete/experimentally complete exceptionally）。可以完全替代 Future。
