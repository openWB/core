export interface SvgSize {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  circleRadius: number;
  strokeWidth: number;
  textSize: number;
  numRows: number;
  numColumns: number;
}

export interface ComponentClass {
  base: string;
  valueLabel: string;
  animated?: boolean;
  animatedReverse?: boolean;
}

export interface ComponentPosition {
  row: number;
  column: number;
}

export interface FlowComponent {
  id: string;
  class: ComponentClass;
  position: ComponentPosition;
  label: string[];
  soc?: number;
  icon: string;
}
