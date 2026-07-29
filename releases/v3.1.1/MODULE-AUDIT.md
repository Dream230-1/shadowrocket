# v3.1.1 模块审计清单

审计日期：2026-07-29。机器可读源为 `LOWERTOP-Enterprise-v3.1/config/module-audit.yaml`。

| 模块 | 来源与固定提交 | MITM 主机 | 冲突/边界 |
|---|---|---|---|
| iCloud 专用代理优先 | Dream230-1/shadowrocket `1aa01d21eee532f9f7391d4d684dee90f663c482` | 无 | 必须位于 `direct_list` 上方 |
| Apple Weather QWeather | NSRingo/WeatherKit `348dc2a30dc2407d2bbd88d00cfd93a9f911a3c6`；本地冻结运行包 `0c2941d8a438d7e78ba71a1a5ed58366926c5369` | `weatherkit.apple.com` | 不与其他天气响应改写模块叠加 |
| 微信公众号去广告 | NobyDa/Script `7f8b309f8d943806b90c6ff25d8b8aa0c59b0c03` | `mp.weixin.qq.com` | 与 Ultra+ 微信改写冲突 |
| 微博去广告 | zmqcherish/proxy-script `1d9f51bc9a0077d81998bb503ee6158ca83faa73` | `api.weibo.cn`、`mapi.weibo.com`、两个精确 UVE 主机 | 与 Ultra+ 微博改写冲突 |
| YouTube 信息流去广告 | app2smile/rules `df6366a7024e0b3f0aa3510c5b791eea6f3cba89` | `youtubei.googleapis.com` | 与 Ultra+ YouTube 改写冲突 |
| Netflix 双字幕/评分 | DualSubs/Universal `14fdcecdaaaf8e2b80c74a6bfc2bb0890da0775e`；yichahucha/surge `06d6e36771880959c008d3c59c192068f00ddd51` | `ios.prod.ftl.netflix.com`、`*.oca.nflxvideo.net` | 不与其他 Netflix 字幕或评分模块叠加 |
| 哔哩哔哩纯去广告 | app2smile 端点参考 `df6366a7024e0b3f0aa3510c5b791eea6f3cba89`；本地实现 `0c2941d8a438d7e78ba71a1a5ed58366926c5369` | `app.bilibili.com` | 与 Ultra+、旧全量改写模块冲突；当前设备抓包验证待完成 |
| 百度网盘纯去广告 | 旧端点审计 `e28ff3d7ce0d628820df2322e4f4ac7c64bacc1e`；本地实现 `0c2941d8a438d7e78ba71a1a5ed58366926c5369` | `pan.baidu.com` | 与 Ultra+、会员解锁模块冲突；当前设备抓包验证待完成 |

## 强制审计规则

- 所有 `script-path` 必须使用 `raw.githubusercontent.com` 和 40 位提交 SHA。
- 禁止 `main`、`master`、GitHub `blob`、`releases/latest` 与 `latest/download`。
- 禁止未登记 MITM 通配符；Netflix CDN 是当前唯一登记例外。
- 禁止会员/VIP 解锁模块和支付、登录、账号类 MITM 主机。
- 禁止跨模块重复 MITM 主机。
- 哔哩哔哩脚本模式禁止包含 VIP、收藏、账号、评论或播放端点。
- 百度网盘脚本模式禁止包含登录、账号、会员、分享、下载、文件列表或传输端点。

静态审计通过不等于当前 App 版本实机通过。哔哩哔哩与百度网盘在取得当前设备抓包前保持候选状态。
