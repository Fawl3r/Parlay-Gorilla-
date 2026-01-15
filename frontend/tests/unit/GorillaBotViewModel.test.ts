import { describe, expect, it, vi } from 'vitest'

import type { GorillaBotApiClient, GorillaBotState } from '@/components/gorilla-bot/GorillaBotViewModel'
import { GorillaBotViewModel } from '@/components/gorilla-bot/GorillaBotViewModel'

class FakeIdGenerator {
  private counter = 0
  create() {
    this.counter += 1
    return `fake_${this.counter}`
  }
}

function buildState(overrides: Partial<GorillaBotState> = {}): GorillaBotState {
  return {
    isOpen: false,
    messages: [],
    input: '',
    isLoading: false,
    error: null,
    conversationId: null,
    ...overrides,
  }
}

describe('GorillaBotViewModel', () => {
  it('appends messages and updates conversation id', async () => {
    let state = buildState({ input: 'Hello bot' })
    const setState = (next: GorillaBotState) => {
      state = next
    }
    const getState = () => state
    const apiClient: GorillaBotApiClient = {
      gorillaBotChat: vi.fn().mockResolvedValue({
        conversation_id: 'conv_1',
        message_id: 'msg_1',
        reply: 'Hello!',
        citations: [],
      }),
    }

    const viewModel = new GorillaBotViewModel(getState, setState, new FakeIdGenerator() as any, apiClient)
    await viewModel.sendMessage()

    expect(state.isLoading).toBe(false)
    expect(state.conversationId).toBe('conv_1')
    expect(state.messages).toHaveLength(2)
    expect(state.messages[0]?.role).toBe('user')
    expect(state.messages[1]?.role).toBe('assistant')
  })

  it('sets error state on failure', async () => {
    let state = buildState({ input: 'Hello bot' })
    const setState = (next: GorillaBotState) => {
      state = next
    }
    const getState = () => state
    const apiClient: GorillaBotApiClient = {
      gorillaBotChat: vi.fn().mockRejectedValue(new Error('429 too many requests')),
    }

    const viewModel = new GorillaBotViewModel(getState, setState, new FakeIdGenerator() as any, apiClient)
    await viewModel.sendMessage()

    expect(state.isLoading).toBe(false)
    expect(state.error).toContain('429')
  })

  it('toggles dialog open state', () => {
    let state = buildState()
    const setState = (next: GorillaBotState) => {
      state = next
    }
    const getState = () => state
    const apiClient: GorillaBotApiClient = {
      gorillaBotChat: vi.fn(),
    }

    const viewModel = new GorillaBotViewModel(getState, setState, new FakeIdGenerator() as any, apiClient)
    viewModel.setOpen(true)
    expect(state.isOpen).toBe(true)
    viewModel.setOpen(false)
    expect(state.isOpen).toBe(false)
  })
})
