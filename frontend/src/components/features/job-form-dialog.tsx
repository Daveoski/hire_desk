"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Field } from "@/components/shared/field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useCreateJob, useUpdateJob, useUsers } from "@/lib/queries";
import { jobSchema } from "@/lib/schemas";
import type { Job } from "@/lib/types";

type JobValues = z.infer<typeof jobSchema>;

// Create a job (no `job`) or edit one. Only company admins can open this.
export function JobFormDialog({
  open,
  onOpenChange,
  job,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  job?: Job;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{job ? "Edit job" : "Create a job"}</DialogTitle>
          <DialogDescription>
            {job ? "Changes show on the public page right away." : "Save it as a draft, or open it to start taking applications."}
          </DialogDescription>
        </DialogHeader>
        {/* Mounted only while open, so the form always starts from the current job. */}
        {open && <JobForm job={job} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  );
}

function JobForm({ job, onDone }: { job?: Job; onDone: () => void }) {
  const managers = useUsers(true, "hiring_manager");
  const create = useCreateJob();
  const update = useUpdateJob(job?.id ?? "");
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<JobValues>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      title: job?.title ?? "",
      description: job?.description ?? "",
      status: job?.status ?? "draft",
      hiring_manager_id: job?.hiring_manager_id ?? "",
    },
  });

  const pending = create.isPending || update.isPending;

  function onSubmit(values: JobValues) {
    const hiring_manager_id = values.hiring_manager_id || null;
    const onError = (error: Error) => toast.error(error.message);
    if (job) {
      update.mutate(
        { title: values.title, description: values.description, status: values.status, hiring_manager_id },
        { onSuccess: () => { toast.success("Job saved"); onDone(); }, onError },
      );
    } else {
      // A new job starts as a draft. If the admin chose another status, set it right after.
      create.mutate(
        { title: values.title, description: values.description, hiring_manager_id },
        {
          onSuccess: async (created) => {
            if (values.status !== "draft") {
              await api.patch(`/jobs/${created.id}`, { status: values.status }).catch(() => null);
            }
            toast.success("Job created");
            onDone();
          },
          onError,
        },
      );
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <Field label="Job title" htmlFor="title" error={errors.title?.message}>
        <Input id="title" placeholder="Product Designer" {...register("title")} />
      </Field>
      <Field label="Description" htmlFor="description" error={errors.description?.message}>
        <Textarea id="description" rows={6} {...register("description")} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Status" htmlFor="status" hint="Only open jobs accept applications">
          <Select id="status" {...register("status")}>
            <option value="draft">Draft</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </Select>
        </Field>
        <Field label="Hiring manager" htmlFor="hiring_manager_id">
          <Select id="hiring_manager_id" {...register("hiring_manager_id")}>
            <option value="">No hiring manager</option>
            {managers.data?.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={pending}>
          {pending ? "Saving..." : job ? "Save job" : "Create job"}
        </Button>
      </div>
    </form>
  );
}
