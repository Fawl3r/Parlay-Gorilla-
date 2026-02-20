"use client"

import { useEffect } from 'react'
import { MessageCircle } from 'lucide-react'
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { GorillaBotMessageList } from './GorillaBotMessageList'
import { GorillaBotComposer } from './GorillaBotComposer'
import { useGorillaBotViewModel } from './GorillaBotViewModel'
import { GORILLA_BOT_OPEN_EVENT, type GorillaBotOpenEventDetail } from '@/lib/gorilla-bot/events'

export function GorillaBotWidget() {
  const { state, setOpen, updateInput, sendMessage, applySuggestion, startNewConversation } =
    useGorillaBotViewModel()

  useEffect(() => {
    const onOpen = (event: Event) => {
      const customEvent = event as CustomEvent<GorillaBotOpenEventDetail>
      const prefill = customEvent.detail?.prefill?.trim()
      setOpen(true)
      if (prefill) applySuggestion(prefill)
    }

    window.addEventListener(GORILLA_BOT_OPEN_EVENT, onOpen)
    return () => window.removeEventListener(GORILLA_BOT_OPEN_EVENT, onOpen)
  }, [setOpen, applySuggestion])

  return (
    <div className="fixed bottom-24 right-4 z-40">
      <Dialog open={state.isOpen} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button className="h-12 w-12 rounded-full shadow-lg" aria-label="Open Gorilla Bot">
            <MessageCircle className="h-5 w-5" />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-xl">
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle>Gorilla Bot</DialogTitle>
              <p className="text-xs text-muted-foreground">Account-aware help for Parlay Gorilla.</p>
            </div>
            <Button variant="ghost" size="sm" onClick={startNewConversation}>
              New chat
            </Button>
          </div>

          <div className="max-h-[50vh] overflow-y-auto rounded-lg border border-border bg-background p-3">
            <GorillaBotMessageList messages={state.messages} />
          </div>

          <GorillaBotComposer
            input={state.input}
            isLoading={state.isLoading}
            error={state.error}
            onInputChange={updateInput}
            onSend={sendMessage}
            onSuggestion={applySuggestion}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
