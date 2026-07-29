/*
 * LOWERTOP Baidu Netdisk ads-only response filter.
 *
 * The module pattern limits execution to explicit advertising endpoints.
 * This script preserves response metadata and removes only explicit ad
 * containers. It never runs on login, account, membership, share, transfer,
 * file-list, playback, or download endpoints.
 */

var AD_KEYS = [
  "ad",
  "ads",
  "ad_info",
  "ad_data",
  "advert",
  "advertise",
  "advertisement",
  "splash",
  "splash_list",
  "banner",
  "banners"
];

function removeAdKeys(container) {
  var changed = false;
  if (!container || typeof container !== "object" || Array.isArray(container)) return changed;
  AD_KEYS.forEach(function (key) {
    if (Object.prototype.hasOwnProperty.call(container, key)) {
      delete container[key];
      changed = true;
    }
  });
  return changed;
}

function isAdItem(item) {
  if (!item || typeof item !== "object") return false;
  if (item.ad_id || item.adId || item.ad_info || item.adInfo) return true;
  if (item.is_ad === true || item.isAd === true) return true;
  var type = String(item.type || item.card_type || "").toLowerCase();
  return type === "ad" || type === "ads" || type === "advert" || type === "advertisement";
}

try {
  if (!$response || !$response.body) {
    $done({});
  } else {
    var payload = JSON.parse($response.body);
    var changed = false;

    if (Array.isArray(payload)) {
      var filtered = payload.filter(function (item) { return !isAdItem(item); });
      changed = filtered.length !== payload.length;
      payload = filtered;
    } else if (payload && typeof payload === "object") {
      changed = removeAdKeys(payload) || changed;
      changed = removeAdKeys(payload.data) || changed;
      changed = removeAdKeys(payload.result) || changed;

      ["list", "items"].forEach(function (key) {
        [payload, payload.data, payload.result].forEach(function (container) {
          if (container && Array.isArray(container[key])) {
            var before = container[key].length;
            container[key] = container[key].filter(function (item) { return !isAdItem(item); });
            changed = changed || container[key].length !== before;
          }
        });
      });
    }

    $done(changed ? { body: JSON.stringify(payload) } : {});
  }
} catch (error) {
  console.log("LOWERTOP Baidu Netdisk ads-only: " + error);
  $done({});
}
