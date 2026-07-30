'use strict';

try {
  const body = JSON.parse($response.body);
  if (Array.isArray(body.resources)) {
    body.resources = body.resources.filter((item) => {
      const resourceUrl = String(item?.url ?? '');
      return !resourceUrl.includes('/ad');
    });
  }
  $done({ body: JSON.stringify(body) });
} catch (error) {
  console.log(`[LOWERTOP fanqie-ad-lite] ${String(error)}`);
  $done({});
}
