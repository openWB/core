import { QTableColumn } from 'quasar';
'';

export type Align = Record<string, 'left' | 'right' | 'center'>;

export type columnConfig = {
  fields: string[];
  labels?: Record<string, string>;
  align?: Align;
};

export interface BodySlotProps {
  key: string | number;
  row: Record<string, unknown>;
  cols: QTableColumn[];
  expand: boolean;
}
