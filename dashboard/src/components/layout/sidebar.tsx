import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Activity,
  GitMerge,
  AlertTriangle,
  History,
  TerminalSquare
} from "lucide-react";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Runtime", href: "/runtime", icon: Activity },
  { name: "Prompts", href: "/prompts", icon: History },
  { name: "Canary", href: "/canary", icon: GitMerge },
  { name: "Drift", href: "/drift", icon: AlertTriangle },
  { name: "Eval Proof", href: "/results", icon: Activity }, // Reusing Activity icon or similar
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card/50 backdrop-blur-sm">
      <div className="flex h-16 shrink-0 items-center px-6 border-b">
        <TerminalSquare className="h-6 w-6 text-primary mr-2" />
        <span className="text-lg font-bold tracking-tight">APIS</span>
      </div>
      <div className="flex flex-1 flex-col overflow-y-auto pt-6">
        <nav className="flex-1 space-y-1 px-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors"
                )}
              >
                <item.icon
                  className={cn(
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                    "mr-3 h-5 w-5 flex-shrink-0 transition-colors"
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
