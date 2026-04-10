import { defineStore } from 'pinia'
import { createEventStream } from '@/api/streaming'
import { useAttendanceStore } from '@/stores/attendance'

export const useStreamingStore = defineStore('streaming', {
  state: () => ({
    connectionStatus: 'idle',
    lastEvent: null,
    lastError: null,
    eventCount: 0,
    connectedAt: null,
    systemStatus: null,
    attendanceStatus: null,
    streamHandle: null,
  }),

  getters: {
    isConnected: (state) => state.connectionStatus === 'connected',
    systemStatusLabel: (state) => state.systemStatus?.status || 'unknown',
  },

  actions: {
    connect() {
      if (this.streamHandle || this.connectionStatus === 'connecting') {
        return
      }

      this.connectionStatus = 'connecting'
      this.lastError = null

      try {
        this.streamHandle = createEventStream({
          eventNames: ['system.status.v1', 'attendance.status.v1', 'system.heartbeat.v1'],
          onMessage: (payload, meta = {}) => {
            this.connectionStatus = 'connected'
            this.lastEvent = {
              type: meta.eventType || 'message',
              payload,
              receivedAt: new Date().toISOString(),
            }
            this.eventCount += 1
            if (!this.connectedAt) {
              this.connectedAt = new Date().toISOString()
            }

            if (meta.eventType === 'system.status.v1') {
              this.systemStatus = payload
            }

            if (meta.eventType === 'attendance.status.v1') {
              this.attendanceStatus = payload
              const attendanceStore = useAttendanceStore()
              attendanceStore.applyStreamingStatus(payload)
            }
          },
          onError: () => {
            this.connectionStatus = 'error'
            this.lastError = 'streaming 連線發生錯誤'
          },
        })
      } catch (error) {
        this.connectionStatus = 'error'
        this.lastError = error.message || '無法建立 streaming 連線'
      }
    },

    disconnect() {
      if (this.streamHandle) {
        this.streamHandle.close()
      }

      this.streamHandle = null
      this.connectionStatus = 'idle'
      this.connectedAt = null
      this.systemStatus = null
      this.attendanceStatus = null
    },
  },
})
