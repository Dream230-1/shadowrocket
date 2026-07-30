'use strict';

const url = $request.url;

function finish(body) {
  $done({ body: JSON.stringify(body) });
}

try {
  const body = JSON.parse($response.body);

  if (/^https?:\/\/(t7z|kjp)\.cupid\.iqiyi\.com\/mixer\?/.test(url)) {
    delete body.adSlots;
    finish(body);
  } else if (/^https?:\/\/capis(-?\w*)?\.didapinche\.com\/ad\/cx\/startup\?/.test(url)) {
    body.show_time = 0;
    body.full_screen = 0;
    body.startupPages = [];
    finish(body);
  } else if (/^https?:\/\/fmapp\.chinafamilymart\.com\.cn\/api\/app\/market\/start\/ad/.test(url)) {
    body.data = {};
    finish(body);
  } else if (/^https?:\/\/app\.bilibili\.com\/x\/v2\/splash\/(show|list)/.test(url)) {
    const data = body.data;
    if (data && typeof data === 'object') {
      data.max_time = 0;
      data.min_interval = 31536000;
      data.pull_interval = 31536000;
      if (Array.isArray(data.show)) data.show = [];
      if (Array.isArray(data.list)) {
        data.list = [];
      } else if (data.list && typeof data.list === 'object') {
        if (Array.isArray(data.list.show)) data.list.show = [];
        if (Array.isArray(data.list.list)) data.list.list = [];
      }
    }
    finish(body);
  } else if (/^https?:\/\/wmapi\.meituan\.com\/api\/v\d+\/loadInfo\?/.test(url)) {
    const startpicture = body?.data?.startpicture;
    if (startpicture && typeof startpicture === 'object') {
      if (Object.prototype.hasOwnProperty.call(startpicture, 'ad')) startpicture.ad = [];
      if (Object.prototype.hasOwnProperty.call(startpicture, 'mk')) startpicture.mk = [];
    }
    finish(body);
  } else if (/^https?:\/\/hd\.mina\.mi\.com\/splashscreen\/alert/.test(url)) {
    body.data = [];
    finish(body);
  } else if (/^https?:\/\/api\.m\.jd\.com\/client\.action\?functionId=start/.test(url)) {
    body.images = [];
    body.countdown = 0;
    body.showTimesDaily = 0;
    finish(body);
  } else if (/^https?:\/\/mi\.gdt\.qq\.com\/gdt_mview\.fcg/.test(url)) {
    body.seq = '0';
    body.reqinterval = 0;
    delete body.last_ads;
    delete body.data;
    finish(body);
  } else if (/^https?:\/\/cmsapi\.dmall\.com\/app\/home\/homepageStartUpPic/.test(url)) {
    if (body?.data && typeof body.data === 'object') body.data.welcomePage = [];
    finish(body);
  } else if (/^https?:\/\/gw\.yolanda\.hk\/api\/servlets\?endpoint=banners\/show_launch_banner/.test(url)) {
    body.code = body.code ?? '200';
    body.msg = body.msg ?? 'ok';
    body.data = { present_flag: 0, banner: null };
    finish(body);
  } else {
    $done({});
  }
} catch (error) {
  console.log(`[LOWERTOP startup-ad-lite] ${String(error)}`);
  $done({});
}
