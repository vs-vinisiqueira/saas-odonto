import { z } from "zod";

export const chargeFormSchema = z.object({
  valor: z.coerce.number().positive("Valor deve ser maior que zero"),
  descricao: z.string().optional(),
  patient_id: z.string().optional(),
});

export type ChargeFormInput = z.infer<typeof chargeFormSchema>;

export interface Payment {
  id: string;
  valor: string;
  descricao: string | null;
  metodo: string;
  status: string;
  charge_id: string;
  qr_code: string | null;
  qr_code_base64: string | null;
  patient_id: string | null;
  appointment_id: string | null;
}
