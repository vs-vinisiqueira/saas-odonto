import { Plus, QrCode, RefreshCw } from "lucide-react";
import { useState } from "react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useCharges, useRefreshCharge } from "./api";
import { ChargeFormDialog } from "./charge-form-dialog";

const STATUS: Record<string, { label: string; variant: BadgeProps["variant"] }> = {
  pending: { label: "Pendente", variant: "warning" },
  paid: { label: "Pago", variant: "success" },
  expired: { label: "Expirado", variant: "muted" },
  canceled: { label: "Cancelado", variant: "destructive" },
};

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function BillingPage() {
  const { data, isLoading, isError } = useCharges();
  const refresh = useRefreshCharge();
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Cobranças</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.length} cobrança(s)` : "Carregando..."}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" />
          Nova cobrança
        </Button>
      </div>

      <Card className="divide-y">
        {isLoading && (
          <div className="flex items-center justify-center p-8">
            <Spinner className="text-primary" />
          </div>
        )}
        {isError && (
          <p className="p-6 text-sm text-destructive">Erro ao carregar cobranças.</p>
        )}
        {!isLoading && !isError && (data?.length ?? 0) === 0 && (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Nenhuma cobrança ainda.
          </p>
        )}
        {data?.map((c) => {
          const st = STATUS[c.status] ?? { label: c.status, variant: "muted" as const };
          return (
            <div key={c.id} className="flex items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="font-medium">{brl.format(Number(c.valor))}</p>
                <p className="truncate text-sm text-muted-foreground">
                  {c.descricao || "Sem descrição"}
                  <span className="ml-1 inline-flex items-center gap-1">
                    <QrCode className="inline h-3 w-3" />
                    {c.charge_id}
                  </span>
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Badge variant={st.variant}>{st.label}</Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  title="Atualizar status"
                  disabled={refresh.isPending}
                  onClick={() => refresh.mutate(c.id)}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          );
        })}
      </Card>

      <ChargeFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
