# v3.1 后续升级方向

## v3.1.x 稳定维护

1. 锁定 Shadowrocket 版本兼容矩阵，记录 iOS 与 App 版本。
2. 对已审计模块执行 24 至 72 小时独立实机回归，不把静态审计当作功能通过。
3. 增加 MITM 主机差异检查，任何新增主机都必须重新审批。
4. 监测固定上游提交是否出现已知安全问题，不自动跟随 `main` 或 `master`。

## v3.2 模块兼容层

1. 为 GMOogway 规则生成受保护域名排除报告，不直接启用宽泛 `proxy_list`。
2. 将 Stable、Candidate、Experimental 三类模块分目录和发布通道。
3. 增加外部脚本的网络访问、持久化存储、动态执行和凭证扫描。
4. 输出每个模块的最小 MITM 主机、回滚步骤和功能回归清单。

## 独立实验

1. `bilibili-next` 只针对已抓包确认的广告字段，不覆盖收藏、账户、评论和播放接口。
2. `baidunetdisk-next` 只处理已确认的广告接口，不伪造会员或账号状态。
3. DNS 多协议、IPv6、HTTPS/SVCB 与 ECH 继续保留在实验版，完成跨网络实机证据后再进入 Performance。

## 发布不变量

- 普通 iCloud、Apple Account、支付、登录及银行域名不得进入 MITM。
- `mask.icloud.com`、`mask-h2.icloud.com`、`mask-api.icloud.com` 继续精确走 `AI`。
- 正式主配置继续无 `[Script]`、无 `[MITM]`，第三方功能只通过可回滚模块提供。
- 任何规则、脚本或主机范围变化都必须绑定提交、校验值和回归证据。
