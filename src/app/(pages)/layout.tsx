import NavbarDemo from '@/src/components/navbardemo'
import React from 'react'
import { SidebarDemo } from '@/src/components/sidebardemo';
type Props = { children: React.ReactNode }

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark flex min-h-screen" >
      <SidebarDemo />
      <main className="flex-1 overflow-y-auto bg-gray-1000 p-4">
        {children}
      </main>
    </div>
  );
}