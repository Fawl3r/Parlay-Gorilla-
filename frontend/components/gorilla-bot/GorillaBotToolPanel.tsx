"use client"

import { useEffect } from "react"
import { MessageCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { GORILLA_BOT_OPEN_EVENT, type GorillaBotOpenEventDetail } from "@/lib/gorilla-bot/events"

import { GorillaBotMessageList } from "./GorillaBotMessageList"
import { GorillaBotComposer } from "./GorillaBotComposer"
import { useGorillaBotViewModel } from "./GorillaBotViewModel"

type Props = {
  title: string
  subtitle?: string
  suggestedQuestions?: string[]
  className?: string
}

export function GorillaBotToolPanel({ title, subtitle, suggestedQuestions, className }: Props) {
  const { state, setOpen, updateInput, sendMessage, applySuggestion, startNewConversation } =
    useGorillaBotViewModel()

  useEffect(() => {
    const onOpen = (event: Event) => {
      const customEvent = event as CustomEvent<GorillaBotOpenEventDetail>
      const prefill = customEvent.detail?.prefill?.trim()
      if (prefill) applySuggestion(prefill)
      setOpen(true)
    }

    window.addEventListener(GORILLA_BOT_OPEN_EVENT, onOpen)
    return () => window.removeEventListener(GORILLA_BOT_OPEN_EVENT, onOpen)
  }, [setOpen, applySuggestion])

  const bodyContent = (
    <>
      <div className="max-h-[52vh] overflow-y-auto rounded-lg border border-white/10 bg-black/20 p-3">
        <GorillaBotMessageList messages={state.messages} />
      </div>

      <GorillaBotComposer
        input={state.input}
        isLoading={state.isLoading}
        error={state.error}
        onInputChange={updateInput}
        onSend={sendMessage}
        onSuggestion={applySuggestion}
        suggestedQuestions={suggestedQuestions}
      />
    </>
  )

  return (
    <div className={cn("min-w-0", className)}>
      {/* Desktop: always-visible side panel */}
      <div className="hidden lg:flex flex-col gap-4 rounded-xl border border-white/10 bg-black/20 backdrop-blur p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-white">{title}</h3>
            {subtitle ? <p className="text-xs text-white/60 mt-1">{subtitle}</p> : null}
          </div>
          <Button variant="ghost" size="sm" onClick={startNewConversation} className="shrink-0">
            New chat
          </Button>
        </div>
        {bodyContent}
      </div>

      {/* Mobile: bottom sheet */}
      <div className="lg:hidden">
        <Dialog open={state.isOpen} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button
              type="button"
              variant="outline"
              className="w-full border-white/15 bg-white/5 text-white/90 hover:bg-white/10"
            >
              <MessageCircle className="h-4 w-4 mr-2" />
              Ask Gorilla Bot
            </Button>
          </DialogTrigger>
          <DialogContent
            overlayClassName="bg-black/70"
            className={cn(
              "left-0 right-0 bottom-0 top-auto translate-x-0 translate-y-0 max-w-none",
              "rounded-t-2xl rounded-b-none sm:rounded-t-2xl sm:rounded-b-none",
              "border-white/10 bg-black/90 text-white"
            )}
          >
            <div className="flex flex-col gap-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <DialogTitle className="text-sm font-bold text-white">{title}</DialogTitle>
                  {subtitle ? <p className="text-xs text-white/60 mt-1">{subtitle}</p> : null}
                </div>
                <Button variant="ghost" size="sm" onClick={startNewConversation} className="shrink-0">
                  New chat
                </Button>
              </div>
              {bodyContent}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}

