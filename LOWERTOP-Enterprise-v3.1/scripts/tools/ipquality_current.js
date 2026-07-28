// ==Shadowrocket==
// Name: Current Egress IP Quality
// Description: Inspect the currently active Shadowrocket egress. Detect on network change and scheduled polling.
// Source inspiration: MaYIHEI/paperclip ipquality
// ==/Shadowrocket==

const TIMEOUT_MS = 10000;
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148";
const STORE_KEY = "LOWERTOP_RC4_LAST_EGRESS_IP";

function requestJSON(url) {
  return new Promise((resolve, reject) => {
    $httpClient.get(
      { url, headers: { Accept: "application/json", "User-Agent": UA }, timeout: TIMEOUT_MS / 1000 },
      (error, response, body) => {
        if (error) return reject(new Error(String(error)));
        const status = Number(response && (response.status || response.statusCode));
        if (!Number.isFinite(status) || status < 200 || status >= 300) {
          return reject(new Error(`HTTP ${status || "?"}`));
        }
        try { resolve(JSON.parse(body || "{}")); }
        catch (_) { reject(new Error("JSON parse failed")); }
      }
    );
  });
}

function clean(value) {
  return value === null || value === undefined || value === "" ? "-" : String(value);
}

function yesNo(value) {
  return value === true ? "是" : value === false ? "否" : "未知";
}

function riskLevel(score, flags) {
  if (flags.tor || flags.proxy || flags.vpn || flags.datacenter || score >= 75) return "高风险";
  if (score >= 40) return "中风险";
  if (Number.isFinite(score)) return "低风险";
  return "未确认";
}

function notify(title, subtitle, body) {
  if (typeof $notification !== "undefined" && $notification.post) {
    $notification.post(title, subtitle, body);
  }
}

function shouldNotify(ip) {
  const argument = typeof $argument === "string" ? $argument : "";
  const force = /(?:^|&)force=1(?:&|$)/.test(argument);
  const previous = $persistentStore.read(STORE_KEY);
  $persistentStore.write(ip, STORE_KEY);
  return force || !previous || previous !== ip;
}

async function main() {
  const ipResult = await requestJSON("https://api4.ipify.org?format=json");
  const ip = clean(ipResult.ip);
  if (ip === "-") throw new Error("无法获取当前出口 IP");

  if (!shouldNotify(ip)) return;

  const results = await Promise.allSettled([
    requestJSON(`https://api.ipapi.is/?q=${encodeURIComponent(ip)}`),
    requestJSON("https://my.ippure.com/v1/info"),
    requestJSON(`https://ipwho.is/${encodeURIComponent(ip)}`),
  ]);

  const ipapi = results[0].status === "fulfilled" ? results[0].value : {};
  const ippure = results[1].status === "fulfilled" ? results[1].value : {};
  const ipwho = results[2].status === "fulfilled" ? results[2].value : {};

  const fraudScore = Number(ippure.fraudScore);
  const flags = {
    proxy: Boolean(ipapi.is_proxy || ipwho.proxy),
    vpn: Boolean(ipapi.is_vpn),
    tor: Boolean(ipapi.is_tor),
    datacenter: Boolean(ipapi.is_datacenter || ipapi.is_hosting || ipwho.hosting),
  };

  const company = ipapi.company || {};
  const asn = ipapi.asn || {};
  const location = ipapi.location || {};
  const risk = riskLevel(fraudScore, flags);
  const scoreText = Number.isFinite(fraudScore) ? String(fraudScore) : "未返回";
  const country = clean(location.country_code || ipwho.country_code);
  const region = clean(location.state || ipwho.region);
  const city = clean(location.city || ipwho.city);
  const asnText = clean(asn.asn || (ipwho.connection && ipwho.connection.asn));
  const org = clean(company.name || asn.org || (ipwho.connection && ipwho.connection.org));
  const networkType = clean(company.type || ipapi.type);

  const subtitle = `${risk} · IPPure ${scoreText}`;
  const body = [
    `IP  ${ip}`,
    `地区  ${country} · ${region} · ${city}`,
    `ASN  ${asnText}`,
    `组织  ${org}`,
    `类型  ${networkType}`,
    `代理 ${yesNo(flags.proxy)} ｜ VPN ${yesNo(flags.vpn)}`,
    `Tor ${yesNo(flags.tor)} ｜ 机房 ${yesNo(flags.datacenter)}`,
  ].join("\n");

  notify("节点 IP 质量检测", subtitle, body);
}

main()
  .catch((error) => {
    notify("节点 IP 质量检测失败", "请检查网络或稍后重试", String(error && error.message ? error.message : error));
  })
  .finally(() => $done());
