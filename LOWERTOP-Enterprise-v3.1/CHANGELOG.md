# CHANGELOG

## 3.1.0-rc4

### Added

- 独立的哔哩哔哩 JSON/gRPC 结构化去广告模块，覆盖开屏、信息流、搜索、动态、视频相关推荐、直播推广和评论区广告。
- 百度网盘保守实验模块，仅拦截已识别推广接口。
- Apple 天气 QWeather 参数化模块，基于 NSRingo WeatherKit v3.1.0。
- Shadowrocket 当前出口 IP 质量检测模块。
- RC4 模块安全审计与公开仓库凭证扫描。
- 生成配置 `[Rule]`、`[Script]`、`[MITM]` 分段规范化与校验。

### Changed

- 哔哩哔哩、百度网盘和 Apple 天气由主配置自动注入改为独立模块，默认不启用。
- 自维护脚本 URL 切换至 `release/v3.1-rc4`。
- 功能开关区分“模块已提供”和“默认启用”。

### Removed

- 删除会对播放、推荐、搜索和评论接口整段返回空 JSON 的旧 `bilibili_full.js`。
- 删除哔哩哔哩会员状态伪造逻辑。
- 删除过宽的 `DOMAIN-KEYWORD,baidustatic` 拦截。

### Release gates

- 哔哩哔哩需完成首页、播放页、评论、搜索、直播和登录回归。
- 百度网盘需完成登录、下载、分享和在线播放回归，验证前保持 Experimental。
- Apple 天气真实 API Token 不得进入 Git 历史。
- 稳定版前将 BiliUniverse 运行包从 `latest` 固定至已验证版本。

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
