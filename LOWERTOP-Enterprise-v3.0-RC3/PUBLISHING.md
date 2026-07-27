# 可复现发布

RC3 新增 `scripts/publish.py`。发布工具要求提供 40 位 Git Commit SHA，并据此生成：

- Direct 配置
- Modular 配置
- IPv6/SVCB Experimental 配置
- 自维护规则集
- 审计报告
- `CHECKSUMS.sha256`
- `release.json`

示例：

```bash
python scripts/publish.py \
  --source-ref "$GITHUB_SHA" \
  --repository Dream230-1/ShuntRules
```

Modular 配置中的自维护规则 URL 会固定到该 Commit，不引用 `main`，从而避免无感知规则漂移。
