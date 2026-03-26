#!/bin/bash
# 搜索索引定时任务管理脚本

PLIST_NAME="com.yycoder.java-interview.update-search-index"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
SCRIPT_PATH="/Users/yycoder/.qclaw/workspace/java-backend-interview/update_search_index.sh"

show_usage() {
    cat << EOF
搜索索引定时任务管理工具

用法:
    $0 <command>

命令:
    install      安装定时任务(每天早上 6:00 自动执行)
    uninstall    卸载定时任务
    start        立即启动定时任务
    stop         停止定时任务
    status       查看定时任务状态
    run          手动执行一次索引更新
    logs         查看日志
    help         显示此帮助信息

示例:
    $0 install     # 安装定时任务
    $0 run         # 手动执行一次
    $0 logs        # 查看日志
EOF
}

check_root() {
    if [ ! -d "/Users/yycoder/.qclaw/workspace/java-backend-interview" ]; then
        echo "❌ 错误: 项目目录不存在"
        exit 1
    fi
}

install_cron() {
    echo "📦 安装定时任务..."
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo "⚠️  定时任务已存在,先卸载旧任务"
        uninstall_cron
    fi
    
    launchctl load "$PLIST_PATH"
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo "✅ 定时任务安装成功(每天早上 6:00 执行)"
    else
        echo "❌ 定时任务安装失败"
        exit 1
    fi
}

uninstall_cron() {
    echo "🗑️  卸载定时任务..."
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        launchctl unload "$PLIST_PATH"
        echo "✅ 定时任务已卸载"
    else
        echo "ℹ️  定时任务未安装"
    fi
}

start_cron() {
    echo "▶️  启动定时任务..."
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo "ℹ️  定时任务已在运行"
    else
        launchctl load "$PLIST_PATH"
        echo "✅ 定时任务已启动"
    fi
}

stop_cron() {
    echo "⏸️  停止定时任务..."
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        launchctl unload "$PLIST_PATH"
        echo "✅ 定时任务已停止"
    else
        echo "ℹ️  定时任务未运行"
    fi
}

show_status() {
    echo "📊 定时任务状态:"
    echo ""
    
    if launchctl list | grep -q "$PLIST_NAME"; then
        echo "状态: ✅ 运行中"
        echo ""
        launchctl list | grep "$PLIST_NAME"
    else
        echo "状态: ⭕ 未运行"
    fi
    
    echo ""
    echo "📅 定时配置:"
    echo "  执行时间: 每天早上 6:00"
    echo "  脚本路径: $SCRIPT_PATH"
    echo "  配置文件: $PLIST_PATH"
}

run_once() {
    echo "🚀 手动执行索引更新..."
    bash "$SCRIPT_PATH" --force
}

show_logs() {
    LOG_FILE="/Users/yycoder/.qclaw/workspace/java-backend-interview/search_index_update.log"
    STDOUT_LOG="/Users/yycoder/.qclaw/workspace/java-backend-interview/launchd_stdout.log"
    STDERR_LOG="/Users/yycoder/.qclaw/workspace/java-backend-interview/launchd_stderr.log"
    
    echo "📋 最近更新日志:"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        echo "=== 索引更新日志 (最后 20 行) ==="
        tail -20 "$LOG_FILE"
    else
        echo "索引更新日志文件不存在"
    fi
    
    echo ""
    
    if [ -f "$STDOUT_LOG" ]; then
        echo "=== launchd 标准输出 (最后 10 行) ==="
        tail -10 "$STDOUT_LOG"
    fi
    
    echo ""
    
    if [ -f "$STDERR_LOG" ]; then
        echo "=== launchd 错误输出 (最后 10 行) ==="
        tail -10 "$STDERR_LOG"
    fi
}

# 主流程
check_root

case "${1:-help}" in
    install)
        install_cron
        ;;
    uninstall)
        uninstall_cron
        ;;
    start)
        start_cron
        ;;
    stop)
        stop_cron
        ;;
    status)
        show_status
        ;;
    run)
        run_once
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
