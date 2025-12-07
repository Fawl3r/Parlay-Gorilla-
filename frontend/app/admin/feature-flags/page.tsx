"use client";

import { useEffect, useState } from 'react';
import { adminApi, FeatureFlag } from '@/lib/admin-api';
import {
  Flag,
  Plus,
  Edit2,
  Trash2,
  ToggleLeft,
  ToggleRight,
  X,
  Save,
} from 'lucide-react';

export default function AdminFeatureFlagsPage() {
  const [loading, setLoading] = useState(true);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingFlag, setEditingFlag] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    description: '',
    enabled: false,
    category: '',
  });

  async function fetchFlags() {
    try {
      setLoading(true);
      const data = await adminApi.getFeatureFlags();
      setFlags(data);
    } catch (err: any) {
      console.error('Failed to fetch feature flags:', err);
      setError(err.message || 'Failed to load feature flags');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchFlags();
  }, []);

  async function handleToggle(key: string) {
    try {
      setActionLoading(key);
      await adminApi.toggleFeatureFlag(key);
      await fetchFlags();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle flag');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleCreate() {
    try {
      setActionLoading('create');
      await adminApi.createFeatureFlag({
        key: formData.key,
        name: formData.name || formData.key,
        description: formData.description,
        enabled: formData.enabled,
        category: formData.category || undefined,
      });
      setShowCreateModal(false);
      setFormData({ key: '', name: '', description: '', enabled: false, category: '' });
      await fetchFlags();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || 'Failed to create flag');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleUpdate(key: string) {
    try {
      setActionLoading(key);
      await adminApi.updateFeatureFlag(key, {
        name: formData.name,
        description: formData.description,
        category: formData.category || undefined,
      });
      setEditingFlag(null);
      await fetchFlags();
    } catch (err: any) {
      alert(err.message || 'Failed to update flag');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(key: string) {
    if (!confirm(`Are you sure you want to delete the flag "${key}"?`)) {
      return;
    }
    
    try {
      setActionLoading(key);
      await adminApi.deleteFeatureFlag(key);
      await fetchFlags();
    } catch (err: any) {
      alert(err.message || 'Failed to delete flag');
    } finally {
      setActionLoading(null);
    }
  }

  function startEdit(flag: FeatureFlag) {
    setEditingFlag(flag.key);
    setFormData({
      key: flag.key,
      name: flag.name || '',
      description: flag.description || '',
      enabled: flag.enabled,
      category: flag.category || '',
    });
  }

  const getCategoryColor = (category: string | undefined) => {
    switch (category) {
      case 'beta':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'premium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'experimental':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6 text-center">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => fetchFlags()}
          className="mt-4 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Feature Flags</h1>
          <p className="text-gray-400 mt-1">
            Control feature availability across the platform
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Flag
        </button>
      </div>

      {/* Flags table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#0a0a0f]">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Flag
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-emerald-900/20">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-6 py-4">
                    <div className="h-4 bg-emerald-900/20 rounded w-32" />
                    <div className="h-3 bg-emerald-900/20 rounded w-24 mt-1" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-4 bg-emerald-900/20 rounded w-48" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="h-6 bg-emerald-900/20 rounded w-16 mx-auto" />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="h-6 bg-emerald-900/20 rounded w-16 mx-auto" />
                  </td>
                  <td className="px-6 py-4">
                    <div className="h-8 bg-emerald-900/20 rounded w-24 ml-auto" />
                  </td>
                </tr>
              ))
            ) : flags.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  No feature flags configured
                </td>
              </tr>
            ) : (
              flags.map((flag) => (
                <tr key={flag.key} className="hover:bg-emerald-900/5">
                  <td className="px-6 py-4">
                    {editingFlag === flag.key ? (
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="bg-[#0a0a0f] border border-emerald-900/30 rounded px-2 py-1 text-white w-full"
                        placeholder="Display name"
                      />
                    ) : (
                      <>
                        <div className="text-white font-medium">{flag.name || flag.key}</div>
                        <div className="text-gray-500 text-sm font-mono">{flag.key}</div>
                      </>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {editingFlag === flag.key ? (
                      <input
                        type="text"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="bg-[#0a0a0f] border border-emerald-900/30 rounded px-2 py-1 text-white w-full"
                        placeholder="Description"
                      />
                    ) : (
                      <span className="text-gray-400">{flag.description || '-'}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {editingFlag === flag.key ? (
                      <select
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="bg-[#0a0a0f] border border-emerald-900/30 rounded px-2 py-1 text-white"
                      >
                        <option value="">Feature</option>
                        <option value="beta">Beta</option>
                        <option value="premium">Premium</option>
                        <option value="experimental">Experimental</option>
                      </select>
                    ) : (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getCategoryColor(flag.category)}`}>
                        {flag.category || 'feature'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => handleToggle(flag.key)}
                      disabled={actionLoading === flag.key}
                      className="inline-flex items-center"
                    >
                      {actionLoading === flag.key ? (
                        <div className="w-6 h-6 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                      ) : flag.enabled ? (
                        <ToggleRight className="w-8 h-8 text-emerald-400" />
                      ) : (
                        <ToggleLeft className="w-8 h-8 text-gray-500" />
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {editingFlag === flag.key ? (
                        <>
                          <button
                            onClick={() => handleUpdate(flag.key)}
                            disabled={actionLoading === flag.key}
                            className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors"
                          >
                            <Save className="w-4 h-4 text-emerald-400" />
                          </button>
                          <button
                            onClick={() => setEditingFlag(null)}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                          >
                            <X className="w-4 h-4 text-gray-400" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => startEdit(flag)}
                            className="p-2 hover:bg-emerald-900/20 rounded-lg transition-colors"
                          >
                            <Edit2 className="w-4 h-4 text-gray-400" />
                          </button>
                          <button
                            onClick={() => handleDelete(flag.key)}
                            disabled={actionLoading === flag.key}
                            className="p-2 hover:bg-red-900/20 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4 text-red-400" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#111118] border border-emerald-900/30 rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Create Feature Flag</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 hover:bg-gray-800 rounded"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Key (required)</label>
                <input
                  type="text"
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                  className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
                  placeholder="my_feature_flag"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
                  placeholder="My Feature Flag"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50 resize-none"
                  rows={3}
                  placeholder="What does this flag control?"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="">Feature</option>
                  <option value="beta">Beta</option>
                  <option value="premium">Premium</option>
                  <option value="experimental">Experimental</option>
                </select>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="rounded border-emerald-900/30 bg-[#0a0a0f] text-emerald-500 focus:ring-emerald-500"
                />
                <label htmlFor="enabled" className="text-sm text-gray-300">Enable immediately</label>
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!formData.key || actionLoading === 'create'}
                className="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionLoading === 'create' ? 'Creating...' : 'Create Flag'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

