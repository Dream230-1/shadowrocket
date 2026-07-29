# v3.1 模块组合与 HTTPS 解密

v3.1 正式主配置保持无 `[Script]`、无 `[MITM]`。功能增强全部作为独立模块启用和回滚。

## 当前推荐开启顺序

1. `iCloud 专用代理优先 v3.1`
2. GMOogway `direct_list`
3. `微信公众号去广告 审计版 v3.1`
4. `微博去广告 审计精简版 v3.1`
5. `Netflix 评分增强 审计版 v3.1`
6. `Apple 天气增强 QWeather v3.1`

YouTube 与 ADBlock 按当前方案关闭。脚本模块之间没有路由优先级关系，但保持以上固定顺序便于排障。

## 必须关闭

- `proxy_list`：主配置已使用 `FINAL,PROXY`，该模块没有额外兜底价值，反而会提前覆盖 YouTube、Telegram、OpenAI、Netflix 等专用策略。
- `reject_list`：与正式版内置 AdvertisingLite 重复，扩大误杀面。
- iFansClub ADBlock：未取得截图中实际下载 URL，不能证明内容。
- APP 启动页去广告 Ultra+：MITM 范围包含银行、支付、运营商和大量业务 API。
- `4 in 1`：为搜索跳转而解密 `www.google.com`，收益与风险不匹配。
- 番茄小说、旧哔哩哔哩、天气提醒：分别存在过宽阻断、功能接口改写或共享明文凭证问题。
- 百度网盘 RC4.2 Experimental：缺少截图对应的可复现模块 URL。
- 美图秀秀、扫描全能王、医考帮：不属于正式版网络分流和去广告边界。

完整证据见 `MODULE-AUDIT.md`。

## 模块链接

### iCloud 专用代理优先

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/iCloud.PrivateRelay.Priority.v3.1.sgmodule
```

该模块只包含三个精确 `mask* → AI` 规则，不含脚本或 MITM。必须位于 `direct_list` 上方。

### 微信公众号去广告

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/WeChat.OfficialAccounts.NoAds.v3.1.sgmodule
```

只处理 `mp.weixin.qq.com/mp/getappmsgad`，不会解密微信登录、支付或聊天接口。

### 微博去广告

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/Weibo.NoAds.v3.1.sgmodule
```

只保留信息流及开屏广告处理。上游的非会员皮肤改写已删除，MITM 通配符已改为精确主机。

### Netflix 评分增强

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/Netflix.Ratings.v3.1.sgmodule
```

该模块不解锁 Netflix。它会将片名发送给 OMDb，并将 IMDb ID 发送给豆瓣搜索以获取评分。

### Apple 天气增强

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/AppleWeather.QWeather.v3.1.sgmodule
```

Token 只在 Shadowrocket 本机模块参数中填写。免费凭证不支持昨日空气质量时，将两项 `AirQuality.Comparison.Yesterday.*` 改为 `WeatherKit`。

### YouTube 信息流去广告

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/YouTube.NoAds.v3.1.sgmodule
```

当前保持关闭。该模块只过滤首页和推荐列表广告，不处理视频贴片广告。

## HTTPS 解密

使用当前推荐组合时必须开启 HTTPS 解密、完全信任 Shadowrocket CA，并开启 HTTP/2。模块均使用 `%APPEND%` 合并主机。

最终最小主机集合为：

```text
weatherkit.apple.com
mp.weixin.qq.com
api.weibo.cn
mapi.weibo.com
sdkapp.uve.weibo.com
wbapp.uve.weibo.com
ios.prod.ftl.netflix.com
```

如果关闭某个模块，应同时从手动 MITM 列表删除该模块对应主机。若以后单独开启 YouTube 审计版，再追加：

```text
youtubei.googleapis.com
```

禁止加入：

- `hostname = *` 或泛 Apple、Google、微信、微博通配符
- iCloud、Apple Account、支付、登录及银行主机

## 回归顺序

1. 先验证 iCloud 同步、Private Relay、App Store、推送和 Apple 天气。
2. 再验证微信文章、聊天、支付，确认只有公众号底部广告被处理。
3. 再验证微博登录、收藏、评论、私信、视频和推送。
4. 最后验证 Netflix 登录、DRM、字幕、播放和评分显示。

出现异常时，从最后启用的脚本模块开始逐个关闭，不修改主配置规则。
