# v3.1 模块启用与 HTTPS 解密边界

## 推荐顺序

1. `iCloud 专用代理优先 v3.1`
2. `direct_list`
3. 通用广告规则仅选择一个：`reject_list`、ADBlock 或核心内置 AdvertisingLite
4. APP 启动页去广告 Ultra+
5. YouTube 去广告
6. Apple 天气增强 QWeather v3.1

`proxy_list` 不建议默认开启。它属于宽泛代理兜底，若包含 YouTube、Telegram、OpenAI 或 Apple 域名，会在主配置之前命中并绕过专用策略组。只有完成内容审计和日志命中验证后才可放在所有模块末尾试用。

## iCloud 专用代理优先 v3.1

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/iCloud.PrivateRelay.Priority.v3.1.sgmodule
```

该模块只含三个精确 `mask* → AI` 规则，不含脚本或 MITM。普通 iCloud 同步仍由 `direct_list` 或主配置保持 `DIRECT`。

## Apple 天气增强 QWeather v3.1

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1/LOWERTOP-Enterprise-v3.1/modules/optional/AppleWeather.QWeather.v3.1.sgmodule
```

Token 只在 Shadowrocket 本机模块参数中填写。免费凭证不支持昨日空气质量时，将两项 `AirQuality.Comparison.Yesterday.*` 改为 `WeatherKit`。

## HTTPS 解密与 MITM

- 仅使用主配置、`direct_list`、规则型 `reject_list`、规则型 ADBlock：关闭 HTTPS 解密。
- 启用 Apple 天气：开启 HTTPS 解密并信任 Shadowrocket CA；只允许 `weatherkit.apple.com`。
- APP 启动页 Ultra+ 或 YouTube 去广告若含 `http-response`、`requires-body=1`、`[URL Rewrite]` 或 `[MITM]`：必须开启 HTTPS 解密。
- 禁止使用 `hostname = *`，禁止将 iCloud、Apple Account、支付、登录和银行域名加入 MITM。

## 去广告重叠

核心配置已启用 AdvertisingLite。再叠加 `reject_list` 和 ADBlock不会线性提升效果，只会扩大重复匹配与误杀面。哔哩哔哩曾出现“收藏”入口异常，因此外部规则启用后必须单独验证收藏、登录、播放、评论、支付和推送。

YouTube 广告与视频常使用相同域名，纯 DNS/REJECT 规则通常不足；只有经过版本匹配验证的响应改写模块才适合启用。
