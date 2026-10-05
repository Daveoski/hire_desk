"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Field } from "@/components/shared/field";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select } from "@/components/ui/input";
import { useScheduleInterview, useUsers } from "@/lib/queries";
import { scheduleSchema } from "@/lib/schemas";
import type { Application } from "@/lib/types";

type ScheduleValues = z.infer<typeof scheduleSchema>;

// The backend rejects a slot that overlaps another interview for the same interviewer (409).
// That message is shown as a form error so the manager can pick another time.
export function ScheduleDialog({
  application,
  open,
  onOpenChange,
}: {
  application: Application;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule interview</DialogTitle>
          <DialogDescription>With {application.full_name} for {application.job_title}.</DialogDescription>
        </DialogHeader>
        {open && <ScheduleForm application={application} onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  );
}

function ScheduleForm({ application, onDone }: { application: Application; onDone: () => void }) {
  const interviewers = useUsers(true, "interviewer");
  const schedule = useScheduleInterview();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ScheduleValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: { interviewer_id: "", starts_at: "", duration_minutes: 45 },
  });

  function onSubmit(values: ScheduleValues) {
    schedule.mutate(
      {
        application_id: application.id,
        interviewer_id: values.interviewer_id,
        // The datetime-local value has no timezone; new Date() reads it as local time and
        // toISOString() converts it to UTC, which is what the backend requires.
        starts_at: new Date(values.starts_at).toISOString(),
        duration_minutes: values.duration_minutes,
      },
      {
        onSuccess: () => {
          toast.success("Interview scheduled");
          onDone();
        },
        onError: (error) => setError("starts_at", { message: error.message }),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <Field label="Interviewer" htmlFor="interviewer_id" error={errors.interviewer_id?.message}>
        <Select id="interviewer_id" {...register("interviewer_id")}>
          <option value="">Choose an interviewer</option>
          {interviewers.data?.map((user) => (
            <option key={user.id} value={user.id}>
              {user.full_name}
            </option>
          ))}
        </Select>
      </Field>
      <div className="grid gap-4 sm:grid-cols-[1fr_9rem]">
        <Field label="Date and time" htmlFor="starts_at" error={errors.starts_at?.message}>
          <Input id="starts_at" type="datetime-local" {...register("starts_at")} />
        </Field>
        <Field label="Minutes" htmlFor="duration_minutes" error={errors.duration_minutes?.message}>
          <Input id="duration_minutes" type="number" step={15} min={15} max={240} {...register("duration_minutes", { valueAsNumber: true })} />
        </Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={schedule.isPending}>
          {schedule.isPending ? "Scheduling..." : "Schedule interview"}
        </Button>
      </div>
    </form>
  );
}
