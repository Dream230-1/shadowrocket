// ==Shadowrocket==
// Name: 闲鱼去广告
// Author: LOWERTOP
// ==/Shadowrocket==

var url = $request.url;

// 闲鱼广告字段清理
try {
  var body = $response.body;
  if (!body || body.length < 20) { $done(); return; }
  
  if (body.charAt(0) === '{') {
    var obj = JSON.parse(body);
    var changed = false;
    
    // 递归删除广告字段
    function cleanAds(obj) {
      if (!obj || typeof obj !== 'object') return;
      var adKeys = ['ad', 'ads', 'adInfo', 'ad_info', 'advertisement', 'spm', 'adData', 'adList', 'banner', 'splash', 'recommendAds', 'advert'];
      for (var k in obj) {
        if (adKeys.indexOf(k) >= 0) {
          delete obj[k];
          changed = true;
        } else if (typeof obj[k] === 'object') {
          cleanAds(obj[k]);
        }
      }
    }
    
    cleanAds(obj);
    if (changed) { $done({body: JSON.stringify(obj)}); return; }
  }
} catch(e) {}

$done();
