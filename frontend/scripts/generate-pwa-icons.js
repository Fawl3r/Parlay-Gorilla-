/**
 * One-off script to generate PWA icons (192x192, 512x512) from public/images/newlogohead.png.
 * Run from frontend: node scripts/generate-pwa-icons.js
 * Requires: npm install sharp --save-dev (or sharp already present via next).
 */
const path = require('path')
const fs = require('fs')

const publicDir = path.join(__dirname, '..', 'public')
const srcPath = path.join(publicDir, 'images', 'newlogohead.png')
const iconsDir = path.join(publicDir, 'icons')

const sizes = [192, 512]

async function main() {
  let sharp
  try {
    sharp = require('sharp')
  } catch (e) {
    console.error('sharp not found. Install with: npm install sharp --save-dev')
    process.exit(1)
  }

  if (!fs.existsSync(srcPath)) {
    console.error('Source image not found:', srcPath)
    process.exit(1)
  }

  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true })
  }

  for (const size of sizes) {
    const outPath = path.join(iconsDir, `icon-${size}.png`)
    await sharp(srcPath)
      .resize(size, size)
      .png()
      .toFile(outPath)
    console.log('Wrote', outPath)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
