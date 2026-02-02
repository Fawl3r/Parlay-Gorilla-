/* Web Push service worker for Parlay Gorilla.
 *
 * This file must live in /public so it can be registered at /push-sw.js.
 * PWA installability: install/activate only; no fetch handler.
 */

self.addEventListener("install", () => {
  self.skipWaiting()
})

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("push", (event) => {
  let payload = {}
  try {
    payload = event?.data ? event.data.json() : {}
  } catch {
    try {
      payload = { body: event?.data ? event.data.text() : "" }
    } catch {
      payload = {}
    }
  }

  const title = payload.title || "Parlay Gorilla"
  const url = payload.url || "/analysis"
  const body = payload.body || ""
  const tag = payload.tag
  const icon = payload.icon || "/favicon.ico"

  const options = {
    body,
    icon,
    tag,
    data: {
      url,
      ...(payload.data || {}),
    },
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener("notificationclick", (event) => {
  event.notification?.close()

  const url = event?.notification?.data?.url || "/analysis"

  event.waitUntil(
    (async () => {
      const targetUrl = new URL(url, self.location.origin).toString()
      const windowClients = await clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      })

      for (const client of windowClients) {
        try {
          const clientUrl = new URL(client.url)
          if (clientUrl.origin === self.location.origin) {
            await client.focus()
            client.navigate(targetUrl)
            return
          }
        } catch {
          // Ignore invalid client URLs
        }
      }

      await clients.openWindow(targetUrl)
    })()
  )
})


