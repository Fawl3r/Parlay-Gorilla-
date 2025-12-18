"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  BarChart3,
  TrendingUp,
  Ticket,
  DollarSign,
  Globe,
  Flag,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { ParlayGorillaLogo } from '@/components/ParlayGorillaLogo';

interface AdminSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const navItems = [
  { href: '/admin', label: 'Overview', icon: LayoutDashboard },
  { href: '/admin/users', label: 'Users', icon: Users },
  { href: '/admin/usage', label: 'Usage', icon: BarChart3 },
  { href: '/admin/model-performance', label: 'Model Performance', icon: TrendingUp },
  { href: '/admin/parlays', label: 'Parlays', icon: Ticket },
  { href: '/admin/affiliates', label: 'Affiliates', icon: DollarSign },
  { href: '/admin/revenue', label: 'Revenue', icon: DollarSign },
  { href: '/admin/traffic', label: 'Traffic & SEO', icon: Globe },
  { href: '/admin/feature-flags', label: 'Feature Flags', icon: Flag },
  { href: '/admin/logs', label: 'System Logs', icon: FileText },
];

export function AdminSidebar({ isOpen, onToggle }: AdminSidebarProps) {
  const pathname = usePathname();
  
  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-[#111118] border-r border-emerald-900/30 transition-all duration-300 z-40 ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-emerald-900/30">
        {isOpen ? (
          <div className="flex items-center gap-2">
            <ParlayGorillaLogo size="sm" showText={false} />
            <span className="font-bold text-emerald-400">Admin</span>
          </div>
        ) : (
          <ParlayGorillaLogo size="sm" showText={false} />
        )}
        <button
          onClick={onToggle}
          className="p-1 hover:bg-emerald-900/20 rounded-lg transition-colors"
        >
          {isOpen ? (
            <ChevronLeft className="w-5 h-5 text-emerald-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-emerald-400" />
          )}
        </button>
      </div>
      
      {/* Navigation */}
      <nav className="mt-4 px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:bg-emerald-900/10 hover:text-emerald-300'
              }`}
              title={!isOpen ? item.label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {isOpen && <span className="text-sm font-medium">{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      
      {/* Footer */}
      {isOpen && (
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-emerald-900/20 rounded-lg p-3 border border-emerald-900/30">
            <p className="text-xs text-gray-500">Parlay Gorilla Admin</p>
            <p className="text-xs text-emerald-400">v1.0.0</p>
          </div>
        </div>
      )}
    </aside>
  );
}

