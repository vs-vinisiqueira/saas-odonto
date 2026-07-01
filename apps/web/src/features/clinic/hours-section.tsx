import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useMyClinic, useUpdateClinic, type DayHours, type WeekdayKey, type WorkingHoursConfig } from "./api";

const DAYS: { key: WeekdayKey; label: string }[] = [
  { key: "mon", label: "Segunda" },
  { key: "tue", label: "Terça" },
  { key: "wed", label: "Quarta" },
  { key: "thu", label: "Quinta" },
  { key: "fri", label: "Sexta" },
  { key: "sat", label: "Sábado" },
  { key: "sun", label: "Domingo" },
];

const DEFAULT_DAY: DayHours = {
  closed: false,
  start: "09:00",
  end: "18:00",
  lunch_start: "12:00",
  lunch_end: "13:00",
};

const DEFAULT_CLOSED: DayHours = { ...DEFAULT_DAY, closed: true, lunch_start: null, lunch_end: null };

function fillDefaults(config: WorkingHoursConfig | undefined): Record<WeekdayKey, DayHours> {
  const out = {} as Record<WeekdayKey, DayHours>;
  for (const { key } of DAYS) {
    const existing = config?.[key];
    out[key] = existing ?? (key === "sun" ? DEFAULT_CLOSED : DEFAULT_DAY);
  }
  return out;
}

const timeInputClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-sm disabled:opacity-40";

export function HoursSection() {
  const clinic = useMyClinic();
  const update = useUpdateClinic();
  const [days, setDays] = useState<Record<WeekdayKey, DayHours> | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (clinic.data) setDays(fillDefaults(clinic.data.config.working_hours));
  }, [clinic.data]);

  function updateDay(key: WeekdayKey, patch: Partial<DayHours>) {
    setDays((prev) => (prev ? { ...prev, [key]: { ...prev[key], ...patch } } : prev));
    setSaved(false);
  }

  async function handleSave() {
    if (!days) return;
    setFormError(null);
    try {
      await update.mutateAsync({ config: { working_hours: days } });
      setSaved(true);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível salvar os horários."));
    }
  }

  if (clinic.isLoading || !days) {
    return (
      <div className="flex justify-center rounded-[18px] border bg-card py-16">
        <Spinner className="text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h3 className="text-lg font-bold text-foreground">Horários de funcionamento</h3>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Define os horários disponíveis para agendamento na agenda (horários em UTC).
        </p>
      </div>

      <div className="flex flex-col gap-2 rounded-[18px] border bg-card p-4 shadow-[0_1px_2px_rgba(16,24,40,.04)] sm:p-6">
        {DAYS.map(({ key, label }) => {
          const d = days[key];
          return (
            <div
              key={key}
              className={cn(
                "grid grid-cols-1 items-center gap-2.5 border-b border-border-soft py-3 last:border-0 sm:grid-cols-[110px_auto_1fr_1fr]",
                d.closed && "opacity-60",
              )}
            >
              <span className="text-sm font-semibold text-foreground">{label}</span>

              <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <input
                  type="checkbox"
                  checked={!d.closed}
                  onChange={(e) => updateDay(key, { closed: !e.target.checked })}
                  className="h-4 w-4 rounded border-input accent-primary"
                />
                Aberto
              </label>

              <div className="flex items-center gap-1.5">
                <input
                  type="time"
                  value={d.start}
                  disabled={d.closed}
                  onChange={(e) => updateDay(key, { start: e.target.value })}
                  className={timeInputClass}
                />
                <span className="text-xs text-muted-foreground">até</span>
                <input
                  type="time"
                  value={d.end}
                  disabled={d.closed}
                  onChange={(e) => updateDay(key, { end: e.target.value })}
                  className={timeInputClass}
                />
              </div>

              <div className="flex items-center gap-1.5">
                <span className="shrink-0 text-xs text-muted-foreground">Almoço</span>
                <input
                  type="time"
                  value={d.lunch_start ?? ""}
                  disabled={d.closed}
                  onChange={(e) => updateDay(key, { lunch_start: e.target.value || null })}
                  className={timeInputClass}
                />
                <span className="text-xs text-muted-foreground">–</span>
                <input
                  type="time"
                  value={d.lunch_end ?? ""}
                  disabled={d.closed}
                  onChange={(e) => updateDay(key, { lunch_end: e.target.value || null })}
                  className={timeInputClass}
                />
              </div>
            </div>
          );
        })}

        {formError && (
          <p className="mt-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </p>
        )}
        {saved && !formError && (
          <p className="mt-2 rounded-md bg-success/10 px-3 py-2 text-sm text-success">
            Horários salvos.
          </p>
        )}

        <div className="mt-2 flex justify-end">
          <Button onClick={handleSave} disabled={update.isPending}>
            {update.isPending && <Spinner />}
            Salvar
          </Button>
        </div>
      </div>
    </div>
  );
}
