---
layout: default
title: 字符串高频算法与面试题 ⭐⭐
---

# 字符串高频算法与面试题 ⭐⭐

> 字符串是面试中出现频率最高的数据类型，本文覆盖所有高频考点

---

## 一、字符串常用技巧

### 1.1 双指针技巧

双指针是处理字符串问题的万能钥匙，主要有两种形式：

**对撞指针（左右夹逼）：**
```java
// 判断回文串
public boolean isPalindrome(String s) {
    int left = 0, right = s.length() - 1;
    while (left < right) {
        if (s.charAt(left) != s.charAt(right)) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}

// 盛水容器（双指针优化版）
public int maxArea(int[] height) {
    int left = 0, right = height.length - 1;
    int max = 0;
    while (left < right) {
        int area = Math.min(height[left], height[right]) * (right - left);
        max = Math.max(max, area);
        if (height[left] < height[right]) {
            left++;
        } else {
            right--;
        }
    }
    return max;
}
```

**快慢指针：**
```java
// 删除倒数第 N 个节点
public ListNode removeNthFromEnd(ListNode head, int n) {
    ListNode fast = head, slow = head;
    for (int i = 0; i < n; i++) {
        fast = fast.next;
    }
    if (fast == null) return head.next; // 删除头节点
    while (fast.next != null) {
        fast = fast.next;
        slow = slow.next;
    }
    slow.next = slow.next.next;
    return head;
}
```

### 1.2 滑动窗口

滑动窗口是处理"子串/子数组"问题的核心技巧：

```java
// 无重复字符的最长子串
public int lengthOfLongestSubstring(String s) {
    Map<Character, Integer> window = new HashMap<>();
    int left = 0, right = 0, maxLen = 0;

    while (right < s.length()) {
        char c = s.charAt(right);
        window.put(c, window.getOrDefault(c, 0) + 1);
        right++;

        // 收缩窗口直到没有重复
        while (window.get(c) > 1) {
            char d = s.charAt(left);
            window.put(d, window.get(d) - 1);
            left++;
        }

        maxLen = Math.max(maxLen, right - left);
    }
    return maxLen;
}

// 最小覆盖子串（LeetCode 76）
public String minWindow(String s, String t) {
    Map<Character, Integer> need = new HashMap<>();
    for (char c : t.toCharArray()) {
        need.put(c, need.getOrDefault(c, 0) + 1);
    }

    Map<Character, Integer> window = new HashMap<>();
    int left = 0, right = 0, valid = 0;
    int start = 0, minLen = Integer.MAX_VALUE;

    while (right < s.length()) {
        char c = s.charAt(right++);
        if (need.containsKey(c)) {
            window.put(c, window.getOrDefault(c, 0) + 1);
            if (window.get(c).equals(need.get(c))) valid++;
        }

        while (valid == need.size()) {
            if (right - left < minLen) {
                start = left;
                minLen = right - left;
            }
            char d = s.charAt(left++);
            if (need.containsKey(d)) {
                if (window.get(d).equals(need.get(d))) valid--;
                window.put(d, window.get(d) - 1);
            }
        }
    }
    return minLen == Integer.MAX_VALUE ? "" : s.substring(start, start + minLen);
}
```

### 1.3 字典（HashMap）技巧

```java
// 字母异位词分组
public List<List<String>> groupAnagrams(String[] strs) {
    Map<String, List<String>> map = new HashMap<>();
    for (String s : strs) {
        char[] chars = s.toCharArray();
        Arrays.sort(chars);  // 排序后作为 key
        String key = new String(chars);
        map.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
    }
    return new ArrayList<>(map.values());
}

// 变位词判断
public boolean isAnagram(String s, String t) {
    if (s.length() != t.length()) return false;
    int[] counter = new int[26];
    for (int i = 0; i < s.length(); i++) {
        counter[s.charAt(i) - 'a']++;
        counter[t.charAt(i) - 'a']--;
    }
    for (int count : counter) {
        if (count != 0) return false;
    }
    return true;
}
```

