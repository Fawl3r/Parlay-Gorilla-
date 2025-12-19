/* eslint-disable no-console */
const fs = require("fs");
const path = require("path");

class NextServerBundleVerifier {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
  }

  verify() {
    const entrypointPath = this.#getServerEntrypointPath();
    this.#assertFileExists(entrypointPath);

    // If this require fails, Next will also fail at runtime with a similar error.
    // eslint-disable-next-line global-require
    require(entrypointPath);

    console.log(`[OK] Next server bundle loads: ${path.relative(this.projectRoot, entrypointPath)}`);
  }

  #getServerEntrypointPath() {
    // Support both legacy Pages Router builds (Next 12/13) and App Router builds (Next 13+).
    // Turbopack builds (Next 16+) may not emit `server/pages/_document.js` at all.
    const candidates = [
      // Pages Router
      path.join(this.projectRoot, ".next", "server", "pages", "_document.js"),
      // App Router
      path.join(this.projectRoot, ".next", "server", "app", "page.js"),
      path.join(this.projectRoot, ".next", "server", "app", "layout.js"),
    ];

    for (const p of candidates) {
      if (fs.existsSync(p)) {
        return p;
      }
    }

    // Return the first candidate for a helpful error message downstream.
    return candidates[0];
  }

  #assertFileExists(filePath) {
    if (!fs.existsSync(filePath)) {
      throw new Error(
        [
          `Expected file does not exist: ${filePath}`,
          "Run `npm run build` first to generate the Next.js server bundle.",
        ].join("\n"),
      );
    }
  }
}

function main() {
  const projectRoot = path.join(__dirname, "..");
  new NextServerBundleVerifier(projectRoot).verify();
}

main();


