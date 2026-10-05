import { Logo } from "@/components/layout/logo";
import { StageThread } from "@/components/shared/stage-thread";

// Shared frame for login and register: the form on the left, the product idea on the right.
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col px-6 py-8 sm:px-12">
        <Logo href="/login" />
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="mb-8 mt-2 text-muted-foreground">{subtitle}</p>
          {children}
        </div>
      </div>
      <div className="hidden flex-col justify-center gap-10 bg-foreground p-14 text-background lg:flex">
        <h2 className="max-w-md text-4xl font-bold leading-tight">Every candidate, one clear path to a decision.</h2>
        <p className="max-w-md text-background/70">
          Post a job, collect applications on a public page, and move people through interviews without spreadsheets.
        </p>
        <div className="max-w-md rounded-lg bg-background p-6 text-foreground">
          <StageThread stage="interview" />
        </div>
      </div>
    </div>
  );
}