---

## 二、最长回文子串

### 2.1 中心扩展法 — O(n²)

**核心思想**：回文串关于中心对称，从每个位置向外扩展。

```java
public String longestPalindrome(String s) {
    if (s == null || s.length() < 1) return "";

    int start = 0, end = 0;

    for (int i = 0; i < s.length(); i++) {
        // 奇数长度：中心是一个字符
        int len1 = expandAroundCenter(s, i, i);
        // 偶数长度：中心是两个字符
        int len2 = expandAroundCenter(s, i, i + 1);

        int len = Math.max(len1, len2);
        if (len > end - start + 1) {
            // 计算新起始位置
            start = i - (len - 1) / 2;
            end = i + len / 2;
        }
    }
    return s.substring(start, end + 1);
}

// 从 left 和 right 向外扩展，返回最长回文半径
private int expandAroundCenter(String s, int left, int right) {
    while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
        left--;
        right++;
    }
    return right - left - 1; // 半径长度
}
```

**为什么 `start = i - (len-1)/2`？**
- 奇数：`i` 是中心，`len = 2k+1`，`start = i - k`
- 偶数：中心在 `i` 和 `i+1` 之间，`len = 2k`，`start = i - k + 1`

### 2.2 Manacher 算法 — O(n)

**核心思想**：利用已经计算过的回文信息，加速后续计算。

```java
public String longestPalindromeManacher(String s) {
    // 预处理：将字符串用特殊字符隔开，如 "abc" -> "#a#b#c#"
    String t = "#" + s.replace("", "#") + "#";
    int n = t.length();
    int[] p = new int[n];  // p[i] = 以 i 为中心的回文半径
    int center = 0, right = 0;
    int maxLen = 0, maxCenter = 0;

    for (int i = 0; i < n; i++) {
        // 快速扩展：利用对称性
        if (i < right) {
            p[i] = Math.min(p[2 * center - i], right - i);
        }
        // 尝试扩展
        while (i - p[i] - 1 >= 0 && i + p[i] + 1 < n
                && t.charAt(i - p[i] - 1) == t.charAt(i + p[i] + 1)) {
            p[i]++;
        }
        // 更新 center 和 right
        if (i + p[i] > right) {
            center = i;
            right = i + p[i];
        }
        // 记录最长回文
        if (p[i] > maxLen) {
            maxLen = p[i];
            maxCenter = i;
        }
    }

    // 还原原始字符串
    int start = (maxCenter - maxLen) / 2;
    return s.substring(start, start + maxLen);
}
```

### 2.3 动态规划 — O(n²)

```java
public String longestPalindromeDP(String s) {
    int n = s.length();
    if (n < 2) return s;

    boolean[][] dp = new boolean[n][n];
    int start = 0, maxLen = 1;

    // 所有单字符是回文
    for (int i = 0; i < n; i++) dp[i][i] = true;

    for (int len = 2; len <= n; len++) {
        for (int i = 0; i + len <= n; i++) {
            int j = i + len - 1;
            if (s.charAt(i) == s.charAt(j)) {
                if (len == 2) {
                    dp[i][j] = true;
                } else {
                    dp[i][j] = dp[i + 1][j - 1];
                }
            }
            if (dp[i][j] && len > maxLen) {
                start = i;
                maxLen = len;
            }
        }
    }
    return s.substring(start, start + maxLen);
}
```

**三种方法对比：**
| 方法 | 时间复杂度 | 空间复杂度 | 适用场景 |
|------|-----------|-----------|---------|
| 中心扩展 | O(n²) | O(1) | 面试手写，简单直观 |
| Manacher | O(n) | O(n) | 需要最优解时 |
| 动态规划 | O(n²) | O(n²) | 需记录所有子串状态 |

---

## 三、字符串相乘（高精度乘法）

### 3.1 逐位相乘法 — O(mn)

