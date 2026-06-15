import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useDeletePatient, usePatients } from "./api";
import { PatientFormDialog } from "./patient-form-dialog";
import type { Patient } from "./schemas";

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
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Pacientes</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.length} cadastrado(s)` : "Carregando..."}
          </p>
        </div>
        <Button onClick={openNew}>
          <Plus className="h-4 w-4" />
          Novo paciente
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Buscar por nome ou telefone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <Card className="divide-y">
        {isLoading && (
          <div className="flex items-center justify-center p-8">
            <Spinner className="text-primary" />
          </div>
        )}
        {isError && (
          <p className="p-6 text-sm text-destructive">Erro ao carregar pacientes.</p>
        )}
        {!isLoading && !isError && filtered.length === 0 && (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Nenhum paciente encontrado.
          </p>
        )}
        {filtered.map((p) => (
          <div key={p.id} className="flex items-center justify-between gap-3 p-4">
            <div className="min-w-0">
              <p className="truncate font-medium">{p.nome}</p>
              <p className="truncate text-sm text-muted-foreground">
                {p.telefone}
                {p.email ? ` · ${p.email}` : ""}
              </p>
            </div>
            <div className="flex shrink-0 gap-1">
              <Button variant="ghost" size="icon" onClick={() => openEdit(p)}>
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(p)}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </Card>

      <PatientFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        patient={editing}
      />
    </div>
  );
}
