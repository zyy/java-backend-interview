---
layout: default
title: 如何实现大文件分片上传与断点续传？⭐⭐⭐
---
# 如何实现大文件分片上传与断点续传？

## 🎯 面试题：大文件上传怎么做？断点续传原理是什么？

---

## 一、痛点分析

```
普通单次上传的问题：
  ❌ 文件太大（几个 GB），HTTP 超时中断
  ❌ 网络波动后重新上传，已上传部分丢失
  ❌ 服务器内存压力大
  ❌ 无法并发加速
  ❌ 无法增量更新

解决方案：
  ✅ 分片上传：切成多个小块，各自独立上传
  ✅ 断点续传：记录已上传分片，中断后可从断点继续
  ✅ 秒传：服务端已有相同文件，直接返回成功
```

---

## 二、整体架构

```
┌────────────────────────────────────────────────────────────┐
│                    分片上传完整流程                          │
│                                                            │
│  前端：计算文件 MD5                                         │
│        ↓                                                   │
│  查后端秒传接口 → 已存在？→ 秒传成功 ✅                       │
│        ↓ 不存在                                            │
│  获取 uploadId（全局唯一上传会话）                           │
│        ↓                                                   │
│  前端：按 2MB/片分片，并发上传（如 3 路并发）                 │
│        ↓                                                   │
│  每个分片独立请求 POST /upload/chunk                        │
│        ↓                                                   │
│  服务端：存储分片文件，记录已上传分片列表                      │
│        ↓                                                   │
│  所有分片上传完成 → 通知合并                                 │
│        ↓                                                   │
│  服务端：按分片顺序合并为完整文件                             │
│        ↓                                                   │
│  校验 MD5，匹配则上传成功                                   │
└────────────────────────────────────────────────────────────┘
```

---

## 三、服务端实现

### 1. 分片上传接口

