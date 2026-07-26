# CHANGELOG

## 3.1.0-rc2

### Added

- RC1 Performance 语义行为锁和可审计契约。
- V3.1 完整离线/在线审计执行链。
- Apple Global/Core 负向断言与域名边界回归矩阵。
- AI、Apple、通信、媒体、游戏、广告和基础路由模块声明。
- 全局跨策略规则冲突与遮蔽检测。
- 带原因、负责人和过期时间的冲突 allowlist。
- ETag/Last-Modified 条件缓存、304 复用、原子更新与 stale-if-error。
- Wi-Fi、蜂窝、网络切换设备测试模板。
- AdvertisingLite 72 小时误杀观察模板。
- 发布验证 JSON/Markdown 报告生成器。
- Direct 与 Modular 两类构建产物。

### Fixed

- 修复 V3.1 RC1 `--online` 只打印“继承 RC3 审计”却不实际运行审计脚本的问题。
- 修复 V3.1 功能开关只声明、不接入执行链的问题。
- 补齐 V3.1 自维护规则、回归输入和报告输出。

### Preserved

- Performance 的 QUIC/HTTP3。
- 系统 DNS 回退禁用。
- 境外备用 DoH 通过 `#proxy`。
- 发布版 IPv6 关闭。
- UDP 不支持时 `REJECT`。
- AdvertisingLite 默认启用。
- RC1 的策略组、路由顺序与 FINAL 行为。

### Experimental only

- IPv6 与 HTTPS/SVCB。
- 潜在 ECH 协商观察；不宣称强制 ECH。

### Deferred

- 未经 Shadowrocket 实测确认的 DoQ/DoH3/DoH/DoT 严格协议回退。
- 自动改写终端 DNS 的动态健康选优。
- 游戏模块默认启用与新游戏分流。

## 3.1.0-rc1

- 分层 `config/release.yaml`、`dns.yaml` 与 `features.yaml`。
- V3.1 兼容层生成器，复用已验证的 RC3 构建内核。
- Performance 网络参数与 AdvertisingLite 默认策略保持不变。
