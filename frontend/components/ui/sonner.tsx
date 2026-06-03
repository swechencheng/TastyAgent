"use client";

import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-card group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-[0_8px_24px_rgba(0,0,0,0.5)] group-[.toaster]:rounded-[10px]",
          description: "group-[.toast]:text-muted-foreground",
          actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton: "group-[.toast]:bg-secondary group-[.toast]:text-muted-foreground",
          success: "group-[.toaster]:border-l-2 group-[.toaster]:border-l-gain",
          error: "group-[.toaster]:border-l-2 group-[.toaster]:border-l-loss",
          info: "group-[.toaster]:border-l-2 group-[.toaster]:border-l-info",
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
