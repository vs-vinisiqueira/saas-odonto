import { Plus, QrCode, RefreshCw, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Spinner } from "@/components/ui/spinner";
import { useCharges, useDeleteCharge, useRefreshCharge } from "./api";
import { ChargeFormDialog } from "./charge-form-dialog";

const STATUS_INFO: Record<string, { label: string; dot: string; bg: string; color: string }> = {
  pending:   { label: "Pendente",  dot: "#F59E0B", bg: "#FFFBEB", color: "#B45309" },
  paid:      { label: "Pago",      dot: "#22C55E", bg: "#F0FDF4", color: "#15803D" },
  approved:  { label: "Pago",      dot: "#22C55E", bg: "#F0FDF4", color: "#15803D" },
  expired:   { label: "Expirado",  dot: "#A1A1AA", bg: "#F4F4F5", color: "#52525B" },
  canceled:  { label: "Cancelado", dot: "#EF4444", bg: "#FEF2F2", color: "#B91C1C" },
  rejected:  { label: "Recusado",  dot: "#EF4444", bg: "#FEF2F2", color: "#B91C1C" },
};

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function BillingPage() {
  const { data, isLoading, isError } = useCharges();
  const refresh = useRefreshCharge();
  const del = useDeleteCharge();
  const [dialogOpen, setDialogOpen] = useState(false);

  function handleDelete(id: string, descricao: string | null) {
    if (window.confirm(`Excluir a cobrança "${descricao || "Cobrança Pix"}"?`)) {
      del.mutate(id);
    }
  }

  const { sumPaid, sumPending } = useMemo(() => {
    const list = data ?? [];
    const isPaid = (s: string) => s === "paid" || s === "approved";
    const sp = list.filter((c) => isPaid(c.status)).reduce((a, c) => a + Number(c.valor), 0);
    const spe = list.filter((c) => c.status === "pending").reduce((a, c) => a + Number(c.valor), 0);
    return { sumPaid: sp, sumPending: spe };
  }, [data]);

  return (
    <div className="mx-auto flex max-w-[1140px] flex-col gap-5 pb-12">
      {/* Header */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">Cobranças</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Gere cobranças via Pix e acompanhe os pagamentos.
          </p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-[11px] bg-primary px-[17px] py-[11px] text-sm font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,.28)] transition-all hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(124,58,237,.36)]"
        >
          <Plus className="h-[17px] w-[17px]" />
          Nova cobrança
        </button>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SummaryCard label="Recebido este mês" value={brl.format(sumPaid)} valueColor="#15803D" delay="0s" />
        <SummaryCard label="A receber" value={brl.format(sumPending)} valueColor="#B45309" delay=".06s" />
        <SummaryCard label="Total de cobranças" value={String(data?.length ?? 0)} valueColor="hsl(var(--foreground))" delay=".12s" />
      </div>

      {/* Tabela */}
      <div className="animate-fade-up overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]" style={{ animationDelay: ".12s" }}>
        {/* Cabeçalho */}
        <div className="grid grid-cols-[2fr_1.6fr_1.2fr_1.2fr_auto] items-center gap-3 border-b border-border-soft px-[22px] py-3 text-[11.5px] font-bold uppercase tracking-[.04em] text-muted-foreground">
          <div>Descrição</div>
          <div>Referência</div>
          <div>Valor</div>
          <div>Status</div>
          <div className="text-right">Ações</div>
        </div>

        {isLoading && (
          <div className="flex justify-center p-10">
            <Spinner className="text-primary" />
          </div>
        )}
        {isError && (
          <p className="p-6 text-sm text-destructive">Erro ao carregar cobranças.</p>
        )}
        {!isLoading && !isError && (data?.length ?? 0) === 0 && (
          <p className="p-12 text-center text-sm text-muted-foreground">Nenhuma cobrança ainda.</p>
        )}

        {data?.map((c) => {
          const st = STATUS_INFO[c.status] ?? STATUS_INFO.pending;
          return (
            <div
              key={c.id}
              className="grid grid-cols-[2fr_1.6fr_1.2fr_1.2fr_auto] items-center gap-3 border-b border-border-soft px-[22px] py-[14px] transition-colors hover:bg-secondary last:border-0"
            >
              {/* Descrição */}
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-accent text-primary">
                  <QrCode className="h-4 w-4" />
                </div>
                <span className="truncate text-sm font-semibold text-foreground">
                  {c.descricao || "Cobrança Pix"}
                </span>
              </div>

              {/* Referência */}
              <span className="truncate font-mono text-[12px] text-muted-foreground">
                {c.charge_id}
              </span>

              {/* Valor */}
              <span className="text-sm font-bold tabular-nums text-foreground">
                {brl.format(Number(c.valor))}
              </span>

              {/* Status badge */}
              <div>
                <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold" style={{ background: st.bg, color: st.color }}>
                  <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: st.dot }} />
                  {st.label}
                </span>
              </div>

              {/* Ações */}
              <div className="flex items-center justify-end gap-1">
                <button
                  onClick={() => refresh.mutate(c.id)}
                  disabled={refresh.isPending}
                  title="Atualizar status"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-primary transition-colors hover:bg-accent disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${refresh.isPending ? "animate-spin" : ""}`} />
                </button>
                <button
                  onClick={() => handleDelete(c.id, c.descricao)}
                  disabled={del.isPending}
                  title="Excluir cobrança"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <ChargeFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}

function SummaryCard({ label, value, valueColor, delay }: { label: string; value: string; valueColor: string; delay: string }) {
  return (
    <div
      className="animate-fade-up rounded-[16px] border bg-card p-[18px] shadow-[0_1px_2px_rgba(16,24,40,.04)]"
      style={{ animationDelay: delay }}
    >
      <div className="text-[12.5px] font-semibold text-muted-foreground">{label}</div>
      <div className="mt-2 text-[26px] font-extrabold tracking-[-0.025em]" style={{ color: valueColor }}>
        {value}
      </div>
    </div>
  );
}
