import apiClient from './client';
import type { Job, SavedJob } from '../types';

export interface JobSearchRequest {
  cv_file: File;
  job_source: 'jobicy' | 'jobspy';
  region?: string;
  job_title?: string;
  top_k?: number;
  jobspy_sites?: string[];
}

export interface JobSearchResult {
  recommendations: Job[];
  job_source_used: string;
  total_jobs_found: number;
  cv_profile?: any;
  error?: string;
}

export interface JobSource {
  name: string;
  display_name: string;
  description: string;
  requires_sites: boolean;
  available_sites?: string[];
}

export interface SaveJobRequest {
  job_title: string;
  company: string;
  job_url: string;
  match_score?: number;
  notes?: string;
}

// Get available job sources
export const getJobSources = async (): Promise<JobSource[]> => {
  const response = await apiClient.get('/api/job-sources');
  return response.data;
};

// Search for jobs
export const searchJobs = async (request: JobSearchRequest): Promise<JobSearchResult> => {
  const formData = new FormData();
  formData.append('cv_file', request.cv_file);
  formData.append('job_source', request.job_source);

  if (request.region) {
    formData.append('region', request.region);
  }
  if (request.job_title) {
    formData.append('job_title', request.job_title);
  }
  if (request.top_k) {
    formData.append('top_k', request.top_k.toString());
  }
  if (request.jobspy_sites && request.jobspy_sites.length > 0) {
    formData.append('jobspy_sites', request.jobspy_sites.join(','));
  }

  const response = await apiClient.post('/jobs/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 180000, // 3 minutes for JobSpy scraping
  });

  return response.data;
};

// Get user's saved jobs
export const getSavedJobs = async (): Promise<SavedJob[]> => {
  const response = await apiClient.get('/api/saved-jobs');
  return response.data;
};

// Save a job
export const saveJob = async (jobData: SaveJobRequest): Promise<SavedJob> => {
  const response = await apiClient.post('/api/saved-jobs', jobData);
  return response.data;
};

// Update saved job (e.g., add notes, change status)
export const updateSavedJob = async (
  jobId: number,
  updates: Partial<SavedJob>
): Promise<SavedJob> => {
  const response = await apiClient.put(`/api/saved-jobs/${jobId}`, updates);
  return response.data;
};

// Delete a saved job
export const deleteSavedJob = async (jobId: number): Promise<void> => {
  await apiClient.delete(`/api/saved-jobs/${jobId}`);
};

// Suggest job title from CV
export const suggestJobTitle = async (cvFile: File): Promise<string> => {
  const formData = new FormData();
  formData.append('cv_file', cvFile);

  const response = await apiClient.post('/jobs/suggest-title', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // 60 seconds
  });

  return response.data.suggested_title;
};
