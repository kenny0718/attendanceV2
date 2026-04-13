<template>
  <Card
    title="外出管理"
    class="break-management-card"
  >
    <!-- 外出原因 -->
    <OutReasonSection 
      :reason-presets="reasonPresets"
      :reason-customs="reasonCustoms"
      :selected-reason="selectedReason"
      :new-custom-reason="newCustomReason"
      @select-reason="$emit('select-reason', $event)"
      @remove-custom-reason="$emit('remove-custom-reason', $event)"
      @add-custom-reason="$emit('add-custom-reason')"
      @update:selected-reason="$emit('update:selected-reason', $event)"
      @update:new-custom-reason="$emit('update:new-custom-reason', $event)"
    />

    <!-- 外出 / 返回打卡 -->
    <OutActionsSection 
      :can-break-out="canBreakOut"
      :can-break-in="canBreakIn"
      :is-on-break="isOnBreak"
      :is-loading="isLoading"
      @break-out="$emit('break-out')"
      @break-in="$emit('break-in')"
    />

    <!-- 今日外出 / 返回紀錄 -->
    <OutLogsSection 
      :break-punches="breakPunches"
      :initial-expanded="isBreakLogsExpanded"
      @edit-note="$emit('edit-note', $event)"
    />
  </Card>
</template>

<script setup>
import Card from '@/components/Card.vue'
import OutReasonSection from './OutReasonSection.vue'
import OutActionsSection from './OutActionsSection.vue'
import OutLogsSection from './OutLogsSection.vue'

// Props - 從 Home.vue 接收數據
const props = defineProps({
  // 外出原因相關
  reasonPresets: {
    type: Array,
    default: () => []
  },
  reasonCustoms: {
    type: Array,
    default: () => []
  },
  selectedReason: {
    type: String,
    default: ''
  },
  newCustomReason: {
    type: String,
    default: ''
  },
  // 外出狀態相關
  canBreakOut: {
    type: Boolean,
    default: false
  },
  canBreakIn: {
    type: Boolean,
    default: false
  },
  isOnBreak: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  // 外出記錄相關
  breakPunches: {
    type: Array,
    default: () => []
  },
  isBreakLogsExpanded: {
    type: Boolean,
    default: false
  }
})

// Emits - 向上傳遞事件
defineEmits([
  'select-reason',
  'remove-custom-reason',
  'add-custom-reason',
  'update:selected-reason',
  'update:new-custom-reason',
  'break-out',
  'break-in',
  'edit-note'
])
</script>

<style scoped>
.break-management-card {
  margin-bottom: 16px;
}
</style>
