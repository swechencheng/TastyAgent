import React from "react";

interface IbkrLogoProps extends React.SVGProps<SVGSVGElement> {}

/**
 * Pure Interactive Brokers (IBKR) logo mark component (geometric emblem only, no text letters).
 */
export default function IbkrLogo({
  className = "h-6 w-auto",
  ...props
}: IbkrLogoProps) {
  return (
    <svg
      viewBox="0 0 48 88.4"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="IBKR Logo"
      {...props}
    >
      <defs>
        <linearGradient
          id="ibkr-logo-grad"
          gradientUnits="userSpaceOnUse"
          x1="3633.335"
          y1="66.0445"
          x2="3671.0737"
          y2="66.0445"
          gradientTransform="matrix(-1 0 0 1 3673.7529 0)"
        >
          <stop offset="0" stopColor="#D71F27" />
          <stop offset="1" stopColor="#971B1E" />
        </linearGradient>
      </defs>
      {/* Lower darker shaded triangle */}
      <polygon fill="url(#ibkr-logo-grad)" points="40.4,86.8 2.7,86.8 2.7,45.3" />
      {/* Red circle */}
      <circle fill="#D71F27" cx="35.2" cy="55.5" r="11.3" />
      {/* Main upward chevron */}
      <polygon fill="#D71F27" points="40.4,1.5 2.7,45.3 2.7,86.8" />
    </svg>
  );
}
