// ==Shadowrocket==
// Name: Current Egress IP Quality
// Description: Inspect the currently active Shadowrocket egress after a network or proxy change.
// Source inspiration: MaYIHEI/paperclip ipquality
// ==/Shadowrocket==

const TIMEOUT_MS = 10000;
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148";

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
        try {
          resolve(JSON.parse(body || "{}"));
        } catch (_) {
          reject(new Error("JSON parse failed"));
        }
      }
    );
  });
}

function clean(value) {
  return value === null || value === undefined || value === "" ? "-" : String(value);
}

function boolFlag(value) {
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

async function main() {
  const ipResult = await requestJSON("https://api4.ipify.org?format=json");
  const ip = clean(ipResult.ip);
  if (ip === "-") throw new Error("无法获取当前出口 IP");

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
  const countryCode = clean(location.country_code || ipwho.country_code);
  const region = clean(location.state || ipwho.region);
  const city = clean(location.city || ipwho.city);
  const scoreText = Number.isFinite(fraudScore) ? String(fraudScore) : "未返回";
  const risk = riskLevel(fraudScore, flags);

  const lines = [
    `出口 IP：${ip}`,
    `风险结论：${risk}`,
    `IPPure 评分：${scoreText}`,
    `国家/地区：${countryCode} ${region} ${city}`,
    `ASN：${clean(asn.asn || (ipwho.connection && ipwho.connection.asn))}`,
    `运营组织：${clean(company.name || asn.org || (ipwho.connection && ipwho.connection.org))}`,
    `网络类型：${clean(company.type || ipapi.type)}`,
    `代理：${boolFlag(flags.proxy)}  VPN：${boolFlag(flags.vpn)}`,
    `Tor：${boolFlag(flags.tor)}  数据中心：${boolFlag(flags.datacenter)}`,
  ];

  notify("节点 IP 质量检测", `${risk} · ${ip}`, lines.join("\n"));
  $done();
}

main().catch((error) => {
  notify("节点 IP 质量检测失败", "请确认网络已连接", String(error && error.message ? error.message : error));
  $done();
});
