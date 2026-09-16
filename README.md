# miaoli_like · 喵璃の点赞

> 「喵璃」机器人本体的点赞扩展，基于 [Ncatbot](https://github.com/NapNeko/NcatBot) 插件系统。

在聊天中发送 `赞我`，插件会按配置的配额为自己点赞，并把成功次数回复给用户。点赞逐次发送、每次成功调用后间隔 0.5 秒，避免瞬时高频请求。

- 插件名：`miaoli_like`
- 版本：`0.1.0`
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
- [已知限制与待办](#已知限制与待办)

---

## 特性

| 特性 | 说明 |
| --- | --- |
| 命令触发 | 注册 `赞我` 命令（`registrar.on_command`，群聊 / 私聊均响应） |
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

1. 用户在群聊或私聊发送 `赞我`，`registrar.on_command("赞我")` 匹配 `message.text`，进入 `on_like_command`。
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
        │ ncatbot 命令事件（群 / 私聊）
        ▼
registrar.on_command("赞我") → MiaoLiLike.on_like_command
        │
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
| `on_like_command(event)` | `赞我` 命令入口：触发点赞、记录统计日志、回复结果 |
| `on_load` / `on_close` | 生命周期钩子：读取配置、输出加载 / 卸载日志 |

### `models/runtime/like_result.py` · `LikeResult`

| 成员 | 说明 |
| --- | --- |
| `total` | 总次数（= `total_max_likes`） |
| `success` | 成功次数，默认 0 |
| `fail`（property） | `total - success` |
| `add_success(n=1)` | 成功计数累加 |

---

## 已知限制与待办

- **点赞状态未持久化**：代码中已标记 TODO，后续引入点赞状态持久化。
- **`APIError` 静默跳过**：当前版本不对 API 错误做细分处理（代码注释：暂时不写逻辑 因为用不上），成功统计只计入正常返回的调用。
