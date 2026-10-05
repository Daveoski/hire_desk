"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { ErrorState } from "@/components/shared/empty-state";
import { Field } from "@/components/shared/field";
import { PageHeader } from "@/components/shared/page-header";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCreateUser, useUsers } from "@/lib/queries";
import { userSchema } from "@/lib/schemas";
import { ROLE_LABEL } from "@/lib/stages";
import { useAuthStore } from "@/stores/auth-store";

type UserValues = z.infer<typeof userSchema>;

export default function TeamPage() {
  const router = useRouter();
  const current = useAuthStore((state) => state.user);
  const isAdmin = current?.role === "company_admin";
  const users = useUsers(isAdmin);
  const [adding, setAdding] = useState(false);

  // Only company admins manage the team.
  useEffect(() => {
    if (current && !isAdmin) router.replace("/overview");
  }, [current, isAdmin, router]);

  return (
    <>
      <PageHeader
        title="Team"
        description="Add hiring managers and interviewers to your company."
        actions={
          <Button onClick={() => setAdding(true)}>
            <UserPlus /> Add team member
          </Button>
        }
      />
      {users.isError && <ErrorState message={users.error.message} />}
      {users.isLoading && <Skeleton className="h-48" />}
      {users.data && (
        <Card className="overflow-hidden">
          <ul className="divide-y">
            {users.data.map((member) => (
              <li key={member.id} className="flex items-center gap-3 px-5 py-3.5">
                <Avatar name={member.full_name} />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold">{member.full_name}</p>
                  <p className="truncate text-sm text-muted-foreground">{member.email}</p>
                </div>
                <Badge>{ROLE_LABEL[member.role]}</Badge>
              </li>
            ))}
          </ul>
        </Card>
      )}
      <AddMemberDialog open={adding} onOpenChange={setAdding} />
    </>
  );
}

function AddMemberDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add team member</DialogTitle>
          <DialogDescription>Share the email and password with them so they can log in.</DialogDescription>
        </DialogHeader>
        {open && <AddMemberForm onDone={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  );
}

function AddMemberForm({ onDone }: { onDone: () => void }) {
  const create = useCreateUser();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<UserValues>({ resolver: zodResolver(userSchema), defaultValues: { role: "interviewer" } });

  function onSubmit(values: UserValues) {
    create.mutate(values, {
      onSuccess: () => {
        toast.success(`${values.full_name} added`);
        onDone();
      },
      onError: (error) => setError("email", { message: error.message }),
    });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <Field label="Full name" htmlFor="full_name" error={errors.full_name?.message}>
        <Input id="full_name" {...register("full_name")} />
      </Field>
      <Field label="Email" htmlFor="email" error={errors.email?.message}>
        <Input id="email" type="email" {...register("email")} />
      </Field>
      <Field label="Temporary password" htmlFor="password" error={errors.password?.message} hint="At least 8 characters">
        <Input id="password" type="text" autoComplete="off" {...register("password")} />
      </Field>
      <Field label="Role" htmlFor="role">
        <Select id="role" {...register("role")}>
          <option value="interviewer">Interviewer</option>
          <option value="hiring_manager">Hiring manager</option>
          <option value="company_admin">Company admin</option>
        </Select>
      </Field>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Adding..." : "Add team member"}
        </Button>
      </div>
    </form>
  );
}
