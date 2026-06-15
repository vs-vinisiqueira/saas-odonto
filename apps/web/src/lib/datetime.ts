/** Formatação de data/hora em UTC.
 *
 * O backend opera a agenda em UTC (janela 09–18h UTC, slots de 30min). Para
 * casar com o que a API devolve, exibimos os horários em UTC — sem converter
 * para o fuso local do navegador (que deslocaria as horas). Refinamento futuro:
 * fuso da clínica. */

const WEEKDAYS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
const MONTHS = [
  "jan", "fev", "mar", "abr", "mai", "jun",
  "jul", "ago", "set", "out", "nov", "dez",
];

export function formatTimeUTC(iso: string): string {
  const d = new Date(iso);
  const h = String(d.getUTCHours()).padStart(2, "0");
  const m = String(d.getUTCMinutes()).padStart(2, "0");
  return `${h}:${m}`;
}

/** "qua, 5 jan" a partir de um date string YYYY-MM-DD. */
export function formatDateLabel(dateStr: string): string {
  const [y, mo, da] = dateStr.split("-").map(Number);
  const d = new Date(Date.UTC(y, mo - 1, da));
  return `${WEEKDAYS[d.getUTCDay()]}, ${da} ${MONTHS[mo - 1]}`;
}

/** Date string YYYY-MM-DD a partir de um Date (em UTC). */
export function toDateStr(d: Date): string {
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, "0"),
    String(d.getUTCDate()).padStart(2, "0"),
  ].join("-");
}

/** Hoje (UTC) como YYYY-MM-DD. */
export function todayStr(): string {
  return toDateStr(new Date());
}

/** Soma `days` a um date string e devolve outro date string. */
export function addDaysStr(dateStr: string, days: number): string {
  const [y, mo, da] = dateStr.split("-").map(Number);
  const d = new Date(Date.UTC(y, mo - 1, da));
  d.setUTCDate(d.getUTCDate() + days);
  return toDateStr(d);
}
