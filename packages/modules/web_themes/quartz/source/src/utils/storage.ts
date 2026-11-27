/** localStorage can throw on access (blocked site data, private mode, some kiosk browsers) - the page must not depend on it. */
export function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // nothing to do, the setting just is not remembered
  }
}
