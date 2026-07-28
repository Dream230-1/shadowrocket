// ==Shadowrocket==
// Name: 百度网盘去广告
// Author: LOWERTOP
// ==/Shadowrocket==

const url = $request.url;

// 广告配置接口 → 返回空 JSON
if (/(api\/getconfig|api\/getsyscfg|api\/taskscore\/tasklist|act\/api\/activityentry|pcs\/adv|api\/plugin\/get)/.test(url)) {
  $done({body: '{}'});
  return;
}

// 推荐列表 → 过滤广告类型
if (/recommend\/query\/list/.test(url)) {
  try {
    var obj = JSON.parse($response.body);
    if (obj && obj.data && obj.data.data) {
      var filtered = [];
      for (var i = 0; i < obj.data.data.length; i++) {
        var item = obj.data.data[i];
        if (item.type !== 'novel' && item.type !== 'shortplay' && item.type !== 'print' && item.type !== 'job_hunt') {
          filtered.push(item);
        }
      }
      obj.data.data = filtered;
    }
    $done({body: JSON.stringify(obj)});
  } catch(e) {
    $done();
  }
  return;
}

$done();