```java
public String multiply(String num1, String num2) {
    if ("0".equals(num1) || "0".equals(num2)) return "0";

    int m = num1.length(), n = num2.length();
    int[] result = new int[m + n]; // 最多 m+n 位

    // 从右向左逐位相乘
    for (int i = m - 1; i >= 0; i--) {
        for (int j = n - 1; j >= 0; j--) {
            int mul = (num1.charAt(i) - '0') * (num2.charAt(j) - '0');
            int p1 = i + j;     // 高位位置
            int p2 = i + j + 1; // 低位位置
            int sum = mul + result[p2]; // 加上之前的进位

            result[p2] = sum % 10;      // 当前位
            result[p1] += sum / 10;     // 进位到高位
        }
    }

    // 跳过前导零
    StringBuilder sb = new StringBuilder();
    for (int num : result) {
        if (!(sb.length() == 0 && num == 0)) {
            sb.append(num);
        }
    }
    return sb.length() == 0 ? "0" : sb.toString();
}
```

**示例**：`"123" × "456"`

```
    1   2   3    (num1)
  × 4   5   6    (num2)
  ─────────────
    6  12  18     i=2
   5  10  15      i=1
  4   8  12       i=0
  ─────────────
 5  6  0  8  8  ← 结果
```

---

## 四、正则表达式匹配

### 4.1 动态规划 — O(mn)

```java
public boolean isMatch(String s, String p) {
    int m = s.length(), n = p.length();
    boolean[][] dp = new boolean[m + 1][n + 1];

    // 空串匹配空模式
    dp[0][0] = true;

    // 空串匹配带 * 的模式，如 a*, a*b* 等
    for (int j = 2; j <= n; j++) {
        if (p.charAt(j - 1) == '*') {
            dp[0][j] = dp[0][j - 2];
        }
    }

    // 填充 dp 表
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            char pc = p.charAt(j - 1);
            char sc = s.charAt(i - 1);

            if (pc == '*') {
                // * 匹配零个前面的字符
                dp[i][j] = dp[i][j - 2];
                // * 匹配一个或多个前面的字符（前面的字符要匹配当前 s[i-1]）
                if (p.charAt(j - 2) == '.' || p.charAt(j - 2) == sc) {
                    dp[i][j] = dp[i][j] || dp[i - 1][j];
                }
            } else if (pc == '.' || pc == sc) {
                // . 匹配任意字符，或字符相等
                dp[i][j] = dp[i - 1][j - 1];
            }
            // 其他情况默认 false
        }
    }
    return dp[m][n];
}
```

**核心状态转移：**
- `p[j-1] == '*'`：要么跳过 `x*`（`dp[i][j-2]`），要么用 `x*` 多匹配一个字符（`dp[i-1][j]`）
- `p[j-1] == '.'`：匹配任意字符，向前推进
- 字符相等：正常匹配，向前推进

---

## 五、最长公共子串（LCS）

### 5.1 动态规划 — O(mn)

```java
public String longestCommonSubstring(String s1, String s2) {
    int m = s1.length(), n = s2.length();
    int[][] dp = new int[m + 1][n + 1];
    int maxLen = 0, endIndex = 0;

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
                if (dp[i][j] > maxLen) {
                    maxLen = dp[i][j];
                    endIndex = i; // s1 中以 i-1 结尾
                }
            } else {
                dp[i][j] = 0; // 注意：这里必须是 0，不是 max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    return s1.substring(endIndex - maxLen, endIndex);
}
```

**注意**：最长公共**子串**（Substring）的 DP 和最长公共**子序列**（Subsequence）不同：
- 子串：必须连续，`dp[i][j] = 0` 当不匹配时
- 子序列：可以不连续，`dp[i][j] = max(dp[i-1][j], dp[i][j-1])` 当不匹配时

---

## 六、字符串转整数（atoi）

### 6.1 完整实现（边界处理）

