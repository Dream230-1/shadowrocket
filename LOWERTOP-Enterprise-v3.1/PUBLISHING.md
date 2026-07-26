# 发布与回滚

## 构建产物

RC2 生成：

- `build/`：Direct Strict/Performance；
- `modular/`：Modular Strict/Performance；
- `experimental/`：IPv6/SVCB Experimental；
- `reports/`：行为锁、DNS、回归、冲突、远程审计和性能报告。

Modular 的本地规则 URL 在正式 Release 时必须固定到 40 位 Git Commit，不得引用可变 `main`。

## 发布流程

1. 在候选 Commit 上运行 `python scripts/ci.py --online`；
2. 完成三类设备记录和 72 小时广告观察；
3. 运行 `python scripts/validate_field_records.py --require-complete`；
4. 运行 `python scripts/release_report.py`；
5. 确认 `RELEASE-VALIDATION.md` 的全部闸门为 PASS；
6. 发布 Direct、Modular、Experimental、规则文件、校验和与报告。

## 回滚条件

出现任一情况立即回滚至 RC1 Performance：

- DNS 泄漏或系统 DNS 回退；
- Wi-Fi/蜂窝切换出现可复现瞬时直连；
- Apple Push、iCloud、App Store 或登录支付出现 P0/P1 故障；
- ChatGPT/Telegram 核心链路出现由路由变化导致的回归；
- AdvertisingLite 出现未解决 P0/P1 误杀；
- 行为锁差异未获明确版本审批。

RC1 回滚基线：

- Source Commit：`f50f2f4610c3029e41ce613e3506605d43630be3`
- RC1 Performance raw SHA-256：`207d80a1f5f51ea8f7a79a019b8e8c3f38c18ef74feaf0a5672a14e98a08e1a4`
- RC1 Performance semantic SHA-256：`c4b8d5dfd0c143765148a74d0da09036d85ac34913029e9388fa1678d0c637fb`
