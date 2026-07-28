# LOWERTOP Enterprise 3.1.0-rc4 发布验证报告

> 自动化测试与真实设备证据分开计算；旧版本记录不能证明 RC4 新模块有效。

## 结论

- 自动化基线：**PASS**
- RC4 模块实机验证：**PENDING**
- RC4 可发布：**PENDING**
- Source commit：`41a79719bc731d22841d8007d61c40300f5c26f3`
- Source branch：`release/v3.1-rc4`

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
| wifi_record | PENDING |
| cellular_record | PENDING |
| switching_record | PENDING |
| adblock_observation | PENDING |
| apple_weather_module | PENDING |
| icloud_ai_routing | PENDING |

## 构建产物

- `build/LOWERTOP-Enterprise-v3.1-RC4-Performance-Direct.conf` — `9cfb0c4c2449e6fb753011d94ae2c02d48a65d4ac575008c1de99808445ce264`
- `build/LOWERTOP-Enterprise-v3.1-RC4-Strict-Direct.conf` — `b09d0712333a1bd616224696a065ab6a94c5231d61b620129556c405d78305d5`
- `modular/LOWERTOP-Enterprise-v3.1-RC4-Performance-Modular.conf` — `eca8fa0002ba42b15796fa50f0d32d39a2b93bafffb5fed45d186cab5e9bf4a6`
- `modular/LOWERTOP-Enterprise-v3.1-RC4-Strict-Modular.conf` — `c467d86d61cd7deb7e23c6bf3a3587cbf5bb00c28bff0ac34c25ba402df3f47e`
- `experimental/LOWERTOP-Enterprise-v3.1-RC4-IPv6-SVCB-Experimental-Direct.conf` — `f972c5e9fbc3e8b19ccc39006edf58761ce7e1033d3e2541aac99ad43b22eafc`

## 尚缺证据

- `adblock-72h`
- `cellular`
- `module:apple-weather-qweather`
- `module:icloud-ai-routing`
- `switching`
- `wifi`

## 必须完成的真实设备验证

1. 使用 RC4 主配置完成 Wi-Fi、蜂窝及双向网络切换记录。
2. 使用 RC4 配置完成连续至少 72 小时广告误杀观察。
3. 验证 Apple 天气模块并提交对应记录，覆盖当前、小时、每日、降水、空气质量、定位与小组件。
4. 验证 iCloud Drive、照片、备份、CloudKit、iWork 与 Apple Account 均命中 AI，同时 Apple Push、App Store 与系统更新保持 DIRECT。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 与核心路由继承既有基线，RC4 对最终规范化配置建立独立行为锁。
- Apple Weather 不会自动注入 Direct 主配置，可单独禁用和回滚。
- iCloud AI 路由会进入 Direct 主配置，但不加入 MITM；发布前必须完成独立实机记录。
- Bilibili Next 与 BaiduNetdisk Next 保持独立实验分支，不计入 RC4 发布闸门。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优及 IPv6/ECH 不进入 RC4 默认配置。
