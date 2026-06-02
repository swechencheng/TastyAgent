"use client";

import { useState } from "react";
import useSWR from "swr";
import { ChevronDown, ChevronUp } from "lucide-react";

import { ActivityItem, fetcher } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Empty, ErrorNote, Loading, PageHeader, num } from "@/components/common";
import { cn } from "@/lib/utils";

const POLL = { refreshInterval: 8000 };

export default function Activity() {
  const { data, error } = useSWR<ActivityItem[]>("/api/activity", fetcher, POLL);
  const [open, setOpen] = useState<number | null>(null);

  if (error) return <ErrorNote msg="Could not load the activity log." />;
  if (!data) return <Loading />;

  return (
    <div className="max-w-[1080px]">
      <PageHeader title="Activity">
        Every decision cycle — Claude&apos;s commentary and the trades considered, placed, and rejected.
      </PageHeader>

      {data.length === 0 ? (
        <Empty>No decision cycles yet. Run one from the sidebar.</Empty>
      ) : (
        <div className="flex flex-col">
          {data.map((a, i) => {
            const isOpen = open === a.id || (open === null && i === 0);
            return (
              <div key={a.id} className="flex gap-4">
                <div className="flex flex-col items-center pt-1.5">
                  <span className="z-[1] size-[11px] rounded-full border-2 border-background bg-brand" />
                  {i < data.length - 1 && <span className="mt-1 w-0.5 flex-1 bg-border" />}
                </div>
                <div className="flex-1 pb-6">
                  <div className="flex flex-wrap items-center justify-between gap-4 cursor-pointer" onClick={() => setOpen(isOpen ? -1 : a.id)}>
                    <div className={cn("flex items-center gap-2.5 text-[13px] font-semibold", num)}>
                      {new Date(a.created_at).toLocaleString()}
                      <Badge variant="default" className="text-[11px]">{a.mode}</Badge>
                    </div>
                    <div className="flex items-center gap-3.5 text-xs text-muted-foreground">
                      <span><b className={cn("text-foreground", num)}>{a.considered}</b> considered</span>
                      <span className="text-gain"><b className={num}>{a.placed}</b> placed</span>
                      <span className="text-loss"><b className={num}>{a.rejected}</b> rejected</span>
                      {isOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
                    </div>
                  </div>

                  <div className="mt-2 max-w-[760px] text-[13px] leading-relaxed text-muted-foreground">{a.commentary}</div>

                  {isOpen && a.symbols.length > 0 && (
                    <div className="mt-3">
                      <div className="mb-2 text-[11px] uppercase tracking-[0.05em] text-text-faint">Symbols placed</div>
                      <div className="flex flex-wrap gap-1.5">
                        {a.symbols.map((s) => (
                          <span key={s} className={cn("rounded-md border border-border bg-surface-2 px-2.5 py-0.5 text-xs", num)}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
