import api from './api';

export interface CarbonTrendPoint {
  period: string;
  transport: number;
  energy: number;
  food: number;
  shopping: number;
  total: number;
}

export interface CategoryBreakdownData {
  transport: number;
  energy: number;
  food: number;
  shopping: number;
}

export interface HabitCompletionPoint {
  id: string;
  name: string;
  slug: string;
  icon: string;
  logged_days: number;
  completion_rate: number;
}

export interface EcoScoreTrendPoint {
  period: string;
  score: number;
}

export interface AnalyticsQueryParams {
  range: 'week' | 'month' | 'year' | 'custom';
  start?: string;
  end?: string;
}

function buildParams(params: AnalyticsQueryParams) {
  const query = new URLSearchParams();
  query.append('range', params.range);
  if (params.range === 'custom') {
    if (params.start) query.append('start', params.start);
    if (params.end) query.append('end', params.end);
  }
  return query.toString();
}

export const analyticsService = {
  getCarbonTrend: (params: AnalyticsQueryParams) =>
    api.get<CarbonTrendPoint[]>(`/api/analytics/carbon-trend?${buildParams(params)}`).then((r) => r.data),

  getCategoryBreakdown: (params: AnalyticsQueryParams) =>
    api.get<CategoryBreakdownData>(`/api/analytics/category-breakdown?${buildParams(params)}`).then((r) => r.data),

  getHabitCompletion: (params: AnalyticsQueryParams) =>
    api.get<HabitCompletionPoint[]>(`/api/analytics/habit-completion?${buildParams(params)}`).then((r) => r.data),

  getEcoScoreTrend: (params: AnalyticsQueryParams) =>
    api.get<EcoScoreTrendPoint[]>(`/api/analytics/eco-score-trend?${buildParams(params)}`).then((r) => r.data),

  downloadPdfReport: (params: AnalyticsQueryParams) => {
    const url = `${api.defaults.baseURL || ''}/api/analytics/report/pdf?${buildParams(params)}`;
    return api.get(url, { responseType: 'blob' }).then((response) => {
      // Create a link element, set the href to the blob URL, and click it
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // Try to read content disposition header for filename
      let filename = `CarbonTrack_Report_${params.range}.pdf`;
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    });
  }
};
