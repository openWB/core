/** Badge class for the charging, plugged or idle state; `locked` (chargepoints only) always wins. */
export function stateBadgeClass(charging: boolean, plugged: boolean, locked = false): string {
  if (locked) return 'badge-error'
  if (charging) return 'badge-ok'
  if (plugged) return 'badge-wait'
  return 'badge-muted'
}
