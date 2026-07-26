# V3.1 RC2 测试矩阵

## 自动化硬闸门

| 类别 | 合格标准 |
|---|---|
| 单元测试 | RC3 内核与 V3.1 RC2 测试全部通过 |
| 配置生成 | Strict、Performance、Experimental、Direct、Modular 成功 |
| 行为锁 | RC2 Performance 与 RC1 语义契约完全一致 |
| DNS 审计 | 无系统回退、无明文 DNS、主力 IPv6 关闭、UDP 不直连回落 |
| Apple 负向回归 | Global/Core 正向、禁止策略、伪装域名和边界用例全部通过 |
| 离线回归 | OpenAI、Apple、检测站和 FINAL 首条命中正确 |
| 远程审计 | 固定 Commit 可下载、规则数和语法正常 |
| 漂移审计 | 规则数和字节变化未越阈值 |
| 在线回归 | Telegram、流媒体、广告、ChinaMax 命中正确 |
| 全局冲突 | 无未登记的高风险跨策略遮蔽；allowlist 未过期 |
| 广告碰撞 | 关键业务规则先于 AdvertisingLite |
| 条件缓存 | 首次下载、缓存命中/304、损坏与离线行为正确 |
| 发布报告 | Commit、配置 SHA、自动结果和实机证据状态完整 |

## Wi-Fi 设备测试

1. 标准与扩展 DNSLeakTest。
2. BrowserLeaks IP、WebRTC 与 IPv6。
3. Apple Push、iCloud、Apple ID、App Store 下载。
4. ChatGPT 连续会话、文件上传与语音。
5. Telegram 图片、视频和大文件。
6. YouTube 高码率与常用流媒体登录/DRM。
7. 记录节点、运营商/ISP、设备/iOS/Shadowrocket 版本和配置 SHA。

模板：`validation/device/wifi/TEMPLATE.yaml`。

## 蜂窝设备测试

执行与 Wi-Fi 相同的检查，并记录运营商、无线制式、CGNAT/IPv6 情况。

模板：`validation/device/cellular/TEMPLATE.yaml`。

## 网络切换测试

至少完成：

1. Wi-Fi → 蜂窝，保持 ChatGPT 活跃会话；
2. 蜂窝 → Wi-Fi，保持 Telegram 文件传输；
3. App Store 下载中切换；
4. 切换后立即重复 DNS、IP 和 WebRTC；
5. 记录隧道恢复时间、会话是否存活和是否出现瞬时直连。

模板：`validation/device/switching/TEMPLATE.yaml`。

## AdvertisingLite 72 小时观察

主动覆盖登录注册、验证码、支付、内购、推送、地图定位、分享/深链、银行电商、流媒体 DRM、ChatGPT、Apple ID/iCloud/App Store。

合格条件：

- 连续观察不少于 72 小时；
- 未解决 P0/P1 为 0；
- 每个疑似误杀有关闭广告规则后的对照结果；
- 处理结论与证据进入记录。

模板：`validation/adblock/TEMPLATE-72H.yaml`。

## RC2 发布门槛

- 自动化硬闸门全部通过；
- Wi-Fi、蜂窝、切换三类真实记录全部通过；
- AdvertisingLite 72 小时观察通过；
- `RELEASE-VALIDATION.md` 显示 `RC2 可发布: PASS`；
- 保留可回滚的 RC1 Performance 配置及 SHA。
