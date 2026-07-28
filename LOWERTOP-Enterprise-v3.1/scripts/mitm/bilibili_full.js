// ==Shadowrocket==
// Name: Bilibili 完整去广告
// Author: LOWERTOP (ported from Moli-X Loon plugin)
// ==/Shadowrocket==

var url = $request.url;
var method = $request.method;

// === 工具函数 ===
function emptyJson() {
  $done({response: {status: 200, headers: {'Content-Type': 'application/json;charset=utf-8'}, body: '{}'}});
}

function mockJson(data) {
  $done({response: {status: 200, headers: {'Content-Type': 'application/json;charset=utf-8'}, body: JSON.stringify(data)}});
}

function modifyBody(fn) {
  try {
    var body = $response.body;
    if (body) {
      var obj = JSON.parse(body);
      fn(obj);
      $done({body: JSON.stringify(obj)});
      return true;
    }
  } catch(e) {}
  return false;
}

// === 开屏广告 ===
if (url.indexOf('/x/v2/splash/list') >= 0) {
  mockJson({
    code: 0, message: "0", ttl: 1,
    data: {max_time: 0, min_interval: 31536000, pull_interval: 31536000, keep_ids: [], show: [], list: [{}], splash_request_id: ""}
  });
  return;
}
if (url.indexOf('/x/v2/splash/') >= 0) {
  modifyBody(function(obj) { if (obj && obj.data) { obj.data.show = []; obj.data.event_list = []; } });
  return;
}

// === 信息流广告 ===
// feed/index - 过滤信息流中的广告
if (url.indexOf('/x/v2/feed/index') >= 0 && url.indexOf('/story') < 0) {
  modifyBody(function(obj) {
    if (obj && obj.data && obj.data.items) {
      obj.data.items = obj.data.items.filter(function(item) {
        return !item.banner_item && !item.ad_info && item.card_goto === 'av' && 
               ['small_cover_v2', 'large_cover_single_v9', 'large_cover_v1'].indexOf(item.card_type) >= 0;
      });
    }
  });
  return;
}

// feed/index/story - 过滤 story 模式广告
if (url.indexOf('/x/v2/feed/index/story') >= 0) {
  modifyBody(function(obj) {
    if (obj && obj.data && obj.data.items) {
      obj.data.items = obj.data.items.filter(function(item) {
        return !item.ad_info && ['vertical_ad_av', 'vertical_ad_live', 'vertical_ad_picture'].indexOf(item.card_goto) < 0;
      });
    }
  });
  return;
}

// === 直播间广告 ===
if (url.indexOf('/xlive/e-commerce-interface/v1/ecommerce-user/get_shopping_info') >= 0) { emptyJson(); return; }
if (url.indexOf('/xlive/app-interface/v2/index/feed') >= 0) { emptyJson(); return; }
if (url.indexOf('/xlive/app-room/v1/index/getInfoByRoom') >= 0 || url.indexOf('/xlive/app-room/v1/index/getInfoByUser') >= 0) { emptyJson(); return; }

// === 资源/活动/弹窗广告 ===
if (url.indexOf('/x/resource/show/tab/v2') >= 0) { emptyJson(); return; }
if (url.indexOf('/x/resource/show/skin') >= 0) {
  modifyBody(function(obj) { if (obj && obj.data) delete obj.data.common_equip; });
  return;
}
if (url.indexOf('/x/resource/top/activity') >= 0 || url.indexOf('/x/resource/patch/tab') >= 0 || url.indexOf('/x/v2/search/square') >= 0) {
  emptyJson(); return;
}

// === PGC/影视页广告 ===
if (url.indexOf('/pgc/activity/deliver/material/receive') >= 0) {
  mockJson({code: 0, data: {closeType: "close_win", container: [], showTime: ""}, message: "success"});
  return;
}
if (url.indexOf('/pgc/page/channel') >= 0) {
  modifyBody(function(obj) {
    if (obj && obj.data && obj.data.modules) {
      obj.data.modules = obj.data.modules.filter(function(m) { return m.type !== 'TIP'; });
    }
  });
  return;
}

$done();
