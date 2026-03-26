#!/bin/bash
# 定时更新搜索索引脚本
# 可配合 cron 或 launchd 使用

set -e

REPO_ROOT="/Users/yycoder/.qclaw/workspace/java-backend-interview"
DOCS_DIR="$REPO_ROOT/docs"
INDEX_SCRIPT="$REPO_ROOT/generate_search.py"
INDEX_FILE="$DOCS_DIR/search_index.json"
LOG_FILE="$REPO_ROOT/search_index_update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查是否有未提交的 docs 文件变更
check_changes() {
    cd "$REPO_ROOT"
    
    # 检查是否有未跟踪的文件
    UNTRACKED=$(git ls-files --others --exclude-standard docs/)
    
    # 检查是否有已修改但未提交的文件
    MODIFIED=$(git diff --name-only docs/)
    
    # 检查是否有已暂存但未提交的文件
    STAGED=$(git diff --cached --name-only docs/)
    
    if [ -n "$UNTRACKED" ] || [ -n "$MODIFIED" ] || [ -n "$STAGED" ]; then
        log "检测到 docs 目录有以下变更:"
        [ -n "$UNTRACKED" ] && log "  未跟踪: $UNTRACKED"
        [ -n "$MODIFIED" ] && log "  已修改: $MODIFIED"
        [ -n "$STAGED" ] && log "  已暂存: $STAGED"
        return 0
    else
        log "未检测到 docs 目录变更"
        return 1
    fi
}

# 更新搜索索引
update_index() {
    log "开始更新搜索索引..."
    
    if [ ! -f "$INDEX_SCRIPT" ]; then
        log "❌ 错误: 索引生成脚本不存在: $INDEX_SCRIPT"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log "❌ 错误: Python3 未安装"
        exit 1
    fi
    
    cd "$REPO_ROOT"
    
    # 记录索引文件修改时间
    OLD_MTIME=$(stat -f "%m" "$INDEX_FILE" 2>/dev/null || echo "0")
    
    # 执行索引生成脚本
    if python3 "$INDEX_SCRIPT" >> "$LOG_FILE" 2>&1; then
        NEW_MTIME=$(stat -f "%m" "$INDEX_FILE" 2>/dev/null || echo "0")
        
        if [ "$OLD_MTIME" != "$NEW_MTIME" ]; then
            log "✅ 搜索索引更新成功"
        else
            log "ℹ️  搜索索引无变更"
        fi
    else
        log "❌ 搜索索引更新失败"
        exit 1
    fi
}

# 主流程
main() {
    log "========== 开始执行定时索引更新 =========="
    
    if check_changes || [ "$1" == "--force" ]; then
        update_index
    else
        log "跳过索引更新"
    fi
    
    log "========== 执行完成 =========="
    log ""
}

# 支持强制更新参数
main "$@"
