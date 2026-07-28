# LOWERTOP Enterprise v3.1 RC4

RC4 在保留 RC3 路由、DNS、策略组和 `FINAL,PROXY` 行为的基础上，重点改进生成配置结构、模块安全审计、Developer Toolkit 和可回滚能力。主配置继续保持稳定，可选增强不会自动启用。

## RC4 主要变化

1. **Apple 天气 QWeather 模块**：基于 NSRingo WeatherKit v3.1.0，API Host 与 Token 通过 Shadowrocket 本地模块参数填写，仓库中不保存真实凭证。
2. **生成器结构修复**：`[Rule]`、`[Script]` 与 `[MITM]` 分段独立校验，避免规则误写入脚本段或遗漏解密主机。
3. **模块安全审计**：CI 检查模块元数据、脚本类型、MITM `%APPEND%`、远程脚本地址和疑似凭证。
4. **Developer Toolkit v0.1**：提供模块静态校验、MITM Hostname 提取与风险检查、Shadowrocket 文本日志分析和最小回归测试。
5. **iCloud 专用代理**：独立 `Apple-iCloud` 规则集默认启用并直接走 `AI` fallback；补齐 Live Photos、iWork、Apple Account 与 2026 年 iCloud 连接检测端点，且不启用 HTTPS 解密。

## 模块目录

```text
modules/optional/
└── AppleWeather.QWeather.RC4.sgmodule
```

模块安装、验证项目和回滚方法见 `releases/v3.1-rc4/MODULES.md`。

哔哩哔哩与百度网盘旧模块已从 RC4 主线移除。后续分别在 `bilibili-next` 与 `baidunetdisk-next` 实验分支中基于最新客户端抓包结果重新开发，不继续修补旧规则。

## 保持不变

- Performance 允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 境外备用 DoH 继续通过 `#proxy`。
- 发布配置关闭 IPv6。
- UDP 策略不支持时使用 `REJECT`，不回落至直连。
- AdvertisingLite 默认启用。
- OpenAI、Telegram、流媒体、中国大陆与最终规则的顺序保持现有行为；iCloud 是 RC4 明确批准的路由变更。

## 构建与验证

```bash
python -m pip install -r requirements.txt
python scripts/ci.py
python scripts/ci.py --online
```

RC4 自动检查包括：

- 单元测试与行为锁；
- DNS、远程规则和冲突审计；
- 脚本配置与模块安全审计；
- 生成配置分段校验；
- API Key 与疑似凭证扫描；
- 设备验证记录和发布报告。

## 发布边界

- Apple 天气模块为手动安装，不自动写入 Direct 主配置。
- iCloud 专用规则默认写入主配置并走 `AI`；Apple Push、App Store、系统更新及中国区 Apple Core 继续直连。
- iCloud 与 Apple Account 域名不得加入 `[MITM]`，避免 Apple 服务因 HTTPS 解密失败。
- 真实 QWeather Token 只能保存在本机参数中；此前公开过的 Token 应先轮换。
- 自动检查不能替代 Apple 天气及 RC4 主配置的真实设备验证。
- 请采用替换导入，不要与旧配置合并。
