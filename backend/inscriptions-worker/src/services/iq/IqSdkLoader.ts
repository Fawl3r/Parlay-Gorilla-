import { IqSdkEnv } from "./IqSdkEnv";

type IqSdkDefaultExport = {
  userInit: () => Promise<unknown>;
  codeIn: (dataString: string, datatype: string, handle: string) => Promise<unknown>;
  codeInAfterErr: (
    brokeNum: number,
    beforeHash: string,
    dataString: string,
    datatype: string,
    handle: string
  ) => Promise<unknown>;
};

export class IqSdkLoader {
  private static cached: IqSdkDefaultExport | null = null;

  public static async load(): Promise<IqSdkDefaultExport> {
    IqSdkEnv.assertRequired();

    if (IqSdkLoader.cached) return IqSdkLoader.cached;

    // Lazy-load to avoid crashing the process at module import time when env vars
    // are missing (the upstream SDK decodes SIGNER_PRIVATE_KEY on import).
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const mod = await import("iq-sdk");
    const sdk = (mod as any)?.default ?? mod;

    IqSdkLoader.cached = sdk as IqSdkDefaultExport;
    return IqSdkLoader.cached;
  }
}