```java
@RestController
@Slf4j
public class FileUploadController {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    @Autowired
    private FileStorageService fileStorageService;

    private static final String CHUNKS_DIR = "/data/upload-chunks/";
    private static final long MAX_CHUNK_SIZE = 5 * 1024 * 1024L; // 5MB

    /**
     * Step 1: 初始化上传会话
     * 返回 uploadId，后续所有请求都带上这个 ID
     */
    @PostMapping("/upload/init")
    public Result<UploadInitVO> initUpload(@RequestBody UploadInitRequest req) {
        // 1. 校验文件大小、类型
        validateFile(req.getFileName(), req.getFileSize());

        // 2. 生成全局唯一 uploadId
        String uploadId = UUID.randomUUID().toString().replace("-", "");

        // 3. 记录上传会话（Redis，24 小时过期）
        String sessionKey = "upload:session:" + uploadId;
        Map<String, String> session = new HashMap<>();
        session.put("fileName", req.getFileName());
        session.put("fileSize", String.valueOf(req.getFileSize()));
        session.put("md5", req.getFileMd5());
        session.put("totalChunks", String.valueOf(req.getTotalChunks()));
        session.put("createTime", String.valueOf(System.currentTimeMillis()));
        redisTemplate.opsForHash().putAll(sessionKey, session);
        redisTemplate.expire(sessionKey, 24, TimeUnit.HOURS);

        // 4. 创建分片存储目录
        Path chunkDir = Paths.get(CHUNKS_DIR + uploadId);
        try { Files.createDirectories(chunkDir); } catch (IOException e) { /* ignore */ }

        log.info("[Upload] Init: uploadId={}, file={}, size={}, chunks={}",
            uploadId, req.getFileName(), req.getFileSize(), req.getTotalChunks());

        return Result.success(new UploadInitVO(uploadId, MAX_CHUNK_SIZE));
    }

    /**
     * Step 2: 秒传检查（MD5 命中直接成功）
     */
    @PostMapping("/upload/check")
    public Result<CheckVO> checkUpload(@RequestBody CheckRequest req) {
        String md5 = req.getMd5();
        String filePath = fileStorageService.getFilePathByMd5(md5);

        if (filePath != null) {
            // 秒传成功
            return Result.success(new CheckVO(true, null, "秒传成功"));
        }

        // 返回 uploadId 和已上传分片（断点续传）
        String uploadId = findActiveUploadId(md5, req.getFileName());
        Set<Integer> uploadedChunks = getUploadedChunks(uploadId);

        return Result.success(new CheckVO(false, uploadId, uploadedChunks));
    }

    /**
     * Step 3: 上传单个分片
     */
    @PostMapping("/upload/chunk")
    public Result uploadChunk(
            @RequestParam("file") MultipartFile chunk,
            @RequestParam("uploadId") String uploadId,
            @RequestParam("chunkIndex") int chunkIndex,
            @RequestParam("totalChunks") int totalChunks
    ) {
        // 1. 校验上传会话
        String sessionKey = "upload:session:" + uploadId;
        if (Boolean.FALSE.equals(redisTemplate.hasKey(sessionKey))) {
            return Result.error("上传会话不存在或已过期");
        }

        // 2. 校验分片序号
        int total = Integer.parseInt(
            (String) redisTemplate.opsForHash().get(sessionKey, "totalChunks"));
        if (chunkIndex < 0 || chunkIndex >= total) {
            return Result.error("分片序号非法");
        }

        // 3. 写入分片文件
        Path chunkPath = Paths.get(CHUNKS_DIR + uploadId + "/chunk_" + chunkIndex);
        try {
            Files.createDirectories(chunkPath.getParent());
            chunk.transferTo(chunkPath.toFile());
        } catch (IOException e) {
            log.error("[Upload] Failed to save chunk: {}", chunkPath, e);
            return Result.error("保存分片失败");
        }

        // 4. 记录分片已上传
        String chunksKey = "upload:" + uploadId + ":chunks";
        redisTemplate.opsForSet().add(chunksKey, String.valueOf(chunkIndex));
        redisTemplate.expire(chunksKey, 24, TimeUnit.HOURS);

        // 5. 检查是否全部上传完成
        long uploadedCount = redisTemplate.opsForSet().size(chunksKey);
        if (uploadedCount == totalChunks) {
            // 异步合并
            CompletableFuture.runAsync(() -> mergeChunks(uploadId, totalChunks));
        }

        log.info("[Upload] Chunk uploaded: uploadId={}, chunk={}/{}",
            uploadId, chunkIndex + 1, totalChunks);

        return Result.success(Map.of(
            "uploaded", uploadedCount,
            "total", totalChunks,
            "progress", String.format("%.1f%%", uploadedCount * 100.0 / totalChunks)
        ));
    }

    /**
     * Step 4: 合并分片
     */
    @PostMapping("/upload/merge")
    public Result mergeUpload(@RequestParam String uploadId) {
        String sessionKey = "upload:session:" + uploadId;
        Map<Object, Object> session = redisTemplate.opsForHash().entries(sessionKey);
        if (session.isEmpty()) {
            return Result.error("上传会话不存在");
        }

        int totalChunks = Integer.parseInt((String) session.get("totalChunks"));
        String fileMd5 = (String) session.get("md5");
        String fileName = (String) session.get("fileName");

        // 检查所有分片是否齐全
        Set<String> chunks = redisTemplate.opsForSet()
            .members("upload:" + uploadId + ":chunks");
        if (chunks.size() != totalChunks) {
            return Result.error("分片不完整，已上传 " + chunks.size() + "/" + totalChunks);
        }

        // 执行合并
        String finalPath = fileStorageService.mergeChunks(
            CHUNKS_DIR + uploadId,
            totalChunks,
            fileName,
            fileMd5
        );

        // 清理临时文件
        cleanup(uploadId);

        return Result.success(Map.of("filePath", finalPath, "md5", fileMd5));
    }
}
```

