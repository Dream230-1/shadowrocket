/*
 * LOWERTOP Bilibili ads-only response filter.
 *
 * Scope:
 * - app.bilibili.com/x/v2/splash/{list,show}
 * - app.bilibili.com/x/v2/feed/index
 *
 * This script only removes objects carrying explicit advertising markers.
 * It does not inspect or modify account, VIP, favorites, history, comments,
 * playback authorization, purchases, or navigation tabs.
 */

function finish(body) {
  $done({ body: JSON.stringify(body) });
}

function isAdItem(item) {
  if (!item || typeof item !== "object") return false;
  if (item.ad_info || item.adInfo || item.ad_id || item.adId) return true;
  if (item.is_ad === true || item.isAd === true) return true;

  var cardType = String(item.card_type || "");
  var cardGoto = String(item.card_goto || "");
  if (/^cm(_|$)/.test(cardType)) return true;
  return [
    "ad",
    "ad_av",
    "ad_web_s",
    "ad_web_gif",
    "ad_player",
    "ad_inline_3d",
    "ad_inline_eggs",
    "ad_inline_av"
  ].indexOf(cardGoto) >= 0;
}

try {
  if (!$response || !$response.body) {
    $done({});
  } else {
    var payload = JSON.parse($response.body);
    var data = payload && payload.data;
    var url = $request && $request.url ? $request.url : "";

    if (data && url.indexOf("/x/v2/splash/") >= 0) {
      if (Array.isArray(data.show)) {
        data.show = data.show.filter(function (item) { return !isAdItem(item); });
      }
      if (Array.isArray(data.list)) {
        data.list = data.list.filter(function (item) { return !isAdItem(item); });
      }
      finish(payload);
    } else if (data && url.indexOf("/x/v2/feed/index") >= 0 && Array.isArray(data.items)) {
      data.items = data.items.reduce(function (kept, item) {
        if (isAdItem(item)) return kept;
        if (Array.isArray(item && item.banner_item)) {
          item.banner_item = item.banner_item.filter(function (banner) {
            return !isAdItem(banner) && String(banner && banner.type || "").toLowerCase() !== "ad";
          });
          if (item.banner_item.length === 0) return kept;
        }
        kept.push(item);
        return kept;
      }, []);
      finish(payload);
    } else {
      $done({});
    }
  }
} catch (error) {
  console.log("LOWERTOP Bilibili ads-only: " + error);
  $done({});
}
