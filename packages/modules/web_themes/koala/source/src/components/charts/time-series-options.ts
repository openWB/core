// Shared typography for the history, PV forecast and electricity price charts.
export const timeSeriesAxisFont = { size: 14 };

export const timeSeriesTooltip = {
  titleFont: { size: 16, weight: 'bold' as const, lineHeight: 1.4 },
  bodyFont: { size: 16, lineHeight: 1.4 },
  padding: 12,
  titleMarginBottom: 8,
  bodySpacing: 6,
  boxWidth: 14,
  boxHeight: 14,
  boxPadding: 6,
};

export function wrapTooltipLabel(
  text: string,
  context: CanvasRenderingContext2D,
  maxWidth: number,
): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of text.split(/\s+/)) {
    const candidate = line ? `${line} ${word}` : word;
    if (line && context.measureText(candidate).width > maxWidth) {
      lines.push(line);
      line = '';
    }
    // Device names may contain long, unbroken identifiers.
    for (const character of (line ? ' ' : '') + word) {
      if (line && context.measureText(line + character).width > maxWidth) {
        lines.push(line);
        line = '';
      }
      line += character;
    }
  }
  if (line) lines.push(line);
  return lines;
}
