# miaoli_like · 喵璃の点赞

> 「喵璃」机器人本体的点赞扩展，基于 [Ncatbot](https://github.com/NapNeko/NcatBot) 插件系统。

在聊天中发送 `赞我`，插件会按配置的配额为自己点赞，并把成功次数回复给用户。点赞逐次发送、每次成功调用后间隔 0.5 秒，避免瞬时高频请求。

- 插件名：`miaoli_like`
- 版本：`0.1.1`
- 作者：超可爱乃依
- 入口类：`MiaoLiLike`
- 依赖：无第三方 pip 依赖（仅依赖 NcatBot 运行时）

---

## 目录

- [特性](#特性)
- [目录结构](#目录结构)
- [工作机制](#工作机制)
- [安装](#安装)
- [配置](#配置)
- [数据流](#数据流)
- [模块说明](#模块说明)
- [与其他插件的协作](#与其他插件的协作)
- [已知限制与待办](#已知限制与待办)

---

## 特性

| 特性 | 说明 |
| --- | --- |
| 命令触发 | 注册 `赞我` 命令（`registrar.on_command`，群聊 / 私聊均响应） |
| 事件独占 | 命令以 `priority=100` 注册并在处理器内停止事件传播（`event.data._propagation_stopped = True`），命令事件不再流向下游插件 |
| 配额可配置 | `total_max_likes` 可经插件配置覆盖，默认 50 次 |
| 逐次限速 | 每次成功点赞后 `asyncio.sleep(0.5)`，避免连续调用 |
| 结果统计 | `LikeResult`（dataclass）记录总数与成功数，`fail` 为派生属性 |
| 异常隔离 | `APIError` 静默跳过；其余异常 `logger.exception` 记录后继续循环 |
| 零外部依赖 | `pip_dependencies = []`，随 NcatBot 环境即插即用 |

---

## 目录结构

```text
miaoli_like/
├── __init__.py                # 包标记（空文件）
├── manifest.toml              # 插件元数据清单
├── main.py                    # 插件入口：MiaoLiLike（命令注册、点赞逻辑、生命周期）
└── models/
    ├── __init__.py            # 统一导出模型
    └── runtime/
        ├── __init__.py        # 导出 LikeResult
        └── like_result.py     # LikeResult：点赞统计 dataclass
```

---

## 工作机制

1. 用户在群聊或私聊发送 `赞我`，`registrar.on_command("赞我", priority=100)` 匹配 `message.text`，以较高优先级进入 `on_like_command`，进入后**立即停止事件传播**（0.1.1 起的修复：事件不再下发给其它插件，见[与其他插件的协作](#与其他插件的协作)）。
2. `on_like_command` 调 `smart_like(user_id)` 执行点赞。
3. `smart_like` 循环 `total_max_likes` 次，每次：
   - 调 `send_like(user_id)` → `api.qq.messaging.send_like(user_id=..., times=1)`；
   - 成功后 `asyncio.sleep(0.5)`，随后 `success` 计数 +1；
   - 抛 `APIError` → 静默跳过（暂不写细分逻辑）；
   - 抛其他异常 → `logger.exception` 记录，循环继续。
4. 汇总为 `LikeResult` 返回，`on_like_command` 记录统计日志，并回复 `给杂鱼赞了 {success} 次喵`。

---

## 安装

1. 将本目录放入 ncatbot 的插件目录（如 `plugins/miaoli_like`）。
2. `manifest.toml` 未声明第三方 pip 依赖，无需额外安装（需已有 ncatbot 运行时）。
3. 启动 bot，插件加载后日志输出「喵璃の点赞扩展 已加载」。

---

## 配置

在全局 `config.yaml` 的 `plugin.plugin_configs.miaoli_like` 下覆盖：

```yaml
plugin:
  plugin_configs:
    miaoli_like:
      total_max_likes: 50     # 单次命令的最大点赞次数，默认 50
```

`on_load` 时若 `self.config` 中存在 `total_max_likes`，则覆盖类内默认值。

---

## 数据流

```text
QQ 用户发送「赞我」
        │ ncatbot 命令事件（群 / 私聊），按注册优先级分发
        ▼
registrar.on_command("赞我", priority=100) → MiaoLiLike.on_like_command
        │ event.data._propagation_stopped = True → 下游插件（miaoli_bot）收不到本条消息
        ▼
smart_like(user_id) ── 循环 total_max_likes 次 ──┐
        │                                        │
        │  send_like → api.qq.messaging.send_like(times=1)
        │     ├─ 成功 → sleep(0.5) → success += 1
        │     ├─ APIError → 静默跳过
        │     └─ 其他异常 → logger.exception，继续
        ▼
LikeResult{ total, success, fail }
        │
        ▼
统计日志 + 回复「给杂鱼赞了 N 次喵」
```

---

## 模块说明

### `main.py` · `MiaoLiLike`

| 成员 | 说明 |
| --- | --- |
| `total_max_likes` | 单次命令点赞上限，默认 50，`on_load` 时可由配置覆盖 |
| `send_like(user_id, *, n=1)` | 点赞 `n` 次的薄封装，直接调 `api.qq.messaging.send_like` |
| `smart_like(user_id)` | 循环点赞并汇总 `LikeResult`；逐次限速、异常不中断 |
| `on_like_command(event)` | `赞我` 命令入口：停止事件传播、触发点赞、记录统计日志、回复结果 |
| `on_load` / `on_close` | 生命周期钩子：读取配置、输出加载 / 卸载日志 |

### `models/runtime/like_result.py` · `LikeResult`

| 成员 | 说明 |
| --- | --- |
| `total` | 总次数（= `total_max_likes`） |
| `success` | 成功次数，默认 0 |
| `fail`（property） | `total - success` |
| `add_success(n=1)` | 成功计数累加 |

---

## 与其他插件的协作

本插件与 [miaoli_bot](../miaoli_bot) 共存于同一进程，两者通过 ncatbot 的事件优先级 + 传播停止来分工：

| 插件 | 注册方式 | 作用 |
| --- | --- | --- |
| `miaoli_like`（本插件） | `on_command("赞我", priority=100)` | 抢先接收 `赞我`，处理完停止传播 |
| `miaoli_bot` | `on_message(priority=-100)` | 排在后面；上游已截下的消息不会进入 LLM |

顺序与截断：`赞我` → 本插件（priority=100）先收到 → 置 `event.data._propagation_stopped = True` → 事件不再下发到 `miaoli_bot`，机器人不会把 `赞我` 当普通对话交给 LLM 重复回复；其余消息不受影响，照常到达 `miaoli_bot`。

> 0.1.1 起采用这套分工。此前（0.1.0）命令未抢优先级也未停止传播，私聊发送 `赞我` 会在点赞结果之外**同时触发 `miaoli_bot` 的对话主逻辑**，LLM 又回复一次 —— 现已修复。

---

## 已知限制与待办

- **传播停止依赖框架内部属性**：`event.data._propagation_stopped` 是 ncatbot 事件 data 的私有属性（下划线前缀），当前无公开 API 可替代；升级 ncatbot 后需复核该行为，若失效则命令事件会重新流向下游插件。
- **点赞状态未持久化**：代码中已标记 TODO，后续引入点赞状态持久化。
- **`APIError` 静默跳过**：当前版本不对 API 错误做细分处理（代码注释：暂时不写逻辑 因为用不上），成功统计只计入正常返回的调用。
