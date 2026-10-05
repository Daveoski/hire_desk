import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  Application,
  ApplicationScorecards,
  Company,
  Interview,
  Job,
  JobStatus,
  Role,
  Scorecard,
  Stage,
  StageHistory,
  User,
} from "./types";

// ---- Reading data ----

export const useCompany = () => useQuery({ queryKey: ["company"], queryFn: () => api.get<Company>("/companies/me") });

export const useJobs = (enabled = true) =>
  useQuery({ queryKey: ["jobs"], queryFn: () => api.get<Job[]>("/jobs"), enabled });

export const useJob = (jobId: string) =>
  useQuery({ queryKey: ["jobs", jobId], queryFn: () => api.get<Job>(`/jobs/${jobId}`) });

// Managers and admins only.
export const useUsers = (enabled = true, role?: Role) =>
  useQuery({
    queryKey: ["users", role ?? "all"],
    queryFn: () => api.get<User[]>(role ? `/users?role=${role}` : "/users"),
    enabled,
  });

export const useApplications = (jobId?: string) =>
  useQuery({
    queryKey: ["applications", jobId ?? "all"],
    queryFn: () => api.get<Application[]>(`/applications?limit=200${jobId ? `&job_id=${jobId}` : ""}`),
  });

export const useApplication = (id: string) =>
  useQuery({ queryKey: ["application", id], queryFn: () => api.get<Application>(`/applications/${id}`) });

export const useHistory = (id: string, enabled: boolean) =>
  useQuery({
    queryKey: ["history", id],
    queryFn: () => api.get<StageHistory[]>(`/applications/${id}/history`),
    enabled,
  });

export const useInterviews = (applicationId?: string) =>
  useQuery({
    queryKey: ["interviews", applicationId ?? "all"],
    queryFn: () => api.get<Interview[]>(applicationId ? `/interviews?application_id=${applicationId}` : "/interviews"),
  });

export const useScorecards = (applicationId: string) =>
  useQuery({
    queryKey: ["scorecards", applicationId],
    queryFn: () => api.get<ApplicationScorecards>(`/applications/${applicationId}/scorecards`),
  });

// ---- Google Calendar sync ----

export const useGoogleStatus = () =>
  useQuery({ queryKey: ["google"], queryFn: () => api.get<{ connected: boolean }>("/calendar/google/status") });

export function useGoogleConnect() {
  return useMutation({
    mutationFn: () => api.get<{ url: string }>("/calendar/google/authorize"),
    // The consent happens on Google's own page; it sends the browser back to us.
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
  });
}

export function useGoogleDisconnect() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: () => api.del<{ connected: boolean }>("/calendar/google"),
    onSuccess: () => refresh("google"),
  });
}

// ---- Changing data ----

// Any change to a candidate can affect many screens, so these refresh the related lists.
function useRefresh() {
  const queryClient = useQueryClient();
  return (...keys: string[]) => keys.forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));
}

export function useCreateJob() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (body: { title: string; description: string; hiring_manager_id: string | null }) =>
      api.post<Job>("/jobs", body),
    onSuccess: () => refresh("jobs"),
  });
}

export function useUpdateJob(jobId: string) {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (body: { title?: string; description?: string; status?: JobStatus; hiring_manager_id?: string | null }) =>
      api.patch<Job>(`/jobs/${jobId}`, body),
    onSuccess: () => refresh("jobs", "applications"),
  });
}

export function useMoveStage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: Stage }) =>
      api.patch<Application>(`/applications/${id}/stage`, { stage }),
    // Update the board right away, then roll back if the server refuses (for example, a skipped stage).
    onMutate: async ({ id, stage }) => {
      await queryClient.cancelQueries({ queryKey: ["applications"] });
      const previous = queryClient.getQueriesData<Application[]>({ queryKey: ["applications"] });
      queryClient.setQueriesData<Application[]>({ queryKey: ["applications"] }, (list) =>
        list?.map((item) => (item.id === id ? { ...item, stage } : item)),
      );
      return { previous };
    },
    onError: (_error, _vars, context) => context?.previous.forEach(([key, data]) => queryClient.setQueryData(key, data)),
    onSettled: (_data, _error, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["application", id] });
      queryClient.invalidateQueries({ queryKey: ["history", id] });
    },
  });
}

export function useDecide() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "hired" | "rejected" }) =>
      api.post<Application>(`/applications/${id}/decision`, { decision }),
    onSuccess: () => refresh("applications", "application", "history"),
  });
}

export function useScheduleInterview() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (body: { application_id: string; interviewer_id: string; starts_at: string; duration_minutes: number }) =>
      api.post<Interview>("/interviews", body),
    onSuccess: () => refresh("interviews", "scorecards"),
  });
}

export function useCancelInterview() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (id: string) => api.post<Interview>(`/interviews/${id}/cancel`),
    onSuccess: () => refresh("interviews", "scorecards"),
  });
}

export function useSubmitScorecard() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: ({
      interviewId,
      ratings,
    }: {
      interviewId: string;
      ratings: { criterion: string; rating: number; comment?: string }[];
    }) => api.put<Scorecard>(`/interviews/${interviewId}/scorecard`, { ratings }),
    onSuccess: () => refresh("interviews", "scorecards"),
  });
}

export function useCreateUser() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (body: { full_name: string; email: string; password: string; role: Role }) =>
      api.post<User>("/users", body),
    onSuccess: () => refresh("users"),
  });
}
