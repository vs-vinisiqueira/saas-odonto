import { ChevronLeft, ChevronRight, Plus, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";

import { Spinner } from "@/components/ui/spinner";
import {
  addDaysStr,
  formatDateLabel,
  todayStr,
} from "@/lib/datetime";
import { cn } from "@/lib/utils";
import {
  useAppointments,
  useAppointmentsRange,
  useAvailability,
  useCancelAppointment,
  useDeleteAppointment,
  type Appointment,
  type Slot,
} from "./api";
import { AppointmentDetailsPanel } from "./appointment-details-panel";
import { BookingDialog } from "./booking-dialog";
import { TIPO_INFO } from "./tipo";

const PT_DAYS_SHORT = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18];

const STATUS_INFO: Record<string, { label: string; bg: string; color: string; border: string }> = {
  scheduled:  { label: "Agendada",  bg: "#F4F4F5", color: "#52525B",  border: "#A1A1AA" },
  confirmed:  { label: "Confirmada",bg: "#EFF6FF", color: "#1D4ED8",  border: "#3B82F6" },
  completed:  { label: "Concluída", bg: "#F0FDF4", color: "#15803D",  border: "#22C55E" },
  cancelled:  { label: "Cancelada", bg: "#FEF2F2", color: "#B91C1C",  border: "#EF4444" },
  no_show:    { label: "Faltou",    bg: "#FFF7ED", color: "#C2410C",  border: "#F97316" },
};

type AgendaView = "week" | "day";

export function AgendaPage() {
  const [date, setDate] = useState(todayStr());
  const [view, setView] = useState<AgendaView>("week");
  const [slot, setSlot] = useState<Slot | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailAppt, setDetailAppt] = useState<Appointment | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const availability = useAvailability(date);
  const appointments = useAppointments(date);
  const cancel = useCancelAppointment();
  const deleteAppt = useDeleteAppointment();

  const patientName = (appt: Appointment) => appt.patient_nome ?? "Paciente";

  const weekDays = useMemo(() => {
    const [y, mo, da] = date.split("-").map(Number);
    const dow = new Date(Date.UTC(y, mo - 1, da)).getUTCDay();
    const weekStart = addDaysStr(date, -dow);
    return Array.from({ length: 7 }, (_, i) => addDaysStr(weekStart, i));
  }, [date]);

  const appointmentsWeek = useAppointmentsRange(weekDays[0], weekDays[6]);

  function openSlot(s: Slot) {
    setSlot(s);
    setDialogOpen(true);
  }

  function openDetails(appt: Appointment) {
    setDetailAppt(appt);
    setDetailOpen(true);
  }

  const today = todayStr();

  return (
    <div className="flex h-full min-h-[560px] flex-col gap-0 pb-0">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 pb-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">Agenda</h2>
          <p className="text-[12.5px] text-muted-foreground tabular-nums">
            {formatDateLabel(date)} · horários em UTC
          </p>
        </div>

        {/* Toggle semana/dia */}
        <div className="flex items-center gap-0.5 rounded-[11px] border bg-secondary p-0.5">
          {(["week", "day"] as AgendaView[]).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={cn(
                "rounded-lg px-3.5 py-1.5 text-[13px] font-bold transition-all",
                view === v
                  ? "bg-primary text-white"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {v === "week" ? "Semana" : "Dia"}
            </button>
          ))}
        </div>

        <div className="flex-1" />

        {/* Navegação semana */}
        <div className="flex items-center gap-0.5 rounded-[11px] border bg-card p-0.5">
          <button
            onClick={() => setDate(addDaysStr(date, -7))}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary"
          >
            <ChevronLeft className="h-[17px] w-[17px]" />
          </button>
          <button
            onClick={() => setDate(todayStr())}
            className="h-8 rounded-lg px-3.5 text-[13px] font-bold text-foreground transition-colors hover:bg-secondary"
          >
            Hoje
          </button>
          <button
            onClick={() => setDate(addDaysStr(date, 7))}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary"
          >
            <ChevronRight className="h-[17px] w-[17px]" />
          </button>
        </div>

        <button
          onClick={() => { setSlot(null); setDialogOpen(true); }}
          className="inline-flex items-center gap-1.5 rounded-[11px] bg-primary px-[15px] py-[10px] text-[13.5px] font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,.28)] transition-all hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(124,58,237,.36)]"
        >
          <Plus className="h-4 w-4" />
          Agendar
        </button>
      </div>

      {/* Faixa de dias da semana */}
      <div className="mb-3 grid grid-cols-7 gap-1.5">
        {weekDays.map((d) => {
          const active = d === date;
          const isToday = d === today;
          const [, , dd] = d.split("-");
          const dow = new Date(`${d}T00:00:00Z`).getUTCDay();
          return (
            <button
              key={d}
              onClick={() => setDate(d)}
              className={cn(
                "flex flex-col items-center rounded-[11px] border py-2 text-xs transition-all",
                active
                  ? "border-primary bg-primary text-white font-bold"
                  : isToday
                  ? "border-primary/40 text-primary font-semibold"
                  : "border-border hover:bg-secondary",
              )}
            >
              <span className="text-[10px] uppercase tracking-wide font-bold opacity-70">
                {PT_DAYS_SHORT[dow]}
              </span>
              <span className="mt-0.5 text-base font-extrabold">{Number(dd)}</span>
            </button>
          );
        })}
      </div>

      {/* Grade principal */}
      {view === "week" ? (
        <WeekGrid
          weekDays={weekDays}
          today={today}
          appointments={appointmentsWeek.data ?? []}
          patientName={patientName}
          onSlotClick={(d) => { setDate(d); setView("day"); }}
          onApptOpen={openDetails}
        />
      ) : (
        <DayGrid
          appointments={appointments.data ?? []}
          availability={availability.data ?? []}
          patientName={patientName}
          loading={appointments.isLoading}
          onSlotClick={openSlot}
          onApptOpen={openDetails}
          onCancel={(id) => cancel.mutate(id)}
          onDelete={(id, name) => {
            if (window.confirm(`Excluir definitivamente o agendamento de "${name}"? Esta ação não pode ser desfeita.`))
              deleteAppt.mutate(id);
          }}
        />
      )}

      <BookingDialog open={dialogOpen} onOpenChange={setDialogOpen} slot={slot} defaultDate={date} />
      <AppointmentDetailsPanel
        open={detailOpen}
        onOpenChange={setDetailOpen}
        appointment={detailAppt}
      />
    </div>
  );
}

