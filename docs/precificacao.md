# SaaS Odonto — Modelo de Precificação

> Planilha de trabalho para definir preço e margem. Companion do `features-e-valor.md`.
> Os números marcados com 🔧 são **premissas que você pode/deve ajustar** com os valores reais da sua conta.
> Câmbio usado: **US$ 1 = R$ 5,50** 🔧 · Valores em reais, arredondados.

⚠️ **Estimativas.** Preços de Gemini e WhatsApp/Meta mudam com o tempo. Use como ordem de grandeza e refine com faturas reais.

---

## 1. Premissas de custo (as "células de entrada")

### 1.1 Custo de IA por conversa (Gemini 2.5 Flash)

| Item | Valor 🔧 |
|---|---|
| Chamadas ao Gemini por conversa | 5 |
| Tokens de entrada por chamada | 2.500 |
| Tokens de saída por chamada | 200 |
| Preço entrada (US$/milhão de tokens) | 0,30 |
| Preço saída (US$/milhão de tokens) | 2,50 |
| **→ Custo de IA por conversa** | **≈ R$ 0,03** |

Cálculo: entrada `5×2.500=12.500 tok × US$0,30/1M = US$0,00375` + saída `5×200=1.000 tok × US$2,50/1M = US$0,0025` = `US$0,006 ≈ R$0,03`.

### 1.2 Custo de WhatsApp (Meta)

| Item | Valor 🔧 |
|---|---|
| Conversa iniciada pelo paciente (janela 24h) | **R$ 0,00** (grátis) |
| Lembrete proativo — template "utility" (BR) | R$ 0,07 |
| Lembretes por consulta agendada | **1** |

### 1.3 Custo variável total por atendimento

| Componente | Custo |
|---|---|
| IA (Gemini) | R$ 0,03 |
| WhatsApp — conversa do paciente | R$ 0,00 |
| WhatsApp — 1 lembrete | R$ 0,07 |
| **Custo variável por atendimento** | **≈ R$ 0,10** |
| Margem de segurança (arredondar p/ cima) | **R$ 0,30** 🔧 |

> Vamos usar **R$ 0,30/atendimento** nos cálculos abaixo (folga proposital, cobre picos de conversa mais longa e variação de câmbio).

### 1.4 Custos fixos (independem do uso)

| Item | Custo/mês 🔧 | Observação |
|---|---|---|
| Banco de dados (Neon) | R$ 0 – 120 | Grátis no início; escala com nº de clínicas |
| Hospedagem (API + painel) | R$ 0 – 100 | Vercel/Railway; tiers gratuitos no começo |
| **Total infra (fase inicial)** | **≈ R$ 100/mês** | Rateado entre as clínicas ativas |
| Infra alocada **por clínica** 🔧 | **R$ 30/mês** | Assumindo poucas clínicas; cai com escala |

### 1.5 Pix (Mercado Pago) — custo transacional

| Item | Valor 🔧 |
|---|---|
| Taxa Pix Mercado Pago | ~0,99% por transação |
| **Decisão de modelo** | **Repassar** ao dentista (não embutir) ✅ recomendado |

> Recomendação: **não embutir** o Pix no preço. Repasse a taxa (ou deixe o gateway do próprio dentista). Assim o Pix não vira custo variável seu e o preço fica limpo.

---

## 2. Volume esperado por clínica

Clínica-alvo: 2–5 dentistas.

| Cenário 🔧 | Atendimentos de IA/mês | Consultas agendadas/mês |
|---|---|---|
| Baixo | 150 | ~120 |
| **Médio (base)** | **300** | **~240** |
| Alto | 600 | ~480 |

> "Atendimento de IA" = conversa no WhatsApp (agendou ou não). "Consulta agendada" = gera 1 lembrete.

---

## 3. Custo total por clínica/mês (cenário médio = 300 atendimentos)

| Componente | Cálculo | Custo/mês |
|---|---|---|
| Variável (IA + lembretes) | 300 × R$ 0,30 | R$ 90 |
| Infra fixa alocada | — | R$ 30 |
| **Custo total por clínica** | | **≈ R$ 120/mês** |

---

## 4. Planos e margem

Três planos. O grande divisor de valor é **IA ligada ou desligada**.

| | **Básico** | **Pro** ⭐ | **Premium** |
|---|---|---|---|
| **Preço/mês** 🔧 | R$ 99 | R$ 299 | R$ 499 |
| Agenda, Pacientes, Painel | ✅ | ✅ | ✅ |
| Cobrança Pix (taxa repassada) | ✅ | ✅ | ✅ |
| Agente de IA no WhatsApp | ❌ | ✅ | ✅ |
| Limite de atendimentos IA/mês | — | 300 | 800 |
| Usuários (assentos) | 2 | 5 | ilimitado |
| Inbox / handoff humano ↔ IA | ❌ | ✅ | ✅ |
| Dashboard / relatórios | básico | ✅ | avançado |
| Integrações (BYOK) | ❌ | ✅ | ✅ |

### Margem por plano

| Plano | Preço | Custo estimado | **Margem R$** | **Margem %** |
|---|---|---|---|---|
| Básico | R$ 99 | R$ 30 (só infra) | **R$ 69** | **70%** |
| **Pro** | R$ 299 | R$ 120 (300 atend.) | **R$ 179** | **60%** |
| Premium | R$ 499 | R$ 270 (800 atend.) | **R$ 229** | **46%** |

Custo Premium: `800 × R$0,30 = R$240` + `R$30` infra = `R$270`.

### Excedente de IA (proteção de margem)

Como o único custo que escala é o atendimento de IA, cobre o excedente acima do limite do plano:

| Item | Valor 🔧 |
|---|---|
| Custo real por atendimento extra | R$ 0,30 |
| **Preço cobrado por atendimento extra** | **R$ 1,50** (5× o custo) |

> Isso protege a margem se uma clínica usar muito mais que o previsto, sem precisar mudar o plano dela.

---

## 5. Leitura estratégica

- **Seu custo variável é minúsculo** (~R$ 0,30/atendimento). O preço **não** é limitado pelo custo — é limitado pelo **valor percebido**.
- **Âncora de valor:** o agente de IA substitui parte do trabalho de uma secretária (R$ 1.500–2.500/mês). Cobrar R$ 299/mês por isso é uma pechincha para o dentista **e** margem alta pra você.
- **O divisor de plano que mais importa é a IA** (Básico sem IA × Pro com IA). É onde está o salto de disposição a pagar.
- **Sensibilidade — modelo de IA:** trocar Gemini por um modelo premium (Claude/GPT) pode subir o custo de IA 10–30× (de ~R$0,03 para ~R$0,30–1,00 por conversa). Ainda cabe na margem, mas recalcular a linha 1.1 se mudar.
- **Pix:** repassado, não é custo seu. Mantém o preço limpo.

---

## 6. O que ajustar antes de fechar (checklist)

- [ ] Confirmar preço real do **Gemini** na sua conta (linha 1.1)
- [ ] Confirmar preço do **template de lembrete** no painel da Meta/BSP (linha 1.2)
- [ ] Medir **atendimentos/mês reais** de uma clínica piloto (seção 2)
- [ ] Validar disposição a pagar com **2–3 dentistas reais** (os preços da seção 4 são hipótese)
- [ ] Decidir os **limites de atendimento** de cada plano com base no uso real

---

*Companion de `docs/features-e-valor.md`. Números são estimativas de trabalho, não faturas reais.*
