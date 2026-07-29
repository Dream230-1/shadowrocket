# LOWERTOP Enterprise 3.1.1 发布验证报告

> 自动化测试与真实设备证据分开计算；旧版本记录不能证明 3.1.1 新模块有效。

## 结论

- 自动化基线：**PASS**
- v3.1 模块实机验证：**PENDING**
- 3.1.1 可发布：**PENDING**
- Source commit：`d51d4d0f4530f2b4aad2b2a2ae8aaf1827869fc3`
- Source branch：`release/v3.1.1`

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
| adblock_collisions | PENDING |
| service_health | PASS |
| network_benchmark | PASS |
| rule_conflicts | PASS |
| modular_equivalence | PASS |
| wifi_record | PENDING |
| cellular_record | PENDING |
| switching_record | PENDING |
| adblock_observation | PENDING |
| apple_weather_module | PENDING |
| icloud_ai_routing | PENDING |

## 构建产物

- `build/LOWERTOP-Enterprise-v3.1.1-Performance-Direct.conf` — `55fd03acf3c92ec34f8bd163355517a38f31c6bfcfe664b331ec89caef4e64b7`
- `build/LOWERTOP-Enterprise-v3.1.1-Strict-Direct.conf` — `71de8021dfd21b0ce6d5357d43221dca4889bd9aa14433e0bc0cb50a16cb4e22`
- `modular/LOWERTOP-Enterprise-v3.1.1-Performance-Modular.conf` — `2aa5397cad25b575efff57bb3ec0a1dddb1a3d549ab1cb9fc4f1ea8ea8f13dbe`
- `modular/LOWERTOP-Enterprise-v3.1.1-Strict-Modular.conf` — `77f46d0446fd4d08b2baee88056706288e707bf41357d3999f00f2a345323259`
- `experimental/LOWERTOP-Enterprise-v3.1.1-IPv6-SVCB-Experimental-Direct.conf` — `48fbcb962f57d7a2e745c2b7f52936544c8ba1b4e3c9478de04b2ebf094bed01`

## 尚缺证据

- `adblock-72h`
- `cellular`
- `module:apple-weather-qweather`
- `module:icloud-ai-routing`
- `switching`
- `wifi`

## 必须完成的真实设备验证

1. 使用 3.1.1 主配置完成 Wi-Fi、蜂窝及双向网络切换记录。
2. 使用 3.1.1 配置完成连续至少 72 小时广告误杀观察。
3. 验证 Apple 天气模块并提交对应记录，覆盖当前、小时、每日、降水、空气质量、定位与小组件。
4. 验证 iCloud Drive、照片、备份、CloudKit、iWork 与 Apple Account 均命中 DIRECT，同时专用代理 mask 端点命中 AI。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 与核心路由继承既有基线，v3.1 对最终规范化配置建立独立行为锁。
- Apple Weather 不会自动注入 Direct 主配置，可单独禁用和回滚。
- iCloud 分层路由会进入 Direct 主配置但不加入 MITM；发布前必须完成同步直连与专用代理 AI 的独立实机记录。
- Bilibili Next 与 BaiduNetdisk Next 保持独立实验分支，不计入 v3.1 发布闸门。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优及 IPv6/ECH 不进入 v3.1 默认配置。
