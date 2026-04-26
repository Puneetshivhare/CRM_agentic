"use client";

import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";

export default function WorkflowsPage() {
  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Workflows"
        title="Agentic Workflows"
        description="Design and monitor complex, multi-step agentic workflows."
      />

      <EmptyState 
        title="Coming Soon" 
        description="The workflows feature is currently under development. Please check back later." 
      />
    </div>
  );
}
