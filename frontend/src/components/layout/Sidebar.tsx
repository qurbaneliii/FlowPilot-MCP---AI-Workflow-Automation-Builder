import { FileText, GitBranch, Network, ShieldCheck, Terminal } from "lucide-react";

const items = [
  { label: "Builder", icon: GitBranch },
  { label: "Canvas", icon: Network },
  { label: "Approval", icon: ShieldCheck },
  { label: "Reports", icon: FileText },
  { label: "Logs", icon: Terminal }
];

export function Sidebar() {
  return (
    <aside className="hidden border-r border-neutral-800 bg-neutral-950/50 px-2 py-4 xl:block">
      <nav aria-label="Workspace sections" className="sticky top-24 flex flex-col items-center gap-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <a
              key={item.label}
              href={`#${item.label.toLowerCase()}`}
              aria-label={item.label}
              title={item.label}
              className="group grid h-11 w-11 place-items-center rounded-md border border-transparent text-neutral-500 transition hover:border-neutral-800 hover:bg-neutral-900 hover:text-neutral-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300"
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">{item.label}</span>
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
