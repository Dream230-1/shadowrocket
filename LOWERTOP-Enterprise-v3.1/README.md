# LOWERTOP Enterprise v3.1 RC2

RC2 是 **验证收口与行为固化版本**。默认 Performance 网络参数、DNS、QUIC、IPv6、UDP 回退和路由结果继承 RC1；本轮主要增强工程化验证，不把未经 Shadowrocket 实机证明的新协议写进主力配置。

## RC2 核心变化

1. **RC1 Performance 行为锁**：固定 `[General]`、`[Proxy Group]`、首条命中规则顺序、策略绑定、`[Host]` 与 `FINAL,PROXY`。
2. **真实审计链**：`--online` 会实际运行远程规则、漂移、在线回归、广告碰撞、全局冲突、服务健康和性能报告，不再只打印继承提示。
3. **Apple 负向回归**：覆盖 Apple Global/Core 优先级、禁止策略、域名边界、大小写和尾点语义。
4. **规则模块化**：AI、Apple、通信、媒体、游戏、广告和基础路由分别声明；RC2 装配后必须与 RC1 行为等价。
5. **全局冲突检测**：检测跨策略精确域名、后缀、关键词和 CIDR 遮蔽；有意重叠必须在带原因、负责人和期限的 allowlist 中登记。
6. **条件缓存**：支持 ETag、Last-Modified、304、本地哈希、原子写入和 stale-if-error。
7. **真实验证记录**：提供 Wi-Fi、蜂窝、网络切换与 AdvertisingLite 72 小时观察模板。
8. **发布验证报告**：自动绑定 Commit、配置 SHA-256、自动化结果和实机证据状态。

## 保持不变

- Performance 允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 境外备用 DoH 继续通过 `#proxy`。
- Performance 与 Strict 关闭 IPv6。
- UDP 策略不支持时 `REJECT`，不回落到直连。
- AdvertisingLite 为默认广告规则。
- OpenAI、Apple、Telegram、流媒体、中国大陆与 FINAL 的策略和顺序保持 RC1 行为。

## 目录

```text
config/       DNS、功能、发布与冲突豁免
modules/      规则模块声明
rules/        V3.1 自维护本地规则
regression/   基础与 Apple 负向回归
baselines/    RC1 Performance 行为契约
validation/   设备与广告观察记录
scripts/      构建、审计、缓存和报告工具
```

## 构建与验证

```bash
python -m pip install -r requirements.txt
python scripts/ci.py
python scripts/ci.py --online
```

生成发布验证报告：

```bash
python scripts/release_report.py
```

真实设备记录完成后执行严格证据闸门：

```bash
python scripts/validate_field_records.py --require-complete
```

## RC2 发布条件

- 自动化行为锁、DNS 审计、Apple 负向回归、全局冲突和在线审计通过；
- Wi-Fi、蜂窝、双向切换记录完成；
- AdvertisingLite 连续至少 72 小时，无未解决 P0/P1 误杀；
- 发布报告与本次 Commit 和配置 SHA-256 绑定。

## 准确边界

- `allow-dns-svcb=true` 只允许 HTTPS/SVCB 查询，不等于强制或确认 ECH。
- DoQ → DoH3 → DoH → DoT 的严格自动回退尚未完成 Shadowrocket 实机语义验证，不进入 RC2 默认配置。
- DNS 健康评分在后续版本先做观测和建议，不在 RC2 自动改写终端配置。
- IPv6/SVCB 仍只在 Experimental 生成物中存在。

后续路线见 [ROADMAP.md](ROADMAP.md)，实机步骤见 [TEST-MATRIX.md](TEST-MATRIX.md)。
