# CHANGELOG

## 3.1.0

### Released

- 冻结 RC4 已验证的 DNS、策略组、路由顺序、iCloud 分层分流和 `FINAL,PROXY` 行为。
- AdvertisingLite 与明确广告域名继续作为默认规则型拦截。
- Apple 天气 QWeather 与 iCloud 专用代理优先模块更新为 v3.1 正式版。
- 新增外部 `direct_list`、`reject_list`、`proxy_list`、ADBlock、启动页去广告与 YouTube 去广告的启用边界和顺序说明。

### Security

- 从默认主配置移除闲鱼 MITM 去广告脚本及 `market.wapa.taobao.com` 解密主机。
- 核心配置不再要求 HTTPS 解密；Apple 天气仅解密 `weatherkit.apple.com`。
- iCloud、Apple Account、支付及登录域名不得加入 MITM。

### Compatibility

- `direct_list` 可继续用于优先直连，但 `iCloud 专用代理优先 v3.1` 必须位于其上方。
- 通用 `proxy_list` 不作为默认模块，避免抢先覆盖 YouTube 等专用策略组。
- 重复启用 AdvertisingLite、`reject_list` 和 ADBlock 会扩大误杀面，正式版建议只选择一层通用广告规则。

## 3.1.0-rc4

### Added

- Apple 天气 QWeather 参数化模块，基于 NSRingo WeatherKit v3.1.0。
- Developer Toolkit v0.1：模块静态校验、MITM Hostname 提取、日志分析和最小回归测试。
- Developer Toolkit v0.2 alpha：模块与主配置覆盖冲突审计及 JSON 报告。
- RC4 模块安全审计与公开仓库凭证扫描。
- 生成配置 `[Rule]`、`[Script]`、`[MITM]` 分段规范化与校验。
- iCloud 专用 AI 分流，覆盖 Drive、照片、备份、CloudKit、Live Photos、iWork、连接检测与 Apple Account 认证端点。

### Changed

- Apple 天气由主配置自动注入改为独立模块，默认不启用。
- 自维护脚本 URL 切换至 `release/v3.1-rc4`。
- RC4 模块审计收缩为仅校验仍属主线的 Apple 天气模块。
- RC4 实机证据与发布报告收缩为仅要求 Apple 天气模块，不再引用已冻结或移除的模块。
- GitHub Actions 切换至 Node 24 运行时的 Checkout、Setup Python、Cache 与 Artifact 主版本。
- 移除未再使用的 `iCloud` 选择组；普通 `Apple-iCloud` 同步固定 `DIRECT`，仅专用代理 `mask*` 精确端点走 `AI` fallback。

### Removed

- 从 RC4 主线移除哔哩哔哩与百度网盘旧模块；后续分别在 `bilibili-next`、`baidunetdisk-next` 基于最新客户端抓包结果重新开发。
- 删除会对播放、推荐、搜索和评论接口整段返回空 JSON 的旧 `bilibili_full.js`。
- 删除哔哩哔哩会员状态伪造逻辑。
- 删除过宽的 `DOMAIN-KEYWORD,baidustatic` 拦截。
- 移除缺乏可靠节点切换触发与手动触发机制的当前出口 IP 质量模块方案。

### Release gates

- Apple 天气真实 API Token 不得进入 Git 历史。
- 完成 RC4 Wi-Fi、蜂窝及双向切换验证。
- 完成 AdvertisingLite 连续至少 72 小时误杀观察。
- 完成 Apple 天气当前、小时、每日、降水和空气质量实机验证。

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
