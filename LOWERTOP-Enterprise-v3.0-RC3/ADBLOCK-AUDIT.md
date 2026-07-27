# AdvertisingLite 碰撞审计

RC3 保持 AdvertisingLite 为默认广告拦截规则，并新增 `scripts/adblock_collision.py`。

工作方式：

1. 先运行 `remote_audit.py` 下载并验证固定快照规则。
2. 将 AdvertisingLite 与 OpenAI、Apple、Telegram 和流媒体规则交叉比较。
3. 报告精确域名、后缀、关键词和 CIDR 的潜在重叠。
4. 验证关键服务规则阶段必须早于广告规则阶段。

默认发布闸门以“规则顺序安全”为准。共享追踪域名可能同时出现在流媒体与广告库中，因此 RC3 会报告碰撞，但不会仅凭流媒体共享域名自动阻断发布。

运行：

```bash
python scripts/remote_audit.py
python scripts/adblock_collision.py
```
