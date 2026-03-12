import type { ReactNode } from "react";

type AppShellProps = {
  sidebar: ReactNode;
  children: ReactNode;
};

export function AppShell({ sidebar, children }: AppShellProps) {
  return (
    <div className="h-screen overflow-hidden bg-slate-100">
      <div className="mx-auto flex h-full max-w-[1680px] gap-4 p-4 lg:gap-6 lg:p-6">
        <aside className="hidden w-[320px] shrink-0 lg:block">{sidebar}</aside>
        <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
