# Conectar o Pix (Mercado Pago, sandbox) — passo a passo

Guia para emitir cobranças **Pix reais em sandbox** (grátis). Diferente do
WhatsApp, dá para testar **sem ngrok**: o endpoint
`POST /billing/charges/{id}/refresh` consulta o status direto na API do Mercado
Pago. O webhook (opcional) só é necessário para atualização em tempo real.

O backend já está pronto: gateway `MercadoPagoGateway`, seleção por
`BILLING_PROVIDER=mercadopago`, e webhook em `POST /billing/mercadopago/webhook`.

---

## Parte 1 — Conta + aplicação
1. Crie/entre numa conta em **https://www.mercadopago.com.br**.
2. Vá ao **painel de desenvolvedores**:
   https://www.mercadopago.com.br/developers/panel/app
3. **Criar aplicação** → produto **Pagamentos online (Checkout API)** → marque
   **Pix** entre os meios de pagamento.

## Parte 2 — Credenciais de TESTE
1. Na aplicação → **Credenciais de teste**.
2. Copie o **Access Token** (começa com `TEST-...`). → vira `MERCADOPAGO_ACCESS_TOKEN`.
3. (Opcional, recomendado) Em **Contas de teste**, crie um **usuário de teste
   comprador** e use o e-mail dele em `MERCADOPAGO_PAYER_EMAIL`.

## Parte 3 — `.env` e reiniciar
No `.env` (raiz):
```
BILLING_PROVIDER=mercadopago
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxxxxx
MERCADOPAGO_PAYER_EMAIL=test_user_123@testuser.com
```
Reinicie o uvicorn para reler o `.env`.

## Parte 4 — Criar uma cobrança Pix
1. Login:
   ```bash
   curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
     -d '{"email":"owner@sorriso.com","password":"senha123"}'
   ```
2. Criar a cobrança:
   ```bash
   curl -X POST http://localhost:8000/billing/charges \
     -H "Authorization: Bearer <ACCESS_TOKEN>" -H "Content-Type: application/json" \
     -d '{"valor":"150.00","descricao":"Limpeza"}'
   ```
   A resposta traz `charge_id` (id do pagamento no MP), `qr_code` (Pix
   **copia-e-cola**) e `qr_code_base64` (imagem do QR). No painel/app você verá a
   cobrança como **pendente**.

## Parte 5 — Conferir o status (sem ngrok)
```bash
curl -X POST http://localhost:8000/billing/charges/<PAYMENT_ID>/refresh \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
Isso consulta a API do MP e atualiza o `status` (`pending` → `paid` quando o
pagamento for aprovado). No painel é possível acompanhar/simular o pagamento de
teste.

## Parte 6 (opcional) — Webhook em tempo real
Para o status atualizar sozinho (sem chamar o refresh):
1. Exponha a API com `ngrok http 8000` (igual ao guia do WhatsApp).
2. Na aplicação do MP → **Webhooks / Notificações** → URL:
   `https://SEU-NGROK/billing/mercadopago/webhook`, evento **Pagamentos**.
3. O MP passa a mandar o id do pagamento; o backend consulta o status e atualiza.

---

## Observações
- **Sandbox:** o Mercado Pago só cobra um percentual por transação em produção
  (com credenciais de produção). No sandbox é tudo grátis e fictício.
- **Aprovação do Pix em teste:** dependendo da conta, o pagamento de teste pode
  ficar `pending` até você simular a aprovação pelas contas de teste. A integração
  validada aqui é: criar cobrança → QR → consultar/atualizar status (refresh ou
  webhook).
- Sem `MERCADOPAGO_ACCESS_TOKEN` (ou `BILLING_PROVIDER=mock`), tudo segue no
  gateway mock — útil para dev/testes offline.
