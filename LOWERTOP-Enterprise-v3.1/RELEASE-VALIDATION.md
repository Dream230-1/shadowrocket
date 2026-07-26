# LOWERTOP Enterprise v3.1 RC2 发布验证报告

> 自动生成骨架；设备实测与 AdvertisingLite 观察必须由真实记录补齐，不能由 CI 代填。

## 结论

- 自动化基线：**PASS**
- RC2 可发布：**PENDING**
- Source commit：`42069b7d75353c64b083a59ddfd179370fbe13c2`
- Source branch：`release/v3.1-rc2`

## 发布闸门

| 闸门 | 状态 |
|---|---|
| behavior_lock | PASS |
| dns_audit | PASS |
| offline_regression | PASS |
| cache_refresh | PASS |
| online_regression | PASS |
| remote_audit | PASS |
| ruleset_drift | PASS |
| adblock_collisions | PASS |
| service_health | PASS |
| network_benchmark | PASS |
| rule_conflicts | PASS |
| modular_equivalence | PASS |
| wifi_record | PASS |
| cellular_record | PASS |
| switching_record | PASS |
| adblock_observation | PENDING |

## 构建产物

- `build/LOWERTOP-Enterprise-v3.1-RC2-Performance-Direct.conf` — `874a88048a0b07646e060257e1248b519d6493d84422ed3b308d08be83c4e1c0`
- `build/LOWERTOP-Enterprise-v3.1-RC2-Strict-Direct.conf` — `6f23f7713171338fe4d10696f9b927b852d82379dcc40c48d5e58517cfcf7f6c`
- `modular/LOWERTOP-Enterprise-v3.1-RC2-Performance-Modular.conf` — `01e78a772f8ab8a1371f6174fe23c1df38a9ef2ff5ec63aea27efccb1ad44363`
- `modular/LOWERTOP-Enterprise-v3.1-RC2-Strict-Modular.conf` — `bedfdbe80e130526331b148faf59e3dfd4ed200cea08db63c5236c2f62fe5998`
- `experimental/LOWERTOP-Enterprise-v3.1-RC2-IPv6-SVCB-Experimental-Direct.conf` — `414e42ccdf573d3aa29106f93f4118956eeca0dccdec9327f8372c9ed4f1fe55`

## 尚需真实设备完成

1. 家庭/办公 Wi-Fi 实测记录。
2. 蜂窝网络实测记录。
3. Wi-Fi → 蜂窝与蜂窝 → Wi-Fi 网络切换记录。
4. AdvertisingLite 连续 72 小时误杀观察和处理结论。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 和路由行为受 RC1 行为锁保护。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优、IPv6/ECH 不进入 RC2 默认配置。
- Experimental 仅提供 IPv6/SVCB 验证，不宣称强制或确认 ECH。
