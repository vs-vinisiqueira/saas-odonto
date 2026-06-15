import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { LoginPage } from "./login-page";
import { loginSchema } from "./schemas";

describe("LoginPage", () => {
  it("renderiza o formulário de login", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("SaaS Odonto")).toBeInTheDocument();
    expect(screen.getByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.getByLabelText("Senha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /entrar/i })).toBeInTheDocument();
  });
});

describe("loginSchema", () => {
  it("rejeita e-mail inválido e senha vazia", () => {
    expect(loginSchema.safeParse({ email: "nao-e-email", password: "x" }).success).toBe(
      false,
    );
    expect(
      loginSchema.safeParse({ email: "a@b.com", password: "" }).success,
    ).toBe(false);
  });

  it("aceita credenciais bem formadas", () => {
    expect(
      loginSchema.safeParse({ email: "owner@sorriso.com", password: "senha123" }).success,
    ).toBe(true);
  });
});
