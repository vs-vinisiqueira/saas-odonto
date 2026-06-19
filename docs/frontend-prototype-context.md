# SaaS Odonto — Contexto para Protótipo Visual de Frontend

> **Para:** Claude Design / Figma / prototipação visual  
> **Objetivo:** criar protótipo de alta fidelidade do painel web para clínicas odontológicas

---

## 1. O produto

**SaaS B2B multi-tenant** para clínicas odontológicas de pequeno porte (2–5 dentistas).  
Diferencial: **atendimento por IA no WhatsApp** — o paciente manda mensagem, a IA agenda, confirma e responde em linguagem natural. O dentista/recepcionista gerencia tudo pelo painel web.

**Usuário primário:** recepcionista ou dono da clínica.  
**Idioma:** 100% português brasileiro (PT-BR).

---

## 2. Design system & marca

| Decisão | Valor |
|---|---|
| Cor primária | `#7C3AED` (violet-600) — roxo vibrante |
| Neutros | zinc / slate |
| Tema | **Claro** (light mode only) |
| Estética | SaaS limpo, profissional, moderno — parecido com Linear, Vercel Dashboard |
| Tipografia | Sans-serif limpa (Inter ou similar) |
| Componentes | shadcn/ui (Tailwind + Radix primitives) |
| Radius | Médio (rounded-md / 8px) |
| Sombras | Sutis (shadow-sm / shadow-md) |

**Paleta orientativa:**
- Primary: `#7C3AED` violet-600
- Primary hover: `#6D28D9` violet-700
- Background: `#FAFAFA` / `#FFFFFF`
- Surface card: `#FFFFFF` border `#E4E4E7` zinc-200
- Text principal: `#18181B` zinc-900
- Text secundário: `#71717A` zinc-500
- Destaque sucesso: `#16A34A` green-600
- Destaque alerta: `#D97706` amber-600
- Destaque erro: `#DC2626` red-600

---

## 3. Layout shell

```
┌──────────────────────────────────────────────────────────┐
│ TOPBAR  [logo/nome clínica]              [avatar usuário] │
├──────────┬───────────────────────────────────────────────┤
│          │                                               │
│ SIDEBAR  │              CONTENT AREA                     │
│ (240px)  │                                               │
│          │                                               │
└──────────┴───────────────────────────────────────────────┘
```

**Sidebar — itens de navegação (com ícone + label):**
1. Dashboard (ícone: gráfico de barras)
2. Pacientes (ícone: pessoas)
3. Agenda (ícone: calendário)
4. Conversas (ícone: chat/mensagem) — **badge com contador de não lidas**
5. Cobranças (ícone: cifrão / carteira)
6. Configurações (ícone: engrenagem) — no rodapé da sidebar

**Topbar:** nome da clínica (ex: "Clínica Sorriso") + avatar do usuário com menu dropdown (perfil / sair).

Mobile: sidebar vira drawer hamburguer.

---

## 4. Telas a prototipar

### 4.1 Login

Tela centralizada (não usa o shell), fundo branco ou gradiente muito sutil.

- Logo / nome do produto no topo
- Card central: "Entrar na sua clínica"
- Campo: E-mail (email@clinica.com)
- Campo: Senha (password)
- Botão primário roxo: "Entrar"
- Link: "Esqueci minha senha" (placeholder)

**Estados:** loading (botão spinner) / erro ("E-mail ou senha incorretos" — banner vermelho abaixo do card).

---

### 4.2 Dashboard

Cards de resumo no topo (grid 4 colunas):
- **Consultas hoje** (número grande + ícone calendário)
- **Novos pacientes esta semana** (número + ícone pessoas)
- **Mensagens não respondidas** (número + ícone chat) — roxo destaque se > 0
- **Cobranças pendentes** (número + ícone $)

Abaixo: dois blocos lado a lado
- **Gráfico de barras** — consultas por dia na semana (dados de `GET /scheduling/stats?from=...&to=...`)
- **Lista "Próximas consultas hoje"** — 5 itens com [horário] [nome paciente] [status badge] [botão cancelar]

Status badge da consulta (pill colorida):
- `scheduled` → cinza/zinc — "Agendada"
- `confirmed` → azul — "Confirmada"
- `cancelled` → vermelho — "Cancelada"
- `completed` → verde — "Concluída"
- `no_show` → laranja — "Não compareceu"

---

### 4.3 Pacientes

**Lista (tabela):**

