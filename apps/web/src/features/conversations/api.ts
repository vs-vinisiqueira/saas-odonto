import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type MessageSender = "patient" | "ai" | "human";

export interface Conversation {
  id: string;
  patient_id: string | null;
  patient_nome: string | null;
  external_number: string;
  channel: string;
  ai_enabled: boolean;
  last_message_at: string | null;
  last_message_preview: string | null;
  last_message_sender: MessageSender | null;
}

export interface Message {
  id: string;
  direction: "inbound" | "outbound";
  sender: MessageSender;
  text: string;
  created_at: string;
}

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: async () => (await api.get<Conversation[]>("/conversations")).data,
    // Inbox: atualiza sozinho para refletir novas mensagens do agente.
    refetchInterval: 15_000,
  });
}

export function useConversationMessages(id: string | null) {
  return useQuery({
    queryKey: ["conversation-messages", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<Message[]>(`/conversations/${id}/messages`)).data,
    refetchInterval: id ? 10_000 : false,
  });
}

export function useSendMessage(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (text: string) =>
      (await api.post<Message>(`/conversations/${id}/messages`, { text })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversation-messages", id] });
      qc.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useToggleAI(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const conv = qc.getQueryData<Conversation[]>(["conversations"])?.find((c) => c.id === id);
      return (
        await api.patch<Conversation>(`/conversations/${id}`, {
          ai_enabled: !(conv?.ai_enabled ?? true),
        })
      ).data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
