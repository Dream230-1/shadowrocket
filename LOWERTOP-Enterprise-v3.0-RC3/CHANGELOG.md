# CHANGELOG

## 3.0.0-rc3

### Added
- DNS Leak Guard v2 静态审计。
- AdvertisingLite 与关键服务规则碰撞报告。
- 远程规则 SHA、规则数和字节数漂移基线。
- 按 40 位 Git Commit 生成 Direct/Modular 可复现发布包。
- 非阻断式服务端点性能基准框架。
- OpenAI、Apple、Telegram、流媒体回归用例扩充。
- RC3 GitHub Actions 构建、在线审计和发布 Artifact。

### Preserved
- Performance 继续允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 发布版继续关闭 IPv6。
- UDP 不支持时继续 REJECT。
- AdvertisingLite 继续作为默认广告拦截。
- OpenAI、Apple、Telegram、流媒体和国内流量保持策略隔离。

### Changed
- 远程规则审计阈值以 RC2 成功运行数据校准。
- 发布产物不再依赖可变 `main` URL。
- 临时导入标记不进入 RC3 项目目录。

### Limitations
- GitHub Runner 无法代表 iPhone 的真实延迟、带宽和运营商 DNS 行为。
- ECH 仍仅属于实验观察项，未宣称强制启用。
