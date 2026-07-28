# LOWERTOP Shadowrocket Developer Toolkit

用于开发、审计和回归验证 Shadowrocket 配置与模块。

## 当前能力

1. `validate_module.py`
   - 校验模块元数据、区块名称和脚本类型。
   - 检查 `%APPEND%`、MITM Hostname 和远程脚本 URL。
   - 标记高风险用法，例如整接口返回空对象、未知脚本类型和过宽 Hostname。

2. `extract_mitm.py`
   - 从 `.sgmodule`、`.srmodule`、`.conf` 中提取 MITM Hostname。
   - 输出去重后的 Hostname 清单。
   - 可用于核对需要手动加入 HTTPS 解密的域名。

3. `analyze_log.py`
   - 分析从 Shadowrocket 导出的文本日志。
   - 汇总 DIRECT、PROXY、REJECT、MITM、SCRIPT 等命中情况。
   - 支持按关键字筛选，例如 `bilibili`、`fav`、`baidu`。

## 使用示例

```bash
python3 developer-toolkit/validate_module.py modules/optional/Bilibili.ADBlock.RC4.sgmodule
python3 developer-toolkit/extract_mitm.py modules/optional/Bilibili.ADBlock.RC4.sgmodule
python3 developer-toolkit/analyze_log.py shadowrocket.log --keyword bilibili
```

## 开发原则

- 不允许以去广告为由修改会员、账号或付费状态。
- 不允许对核心业务域名做无边界 REJECT。
- 不允许在未做实机回归前把实验模块并入主配置。
- JSON 和 protobuf 响应应做字段级修改，避免整接口清空。
- 每个模块必须保留明确的回滚入口和实机验证记录。

## 下一阶段

- JSON 差异分析器
- protobuf/gRPC 请求识别
- 模块与主配置冲突检查
- CI 自动生成模块审计报告