| Nome | Telefone | E-mail | Ações |
|---|---|---|---|
| Ana Souza | (11) 99999-1111 | ana@email.com | [Editar] [Excluir] |

- Busca por nome (filtro local no frontend)
- Botão "+ Novo Paciente" (roxo, canto superior direito)
- Paginação simples

**Modal "Novo / Editar Paciente":**
- Nome* (text)
- Telefone* (text — formato WhatsApp: +5511999999999)
- E-mail (email, opcional)
- Observações (textarea, opcional)
- Botões: [Cancelar] [Salvar]

**API:**
```
GET    /patients            → lista todos
POST   /patients            → { nome, telefone, email?, observacoes? }
GET    /patients/{id}
PATCH  /patients/{id}       → campos opcionais
DELETE /patients/{id}       → 204
```

---

### 4.4 Agenda

Vista principal: **calendário semanal** (coluna por dia, linhas por hora).

- Navegação ← semana → com data atual
- Botão "+ Agendar" (roxo)
- Cada appointment aparece como card colorido no slot do horário
  - Cor por status (ver badges acima)
  - Conteúdo: nome do paciente + horário
  - Click: abre painel lateral de detalhes

**Painel lateral de detalhes da consulta:**
- Nome paciente (link para ficha)
- Dentista
- Data e hora
- Duração
- Status com possibilidade de alterar
- Notas
- Botão "Cancelar consulta" (destrutivo, vermelho)

**Modal "Agendar Consulta":**
- Selecionar data (date picker)
- Selecionar paciente (dropdown searchable)
- Ver slots disponíveis (chips de horário vindos de `GET /scheduling/availability?date=YYYY-MM-DD`)
- Duração (padrão 30min)
- Dentista (opcional)
- Notas (opcional)
- Botão [Agendar]

**API:**
```
GET  /scheduling/availability?date=YYYY-MM-DD&dentist_id?&slot_min?
     → [{ starts_at, ends_at }, ...]   (slots livres 09–18h UTC, 30min)

GET  /scheduling/appointments?date?&dentist_id?
     → [{ id, patient_id, dentist_id?, starts_at, ends_at, status, notes? }]

POST /scheduling/appointments
     → { patient_id, starts_at, duration_min=30, dentist_id?, notes? }

PATCH /scheduling/appointments/{id}
     → { starts_at?, duration_min?, dentist_id?, status?, notes? }

POST  /scheduling/appointments/{id}/cancel  → marca status=cancelled

GET  /scheduling/stats?from=YYYY-MM-DD&to=YYYY-MM-DD
     → { total, by_status: {status: count}, per_day: {"YYYY-MM-DD": count} }
```

---

### 4.5 Conversas (Inbox WhatsApp IA)

**Tela estilo inbox de chat — layout 2 colunas:**

```
┌─────────────────────┬──────────────────────────────────────┐
│ LISTA DE CONVERSAS  │ THREAD DA CONVERSA SELECIONADA       │
│                     │                                      │
│ [busca]             │ [nome paciente / número]  [toggle IA]│
│                     │─────────────────────────────────────│
│ ● Ana Souza         │                                      │
│   "Quero agendar..."│  [balão] Ana: Oi, quero agendar...  │
│   há 5 min          │  [balão] IA: Olá! Para qual dia...  │
│                     │  [balão] Ana: Quinta-feira           │
│ ○ João Silva        │  [balão] IA: Temos 10h e 14h...     │
│   "Ok confirmado"   │                                      │
│   há 2h             │─────────────────────────────────────│
│                     │  [campo de texto]    [Enviar]        │
└─────────────────────┴──────────────────────────────────────┘
```

**Lista (lado esquerdo):**
- Avatar/inicial do paciente
- Nome ou número de telefone
- Preview da última mensagem (truncado)
- Tempo relativo ("há 5min", "ontem")
- Indicador se IA está ativa ou pausada

**Thread (lado direito):**
- Balões: mensagens do paciente (esquerda, cinza), IA/atendente (direita, roxo claro)
- Badge de remetente: "IA" ou "Clínica" (pequeno chip)
- Toggle "IA ativa / pausada" no header — quando desligado, o atendente responde manualmente
- Campo de texto + botão Enviar (só habilitado quando IA está pausada)

