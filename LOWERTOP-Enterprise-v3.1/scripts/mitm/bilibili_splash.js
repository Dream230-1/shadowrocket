// ==Shadowrocket==
// Name: Bilibili 去广告
// Author: LOWERTOP (ported from Moli-X Loon plugin)
// ==/Shadowrocket==

var url = $request.url;

// === 开屏广告 ===

// /x/v2/splash/list - 直接返回空开屏数据
if (url.indexOf('/x/v2/splash/list') >= 0) {
  $done({
    response: {
      status: 200,
      headers: {'Content-Type': 'application/json;charset=utf-8'},
      body: JSON.stringify({
        "code": 0, "message": "0", "ttl": 1,
        "data": {
          "max_time": 0, "min_interval": 31536000,
          "pull_interval": 31536000, "keep_ids": [],
          "show": [], "list": [{}],
          "splash_request_id": ""
        }
      })
    }
  });
  return;
}

// /x/v2/splash/show 或 /x/v2/splash/event/list2 - 清空开屏数据
if (url.indexOf('/x/v2/splash/') >= 0) {
  try {
    var body = $response.body;
    if (body) {
      var obj = JSON.parse(body);
      if (obj && obj.data) {
        obj.data.show = [];
        obj.data.event_list = [];
      }
      $done({body: JSON.stringify(obj)});
      return;
    }
  } catch(e) {}
}

$done();
