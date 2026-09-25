import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  title: "IBTastyAgent",
  description: "AI options-trading agent — monitor & manage",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        {/*
          Dev-only guard for the Next.js "Runtime Error: [object Event]" overlay.
          Some browser transports (HMR socket, blocked Notification/permission
          events, aborted resource loads) emit unhandled promise rejections whose
          `reason` is a DOM `Event` rather than an `Error`. These aren't actionable
          app bugs, but the dev overlay still surfaces them as a runtime error.
          This inline script runs during HTML parse — before Next's client runtime
          registers its own handler — so stopImmediatePropagation() prevents the
          overlay from ever seeing Event-typed (or empty) rejections. Genuine
          errors reject with an `Error` instance and are left fully visible.
          Rendered only in development; production has no overlay.
        */}
        {process.env.NODE_ENV !== "production" && (
          <script
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{
              __html:
                "window.addEventListener('unhandledrejection',function(e){var r=e.reason;if(r instanceof Event||r==null){e.stopImmediatePropagation();e.preventDefault();}},true);",
            }}
          />
        )}
        {children}
      </body>
    </html>
  );
}
