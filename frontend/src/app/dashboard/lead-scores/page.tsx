"use client";

import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";

export default function LeadScoresPage() {
  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Scoring"
        title="Lead Scoring"
        description="Prioritize your prospects based on firmographic fit, intent signals, and engagement."
      />

      <EmptyState 
        title="Coming Soon" 
        description="The lead scoring engine is currently being calibrated. Please check back later." 
      />
    </div>
  );
}
