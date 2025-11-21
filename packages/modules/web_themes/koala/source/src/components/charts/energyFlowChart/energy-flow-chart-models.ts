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
  animationId?: string;
  valueLabel: string;
  animated?: boolean;
  animatedReverse?: boolean;
  powerCategory?: string;
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
  powerValue?: number;
  soc?: number;
  icon: string;
}

