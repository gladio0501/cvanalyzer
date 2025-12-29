import apiClient from './client';

export interface CVAnalysisRequest {
  cv_file: File;
  job_description: string;
}

export interface CVAnalysisResult {
  match_score?: number;
  feedback?: string;
  skills_match?: {
    matched: string[];
    missing: string[];
  };
  experience_analysis?: string;
  recommendations?: string[];
  error?: string;
}

export interface CVUploadHistory {
  id: number;
  filename: string;
  file_size: number;
  uploaded_at: string;
  last_used: string;
  profile_data: any;
}

// Analyze CV against job description
export const analyzeCVWithJob = async (
  cvFile: File,
  jobDescription: string
): Promise<CVAnalysisResult> => {
  const formData = new FormData();
  formData.append('cv_file', cvFile);
  formData.append('job_text', jobDescription);

  const response = await apiClient.post<CVAnalysisResult>('/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Get user's uploaded CVs
export const getUserCVs = async (): Promise<CVUploadHistory[]> => {
  const response = await apiClient.get<CVUploadHistory[]>('/api/cvs');
  return response.data;
};

// Delete a CV
export const deleteCV = async (cvId: number): Promise<void> => {
  await apiClient.delete(`/api/cvs/${cvId}`);
};

// Upload CV (without analysis)
export const uploadCV = async (cvFile: File): Promise<CVUploadHistory> => {
  const formData = new FormData();
  formData.append('cv_file', cvFile);

  const response = await apiClient.post<CVUploadHistory>('/api/cvs/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};
