# LOWERTOP Enterprise v3.1 正式版

v3.1 由 RC4 冻结发布。核心配置保留已验证的 DNS、策略组、路由顺序、iCloud 分层分流、AdvertisingLite 和 `FINAL,PROXY`。

构建源提交：`3cfcfa8e5d164c9d2647b84cbeeb20c13062f6d6`。

## 正式版边界

- 普通 iCloud 同步与 Apple Account 保持 `DIRECT`。
- `mask.icloud.com`、`mask-h2.icloud.com`、`mask-api.icloud.com` 走 `AI`。
- AdvertisingLite 默认启用。
- 默认主配置不含脚本和 MITM，不要求 HTTPS 解密。
- Apple 天气、启动页去广告、YouTube 去广告等响应改写能力均为可选模块。
- 哔哩哔哩与百度网盘旧 MITM 模块不进入正式版。
- 微信公众号、微博、Netflix 评分和 YouTube 信息流提供固定上游提交的审计版模块。
- 当前推荐组合关闭 YouTube 模块；YouTube 审计版只作为后续单独测试项。

## 安装

主配置必须替换导入，不要与 RC 配置合并。可选模块和顺序见同目录 `MODULES.md`。

第三方模块逐项结论见 `MODULE-AUDIT.md`，后续方向见 `UPGRADE-ROADMAP.md`。
