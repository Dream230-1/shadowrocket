# Performance 基准框架

RC3 保持 Performance 版允许 QUIC/HTTP3，并新增非阻断式端点基准工具：

```bash
python scripts/network_benchmark.py
```

通过本地 Shadowrocket SOCKS5 测试：

```bash
python scripts/network_benchmark.py --proxy socks5h://127.0.0.1:7221
```

记录每个端点的成功率、中位延迟、最小值、最大值和 HTTP 状态。公共 GitHub Runner 的绝对延迟不能代表 iPhone 实际速度，只适合同环境版本对比。