```java
public int myAtoi(String s) {
    if (s == null || s.isEmpty()) return 0;

    int i = 0, sign = 1, result = 0, n = s.length();

    // 1. 跳过前导空格
    while (i < n && s.charAt(i) == ' ') i++;

    if (i == n) return 0;

    // 2. 处理符号
    if (s.charAt(i) == '+' || s.charAt(i) == '-') {
        sign = (s.charAt(i++) == '-') ? -1 : 1;
    }

    // 3. 处理数字
    while (i < n && Character.isDigit(s.charAt(i))) {
        int digit = s.charAt(i++) - '0';

        // 4. 越界检查：Integer.MAX_VALUE = 2147483647
        // 关键判断：(result > Integer.MAX_VALUE / 10) 
        //           || (result == Integer.MAX_VALUE / 10 && digit > 7)
        if (result > Integer.MAX_VALUE / 10 ||
           (result == Integer.MAX_VALUE / 10 && digit > 7)) {
            return sign == 1 ? Integer.MAX_VALUE : Integer.MIN_VALUE;
        }

        result = result * 10 + digit;
    }

    return result * sign;
}
```

**边界情况处理：**
- `"  -42"` → `-42`
- `"4193 with words"` → `4193`
- `"words and 987"` → `0`（非空非数字直接返回 0）
- `"91283472332"` → `2147483647`（溢出）
- `"-91283472332"` → `-2147483648`（下溢）

---

## 七、字符串解码

### 7.1 栈解法

```java
public String decodeString(String s) {
    Stack<Integer> countStack = new Stack<>();
    Stack<String> resultStack = new Stack<>();
    String result = "";
    int count = 0;

    for (char c : s.toCharArray()) {
        if (Character.isDigit(c)) {
            count = count * 10 + (c - '0'); // 处理多位数字
        } else if (c == '[') {
            // 入栈：当前结果和数字
            countStack.push(count);
            resultStack.push(result);
            result = "";
            count = 0;
        } else if (c == ']') {
            // 出栈：拼接重复字符串
            String repeat = resultStack.pop();
            int times = countStack.pop();
            StringBuilder sb = new StringBuilder(repeat);
            for (int i = 0; i < times; i++) {
                sb.append(result);
            }
            result = sb.toString();
        } else {
            result += c;
        }
    }
    return result;
}
```

### 7.2 递归解法

```java
public String decodeStringRec(String s) {
    return decodeHelper(s, new int[]{0});
}

private String decodeHelper(String s, int[] index) {
    StringBuilder result = new StringBuilder();
    int num = 0;

    while (index[0] < s.length() && s.charAt(index[0]) != ']') {
        char c = s.charAt(index[0]++);
        if (Character.isDigit(c)) {
            num = num * 10 + (c - '0');
        } else if (c == '[') {
            // 递归处理括号内的内容
            String inner = decodeHelper(s, index);
            // 拼接重复的字符串
            for (int i = 0; i < num; i++) {
                result.append(inner);
            }
            num = 0; // 重置数字
        } else {
            result.append(c);
        }
    }

    if (index[0] < s.length() && s.charAt(index[0]) == ']') {
        index[0]++; // 跳过 ]
    }
    return result.toString();
}
```

**示例**：`"3[a2[c]]"` → `"accaccacc"`

---

## 八、单词搜索（矩阵 DFS）

### 8.1 回溯搜索

```java
public boolean exist(char[][] board, String word) {
    if (board == null || board.length == 0) return false;
    int m = board.length, n = board[0].length;

    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            if (dfs(board, word, i, j, 0)) {
                return true;
            }
        }
    }
    return false;
}

private boolean dfs(char[][] board, String word, int i, int j, int idx) {
    // 全部匹配成功
    if (idx == word.length()) return true;

    // 边界检查 + 字符匹配检查
    if (i < 0 || i >= board.length || j < 0 || j >= board[0].length
            || board[i][j] != word.charAt(idx)) {
        return false;
    }

    // 标记已访问（用特殊字符占位，防止重复访问）
    board[i][j] = '#';

    // 上下左右四个方向搜索
    boolean found = dfs(board, word, i + 1, j, idx + 1)
                  || dfs(board, word, i - 1, j, idx + 1)
                  || dfs(board, word, i, j + 1, idx + 1)
                  || dfs(board, word, i, j - 1, idx + 1);

    // 恢复（回溯）
    board[i][j] = word.charAt(idx);

    return found;
}
```

