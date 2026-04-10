const STREAM_PATH = '/v1/streaming/events'

function resolveStreamUrl(path = STREAM_PATH) {
  const apiBase = import.meta.env.VITE_API_BASE || '/api'
  const origin = window.location.origin
  return new URL(`${apiBase}${path}`, origin).toString()
}

function parseEventData(raw) {
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

export function createEventStream({
  path = STREAM_PATH,
  onMessage,
  onError,
  withCredentials = false,
  eventNames = []
} = {}) {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('缺少 token，無法建立 streaming 連線')
  }

  const url = new URL(resolveStreamUrl(path))
  url.searchParams.set('access_token', token)

  const eventSource = new EventSource(url.toString(), { withCredentials })

  eventSource.onmessage = (event) => {
    if (!onMessage) return
    onMessage(parseEventData(event.data), { eventType: 'message' })
  }

  eventNames.forEach((eventName) => {
    eventSource.addEventListener(eventName, (event) => {
      if (!onMessage) return
      onMessage(parseEventData(event.data), { eventType: eventName })
    })
  })

  eventSource.onerror = (error) => {
    if (onError) {
      onError(error)
    }
  }

  return {
    source: eventSource,
    close: () => eventSource.close(),
  }
}