// ─── Week Grid ──────────────────────────────────────────────────────────────
function WeekGrid({
  weekDays, today, appointments, patientName, onSlotClick, onApptOpen,
}: {
  weekDays: string[]; today: string;
  appointments: ReturnType<typeof useAppointments>["data"] extends (infer T)[] | undefined ? T[] : never[];
  patientName: (appt: Appointment) => string;
  onSlotClick: (d: string) => void;
  onApptOpen: (a: Appointment) => void;
}) {
  // map: day_index + hour -> appointment
  const grid = useMemo(() => {
    const m: Record<string, typeof appointments[0]> = {};
    for (const a of appointments) {
      if (a.status === "cancelled") continue;
      const dt = new Date(a.starts_at);
      const dStr = dt.toISOString().slice(0, 10);
      const h = dt.getUTCHours();
      m[`${dStr}:${h}`] = a;
    }
    return m;
  }, [appointments]);

  return (
    <div className="min-h-0 flex-1 overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
      {/* Rola horizontalmente no mobile para os 7 dias não ficarem ilegíveis */}
      <div className="h-full overflow-x-auto">
        {/* Header dias */}
        <div className="flex h-full min-h-0 min-w-[620px] flex-col">
        <div className="grid shrink-0 border-b" style={{ gridTemplateColumns: "62px repeat(7, 1fr)" }}>
          <div className="border-r border-border-soft" />
          {weekDays.map((d) => {
            const isToday = d === today;
            const dow = new Date(`${d}T00:00:00Z`).getUTCDay();
            const dd = Number(d.split("-")[2]);
            return (
              <div key={d} className="border-r border-border-soft py-3 text-center last:border-0">
                <div className={cn("text-[11px] font-bold uppercase tracking-[.04em]", isToday ? "text-primary" : "text-muted-foreground")}>
                  {PT_DAYS_SHORT[dow]}
                </div>
                <div
                  className={cn(
                    "mx-auto mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-[17px] font-extrabold leading-none",
                    isToday ? "bg-primary text-white" : "text-foreground",
                  )}
                >
                  {dd}
                </div>
              </div>
            );
          })}
        </div>

        {/* Body */}
        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="grid" style={{ gridTemplateColumns: "62px repeat(7, 1fr)" }}>
            {/* Coluna de horários */}
            <div className="border-r border-border-soft">
              {HOURS.map((h) => (
                <div key={h} className="flex h-14 items-start justify-end border-b border-border-soft px-2 pt-1 text-[11px] font-semibold tabular-nums text-muted-foreground">
                  {String(h).padStart(2, "0")}:00
                </div>
              ))}
            </div>

            {/* Colunas dos dias */}
            {weekDays.map((d) => {
              const isToday = d === today;
              return (
                <div key={d} className="border-r border-border-soft last:border-0" style={{ background: isToday ? "rgba(124,58,237,.04)" : undefined }}>
                  {HOURS.map((h) => {
                    const appt = grid[`${d}:${h}`];
                    const st = appt ? (STATUS_INFO[appt.status] ?? STATUS_INFO.scheduled) : null;
                    return (
                      <div
                        key={h}
                        onClick={() => !appt && onSlotClick(d)}
                        className={cn("h-14 border-b border-border-soft p-0.5", !appt && "cursor-pointer hover:bg-secondary/50")}
                      >
                        {appt && st && (
                          <div
                            onDoubleClick={() => onApptOpen(appt)}
                            title="Duplo clique para ver detalhes"
                            className="group h-full cursor-pointer overflow-hidden rounded-lg p-1.5 transition-all hover:scale-[1.04] hover:shadow-[0_6px_16px_rgba(16,24,40,.16)]"
                            style={{ background: st.bg, borderLeft: `3px solid ${st.border}` }}
                          >
                            <div className="flex items-center gap-1">
                              <span
                                className="h-1.5 w-1.5 shrink-0 rounded-full"
                                style={{ background: (TIPO_INFO[appt.tipo] ?? TIPO_INFO.avaliacao).color }}
                                title={(TIPO_INFO[appt.tipo] ?? TIPO_INFO.avaliacao).label}
                              />
                              <div className="truncate text-[9.5px] font-extrabold uppercase leading-none tracking-[.03em]" style={{ color: st.color }}>
                                {st.label}
                              </div>
                            </div>
                            <div className="mt-0.5 truncate text-xs font-semibold text-foreground">
                              {patientName(appt)}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

// ─── Day Grid ───────────────────────────────────────────────────────────────
function DayGrid({
  appointments, availability, patientName, loading, onSlotClick, onApptOpen, onCancel, onDelete,
}: {
  appointments: ReturnType<typeof useAppointments>["data"] extends (infer T)[] | undefined ? T[] : never[];
  availability: Slot[];
  patientName: (appt: Appointment) => string;
  loading: boolean;
  onSlotClick: (s: Slot) => void;
  onApptOpen: (a: Appointment) => void;
  onCancel: (id: string) => void;
  onDelete: (id: string, name: string) => void;
}) {
  const apptByHour = useMemo(() => {
    const m: Record<number, typeof appointments[0]> = {};
    for (const a of appointments) {
      if (a.status === "cancelled") continue;
      m[new Date(a.starts_at).getUTCHours()] = a;
    }
    return m;
  }, [appointments]);

  const freeSlotsByHour = useMemo(() => {
    const m: Record<number, Slot> = {};
    for (const s of availability) {
      m[new Date(s.starts_at).getUTCHours()] = s;
    }
    return m;
  }, [availability]);

  return (
    <div className="min-h-0 flex-1 overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
      <div className="h-full overflow-y-auto">
        {loading ? (
          <div className="flex justify-center p-10"><Spinner className="text-primary" /></div>
        ) : (
          HOURS.map((h) => {
            const appt = apptByHour[h];
            const freeSlot = freeSlotsByHour[h];
            const st = appt ? (STATUS_INFO[appt.status] ?? STATUS_INFO.scheduled) : null;
            const canCancel = appt && (appt.status === "scheduled" || appt.status === "confirmed");
            return (
              <div key={h} className="grid min-h-16 border-b border-border-soft" style={{ gridTemplateColumns: "76px 1fr" }}>
                <div className="border-r border-border-soft p-2.5 text-right text-xs font-semibold tabular-nums text-muted-foreground">
                  {String(h).padStart(2, "0")}:00
                </div>
                <div className="p-2">
                  {appt && st ? (
                    <div
                      onDoubleClick={() => onApptOpen(appt)}
                      title="Duplo clique para ver detalhes"
                      className="flex cursor-pointer items-center gap-3.5 rounded-xl p-3 transition-all hover:translate-x-0.5 hover:shadow-[0_6px_18px_rgba(16,24,40,.12)]"
                      style={{ background: st.bg, borderLeft: `3px solid ${st.border}` }}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span
                            className="h-2 w-2 shrink-0 rounded-full"
                            style={{ background: (TIPO_INFO[appt.tipo] ?? TIPO_INFO.avaliacao).color }}
                          />
                          <div className="text-[10px] font-extrabold uppercase tracking-[.04em]" style={{ color: st.color }}>{st.label}</div>
                          <span className="text-[10px] font-semibold text-muted-foreground">
                            · {(TIPO_INFO[appt.tipo] ?? TIPO_INFO.avaliacao).label}
                          </span>
                        </div>
                        <div className="mt-0.5 text-[15px] font-bold text-foreground">{patientName(appt)}</div>
                      </div>
                      <div
                        className="flex shrink-0 items-center gap-1"
                        onDoubleClick={(e) => e.stopPropagation()}
                      >
                        {canCancel && (
                          <button
                            onClick={() => onCancel(appt.id)}
                            title="Cancelar"
                            className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-orange-50 hover:text-orange-600"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => onDelete(appt.id, patientName(appt))}
                          title="Excluir definitivamente"
                          className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-red-50 hover:text-red-600"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ) : freeSlot ? (
                    <button
                      onClick={() => onSlotClick(freeSlot)}
                      className="w-full rounded-xl border border-dashed border-primary/30 py-2 text-xs font-semibold text-primary/60 transition-colors hover:border-primary hover:bg-accent hover:text-primary"
                    >
                      + Agendar
                    </button>
                  ) : null}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
