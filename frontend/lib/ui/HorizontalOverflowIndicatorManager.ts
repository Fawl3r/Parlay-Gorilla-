export type HorizontalOverflowIndicators = Readonly<{
  canScrollLeft: boolean
  canScrollRight: boolean
}>

export class HorizontalOverflowIndicatorManager {
  static compute({
    scrollLeft,
    clientWidth,
    scrollWidth,
    thresholdPx = 8,
  }: {
    scrollLeft: number
    clientWidth: number
    scrollWidth: number
    thresholdPx?: number
  }): HorizontalOverflowIndicators {
    // If content doesn't overflow, no indicators should show.
    if (clientWidth <= 0 || scrollWidth <= clientWidth) {
      return { canScrollLeft: false, canScrollRight: false }
    }

    const canScrollLeft = scrollLeft > thresholdPx
    const canScrollRight = scrollLeft + clientWidth < scrollWidth - thresholdPx

    return { canScrollLeft, canScrollRight }
  }
}


