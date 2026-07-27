# v3.0 RC3 回归矩阵

## CI 自动闸门

| 类别 | 合格标准 |
|---|---|
| 单元测试 | 全部通过 |
| 配置生成 | Strict、Performance、Experimental 均成功 |
| DNS 审计 | 发布版无系统 DNS 回退、无明文 DNS、IPv6 关闭 |
| 离线回归 | OpenAI、Apple、检测站和 FINAL 首条命中正确 |
| 远程审计 | 固定快照可下载、规则数和语法正常 |
| 漂移审计 | 规则数和字节数未超阈值 |
| 在线回归 | Telegram、流媒体、广告、ChinaMax 命中正确 |
| 广告碰撞 | 关键规则阶段早于 AdvertisingLite |
| 发布 | 生成 Commit 固定的 Direct/Modular 包和校验值 |

## 设备侧必测

1. 家庭 Wi-Fi 标准与扩展 DNSLeakTest。
2. 蜂窝数据标准与扩展 DNSLeakTest。
3. BrowserLeaks IP、WebRTC 和 IPv6。
4. Wi-Fi 与蜂窝切换后重复测试。
5. ChatGPT 连续会话、文件上传和语音。
6. Telegram 图片、视频和大文件。
7. Apple Push、iCloud、App Store 下载。
8. YouTube 高码率播放和常用流媒体登录。
9. 登录、支付、验证码无 AdvertisingLite 误杀。

## Stable 门槛

- CI 连续通过。
- 定时在线审计至少成功一次。
- Performance 设备侧连续使用 72 小时。
- 无本地运营商或路由器 DNS。
- 主力版 IPv6 不可用或 `n/a`。
- 分流命中和广告拦截符合预期。
- 性能不低于 RC2 Performance。
