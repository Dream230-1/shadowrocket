// ==Shadowrocket==
// Name: 闲鱼去广告（http-request）
// Author: LOWERTOP
// ==/Shadowrocket==

// http-request 模式：直接返回空 JSON，阻断广告数据加载
$done({response: {
  status: 200,
  headers: {'Content-Type': 'application/json;charset=utf-8'},
  body: '{}'
}});
