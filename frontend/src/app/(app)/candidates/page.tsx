"use client";

import { Users } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { EmptyState, ErrorState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { StageBadge } from "@/components/shared/stage-badge";
import { Avatar } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useApplications } from "@/lib/queries";
import { PIPELINE, STAGE_LABEL } from "@/lib/stages";
import { formatDate } from "@/lib/utils";

export default function CandidatesPage() {
  const applications = useApplications();
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("");

  const rows = (applications.data ?? []).filter(
    (item) =>
      (!stage || item.stage === stage) &&
      (!search || `${item.full_name} ${item.email} ${item.job_title}`.toLowerCase().includes(search.toLowerCase())),
  );

  return (
    <>
      <PageHeader title="Candidates" description="Everyone you can see across your jobs." />
      <div className="mb-4 flex flex-wrap gap-3">
        <Input
          aria-label="Search candidates"
          placeholder="Search by name, email or job"
          className="max-w-xs"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Select aria-label="Filter by stage" className="w-44" value={stage} onChange={(event) => setStage(event.target.value)}>
          <option value="">All stages</option>
          {PIPELINE.map((item) => (
            <option key={item} value={item}>
              {STAGE_LABEL[item]}
            </option>
          ))}
        </Select>
      </div>

      {applications.isError && <ErrorState message={applications.error.message} />}
      {applications.isLoading && <Skeleton className="h-48" />}
      {applications.data && rows.length === 0 && (
        <EmptyState icon={Users} title="No candidates found" description="Try a different search or stage." />
      )}
      {rows.length > 0 && (
        <Card className="overflow-hidden">
          <ul className="divide-y">
            {rows.map((item) => (
              <li key={item.id}>
                <Link href={`/candidates/${item.id}`} className="flex items-center gap-3 px-5 py-3.5 hover:bg-muted/50">
                  <Avatar name={item.full_name} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{item.full_name}</p>
                    <p className="truncate text-sm text-muted-foreground">{item.job_title}</p>
                  </div>
                  <span className="hidden text-sm text-muted-foreground sm:block">{formatDate(item.created_at)}</span>
                  <StageBadge stage={item.stage} />
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}
