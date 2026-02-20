"use client";

import { useEffect, useState } from 'react';
import { adminApi, User, UsersListResponse } from '@/lib/admin-api';
import { Search, ChevronLeft, ChevronRight, MoreVertical, Shield, ShieldOff, UserCog, Crown, Calendar } from 'lucide-react';

type UserRole = 'user' | 'mod' | 'admin';
type UserPlan = 'free' | 'standard' | 'elite';

export default function AdminUsersPage() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [planFilter, setPlanFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [updateLoading, setUpdateLoading] = useState<string | null>(null);
  const [grantingSubscription, setGrantingSubscription] = useState<string | null>(null);
  const [subscriptionModalOpen, setSubscriptionModalOpen] = useState<string | null>(null);
  const [subscriptionPlan, setSubscriptionPlan] = useState<UserPlan>('elite');
  const [subscriptionDuration, setSubscriptionDuration] = useState<number>(30);
  const [isLifetime, setIsLifetime] = useState(false);

  async function fetchUsers() {
    try {
      setLoading(true);
      const params: any = { page, pageSize };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      if (planFilter) params.plan = planFilter;
      if (activeFilter) params.isActive = activeFilter === 'active';
      
      const response: UsersListResponse = await adminApi.getUsers(params);
      setUsers(response?.users ?? []);
      setTotal(response?.total ?? 0);
      setTotalPages(response?.total_pages ?? 1);
    } catch (err: any) {
      console.error('Failed to fetch users:', err);
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, planFilter, activeFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        fetchUsers();
      } else {
        setPage(1);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  async function handleUpdateUser(userId: string, updates: { role?: string; plan?: string; is_active?: boolean }) {
    try {
      setUpdateLoading(userId);
      await adminApi.updateUser(userId, updates);
      await fetchUsers();
      setEditingUser(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user');
    } finally {
      setUpdateLoading(null);
    }
  }

  async function handleGrantSubscription(userId: string) {
    try {
      setGrantingSubscription(userId);
      await adminApi.manualUpgrade(userId, subscriptionPlan, subscriptionDuration, isLifetime);
      alert(`Successfully granted ${isLifetime ? 'lifetime' : `${subscriptionDuration}-day`} ${subscriptionPlan} subscription`);
      await fetchUsers();
      setSubscriptionModalOpen(null);
      setIsLifetime(false);
      setSubscriptionDuration(30);
      setSubscriptionPlan('elite');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to grant subscription');
    } finally {
      setGrantingSubscription(null);
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'mod':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getPlanBadgeColor = (plan: string) => {
    switch (plan) {
      case 'elite':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'standard':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">User Management</h1>
        <p className="text-gray-400 mt-1">
          View and manage all registered users
        </p>
      </div>

      {/* Filters */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by email or username..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>

          {/* Role filter */}
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value="">All Roles</option>
            <option value="user">User</option>
            <option value="mod">Mod</option>
            <option value="admin">Admin</option>
          </select>

          {/* Plan filter */}
          <select
            value={planFilter}
            onChange={(e) => setPlanFilter(e.target.value)}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value="">All Plans</option>
            <option value="free">Free</option>
            <option value="standard">Standard</option>
            <option value="elite">Elite</option>
          </select>

          {/* Active filter */}
          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Users table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#0a0a0f]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Plan
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Joined
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-emerald-900/20">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-4">
                      <div className="h-4 bg-emerald-900/20 rounded w-48" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-emerald-900/20 rounded w-16" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-emerald-900/20 rounded w-16" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-6 bg-emerald-900/20 rounded w-16" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-4 bg-emerald-900/20 rounded w-24" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-4 bg-emerald-900/20 rounded w-24" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="h-8 bg-emerald-900/20 rounded w-8 ml-auto" />
                    </td>
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id} className="hover:bg-emerald-900/5">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-white font-medium">{user.email}</div>
                        {user.username && (
                          <div className="text-gray-500 text-sm">@{user.username}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeColor(user.role)}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPlanBadgeColor(user.plan)}`}>
                        {user.plan}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.is_active
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {user.last_login
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4 text-right relative">
                      <button
                        onClick={() => setEditingUser(editingUser === user.id ? null : user.id)}
                        className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors"
                        disabled={updateLoading === user.id}
                      >
                        {updateLoading === user.id ? (
                          <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <MoreVertical className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                      
                      {/* Actions dropdown */}
                      {editingUser === user.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-[#1a1a24] border border-emerald-900/30 rounded-lg shadow-xl z-10">
                          <div className="py-1">
                            {/* Role actions */}
                            <div className="px-3 py-2 text-xs text-gray-500 uppercase">Role</div>
                            {(['user', 'mod', 'admin'] as UserRole[]).map((role) => (
                              <button
                                key={role}
                                onClick={() => handleUpdateUser(user.id, { role })}
                                disabled={user.role === role}
                                className={`w-full px-4 py-2 text-left text-sm hover:bg-emerald-900/20 flex items-center gap-2 ${
                                  user.role === role ? 'text-emerald-400' : 'text-gray-300'
                                }`}
                              >
                                <Shield className="w-4 h-4" />
                                Set as {role}
                              </button>
                            ))}
                            
                            <div className="border-t border-emerald-900/20 my-1" />
                            
                            {/* Plan actions */}
                            <div className="px-3 py-2 text-xs text-gray-500 uppercase">Plan</div>
                            {(['free', 'standard', 'elite'] as UserPlan[]).map((plan) => (
                              <button
                                key={plan}
                                onClick={() => handleUpdateUser(user.id, { plan })}
                                disabled={user.plan === plan}
                                className={`w-full px-4 py-2 text-left text-sm hover:bg-emerald-900/20 flex items-center gap-2 ${
                                  user.plan === plan ? 'text-emerald-400' : 'text-gray-300'
                                }`}
                              >
                                <UserCog className="w-4 h-4" />
                                Set to {plan}
                              </button>
                            ))}
                            
                            <div className="border-t border-emerald-900/20 my-1" />
                            
                            {/* Grant Subscription */}
                            <button
                              onClick={() => {
                                setSubscriptionModalOpen(user.id);
                                setSubscriptionPlan(user.plan === 'free' ? 'elite' : user.plan as UserPlan);
                              }}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-emerald-900/20 flex items-center gap-2 text-emerald-400"
                            >
                              <Crown className="w-4 h-4" />
                              Grant Subscription
                            </button>
                            
                            <div className="border-t border-emerald-900/20 my-1" />
                            
                            {/* Active toggle */}
                            <button
                              onClick={() => handleUpdateUser(user.id, { is_active: !user.is_active })}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-emerald-900/20 flex items-center gap-2 text-gray-300"
                            >
                              {user.is_active ? (
                                <>
                                  <ShieldOff className="w-4 h-4 text-red-400" />
                                  <span className="text-red-400">Deactivate</span>
                                </>
                              ) : (
                                <>
                                  <Shield className="w-4 h-4 text-emerald-400" />
                                  <span className="text-emerald-400">Activate</span>
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {/* Subscription Grant Modal */}
                      {subscriptionModalOpen === user.id && (
                        <div 
                          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                          onClick={(e) => {
                            if (e.target === e.currentTarget) {
                              setSubscriptionModalOpen(null);
                            }
                          }}
                        >
                          <div 
                            className="bg-[#1a1a24] border border-emerald-900/30 rounded-xl p-6 max-w-md w-full shadow-2xl"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                              <Crown className="w-5 h-5 text-emerald-400" />
                              Grant Subscription
                            </h3>
                            <p className="text-gray-400 text-sm mb-6">
                              Create a subscription for {user.email}
                            </p>
                            
                            <div className="space-y-4">
                              {/* Plan Selection */}
                              <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Plan</label>
                                <div className="grid grid-cols-2 gap-2">
                                  {(['standard', 'elite'] as UserPlan[]).map((plan) => (
                                    <button
                                      key={plan}
                                      onClick={() => setSubscriptionPlan(plan)}
                                      className={`px-4 py-2 rounded-lg border transition-colors ${
                                        subscriptionPlan === plan
                                          ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                                          : 'border-emerald-900/30 text-gray-300 hover:border-emerald-500/50'
                                      }`}
                                    >
                                      {plan.charAt(0).toUpperCase() + plan.slice(1)}
                                    </button>
                                  ))}
                                </div>
                              </div>
                              
                              {/* Lifetime Toggle */}
                              <div>
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={isLifetime}
                                    onChange={(e) => setIsLifetime(e.target.checked)}
                                    className="w-4 h-4 rounded border-emerald-900/30 bg-[#0a0a0f] text-emerald-500 focus:ring-emerald-500"
                                  />
                                  <span className="text-sm text-gray-300">Lifetime Subscription</span>
                                </label>
                              </div>
                              
                              {/* Duration Selection (if not lifetime) */}
                              {!isLifetime && (
                                <div>
                                  <label className="block text-sm font-medium text-gray-300 mb-2">Duration (Days)</label>
                                  <div className="grid grid-cols-4 gap-2">
                                    {[30, 60, 90, 365].map((days) => (
                                      <button
                                        key={days}
                                        onClick={() => setSubscriptionDuration(days)}
                                        className={`px-3 py-2 rounded-lg border transition-colors text-sm ${
                                          subscriptionDuration === days
                                            ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                                            : 'border-emerald-900/30 text-gray-300 hover:border-emerald-500/50'
                                        }`}
                                      >
                                        {days}
                                      </button>
                                    ))}
                                  </div>
                                  <input
                                    type="number"
                                    min="1"
                                    value={subscriptionDuration}
                                    onChange={(e) => setSubscriptionDuration(parseInt(e.target.value) || 30)}
                                    className="mt-2 w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-emerald-500/50"
                                    placeholder="Custom days"
                                  />
                                </div>
                              )}
                              
                              {/* Summary */}
                              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                                <p className="text-sm text-emerald-400">
                                  <strong>Summary:</strong> Grant {subscriptionPlan.charAt(0).toUpperCase() + subscriptionPlan.slice(1)} plan
                                  {isLifetime ? ' (Lifetime)' : ` for ${subscriptionDuration} days`}
                                </p>
                              </div>
                              
                              {/* Actions */}
                              <div className="flex gap-3 pt-2">
                                <button
                                  onClick={() => {
                                    setSubscriptionModalOpen(null);
                                    setIsLifetime(false);
                                    setSubscriptionDuration(30);
                                  }}
                                  className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
                                  disabled={grantingSubscription === user.id}
                                >
                                  Cancel
                                </button>
                                <button
                                  onClick={() => handleGrantSubscription(user.id)}
                                  disabled={grantingSubscription === user.id}
                                  className="flex-1 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                  {grantingSubscription === user.id ? (
                                    <>
                                      <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                                      Granting...
                                    </>
                                  ) : (
                                    <>
                                      <Crown className="w-4 h-4" />
                                      Grant Subscription
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-emerald-900/20 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} users
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5 text-gray-400" />
            </button>
            <span className="text-gray-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
              className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

