# LOWERTOP Enterprise 3.1.0-rc4 发布验证报告

> 自动化测试与真实设备证据分开计算；旧版本记录不能证明 RC4 新模块有效。

## 结论

- 自动化基线：**PASS**
- RC4 模块实机验证：**PENDING**
- RC4 可发布：**PENDING**
- Source commit：`9a2fd78a5600218bc38b1563e128f97ecde1a509`
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

- `build/LOWERTOP-Enterprise-v3.1-RC4-Performance-Direct.conf` — `91bd23fd50346647b3c3e032fc2b6df663e38fef8d5ec03caf8f386df40b524f`
- `build/LOWERTOP-Enterprise-v3.1-RC4-Strict-Direct.conf` — `95d76b006daf00bbd8fcd192fba5698bbdb7b9e752efc4e19d0ccb9cb5de79c8`
- `modular/LOWERTOP-Enterprise-v3.1-RC4-Performance-Modular.conf` — `7a1492a31cec04b1ba22554869834714c8fead8a652d336ec88604524f7b4e45`
- `modular/LOWERTOP-Enterprise-v3.1-RC4-Strict-Modular.conf` — `f942cff09730d955cc24487f4f69bcea3edcc3bf471a2be7b480d0c979c924c0`
- `experimental/LOWERTOP-Enterprise-v3.1-RC4-IPv6-SVCB-Experimental-Direct.conf` — `46b710fd1fc6e97c5224f455942a257e2ba68375de97ca1c37bf640e722b7436`

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
4. 验证 iCloud Drive、照片、备份、CloudKit、iWork 与 Apple Account 均命中 DIRECT，同时专用代理 mask 端点命中 AI。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 与核心路由继承既有基线，RC4 对最终规范化配置建立独立行为锁。
- Apple Weather 不会自动注入 Direct 主配置，可单独禁用和回滚。
- iCloud 分层路由会进入 Direct 主配置但不加入 MITM；发布前必须完成同步直连与专用代理 AI 的独立实机记录。
- Bilibili Next 与 BaiduNetdisk Next 保持独立实验分支，不计入 RC4 发布闸门。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优及 IPv6/ECH 不进入 RC4 默认配置。
