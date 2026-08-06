# SaaS Odonto — Features & Balanceamento de Valor

> Documento-base para o funil de vendas e a modelagem financeira (precificação e modelos de cobrança).
> Objetivo: listar **tudo que o produto faz hoje**, organizado por blocos de valor, para servir de
> insumo à discussão de preço. Não é material de marketing — é o inventário real da capacidade entregue.

**O que é:** SaaS B2B **multi-tenant** para clínicas odontológicas pequenas (2–5 dentistas).
**Diferencial central:** atendimento por **IA no WhatsApp** que agenda sozinha, integrado à gestão da clínica.
**Isolamento entre clínicas:** garantido pelo banco (Row-Level Security do PostgreSQL) — cada clínica só enxerga os próprios dados.

---

## Índice de blocos de valor

1. Agente de IA no WhatsApp (o "vendedor")
2. Agenda inteligente
3. Gestão de pacientes (CRM/prontuário)
4. Cobrança e recebimento (Pix)
5. Inbox / Conversas (atendimento humano + IA)
6. Multiusuário e controle de acesso (equipe)
7. Configurações da clínica
8. Central de integrações (autoatendimento)
9. Dashboard e indicadores
10. Fundação técnica (o que sustenta o preço premium)

---

## 1. Agente de IA no WhatsApp — o coração do produto

O paciente conversa por WhatsApp em linguagem natural e o agente **resolve sozinho**, sem humano no meio.

| Capacidade | O que faz | Valor para a clínica |
|---|---|---|
| Atendimento 24/7 | Responde a qualquer hora, inclusive fora do expediente | Não perde lead / paciente à noite e fim de semana |
| Identificação do paciente | Reconhece pelo telefone; **cria o cadastro** se for novo | Zero trabalho manual de cadastro |
| Consulta de horários (`buscar_horarios`) | Lê a agenda **real** e informa os horários livres | Nunca oferece horário ocupado |
| Agendamento autônomo (`agendar`) | Marca a consulta direto na agenda, com checagem de conflito | Secretária deixa de fazer marcação por chat |
| Escopo por clínica | Toda ação da IA é isolada por tenant (RLS) | Segurança: IA de uma clínica não toca dados de outra |
| LLM plugável | Roda com **Google Gemini** (real) ou modo mock offline | Custo de IA controlável / trocável |

**Gancho de precificação:** este é o item de maior disposição a pagar. Substitui parte do trabalho de uma
secretária e captura agendamentos fora do horário comercial. Candidato natural a *feature de plano superior*
ou a **cobrança por volume** (nº de conversas/atendimentos de IA por mês).

---

## 2. Agenda inteligente

| Capacidade | Detalhe |
|---|---|
| Horários livres por dia | Calcula slots disponíveis respeitando horário de funcionamento e almoço |
| Agendar com checagem de conflito | Impede overbooking no mesmo horário/dentista |
| Reagendar / mudar status | Confirmar, remarcar, no-show etc. |
| Cancelar consulta | Fluxo dedicado |
| Tipos de procedimento | Avaliação, limpeza, restauração, canal, clareamento, cirurgia |
| Duração configurável | De 5 a 480 min por consulta |
| Vínculo com dentista | Consulta atribuída a um profissional específico |
| Horário de funcionamento por dia | Abertura, fechamento e janela de almoço por dia da semana |
| Fuso horário por clínica | Padrão America/Sao_Paulo, ajustável (IANA) |
| Calendário no painel | Tela de agenda visual (livres → agendar/cancelar) |
| Sync com Google Calendar | Integração plugável (adapter pronto) |

**Gancho de precificação:** base do produto. Candidato a **limite por nº de dentistas/cadeiras** ou
por **volume de agendamentos**.

---

## 3. Gestão de pacientes (CRM / prontuário)

| Capacidade | Detalhe |
|---|---|
| CRUD de pacientes | Nome, telefone, e-mail, observações |
| Escopo por clínica | Isolamento por RLS |
| Prontuário / ficha (`/record`) | Histórico consolidado do paciente: **consultas + cobranças** numa tela |
| Criação automática pela IA | Paciente novo que chama no WhatsApp já entra na base |

**Gancho de precificação:** candidato a **limite por nº de pacientes ativos** na base (típico de CRM).

---

## 4. Cobrança e recebimento (Pix)

| Capacidade | Detalhe |
|---|---|
| Emitir cobrança Pix | Valor, descrição, vínculo a paciente e/ou consulta |
| QR Code | Copia-e-cola + imagem base64 |
| Consultar status | Atualiza pagamento junto ao gateway |
| Confirmação por webhook | Baixa automática quando o pagamento cai |
| Gateway real | **Mercado Pago** (com verificação de assinatura do webhook) ou mock |
| Listar / excluir cobranças | Gestão financeira básica |

**Gancho de precificação:** aqui cabe o modelo **transacional** — % ou taxa fixa por Pix processado —
como alternativa (ou adicional) à mensalidade.

---

## 5. Inbox / Conversas — atendimento humano + IA no mesmo lugar

