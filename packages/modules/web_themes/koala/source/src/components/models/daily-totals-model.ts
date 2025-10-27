export interface DailyTotalsItem {
  id: string;
  title: string;
  icon: string;
  soc?: number;
  power: string;
  powerValue: number;
  today: {
    charged?: string;
    discharged?: string;
    yield?: string;
    imported?: string;
    exported?: string;
    energy?: string;
  };
  backgroundColor: string;
  // optional placeholders for table layout columns
  gap?: string;
  rightLabel?: string;
  rightValue?: string;
  arrow?: string;
}

