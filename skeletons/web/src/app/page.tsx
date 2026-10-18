import { HealthStatus } from "@/features/health/components/health-status";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">__NAME__</h1>
      <p className="text-lg text-muted-foreground">
        Edit <code className="font-mono">src/app/page.tsx</code> to get started.
      </p>
      <HealthStatus />
    </main>
  );
}
