"use client"

import type { GorillaBotCitation } from '@/lib/api/types'
import type { GorillaBotUiMessage } from './GorillaBotViewModel'
import { cn } from '@/lib/utils'

type Props = {
  messages: GorillaBotUiMessage[]
}

export function GorillaBotMessageList({ messages }: Props) {
  if (!messages.length) {
    return (
      <div className="text-sm text-muted-foreground">
        Ask Gorilla Bot anything about Parlay Gorilla features, usage limits, or account questions.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div key={message.id} className={cn('rounded-lg px-3 py-2 text-sm', message.role === 'user'
          ? 'bg-primary/15 text-primary-foreground'
          : 'bg-card text-foreground border border-border'
        )}>
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          {message.role === 'assistant' && message.citations?.length ? (
            <GorillaBotCitations citations={message.citations} />
          ) : null}
        </div>
      ))}
    </div>
  )
}

function GorillaBotCitations({ citations }: { citations: GorillaBotCitation[] }) {
  return (
    <div className="mt-3 border-t border-border/60 pt-2 text-xs text-muted-foreground">
      <div className="font-semibold uppercase tracking-wide text-[10px]">Sources</div>
      <ul className="mt-1 space-y-1">
        {citations.map((citation) => (
          <li key={`${citation.title}-${citation.source_path}`}>
            {citation.source_url ? (
              <a
                href={citation.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                {citation.title}
              </a>
            ) : (
              <span>{citation.title}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
