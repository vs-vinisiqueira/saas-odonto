import { ArrowLeft, CalendarDays, CreditCard, Mail, Phone } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { Spinner } from "@/components/ui/spinner";
import { formatDateLabel, formatTimeUTC } from "@/lib/datetime";
import { usePatientRecord } from "./api";

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const APPT_STATUS: Record<string, { label: string; bg: string; color: string }> = {
  scheduled: { label: "Agendada", bg: "#F4F4F5", color: "#52525B" },
  confirmed: { label: "Confirmada", bg: "#EFF6FF", color: "#1D4ED8" },
  completed: { label: "Concluída", bg: "#F0FDF4", color: "#15803D" },
  cancelled: { label: "Cancelada", bg: "#FEF2F2", color: "#B91C1C" },
  no_show: { label: "Faltou", bg: "#FFF7ED", color: "#C2410C" },
};

const CHARGE_STATUS: Record<string, { label: string; bg: string; color: string }> = {
  pending: { label: "Pendente", bg: "#FFFBEB", color: "#B45309" },
  paid: { label: "Pago", bg: "#F0FDF4", color: "#15803D" },
  approved: { label: "Pago", bg: "#F0FDF4", color: "#15803D" },
  expired: { label: "Expirado", bg: "#F4F4F5", color: "#52525B" },
  canceled: { label: "Cancelado", bg: "#FEF2F2", color: "#B91C1C" },
  rejected: { label: "Recusado", bg: "#FEF2F2", color: "#B91C1C" },
};

function Pill({ info }: { info: { label: string; bg: string; color: string } }) {
  return (
    <span
      className="inline-flex w-fit items-center rounded-full px-2.5 py-1 text-[11px] font-extrabold uppercase tracking-[.04em]"
      style={{ background: info.bg, color: info.color }}
    >
      {info.label}
    </span>
  );
}

export function PatientRecordPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = usePatientRecord(id);

  if (isLoading) {
    return (
      <div className="flex justify-center p-16">
        <Spinner className="text-primary" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-[980px]">
        <BackButton onClick={() => navigate("/pacientes")} />
        <p className="mt-6 text-sm text-destructive">
          Não foi possível carregar o prontuário deste paciente.
        </p>
      </div>
    );
  }

  const { patient, appointments, charges } = data;

  return (
    <div className="mx-auto flex max-w-[980px] flex-col gap-5 pb-12">
      <BackButton onClick={() => navigate("/pacientes")} />

      {/* Cabeçalho do paciente */}
      <div className="animate-fade-up rounded-[18px] border bg-card p-6 shadow-[0_1px_2px_rgba(16,24,40,.04)]">
        <h2 className="text-2xl font-extrabold tracking-tight text-foreground">
          {patient.nome}
        </h2>
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <Phone className="h-4 w-4" />
            {patient.telefone}
          </span>
          {patient.email && (
            <span className="inline-flex items-center gap-1.5">
              <Mail className="h-4 w-4" />
              {patient.email}
            </span>
          )}
        </div>
        {patient.observacoes && (
          <p className="mt-4 rounded-lg bg-secondary px-3.5 py-2.5 text-sm text-foreground">
            {patient.observacoes}
          </p>
        )}
      </div>

      {/* Consultas */}
      <Section
        icon={<CalendarDays className="h-[18px] w-[18px]" />}
        title="Consultas"
        count={appointments.length}
      >
        {appointments.length === 0 ? (
          <Empty>Nenhuma consulta registrada.</Empty>
        ) : (
          appointments.map((a) => {
            const st = APPT_STATUS[a.status] ?? APPT_STATUS.scheduled;
            return (
              <div
                key={a.id}
                className="grid grid-cols-[1.4fr_1fr_auto] items-center gap-3 border-b border-border-soft px-[22px] py-3.5 last:border-0"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-foreground">
                    {formatDateLabel(a.starts_at.slice(0, 10))}
                  </span>
                  <span className="text-[12.5px] tabular-nums text-muted-foreground">
                    {formatTimeUTC(a.starts_at)}–{formatTimeUTC(a.ends_at)} UTC
                  </span>
                </div>
                <span className="truncate text-[13px] text-muted-foreground">
                  {a.notes || "—"}
                </span>
                <Pill info={st} />
              </div>
            );
          })
        )}
      </Section>

      {/* Cobranças */}
      <Section
        icon={<CreditCard className="h-[18px] w-[18px]" />}
        title="Cobranças"
        count={charges.length}
      >
        {charges.length === 0 ? (
          <Empty>Nenhuma cobrança registrada.</Empty>
        ) : (
          charges.map((c) => {
            const st = CHARGE_STATUS[c.status] ?? CHARGE_STATUS.pending;
            return (
              <div
                key={c.id}
                className="grid grid-cols-[1.6fr_1fr_auto] items-center gap-3 border-b border-border-soft px-[22px] py-3.5 last:border-0"
              >
                <span className="truncate text-sm font-semibold text-foreground">
                  {c.descricao || "Cobrança Pix"}
                </span>
                <span className="text-sm font-bold tabular-nums text-foreground">
                  {brl.format(Number(c.valor))}
                </span>
                <Pill info={st} />
              </div>
            );
          })
        )}
      </Section>
    </div>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex w-fit items-center gap-1.5 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground"
    >
      <ArrowLeft className="h-4 w-4" />
      Voltar para Pacientes
    </button>
  );
}

function Section({
  icon,
  title,
  count,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div className="animate-fade-up overflow-hidden rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]">
      <div className="flex items-center gap-2 border-b border-border-soft px-[22px] py-3.5 text-sm font-bold text-foreground">
        <span className="text-primary">{icon}</span>
        {title}
        <span className="ml-1 rounded-full bg-secondary px-2 py-0.5 text-[11.5px] font-bold text-muted-foreground">
          {count}
        </span>
      </div>
      {children}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="p-10 text-center text-sm text-muted-foreground">{children}</p>;
}