**优化：剪枝** — 如果当前字符在 board 中出现的次数少于 word 中的次数，直接返回 false。

---

## 九、字符串排列（回溯 + 剪枝）

### 9.1 无重复字符的排列

```java
public List<String> permutation(String s) {
    List<String> result = new ArrayList<>();
    char[] chars = s.toCharArray();
    Arrays.sort(chars); // 排序，便于剪枝
    boolean[] used = new boolean[chars.length];
    StringBuilder path = new StringBuilder();

    dfs(chars, used, path, result);
    return result;
}

private void dfs(char[] chars, boolean[] used, StringBuilder path, List<String> result) {
    if (path.length() == chars.length) {
        result.add(path.toString());
        return;
    }

    for (int i = 0; i < chars.length; i++) {
        // 剪枝：同层相同字符只选第一个
        if (used[i] || (i > 0 && chars[i] == chars[i-1] && !used[i-1])) {
            continue;
        }

        used[i] = true;
        path.append(chars[i]);
        dfs(chars, used, path, result);
        path.deleteCharAt(path.length() - 1); // 回溯
        used[i] = false;
    }
}
```

**剪枝条件**：`i > 0 && chars[i] == chars[i-1] && !used[i-1]`
- `used[i-1] == false`：说明同一层之前用过相同字符（同一层重复）
- 必须先对 `chars` 排序！

---

## 十、LRU 缓存置换

### 10.1 哈希表 + 双向链表

```java
public class LRUCache {
    private class Node {
        int key, value;
        Node prev, next;
        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }

    private Map<Integer, Node> cache = new HashMap<>();
    private Node head, tail;       // 虚拟头尾节点
    private int capacity;

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head = new Node(0, 0);
        tail = new Node(0, 0);
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node node = cache.get(key);
        if (node == null) return -1;
        // 移到链表头部（最近使用）
        moveToHead(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node node = cache.get(key);
        if (node == null) {
            // 新建节点
            node = new Node(key, value);
            cache.put(key, node);
            addToHead(node);
            // 检查容量
            if (cache.size() > capacity) {
                Node removed = removeTail();
                cache.remove(removed.key);
            }
        } else {
            // 更新值
            node.value = value;
            moveToHead(node);
        }
    }

    private void addToHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private void removeNode(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void moveToHead(Node node) {
        removeNode(node);
        addToHead(node);
    }

    private Node removeTail() {
        Node node = tail.prev;
        removeNode(node);
        return node;
    }
}
```

**复杂度分析：**
- `get` / `put`：O(1)
- 哈希表：O(capacity) 空间
- 双向链表：O(capacity) 空间

**核心思想**：哈希表提供 O(1) 查找，双向链表维护访问顺序（头部最新，尾部最旧）。

---

## 十一、KMP 算法

### 11.1 next 数组构建 — O(n)

KMP 的核心是**前缀匹配表（next 数组）**，记录模式串每个位置的最长相等前后缀长度。

```java
public int[] buildNext(String pattern) {
    int n = pattern.length();
    int[] next = new int[n];
    int j = 0; // j = 当前公共前后缀长度

    for (int i = 1; i < n; i++) {
        // 失配时回退
        while (j > 0 && pattern.charAt(i) != pattern.charAt(j)) {
            j = next[j - 1];
        }
        // 匹配，扩展公共前后缀
        if (pattern.charAt(i) == pattern.charAt(j)) {
            j++;
        }
        next[i] = j;
    }
    return next;
}
```

**next 数组含义**：`next[i]` = `pattern[0..i]` 的最长相等前后缀长度（不包括自身）

