"use client";

import { ChevronDown, ChevronUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useHealth } from "@/features/health/api";
import { useUiStore } from "@/stores/ui";

export function HealthStatus() {
  const { data, error, isPending } = useHealth();
  const detailsOpen = useUiStore((state) => state.detailsOpen);
  const toggleDetails = useUiStore((state) => state.toggleDetails);

  const label = isPending
    ? "Checking the API..."
    : error
      ? "API unreachable"
      : `API status: ${data.status}`;

  return (
    <section className="flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex items-center justify-between gap-4">
        <p className="font-medium">{label}</p>
        <Button variant="ghost" size="sm" onClick={toggleDetails}>
          {detailsOpen ? <ChevronUp /> : <ChevronDown />}
          {detailsOpen ? "Hide details" : "Show details"}
        </Button>
      </div>
      {detailsOpen ? (
        <p className="text-sm text-muted-foreground">
          Calls <code className="font-mono">GET /health</code> on the API set
          in <code className="font-mono">NEXT_PUBLIC_API_URL</code>.
        </p>
      ) : null}
    </section>
  );
}
