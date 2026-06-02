import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap transition-colors",
  {
    variants: {
      variant: {
        default: "border-border text-muted-foreground",
        brand: "border-transparent bg-brand-soft text-brand",
        open: "border-gain/50 text-gain",
        warn: "border-warn/50 text-warn",
        gain: "border-transparent bg-gain-soft text-gain",
        loss: "border-transparent bg-loss-soft text-loss",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

function Badge({ className, variant, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {dot && <span className="size-[7px] rounded-full bg-current" />}
      {children}
    </span>
  );
}

export { Badge, badgeVariants };
