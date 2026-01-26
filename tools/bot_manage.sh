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
GREEN='\033[0;32m'
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

    # 启动命令
    nohup ./tools/start_bot.sh > "$LOG_FILE" 2>&1 &
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
    echo "正在停止 Bot (PID: $PID)..."
    kill "$PID"

    # 等待停止
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done

    # 强制停止
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}进程未响应，强制停止...${NC}"
        kill -9 "$PID"
    fi

    rm "$PID_FILE"
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
