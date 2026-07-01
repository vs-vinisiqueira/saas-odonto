import { Bell, Building2, Clock, Plug, Users } from "lucide-react";
import { useState } from "react";

import { useAuthStore } from "@/lib/auth-store";
import { ClinicSection } from "@/features/clinic/clinic-section";
import { HoursSection } from "@/features/clinic/hours-section";
import { PreferencesSection } from "@/features/clinic/preferences-section";
import { IntegrationsSection } from "@/features/integrations/integrations-section";
import { UsersSection } from "@/features/users/users-section";

type SectionId = "users" | "clinic" | "hours" | "integrations" | "preferences";

const SECTIONS: { id: SectionId; label: string; icon: typeof Users; ready: boolean }[] = [
  { id: "users", label: "Usuários", icon: Users, ready: true },
  { id: "clinic", label: "Dados da clínica", icon: Building2, ready: true },
  { id: "hours", label: "Horários", icon: Clock, ready: true },
  { id: "integrations", label: "Integrações", icon: Plug, ready: true },
  { id: "preferences", label: "Preferências", icon: Bell, ready: true },
];

export function ConfigPage() {
  const [active, setActive] = useState<SectionId>("users");
  const role = useAuthStore((s) => s.user?.role);
  const isOwner = role === "owner";

  return (
    <div className="mx-auto flex max-w-[1180px] flex-col gap-5 pb-12">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight text-foreground">Configurações</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Gerencie a equipe e as preferências da sua clínica.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-[220px_1fr] md:gap-6">
        {/* Navegação de seções — empilha no mobile, vira coluna lateral no desktop */}
        <nav className="flex gap-1 overflow-x-auto pb-1 md:flex-col md:overflow-visible md:pb-0">
          {SECTIONS.map((s) => {
            const Icon = s.icon;
            const isActive = active === s.id;
            return (
              <button
                key={s.id}
                onClick={() => setActive(s.id)}
                className={[
                  "flex shrink-0 items-center justify-between gap-2 whitespace-nowrap rounded-[11px] px-3.5 py-2.5 text-left text-sm font-semibold transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                ].join(" ")}
              >
                <span className="flex items-center gap-2.5">
                  <Icon className="h-[18px] w-[18px]" />
                  {s.label}
                </span>
                {!s.ready && (
                  <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    em breve
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Conteúdo da seção */}
        <div>
          {active === "users" &&
            (isOwner ? (
              <UsersSection />
            ) : (
              <Placeholder
                icon={Users}
                title="Apenas administradores"
                text="A gestão de usuários é restrita a administradores da clínica."
              />
            ))}

          {active === "integrations" &&
            (isOwner ? (
              <IntegrationsSection />
            ) : (
              <Placeholder
                icon={Plug}
                title="Apenas administradores"
                text="As integrações da clínica são configuradas por administradores."
              />
            ))}

          {active === "clinic" &&
            (isOwner ? (
              <ClinicSection />
            ) : (
              <Placeholder
                icon={Building2}
                title="Apenas administradores"
                text="Os dados da clínica são configurados por administradores."
              />
            ))}

          {active === "hours" &&
            (isOwner ? (
              <HoursSection />
            ) : (
              <Placeholder
                icon={Clock}
                title="Apenas administradores"
                text="Os horários de funcionamento são configurados por administradores."
              />
            ))}

          {active === "preferences" &&
            (isOwner ? (
              <PreferencesSection />
            ) : (
              <Placeholder
                icon={Bell}
                title="Apenas administradores"
                text="As preferências da clínica são configuradas por administradores."
              />
            ))}
        </div>
      </div>
    </div>
  );
}

function Placeholder({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Users;
  title: string;
  text: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[18px] border bg-card py-20 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-[18px] bg-secondary">
        <Icon className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="mb-1 text-[17px] font-bold text-muted-foreground">{title}</h3>
      <p className="max-w-xs text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
