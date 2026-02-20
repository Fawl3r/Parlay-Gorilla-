export const GORILLA_BOT_OPEN_EVENT = "gorilla-bot:open"

export type GorillaBotOpenEventDetail = {
  prefill?: string
}

export function dispatchGorillaBotOpen(detail: GorillaBotOpenEventDetail = {}) {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent<GorillaBotOpenEventDetail>(GORILLA_BOT_OPEN_EVENT, { detail }))
}
