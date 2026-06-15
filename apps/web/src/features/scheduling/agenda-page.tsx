import { ChevronLeft, ChevronRight, Clock, X } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { usePatients } from "@/features/patients/api";
import {
  addDaysStr,
  formatDateLabel,
  formatTimeUTC,
  todayStr,
} from "@/lib/datetime";
import { cn } from "@/lib/utils";
import {
  useAppointments,
  useAvailability,
  useCancelAppointment,
  type Slot,
} from "./api";
import { BookingDialog } from "./booking-dialog";

const STATUS: Record<string, { label: string; variant: BadgeProps["variant"] }> = {
  scheduled: { label: "Agendado", variant: "default" },
  confirmed: { label: "Confirmado", variant: "success" },
  cancelled: { label: "Cancelado", variant: "muted" },
  completed: { label: "Concluído", variant: "success" },
  no_show: { label: "Faltou", variant: "warning" },
};

export function AgendaPage() {
  const [date, setDate] = useState(todayStr());
  const [slot, setSlot] = useState<Slot | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const availability = useAvailability(date);
  const appointments = useAppointments(date);
  const patients = usePatients();
  const cancel = useCancelAppointment();

  const patientName = useMemo(() => {
    const map = new Map((patients.data ?? []).map((p) => [p.id, p.nome]));
    return (id: string) => map.get(id) ?? "Paciente";
  }, [patients.data]);

  const weekDays = useMemo(() => {
    const [y, mo, da] = date.split("-").map(Number);
    const dow = new Date(Date.UTC(y, mo - 1, da)).getUTCDay();
    const weekStart = addDaysStr(date, -dow);
    return Array.from({ length: 7 }, (_, i) => addDaysStr(weekStart, i));
  }, [date]);

  function openSlot(s: Slot) {
    setSlot(s);
    setDialogOpen(true);
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Agenda</h1>
        <div className="flex items-center gap-1">
          <Button variant="outline" size="icon" onClick={() => setDate(addDaysStr(date, -1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setDate(todayStr())}>
            Hoje
          </Button>
          <Button variant="outline" size="icon" onClick={() => setDate(addDaysStr(date, 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Faixa da semana */}
      <div className="grid grid-cols-7 gap-1">
        {weekDays.map((d) => {
          const active = d === date;
          const [, , dd] = d.split("-");
          return (
            <button
              key={d}
              onClick={() => setDate(d)}
              className={cn(
                "flex flex-col items-center rounded-md border py-2 text-xs transition-colors",
                active
                  ? "border-primary bg-primary text-primary-foreground"
                  : "hover:bg-secondary",
              )}
            >
              <span className="uppercase">{formatDateLabel(d).split(",")[0]}</span>
              <span className="text-base font-semibold">{Number(dd)}</span>
            </button>
          );
        })}
      </div>

      <p className="text-sm text-muted-foreground">
        {formatDateLabel(date)} · horários em UTC
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Disponibilidade */}
        <Card>
          <CardHeader>
            <CardTitle>Horários livres</CardTitle>
          </CardHeader>
          <CardContent>
            {availability.isLoading ? (
              <div className="flex justify-center p-4">
                <Spinner className="text-primary" />
              </div>
            ) : availability.data && availability.data.length > 0 ? (
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                {availability.data.map((s) => (
                  <Button
                    key={s.starts_at}
                    variant="outline"
                    size="sm"
                    onClick={() => openSlot(s)}
                  >
                    {formatTimeUTC(s.starts_at)}
                  </Button>
                ))}
              </div>
            ) : (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Sem horários livres neste dia.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Consultas do dia */}
        <Card>
          <CardHeader>
            <CardTitle>Consultas do dia</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {appointments.isLoading ? (
              <div className="flex justify-center p-4">
                <Spinner className="text-primary" />
              </div>
            ) : appointments.data && appointments.data.length > 0 ? (
              appointments.data.map((a) => {
                const st = STATUS[a.status] ?? { label: a.status, variant: "muted" as const };
                const canCancel = a.status === "scheduled" || a.status === "confirmed";
                return (
                  <div
                    key={a.id}
                    className="flex items-center justify-between gap-2 rounded-md border p-3"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="flex items-center gap-1 text-sm font-medium">
                        <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                        {formatTimeUTC(a.starts_at)}
                      </span>
                      <span className="truncate text-sm">{patientName(a.patient_id)}</span>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Badge variant={st.variant}>{st.label}</Badge>
                      {canCancel && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => cancel.mutate(a.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Nenhuma consulta neste dia.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <BookingDialog open={dialogOpen} onOpenChange={setDialogOpen} slot={slot} />
    </div>
  );
}
