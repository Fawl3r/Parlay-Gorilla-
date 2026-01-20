"use client"

import { useState } from "react"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { getCopy, getCopyObject } from "@/lib/content"
import { CheckCircle2, XCircle } from "lucide-react"

interface FirstParlayConfidenceModalProps {
  open: boolean
  onClose: () => void
  onDontShowAgain: () => void
}

const STORAGE_KEY = "parlay_gorilla_first_parlay_confidence_seen"

export function FirstParlayConfidenceModal({
  open,
  onClose,
  onDontShowAgain,
}: FirstParlayConfidenceModalProps) {
  const [dontShowAgain, setDontShowAgain] = useState(false)

  const handleClose = () => {
    if (dontShowAgain) {
      localStorage.setItem(STORAGE_KEY, "true")
      onDontShowAgain()
    }
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl">
            {getCopy("confidence.firstParlay.title")}
          </DialogTitle>
          <DialogDescription className="text-base">
            {getCopy("confidence.firstParlay.subtitle")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <p className="text-sm text-foreground/90">
              {getCopy("confidence.firstParlay.explanation")}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                <h4 className="font-semibold">
                  {getCopy("confidence.firstParlay.winProbabilityLabel")}
                </h4>
              </div>
              <p className="text-sm text-muted-foreground">
                {getCopy("confidence.firstParlay.winProbabilityDesc")}
              </p>
            </div>

            <div className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-amber-400" />
                <h4 className="font-semibold">
                  {getCopy("confidence.firstParlay.confidenceLabel")}
                </h4>
              </div>
              <p className="text-sm text-muted-foreground">
                {getCopy("confidence.firstParlay.confidenceDesc")}
              </p>
            </div>
          </div>

          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 space-y-2">
            <h4 className="font-semibold text-emerald-100">
              {getCopy("confidence.firstParlay.howToUse")}
            </h4>
            <ul className="space-y-1 text-sm text-foreground/90">
              <li>• {getCopy("confidence.firstParlay.tip1")}</li>
              <li>• {getCopy("confidence.firstParlay.tip2")}</li>
              <li>• {getCopy("confidence.firstParlay.tip3")}</li>
            </ul>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="dont-show-again"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <label 
              htmlFor="dont-show-again" 
              className="text-sm text-muted-foreground cursor-pointer"
            >
              {getCopy("confidence.firstParlay.dontShowAgain")}
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button onClick={handleClose} className="min-w-[100px]">
            {getCopy("confidence.firstParlay.cta")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function shouldShowFirstParlayModal(): boolean {
  if (typeof window === "undefined") return false
  return localStorage.getItem(STORAGE_KEY) !== "true"
}
