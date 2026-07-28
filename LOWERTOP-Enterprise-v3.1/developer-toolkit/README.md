# LOWERTOP Shadowrocket Developer Toolkit

用于开发、审计和回归验证 Shadowrocket 配置与模块。

## 当前能力

1. `validate_module.py`
   - 校验模块元数据、区块名称和脚本类型。
   - 检查 `%APPEND%`、MITM Hostname 和远程脚本 URL。
   - 明确拒绝 Shadowrocket 不支持的 `type=generic`。
   - 将整接口空对象、浮动 `releases/latest` 等高风险写法标记为警告。

2. `extract_mitm.py`
   - 从 `.sgmodule`、`.srmodule`、`.module`、`.conf` 中提取 MITM Hostname。
   - 输出去重后的 Hostname、来源文件、行号与 `%APPEND%` 状态。
   - 检查通配符、URL 误填和无效格式。

3. `analyze_log.py`
   - 分析 Shadowrocket 导出的文本日志或整理后的请求记录。
   - 汇总 DIRECT、PROXY、REJECT、MITM、SCRIPT、HTTP 状态码和命中规则。
   - 支持按多个关键字筛选，例如 `bilibili`、`fav`、`baidu`。
   - 可在发现 REJECT 时返回失败退出码，便于自动化回归。

4. Toolkit CI
   - 工作流：`.github/workflows/developer-toolkit.yml`。
   - 自动编译脚本、运行回归测试、校验模块并生成 MITM 审计报告。
   - 报告以 GitHub Actions Artifact 形式保存。

5. `audit_coverage.py`
   - 对照 RC 主配置审计可选模块的 Script、URL Rewrite、Map Local 与 MITM 覆盖范围。
   - 阻断重复脚本名、跨机制相同匹配表达式和主配置与模块间重复 MITM Hostname。
   - 输出包含来源文件、行号和覆盖机制的 JSON 报告。

## 使用示例

在 `LOWERTOP-Enterprise-v3.1` 目录执行：

```bash
python3 developer-toolkit/validate_module.py modules/optional/AppleWeather.QWeather.RC4.sgmodule
python3 developer-toolkit/validate_module.py modules/optional --json-out reports/modules.json
python3 developer-toolkit/extract_mitm.py modules/optional --unique
python3 developer-toolkit/audit_coverage.py \
  --base-config ../releases/v3.1-rc4/LOWERTOP-Enterprise-v3.1-RC4-Performance-Direct.conf \
  modules/optional --json-out reports/developer-toolkit-coverage.json
python3 developer-toolkit/analyze_log.py shadowrocket.log --keyword bilibili --keyword fav \
  --json-out reports/bilibili-log.json --markdown-out reports/bilibili-log.md
```

## Shadowrocket 实机证据流程

1. 关闭与测试目标无关的模块和 HTTPS 解密域名。
2. 清空 Shadowrocket 请求日志。
3. 执行单一测试动作，例如打开“我的收藏”或冷启动百度网盘。
4. 导出文本日志，或按时间顺序整理为一行一条请求记录。
5. 使用 `analyze_log.py` 分析域名、策略、规则和异常状态码。
6. 只有在核心功能回归通过后，才扩大广告接口覆盖范围。

## 开发原则

- 不允许以去广告为由修改会员、账号或付费状态。
- 不允许对核心业务域名做无边界 REJECT。
- 不允许在未做实机回归前把实验模块并入主配置。
- JSON 和 protobuf 响应应做字段级修改，避免整接口清空。
- 每个模块必须保留明确的回滚入口和实机验证记录。
- 自动化静态通过不能替代真实设备验证。

## v0.2 当前阶段

- 模块与主配置冲突检查
- URL Rewrite、Map Local、Script 与 MITM 覆盖范围报告

## 后续阶段

- JSON 响应差异分析器
- protobuf/gRPC 请求识别与样本登记
- 请求样本匿名化工具
- Bilibili Next 与 BaiduNetdisk Next 独立实验目录
