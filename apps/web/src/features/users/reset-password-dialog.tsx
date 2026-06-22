import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { useResetPassword } from "./api";
import { passwordResetSchema, type PasswordResetInput, type User } from "./schemas";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: User | null;
}

export function ResetPasswordDialog({ open, onOpenChange, user }: Props) {
  const reset = useResetPassword();
  const [formError, setFormError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const {
    register,
    handleSubmit,
    reset: resetForm,
    formState: { errors, isSubmitting },
  } = useForm<PasswordResetInput>({
    resolver: zodResolver(passwordResetSchema),
    defaultValues: { password: "" },
  });

  useEffect(() => {
    if (open) {
      resetForm({ password: "" });
      setFormError(null);
      setDone(false);
    }
  }, [open, resetForm]);

  async function onSubmit(values: PasswordResetInput) {
    if (!user) return;
    setFormError(null);
    try {
      await reset.mutateAsync({ id: user.id, password: values.password });
      setDone(true);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível redefinir a senha."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Redefinir senha"
      description={user ? `Defina uma nova senha para ${user.nome ?? user.email}.` : undefined}
    >
      {done ? (
        <div className="flex flex-col gap-4">
          <p className="rounded-md bg-green-100 px-3 py-2 text-sm text-green-700">
            Senha redefinida. Passe a nova senha para a pessoa — ela poderá entrar imediatamente.
          </p>
          <div className="flex justify-end">
            <Button onClick={() => onOpenChange(false)}>Fechar</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="new-password">Nova senha</Label>
            <Input id="new-password" type="text" autoComplete="off" {...register("password")} />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
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
              Redefinir
            </Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}
