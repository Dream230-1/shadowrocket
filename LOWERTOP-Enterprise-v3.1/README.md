# LOWERTOP Enterprise v3.1 RC4

RC4 在保留 RC3 路由、DNS、策略组和 `FINAL,PROXY` 行为的基础上，重点改进 MITM 模块安全性、工具模块和可回滚能力。主配置继续保持稳定，广告增强与天气增强以独立模块提供，不会自动启用。

## RC4 主要变化

1. **哔哩哔哩结构化去广告模块**：基于 BiliUniverse 官方 Shadowrocket 模板处理 JSON 与 gRPC，覆盖开屏、信息流、视频相关推荐、搜索、动态、直播推广及评论区广告；不再整接口返回空 JSON，也不伪造会员状态。
2. **百度网盘保守实验模块**：只拦截已识别的活动入口、福利推广、游戏中心和广告配置接口，不修改账号、会员、下载、分享或视频主链路。
3. **Apple 天气 QWeather 模块**：基于 NSRingo WeatherKit v3.1.0，API Host 与 Token 通过 Shadowrocket 本地模块参数填写，仓库中不保存真实凭证。
4. **当前出口 IP 质量检测**：检测当前实际出口 IP、ASN、网络类型和风险标记；运行前需先切换至目标节点。
5. **生成器结构修复**：`[Rule]`、`[Script]` 与 `[MITM]` 分段独立校验，避免规则误写入脚本段或遗漏解密主机。
6. **安全审计**：CI 阻止会员伪造、整接口清空、明文 API Key、过宽百度规则以及非 `%APPEND%` MITM 模块进入 RC4。

## 模块目录

```text
modules/optional/
├── Bilibili.ADBlock.RC4.sgmodule
├── AppleWeather.QWeather.RC4.sgmodule
└── IPQuality.CurrentEgress.sgmodule

modules/experimental/
└── BaiduNetdisk.AdBlock.Experimental.sgmodule
```

模块安装、启用顺序、验证项目和回滚方法见 `releases/v3.1-rc4/MODULES.md`。

## 保持不变

- Performance 允许 QUIC/HTTP3。
- 禁止系统 DNS 回退。
- 境外备用 DoH 继续通过 `#proxy`。
- 发布配置关闭 IPv6。
- UDP 策略不支持时使用 `REJECT`，不回落至直连。
- AdvertisingLite 默认启用。
- OpenAI、Apple、Telegram、流媒体、中国大陆与最终规则的顺序保持现有行为。

## 构建与验证

```bash
python -m pip install -r requirements.txt
python scripts/ci.py
python scripts/ci.py --online
```

RC4 自动检查包括：

- 单元测试与行为锁；
- DNS、远程规则和冲突审计；
- 脚本配置与模块安全审计；
- 生成配置分段校验；
- API Key 与疑似凭证扫描；
- 设备验证记录和发布报告。

## 发布边界

- 三个增强模块在 RC4 阶段均为手动安装，不自动写入 Direct 主配置。
- 哔哩哔哩模块运行包在 RC 验证期跟随官方最新 Release；稳定版前必须固定到已验证版本。
- 百度网盘模块在完成登录、下载、分享和在线播放回归前保持 Experimental。
- Apple 天气模块的真实 QWeather Token 只能保存在本机参数中；此前公开过的 Token 应先轮换。
- 请采用替换导入，不要与旧配置合并。
