#!/bin/bash
# 数据收集守护进程启动脚本 (Linux/Mac)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="${PYTHON:-python3}"

# 日志目录
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

# PID文件
PID_FILE="$PROJECT_ROOT/data/collector.pid"

# 日志文件
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/collector_${TIMESTAMP}.log"

start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "守护进程已在运行 (PID: $PID)"
            exit 1
        fi
    fi

    echo "======================================================================"
    echo "启动数据收集守护进程"
    echo "======================================================================"
    echo "Python: $PYTHON"
    echo "日志: $LOG_FILE"
    echo ""

    # 使用nohup后台运行
    nohup $PYTHON "$SCRIPT_DIR/collect_continuous.py" > "$LOG_FILE" 2>&1 &
    PID=$!

    echo $PID > "$PID_FILE"

    echo "✓ 守护进程已启动 (PID: $PID)"
    echo ""
    echo "管理命令:"
    echo "  查看日志: tail -f $LOG_FILE"
    echo "  停止进程: $0 stop"
    echo "  查看状态: $0 status"
    echo ""
    echo "程序将持续运行并每小时自动保存数据"
    echo "======================================================================"
}

stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "未找到运行中的守护进程"
        exit 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        echo "停止守护进程 (PID: $PID)..."
        kill $PID
        sleep 2

        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止..."
            kill -9 $PID
        fi

        rm -f "$PID_FILE"
        echo "✓ 守护进程已停止"
    else
        echo "守护进程未运行 (PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

status_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "守护进程未运行"
        exit 0
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        echo "✓ 守护进程正在运行 (PID: $PID)"

        # 显示最新日志
        LATEST_LOG=$(ls -t "$LOG_DIR"/collector_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo ""
            echo "最新日志: $LATEST_LOG"
            echo "最近10行:"
            echo "----------------------------------------------------------------------"
            tail -10 "$LATEST_LOG"
        fi
    else
        echo "守护进程已停止 (PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        status_daemon
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        echo ""
        echo "命令:"
        echo "  start   - 启动守护进程"
        echo "  stop    - 停止守护进程"
        echo "  restart - 重启守护进程"
        echo "  status  - 查看状态"
        exit 1
        ;;
esac
