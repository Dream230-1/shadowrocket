# v3.1 第三方模块在线审计

审计日期：2026-07-29。

本报告区分语法可解析、内容边界可接受和适合默认开启。通过静态审计不等同于通过当前 App 版本的实机回归。

## 推荐组合

| 模块 | 结论 | HTTPS 解密 |
|---|---|---|
| iCloud 专用代理优先 v3.1 | 开启，必须位于 `direct_list` 上方 | 不需要 |
| GMOogway `direct_list` | 可开启，用于中国大陆域名优先直连 | 不需要 |
| 微信公众号去广告 审计版 | 可开启，只改写公众号广告接口 | `mp.weixin.qq.com` |
| 微博去广告 审计精简版 | 可开启，已删除皮肤改写并收缩主机 | 4 个精确微博主机 |
| Netflix 评分增强 审计版 | 可选开启，存在片名与 IMDb ID 的第三方查询 | `ios.prod.ftl.netflix.com` |
| Apple 天气增强 QWeather v3.1 | 开启，已完成实机验证 | `weatherkit.apple.com` |
| YouTube 信息流去广告 审计版 | 已审计，但按当前组合关闭 | `youtubei.googleapis.com` |

## 不进入推荐组合

| 截图模块 | 审计事实 | 结论 |
|---|---|---|
| GMOogway `proxy_list` | 27,139 条规则会提前命中 YouTube、Telegram、OpenAI、Netflix 等域名；主配置本身已是 `FINAL,PROXY` | 关闭，功能冗余且破坏专用策略 |
| GMOogway `reject_list` | 170,031 条规则与内置 AdvertisingLite 重复，并包含 Apple、Netflix、OpenAI 等遥测或服务域名 | 默认关闭，继续使用已通过观察的内置 AdvertisingLite |
| iFansClub ADBlock | 截图无法提供下载 URL，无法证明实际内容；同名公开 ADBlock 版本包含约 153 个 MITM 主机 | 关闭 |
| APP 启动页去广告 Ultra+ | 当前公开版本约 2,746 行，MITM 覆盖数百主机，包括银行、支付、运营商和大量业务 API | 关闭，不做全局精简修补 |
| 百度网盘去广告 RC4.2 Experimental | 截图中的文件不在 v3.1 仓库或已发布实验分支，缺少可复现来源 | 关闭，待提供模块信息页 URL |
| 4 in 1 | 只重定向特定 Google 搜索词，却解密 `www.google.com` | 关闭 |
| iFansClub YouTube | 截图无法提供下载 URL | 关闭；需要时使用仓库内审计版替代 |
| 番茄小说 | 含 `DOMAIN-SUFFIX,bytedance.com,REJECT` 及多个过宽 MITM 通配符 | 关闭，可能阻断正常内容、登录或推送 |
| 旧哔哩哔哩模块 | 15 条响应脚本覆盖动态、账户、推荐等接口，且已有收藏功能异常证据 | 关闭，等待 `bilibili-next` 实机重建 |
| 天气提醒 | 脚本含共享的明文 `appid/appsecret`，且与 Apple 天气增强重复 | 关闭 |
| 美图秀秀、扫描全能王、医考帮 | 属于会员或权限状态改写，不属于 v3.1 网络分流及去广告边界 | 不纳入正式版 |

## 固定上游

- GMOogway/shadowrocket-rules：`096416961d62ffd2aec50d23030bc1c99ca5855d`
- deezertidal/shadowrocket-rules：`7fad8dc2c42b168dc1cbebf18b1591fc39579b9d`
- NobyDa/Script：`7f8b309f8d943806b90c6ff25d8b8aa0c59b0c03`
- zmqcherish/proxy-script：`1d9f51bc9a0077d81998bb503ee6158ca83faa73`
- yichahucha/surge：`06d6e36771880959c008d3c59c192068f00ddd51`
- app2smile/rules：`df6366a7024e0b3f0aa3510c5b791eea6f3cba89`

仓库内审计模块的 `script-path` 均固定到以上不可变提交，不使用 `main`、`master` 或 `latest`。
