import type { ReactNode } from "react";

interface SectionCardProps {
  id?: string;
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionCard({
  id,
  title,
  eyebrow,
  action,
  children,
  className = ""
}: SectionCardProps) {
  return (
    <section id={id} className={`section-card ${className}`}>
      {(title || eyebrow || action) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {eyebrow && (
              <p className="mb-1 font-mono text-[11px] uppercase tracking-normal text-neutral-500">
                {eyebrow}
              </p>
            )}
            {title && <h2 className="text-base font-semibold text-neutral-50">{title}</h2>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
