# Developer Toolkit Roadmap

## v0.1 已完成

- Shadowrocket 模块静态校验
- MITM Hostname 提取与风险检查
- 文本日志策略、规则和状态码分析
- 最小回归测试
- 独立 GitHub Actions 工作流与审计产物

## v0.2 进行中

- [x] 模块与主配置冲突检查
- [x] URL Rewrite、Map Local、Script 与 MITM 覆盖范围报告
- [ ] JSON 响应差异分析器
- [ ] 请求样本匿名化工具

## v0.3

- protobuf/gRPC 方法识别与样本登记
- Bilibili Next 单接口实验框架
- BaiduNetdisk Next 开屏接口实验框架

## 发布约束

- Bilibili Next 和 BaiduNetdisk Next 不自动注入主配置。
- 未完成真实设备回归的模块只能保留在 Experimental。
- 出现账号、收藏、下载、分享或播放回归时立即停止扩大覆盖范围。
