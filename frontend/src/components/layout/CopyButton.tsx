"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";
import { copyToClipboard } from "@/lib/formatters";

interface CopyButtonProps {
  value: string;
  label?: string;
  className?: string;
}

export function CopyButton({ value, label = "Copy", className = "btn-ghost" }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const resetTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (resetTimer.current) window.clearTimeout(resetTimer.current);
    };
  }, []);
  return (
    <button
      type="button"
      className={className}
      onClick={() => {
        void copyToClipboard(value).then(() => {
          setCopied(true);
          if (resetTimer.current) window.clearTimeout(resetTimer.current);
          resetTimer.current = window.setTimeout(() => setCopied(false), 1400);
        });
      }}
    >
      {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Copy className="h-4 w-4" aria-hidden="true" />}
      {copied ? "Copied" : label}
    </button>
  );
}
