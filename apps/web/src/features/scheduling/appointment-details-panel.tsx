import { Check, FileText, Trash2, X, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { usePatients } from "@/features/patients/api";
import { useDentists } from "@/features/users/api";
import { errorMessage } from "@/lib/api";
import { formatDateLabel, formatTimeUTC } from "@/lib/datetime";
import { cn } from "@/lib/utils";
import {
  useDeleteAppointment,
  useUpdateAppointment,
  type Appointment,
} from "./api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointment: Appointment | null;
}

const STATUS_INFO: Record<string, { label: string; bg: string; color: string }> = {
  scheduled: { label: "Agendada", bg: "#F4F4F5", color: "#52525B" },
  confirmed: { label: "Confirmada", bg: "#EFF6FF", color: "#1D4ED8" },
  completed: { label: "Concluída", bg: "#F0FDF4", color: "#15803D" },
  cancelled: { label: "Cancelada", bg: "#FEF2F2", color: "#B91C1C" },
  no_show: { label: "Faltou", bg: "#FFF7ED", color: "#C2410C" },
};

// Ações rápidas de status (Cancelar fica no rodapé, com confirmação).
const QUICK_STATUS = [
  { key: "confirmed", label: "Confirmar" },
  { key: "completed", label: "Concluir" },
  { key: "no_show", label: "Faltou" },
];

function durationMin(a: Appointment): number {
  return Math.round(
    (new Date(a.ends_at).getTime() - new Date(a.starts_at).getTime()) / 60000,
  );
}

