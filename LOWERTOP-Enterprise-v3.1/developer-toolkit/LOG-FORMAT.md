# Shadowrocket 日志取证格式

`analyze_log.py` 采用宽松解析，不要求固定导出格式。建议每行至少包含以下内容中的两项：

```text
<URL 或 host:port> <命中规则> <最终策略> <HTTP 状态码>
```

示例：

```text
api.bilibili.com:443 DOMAIN-SUFFIX,bilibili.com,DIRECT HTTPS
https://api.bilibili.com/x/v3/fav/folder/created/list-all RULE-SET,AdvertisingLite,REJECT HTTP 403
app.bilibili.com:443 SCRIPT HTTP 200
```

## 推荐取证步骤

1. 清空请求日志。
2. 记录开始时间。
3. 只执行一个动作，例如点击“我的收藏”。
4. 记录结束时间。
5. 导出该时间段日志。
6. 使用多个关键字分析：

```bash
python3 developer-toolkit/analyze_log.py shadowrocket.log \
  --keyword bilibili \
  --keyword fav \
  --keyword favorite \
  --json-out reports/bilibili-favorites.json \
  --markdown-out reports/bilibili-favorites.md
```

## 结果解释

- `DIRECT`：仅表示路由策略为直连，不等于请求一定成功。
- `REJECT`：规则明确阻断，应优先定位所属规则集。
- `MITM` 或 `SCRIPT`：说明请求可能被解密或改写，应核对模块和 Hostname。
- HTTP `4xx/5xx`：服务端或客户端校验失败，需要保留完整路径和状态码。
- 日志没有异常但界面异常：继续检查响应内容、客户端缓存和聚合接口字段。
