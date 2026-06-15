import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { usePatients } from "@/features/patients/api";
import { errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCreateCharge } from "./api";
import { chargeFormSchema, type ChargeFormInput } from "./schemas";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChargeFormDialog({ open, onOpenChange }: Props) {
  const create = useCreateCharge();
  const patients = usePatients();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChargeFormInput>({
    resolver: zodResolver(chargeFormSchema),
    defaultValues: { valor: undefined, descricao: "", patient_id: "" },
  });

  useEffect(() => {
    if (open) {
      reset({ valor: undefined, descricao: "", patient_id: "" });
      setFormError(null);
    }
  }, [open, reset]);

  async function onSubmit(values: ChargeFormInput) {
    setFormError(null);
    try {
      await create.mutateAsync(values);
      onOpenChange(false);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível criar a cobrança."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Nova cobrança Pix"
      description="Gera um QR Pix (provedor mock nesta fase)."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="valor">Valor (R$)</Label>
          <Input
            id="valor"
            type="number"
            step="0.01"
            min="0"
            placeholder="150.00"
            {...register("valor")}
          />
          {errors.valor && (
            <p className="text-sm text-destructive">{errors.valor.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="descricao">Descrição (opcional)</Label>
          <Input id="descricao" placeholder="Limpeza, consulta..." {...register("descricao")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="patient_id">Paciente (opcional)</Label>
          <select
            id="patient_id"
            {...register("patient_id")}
            className={cn(
              "h-10 w-full rounded-md border border-input bg-background px-3 text-sm",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <option value="">—</option>
            {patients.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </select>
        </div>

        {formError && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </p>
        )}

        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Spinner />}
            Gerar cobrança
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
