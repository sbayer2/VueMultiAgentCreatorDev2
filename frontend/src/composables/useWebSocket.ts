import { ref, onMounted, onUnmounted } from 'vue'

export interface WebSocketOptions {
  url: string
  protocols?: string | string[]
  reconnect?: boolean
  reconnectDelay?: number
  reconnectAttempts?: number
  heartbeat?: boolean
  heartbeatInterval?: number
  heartbeatMessage?: string
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    protocols,
    reconnect = true,
    reconnectDelay = 3000,
    reconnectAttempts = 5,
    heartbeat = true,
    heartbeatInterval = 30000,
    heartbeatMessage = 'ping'
  } = options

  // State
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const reconnectCount = ref(0)
  const lastError = ref<Event | null>(null)
  const lastMessage = ref<WebSocketMessage | null>(null)

  // Heartbeat
  let heartbeatTimer: NodeJS.Timeout | null = null

  // Message handlers
  const messageHandlers = new Map<string, ((data: any) => void)[]>()

  // Methods
  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    isConnecting.value = true
    lastError.value = null

    try {
      ws.value = new WebSocket(url, protocols)

      ws.value.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectCount.value = 0

        // Start heartbeat
        if (heartbeat) {
          startHeartbeat()
        }

        // Emit connected event
        emit('connected', null)
      }

      ws.value.onclose = (event) => {
        isConnected.value = false
        isConnecting.value = false
        stopHeartbeat()

        // Emit disconnected event
        emit('disconnected', event)

        // Attempt reconnection
        if (reconnect && reconnectCount.value < reconnectAttempts) {
          reconnectCount.value++
          setTimeout(() => {
            connect()
          }, reconnectDelay)
        }
      }

      ws.value.onerror = (error) => {
        lastError.value = error
        isConnecting.value = false

        // Emit error event
        emit('error', error)
      }

      ws.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = {
            type: 'message',
            data: JSON.parse(event.data),
            timestamp: Date.now()
          }

          // Handle heartbeat response
          if (message.data.type === 'pong') {
            return
          }

          lastMessage.value = message

          // Emit message event
          emit('message', message.data)

          // Handle typed messages
          if (message.data.type) {
            emit(message.data.type, message.data)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      isConnecting.value = false
      lastError.value = error as Event
      console.error('WebSocket connection error:', error)
    }
  }

  const disconnect = () => {
    stopHeartbeat()
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
    isConnecting.value = false
  }

  const send = (data: any) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected')
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }

  const on = (event: string, handler: (data: any) => void) => {
    if (!messageHandlers.has(event)) {
      messageHandlers.set(event, [])
    }
    messageHandlers.get(event)!.push(handler)
  }

  const off = (event: string, handler?: (data: any) => void) => {
    if (!messageHandlers.has(event)) {
      return
    }

    if (handler) {
      const handlers = messageHandlers.get(event)!
      const index = handlers.indexOf(handler)
      if (index !== -1) {
        handlers.splice(index, 1)
      }
    } else {
      messageHandlers.delete(event)
    }
  }

  const emit = (event: string, data: any) => {
    const handlers = messageHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      send({ type: 'ping', message: heartbeatMessage })
    }, heartbeatInterval)
  }

  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // Lifecycle
  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    ws,
    isConnected,
    isConnecting,
    reconnectCount,
    lastError,
    lastMessage,

    // Methods
    connect,
    disconnect,
    send,
    on,
    off,
  }
}