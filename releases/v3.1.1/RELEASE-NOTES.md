# LOWERTOP Enterprise v3.1.1

v3.1.1 是按用户稳定线路偏好发布的正式修订版。

冻结源提交：`ae08eee2d4190ccb61f33ff0d3a9e4fa26ba2b88`。

## 路由变化

- `proxy_list` 保留上游全部规则并统一转为 `AI`，每天自动更新转码。
- 删除 Telegram 与 YouTube 独立策略组；两类规则直接走 `AI`。
- 其他主配置策略组保留，但若流量先命中模块级 `proxy_list`，以 `AI` 为最终结果。
- 普通 iCloud 继续直连；Private Relay 的三个 `mask*` 精确端点继续优先走 `AI`。

## 广告与模块

- 删除内置 AdvertisingLite。
- 外部 `reject_list` 负责规则型广告拦截；Ultra+ 可负责响应改写。
- ADBlock 不与 `reject_list` 同时启用。
- 新增哔哩哔哩、百度网盘纯去广告候选模块。
- 修复并固定 Netflix 双字幕/评分模块。

## 验证

- 项目单元测试：12 项通过。
- 内核单元测试：9 项通过。
- 路由回归：52 项通过。
- 行为锁、DNS、Direct/Modular 等价性、规则冲突和可选模块安全审计通过。
- 哔哩哔哩与百度网盘当前客户端抓包验证仍待完成，不能据静态审计宣称实机通过。

主配置必须替换导入，不要与 v3.1 合并。
