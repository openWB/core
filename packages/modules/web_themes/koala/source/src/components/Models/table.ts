export type Align = Record<string, 'left' | 'right' | 'center'>;

export type columnConfig = {
  fields: string[];
  labels?: Record<string, string>;
  align?: Align;
};
