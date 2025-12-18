/* eslint-disable no-console */
const fs = require("fs");
const path = require("path");

class NextServerBundleVerifier {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
  }

  verify() {
    const documentBundlePath = this.#getDocumentBundlePath();
    this.#assertFileExists(documentBundlePath);

    // If this require fails, Next will also fail at runtime with a similar error.
    // eslint-disable-next-line global-require
    require(documentBundlePath);

    console.log(`[OK] Next server bundle loads: ${path.relative(this.projectRoot, documentBundlePath)}`);
  }

  #getDocumentBundlePath() {
    return path.join(this.projectRoot, ".next", "server", "pages", "_document.js");
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


