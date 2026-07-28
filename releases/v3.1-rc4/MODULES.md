# RC4 独立模块安装与验证

RC4 当前包含三类能力：内置的 iCloud 分层分流、用于兼容外部 `direct_list` 的 iCloud 专用代理优先模块，以及需单独安装的 Apple 天气 QWeather 可选模块。未启用外部 `direct_list` 时，主配置自身已能正确分流 iCloud；Apple 天气与 iCloud 专用代理优先模块均可单独安装、启用和回滚。

哔哩哔哩与百度网盘旧模块已从 RC4 移除。后续分别在 `bilibili-next` 与 `baidunetdisk-next` 实验分支中基于最新客户端抓包结果重新开发，不继续修补或安装 RC4 旧模块。

## iCloud 分层分流

- `Apple-iCloud` 规则集使 Drive、照片、备份、CloudKit、Live Photos、iWork、连接检测及 Apple Account 保持 `DIRECT`。
- `mask.icloud.com`、`mask-h2.icloud.com`、`mask-api.icloud.com` 由更靠前的 `Apple-Global-AI` 精确规则交给 `AI`。
- Apple Push、App Store、系统更新与中国区 Apple Core 保持 `DIRECT`。
- 不需要开启 HTTPS 解密，iCloud 与 Apple Account 域名不得加入 MITM。
- 正式发布前按 `validation/modules/TEMPLATE-ICLOUD-AI.yaml` 完成 Wi-Fi、蜂窝、网络切换与负向对照。

## iCloud 专用代理优先 RC4

仅当外部 `direct_list` 含有 `DOMAIN-SUFFIX,icloud.com,DIRECT` 等泛 iCloud 直连规则时安装：

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1-rc4/LOWERTOP-Enterprise-v3.1/modules/optional/iCloud.PrivateRelay.Priority.RC4.sgmodule
```

模块顺序必须为：

1. `iCloud 专用代理优先 RC4`
2. `direct_list`
3. Apple 天气及其他模块

该模块只包含三个精确 `DOMAIN` 规则，不含脚本或 MITM。其作用是让 `mask.icloud.com`、`mask-h2.icloud.com`、`mask-api.icloud.com` 在 `direct_list` 的泛域名规则之前命中 `AI`；普通 iCloud 同步仍由 `direct_list` 或主配置保持 `DIRECT`。

## 安装前准备

1. Shadowrocket 首页保持“全局路由 = 配置”。
2. 打开当前配置的 HTTPS 解密，生成并信任 Shadowrocket CA 证书。
3. 保留 RC3 配置，确认 RC4 与模块稳定后再清理旧配置。
4. 不要同时启用功能重叠的 WeatherKit 模块。

## Apple 天气 QWeather RC4

安装链接：

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1-rc4/LOWERTOP-Enterprise-v3.1/modules/optional/AppleWeather.QWeather.RC4.sgmodule
```

安装后进入模块参数：

- `API.QWeather.Host`：填写和风天气控制台提供的 API Host；
- `API.QWeather.Token`：填写重新生成的新 API Key；
- 其他参数默认使用 QWeather 提供天气、未来一小时降水和空气质量。

安全要求：

- 不要把真实 Token 写入 GitHub、配置分享链接或截图；
- 先撤销此前已公开的旧 Key，再生成新 Key；
- Token 只保存在 Shadowrocket 本机模块参数中。

验证项目：

- 当前天气；
- 每小时和 10 日预报；
- 未来一小时降水；
- 空气质量和主要污染物；
- 添加城市、定位城市和天气小组件；
- 禁用模块后恢复原行为。

免费凭证若不支持昨日空气质量接口，可将两项 `AirQuality.Comparison.Yesterday.*` 参数改回默认数据源。
