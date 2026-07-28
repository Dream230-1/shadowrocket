// ==Shadowrocket==
// Name: 百度网盘去广告
// Author: LOWERTOP
// ==/Shadowrocket==

const url = $request.url;
const method = $request.method;

console.log(`[百度网盘] 拦截: ${url}`);

// 广告相关接口 → 返回空 JSON（等效 Loon 的 reject-dict）
if (/(api\/getconfig|api\/getsyscfg|api\/taskscore\/tasklist|act\/api\/activityentry|pcs\/adv|api\/plugin\/get)/.test(url)) {
  console.log(`[百度网盘] 拦截广告: ${url}`);
  $done({body: '{}'});
  return;
}

// 推荐列表 → 保留非广告类型
if (/recommend\/query\/list/.test(url)) {
  try {
    let obj = JSON.parse($response.body);
    if (obj && obj.data && obj.data.data) {
      obj.data.data = obj.data.data.filter(function(item) {
        return item.type !== 'novel' && item.type !== 'shortplay' && item.type !== 'print' && item.type !== 'job_hunt';
      });
    }
    $done({body: JSON.stringify(obj)});
  } catch(e) {
    $done();
  }
  return;
}

// 首页推荐 → 过滤广告类型
if (/feed\/kingkongdistrict/.test(url)) {
  $done();
  return;
}

$done();
