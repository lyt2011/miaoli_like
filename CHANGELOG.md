# Changelog

本项目所有重要变更均记录在此。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循语义化版本（[SemVer](https://semver.org/lang/zh-CN/)）。

## [0.1.1] - 2026-09-17

### Fixed
- **私聊发送 `赞我` 会同时触发 `miaoli_bot` 的对话主逻辑**（`main.py`）：命令以默认优先级注册且未停止事件传播，事件会继续下发给 `miaoli_bot` 的 `on_message`，导致本插件回复点赞结果的同时 LLM 又当作普通对话回复一次。现改为 `@registrar.on_command("赞我", priority=100)` 并在处理器内 `event.data._propagation_stopped = True`，命令事件不再流向下游插件

### Note
- `_propagation_stopped` 是 ncatbot 事件 data 的私有属性（下划线前缀），当前无公开 API 可替代；升级 ncatbot 后需复核该行为
- 已手动验证：`赞我` 由本插件独占响应，下游插件不再处理

## [0.1.0] - 2026-09-16

### Added
- 初始版本：`赞我` 命令按配额点赞（默认 50 次，可由插件配置 `total_max_likes` 覆盖），逐次 `asyncio.sleep(0.5)` 限速，`LikeResult` 统计成功数，`APIError` 静默跳过、其余异常记录日志后继续
