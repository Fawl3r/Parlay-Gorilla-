export class BringIntoViewManager {
  static bringIntoView(
    element: HTMLElement | null | undefined,
    options: ScrollIntoViewOptions = { behavior: "smooth", block: "start", inline: "nearest" }
  ) {
    if (!element) return

    const run = () => {
      try {
        element.scrollIntoView(options)
      } catch {
        // ignore
      }

      try {
        element.focus({ preventScroll: true })
      } catch {
        // ignore
      }
    }

    if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(run)
      return
    }

    run()
  }
}


