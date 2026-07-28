# Shadowrocket Enterprise v3.1.0-rc4

## Scope

RC4 以 RC3 的稳定路由和 DNS 基线为前提，聚焦生成配置结构、主线模块审计、Developer Toolkit 与可回滚验证。

### 主线范围

1. Apple Weather enhancement
   - QWeather-backed optional module.
   - API host and API key remain local parameters and must never be committed to this public repository.
   - The previously disclosed QWeather API key must be rotated before use.

2. Configuration hardening
   - Validate independent `[Rule]`, `[Script]` and `[MITM]` sections.
   - Preserve RC3 DNS and `FINAL,PROXY` behavior.
   - Apply the approved RC4 routing delta: ordinary `Apple-iCloud` synchronization stays `DIRECT`; Private Relay `mask*` endpoints route to `AI`; the unused legacy `iCloud` select group is removed.

3. iCloud layered routing
   - Cover iCloud Drive, Photos, Backup, CloudKit, Live Photos, iWork, connection probes and Apple Account authentication.
   - Keep Apple Push, App Store, software updates and China Apple Core on `DIRECT`.
   - Never add iCloud or Apple Account hosts to MITM.

4. Developer Toolkit
   - Module static validation.
   - MITM hostname extraction and risk checks.
   - Shadowrocket text-log analysis and regression tests.

### Excluded from RC4

- Bilibili ad filtering is frozen on RC4 and moved to `bilibili-next`.
- Baidu Netdisk ad filtering is frozen on RC4 and moved to `baidunetdisk-next`.
- Both modules must be redesigned from current client packet captures, not by patching the removed RC4 rules.
- Current-egress IP quality inspection is excluded because Shadowrocket lacks a reliable node-switch trigger and direct manual trigger for the intended workflow.

## Safety constraints

- Do not fabricate VIP membership or paid account state.
- Do not apply broad domain blocking that can disrupt login, downloads, sharing, playback or risk control.
- Prefer field-level JSON or protobuf modification over clearing complete responses.
- Keep third-party scripts pinned to a release or commit when feasible.
- Keep MITM hostnames additive and scoped to required endpoints.
- Do not commit secrets, private keys or personal API credentials.

## Release gates

- JavaScript syntax validation.
- Configuration-section validation.
- Duplicate and conflicting rule checks.
- Apple Weather current, hourly, daily, precipitation and air-quality verification.
- iCloud DIRECT synchronization, Private Relay AI routing and Apple Core negative-control verification.
- RC4 Wi-Fi, cellular and bidirectional switching verification.
- AdvertisingLite observation for at least 72 hours without unresolved P0/P1 regressions.
- Secret scanning before release.