**示例**：`pattern = "ABABAB"`
```
index:    0  1  2  3  4  5
char:     A  B  A  B  A  B
next:     0  0  1  2  3  4
```

### 11.2 KMP 匹配 — O(n+m)

```java
public int kmpSearch(String text, String pattern) {
    if (pattern.isEmpty()) return 0;
    int[] next = buildNext(pattern);
    int j = 0; // 已匹配的模式串长度

    for (int i = 0; i < text.length(); i++) {
        while (j > 0 && text.charAt(i) != pattern.charAt(j)) {
            j = next[j - 1]; // 失配回退
        }
        if (text.charAt(i) == pattern.charAt(j)) {
            j++;
        }
        if (j == pattern.length()) {
            return i - pattern.length() + 1; // 匹配成功
        }
    }
    return -1;
}
```

**KMP vs 暴力匹配：**
- 暴力：每次失配回退到起始位置下一位，最坏 O(nm)
- KMP：利用已匹配信息，避免回退，最坏 O(n+m)

---

## 十二、Sunday 算法

### 12.1 快速字符串匹配

Sunday 算法在失配时，根据被匹配字符串中"下一个字符"的位置，决定跳跃步数，比 KMP 更简洁，在实践中往往更快。

```java
public int sundaySearch(String text, String pattern) {
    if (pattern.isEmpty()) return 0;
    int n = text.length(), m = pattern.length();

    // 构建偏移表：每个字符最多跳 m+1 步
    Map<Character, Integer> offset = new HashMap<>();
    for (int i = 0; i < 256; i++) {
        offset.put((char) i, m + 1); // 默认跳 m+1
    }
    for (int i = 0; i < m; i++) {
        offset.put(pattern.charAt(i), m - i);
    }

    int i = 0;
    while (i <= n - m) {
        int j = 0;
        while (j < m && text.charAt(i + j) == pattern.charAt(j)) {
            j++;
        }
        if (j == m) return i; // 匹配成功

        // Sunday 跳跃
        if (i + m < n) {
            i += offset.getOrDefault(text.charAt(i + m), m + 1);
        } else {
            break;
        }
    }
    return -1;
}
```

**Sunday vs KMP：**
- Sunday：代码更简单，平均性能更好
- KMP：最坏情况 O(n+m)，更稳定

---

## 十三、面试高频题

### 面试题 1：最长回文子串如何求？有几种方法？

**参考答案：**

三种主流方法：
1. **中心扩展法**（面试首选）：枚举每个位置作为中心，向外扩展找最长回文，O(n²)
2. **Manacher 算法**：最优解 O(n)，面试加分项
3. **动态规划**：dp[i][j] 表示子串 i~j 是否为回文，O(n²)

**中心扩展法实现要点**：
- 每个位置要考虑**奇数长度**（中心是一个字符）和**偶数长度**（中心是两个字符）两种情况
- 用 `expandAroundCenter` 函数从左右两边向外扩展
- 记录最长回文的起始和结束位置

---

### 面试题 2：字符串相乘（大数乘法）如何实现？

**参考答案：**

用数组模拟竖式乘法，按位存储结果：

```java
public String multiply(String num1, String num2) {
    int m = num1.length(), n = num2.length();
    int[] result = new int[m + n];
    for (int i = m - 1; i >= 0; i--) {
        for (int j = n - 1; j >= 0; j--) {
            int mul = (num1.charAt(i) - '0') * (num2.charAt(j) - '0');
            int p1 = i + j, p2 = i + j + 1;
            int sum = mul + result[p2];
            result[p2] = sum % 10;
            result[p1] += sum / 10;
        }
    }
    // 跳过前导零，构建结果字符串
}
```

**关键点**：
- `result[p2]` 存当前位，`result[p1]` 累加进位
- 最后要跳过前导零（但保留唯一的 "0"）
- 可以处理任意长度的大整数乘法

---

### 面试题 3：正则表达式匹配（. 和 *）如何用 DP 实现？

