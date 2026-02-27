# memectl 自动创建虚拟环境与依赖完善设计

Date: 2026-02-27
Status: Approved

## 1. 背景与问题

当前 `tools/memectl` 会按顺序解析 Python 解释器：`.venv/bin/python` -> `venv/bin/python` -> `python3`。当项目虚拟环境不存在时会回退到系统 Python，容易出现系统包与项目包混用，导致版本漂移告警（例如 `requests` 与 `urllib3/chardet` 不匹配）。

同时，`requirements.txt` 存在“直接依赖未显式声明”问题（如 `eth-account`），增加了环境不可预期性。

## 2. 目标

1. 在无虚拟环境时，`memectl` 自动创建 `.venv`。
2. 自动安装依赖，避免“创建了环境但首次运行缺包”的冷启动失败。
3. 采用幂等策略：仅在首次创建或 `requirements.txt` 变更时安装依赖。
4. 完善 `requirements.txt` 的关键依赖声明，降低版本漂移与兼容风险。

## 3. 非目标

1. 不引入 Poetry/Pipenv 等新包管理器。
2. 不新增 setup 向导命令。
3. 不改变 `memectl` CLI 形态（`./tools/memectl <service> <action>`）。

## 4. 方案选择

### 备选方案

- A. 自动创建 + 按需安装（首次创建或 requirements 变化触发）
- B. 自动创建 + 每次 start 都安装
- C. 只自动创建，不自动安装

### 结论

采用 **A**：兼顾稳定性与启动速度，避免每次启动都重复联网安装。

## 5. 架构与职责

### 5.1 `tools/memectl`

入口与子命令保持不变，仍通过 `require_python_bin` 获取运行解释器。`start_service` 不直接处理依赖逻辑。

### 5.2 `tools/lib/python_env.sh`

将环境生命周期集中在该模块：

1. 发现现有虚拟环境：优先 `.venv`，其次 `venv`。
2. 若都不存在：自动创建 `.venv`。
3. 依赖安装判定：
   - 首次创建虚拟环境时安装；
   - 或 `requirements.txt` 的 hash 与上次安装记录不一致时安装。
4. 安装成功后记录当前 hash（例如 `.venv/.requirements.sha256`）。
5. 返回最终解释器路径给调用方。

## 6. 详细流程

当执行 `./tools/memectl bot start` / `collector start`：

1. `require_python_bin` 检测 `.venv` / `venv`。
2. 若无环境，调用 `python3 -m venv .venv` 创建。
3. 读取 `requirements.txt` 并计算 SHA256。
4. 对比 `.venv/.requirements.sha256`：
   - 不存在或不一致 -> 执行 `python -m pip install -r requirements.txt`；
   - 一致 -> 跳过安装。
5. 记录新 hash。
6. 返回解释器路径并启动服务。

## 7. 错误处理与可观测性

1. 若系统无 `python3`，直接 fail-fast，提示无法创建虚拟环境。
2. 若 `requirements.txt` 缺失或安装失败，终止启动，避免半初始化状态。
3. 对自动动作打印明确日志：
   - “未检测到虚拟环境，正在创建 .venv”
   - “检测到 requirements 变更，正在安装依赖”
   - “依赖已是最新，跳过安装”

## 8. requirements.txt 完善策略（运行时 + 训练范围）

基于代码导入审计，`requirements.txt` 变更如下：

1. **新增直接依赖（必加）**
   - `eth-account>=0.10,<0.14`

2. **新增关键网络依赖（显式治理）**
   - `requests>=2.31,<3`
   - `urllib3>=2.2,<3`

3. **暂不新增**
   - `chardet`（当前无直接使用，避免无效膨胀）

## 9. 兼容性与权衡

1. 优先 `.venv`，兼容已有 `venv`，降低迁移成本。
2. 不强制每次启动安装依赖，减少启动延迟与外网抖动影响。
3. 显式声明网络关键依赖会提高可控性，但也需要后续按节奏升级版本上界。

## 10. 验证计划

1. 删除 `.venv` 后执行 `./tools/memectl collector start`：应自动创建并安装依赖，服务成功启动。
2. 再次 `start`（或 `restart`）：应跳过安装并正常启动。
3. 修改 `requirements.txt` 后 `restart`：应触发重新安装。
4. `collector logs -f` 不再出现由系统 Python 混装引发的 `RequestsDependencyWarning`。
5. `bot` 与 `collector` 流程一致通过。

## 11. 实施边界

仅修改：

- `tools/lib/python_env.sh`
- `requirements.txt`

必要时仅在 `tools/memectl` 做最小调用适配，不改变 CLI 接口。