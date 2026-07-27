# DNS Leak Guard v2

RC3 新增 `scripts/dns_audit.py`，在配置发布前执行静态 DNS 安全审计。

检查范围：

- 所有 DNS 端点必须使用 HTTPS DoH。
- `fallback-dns-server` 的境外解析器必须包含 `#proxy`。
- 禁止 system DNS 回退。
- 发布版必须关闭 IPv6 和 IPv6 优先。
- IPv6/SVCB 仅允许在 Experimental 配置启用。
- 硬编码公共 DNS 53 端口必须被 `hijack-dns` 覆盖。
- 节点不支持 UDP 时必须 `REJECT`，不得回落为 `DIRECT`。
- Strict 与 Performance 的 QUIC 参数必须与 manifest 一致。

运行：

```bash
python scripts/generate.py --profile all-release --mode inline
python scripts/generate.py --profile ipv6_svcb_experimental --mode inline --out-dir experimental
python scripts/dns_audit.py
```

该工具无法代替真实设备上的 DNSLeakTest、WebRTC、Wi-Fi、蜂窝和网络切换测试。
