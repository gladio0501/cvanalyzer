import apiClient from './client';

export interface DashboardStats {
  cvs_uploaded: number;
  job_searches: number;
  saved_jobs: number;
  applications: number;
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/stats');
  return response.data;
};
