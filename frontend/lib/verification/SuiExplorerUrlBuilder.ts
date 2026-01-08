/**
 * Utility for building Sui blockchain explorer URLs.
 * 
 * Main explorers:
 * - Sui Explorer: https://suiexplorer.com/
 * - SuiScan: https://suiscan.com/ and https://suiscan.xyz/
 * - SuiVision: https://suivision.xyz/
 */

export type SuiNetwork = "mainnet" | "testnet" | "devnet";

export type ExplorerType = "suiexplorer" | "suiscan" | "suivision";

export interface SuiExplorerConfig {
  network: SuiNetwork;
  explorer?: ExplorerType;
}

const EXPLORER_BASES = {
  suiexplorer: {
    mainnet: "https://suiexplorer.com",
    testnet: "https://suiexplorer.com",
    devnet: "https://suiexplorer.com",
  },
  suiscan: {
    mainnet: "https://suiscan.xyz",
    testnet: "https://testnet.suiscan.xyz",
    devnet: "https://devnet.suiscan.xyz",
  },
  suivision: {
    mainnet: "https://suivision.xyz",
    testnet: "https://testnet.suivision.xyz",
    devnet: "https://devnet.suivision.xyz",
  },
};

export class SuiExplorerUrlBuilder {
  private readonly network: SuiNetwork;
  private readonly explorer: ExplorerType;

  constructor(config: SuiExplorerConfig) {
    this.network = config.network || "mainnet";
    this.explorer = config.explorer || "suiexplorer";
  }

  /**
   * Build URL for a transaction digest.
   * 
   * @param txDigest Transaction digest (base58 or hex)
   * @returns Explorer URL for the transaction
   */
  txUrl(txDigest: string): string {
    const base = EXPLORER_BASES[this.explorer][this.network];
    const digest = String(txDigest || "").trim();
    if (!digest) return base;

    if (this.explorer === "suiexplorer") {
      return `${base}/txblock/${digest}`;
    } else if (this.explorer === "suiscan") {
      return `${base}/tx/${digest}`;
    } else {
      // SuiVision
      return `${base}/tx/${digest}`;
    }
  }

  /**
   * Build URL for an object ID.
   * 
   * @param objectId Object ID (hex string starting with 0x)
   * @returns Explorer URL for the object
   */
  objectUrl(objectId: string): string {
    const base = EXPLORER_BASES[this.explorer][this.network];
    const id = String(objectId || "").trim();
    if (!id) return base;

    if (this.explorer === "suiexplorer") {
      return `${base}/object/${id}`;
    } else {
      // SuiScan
      return `${base}/object/${id}`;
    }
  }

  /**
   * Build URL for a package ID.
   * 
   * @param packageId Package ID (hex string starting with 0x)
   * @returns Explorer URL for the package
   */
  packageUrl(packageId: string): string {
    const base = EXPLORER_BASES[this.explorer][this.network];
    const id = String(packageId || "").trim();
    if (!id) return base;

    return `${base}/package/${id}`;
  }
}

/**
 * Default builder for mainnet using Sui Explorer.
 */
export const defaultSuiExplorer = new SuiExplorerUrlBuilder({
  network: "mainnet",
  explorer: "suiexplorer",
});

/**
 * Get all available explorer URLs for a transaction, object, or package.
 * Useful for providing multiple explorer options to users.
 */
export function getAllExplorerUrls(
  type: "tx" | "object" | "package",
  id: string,
  network: SuiNetwork = "mainnet"
): Array<{ name: string; url: string }> {
  const explorers: ExplorerType[] = ["suiexplorer", "suiscan", "suivision"];
  return explorers.map((explorerType) => {
    const builder = new SuiExplorerUrlBuilder({ network, explorer: explorerType });
    let url: string;
    switch (type) {
      case "tx":
        url = builder.txUrl(id);
        break;
      case "object":
        url = builder.objectUrl(id);
        break;
      case "package":
        url = builder.packageUrl(id);
        break;
    }
    return {
      name: explorerType === "suiexplorer" ? "Sui Explorer" : explorerType === "suiscan" ? "SuiScan" : "SuiVision",
      url,
    };
  });
}

