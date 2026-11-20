/** One colored segment of a FlowBar - a share of a Fluss-Leiste's source or sink total. */
export interface FlowSegment {
  label: string
  value: number
  colorVar: string
  /** Diagonal stripe overlay - distinguishes a segment that shares its color with another one
   *  (Zähler reuses --grid, same as Netz) without introducing a whole new color. */
  hatched?: boolean
}
