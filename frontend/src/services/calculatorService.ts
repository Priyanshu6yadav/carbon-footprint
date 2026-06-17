import api from './api';
import type { CalculationResult, CalculatorInput, SavedLog } from '@/types';

export const calculatorService = {
  calculate: (data: CalculatorInput) =>
    api.post<CalculationResult>('/api/calculator/calculate', data).then((r) => r.data),

  save: (data: CalculatorInput) =>
    api.post<SavedLog>('/api/calculator/save', data).then((r) => r.data),

  history: (limit = 20, offset = 0) =>
    api.get<SavedLog[]>(`/api/calculator/history?limit=${limit}&offset=${offset}`).then((r) => r.data),
};
