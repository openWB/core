export interface DailyTotalsItem {
  id: string;
  title: string;
  icon: string;
  soc?: number;
  power: string;
  powerValue: number;
  today: {
    imported?: string;
    exported?: string;
  };
  // optional placeholders for table layout columns
  gap?: string;
  rightLabel?: string;
  rightValue?: string;
  arrow?: string;
}
