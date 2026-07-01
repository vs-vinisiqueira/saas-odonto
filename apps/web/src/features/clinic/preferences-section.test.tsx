import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { api } from "@/lib/api";
import { PreferencesSection } from "./preferences-section";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), patch: vi.fn() },
  errorMessage: () => "erro",
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("PreferencesSection", () => {
  it("carrega o estado do lembrete e salva ao alternar", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { id: "c1", nome: "Clínica X", config: { preferences: { reminders_enabled: false } } },
    });
    vi.mocked(api.patch).mockResolvedValue({
      data: { id: "c1", nome: "Clínica X", config: { preferences: { reminders_enabled: true } } },
    });

    renderWithClient(<PreferencesSection />);

    await waitFor(() => expect(screen.getByText("Lembretes de consulta")).toBeInTheDocument());

    const toggle = screen.getByRole("button");
    await userEvent.click(toggle);

    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith("/clinics/me", {
        config: { preferences: { reminders_enabled: true } },
      }),
    );
  });
});
