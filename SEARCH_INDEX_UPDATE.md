# 搜索索引自动更新功能

## 📋 功能说明

本项目实现了两种自动更新搜索索引的方式:

### 1. Git 钩子 - 提交后自动更新

**位置**: `.git/hooks/post-commit`

**触发时机**: 每次 `git commit` 后自动执行

**工作流程**:
1. 检测本次提交是否包含 `docs/` 目录的变更
2. 如果有变更,自动执行 `generate_search.py` 重新生成索引
3. 如果索引文件有变化,自动提交更新

**优点**: 实时性好,每次提交都能保证索引最新

### 2. 定时任务 - 每天自动更新

**配置文件**: `~/Library/LaunchAgents/com.yycoder.java-interview.update-search-index.plist`

**执行时间**: 每天早上 6:00

**执行脚本**: `update_search_index.sh`

**工作流程**:
1. 检查 `docs/` 目录是否有未提交的变更
2. 如果有变更或使用 `--force` 参数,重新生成索引
3. 记录详细日志到 `search_index_update.log`

**优点**: 无需人工干预,适合长期维护

## 🚀 快速开始

### 安装定时任务

```bash
# 安装定时任务(每天早上 6:00 自动执行)
./cron_manager.sh install

# 查看状态
./cron_manager.sh status
```

### 手动执行更新

```bash
# 方式 1: 使用管理脚本
./cron_manager.sh run

# 方式 2: 直接执行更新脚本
./update_search_index.sh

# 方式 3: 强制更新(即使没有变更)
./update_search_index.sh --force
```

### 查看日志

```bash
./cron_manager.sh logs
```

## 🛠️ 管理命令

使用 `cron_manager.sh` 管理定时任务:

```bash
# 安装定时任务
./cron_manager.sh install

# 卸载定时任务
./cron_manager.sh uninstall

# 启动定时任务
./cron_manager.sh start

# 停止定时任务
./cron_manager.sh stop

# 查看状态
./cron_manager.sh status

# 手动执行一次
./cron_manager.sh run

# 查看日志
./cron_manager.sh logs

# 显示帮助
./cron_manager.sh help
```

## 📝 日志文件

- **索引更新日志**: `search_index_update.log` - 记录每次更新的详细信息
- **launchd 标准输出**: `launchd_stdout.log` - 定时任务的标准输出
- **launchd 错误输出**: `launchd_stderr.log` - 定时任务的错误输出

## 🔧 自定义配置

### 修改定时执行时间

编辑 `~/Library/LaunchAgents/com.yycoder.java-interview.update-search-index.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>  <!-- 修改小时 -->
    <key>Minute</key>
    <integer>0</integer>  <!-- 修改分钟 -->
</dict>
```

修改后需要重新加载:

```bash
./cron_manager.sh uninstall
./cron_manager.sh install
```

### 修改检查间隔

如果想要每小时执行一次,可以修改为:

```xml
<key>StartInterval</key>
<integer>3600</integer>  <!-- 每小时(3600秒)执行一次 -->
```

## 📂 文件说明

```
java-backend-interview/
├── .git/hooks/
│   └── post-commit              # Git 提交后钩子
├── update_search_index.sh       # 定时更新脚本
├── cron_manager.sh              # 定时任务管理工具
├── generate_search.py           # 索引生成脚本(已有)
├── search_index_update.log      # 更新日志(自动生成)
├── launchd_stdout.log           # launchd 标准输出(自动生成)
└── launchd_stderr.log           # launchd 错误输出(自动生成)

~/Library/LaunchAgents/
└── com.yycoder.java-interview.update-search-index.plist  # launchd 配置
```

## ⚠️ 注意事项

1. **Python 依赖**: 需要 Python 3 环境,脚本会自动检查
2. **Git 权限**: Git 钩子需要有执行权限(已设置)
3. **索引提交**: Git 钩子会自动提交索引更新,提交信息包含 `[skip ci]` 标记
4. **首次使用**: 定时任务需要手动安装,不会自动启动

## 🔍 验证功能

### 测试 Git 钩子

```bash
# 修改任意 docs 文件
echo "test" >> docs/test.md

# 提交变更
git add docs/test.md
git commit -m "test: 测试钩子"

# 查看是否有自动提交
git log --oneline -3
```

### 测试定时任务

```bash
# 手动执行一次
./cron_manager.sh run

# 查看日志
./cron_manager.sh logs
```

## 🎯 最佳实践

1. **日常编辑**: Git 钩子会自动处理提交后的索引更新
2. **长期维护**: 定时任务确保即使忘记提交也能保持索引最新
3. **手动控制**: 使用 `cron_manager.sh run` 手动触发更新
4. **监控日志**: 定期查看日志确保功能正常

## 📞 问题排查

### 索引未更新

1. 检查 Python 3 是否安装: `python3 --version`
2. 检查脚本权限: `ls -l update_search_index.sh`
3. 查看错误日志: `./cron_manager.sh logs`

### 定时任务未执行

1. 检查任务状态: `./cron_manager.sh status`
2. 检查配置文件: `cat ~/Library/LaunchAgents/com.yycoder.java-interview.update-search-index.plist`
3. 手动启动: `./cron_manager.sh start`

### Git 钩子未执行

1. 检查钩子权限: `ls -l .git/hooks/post-commit`
2. 确保钩子可执行: `chmod +x .git/hooks/post-commit`
3. 检查钩子脚本内容: `cat .git/hooks/post-commit`
