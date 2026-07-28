# LOWERTOP Enterprise v3.1 RC2 发布验证报告

> 自动生成骨架；设备实测与 AdvertisingLite 观察必须由真实记录补齐，不能由 CI 代填。

## 结论

- 自动化基线：**PASS**
- RC2 可发布：**PENDING**
- Source commit：`unknown`
- Source branch：`unknown`

## 发布闸门

| 闸门 | 状态 |
|---|---|
| behavior_lock | PASS |
| dns_audit | PASS |
| offline_regression | PASS |
| cache_refresh | PENDING |
| online_regression | PENDING |
| remote_audit | PENDING |
| ruleset_drift | PENDING |
| adblock_collisions | PENDING |
| service_health | PENDING |
| network_benchmark | PENDING |
| rule_conflicts | PASS |
| modular_equivalence | PASS |
| wifi_record | PASS |
| cellular_record | PASS |
| switching_record | PASS |
| adblock_observation | PASS |

## 构建产物

- `build/LOWERTOP-Enterprise-v3.1-RC2-Performance-Direct.conf` — `874a88048a0b07646e060257e1248b519d6493d84422ed3b308d08be83c4e1c0`
- `build/LOWERTOP-Enterprise-v3.1-RC2-Strict-Direct.conf` — `6f23f7713171338fe4d10696f9b927b852d82379dcc40c48d5e58517cfcf7f6c`
- `build/LOWERTOP-Enterprise-v3.1-RC3-Performance-Direct.conf` — `d45bd32dc9c48f8ef0278e08ab250e174519e70c7f1981dce09566f84f08397d`
- `build/LOWERTOP-Enterprise-v3.1-RC3-Strict-Direct.conf` — `5960d8864b8375e64094a0368db981ff01b00d2fd90e36666c6cd9882be899ff`
- `modular/LOWERTOP-Enterprise-v3.1-RC3-Performance-Modular.conf` — `6b4a2ce0a117c6ab14b772312ca0c904a11413fa1b415a3e1bb9b773b38e9dd0`
- `modular/LOWERTOP-Enterprise-v3.1-RC3-Strict-Modular.conf` — `38149dbf9c6e97a85cbb0f44b6602290c251b8d7d0d678a96dd748e8088a7af9`
- `experimental/LOWERTOP-Enterprise-v3.1-RC2-IPv6-SVCB-Experimental-Direct.conf` — `414e42ccdf573d3aa29106f93f4118956eeca0dccdec9327f8372c9ed4f1fe55`
- `experimental/LOWERTOP-Enterprise-v3.1-RC3-IPv6-SVCB-Experimental-Direct.conf` — `7c9860841abf203c600feba91a722b142a5ef38237fcb4748804b2cb3be03820`

## 尚需真实设备完成

1. 家庭/办公 Wi-Fi 实测记录。
2. 蜂窝网络实测记录。
3. Wi-Fi → 蜂窝与蜂窝 → Wi-Fi 网络切换记录。
4. AdvertisingLite 连续 72 小时误杀观察和处理结论。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 和路由行为受 RC1 行为锁保护。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优、IPv6/ECH 不进入 RC2 默认配置。
- Experimental 仅提供 IPv6/SVCB 验证，不宣称强制或确认 ECH。
