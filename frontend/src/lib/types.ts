// These types mirror the backend response schemas.

export type Role = "company_admin" | "hiring_manager" | "interviewer";
export type Stage = "applied" | "screen" | "interview" | "offer" | "hired" | "rejected";
export type JobStatus = "draft" | "open" | "closed";
export type InterviewStatus = "scheduled" | "completed" | "cancelled";
export type ScorecardStatus = "pending" | "submitted";

export interface User {
  id: string;
  company_id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface Company {
  id: string;
  name: string;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  status: JobStatus;
  hiring_manager_id: string | null;
  created_at: string;
  stages: Stage[];
}

export interface PublicJob {
  id: string;
  title: string;
  description: string;
  company_name: string;
}

export interface Application {
  id: string;
  job_id: string;
  job_title: string;
  full_name: string;
  email: string;
  phone: string;
  cv_url: string;
  cover_letter: string | null;
  stage: Stage;
  created_at: string;
}

export interface StageHistory {
  id: string;
  from_stage: Stage | null;
  to_stage: Stage;
  changed_by_id: string | null;
  changed_at: string;
}

export interface Interview {
  id: string;
  application_id: string;
  interviewer_id: string;
  starts_at: string;
  ends_at: string;
  status: InterviewStatus;
  duration_minutes: number;
}

export interface Rating {
  criterion: string;
  rating: number;
  comment: string | null;
}

export interface Scorecard {
  id: string;
  interview_id: string;
  interviewer_id: string;
  status: ScorecardStatus;
  submitted_at: string | null;
  ratings: Rating[];
  average_score: number | null;
}

export interface ApplicationScorecards {
  aggregate_score: number | null;
  scorecards: Scorecard[];
}
