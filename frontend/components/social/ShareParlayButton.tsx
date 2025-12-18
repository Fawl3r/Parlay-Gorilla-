"use client"

import { useState } from "react"
import { socialApi } from "@/lib/social-api"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Copy } from "lucide-react"

type Privacy = "public" | "unlisted" | "private"

export function ShareParlayButton({ parlayId }: { parlayId: string }) {
  const [open, setOpen] = useState(false)
  const [comment, setComment] = useState("")
  const [privacy, setPrivacy] = useState<Privacy>("public")
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleShare = async () => {
    setLoading(true)
    try {
      const result = await socialApi.shareParlay(parlayId, comment.trim() || undefined, privacy)
      const url = `${window.location.origin}${result.share_url}`
      setShareUrl(url)
    } finally {
      setLoading(false)
    }
  }

  const copyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl)
    }
  }

  return (
    <>
      <Button variant="secondary" onClick={() => setOpen(true)}>
        Share Parlay
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Share this parlay</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="comment">Add a note (optional)</Label>
              <Textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Why do you like this parlay?"
              />
            </div>
            <div className="space-y-2">
              <Label>Privacy</Label>
              <Select value={privacy} onValueChange={(value: Privacy) => setPrivacy(value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select privacy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="unlisted">Unlisted</SelectItem>
                  <SelectItem value="private">Private (only you)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {shareUrl && (
              <div className="space-y-2">
                <Label>Share link</Label>
                <div className="flex gap-2">
                  <Input value={shareUrl} readOnly />
                  <Button variant="outline" size="icon" onClick={copyLink}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="flex justify-between gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button onClick={handleShare} disabled={loading}>
              {loading ? "Sharing..." : "Share"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

