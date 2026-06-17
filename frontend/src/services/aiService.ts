import api from './api';

export interface Challenge {
  id: string;
  title: string;
  description: string;
  challenge_type: 'daily' | 'weekly' | 'monthly';
  template_slug: string | null;
  xp_reward: number;
  co2_saved_estimate_kg: number;
  difficulty: 'easy' | 'medium' | 'hard';
  is_active: boolean;
}

export interface ChallengeCompletionResponse {
  id: string;
  challenge_id: string;
  completed_at: string;
  notes: string | null;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export const aiService = {
  listChallenges: () =>
    api.get<Challenge[]>('/api/challenges/').then((r) => r.data),

  generateChallenges: () =>
    api.post<Challenge[]>('/api/challenges/generate').then((r) => r.data),

  completeChallenge: (challengeId: string, notes?: string) =>
    api.post<ChallengeCompletionResponse>(`/api/challenges/${challengeId}/complete`, {
      challenge_id: challengeId,
      notes,
    }).then((r) => r.data),

  chatSustainability: (message: string, history: ChatMessage[]) =>
    api.post<ChatResponse>('/api/chat/sustainability', {
      message,
      history,
    }).then((r) => r.data),
};
