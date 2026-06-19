import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Spinner } from "@/components/ui/spinner";
import { useDeletePatient, usePatients } from "./api";
import { PatientFormDialog } from "./patient-form-dialog";
import type { Patient } from "./schemas";

function avatarInitials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function PatientsPage() {
  const { data, isLoading, isError } = usePatients();
  const del = useDeletePatient();
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Patient | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const list = data ?? [];
    if (!q) return list;
    return list.filter(
      (p) => p.nome.toLowerCase().includes(q) || p.telefone.includes(q),
    );
  }, [data, search]);

  function openNew() {
    setEditing(null);
    setDialogOpen(true);
  }

  function openEdit(p: Patient) {
    setEditing(p);
    setDialogOpen(true);
  }

  async function handleDelete(p: Patient) {
    if (window.confirm(`Excluir o paciente "${p.nome}"?`)) {
      await del.mutateAsync(p.id);
    }
  }

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-5 pb-12">
      {/* Header */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">Pacientes</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {data ? `${data.length} paciente(s) cadastrados na sua clínica.` : "Carregando..."}
          </p>
        </div>
        <button
          onClick={openNew}
          className="inline-flex items-center gap-2 rounded-[11px] bg-primary px-[17px] py-[11px] text-sm font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,.28)] transition-all hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(124,58,237,.36)]"
        >
          <Plus className="h-[17px] w-[17px]" />
          Novo paciente
        </button>
      </div>

      {/* Tabela */}
      <div className="animate-fade-up overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
        {/* Barra de busca */}
        <div className="flex items-center gap-3 border-b border-border-soft px-[18px] py-3.5">
          <div className="relative max-w-[340px] flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nome ou telefone..."
              className="w-full rounded-[10px] border border-input bg-secondary py-2 pl-9 pr-3 text-[13.5px] text-foreground placeholder:text-muted-foreground focus:border-primary focus:bg-card focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            />
          </div>
        </div>

        {/* Header da tabela */}
        <div className="grid grid-cols-[2.4fr_1.6fr_2fr_0.8fr] items-center gap-3 border-b border-border-soft px-[22px] py-3 text-[11.5px] font-bold uppercase tracking-[.04em] text-muted-foreground">
          <div>Paciente</div>
          <div>Telefone</div>
          <div>E-mail</div>
          <div className="text-right">Ações</div>
        </div>

        {/* Estado de carga */}
        {isLoading && (
          <div className="flex items-center justify-center p-10">
            <Spinner className="text-primary" />
          </div>
        )}
        {isError && (
          <p className="p-6 text-sm text-destructive">Erro ao carregar pacientes.</p>
        )}
        {!isLoading && !isError && filtered.length === 0 && (
          <p className="p-12 text-center text-sm text-muted-foreground">
            Nenhum paciente encontrado.
          </p>
        )}

        {/* Linhas */}
        {filtered.map((p, i) => (
          <PatientRow
            key={p.id}
            p={p}
            delay={`${i * 0.04}s`}
            onEdit={() => openEdit(p)}
            onDelete={() => handleDelete(p)}
          />
        ))}
      </div>

      <PatientFormDialog open={dialogOpen} onOpenChange={setDialogOpen} patient={editing} />
    </div>
  );
}

function PatientRow({
  p,
  delay,
  onEdit,
  onDelete,
}: {
  p: Patient;
  delay: string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const abbr = avatarInitials(p.nome);

  return (
    <div
      className="animate-fade-up grid grid-cols-[2.4fr_1.6fr_2fr_0.8fr] items-center gap-3 border-b border-border-soft px-[22px] py-[13px] transition-colors hover:bg-secondary last:border-0"
      style={{ animationDelay: delay }}
    >
      {/* Avatar + nome */}
      <div className="flex min-w-0 items-center gap-3">
        <div
          className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-[#6D28D9]"
          style={{ background: "linear-gradient(135deg, #EDE9FE, #CCFBF1)" }}
        >
          {abbr}
        </div>
        <span className="truncate text-sm font-semibold text-foreground">{p.nome}</span>
      </div>

      {/* Telefone */}
      <span className="tabular-nums text-[13.5px] text-muted-foreground">{p.telefone}</span>

      {/* Email */}
      <span className="truncate text-[13.5px] text-muted-foreground">{p.email || "—"}</span>

      {/* Ações */}
      <div className="flex items-center justify-end gap-1">
        <ActionBtn
          onClick={onEdit}
          hoverBg="#F4F1FE"
          hoverColor="#7C3AED"
          title="Editar"
        >
          <Pencil className="h-4 w-4" />
        </ActionBtn>
        <ActionBtn
          onClick={onDelete}
          hoverBg="#FEF2F2"
          hoverColor="#DC2626"
          title="Excluir"
        >
          <Trash2 className="h-4 w-4" />
        </ActionBtn>
      </div>
    </div>
  );
}

function ActionBtn({
  onClick,
  hoverBg,
  hoverColor,
  title,
  children,
}: {
  onClick: () => void;
  hoverBg: string;
  hoverColor: string;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="group flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-all"
      style={
        {
          "--hbg": hoverBg,
          "--hcol": hoverColor,
        } as React.CSSProperties
      }
      onMouseEnter={(e) => {
        const el = e.currentTarget;
        el.style.background = hoverBg;
        el.style.color = hoverColor;
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget;
        el.style.background = "";
        el.style.color = "";
      }}
    >
      {children}
    </button>
  );
}
