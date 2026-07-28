// ==Shadowrocket==
// name: 百度网盘去广告
// description: 移除百度网盘开屏广告、首页卡片、传输页面广告、弹窗
// author: LOWERTOP (ported from Moli-X Loon plugin)
// ==/Shadowrocket==

// pan.baidu.com/api/getconfig → 广告配置
// pan.baidu.com/api/getsyscfg → 系统广告配置
// pan.baidu.com/api/taskscore/tasklist → 任务列表广告
// pan.baidu.com/act/api/activityentry → 活动入口广告
// pan.baidu.com/rest/1.0/pcs/adv → 广告
// pan.baidu.com/api/plugin/get → 插件推荐
// pan.baidu.com/recommend/query/list → 推荐列表广告

const url = $request.url;
const body = $response.body;

if (body) {
  let obj = JSON.parse(body);
  
  // /api/getconfig - 清空广告配置
  if (url.includes('/api/getconfig')) {
    if (obj.data) {
      delete obj.data.ad;
      delete obj.data.ads;
      delete obj.data.ad_config;
    }
  }
  
  // /api/taskscore/tasklist - 清空任务广告
  if (url.includes('/api/taskscore/tasklist')) {
    if (obj.data) obj.data = [];
  }
  
  // /act/api/activityentry - 清空活动入口
  if (url.includes('/act/api/activityentry')) {
    if (obj.data) obj.data = [];
  }
  
  // /rest/*/pcs/adv - 清空广告
  if (url.includes('/pcs/adv')) {
    if (obj.data) obj.data = [];
  }
  
  // /api/plugin/get - 清空插件推荐
  if (url.includes('/api/plugin/get')) {
    if (obj.data) obj.data = [];
  }
  
  // /recommend/query/list - 过滤推荐中的广告类型
  if (url.includes('/recommend/query/list')) {
    if (obj.data && obj.data.data) {
      obj.data.data = obj.data.data.filter(item => 
        item.type !== 'novel' && item.type !== 'shortplay' && 
        item.type !== 'print' && item.type !== 'job_hunt'
      );
    }
  }

  $done({body: JSON.stringify(obj)});
} else {
  $done();
}