export function AppointmentDetailsPanel({ open, onOpenChange, appointment }: Props) {
  const navigate = useNavigate();
  const patients = usePatients();
  const dentistsQuery = useDentists();
  const update = useUpdateAppointment();
  const del = useDeleteAppointment();

  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  // Estado de montagem para a animação de slide-in.
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (open) {
      setNotes(appointment?.notes ?? "");
      setError(null);
      const t = setTimeout(() => setShown(true), 10);
      return () => clearTimeout(t);
    }
    setShown(false);
  }, [open, appointment]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onOpenChange(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  if (!open || !appointment) return null;

  const appt = appointment;
  const dentists = dentistsQuery.data ?? [];
  const patient = patients.data?.find((p) => p.id === appt.patient_id);
  const patientName = patient?.nome ?? "Paciente";
  const st = STATUS_INFO[appt.status] ?? STATUS_INFO.scheduled;
  const dateStr = appt.starts_at.slice(0, 10);

  async function patch(data: { status?: string; dentist_id?: string; notes?: string }) {
    setError(null);
    try {
      await update.mutateAsync({ id: appt.id, data });
    } catch (err) {
      setError(errorMessage(err, "Não foi possível salvar a alteração."));
    }
  }

  function handleDentistChange(value: string) {
    if (!value) return; // backend não permite remover o dentista; só atribuir/trocar
    void patch({ dentist_id: value });
  }

  function handleNotesBlur() {
    if (notes.trim() === (appt.notes ?? "")) return;
    void patch({ notes: notes.trim() });
  }

  async function handleCancel() {
    if (!window.confirm(`Cancelar a consulta de "${patientName}"? O horário ficará livre.`))
      return;
    await patch({ status: "cancelled" });
  }

  async function handleDelete() {
    if (
      !window.confirm(
        `Excluir definitivamente a consulta de "${patientName}"? Esta ação não pode ser desfeita.`,
      )
    )
      return;
    setError(null);
    try {
      await del.mutateAsync(appt.id);
      onOpenChange(false);
    } catch (err) {
      setError(errorMessage(err, "Não foi possível excluir."));
    }
  }

  const busy = update.isPending || del.isPending;

  return (
    <div className="fixed inset-0 z-50" aria-modal="true" role="dialog">
      {/* Overlay */}
      <div
        className={cn(
          "absolute inset-0 bg-black/30 transition-opacity duration-200",
          shown ? "opacity-100" : "opacity-0",
        )}
        onMouseDown={() => onOpenChange(false)}
      />

      {/* Painel */}
      <div
        className={cn(
          "absolute right-0 top-0 flex h-full w-full max-w-[420px] flex-col bg-card shadow-2xl transition-transform duration-200 ease-out",
          shown ? "translate-x-0" : "translate-x-full",
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b px-6 py-5">
          <div className="flex flex-col gap-1.5">
            <span
              className="inline-flex w-fit items-center rounded-full px-2.5 py-1 text-[11px] font-extrabold uppercase tracking-[.04em]"
              style={{ background: st.bg, color: st.color }}
            >
              {st.label}
            </span>
            <h2 className="text-lg font-bold text-foreground">{patientName}</h2>
          </div>
          <button
            type="button"
            aria-label="Fechar"
            onClick={() => onOpenChange(false)}
            className="rounded-md p-1 text-muted-foreground hover:bg-secondary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Corpo */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <div className="flex flex-col gap-5">
            {/* Infos somente leitura */}
            <div className="grid grid-cols-2 gap-4">
              <Info label="Data" value={formatDateLabel(dateStr)} />
              <Info
                label="Horário (UTC)"
                value={`${formatTimeUTC(appt.starts_at)}–${formatTimeUTC(appt.ends_at)}`}
              />
              <Info label="Duração" value={`${durationMin(appt)} min`} />
              <Info label="Paciente" value={patient?.telefone ?? "—"} />
            </div>

            {/* Dentista */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="appt-dentist">Dentista responsável</Label>
              <select
                id="appt-dentist"
                value={appt.dentist_id ?? ""}
                disabled={busy}
                onChange={(e) => handleDentistChange(e.target.value)}
                className={cn(
                  "h-10 w-full rounded-md border border-input bg-background px-3 text-sm",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "disabled:opacity-50",
                )}
              >
                <option value="">Sem dentista</option>
                {dentists.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.nome ?? d.email}
                  </option>
                ))}
              </select>
            </div>

            {/* Status rápido */}
            <div className="flex flex-col gap-1.5">
              <Label>Status</Label>
              <div className="flex flex-wrap gap-2">
                {QUICK_STATUS.map((q) => {
                  const active = appt.status === q.key;
                  return (
                    <button
                      key={q.key}
                      disabled={busy || active}
                      onClick={() => patch({ status: q.key })}
                      className={cn(
                        "rounded-lg border px-3 py-1.5 text-[13px] font-semibold transition-colors disabled:opacity-60",
                        active
                          ? "border-primary bg-primary text-white"
                          : "border-border bg-background text-foreground hover:bg-secondary",
                      )}
                    >
                      {q.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Observações */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="appt-notes">Observações</Label>
              <Textarea
                id="appt-notes"
                rows={4}
                value={notes}
                disabled={busy}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={handleNotesBlur}
                placeholder="Sem observações. Clique para adicionar..."
              />
              <span className="text-[11px] text-muted-foreground">
                As observações são salvas ao sair do campo.
              </span>
            </div>

            {/* Prontuário */}
            <button
              onClick={() => navigate(`/pacientes/${appt.patient_id}`)}
              className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-primary hover:underline"
            >
              <FileText className="h-4 w-4" />
              Ver prontuário do paciente
            </button>

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Rodapé: ações destrutivas */}
        <div className="flex items-center justify-between gap-2 border-t px-6 py-4">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={busy || appt.status === "cancelled"}
          >
            <XCircle className="h-4 w-4" />
            Cancelar consulta
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={busy}>
            {del.isPending ? <Spinner /> : <Trash2 className="h-4 w-4" />}
            Excluir
          </Button>
        </div>

        {update.isPending && (
          <div className="pointer-events-none absolute right-6 top-5">
            <Check className="h-4 w-4 animate-pulse text-primary" />
          </div>
        )}
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[11px] font-bold uppercase tracking-[.04em] text-muted-foreground">
        {label}
      </span>
      <span className="text-sm font-semibold text-foreground">{value}</span>
    </div>
  );
}
