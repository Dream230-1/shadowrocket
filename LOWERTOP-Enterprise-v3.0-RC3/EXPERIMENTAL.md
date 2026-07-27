# IPv6 / HTTPS-SVCB / ECH 实验说明

实验配置仅增加 IPv6 与 HTTPS/SVCB 查询能力，不宣称强制 ECH：

```ini
ipv6 = true
prefer-ipv6 = false
allow-dns-svcb = true
```

## 启用条件

- AI、Telegram、PROXY 和流媒体所用节点均有稳定 IPv6 出口。
- IPv4 与 IPv6 出口国家/地区符合预期。
- DNSLeakTest 不出现本地运营商解析器。
- BrowserLeaks 的 WebRTC IPv6 不暴露本地公网 IPv6。
- ChatGPT、Apple Push、iCloud、Telegram 和流媒体功能正常。

## ECH 判定

HTTPS/SVCB 记录可以携带 ECH 配置信息，但最终是否使用 ECH 还取决于操作系统、应用网络栈、TLS 客户端和服务端。Shadowrocket 的 `allow-dns-svcb` 只控制 HTTPS/SVCB 查询是否被允许。