**参考答案：**

定义 `dp[i][j]` = `s[0..i-1]` 与 `p[0..j-1]` 是否匹配：

```java
if (p[j-1] == '*') {
    // 匹配0次：跳过 x*
    dp[i][j] = dp[i][j-2];
    // 匹配>=1次：p[j-2] 必须能匹配 s[i-1]
    if (p[j-2] == '.' || p[j-2] == s[i-1]) {
        dp[i][j] |= dp[i-1][j];
    }
} else if (p[j-1] == '.' || p[j-1] == s[i-1]) {
    dp[i][j] = dp[i-1][j-1];
}
```

**边界**：
- `dp[0][0] = true`（空串匹配空模式）
- `dp[0][j]`：处理 `a*`, `a*b*` 这种可以匹配空串的模式

---

### 面试题 4：LRU 缓存是如何实现的？为什么要用双向链表？

**参考答案：**

**为什么用双向链表？**
- **O(1) 移动节点**：将最近使用的节点移到头部，需要先删除再插入，双向链表支持 O(1) 的 prev/next 操作
- **O(1) 删除最久未使用**：tail.prev 直接指向最旧节点，单链表无法 O(1) 获取前驱
- **O(1) 头部插入**：head.next 直接可插入

**为什么用哈希表？**
- 哈希表提供 O(1) 的 key 查找，直接定位到链表中的节点
- 两者结合：哈希表 O(1) 查找 + 双向链表 O(1) 调整顺序

**Java 内置实现**：`LinkedHashMap` 支持按插入顺序或访问顺序遍历，可以简单实现 LRU：
```java
Map<Integer, Integer> cache = new LinkedHashMap<>(capacity, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > capacity;
    }
};
```

---

### 面试题 5：KMP 算法中的 next 数组是什么意思？如何构建？

**参考答案：**

**next[i] 的含义**：`pattern[0..i]` 这个子串的**最长相等前后缀长度**（不包括整个子串自身）

**构建过程**（模式串 "AAAA" 为例）：
```
模式串: A  A  A  A
index:  0  1  2  3
next:   0  1  2  3
```
- `i=0`：`next[0]=0`（"A" 没有真前后缀）
- `i=1`：前后缀 "A" 匹配，`next[1]=1`
- `i=2`：前后缀 "AA" 匹配，`next[2]=2`
- 失配时回退到 `next[j-1]`

**匹配过程**：主串和模式串匹配失配时，不需要回退主串指针，只需让模式串指针回退到 `next[j-1]` 位置继续匹配。

**KMP 的核心思想**：利用已匹配的信息，避免重复比较。

---

## 十四、总结

字符串高频算法核心要点：

| 算法 | 核心思想 | 时间复杂度 |
|------|---------|-----------|
| 双指针 | 从两端向中间收敛，或快慢指针 | O(n) ~ O(n²) |
| 滑动窗口 | 维护一个可变窗口，求解子串问题 | O(n) |
| 中心扩展 | 枚举回文中心，向外扩展 | O(n²) |
| Manacher | 利用对称性加速回文计算 | O(n) |
| KMP | next 数组避免回退 | O(n+m) |
| DP | 状态定义+转移方程 | O(n²) |
| DFS 回溯 | 枚举所有可能，剪枝优化 | 指数级（指数级可优化） |
| 哈希表+双向链表 | O(1) 查找+O(1) 调整顺序 | O(1) |

**面试技巧**：
1. 先讲暴力解法，再优化
2. 边界条件（空串、越界、溢出）要主动提及
3. 能手写核心代码，不仅仅是讲思路

---

> 📚 **延伸阅读**
> - [LeetCode 字符串专题](https://leetcode.cn/tag/string/)
> - [KMP 算法详解](https://www.ruanyifeng.com/blog/2013/05/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm.html)
> - [Manacher 算法图解](https://zhuanlan.zhihu.com/p/70531999)
> - [滑动窗口模板总结](https://labuladong.gitee.io/algo/)
