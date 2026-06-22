import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { useCreateUser, useUpdateUser } from "./api";
import {
  ROLES,
  ROLE_LABELS,
  userCreateSchema,
  userEditSchema,
  type User,
  type UserCreateInput,
  type UserEditInput,
} from "./schemas";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user?: User | null;
}

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1";

export function UserFormDialog({ open, onOpenChange, user }: Props) {
  const isEdit = Boolean(user);
  const create = useCreateUser();
  const update = useUpdateUser();
  const [formError, setFormError] = useState<string | null>(null);

  // Form de criação tem senha; o de edição não. Usamos o schema certo por modo.
  const form = useForm<UserCreateInput>({
    resolver: zodResolver(isEdit ? userEditSchema : userCreateSchema),
    defaultValues: { nome: "", email: "", telefone: "", role: "dentist", password: "" },
  });
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = form;

  useEffect(() => {
    if (open) {
      reset({
        nome: user?.nome ?? "",
        email: user?.email ?? "",
        telefone: user?.telefone ?? "",
        role: user?.role ?? "dentist",
        password: "",
      });
      setFormError(null);
    }
  }, [open, user, reset]);

  async function onSubmit(values: UserCreateInput) {
    setFormError(null);
    try {
      if (isEdit && user) {
        const data: UserEditInput = {
          nome: values.nome,
          telefone: values.telefone,
          role: values.role,
        };
        await update.mutateAsync({ id: user.id, data });
      } else {
        await create.mutateAsync(values);
      }
      onOpenChange(false);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível salvar o usuário."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Editar usuário" : "Novo usuário"}
      description={
        isEdit
          ? "Atualize os dados e o papel do membro da equipe."
          : "Defina uma senha temporária; a pessoa poderá usá-la para entrar."
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="nome">Nome completo</Label>
          <Input id="nome" {...register("nome")} />
          {errors.nome && <p className="text-sm text-destructive">{errors.nome.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            disabled={isEdit}
            {...register("email")}
          />
          {isEdit && (
            <p className="text-xs text-muted-foreground">O e-mail não pode ser alterado.</p>
          )}
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="telefone">Telefone (opcional)</Label>
          <Input id="telefone" placeholder="+5511999990000" {...register("telefone")} />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="role">Papel</Label>
          <select id="role" className={selectClass} {...register("role")}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>
          {errors.role && <p className="text-sm text-destructive">{errors.role.message}</p>}
        </div>

        {!isEdit && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">Senha temporária</Label>
            <Input id="password" type="text" autoComplete="off" {...register("password")} />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>
        )}

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
