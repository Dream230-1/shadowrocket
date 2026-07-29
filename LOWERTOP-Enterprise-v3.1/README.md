# LOWERTOP Enterprise v3.1

v3.1 以 RC4 实机验证结果为发布基线，保留稳定的路由、DNS、策略组和 `FINAL,PROXY` 行为。规则型 AdvertisingLite 默认启用；需要响应体改写或 HTTPS 解密的增强继续作为可选模块。

## 主要变化

1. **Apple 天气 QWeather 模块**：基于 NSRingo WeatherKit v3.1.0，API Host 与 Token 通过 Shadowrocket 本地模块参数填写，仓库中不保存真实凭证。
2. **生成器结构修复**：`[Rule]`、`[Script]` 与 `[MITM]` 分段独立校验，避免规则误写入脚本段或遗漏解密主机。
3. **模块安全审计**：CI 检查模块元数据、脚本类型、MITM `%APPEND%`、远程脚本地址和疑似凭证。
4. **Developer Toolkit v0.1**：提供模块静态校验、MITM Hostname 提取与风险检查、Shadowrocket 文本日志分析和最小回归测试。
5. **iCloud 分层分流**：普通 iCloud 同步及 Apple Account 保持 `DIRECT`；仅专用代理 `mask*` 精确端点优先走 `AI` fallback，且不启用 HTTPS 解密。
6. **最小 MITM**：默认主配置移除闲鱼 MITM 去广告脚本；只有启用 Apple 天气等响应改写模块时才需要 HTTPS 解密。

## 模块目录

```text
modules/optional/
├── AppleWeather.QWeather.v3.1.sgmodule
└── iCloud.PrivateRelay.Priority.v3.1.sgmodule
```

模块安装、顺序、HTTPS 解密边界和回滚方法见 `releases/v3.1/MODULES.md`。

哔哩哔哩与百度网盘旧模块不进入 v3.1 正式版。后续分别在 `bilibili-next` 与 `baidunetdisk-next` 实验分支中基于最新客户端抓包结果重新开发。

## 保持不变

- Performance 允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 境外备用 DoH 继续通过 `#proxy`。
- 发布配置关闭 IPv6。
- UDP 策略不支持时使用 `REJECT`，不回落至直连。
- AdvertisingLite 默认启用。
- OpenAI、Telegram、流媒体、中国大陆与最终规则的顺序保持现有行为；iCloud 分层路由为 v3.1 已批准变更。

## 构建与验证

```bash
python -m pip install -r requirements.txt
python scripts/ci.py
python scripts/ci.py --online
```

v3.1 自动检查包括：

- 单元测试与行为锁；
- DNS、远程规则和冲突审计；
- 脚本配置与模块安全审计；
- 生成配置分段校验；
- API Key 与疑似凭证扫描；
- 设备验证记录和发布报告。

## 发布边界

- Apple 天气模块为手动安装，不自动写入 Direct 主配置。
- iCloud 同步规则默认写入主配置并保持 `DIRECT`；仅专用代理 `mask*` 端点走 `AI`。
- iCloud 与 Apple Account 域名不得加入 `[MITM]`，避免 Apple 服务因 HTTPS 解密失败。
- 真实 QWeather Token 只能保存在本机参数中；此前公开过的 Token 应先轮换。
- 自动检查不能替代 Apple 天气及主配置的真实设备验证。
- 请采用替换导入，不要与旧配置合并。
