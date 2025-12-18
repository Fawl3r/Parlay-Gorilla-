"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import { AdminSidebar } from './components/AdminSidebar';
import { AdminTopbar } from './components/AdminTopbar';

interface AdminLayoutProps {
  children: React.ReactNode;
}

interface AdminUser {
  id: string;
  email: string;
  username?: string;
  role: string;
  plan: string;
  is_active: boolean;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { user: authUser, loading: authLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [timeRange, setTimeRange] = useState('7d');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [adminLoading, setAdminLoading] = useState(true);
  
  // Skip auth check for login page
  const isLoginPage = pathname === '/admin/login';
  
  // Check for admin token and fetch user info
  useEffect(() => {
    if (isLoginPage) {
      setAdminLoading(false);
      return;
    }
    
    const checkAdminAuth = async () => {
      try {
        const adminToken = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
        
        if (!adminToken) {
          setAdminLoading(false);
          router.push('/admin/login');
          return;
        }
        
        // Verify token and get user info
        try {
          const userData = await api.getCurrentUser();
          setAdminUser({
            id: userData.id,
            email: userData.email,
            username: userData.username,
            role: userData.role,
            plan: userData.plan,
            is_active: userData.is_active,
          });
        } catch (error: any) {
          // Token invalid or expired
          console.error('Admin token verification failed:', error);
          localStorage.removeItem('admin_token');
          router.push('/admin/login');
        }
      } catch (error) {
        console.error('Admin auth check failed:', error);
        router.push('/admin/login');
      } finally {
        setAdminLoading(false);
      }
    };
    
    checkAdminAuth();
  }, [isLoginPage, router]);
  
  // If on login page, render children without layout
  if (isLoginPage) {
    return <>{children}</>;
  }
  
  if (adminLoading || authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-emerald-400 text-xl animate-pulse">Loading...</div>
      </div>
    );
  }
  
  // Use admin user if available, otherwise fall back to auth user
  const user = adminUser || authUser;
  
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

