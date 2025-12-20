export class AnalysisSectionTabsStyles {
  static readonly container =
    "mb-6 flex flex-nowrap items-center gap-1 sm:gap-2 overflow-x-auto scrollbar-hide rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1"

  // Critical: `shrink-0` ensures tab labels never compress/overlap on mobile.
  static readonly tabButtonBase =
    "shrink-0 inline-flex items-center px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold whitespace-nowrap transition-colors"

  static readonly tabButtonActive = "bg-emerald-500 text-black"
  static readonly tabButtonInactive = "text-gray-200 hover:bg-white/10"
}


