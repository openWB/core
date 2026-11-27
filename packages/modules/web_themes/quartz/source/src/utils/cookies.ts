/** Minimal cookie helpers - Quartz has no UI-framework dependency (no Quasar $q.cookies), so a
 *  vanilla document.cookie wrapper is needed for the login widget's "store creds in a cookie,
 *  mqtt.js reads them at CONNECT time" mechanism. */
export function getCookie(name: string): string | undefined {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : undefined
}

/** expiresDays defaults to 30 - the login widget's own cookie lifetime. */
export function setCookie(name: string, value: string, expiresDays = 30): void {
  const expires = new Date(Date.now() + expiresDays * 24 * 60 * 60 * 1000).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; secure; samesite=lax`
}

export function removeCookie(name: string): void {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}
