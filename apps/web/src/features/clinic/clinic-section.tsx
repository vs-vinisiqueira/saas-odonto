import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { useMyClinic, useUpdateClinic } from "./api";

const clinicFormSchema = z.object({
  nome: z.string().min(1, "Nome é obrigatório"),
  cnpj: z.string().optional(),
  razao_social: z.string().optional(),
  endereco: z.string().optional(),
  telefone: z.string().optional(),
  logo_url: z.string().optional(),
});

type ClinicFormInput = z.infer<typeof clinicFormSchema>;

export function ClinicSection() {
  const clinic = useMyClinic();
  const update = useUpdateClinic();
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ClinicFormInput>({
    resolver: zodResolver(clinicFormSchema),
    defaultValues: { nome: "", cnpj: "", razao_social: "", endereco: "", telefone: "", logo_url: "" },
  });

  useEffect(() => {
    if (!clinic.data) return;
    const cd = clinic.data.config.clinic_data ?? {};
    reset({
      nome: clinic.data.nome,
      cnpj: cd.cnpj ?? "",
      razao_social: cd.razao_social ?? "",
      endereco: cd.endereco ?? "",
      telefone: cd.telefone ?? "",
      logo_url: cd.logo_url ?? "",
    });
  }, [clinic.data, reset]);

  async function onSubmit(values: ClinicFormInput) {
    setFormError(null);
    setSaved(false);
    try {
      await update.mutateAsync({
        nome: values.nome,
        config: {
          clinic_data: {
            cnpj: values.cnpj || null,
            razao_social: values.razao_social || null,
            endereco: values.endereco || null,
            telefone: values.telefone || null,
            logo_url: values.logo_url || null,
          },
        },
      });
      setSaved(true);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível salvar os dados da clínica."));
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
        <h3 className="text-lg font-bold text-foreground">Dados da clínica</h3>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Essas informações aparecem em documentos e comunicações com pacientes.
        </p>
      </div>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-4 rounded-[18px] border bg-card p-6 shadow-[0_1px_2px_rgba(16,24,40,.04)]"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="nome">Nome da clínica</Label>
          <Input id="nome" {...register("nome")} />
          {errors.nome && <p className="text-sm text-destructive">{errors.nome.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="logo_url">URL do logo (opcional)</Label>
          <Input id="logo_url" placeholder="https://..." {...register("logo_url")} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="cnpj">CNPJ</Label>
            <Input id="cnpj" placeholder="00.000.000/0000-00" {...register("cnpj")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="razao_social">Razão social</Label>
            <Input id="razao_social" {...register("razao_social")} />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="telefone">Telefone</Label>
            <Input id="telefone" placeholder="+5511999990000" {...register("telefone")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="endereco">Endereço</Label>
            <Input id="endereco" {...register("endereco")} />
          </div>
        </div>

        {formError && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </p>
        )}
        {saved && !formError && (
          <p className="rounded-md bg-success/10 px-3 py-2 text-sm text-success">
            Dados da clínica salvos.
          </p>
        )}

        <div className="mt-1 flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Spinner />}
            Salvar
          </Button>
        </div>
      </form>
    </div>
  );
}
