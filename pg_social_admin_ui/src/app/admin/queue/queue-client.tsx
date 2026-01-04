
"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { AdminPageHeader } from "@/components/admin/AdminPageHeader";
import { AdminPageShell } from "@/components/admin/AdminPageShell";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

import { BulkScheduleDialog } from "@/app/admin/queue/components/BulkScheduleDialog";
import { CreatePostDialog } from "@/app/admin/queue/components/CreatePostDialog";
import { PostManageDialog } from "@/app/admin/queue/components/PostManageDialog";
import { PostQueueFiltersBar } from "@/app/admin/queue/components/PostQueueFilters";
import { PostQueueTable } from "@/app/admin/queue/components/PostQueueTable";
import { usePostQueueViewModel } from "@/app/admin/queue/usePostQueueViewModel";

export function QueueClientPage() {
  const searchParams = useSearchParams();
  const highlightPostId = searchParams.get("highlight");
  const { state, visiblePosts, actions, refresh } = usePostQueueViewModel();
  
  // Refresh queue when navigating with highlight parameter (e.g., after generating a post)
  useEffect(() => {
    if (highlightPostId) {
      // Refresh to ensure the new post is loaded
      void refresh();
      // Clear the highlight parameter from URL after a short delay
      const timer = setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.delete("highlight");
        window.history.replaceState({}, "", url.toString());
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [highlightPostId, refresh]);
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});

  const selectedIds = useMemo(() => Object.keys(rowSelection).filter((k) => rowSelection[k]), [rowSelection]);

  const [createOpen, setCreateOpen] = useState(false);
  const [bulkScheduleOpen, setBulkScheduleOpen] = useState(false);
  const [bulkApproveConfirmOpen, setBulkApproveConfirmOpen] = useState(false);

  const [manageId, setManageId] = useState<string | null>(null);
  const activePost = useMemo(() => visiblePosts.find((p) => p.id === manageId) || null, [manageId, visiblePosts]);

  const isMutatingActive = !!(activePost && state.mutatingPostIds.has(activePost.id));

  async function bulkApprove() {
    await actions.bulkApprove(selectedIds);
    setRowSelection({});
  }

  async function bulkSchedule(payload: { scheduled_for: string; tier: string }) {
    await actions.bulkSchedule(selectedIds, payload);
    setRowSelection({});
  }

  return (
    <AdminPageShell>
      <AdminPageHeader
        title="Post Queue"
        description="Create drafts, approve content, and schedule posts for the worker."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {selectedIds.length ? (
              <>
                <Button variant="outline" onClick={() => setBulkScheduleOpen(true)}>
                  Schedule selected…
                </Button>
                <Button onClick={() => setBulkApproveConfirmOpen(true)}>Approve selected</Button>
              </>
            ) : null}
          </div>
        }
      />

      <PostQueueFiltersBar
        filters={state.filters}
        onChange={actions.setFilters}
        onRefresh={refresh}
        onCreate={() => setCreateOpen(true)}
        loading={state.loading}
        visibleCount={visiblePosts.length}
        totalCount={state.posts.length}
        selectedCount={selectedIds.length}
      />

      <PostQueueTable
        posts={visiblePosts}
        loading={state.loading}
        error={state.error}
        rowSelection={rowSelection}
        onRowSelectionChange={setRowSelection}
        onManage={(id) => setManageId(id)}
      />

      {createOpen ? (
        <CreatePostDialog open={createOpen} creating={state.creating} onOpenChange={setCreateOpen} onCreate={actions.createPost} />
      ) : null}

      {bulkScheduleOpen ? (
        <BulkScheduleDialog
          open={bulkScheduleOpen}
          count={selectedIds.length}
          onOpenChange={setBulkScheduleOpen}
          onSchedule={bulkSchedule}
        />
      ) : null}

      <ConfirmDialog
        open={bulkApproveConfirmOpen}
        onOpenChange={setBulkApproveConfirmOpen}
        title={`Approve ${selectedIds.length} selected post(s)?`}
        description="This will run the compliance checks. Failed approvals will be skipped."
        confirmText="Approve"
        onConfirm={bulkApprove}
      />

      {manageId ? (
        <PostManageDialog
          key={`${manageId}:${activePost?.updated_at ?? ""}:${activePost?.image_url ?? ""}`}
          open
          post={activePost}
          isMutating={isMutatingActive}
          onOpenChange={(open) => (open ? null : setManageId(null))}
          onSave={actions.patchPost}
          onApprove={actions.approvePost}
          onSchedule={actions.schedulePost}
          onRetry={actions.retryPost}
          onPostNow={actions.postNow}
          onRegenerateCopy={actions.regenerateCopy}
          onRegenerateImage={actions.regenerateImage}
          onDelete={actions.deletePost}
        />
      ) : null}
    </AdminPageShell>
  );
}
