import { KeyRound, Pencil, Plus, Power, PowerOff } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useAuthStore } from "@/lib/auth-store";
import { useUpdateUser, useUsers } from "./api";
import { ResetPasswordDialog } from "./reset-password-dialog";
import { ROLE_LABELS, type User } from "./schemas";
import { UserFormDialog } from "./user-form-dialog";

function initials(u: User) {
  const base = u.nome?.trim() || u.email;
  return base
    .split(/[\s@.]+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function UsersSection() {
  const { data, isLoading, isError } = useUsers();
  const update = useUpdateUser();
  const currentUserId = useAuthStore((s) => s.user?.sub);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetting, setResetting] = useState<User | null>(null);

  function openNew() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(u: User) {
    setEditing(u);
    setFormOpen(true);
  }

  async function toggleActive(u: User) {
    const verb = u.is_active ? "desativar" : "reativar";
    if (window.confirm(`Deseja ${verb} ${u.nome ?? u.email}?`)) {
      await update.mutateAsync({ id: u.id, data: { is_active: !u.is_active } });
    }
  }

  const users = data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-foreground">Usuários da equipe</h3>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Crie acessos para dentistas e recepção. Só administradores gerenciam a equipe.
          </p>
        </div>
        <button
          onClick={openNew}
          className="inline-flex items-center gap-2 rounded-[11px] bg-primary px-[17px] py-[11px] text-sm font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,.28)] transition-all hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(124,58,237,.36)]"
        >
          <Plus className="h-[17px] w-[17px]" />
          Novo usuário
        </button>
      </div>

      <div className="overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
        <div className="overflow-x-auto">
        <div className="min-w-[780px]">
        <div className="grid grid-cols-[2.4fr_2fr_1.2fr_1fr_120px] items-center gap-3 border-b border-border-soft px-[22px] py-3 text-[11.5px] font-bold uppercase tracking-[.04em] text-muted-foreground">
          <div>Usuário</div>
          <div>E-mail</div>
          <div>Papel</div>
          <div>Status</div>
          <div className="text-right">Ações</div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center p-10">
            <Spinner className="text-primary" />
          </div>
        )}
        {isError && (
          <p className="p-6 text-sm text-destructive">Erro ao carregar usuários.</p>
        )}
        {!isLoading && !isError && users.length === 0 && (
          <p className="p-12 text-center text-sm text-muted-foreground">
            Nenhum usuário cadastrado.
          </p>
        )}

        {users.map((u) => {
          const isSelf = u.id === currentUserId;
          return (
            <div
              key={u.id}
              className="grid grid-cols-[2.4fr_2fr_1.2fr_1fr_120px] items-center gap-3 border-b border-border-soft px-[22px] py-[13px] transition-colors hover:bg-secondary last:border-0"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div
                  className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-[#6D28D9]"
                  style={{ background: "linear-gradient(135deg, #EDE9FE, #CCFBF1)" }}
                >
                  {initials(u)}
                </div>
                <div className="flex min-w-0 flex-col">
                  <span className="truncate text-sm font-semibold text-foreground">
                    {u.nome ?? "—"}
                    {isSelf && (
                      <span className="ml-1.5 text-xs font-normal text-muted-foreground">
                        (você)
                      </span>
                    )}
                  </span>
                  {u.telefone && (
                    <span className="truncate text-xs text-muted-foreground">{u.telefone}</span>
                  )}
                </div>
              </div>

              <span className="truncate text-[13.5px] text-muted-foreground">{u.email}</span>

              <div>
                <Badge variant={u.role === "owner" ? "default" : "muted"}>
                  {ROLE_LABELS[u.role]}
                </Badge>
              </div>

              <div>
                {u.is_active ? (
                  <Badge variant="success">Ativo</Badge>
                ) : (
                  <Badge variant="destructive">Inativo</Badge>
                )}
              </div>

              <div className="flex items-center justify-end gap-1">
                <IconBtn title="Editar" onClick={() => openEdit(u)}>
                  <Pencil className="h-4 w-4" />
                </IconBtn>
                <IconBtn title="Redefinir senha" onClick={() => setResetting(u)}>
                  <KeyRound className="h-4 w-4" />
                </IconBtn>
                <IconBtn
                  title={isSelf ? "Você não pode se desativar" : u.is_active ? "Desativar" : "Reativar"}
                  onClick={() => toggleActive(u)}
                  disabled={isSelf}
                >
                  {u.is_active ? (
                    <PowerOff className="h-4 w-4" />
                  ) : (
                    <Power className="h-4 w-4" />
                  )}
                </IconBtn>
              </div>
            </div>
          );
        })}
        </div>
        </div>
      </div>

      <UserFormDialog open={formOpen} onOpenChange={setFormOpen} user={editing} />
      <ResetPasswordDialog
        open={resetting !== null}
        onOpenChange={(o) => !o && setResetting(null)}
        user={resetting}
      />
    </div>
  );
}

function IconBtn({
  onClick,
  title,
  disabled,
  children,
}: {
  onClick: () => void;
  title?: string;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      disabled={disabled}
      className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-all hover:bg-secondary hover:text-foreground disabled:cursor-not-allowed disabled:opacity-30"
    >
      {children}
    </button>
  );
}
