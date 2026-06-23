import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { usePatients } from "@/features/patients/api";
import { useDentists } from "@/features/users/api";
import { errorMessage } from "@/lib/api";
import { formatTimeUTC, todayStr } from "@/lib/datetime";
import { cn } from "@/lib/utils";
import { useCreateAppointment, type Slot } from "./api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  slot: Slot | null;
  /** Data padrão (YYYY-MM-DD) quando o diálogo é aberto sem um slot pré-definido. */
  defaultDate?: string;
}

const selectClass = cn(
  "h-10 w-full rounded-md border border-input bg-background px-3 text-sm",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
);

export function BookingDialog({ open, onOpenChange, slot, defaultDate }: Props) {
  const patients = usePatients();
  const dentistsQuery = useDentists();
  const create = useCreateAppointment();
  const [patientId, setPatientId] = useState("");
  const [dentistId, setDentistId] = useState("");
  const [notes, setNotes] = useState("");
  // Data/hora manuais (em UTC), usadas quando não há slot pré-selecionado.
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [error, setError] = useState<string | null>(null);

  const dentists = dentistsQuery.data ?? [];

  useEffect(() => {
    if (open) {
      setPatientId("");
      setDentistId("");
      setNotes("");
      setDate(defaultDate ?? todayStr());
      setTime("09:00");
      setError(null);
    }
  }, [open, defaultDate]);

  /** ISO em UTC do horário escolhido: do slot, ou montado a partir de data+hora. */
  function resolveStartsAt(): string | null {
    if (slot) return slot.starts_at;
    if (!date || !time) return null;
    return `${date}T${time}:00Z`;
  }

  async function handleConfirm() {
    if (!patientId) {
      setError("Selecione um paciente.");
      return;
    }
    const startsAt = resolveStartsAt();
    if (!startsAt) {
      setError("Informe a data e o horário.");
      return;
    }
    setError(null);
    try {
      await create.mutateAsync({
        patient_id: patientId,
        starts_at: startsAt,
        duration_min: 30,
        dentist_id: dentistId || undefined,
        notes: notes.trim() || undefined,
      });
      onOpenChange(false);
    } catch (err) {
      setError(errorMessage(err, "Não foi possível agendar."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Agendar consulta"
      description={
        slot
          ? `Horário: ${formatTimeUTC(slot.starts_at)} (30 min)`
          : "Escolha a data, o horário (UTC) e o paciente."
      }
    >
      <div className="flex flex-col gap-4">
        {!slot && (
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="date">Data</Label>
              <Input
                id="date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="time">Horário (UTC)</Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
              />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="patient">Paciente</Label>
          <select
            id="patient"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className={selectClass}
          >
            <option value="">Selecione...</option>
            {patients.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome} — {p.telefone}
              </option>
            ))}
          </select>
          {patients.data?.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Nenhum paciente cadastrado. Cadastre em "Pacientes" primeiro.
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="dentist">Dentista responsável (opcional)</Label>
          <select
            id="dentist"
            value={dentistId}
            onChange={(e) => setDentistId(e.target.value)}
            className={selectClass}
          >
            <option value="">Sem dentista</option>
            {dentists.map((d) => (
              <option key={d.id} value={d.id}>
                {d.nome ?? d.email}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="notes">Observações (opcional)</Label>
          <Textarea
            id="notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Ex.: limpeza, retorno, queixa do paciente..."
          />
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleConfirm} disabled={create.isPending}>
            {create.isPending && <Spinner />}
            Confirmar
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
