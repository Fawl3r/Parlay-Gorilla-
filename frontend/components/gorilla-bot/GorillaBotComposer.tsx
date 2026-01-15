"use client"

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type Props = {
  input: string
  isLoading: boolean
  error: string | null
  onInputChange: (value: string) => void
  onSend: () => void
  onSuggestion: (value: string) => void
}

const SUGGESTED_QUESTIONS = [
  'How do free parlay limits work?',
  'Why am I seeing a paywall?',
  'How do custom parlays get analyzed?',
  'Where can I see my subscription status?',
]

export function GorillaBotComposer({
  input,
  isLoading,
  error,
  onInputChange,
  onSend,
  onSuggestion,
}: Props) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:text-foreground hover:border-primary"
            onClick={() => onSuggestion(question)}
          >
            {question}
          </button>
        ))}
      </div>

      {error ? <div className="text-xs text-red-400">{error}</div> : null}

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Ask Gorilla Bot..."
          className={cn(
            'flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground',
            'focus:outline-none focus:ring-2 focus:ring-primary/50'
          )}
          disabled={isLoading}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              onSend()
            }
          }}
        />
        <Button type="button" onClick={onSend} disabled={isLoading || !input.trim()}>
          {isLoading ? 'Thinking...' : 'Send'}
        </Button>
      </div>
    </div>
  )
}
