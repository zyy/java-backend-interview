# 搜索索引更新 - 快速参考

## 🎯 三种更新方式

### 1️⃣ 自动更新(Git 钩子)
```bash
# 每次提交自动触发,无需手动操作
git commit -m "更新文档"
```

### 2️⃣ 定时更新(每天 6:00)
```bash
# 安装定时任务(首次需要)
./cron_manager.sh install

# 查看状态
./cron_manager.sh status
```

### 3️⃣ 手动更新
```bash
# 方式 1: 管理脚本
./cron_manager.sh run

# 方式 2: 直接执行
./update_search_index.sh

# 方式 3: 强制更新
./update_search_index.sh --force
```

## 📊 常用命令

| 命令 | 说明 |
|------|------|
| `./cron_manager.sh install` | 安装定时任务 |
| `./cron_manager.sh status` | 查看状态 |
| `./cron_manager.sh run` | 手动执行 |
| `./cron_manager.sh logs` | 查看日志 |
| `./cron_manager.sh help` | 查看帮助 |

## 📁 关键文件

- **索引生成脚本**: `generate_search.py`
- **定时更新脚本**: `update_search_index.sh`
- **管理工具**: `cron_manager.sh`
- **更新日志**: `search_index_update.log`
- **详细文档**: `SEARCH_INDEX_UPDATE.md`

## ✅ 验证功能

```bash
# 测试定时任务
./cron_manager.sh run
./cron_manager.sh logs

# 测试 Git 钩子
echo "test" >> docs/test.md
git add docs/test.md
git commit -m "test: 测试钩子"
git log --oneline -3
```
