import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { usePatients } from "@/features/patients/api";
import { errorMessage } from "@/lib/api";
import { formatTimeUTC } from "@/lib/datetime";
import { cn } from "@/lib/utils";
import { useCreateAppointment, type Slot } from "./api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  slot: Slot | null;
}

export function BookingDialog({ open, onOpenChange, slot }: Props) {
  const patients = usePatients();
  const create = useCreateAppointment();
  const [patientId, setPatientId] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setPatientId("");
      setError(null);
    }
  }, [open]);

  async function handleConfirm() {
    if (!slot || !patientId) {
      setError("Selecione um paciente.");
      return;
    }
    setError(null);
    try {
      await create.mutateAsync({
        patient_id: patientId,
        starts_at: slot.starts_at,
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
        slot ? `Horário: ${formatTimeUTC(slot.starts_at)} (30 min)` : undefined
      }
    >
      <div className="flex flex-col gap-4">
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