| Capacidade | Detalhe |
|---|---|
| Lista de conversas | Inbox com prévia da última mensagem, canal e status de não-lida |
| Histórico de mensagens | Thread completa por conversa |
| Envio manual | A secretária responde pelo painel |
| Toggle de IA por conversa (`ai_enabled`) | **Assumir/devolver** o atendimento para a IA a qualquer momento |
| Vínculo ao paciente | Conversa amarrada ao cadastro |

**Gancho de precificação:** o "handoff humano ↔ IA" é diferencial forte. Reforça o valor do plano com IA.

---

## 6. Multiusuário e controle de acesso (equipe)

| Capacidade | Detalhe |
|---|---|
| Papéis (RBAC) | **Owner**, **Dentist**, **Secretary** |
| Gestão de usuários | Criar, editar, ativar/desativar membros da equipe |
| Reset de senha | Pelo owner |
| Seletor de dentistas | Lista enxuta para atribuir consultas |
| Login JWT + refresh + logout | Sessão segura com refresh token |

**Gancho de precificação:** candidato a **limite por nº de usuários/assentos** (seat-based).

---

## 7. Configurações da clínica

| Capacidade | Detalhe |
|---|---|
| Dados cadastrais | CNPJ, razão social, endereço, telefone, logo |
| Horários de funcionamento | Por dia da semana, com almoço |
| Fuso horário | IANA por clínica |
| Preferências | Ex.: toggle de lembretes de consulta |
| Edição da própria clínica | Escopada ao tenant |

---

## 8. Central de integrações (autoatendimento)

O próprio dono conecta os provedores pelo painel, sem depender de suporte técnico. Segredos são **cifrados**
e nunca devolvidos em claro (só dica mascarada tipo `••••1234`).

| Integração | Para quê |
|---|---|
| WhatsApp (Meta) | Canal do agente de IA |
| Mercado Pago | Pix real |
| Google Calendar | Sync de agenda |
| Assistente de IA (Gemini) | Provedor do LLM |

**Gancho de precificação:** BYOK (traga sua própria chave) reduz seu custo de IA/gateway e pode virar
diferencial entre planos ("use nossa infra" vs. "conecte a sua").

---

## 9. Dashboard e indicadores

| Capacidade | Detalhe |
|---|---|
| Resumo da agenda | Total de consultas num intervalo |
| Por status | Distribuição (confirmadas, canceladas, no-show…) |
| Por dia | Série diária — alimenta gráfico semanal |

**Gancho de precificação:** relatórios/analytics avançados são um clássico *upsell* de plano superior.

---

## 10. Fundação técnica (o que justifica preço premium)

Não são features de tela, mas sustentam confiança e o preço.

- **Multi-tenancy com Row-Level Security:** isolamento garantido **pelo banco**, não só pela aplicação — o `clinic_id` vem de dentro do JWT, nunca do cliente.
- **Arquitetura de adapters plugáveis (mock-first):** LLM, WhatsApp, Pix e Calendar trocáveis sem mexer na regra de negócio → evolução rápida e sem lock-in.
- **Segurança:** JWT próprio, RBAC, funções `SECURITY DEFINER` para operações sem contexto (login, webhook de pagamento), verificação de assinatura de webhook.
- **Stack moderna:** FastAPI + SQLAlchemy async + PostgreSQL (Neon) · React/Vite/TypeScript.
- **Testado:** testes de integração que **provam o isolamento por RLS** ponta a ponta.
- **Pronto para deploy:** Docker Compose e Railway.

---

## Matriz de features × modelo de cobrança (insumo para o balanceamento)

| Feature | Mensalidade fixa | Por assento (usuário) | Por volume (uso) | Transacional (%) |
|---|:--:|:--:|:--:|:--:|
| Agente de IA no WhatsApp | ✅ (plano) | — | ✅ (nº de atendimentos) | — |
| Agenda / agendamento | ✅ | — | possível (nº consultas) | — |
| Pacientes (CRM) | ✅ | — | possível (nº pacientes) | — |
| Cobrança Pix | ✅ | — | — | ✅ (por transação) |
| Inbox / Conversas | ✅ | ✅ | — | — |
| Usuários / equipe | — | ✅ | — | — |
| Dashboard / relatórios | upsell | — | — | — |
| Integrações (BYOK) | diferencial de plano | — | — | — |

> Legenda: ✅ = encaixe natural · "possível" = dá para modelar como limite · "upsell" = candidato a plano superior.

---

## Sugestão de eixos para desenhar os planos

Para o balanceamento de valor, os limites mais naturais de "cortar" entre planos são:

1. **Nº de dentistas / cadeiras** (tamanho da clínica).
2. **Nº de usuários** (assentos da equipe).
3. **Volume de atendimentos de IA / mês** (o custo variável real do produto).
4. **IA ligada ou desligada** (plano básico sem IA vs. plano com IA — o grande divisor de valor).
5. **Pix:** incluso na mensalidade vs. taxa transacional à parte.
6. **Relatórios/integrações avançadas** como gatilho de plano superior.

**Recomendação de leitura financeira:** o item 3 (volume de IA) é o único custo que **escala com o uso** —
todo o resto é custo fixo de infra. Qualquer modelo de preço deveria proteger a margem justamente aí,
seja por limite de atendimentos por plano, seja por cobrança de excedente.

---

*Gerado a partir do código real do repositório (backend FastAPI + painel React). Reflete o estado atual da implementação, não um roadmap.*
