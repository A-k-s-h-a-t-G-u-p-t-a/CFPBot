import { SidebarDemo } from '@/src/components/sidebardemo';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark flex h-screen overflow-hidden bg-neutral-950">
      <SidebarDemo />
      <main className="flex flex-1 flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
}
