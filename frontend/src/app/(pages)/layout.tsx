import { Suspense } from 'react';
import { SidebarDemo } from '@/src/components/sidebardemo';

function SidebarSkeleton() {
  return <div className="w-64 bg-neutral-900" />;
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark flex h-screen overflow-hidden bg-neutral-950">
      <Suspense fallback={<SidebarSkeleton />}>
        <SidebarDemo />
      </Suspense>
      <main className="flex flex-1 flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
}
