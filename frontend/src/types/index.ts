// User types (from auth.ts)
export interface User {
  id: number;
  email: string;
  name: string;
  profile_picture: string | null;
  oauth_provider: string;
  default_region: string | null;
  default_job_source: string | null;
  email_notifications: boolean;
  created_at: string;
  last_login: string;
}

// CV Upload types
export interface CVUpload {
  id: number;
  user_id: number;
  filename: string;
  file_path: string;
  file_size: number;
  profile_data: CVProfile | null;
  uploaded_at: string;
  last_used: string;
}

export interface CVProfile {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  skills: string[];
  experience: Experience[];
  education: Education[];
}

export interface Experience {
  title: string;
  company: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface Education {
  degree: string;
  institution: string;
  location?: string;
  graduation_date?: string;
}

// Job types
export interface Job {
  job_id?: string;
  job_title: string;
  company: string;
  location: string;
  description?: string;
  job_url: string;
  job_type?: string;
  posted_date?: string;
  salary?: string;
  match_score?: number;
  match_reasons?: string[];
  lora_score?: number;
  profile_score?: number;
}

export interface JobSearch {
  id: number;
  user_id: number;
  job_source: string;
  region?: string;
  job_title?: string;
  jobspy_sites?: string[];
  total_jobs_found: number;
  average_match_score?: number;
  search_duration_seconds?: number;
  searched_at: string;
}

export interface SavedJob {
  id: number;
  user_id: number;
  job_title: string;
  company: string;
  job_url: string;
  match_score?: number;
  notes?: string;
  application_status: 'saved' | 'applied' | 'interview' | 'rejected' | 'accepted';
  saved_at: string;
  updated_at: string;
}

// Job Source types
export type JobSource = 'jobicy' | 'jobspy';

export interface JobSourceConfig {
  name: string;
  display_name: string;
  requires_region: boolean;
  requires_sites?: boolean;
  available_sites?: string[];
}

// API Response types
export interface ApiError {
  message: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
