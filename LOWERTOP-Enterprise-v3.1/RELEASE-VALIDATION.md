# LOWERTOP Enterprise 3.1.0 发布验证报告

> 自动化测试与真实设备证据分开计算；旧版本记录不能证明 3.1.0 新模块有效。

## 结论

- 自动化基线：**PASS**
- v3.1 模块实机验证：**PENDING**
- 3.1.0 可发布：**PENDING**
- Source commit：`3cfcfa8e5d164c9d2647b84cbeeb20c13062f6d6`
- Source branch：`release/v3.1`

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

- `build/LOWERTOP-Enterprise-v3.1-Performance-Direct.conf` — `f2f77cc601b074d7d0dd83bc7db135ab86b08dac574fdb5ca20b70ccd16019fd`
- `build/LOWERTOP-Enterprise-v3.1-Strict-Direct.conf` — `67e19c2dbfa692dad462ccb86c6ecfc1d8aff285220f17330be1faa1711969db`
- `modular/LOWERTOP-Enterprise-v3.1-Performance-Modular.conf` — `f8f1469c0e58b91cc4e16cdc42169b0bd11b32608b0f9da6c942128e4890376b`
- `modular/LOWERTOP-Enterprise-v3.1-Strict-Modular.conf` — `b78c83893df07ec2083a26268bb5302e15354bf75c957e2da832f75da60a8107`
- `experimental/LOWERTOP-Enterprise-v3.1-IPv6-SVCB-Experimental-Direct.conf` — `283d39023dbae8dbdbb0b3f757a363b7d9499d884f7e487d1cbfb11c4dcc05b6`

## 尚缺证据

- `adblock-72h`
- `cellular`
- `module:apple-weather-qweather`
- `module:icloud-ai-routing`
- `switching`
- `wifi`

## 必须完成的真实设备验证

1. 使用 3.1.0 主配置完成 Wi-Fi、蜂窝及双向网络切换记录。
2. 使用 3.1.0 配置完成连续至少 72 小时广告误杀观察。
3. 验证 Apple 天气模块并提交对应记录，覆盖当前、小时、每日、降水、空气质量、定位与小组件。
4. 验证 iCloud Drive、照片、备份、CloudKit、iWork 与 Apple Account 均命中 DIRECT，同时专用代理 mask 端点命中 AI。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 与核心路由继承既有基线，v3.1 对最终规范化配置建立独立行为锁。
- Apple Weather 不会自动注入 Direct 主配置，可单独禁用和回滚。
- iCloud 分层路由会进入 Direct 主配置但不加入 MITM；发布前必须完成同步直连与专用代理 AI 的独立实机记录。
- Bilibili Next 与 BaiduNetdisk Next 保持独立实验分支，不计入 v3.1 发布闸门。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优及 IPv6/ECH 不进入 v3.1 默认配置。
