# 服务级健康检查

## 能检查什么

- TLS/HTTP 是否可连接
- HTTP 状态码
- 重定向位置
- 响应延迟
- Apple success 页面正文
- 指定 HTTP/HTTPS/SOCKS5 代理路径

## 不能自动检查什么

- iPhone Shadowrocket 中每一个节点
- ChatGPT 登录状态
- OpenAI 账号是否触发地区限制
- Netflix/Disney/MAX 具体账号的版权库解锁
- Telegram App 的完整 MTProto/UDP 行为

## 示例

```bash
python scripts/service_health.py --allow-warnings
python scripts/service_health.py --proxy socks5h://127.0.0.1:1080 --allow-warnings
python scripts/service_health.py --only openai_web --only telegram_web --allow-warnings
```

报告：`reports/service-health.json`
