import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { useMyClinic, useUpdateClinic } from "./api";

export function PreferencesSection() {
  const clinic = useMyClinic();
  const update = useUpdateClinic();
  const [remindersEnabled, setRemindersEnabled] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clinic.data) {
      setRemindersEnabled(clinic.data.config.preferences?.reminders_enabled ?? false);
    }
  }, [clinic.data]);

  async function handleToggle() {
    const next = !remindersEnabled;
    setRemindersEnabled(next);
    setError(null);
    try {
      await update.mutateAsync({
        config: { preferences: { reminders_enabled: next } },
      });
    } catch (err) {
      setRemindersEnabled(!next);
      setError(errorMessage(err, "Não foi possível salvar a preferência."));
    }
  }

  if (clinic.isLoading) {
    return (
      <div className="flex justify-center rounded-[18px] border bg-card py-16">
        <Spinner className="text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h3 className="text-lg font-bold text-foreground">Preferências</h3>
        <p className="mt-0.5 text-sm text-muted-foreground">
          O tema (claro/escuro) fica no botão do topo. O idioma do painel é fixo em português.
        </p>
      </div>

      <div className="flex items-center justify-between gap-4 rounded-[18px] border bg-card p-5 shadow-[0_1px_2px_rgba(16,24,40,.04)]">
        <div>
          <div className="text-sm font-bold text-foreground">Lembretes de consulta</div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Envia um lembrete automático por WhatsApp perto do horário da consulta (em breve).
          </p>
        </div>
        <button
          onClick={handleToggle}
          disabled={update.isPending}
          className="relative h-6 w-10 shrink-0 rounded-full border-none outline-none transition-all disabled:opacity-50"
          style={{ background: remindersEnabled ? "#0D9488" : "#D4D4D8" }}
        >
          <span
            className="absolute top-[3px] h-[18px] w-[18px] rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,.2)] transition-all"
            style={{ left: remindersEnabled ? "21px" : "3px" }}
          />
        </button>
      </div>

      {error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}
