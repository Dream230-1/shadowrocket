# 远程规则审计

`remote_audit.py` 对 `manifest.yaml` 中所有远程规则执行：

1. URL 必须包含固定的 40 位 Commit。
2. HTTP 下载必须成功且不能返回 HTML 错误页。
3. 文件体积不得超过 manifest 阈值。
4. 有效规则数必须位于设定区间。
5. 规则类型和基本字段必须可解析。
6. 输出 SHA-256、规则类型统计和本地缓存。

运行：

```bash
python scripts/remote_audit.py
```

报告：`reports/remote-audit.json`

Commit 固定意味着同一 URL 的内容理论上不可变；规则数量阈值主要用于发现错误路径、截断文件或 HTML 错误页。
