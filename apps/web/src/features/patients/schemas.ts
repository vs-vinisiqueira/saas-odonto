import { z } from "zod";

export const patientFormSchema = z.object({
  nome: z.string().min(1, "Informe o nome"),
  telefone: z.string().min(1, "Informe o telefone"),
  email: z.union([z.string().email("E-mail inválido"), z.literal("")]).optional(),
  observacoes: z.string().optional(),
});

export type PatientFormInput = z.infer<typeof patientFormSchema>;

export interface Patient {
  id: string;
  nome: string;
  telefone: string;
  email: string | null;
  observacoes: string | null;
}

export interface RecordAppointment {
  id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  notes: string | null;
}

export interface RecordCharge {
  id: string;
  valor: string;
  descricao: string | null;
  status: string;
  charge_id: string;
  created_at: string;
}

export interface PatientRecord {
  patient: Patient;
  appointments: RecordAppointment[];
  charges: RecordCharge[];
}
