// ==Shadowrocket==
// Name: 百度网盘请求拦截
// Author: LOWERTOP
// ==/Shadowrocket==

// http-request 模式：在请求发出前直接返回空响应
$done({response: {
  status: 200,
  headers: {'Content-Type': 'application/json'},
  body: '{}'
}});