**API:**
```
GET   /conversations
      → [{ id, patient_id?, patient_nome?, external_number, channel,
           ai_enabled, last_message_at?, last_message_preview?, last_message_sender? }]

GET   /conversations/{id}/messages
      → [{ id, direction: "inbound"|"outbound", sender, text, created_at }]

POST  /conversations/{id}/messages
      → { text }   (resposta manual)

PATCH /conversations/{id}
      → { ai_enabled: bool }   (pausa/ativa IA)
```

---

### 4.6 Cobranças (Billing Pix)

**Lista de cobranças:**

| Descrição | Paciente | Valor | Status | Ações |
|---|---|---|---|---|
| Consulta 10/06 | Ana Souza | R$ 250,00 | Pago | [Ver QR] |
| Limpeza | João Silva | R$ 150,00 | Pendente | [Ver QR] [Atualizar] |

Status badge (billing):
- `pending` → amarelo/amber — "Pendente"
- `approved` → verde — "Pago"
- `rejected` → vermelho — "Recusado"
- `cancelled` → zinc — "Cancelado"

Botão "+ Nova Cobrança" (roxo, canto superior direito)

**Modal "Nova Cobrança":**
- Valor (R$) *
- Descrição (texto, opcional)
- Paciente (dropdown searchable, opcional)
- Vincular consulta (dropdown, opcional)
- Botão [Gerar Cobrança Pix]

**Modal "QR Code Pix":**
- QR code (imagem — campo `qr_code_base64` do backend)
- Código copia-e-cola (`qr_code`)
- Status atual + botão "Verificar pagamento" (chama `/refresh`)

**API:**
```
GET  /billing/charges
     → [{ id, valor, descricao?, metodo, status, charge_id,
          qr_code?, qr_code_base64?, patient_id?, appointment_id? }]

POST /billing/charges
     → { valor, descricao?, patient_id?, appointment_id? }

GET  /billing/charges/{id}

POST /billing/charges/{id}/refresh  → consulta status no gateway
```

---

## 5. Fluxos chave a ilustrar

### Fluxo 1 — Recepcionista agenda consulta
Login → Dashboard → Agenda → "+ Agendar" → seleciona paciente + data + slot → confirma → aparece no calendário

### Fluxo 2 — Paciente manda WhatsApp, IA agenda
(automático, sem interação no painel) → aparece nova conversa no Inbox → recepcionista vê thread → pode pausar IA e responder manualmente

### Fluxo 3 — Cobrança Pix
Cobranças → "+ Nova Cobrança" → preenche valor → QR gerado → copia código Pix → paciente paga → clica "Verificar" → status vira "Pago"

---

## 6. Dados de exemplo (para preencher o protótipo)

**Clínica:** Clínica Sorriso  
**Usuário logado:** Dra. Ana Lima (dono)

**Pacientes:**
- Ana Souza · (11) 98888-1111 · ana@email.com
- João Silva · (21) 97777-2222 · joao@email.com
- Maria Fernanda · (31) 96666-3333

**Consultas (semana atual):**
- Seg 09:00 — Ana Souza — `confirmed`
- Seg 14:00 — João Silva — `scheduled`
- Qua 10:00 — Maria Fernanda — `completed`
- Sex 11:00 — Ana Souza — `scheduled`

**Conversa WhatsApp:**
- Ana Souza: "Oi, quero agendar uma limpeza"
- IA: "Olá Ana! Para qual data você prefere?"
- Ana: "Quinta-feira de manhã"
- IA: "Temos horários às 09:00 e 10:30 na quinta. Qual prefere?"
- Ana: "09:00 por favor"
- IA: "Perfeito! Consulta marcada para quinta-feira às 09:00. Até lá! 😊"

**Cobranças:**
- R$ 250,00 — "Consulta inicial" — Ana Souza — `approved`
- R$ 150,00 — "Limpeza" — João Silva — `pending`

---

## 7. Notas técnicas para o protótipo

- **Datas/horas:** backend retorna UTC, exibir em UTC (ex: "09:00 UTC" ou só "09:00" mantendo UTC)
- **Sem modo escuro:** somente tema claro
- **Responsivo:** desktop-first, mas sidebar deve virar drawer em mobile
- **Acessibilidade:** contraste adequado (WCAG AA) com o roxo primário sobre branco
- **Estados de loading:** skeleton loaders nos cards e listas (não spinners centralizados)
- **Estados vazios:** ilustração/icon + texto amigável quando lista vazia (ex: "Nenhuma conversa ainda — as mensagens do WhatsApp aparecerão aqui")
- **Toasts:** feedback de ação (ex: "Consulta agendada com sucesso ✓") no canto inferior direito
