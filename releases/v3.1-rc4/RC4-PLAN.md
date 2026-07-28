# Shadowrocket Enterprise v3.1.0-rc4

## Scope

RC4 focuses on modular MITM enhancements while preserving the stable routing and DNS baseline from RC3.

### Planned modules

1. Bilibili ad filtering
   - Feed advertisements
   - Video-page recommendation advertisements
   - Membership-shopping cards
   - Comment-area promotional links
   - JSON and gRPC responses must be filtered structurally; core playback, comments and normal recommendations must remain intact.

2. Baidu Netdisk ad filtering
   - Splash and launch advertisements
   - Feed and activity cards
   - Playback advertisements where endpoint behaviour is verified
   - Experimental and disabled by default until packet-log validation is complete.

3. Current-egress IP quality inspection
   - Shadowrocket-compatible adaptation of MaYIHEI/paperclip ipquality.
   - Detects the currently active proxy egress only; Loon node-context APIs are not available in Shadowrocket.

4. Apple Weather enhancement
   - QWeather-backed optional module.
   - API host and API key remain local parameters and must never be committed to this public repository.
   - The previously disclosed QWeather API key must be rotated before use.

## Safety constraints

- Do not return empty JSON for complete Bilibili playback, view, recommendation or comment APIs.
- Do not fabricate VIP membership state.
- Do not apply broad Baidu domain blocking that can disrupt login, downloads, sharing or risk control.
- Keep third-party scripts pinned to a release or commit when feasible.
- Keep MITM hostnames additive and scoped to required endpoints.
- Do not commit secrets, private keys or personal API credentials.

## Release gates

- JavaScript syntax validation
- Configuration-section validation
- Duplicate and conflicting rule checks
- Bilibili playback, feed, search, comments and login regression tests
- Baidu Netdisk login, download, sharing and playback regression tests
- Apple Weather current, hourly, daily and air-quality verification
- Secret scanning before release
