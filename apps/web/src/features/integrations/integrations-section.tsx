import {
  CalendarDays,
  CreditCard,
  MessageCircle,
  Settings2,
  Sparkles,
  Unplug,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useDisconnectIntegration, useIntegrations } from "./api";
import { IntegrationFormDialog } from "./integration-form-dialog";
import { PROVIDER_META, PROVIDER_ORDER, type Integration, type ProviderId } from "./schemas";

const ICONS: Record<ProviderId, typeof MessageCircle> = {
  whatsapp: MessageCircle,
  ai: Sparkles,
  mercadopago: CreditCard,
  google_calendar: CalendarDays,
};

function statusOf(it: Integration): { label: string; variant: "success" | "warning" | "muted" } {
  if (it.enabled && it.configured) return { label: "Conectado", variant: "success" };
  if (it.configured) return { label: "Configurado · desligado", variant: "warning" };
  return { label: "Não configurado", variant: "muted" };
}

export function IntegrationsSection() {
  const { data, isLoading, isError } = useIntegrations();
  const disconnect = useDisconnectIntegration();
  const [editing, setEditing] = useState<Integration | null>(null);

  const byProvider = new Map((data ?? []).map((i) => [i.provider, i]));
  // Mantém a ordem curada mesmo que o backend devolva outra.
  const ordered = PROVIDER_ORDER.map((p) => byProvider.get(p)).filter(
    (i): i is Integration => Boolean(i),
  );

  async function onDisconnect(it: Integration) {
    if (
      window.confirm(
        `Desconectar ${it.label}? As credenciais salvas serão apagadas e a integração desligada.`,
      )
    ) {
      await disconnect.mutateAsync(it.provider);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h3 className="text-lg font-bold text-foreground">Integrações</h3>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Conecte os serviços externos da clínica. Cada chave fica guardada de forma
          cifrada e nunca é exibida de novo.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center p-12">
          <Spinner className="text-primary" />
        </div>
      )}
      {isError && (
        <p className="rounded-[18px] border bg-card p-6 text-sm text-destructive">
          Erro ao carregar as integrações.
        </p>
      )}

      {!isLoading && !isError && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {ordered.map((it) => {
            const meta = PROVIDER_META[it.provider];
            const Icon = ICONS[it.provider];
            const status = statusOf(it);
            return (
              <div
                key={it.provider}
                className="flex flex-col rounded-[18px] border bg-card p-5 shadow-[0_1px_2px_rgba(16,24,40,.04)]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-[13px] bg-primary/10 text-primary">
                      <Icon className="h-[22px] w-[22px]" />
                    </div>
                    <div>
                      <h4 className="text-[15px] font-bold text-foreground">{meta.label}</h4>
                      <Badge variant={status.variant} className="mt-1">
                        {status.label}
                      </Badge>
                    </div>
                  </div>
                </div>

                <p className="mt-3 flex-1 text-sm text-muted-foreground">{meta.tagline}</p>

                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={() => setEditing(it)}
                    className="inline-flex items-center gap-2 rounded-[10px] bg-primary px-4 py-2 text-sm font-bold text-white transition-all hover:-translate-y-px hover:shadow-[0_6px_16px_rgba(124,58,237,.30)]"
                  >
                    <Settings2 className="h-4 w-4" />
                    {it.configured ? "Editar" : "Configurar"}
                  </button>
                  {(it.configured || it.enabled) && (
                    <button
                      onClick={() => onDisconnect(it)}
                      title="Desconectar"
                      className="inline-flex items-center gap-2 rounded-[10px] border px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                    >
                      <Unplug className="h-4 w-4" />
                      Desconectar
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <IntegrationFormDialog
        open={editing !== null}
        onOpenChange={(o) => !o && setEditing(null)}
        integration={editing}
      />
    </div>
  );
}
