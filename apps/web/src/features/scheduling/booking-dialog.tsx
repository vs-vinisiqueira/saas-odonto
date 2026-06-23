import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { usePatients } from "@/features/patients/api";
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

export function BookingDialog({ open, onOpenChange, slot, defaultDate }: Props) {
  const patients = usePatients();
  const create = useCreateAppointment();
  const [patientId, setPatientId] = useState("");
  // Data/hora manuais (em UTC), usadas quando não há slot pré-selecionado.
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setPatientId("");
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
            className={cn(
              "h-10 w-full rounded-md border border-input bg-background px-3 text-sm",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
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
