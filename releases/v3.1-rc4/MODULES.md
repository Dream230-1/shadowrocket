# RC4 独立模块安装与验证

RC4 主配置继续维持 RC3 的稳定路由基线。以下模块需要在 Shadowrocket 中单独安装、启用和回滚，不会自动写入 Direct 配置。

## 安装前准备

1. Shadowrocket 首页保持“全局路由 = 配置”。
2. 打开当前配置的 HTTPS 解密，生成并信任 Shadowrocket CA 证书。
3. 先保留 RC3 配置和旧模块，确认 RC4 模块稳定后再清理。
4. 不要同时启用功能重叠的哔哩哔哩、百度网盘或 WeatherKit 模块。

## 1. 哔哩哔哩去广告 RC4

安装链接：

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1-rc4/LOWERTOP-Enterprise-v3.1/modules/optional/Bilibili.ADBlock.RC4.sgmodule
```

默认处理：

- 开屏广告；
- 首页与短视频信息流广告；
- 视频下方广告相关推荐；
- 搜索和动态广告卡片；
- 直播和会员购推广；
- 评论区广告及推荐推广。

验证顺序：

1. 冷启动哔哩哔哩，确认无白屏或启动循环。
2. 刷新首页 10 次，确认正常视频卡片未明显减少。
3. 打开普通视频和番剧，确认可播放、清晰度和进度条正常。
4. 检查视频相关推荐、评论列表、回复展开和评论跳转。
5. 检查搜索、动态、直播间和账号登录。

异常时直接禁用本模块，不需要替换主配置。

## 2. 百度网盘去广告 RC4 Experimental

安装链接：

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1-rc4/LOWERTOP-Enterprise-v3.1/modules/experimental/BaiduNetdisk.AdBlock.Experimental.sgmodule
```

当前只处理：

- 活动弹窗入口；
- 福利推广列表；
- 广告配置接口；
- “我的”页面游戏中心入口。

必须验证：

- 登录和验证码；
- 文件列表和图片预览；
- 上传、下载和转存；
- 分享链接；
- 在线视频播放。

本模块不解锁会员、不修改账号状态、不调整视频倍速。出现任一主链路异常应立即禁用。

## 3. Apple 天气 QWeather RC4

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
- 添加城市、定位城市和天气小组件。

免费凭证若不支持昨日空气质量接口，可将两项 `AirQuality.Comparison.Yesterday.*` 参数改回默认数据源。

## 4. 当前出口 IP 质量检测

安装链接：

```text
https://raw.githubusercontent.com/Dream230-1/shadowrocket/release/v3.1-rc4/LOWERTOP-Enterprise-v3.1/modules/tools/IPQuality.CurrentEgress.sgmodule
```

使用方法：

1. 在 Shadowrocket 中切换至目标节点并连接。
2. 运行“节点 IP 质量检测（当前出口）”。
3. 查看 IP、ASN、网络类型和风险标记。

该工具检测当前实际出口，不能像 Loon `generic` 脚本一样直接指定任意未连接节点。

## 建议启用顺序

1. IP 质量检测；
2. 哔哩哔哩模块；
3. Apple 天气模块；
4. 百度网盘实验模块。

每次只新增一个模块，至少完成对应回归项目后再启用下一个，便于定位冲突和快速回滚。
