"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { API_BASE, EventFeedItem } from "@/lib/api";

const KIND_LABEL: Record<string, string> = {
  working: "Order working",
  open: "Filled — position open",
  rolled: "Rolled",
  managed: "Managed",
  closed: "Closed",
  canceled: "Canceled",
  rejected: "Rejected",
  planned: "Planned",
};

// Which lifecycle events are worth interrupting the user for.
const NOTIFY = new Set(["working", "open", "rolled", "managed", "closed", "canceled", "rejected"]);

function fire(e: EventFeedItem) {
  const label = KIND_LABEL[e.kind] ?? e.kind;
  const title = `${e.symbol} · ${label}`;
  const opts = { description: e.detail, duration: 6000 };

  // 1) In-app toast (tone by kind)
  if (e.kind === "open") toast.success(title, opts);
  else if (e.kind === "rejected" || e.kind === "canceled") toast.error(title, opts);
  else if (e.kind === "rolled" || e.kind === "managed") toast.warning(title, opts);
  else if (e.kind === "closed") {
    const win = /realized \+/.test(e.detail);
    (win ? toast.success : toast.error)(title, opts);
  } else toast.info(title, opts);

  // 2) Desktop notification (best-effort, if granted)
  if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
    try {
      new Notification(title, { body: e.detail, tag: `tastyagent-${e.id}` });
    } catch {
      /* ignore */
    }
  }
}

/** Background poller: watches /api/events and surfaces new ones as toast + desktop notifications. */
export default function Notifications() {
  const lastId = useRef(0);
  const seeded = useRef(false);

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }

    let alive = true;
    const poll = async () => {
      try {
        const r = await fetch(`${API_BASE}/api/events?after=${lastId.current}&limit=50`);
        if (!r.ok) return;
        const items: EventFeedItem[] = await r.json();
        if (!items.length) return;
        const maxId = items[items.length - 1].id;
        if (!seeded.current) {
          // First run: adopt the current high-water mark, don't replay history.
          seeded.current = true;
          lastId.current = maxId;
          return;
        }
        for (const e of items) if (NOTIFY.has(e.kind)) fire(e);
        lastId.current = maxId;
      } catch {
        /* network blip — try again next tick */
      }
    };

    poll();
    const id = setInterval(() => {
      if (alive) poll();
    }, 4000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return null;
}
