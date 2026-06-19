import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import { queryClient } from "@/lib/query";
import { AppRouter } from "@/routes";
// Inicializa o tema (aplica a classe `dark` no <html>) antes de pintar a UI.
import "@/lib/theme-store";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppRouter />
    </QueryClientProvider>
  </React.StrictMode>,
);
