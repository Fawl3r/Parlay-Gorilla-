"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { AdminSidebar } from './components/AdminSidebar';
import { AdminTopbar } from './components/AdminTopbar';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [timeRange, setTimeRange] = useState('7d');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Skip auth check for login page
  const isLoginPage = pathname === '/admin/login';
  
  // Check for admin role (skip for login page)
  // TODO: In production, verify role from backend on each request
  useEffect(() => {
    if (!isLoginPage && !loading && !user) {
      router.push('/admin/login');
    }
  }, [user, loading, router, isLoginPage]);
  
  // If on login page, render children without layout
  if (isLoginPage) {
    return <>{children}</>;
  }
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-emerald-400 text-xl animate-pulse">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return null;
  }
  
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      {/* Sidebar */}
      <AdminSidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      {/* Main content */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        {/* Topbar */}
        <AdminTopbar 
          timeRange={timeRange} 
          onTimeRangeChange={setTimeRange}
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        />
        
        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

