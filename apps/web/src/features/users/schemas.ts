import { z } from "zod";

export type Role = "owner" | "dentist" | "secretary";

export const ROLES: Role[] = ["owner", "dentist", "secretary"];

export const ROLE_LABELS: Record<Role, string> = {
  owner: "Administrador",
  dentist: "Dentista",
  secretary: "Secretária",
};

export interface User {
  id: string;
  email: string;
  role: Role;
  nome: string | null;
  telefone: string | null;
  is_active: boolean;
  created_at: string;
}

export const userCreateSchema = z.object({
  nome: z.string().min(1, "Informe o nome"),
  email: z.string().email("E-mail inválido"),
  telefone: z.string().optional(),
  role: z.enum(["owner", "dentist", "secretary"]),
  password: z.string().min(8, "Mínimo de 8 caracteres"),
});
export type UserCreateInput = z.infer<typeof userCreateSchema>;

export const userEditSchema = z.object({
  nome: z.string().min(1, "Informe o nome"),
  telefone: z.string().optional(),
  role: z.enum(["owner", "dentist", "secretary"]),
});
export type UserEditInput = z.infer<typeof userEditSchema>;

export const passwordResetSchema = z.object({
  password: z.string().min(8, "Mínimo de 8 caracteres"),
});
export type PasswordResetInput = z.infer<typeof passwordResetSchema>;
