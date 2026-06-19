import { Settings } from "lucide-react";

export function ConfigPage() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-[18px] bg-secondary">
        <Settings className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="mb-1 text-[17px] font-bold text-muted-foreground">Configurações</h3>
      <p className="text-sm text-muted-foreground">
        Preferências da clínica, horários e integrações. Em breve.
      </p>
    </div>
  );
}