### 2. 分片合并逻辑

```java
@Service
@Slf4j
public class FileStorageService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * 按分片顺序合并文件
     */
    public String mergeChunks(String chunkDir, int totalChunks,
                              String fileName, String md5) {
        // 1. 目标文件路径
        String filePath = "/data/uploads/" + md5 + "_" + fileName;
        File outFile = new File(filePath);
        outFile.getParentFile().mkdirs();

        try (OutputStream out = new BufferedOutputStream(
                new FileOutputStream(outFile), 8 * 1024 * 1024)) { // 8MB buffer

            for (int i = 0; i < totalChunks; i++) {
                Path chunkPath = Paths.get(chunkDir + "/chunk_" + i);
                if (!Files.exists(chunkPath)) {
                    throw new IllegalStateException("分片缺失: " + i);
                }
                Files.copy(chunkPath, out);
                Files.deleteIfExists(chunkPath); // 及时删除已合并的分片
            }
        } catch (IOException e) {
            throw new RuntimeException("合并失败: " + e.getMessage(), e);
        }

        // 2. MD5 校验
        String computedMd5 = DigestUtils.md5Hex(new FileInputStream(outFile));
        if (!computedMd5.equalsIgnoreCase(md5)) {
            outFile.delete();
            throw new IllegalStateException("MD5 校验失败，上传过程中文件被篡改");
        }

        // 3. 注册文件（MD5 → 文件路径映射）
        String key = "file:md5:" + md5;
        redisTemplate.opsForValue().set(key, filePath);
        // 同时写 DB
        fileMapper.insert(new FileDO(md5, filePath, fileName, new Date()));

        log.info("[FileStorage] Merged: {} -> {}", chunkDir, filePath);
        return filePath;
    }

    public String getFilePathByMd5(String md5) {
        return redisTemplate.opsForValue().get("file:md5:" + md5);
    }
}
```

---

## 四、前端实现

