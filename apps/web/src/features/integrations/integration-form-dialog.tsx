import { Check, Copy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { errorMessage } from "@/lib/api";
import { useUpdateIntegration } from "./api";
import { PROVIDER_META, type Integration } from "./schemas";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  integration: Integration | null;
}

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

export function IntegrationFormDialog({ open, onOpenChange, integration }: Props) {
  const update = useUpdateIntegration();
  const meta = integration ? PROVIDER_META[integration.provider] : null;

  const [enabled, setEnabled] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (open && integration) {
      setEnabled(integration.enabled);
      // Públicos vêm preenchidos; segredos sempre em branco (mantém se não mexer).
      const init: Record<string, string> = {};
      for (const f of PROVIDER_META[integration.provider].fields) {
        init[f.key] = f.secret ? "" : integration.public_config[f.key] ?? "";
      }
      setValues(init);
      setFormError(null);
    }
  }, [open, integration]);

  const webhookUrl = useMemo(() => {
    if (!meta?.webhookPath) return null;
    return `${API_BASE.replace(/\/$/, "")}${meta.webhookPath}`;
  }, [meta]);

  if (!integration || !meta) return null;

  function setField(key: string, value: string) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function missingRequired(): string[] {
    if (!integration) return [];
    return integration.required_fields.filter((key) => {
      const filled = (values[key] ?? "").trim() !== "";
      const hasHint = Boolean(integration.secret_hints[key]); // segredo já salvo
      return !filled && !hasHint;
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!integration) return;

    if (enabled && missingRequired().length > 0) {
      setFormError(
        "Preencha os campos obrigatórios antes de ativar a integração.",
      );
      return;
    }

    const secrets: Record<string, string> = {};
    const public_config: Record<string, string> = {};
    for (const f of meta!.fields) {
      const val = (values[f.key] ?? "").trim();
      if (f.secret) {
        if (val !== "") secrets[f.key] = val; // em branco = mantém o atual
      } else {
        public_config[f.key] = val; // permite limpar
      }
    }

    try {
      await update.mutateAsync({
        provider: integration.provider,
        data: { enabled, public_config, secrets },
      });
      onOpenChange(false);
    } catch (err) {
      setFormError(errorMessage(err, "Não foi possível salvar a integração."));
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Configurar ${meta.label}`}
      description={meta.intro}
      className="max-w-lg"
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        {webhookUrl && <WebhookBox label={meta.webhookLabel} url={webhookUrl} />}

        {meta.fields.map((f) => {
          const hint = integration.secret_hints[f.key];
          return (
            <div key={f.key} className="flex flex-col gap-1.5">
              <Label htmlFor={f.key}>
                {f.label}
                {f.optional && (
                  <span className="ml-1 text-xs font-normal text-muted-foreground">
                    (opcional)
                  </span>
                )}
              </Label>
              {f.type === "textarea" ? (
                <Textarea
                  id={f.key}
                  rows={5}
                  className="font-mono text-xs"
                  placeholder={f.secret && hint ? "•••••••• (preenchido — deixe em branco para manter)" : f.placeholder}
                  value={values[f.key] ?? ""}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              ) : (
                <Input
                  id={f.key}
                  type={f.type === "password" ? "password" : "text"}
                  autoComplete="off"
                  placeholder={f.secret && hint ? `•••••••• (atual: ${hint}) — deixe em branco para manter` : f.placeholder}
                  value={values[f.key] ?? ""}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              )}
              {f.help && <p className="text-xs text-muted-foreground">{f.help}</p>}
            </div>
          );
        })}

        <label className="mt-1 flex items-center gap-3 rounded-[11px] border bg-secondary/40 px-4 py-3">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="h-4 w-4 accent-[#7C3AED]"
          />
          <span className="flex flex-col">
            <span className="text-sm font-semibold text-foreground">
              Ativar esta integração
            </span>
            <span className="text-xs text-muted-foreground">
              Quando ativa, o sistema passa a usar estas credenciais.
            </span>
          </span>
        </label>

        {formError && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError}
          </p>
        )}

        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={update.isPending}>
            {update.isPending && <Spinner />}
            Salvar
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function WebhookBox({ label, url }: { label?: string; url: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard indisponível: o usuário copia manualmente */
    }
  }

  return (
    <div className="flex flex-col gap-1.5 rounded-[11px] border border-dashed border-primary/40 bg-primary/[0.04] px-3.5 py-3">
      {label && <span className="text-xs font-semibold text-foreground">{label}</span>}
      <div className="flex items-center gap-2">
        <code className="min-w-0 flex-1 truncate rounded bg-background px-2 py-1.5 text-xs text-muted-foreground">
          {url}
        </code>
        <button
          type="button"
          onClick={copy}
          title="Copiar"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
