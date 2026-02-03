/**
 * Generate favicon and PWA icons from a source image.
 * Run from frontend: node scripts/generate-pwa-icons.js [source-image-path]
 * If no path is given, uses public/gorilla-logo-source.png.
 * Requires: sharp (devDependency).
 * Outputs: public/favicon.png (32x32), public/icons/icon-192.png, public/icons/icon-512.png.
 */
const path = require('path')
const fs = require('fs')

const publicDir = path.join(__dirname, '..', 'public')
const defaultSrc = path.join(publicDir, 'gorilla-logo-source.png')
const srcPath = process.argv[2] ? path.resolve(process.cwd(), process.argv[2]) : defaultSrc
const iconsDir = path.join(publicDir, 'icons')

const sizes = [
  { size: 32, name: 'favicon.png', dir: publicDir },
  { size: 192, name: 'icon-192.png', dir: iconsDir },
  { size: 512, name: 'icon-512.png', dir: iconsDir },
]

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
    console.error('Usage: node scripts/generate-pwa-icons.js [path-to-source.png]')
    console.error('Or place your logo at public/gorilla-logo-source.png and run without args.')
    process.exit(1)
  }

  for (const { dir, name, size } of sizes) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    const outPath = path.join(dir, name)
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
