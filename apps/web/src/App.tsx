import { useState } from "react";
import { getMyClinic, login } from "./api";

// Placeholder de painel: login + leitura da própria clínica. A UI completa
// (agenda, pacientes, financeiro) entra na fase do painel.
export function App() {
  const [email, setEmail] = useState("owner@sorriso.com");
  const [password, setPassword] = useState("senha123");
  const [clinic, setClinic] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const tokens = await login(email, password);
      const data = await getMyClinic(tokens.access_token);
      setClinic(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    }
  }

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 420, margin: "4rem auto" }}>
      <h1>🦷 SaaS Odonto</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 8 }}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="E-mail" />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Senha"
        />
        <button type="submit">Entrar</button>
      </form>

      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {clinic && (
        <section style={{ marginTop: 16 }}>
          <h2>Minha clínica</h2>
          <pre>{JSON.stringify(clinic, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
