# Conectar o WhatsApp (Meta Cloud API) + ngrok — passo a passo

Guia para plugar o agente de IA num WhatsApp **de graça**, usando o **número de
teste** da Meta (modo dev: envia para até 5 números verificados). Tempo: ~15 min.

O backend já está pronto: endpoints `GET/POST /ai/whatsapp/webhook` e
`POST /ai/whatsapp/numbers`. Falta o setup externo + ligar `CHANNEL_PROVIDER=meta`.

---

## Parte 0 — Pré-requisitos
- Conta no **Facebook** (pessoal serve).
- Backend rodável localmente (Parte 4).
- Chave do **Gemini** já no `.env` (`LLM_PROVIDER=gemini`) — o agente responde de verdade.

---

## Parte 1 — Criar o app na Meta (grátis)
1. Acesse **https://developers.facebook.com** e faça login.
2. **My Apps** → **Create App**.
3. Use cases: **Other** → **Next**.
4. Tipo: **Business** → **Next**.
5. Nome (ex.: `SaaS Odonto Dev`), e-mail → **Create app**.

## Parte 2 — Adicionar o produto WhatsApp
1. No painel do app → card **WhatsApp** → **Set up**.
2. Selecione/crie um **Meta Business Account** → **Continue**.
3. Você cai em **WhatsApp → API Setup** (ou "Quickstart").

## Parte 3 — Pegar número de teste, token e IDs
Na tela **API Setup**, anote:
1. **Temporary access token** (topo). ⚠️ Expira em **24h**. → vira `WHATSAPP_TOKEN`.
2. **Phone number ID** (na seção "From") — um número longo, **não** é o telefone.
   → vira `WHATSAPP_PHONE_NUMBER_ID`.
3. Em **"To" → Manage phone number list**, adicione **seu número pessoal**; confirme
   o código que chega no seu WhatsApp. (Dev só envia para até 5 números verificados.)

## Parte 4 — Subir o backend
A partir de `backend/`:
```powershell
uv run --env-file ..\.env uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Teste: http://localhost:8000/health → `ok`. Deixe rodando.

## Parte 5 — Expor com ngrok (a Meta exige HTTPS público)
1. Instale: https://ngrok.com/download (crie conta grátis;
   `ngrok config add-authtoken <SEU_TOKEN_NGROK>` uma vez).
2. Em outro terminal: `ngrok http 8000`
3. Copie a URL **https** (ex.: `https://a1b2-c3d4.ngrok-free.app`). Deixe rodando.
   ⚠️ No plano grátis a URL muda a cada reinício — aí refaça a Parte 7.

## Parte 6 — Configurar o `.env` e reiniciar
No `.env` (raiz):
```
CHANNEL_PROVIDER=meta
WHATSAPP_TOKEN=<temporary access token>
WHATSAPP_PHONE_NUMBER_ID=<phone number id>
WHATSAPP_VERIFY_TOKEN=uma-string-secreta-que-voce-inventa
WHATSAPP_API_VERSION=v21.0
```
O `WHATSAPP_VERIFY_TOKEN` é uma senha **que você inventa** (precisa ser idêntica na
Meta no próximo passo). **Reinicie o uvicorn** para reler o `.env`.

## Parte 7 — Cadastrar o webhook na Meta
1. Painel do app → **WhatsApp → Configuration**.
2. Seção **Webhook** → **Edit**.
3. Preencha:
   - **Callback URL:** `https://SEU-NGROK.ngrok-free.app/ai/whatsapp/webhook`
   - **Verify token:** o mesmo de `WHATSAPP_VERIFY_TOKEN`.
4. **Verify and Save** — a Meta faz um GET; nosso endpoint ecoa o challenge se o
   token bater (uvicorn + ngrok precisam estar no ar).
5. Em **Webhook fields** → **Manage** → assine o campo **messages**.

## Parte 8 — Ligar o número à clínica (uma vez)
1. Login (pega o token):
   ```bash
   curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
     -d '{"email":"owner@sorriso.com","password":"senha123"}'
   ```
2. Registrar o número (mesmo `phone_number_id` da Parte 3):
   ```bash
   curl -X POST http://localhost:8000/ai/whatsapp/numbers \
     -H "Authorization: Bearer <ACCESS_TOKEN>" -H "Content-Type: application/json" \
     -d '{"phone_number_id":"<WHATSAPP_PHONE_NUMBER_ID>","label":"Numero de teste"}'
   ```
   `201` = número ligado à Clínica Sorriso (grava em `whatsapp_numbers`).

## Parte 9 — Testar 🎉
Do **seu WhatsApp pessoal** (verificado na Parte 3), mande para o **número de teste**:
> "oi, quais horários vocês têm livres dia 2099-01-05?"

O agente (Gemini) responde com os horários. Depois:
> "pode agendar dia 2099-01-05 às 09:00"

E ele marca a consulta. Os logs do webhook aparecem no terminal do uvicorn.

---

## Problemas comuns
- **Token expira em 24h:** regenere na tela API Setup, ou crie um **token permanente**
  (Business Settings → System Users → token com `whatsapp_business_messaging` +
  `whatsapp_business_management`). Atualize o `.env` e reinicie.
- **"Verify and Save" falha:** uvicorn/ngrok fora do ar, URL do ngrok desatualizada,
  ou verify token diferente.
- **Mensagem não chega ao agente:** confirme a assinatura do campo **messages**
  (7.5) e que o `phone_number_id` registrado (8) é o mesmo do `.env`/número de teste.
- **Agente não responde:** `WHATSAPP_TOKEN` inválido/expirado — o uvicorn loga
  `Falha ao enviar WhatsApp`.
- **URL do ngrok mudou:** refaça a Parte 7 com a nova URL.

---

## Produção (futuro, fora do dev grátis)
Verificar o negócio no Business Manager, usar um **número próprio** (não o de teste),
trocar para token permanente, e habilitar a verificação de assinatura
`X-Hub-Signature-256`. A partir daí a Meta cobra **por conversa** (com cota mensal
grátis). Veja os preços do WhatsApp Business Platform.
