import { useCallback, useMemo, useRef, useState } from 'react'
import type { GorillaBotChatResponse, GorillaBotCitation } from '@/lib/api/types'
import { api } from '@/lib/api'

export type GorillaBotRole = 'user' | 'assistant'

export interface GorillaBotUiMessage {
  id: string
  role: GorillaBotRole
  content: string
  citations?: GorillaBotCitation[] | null
}

export interface GorillaBotState {
  isOpen: boolean
  messages: GorillaBotUiMessage[]
  input: string
  isLoading: boolean
  error: string | null
  conversationId: string | null
}

export interface GorillaBotApiClient {
  gorillaBotChat: (request: { message: string; conversation_id?: string }) => Promise<GorillaBotChatResponse>
}

export class GorillaBotIdGenerator {
  create(): string {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID()
    }
    return `gb_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  }
}

export class GorillaBotViewModel {
  constructor(
    private readonly getState: () => GorillaBotState,
    private readonly setState: (next: GorillaBotState) => void,
    private readonly idGenerator: GorillaBotIdGenerator,
    private readonly apiClient: GorillaBotApiClient
  ) {}

  setOpen(isOpen: boolean) {
    const state = this.getState()
    this.setState({ ...state, isOpen, error: null })
  }

  updateInput(value: string) {
    const state = this.getState()
    this.setState({ ...state, input: value })
  }

  async sendMessage() {
    const state = this.getState()
    const message = state.input.trim()
    if (!message || state.isLoading) return

    const userMessage: GorillaBotUiMessage = {
      id: this.idGenerator.create(),
      role: 'user',
      content: message,
    }

    this.setState({
      ...state,
      input: '',
      isLoading: true,
      error: null,
      messages: [...state.messages, userMessage],
    })

    try {
      const response = await this.apiClient.gorillaBotChat({
        message,
        conversation_id: state.conversationId ?? undefined,
      })
      this.handleResponse(response)
    } catch (error: any) {
      const messageText = error?.message || 'Unable to reach Gorilla Bot.'
      const next = this.getState()
      this.setState({ ...next, isLoading: false, error: messageText })
    }
  }

  applySuggestion(text: string) {
    const state = this.getState()
    this.setState({ ...state, input: text })
  }

  startNewConversation() {
    const state = this.getState()
    this.setState({
      ...state,
      messages: [],
      conversationId: null,
      error: null,
    })
  }

  private handleResponse(response: GorillaBotChatResponse) {
    const state = this.getState()
    const assistantMessage: GorillaBotUiMessage = {
      id: response.message_id,
      role: 'assistant',
      content: response.reply,
      citations: response.citations,
    }
    this.setState({
      ...state,
      isLoading: false,
      conversationId: response.conversation_id,
      messages: [...state.messages, assistantMessage],
    })
  }
}

const defaultState: GorillaBotState = {
  isOpen: false,
  messages: [],
  input: '',
  isLoading: false,
  error: null,
  conversationId: null,
}

export function useGorillaBotViewModel() {
  const [state, setState] = useState<GorillaBotState>(defaultState)
  const stateRef = useRef(state)
  stateRef.current = state

  const viewModel = useMemo(() => {
    const getState = () => stateRef.current
    const setter = (next: GorillaBotState) => setState(next)
    return new GorillaBotViewModel(getState, setter, new GorillaBotIdGenerator(), api)
  }, [])

  const setOpen = useCallback((open: boolean) => viewModel.setOpen(open), [viewModel])
  const updateInput = useCallback((value: string) => viewModel.updateInput(value), [viewModel])
  const sendMessage = useCallback(() => viewModel.sendMessage(), [viewModel])
  const applySuggestion = useCallback((text: string) => viewModel.applySuggestion(text), [viewModel])
  const startNewConversation = useCallback(() => viewModel.startNewConversation(), [viewModel])

  return { state, setOpen, updateInput, sendMessage, applySuggestion, startNewConversation }
}
