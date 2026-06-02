"use client";

import { useEffect, useState } from "react";
import { Info, TriangleAlert } from "lucide-react";

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface ConfirmSpec {
  title: string;
  body: string;
  confirmLabel: string;
  danger?: boolean;
  requireType?: string;
  onConfirm: () => void;
}

export default function ConfirmDialog({
  spec,
  onClose,
}: {
  spec: ConfirmSpec | null;
  onClose: () => void;
}) {
  const [typed, setTyped] = useState("");
  useEffect(() => setTyped(""), [spec]);

  const open = !!spec;
  const ok = !spec?.requireType || typed.trim().toUpperCase() === spec.requireType.toUpperCase();

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent hideClose>
        <DialogHeader>
          <div className="mb-1.5 flex size-11 items-center justify-center rounded-full bg-brand-soft text-brand">
            {spec?.danger ? <TriangleAlert className="size-[22px]" /> : <Info className="size-[22px]" />}
          </div>
          <DialogTitle>{spec?.title}</DialogTitle>
          <DialogDescription>{spec?.body}</DialogDescription>
        </DialogHeader>
        {spec?.requireType && (
          <Input
            placeholder={`Type ${spec.requireType} to confirm`}
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            autoFocus
          />
        )}
        <DialogFooter>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button
            variant={spec?.danger ? "destructive" : "default"}
            disabled={!ok}
            onClick={() => {
              spec?.onConfirm();
            }}
          >
            {spec?.confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
