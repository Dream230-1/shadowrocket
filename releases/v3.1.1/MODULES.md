# v3.1.1 模块组合与 HTTPS 解密

v3.1.1 主配置无 `[Script]`、无 `[MITM]`。模块规则在主配置规则前按 Shadowrocket 模块列表自上而下首次命中。

## 推荐顺序

1. `iCloud 专用代理优先 v3.1`
2. GMOogway `reject_list`
3. GMOogway `direct_list`
4. `proxy_list` AI 每日转码版
5. APP 启动页去广告 Ultra+
6. 与 Ultra+ 不重叠的审计模块
7. Apple 天气 QWeather

第 4 项包含上游全部规则，只把策略目标从 `PROXY` 改为 `AI`。它会优先于主配置中的 Netflix、Disney、TikTok 等专用策略组；这是 v3.1.1 的明确设计。需要临时换线路时，只修改 `AI` 组所选节点。

## 去广告组合

- 内置 AdvertisingLite 已移除。
- `reject_list` 负责域名级广告拦截，不需要 HTTPS 解密。
- Ultra+ 负责响应改写，需要 HTTPS 解密。
- ADBlock 保持关闭，避免与 `reject_list` 重复。
- Ultra+ 开启时，不要同时开启其已覆盖的哔哩哔哩、百度网盘、微信公众号、微博或 YouTube 专项模块。
- 若停用 Ultra+，可以逐个启用仓库内的窄范围审计模块。

## 路由结果

- `proxy_list` 命中的全部流量：`AI`
- Telegram：`AI`
- YouTube：`AI`
- `mask.icloud.com`、`mask-h2.icloud.com`、`mask-api.icloud.com`：`AI`
- 普通 iCloud 同步：`DIRECT`
- 主配置最终兜底：`FINAL,PROXY`

## HTTPS 解密

只启用 iCloud 优先、`reject_list`、`direct_list` 和 `proxy_list` 时，不需要 HTTPS 解密。

启用 Ultra+、Apple Weather、Netflix 双字幕/评分或其他响应改写模块时：

1. 开启 Shadowrocket HTTPS 解密。
2. 安装并完全信任 Shadowrocket CA。
3. 开启 HTTP/2。
4. 由各模块以 `%APPEND%` 合并 MITM 主机，不在主配置中维护总表。

仓库审计模块不允许 `hostname = *`。Netflix 因动态字幕 CDN 保留唯一例外：

```text
*.oca.nflxvideo.net
```

不要把 iCloud、Apple Account、支付、登录或银行主机手动加入 MITM。

## 回归顺序

1. 替换导入 v3.1.1 主配置。
2. 依次启用 iCloud 优先、`reject_list`、`direct_list`、AI 转码 `proxy_list`。
3. 验证 Telegram、YouTube、OpenAI 和常用海外服务均命中 `AI`。
4. 再启用 Ultra+ 与天气；验证登录、支付、微信、微博、哔哩哔哩和百度网盘。
5. 若使用专项模块，每次只新增一个并观察其账号、收藏、分享和下载功能。

出现异常时先关闭最后启用的响应改写模块，不修改主配置路由。
