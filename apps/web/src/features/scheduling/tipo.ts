// Cor/label do tipo de consulta — compartilhado entre a grade da agenda,
// o diálogo de agendamento e o painel de detalhes.
export const TIPO_INFO: Record<string, { label: string; color: string }> = {
  avaliacao:   { label: "Avaliação",   color: "#7C3AED" },
  limpeza:     { label: "Limpeza",     color: "#0D9488" },
  restauracao: { label: "Restauração", color: "#2563EB" },
  canal:       { label: "Canal",       color: "#DC2626" },
  clareamento: { label: "Clareamento", color: "#D97706" },
  cirurgia:    { label: "Cirurgia",    color: "#DB2777" },
};

export const TIPO_OPTIONS = Object.entries(TIPO_INFO).map(([value, info]) => ({
  value,
  label: info.label,
}));
