#!/bin/bash
# MemeBot 管理脚本
# 用法: ./bot_manage.sh {start|stop|restart|status|log}

# 配置
APP_NAME="src.trader.bot"
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
LOG_FILE="${PROJECT_ROOT}/logs/bot.log"
PID_FILE="${PROJECT_ROOT}/logs/bot.pid"

# 颜色
RED='\033[0;31m'

YELLOW='\033[1;33m'
NC='\033[0m'

cd "$PROJECT_ROOT"

# 检查是否运行中
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0 # Running
        else
            return 1 # PID file exists but process dead
        fi
    else
        # Fallback: check by process name
        PID=$(pgrep -f "$APP_NAME")
        if [ -n "$PID" ]; then
            echo "$PID" > "$PID_FILE"
            return 0
        fi
        return 2 # Not running
    fi
}

start() {
    check_status
    STATUS=$?
    if [ $STATUS -eq 0 ]; then
        echo -e "${YELLOW}Bot 已经在运行中 (PID: $(cat $PID_FILE))${NC}"
        return
    fi

    echo "正在启动 MemeBot..."

    # 确保日志目录存在
    mkdir -p logs

    # 激活虚拟环境
    if [ -d "${PROJECT_ROOT}/.venv" ]; then
        source "${PROJECT_ROOT}/.venv/bin/activate"
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        source "${PROJECT_ROOT}/venv/bin/activate"
    fi

    # 启动 Bot（-u 禁用输出缓冲，PYTHONPATH 内联传递确保 nohup 子进程继承）
    nohup env PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}" python -u -m ${APP_NAME} > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "$PID" > "$PID_FILE"

    sleep 2
    check_status
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}启动成功! PID: $PID${NC}"
        echo "日志文件: $LOG_FILE"
    else
        echo -e "${RED}启动失败! 请检查日志:${NC}"
        tail -n 10 "$LOG_FILE"
    fi
}

stop() {
    check_status
    STATUS=$?
    if [ $STATUS -ne 0 ]; then
        echo -e "${YELLOW}Bot 未运行${NC}"
        [ -f "$PID_FILE" ] && rm "$PID_FILE"
        return
    fi

    PID=$(cat "$PID_FILE")

    # 第一步: 发送 SIGINT (Ctrl+C) 触发 Python cleanup（卖出持仓+保存状态）
    echo "正在停止 Bot (PID: $PID)..."
    echo "  → 发送 SIGINT，等待清仓..."
    kill -2 "$PID" 2>/dev/null

    # 等待 cleanup 完成（卖出持仓可能需要30秒以上）
    WAIT_SECS=60
    for i in $(seq 1 $WAIT_SECS); do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        # 每10秒显示进度
        if [ $((i % 10)) -eq 0 ]; then
            echo "  → 等待清仓中... (${i}/${WAIT_SECS}s)"
        fi
        sleep 1
    done

    # 第二步: 如果还在运行，发 SIGTERM
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}  → Cleanup 超时，发送 SIGTERM...${NC}"
        kill "$PID" 2>/dev/null
        sleep 5
    fi

    # 第三步: 最后手段 SIGKILL
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${RED}  → 进程未响应，强制终止 (SIGKILL)${NC}"
        kill -9 "$PID" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}Bot 已停止${NC}"
}

status() {
    check_status
    STATUS=$?
    if [ $STATUS -eq 0 ]; then
        PID=$(cat "$PID_FILE")
        # 获取运行时间等信息
        UPTIME=$(ps -o etime= -p "$PID" | tr -d ' ')
        MEM=$(ps -o pmem= -p "$PID" | tr -d ' ')
        echo -e "${GREEN}● Bot 正在运行${NC}"
        echo "PID:      $PID"
        echo "运行时长: $UPTIME"
        echo "内存占用: $MEM%"
        echo ""
        echo "最新日志:"
        tail -n 5 "$LOG_FILE"
    else
        echo -e "${RED}● Bot 未运行${NC}"
    fi
}

log() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "日志文件不存在"
        return
    fi
    echo "正在查看日志 (Ctrl+C 退出)..."
    tail -f "$LOG_FILE"
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 3
        start
        ;;
    status)
        status
        ;;
    log)
        log
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac
