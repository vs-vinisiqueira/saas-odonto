export type ProviderId = "whatsapp" | "mercadopago" | "google_calendar" | "ai";

/** Status de uma integração (espelha IntegrationOut do backend). Segredos nunca
 *  vêm em claro — só `secret_hints` mascarados (ex.: "••••1234"). */
export interface Integration {
  provider: ProviderId;
  label: string;
  enabled: boolean;
  configured: boolean;
  public_config: Record<string, string | undefined>;
  secret_hints: Record<string, string>;
  secret_fields: string[];
  public_fields: string[];
  required_fields: string[];
}

export interface IntegrationField {
  key: string;
  label: string;
  type: "text" | "password" | "textarea";
  secret: boolean;
  placeholder?: string;
  help?: string;
  optional?: boolean;
}

export interface ProviderMeta {
  id: ProviderId;
  label: string;
  tagline: string;
  /** Texto de ajuda mostrado no topo do formulário. */
  intro?: string;
  fields: IntegrationField[];
  /** Caminho do webhook a colar no painel do provedor (montado sobre a API). */
  webhookPath?: string;
  webhookLabel?: string;
}

export const PROVIDER_META: Record<ProviderId, ProviderMeta> = {
  whatsapp: {
    id: "whatsapp",
    label: "WhatsApp (Meta)",
    tagline: "Atendimento automático pela IA no WhatsApp da clínica.",
    intro:
      "Conecte o número do WhatsApp Business da clínica (Meta Cloud API). A IA responde os pacientes e marca consultas automaticamente.",
    fields: [
      {
        key: "access_token",
        label: "Token de acesso",
        type: "password",
        secret: true,
        placeholder: "EAAG... (token permanente da Meta)",
        help: "Token permanente gerado no painel de desenvolvedores da Meta.",
      },
      {
        key: "phone_number_id",
        label: "ID do número (phone_number_id)",
        type: "text",
        secret: false,
        placeholder: "1234567890",
        help: "Encontrado na configuração da API do WhatsApp, junto ao número.",
      },
      {
        key: "api_version",
        label: "Versão da API",
        type: "text",
        secret: false,
        placeholder: "v21.0",
        optional: true,
        help: "Opcional. Deixe em branco para usar o padrão.",
      },
    ],
    webhookPath: "/ai/whatsapp/webhook",
    webhookLabel: "Cole esta URL no webhook do app na Meta:",
  },
  mercadopago: {
    id: "mercadopago",
    label: "Mercado Pago",
    tagline: "Cobranças Pix automáticas para os pacientes.",
    intro:
      "Conecte sua conta do Mercado Pago para gerar cobranças Pix direto pelo sistema.",
    fields: [
      {
        key: "access_token",
        label: "Access Token de produção",
        type: "password",
        secret: true,
        placeholder: "APP_USR-...",
        help: "Disponível em Suas integrações → Credenciais de produção.",
      },
      {
        key: "payer_email",
        label: "E-mail do pagador (sandbox)",
        type: "text",
        secret: false,
        placeholder: "test_user@testuser.com",
        optional: true,
        help: "Opcional. Usado apenas em ambiente de testes.",
      },
    ],
    webhookPath: "/billing/mercadopago/webhook",
    webhookLabel: "Cole esta URL nas notificações (webhooks) do Mercado Pago:",
  },
  google_calendar: {
    id: "google_calendar",
    label: "Google Calendar",
    tagline: "Espelha os agendamentos na agenda do Google.",
    intro:
      "Cole o conteúdo do arquivo credentials.json de uma Service Account com acesso ao calendário. Compartilhe o calendário com o e-mail da Service Account.",
    fields: [
      {
        key: "sa_credentials_json",
        label: "credentials.json da Service Account",
        type: "textarea",
        secret: true,
        placeholder: '{ "type": "service_account", "client_email": "...", "private_key": "..." }',
        help: "Cole o JSON completo. Fica guardado de forma cifrada.",
      },
      {
        key: "calendar_id",
        label: "ID do calendário",
        type: "text",
        secret: false,
        placeholder: "primary",
        optional: true,
        help: "Opcional. Use 'primary' para o calendário principal.",
      },
    ],
  },
  ai: {
    id: "ai",
    label: "Assistente de IA (Gemini)",
    tagline: "Cérebro da recepcionista virtual. Sem chave, usa o modo de demonstração.",
    intro:
      "Conecte uma chave do Google Gemini para a IA conversar em linguagem natural. Sem chave, o sistema usa um modo de demonstração simples.",
    fields: [
      {
        key: "api_key",
        label: "Chave de API do Gemini",
        type: "password",
        secret: true,
        placeholder: "AIza...",
        help: "Gerada no Google AI Studio.",
      },
      {
        key: "model",
        label: "Modelo",
        type: "text",
        secret: false,
        placeholder: "gemini-2.5-flash",
        optional: true,
        help: "Opcional. Deixe em branco para usar o padrão (gemini-2.5-flash).",
      },
    ],
  },
};

export const PROVIDER_ORDER: ProviderId[] = [
  "whatsapp",
  "ai",
  "mercadopago",
  "google_calendar",
];
