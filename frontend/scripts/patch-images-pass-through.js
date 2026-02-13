/**
 * Overwrites .open-next/cloudflare/images.js with a pass-through-only implementation
 * that never references env.IMAGES. This avoids Wrangler pulling in the Images WASM
 * (resvg.wasm), which fails on Windows due to path + "?module".
 *
 * Run after: npm run build:cloudflare (or as part of deploy:cloudflare).
 * Location: frontend/scripts/patch-images-pass-through.js
 */

const fs = require("fs");
const path = require("path");

const OUT_PATH = path.join(
  __dirname,
  "..",
  ".open-next",
  "cloudflare",
  "images.js"
);

const PASS_THROUGH_IMAGES_JS = `/**
 * Pass-through image handler (no env.IMAGES / no WASM).
 * Patched by scripts/patch-images-pass-through.js for Windows deploy.
 */
function createImageResponse(stream, contentType, flags) {
  const r = new Response(stream, {
    headers: {
      Vary: "Accept",
      "Content-Type": contentType,
      "Content-Disposition": "attachment",
      "Content-Security-Policy": "script-src 'none'; frame-src 'none'; sandbox;",
    },
  });
  if (flags.immutable) {
    r.headers.set("Cache-Control", "public, max-age=315360000, immutable");
  }
  return r;
}

const ALLOWED = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "image/avif",
  "image/svg+xml",
];

function detectContentType(bytes) {
  if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return "image/jpeg";
  if ([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a].every((b, i) => bytes[i] === b)) return "image/png";
  if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x38) return "image/gif";
  if (bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50) return "image/webp";
  if (bytes[0] === 0x3c && (bytes[1] === 0x3f || bytes[1] === 0x73)) return "image/svg+xml";
  if (bytes[4] === 0x66 && bytes[5] === 0x74 && bytes[6] === 0x79 && bytes[7] === 0x70) return "image/avif";
  return null;
}

async function fetchWithRedirects(url, timeoutMs, maxRedirects) {
  const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs), redirect: "manual" });
  if ([301, 302, 303, 307, 308].includes(res.status)) {
    const loc = res.headers.get("Location");
    if (loc && maxRedirects > 0) {
      const next = loc.startsWith("/") ? new URL(loc, url).href : loc;
      return fetchWithRedirects(next, timeoutMs, maxRedirects - 1);
    }
    return { ok: false, error: "too_many_redirects" };
  }
  return { ok: true, response: res };
}

export async function handleImageRequest(requestURL, requestHeaders, env) {
  const urlParam = requestURL.searchParams.get("url");
  if (!urlParam) {
    return new Response('"url" parameter is required', { status: 400 });
  }
  let imageResponse;
  if (urlParam.startsWith("/")) {
    if (!env.ASSETS) {
      return new Response('"url" parameter is valid but upstream response is invalid', { status: 404 });
    }
    const absoluteURL = new URL(urlParam, requestURL);
    imageResponse = await env.ASSETS.fetch(absoluteURL);
  } else {
    try {
      const result = await fetchWithRedirects(urlParam, 7000, 3);
      if (!result.ok) {
        if (result.error === "timed_out") return new Response("upstream response timed out", { status: 504 });
        return new Response("upstream response is invalid", { status: 508 });
      }
      imageResponse = result.response;
    } catch (e) {
      throw new Error("Failed to fetch image", { cause: e });
    }
  }
  if (!imageResponse.ok || !imageResponse.body) {
    return new Response('"url" parameter is valid but upstream response is invalid', { status: imageResponse.status });
  }
  const [headStream, bodyStream] = imageResponse.body.tee();
  const header = new Uint8Array(32);
  const reader = headStream.getReader({ mode: "byob" });
  let chunk;
  try {
    chunk = await reader.read(header);
  } catch {
    await imageResponse.body.cancel();
    return new Response("invalid", { status: 400 });
  }
  if (!chunk.value || chunk.value.byteLength < 8) {
    await imageResponse.body.cancel();
    return new Response("invalid", { status: 400 });
  }
  const bytes = new Uint8Array(32);
  bytes.set(new Uint8Array(chunk.value.buffer, chunk.value.byteOffset, chunk.value.byteLength));
  const contentType = detectContentType(bytes);
  if (!contentType || !ALLOWED.includes(contentType)) {
    return new Response("image type is not allowed", { status: 400 });
  }
  const immutable = imageResponse.headers.get("Cache-Control")?.includes("immutable") ?? false;
  return createImageResponse(bodyStream, contentType, { immutable });
}
`;

if (!fs.existsSync(path.dirname(OUT_PATH))) {
  console.warn("patch-images-pass-through: .open-next/cloudflare not found (run build:cloudflare first).");
  process.exit(0);
}

fs.writeFileSync(OUT_PATH, PASS_THROUGH_IMAGES_JS, "utf8");
console.log("patch-images-pass-through: wrote pass-through images.js (no IMAGES WASM).");
