import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { useCreatePatient, useUpdatePatient } from "./api";
import { patientFormSchema, type Patient, type PatientFormInput } from "./schemas";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient?: Patient | null;
}

export function PatientFormDialog({ open, onOpenChange, patient }: Props) {
  const isEdit = Boolean(patient);
  const create = useCreatePatient();
  const update = useUpdatePatient(patient?.id ?? "");
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PatientFormInput>({
    resolver: zodResolver(patientFormSchema),
    defaultValues: { nome: "", telefone: "", email: "", observacoes: "" },
  });

  // Repopula o form quando abre (novo vs edição).
  useEffect(() => {
    if (open) {
      reset({
        nome: patient?.nome ?? "",
        telefone: patient?.telefone ?? "",
        email: patient?.email ?? "",
        observacoes: patient?.observacoes ?? "",
      });
      setFormError(null);
    }
  }, [open, patient, reset]);

  async function onSubmit(values: PatientFormInput) {
    setFormError(null);
    try {
      if (isEdit) {
        await update.mutateAsync(values);
      } else {
        await create.mutateAsync(values);
      }
      onOpenChange(false);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível salvar o paciente."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Editar paciente" : "Novo paciente"}
      description="Os dados ficam isolados por clínica."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="nome">Nome</Label>
          <Input id="nome" {...register("nome")} />
          {errors.nome && <p className="text-sm text-destructive">{errors.nome.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="telefone">Telefone</Label>
          <Input id="telefone" placeholder="+5511999990000" {...register("telefone")} />
          {errors.telefone && (
            <p className="text-sm text-destructive">{errors.telefone.message}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">E-mail (opcional)</Label>
          <Input id="email" type="email" {...register("email")} />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="observacoes">Observações (opcional)</Label>
          <Input id="observacoes" {...register("observacoes")} />
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
            Salvar
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
