export class NextNavigationErrorGuard {
  private static readonly redirectSignature = "NEXT_REDIRECT"
  private static readonly notFoundSignature = "NEXT_NOT_FOUND"

  static shouldRethrow(error: unknown): boolean {
    return (
      NextNavigationErrorGuard.isRedirectError(error) ||
      NextNavigationErrorGuard.isNotFoundError(error)
    )
  }

  static isRedirectError(error: unknown): boolean {
    const signature = NextNavigationErrorGuard.extractSignature(error)
    return NextNavigationErrorGuard.matchesSignature(
      signature,
      NextNavigationErrorGuard.redirectSignature
    )
  }

  static isNotFoundError(error: unknown): boolean {
    const signature = NextNavigationErrorGuard.extractSignature(error)
    return NextNavigationErrorGuard.matchesSignature(
      signature,
      NextNavigationErrorGuard.notFoundSignature
    )
  }

  private static extractSignature(error: unknown): string {
    if (!error) return ""
    if (typeof error === "string") return error
    if (error instanceof Error && typeof error.message === "string") {
      return error.message
    }

    const digest = (error as { digest?: unknown }).digest
    if (typeof digest === "string") return digest

    const message = (error as { message?: unknown }).message
    if (typeof message === "string") return message

    return ""
  }

  private static matchesSignature(signature: string, token: string): boolean {
    if (!signature) return false
    return signature === token || signature.startsWith(`${token};`)
  }
}