```javascript
// 分片上传核心逻辑（前端）
class ChunkUploader {
  constructor(file, options = {}) {
    this.file = file;
    this.chunkSize = options.chunkSize || 2 * 1024 * 1024; // 2MB
    this.concurrency = options.concurrency || 3; // 并发数
    this.uploadedChunks = new Set(); // 已上传的分片索引
    this.uploadId = null;
  }

  // 计算整个文件的 MD5（用于秒传）
  async calcFileMD5() {
    const spark = new SparkMD5.ArrayBuffer();
    const reader = new FileReader();
    const step = 10 * 1024 * 1024; // 每次读 10MB

    return new Promise((resolve, reject) => {
      let offset = 0;
      const loadNext = () => {
        const slice = this.file.slice(offset, offset + step);
        reader.readAsArrayBuffer(slice);
        reader.onload = e => {
          spark.append(e.target.result);
          offset += step;
          if (offset < this.file.size) loadNext();
          else resolve(spark.end());
        };
        reader.onerror = reject;
      };
      loadNext();
    });
  }

  // 秒传检查
  async checkInstant() {
    const md5 = await this.calcFileMD5();
    const res = await api.post('/upload/check', {
      md5,
      fileName: this.file.name,
      fileSize: this.file.size
    });
    return { md5, ...res.data };
  }

  // 获取已上传分片（断点续传）
  async getUploadedChunks(uploadId) {
    const res = await api.post('/upload/check', {
      md5: await this.calcFileMD5(),
      fileName: this.file.name,
      fileSize: this.file.size
    });
    return res.data.uploadedChunks || [];
  }

  // 上传单个分片
  async uploadChunk(index, uploadId) {
    const start = index * this.chunkSize;
    const end = Math.min(start + this.chunkSize, this.file.size);
    const chunk = this.file.slice(start, end);

    const formData = new FormData();
    formData.append('file', chunk);
    formData.append('uploadId', uploadId);
    formData.append('chunkIndex', index);
    formData.append('totalChunks', this.totalChunks);

    await api.post('/upload/chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }

  // 并发控制上传
  async uploadAll() {
    const md5Result = await this.checkInstant();
    if (md5Result.exists) {
      console.log('秒传成功');
      return { success: true, instant: true };
    }

    // 初始化上传会话
    this.totalChunks = Math.ceil(this.file.size / this.chunkSize);
    this.uploadId = md5Result.uploadId;
    if (!this.uploadId) {
      const initRes = await api.post('/upload/init', {
        fileName: this.file.name,
        fileSize: this.file.size,
        fileMd5: md5Result.md5,
        totalChunks: this.totalChunks
      });
      this.uploadId = initRes.data.uploadId;
    }

    // 断点续传：获取已上传分片
    const uploadedChunks = await this.getUploadedChunks(this.uploadId);
    uploadedChunks.forEach(i => this.uploadedChunks.add(i));

    // 构建所有分片任务
    const tasks = [];
    for (let i = 0; i < this.totalChunks; i++) {
      if (!this.uploadedChunks.has(i)) {
        tasks.push(i);
      }
    }

    // 并发控制
    let running = 0;
    const results = [];
    return new Promise((resolve) => {
      const run = () => {
        while (running < this.concurrency && tasks.length > 0) {
          const index = tasks.shift();
          running++;
          this.uploadChunk(index, this.uploadId)
            .then(() => {
              this.uploadedChunks.add(index);
              this.onProgress(this.uploadedChunks.size, this.totalChunks);
            })
            .catch(err => tasks.push(index)) // 失败重试
            .finally(() => { running--; run(); });
        }
        if (running === 0 && tasks.length === 0) {
          // 全部完成，通知服务端合并
          this.notifyMerge();
          resolve({ success: true });
        }
      };
      run();
    });
  }

  async notifyMerge() {
    await api.post('/upload/merge', { uploadId: this.uploadId });
  }

  onProgress(uploaded, total) {
    const pct = ((uploaded / total) * 100).toFixed(1);
    document.getElementById('progress').textContent = `${pct}%`;
  }
}
```

---

## 五、断点续传原理

```
实现关键点：
  1. 服务端记录每个 uploadId 已上传的分片列表
  2. 前端每次上传前，先查服务端已上传分片
  3. 只上传缺失的分片，已上传的跳过

暂停/恢复：
  前端维护一个本地记录（localStorage）：
    { uploadId, uploadedChunks: [0,1,2,4,5], totalChunks: 10 }

  刷新页面后：
    1. 拿 localStorage 的 uploadId 查服务端已上传分片
    2. 比对本地记录和服务端记录，取并集
    3. 从缺失分片继续上传
```

---

## 六、高频面试题

**Q1: 秒传的原理是什么？**
> 服务端按文件内容 MD5 存文件映射：MD5 → 文件路径。上传前先计算文件 MD5 查服务端，存在则说明文件已上传过，直接关联用户即可，无需再传数据。

**Q2: 分片上传如何保证文件完整性？**
> ① 前端计算文件整体 MD5；② 每个分片上传时带分片序号和总分片数；③ 所有分片上传完成后，服务端按序号顺序合并；④ 合并后再次计算 MD5，与前端传的值比对，匹配则成功。

**Q3: 并发上传多个分片时，分片丢失怎么处理？**
> 合并前检查所有分片是否齐全（Redis Set 记录已上传分片数量）。发现分片缺失时前端重试缺失的分片。合并操作只有在所有分片齐全后才执行。

**Q4: 分片上传如何限流？**
> ① 服务端限流：令牌桶限制整体上传带宽；② 客户端并发数控制（默认 3 路）；③ 服务端按 userId + uploadId 限流，防止单个用户过度占用资源。

---

**参考链接：**
- [Spring Boot 大文件分片上传实现](https://juejin.cn/post/689500)
- [Web Uploader 前端分片上传组件](https://github.com/fex-team/webuploader)
