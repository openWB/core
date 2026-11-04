/**
 * The charging/plugged/idle -> badge-ok/badge-wait/badge-muted vocabulary shared by every card
 * that shows a chargepoint-driven state (ChargePoint/Consumer/Vehicle). A locked chargepoint
 * always shows muted regardless of charge/plug state - optional since only ChargePointCard has
 * a lock concept.
 */
export function stateBadgeClass(charging: boolean, plugged: boolean, locked = false): string {
  if (locked) return 'badge-muted'
  if (charging) return 'badge-ok'
  if (plugged) return 'badge-wait'
  return 'badge-muted'
}
