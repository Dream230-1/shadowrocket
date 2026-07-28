// ==Shadowrocket==
// Name: 百度网盘去广告
// Author: LOWERTOP
// ==/Shadowrocket==

var url = $request.url;

try {
  var body = $response.body;
  if (!body || body.length < 10) { $done(); return; }
  
  // 只处理 JSON 响应
  if (body.charAt(0) === '{' || body.charAt(0) === '[') {
    var obj = JSON.parse(body);
    var modified = false;
    
    // 已知广告路径
    var adPaths = [
      '/api/getconfig', '/api/getsyscfg', '/api/taskscore/tasklist',
      '/act/api/activityentry', '/pcs/adv', '/api/plugin/get',
      '/api/getsplash', '/api/splash', '/api/ad'
    ];
    for (var i = 0; i < adPaths.length; i++) {
      if (url.indexOf(adPaths[i]) >= 0) {
        $done({body: '{}'});
        return;
      }
    }
    
    // 通用广告字段清理（任何 JSON 响应都检查）
    if (obj && typeof obj === 'object') {
      var adKeys = ['ad', 'ads', 'ad_info', 'ad_data', 'splash', 'banner'];
      for (var k = 0; k < adKeys.length; k++) {
        if (obj[adKeys[k]] !== undefined) {
          delete obj[adKeys[k]];
          modified = true;
        }
      }
      if (obj.data && typeof obj.data === 'object') {
        for (var k = 0; k < adKeys.length; k++) {
          if (obj.data[adKeys[k]] !== undefined) {
            delete obj.data[adKeys[k]];
            modified = true;
          }
        }
      }
    }
    
    if (modified) {
      $done({body: JSON.stringify(obj)});
      return;
    }
  }
} catch(e) {
  // 静默失败
}

$done();
