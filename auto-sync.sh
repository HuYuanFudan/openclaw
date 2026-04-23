#!/bin/bash
# OpenClaw 自动同步脚本
# 监控文件变化并自动推送到 GitHub

REPO_DIR="/home/huyuan/openclaw"
LOG_FILE="/tmp/openclaw-auto-sync.log"
LOCK_FILE="/tmp/openclaw-auto-sync.lock"

# 防止重复运行
if [ -f "$LOCK_FILE" ]; then
    echo "脚本已在运行中 (PID: $(cat $LOCK_FILE))"
    exit 1
fi
echo $$ > "$LOCK_FILE"

# 清理函数
cleanup() {
    rm -f "$LOCK_FILE"
    exit 0
}
trap cleanup EXIT INT TERM

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 进入仓库目录
cd "$REPO_DIR" || exit 1

log "开始监控 $REPO_DIR 的文件变化..."

# 检查是否有未推送的更改并推送
sync_to_github() {
    cd "$REPO_DIR" || return

    # 检查是否有变更
    if [ -z "$(git status --porcelain)" ]; then
        return
    fi

    log "检测到文件变化，正在同步..."

    # 添加所有变更
    git add -A

    # 提交变更（使用时间戳作为提交信息）
    git commit -m "auto sync: $(date '+%Y-%m-%d %H:%M:%S')"

    # 推送到 GitHub
    if git push origin main; then
        log "✅ 同步成功"
    else
        log "❌ 同步失败"
    fi
}

# 如果有 inotifywait，使用实时监控
if command -v inotifywait &> /dev/null; then
    log "使用 inotifywait 实时监控..."

    # 先同步一次现有变更
    sync_to_github

    # 持续监控
    while true; do
        inotifywait -r -e modify,create,delete,move \
            --exclude '\.git/' \
            --exclude '\.pyc' \
            --exclude '__pycache__/' \
            --exclude 'node_modules/' \
            --exclude '\.log$' \
            "$REPO_DIR" 2>/dev/null

        # 等待几秒聚合多次变更
        sleep 5
        sync_to_github
    done
else
    log "inotifywait 未安装，使用轮询模式 (每 60 秒检查一次)..."
    log "建议安装: sudo apt install inotify-tools (Ubuntu/Debian) 或 sudo yum install inotify-tools (CentOS/RHEL)"

    while true; do
        sync_to_github
        sleep 60
    done
fi
