"use client";

import { useAuth } from '@/lib/auth-context';
import { Menu, LogOut, User, Bell } from 'lucide-react';
import { TimeRangeSelector } from './TimeRangeSelector';

interface AdminTopbarProps {
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  onMenuClick: () => void;
}

export function AdminTopbar({ timeRange, onTimeRangeChange, onMenuClick }: AdminTopbarProps) {
  const { user, signOut } = useAuth();
  
  return (
    <header className="h-16 bg-[#111118] border-b border-emerald-900/30 flex items-center justify-between px-6">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors lg:hidden"
        >
          <Menu className="w-5 h-5 text-emerald-400" />
        </button>
        <h1 className="text-lg font-semibold text-white">
          Admin Dashboard
        </h1>
      </div>
      
      {/* Center - Time Range */}
      <TimeRangeSelector value={timeRange} onChange={onTimeRangeChange} />
      
      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notifications placeholder */}
        <button className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors relative">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-500 rounded-full" />
        </button>
        
        {/* User menu */}
        <div className="flex items-center gap-3 pl-4 border-l border-emerald-900/30">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
            <User className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-white">{user?.email}</p>
            <p className="text-xs text-emerald-400">Admin</p>
          </div>
          <button
            onClick={() => signOut()}
            className="p-2 hover:bg-red-900/20 rounded-lg transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>
    </header>
  );
}

