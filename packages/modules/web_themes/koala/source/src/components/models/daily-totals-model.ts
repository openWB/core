export interface DailyTotalsItem {
  id: string;
  title: string;
  icon: string;
  level: 'primary' | 'secondary';
  soc?: number;
  power?: string;
  powerValue?: number;
  today?: {
    imported?: string;
    exported?: string;
  };
  // optional placeholders for table layout columns
  gap?: string;
  rightLabel?: string;
  rightValue?: string;
  arrow?: string;
  color?: string;
}
