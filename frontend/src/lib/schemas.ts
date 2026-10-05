import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Enter your password"),
});

export const registerSchema = z.object({
  company_name: z.string().min(1, "Enter your company name").max(100),
  full_name: z.string().min(1, "Enter your name").max(100),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters").max(128),
});

export const jobSchema = z.object({
  title: z.string().min(1, "Enter a job title").max(200),
  description: z.string().min(1, "Describe the role").max(10000),
  status: z.enum(["draft", "open", "closed"]),
  hiring_manager_id: z.string(), // "" means no hiring manager
});

export const applySchema = z.object({
  full_name: z.string().min(1, "Enter your name").max(100),
  email: z.string().email("Enter a valid email"),
  phone: z.string().min(5, "Enter a phone number").max(30),
  cover_letter: z.string().max(5000).optional(),
});

export const userSchema = z.object({
  full_name: z.string().min(1, "Enter a name").max(100),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters").max(128),
  role: z.enum(["company_admin", "hiring_manager", "interviewer"]),
});

export const scheduleSchema = z.object({
  interviewer_id: z.string().min(1, "Choose an interviewer"),
  starts_at: z.string().min(1, "Choose a date and time"),
  duration_minutes: z
    .number({ invalid_type_error: "Enter the length in minutes" })
    .int()
    .min(15, "At least 15 minutes")
    .max(240, "At most 240 minutes"),
});

export const scorecardSchema = z.object({
  ratings: z
    .array(
      z.object({
        criterion: z.string().min(1, "Name the criterion").max(100),
        rating: z.number().int().min(1, "Choose a rating").max(5),
        comment: z.string().max(1000).optional(),
      }),
    )
    .min(1, "Add at least one criterion")
    .max(20),
});

export const CV_EXTENSIONS = [".pdf", ".doc", ".docx"];
export const CV_MAX_BYTES = 5 * 1024 * 1024;

export function checkCv(file: File): string | null {
  const name = file.name.toLowerCase();
  if (!CV_EXTENSIONS.some((ext) => name.endsWith(ext))) return "The CV must be a PDF, DOC or DOCX file";
  if (file.size > CV_MAX_BYTES) return "The CV must be 5 MB or smaller";
  return null;
}
