# LOWERTOP Enterprise v3.0 RC3

RC3 在 RC2 已通过的模块化、声明式生成、远程审计和在线回归基础上，加入发布链、DNS 安全闸门、广告碰撞审计、规则漂移基线和性能报告。

## 推荐配置

日常主力仍为 **Performance**：允许 QUIC/HTTP3，同时保持加密 DNS、禁止系统 DNS 回退、关闭 IPv6、UDP 不支持时拒绝直连回落。

Strict 用于 UDP/QUIC 不稳定环境。IPv6/SVCB Experimental 仅用于实验，不作为日常配置。

## RC3 架构

```text
manifest.yaml
├── rules/*.list
├── scripts/generate.py
├── scripts/dns_audit.py
├── scripts/remote_audit.py
├── scripts/ruleset_drift.py
├── scripts/adblock_collision.py
├── scripts/regression.py
├── scripts/service_health.py
├── scripts/network_benchmark.py
└── scripts/publish.py
```

## 本地离线验证

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/generate.py --profile all-release --mode inline
python scripts/generate.py --profile ipv6_svcb_experimental --mode inline --out-dir experimental
python scripts/regression.py --offline
python scripts/dns_audit.py
```

## 在线审计

```bash
python scripts/remote_audit.py
python scripts/ruleset_drift.py
python scripts/regression.py --online
python scripts/adblock_collision.py
python scripts/service_health.py --allow-warnings --allow-failures
python scripts/network_benchmark.py
```

## 可复现发布

```bash
python scripts/publish.py \
  --source-ref <40位Git提交SHA> \
  --repository Dream230-1/ShuntRules
```

生成的 Modular 配置只引用固定 Commit，不引用 `main`。

## DNS 安全边界

RC3 自动检查 DoH、`#proxy`、系统 DNS 回退、IPv6、DNS 53 劫持和 UDP 回落策略。真实设备仍须在 Wi-Fi、蜂窝、WebRTC 和网络切换场景验证。

## 广告拦截原则

默认继续使用 AdvertisingLite。关键服务和流媒体规则位于广告规则之前，碰撞审计负责发现潜在误杀。更激进的广告库不进入默认 Performance。
