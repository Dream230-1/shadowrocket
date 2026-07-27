# LOWERTOP Enterprise 后续迭代路线

## RC2：验证收口与行为冻结（当前）

目标是不改变已验证网络参数的前提下，将 RC1 从“可生成”升级为“可证明、可复现、可回滚”。

- 冻结 RC1 Performance 行为；
- 扩充 Apple 负向回归；
- 落实真实在线审计；
- 完成规则模块化、冲突检测和条件缓存；
- 收集 Wi-Fi、蜂窝、网络切换与 AdvertisingLite 72 小时证据；
- 生成并提交真实发布验证报告。

## RC3：功能增强与观测

### iCloud 专用代理分流

当前 iCloud（Drive、照片、云备份、CloudKit、Keychain 等）所有域名走 `Apple-Core-Direct` 直连。对中国大陆用户，`icloud.com` / `icloud-content.com` / `apple-cloudkit.com` 等国际端点经常访问缓慢。

计划：

1. 新增独立 `iCloud` 策略组，用户可自行选择 `DIRECT` 或代理节点。
2. 从 `Apple-Core-Direct` 中剥离 iCloud 专属域名，归入新的 `Apple-iCloud.list` 规则集。
3. 新增模块 `25-icloud.yaml`（默认关闭），用户按需启用。
4. Apple Push、App Store CDN、系统更新等非 iCloud 服务仍保留在 `Apple-Core-Direct` 直连。
5. 不会影响 `Apple-Global-AI` 中的 Private Relay / Apple News / Siri 路由。
6. 启用 iCloud 模块后，行为锁会检测到变更，需走 RC3 验证流程而非静默改动。

规则草案：`rules/Apple-iCloud.list` 已在仓库中就绪。

### 观测与韧性增强

1. **DNS Health Observatory**
   - 分网络环境记录 RTT、成功率、超时率、HTTP 状态和出口一致性；
   - Wi-Fi 与蜂窝分别评分，避免使用 GitHub Runner 结果替代设备数据；
   - 只生成推荐报告，不自动改写 Performance。
2. **故障注入**
   - 单 DoH/双 DoH 故障、返回 HTML、超时、证书失败；
   - 缓存损坏、304 但缓存丢失、上游规则异常膨胀；
   - UDP 不支持、Captive Portal、节点失效和网络切换。
3. **冲突分析增强**
   - AND/OR/NOT、URL-REGEX、USER-AGENT 和端口规则；
   - 输出 SARIF，在 Pull Request 中标注遮蔽来源；
   - 冲突豁免到期自动阻断。
4. **性能预算**
   - 构建时间、下载时间、缓存命中率、配置大小、导入时间、恢复时间；
   - 同设备同网络相对 RC1/RC2 劣化不得超过设定预算。
5. **游戏模块试验**
   - 基于明确需求增加游戏平台规则；
   - 默认关闭，完成首条命中和实机联机/语音/NAT 验证后再发布。

### MITM 去广告与功能增强模块

当前 LOWERTOP 的广告拦截基于 DNS 规则级别的 `REJECT`，无法屏蔽应用内原生渲染广告（如 Bilibili 信息流广告、闲鱼页面广告等）。
参考 Loon 生态中成熟的 MITM + 响应改写方案，RC3 计划将以下功能移植为 Shadowrocket MITM 模块：

| 目标 | MITM 域名 | 原理 |
|---|---|---|
| **Bilibili 去广告** | `app.bilibili.com`, `api.bilibili.com`, `grpc.biliapi.net` | 拦截 API 响应，过滤广告 JSON 字段，移除开屏/信息流/视频广告 |
| **闲鱼去广告** | `market.wapa.taobao.com` | 拦截页面 API，移除广告组件 |
| **百度网盘去广告** | `pan.baidu.com` | `reject-dict` 模拟空响应拦截配置和推荐 |
| **Apple 天气增强** | `weatherkit.apple.com` | 替换天气数据源为彩云/和风天气/WAQI |
| **DNS 泄漏防护** | 无 MITM | 额外规则层阻止 DoH/QUIC 泄漏 |

实现方式：

1. 每个功能独立为一个 Shadowrocket `.module` 文件，用户按需加载。
2. 使用 Shadowrocket 的 MITM + HTTP Response Scripting 替代 Loon 的 `response-body-json-jq` / `reject-dict` 语法。
3. 需用户主动开启 Shadowrocket 的 HTTPS 解密（MITM）并信任 CA 证书。
4. MITM 模块不影响 LOWERTOP 行为锁——它们是独立的功能增强，不改变路由规则。

计划在 RC3 中先实现 Bilibili 和闲鱼去广告，其余逐步追加。

## RC4：DNS 多协议实验

前提是确认 Shadowrocket 当前版本的真实语法与回退语义，而不是仅确认解析不报错。

候选链：

```text
DoQ → HTTP/3 DoH → HTTP/2 DoH → DoT
```

必须验证：

- 是否真正按顺序回退或只是并发竞速；
- 超时、NXDOMAIN、SERVFAIL 和连接失败分别如何触发回退；
- `#proxy`、`#no-h3` 等修饰符与各协议组合；
- Wi-Fi、蜂窝、切换、UDP 被封、QUIC 被限速场景；
- 不得回落到系统 DNS 或明文 53；
- Strict 与 Performance 的行为边界。

只有实机证据完整后才考虑单独的 `DNS-Multiprotocol-Experimental`，仍不直接替换 Performance。

## RC5：IPv6、HTTPS/SVCB 与 ECH 实验

分阶段推进：

1. 双栈可用性与代理 IPv6 出口验证；
2. AAAA 与 HTTPS/SVCB 查询行为；
3. WebRTC、DNS 和路由泄漏；
4. Happy Eyeballs 与网络切换；
5. ECHConfig 是否获得、浏览器/系统是否实际使用 ECH；
6. 不支持 ECH、ECH 重试与中间盒干扰时的行为。

`allow-dns-svcb=true` 只能证明允许查询，不能作为“ECH 已启用”的证据。IPv6/ECH 在完成跨运营商设备矩阵前始终保留在 Experimental。

## V3.2：平台与发布工程

- 将模块 Schema 固化并支持版本迁移；
- Stable/Candidate/Experimental 三通道发布；
- 自动生成变更影响图、回滚包和版本差异报告；
- 对 Shadowrocket 新版本做兼容矩阵；
- 如需 Loon/Clash 输出，为每个平台建立独立语义测试，不做未经验证的直接转译；
- 签名校验、SBOM、构建来源证明和不可变 Release Artifact。

## 长期原则

1. 默认配置的稳定性优先于新协议数量。
2. 所有架构重构必须先通过行为锁。
3. Runner 结果不能替代 iPhone 实机结果。
4. 动态选优必须按网络环境建模，并提供确定性回滚。
5. 实验能力不能静默进入 Performance。
6. 每项发布结论必须绑定 Commit、配置 SHA 和证据。
