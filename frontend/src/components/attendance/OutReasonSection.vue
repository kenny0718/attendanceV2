<template>
  <div class="break-reason-section">
    <h3 class="subsection-title">外出原因</h3>
    <div class="reason-input-area">
      <!-- 常用原因快速選擇 -->
      <div class="reason-chips">
        <button
          v-for="reason in reasonPresets"
          :key="reason"
          @click="$emit('select-reason', reason)"
          :class="[
            'reason-chip',
            { 'selected': selectedReason === reason }
          ]"
        >
          {{ reason }}
        </button>
      </div>
      
      <!-- 自訂原因 -->
      <div v-if="reasonCustoms.length > 0" class="custom-reasons">
        <button
          v-for="reason in reasonCustoms"
          :key="reason"
          @click="$emit('select-reason', reason)"
          :class="[
            'reason-chip custom',
            { 'selected': selectedReason === reason }
          ]"
        >
          {{ reason }}
          <span 
            @click.stop="$emit('remove-custom-reason', reason)"
            class="remove-btn"
          >
            ✕
          </span>
        </button>
      </div>
      
      <!-- 原因輸入欄 -->
      <input
        :value="selectedReason"
        @input="$emit('update:selected-reason', $event.target.value)"
        type="text"
        class="reason-input"
        placeholder="請輸入外出原因"
        maxlength="50"
      />
      
      <!-- 新增自訂原因 -->
      <div class="add-custom-reason">
        <input
          :value="newCustomReason"
          @input="$emit('update:new-custom-reason', $event.target.value)"
          @keyup.enter="$emit('add-custom-reason')"
          type="text"
          placeholder="新增常用原因..."
          class="custom-input"
          maxlength="20"
        />
        <button
          @click="$emit('add-custom-reason')"
          :disabled="!newCustomReason.trim()"
          class="add-btn"
        >
          ＋新增
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Props - 只接收顯示數據
const props = defineProps({
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
  }
})

// Emits - 只發送事件
defineEmits([
  'select-reason',
  'remove-custom-reason',
  'add-custom-reason',
  'update:selected-reason',
  'update:new-custom-reason'
])
</script>

<style scoped>
.break-reason-section {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--heading);
  margin-bottom: 12px;
}

.reason-input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reason-chips,
.custom-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reason-chip {
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  border: none;
  background: var(--bg-main);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.reason-chip:active {
  transform: scale(0.95);
}

.reason-chip.selected {
  background: var(--primary);
  color: white;
  box-shadow: 0 2px 6px rgba(74, 111, 165, 0.3);
}

.reason-chip.custom {
  background: #EFF6FF;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reason-chip.custom.selected {
  background: var(--secondary);
}

.remove-btn {
  font-size: 14px;
  opacity: 0.7;
  cursor: pointer;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 1;
}

.reason-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.2s;
}

.reason-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.1);
}

.add-custom-reason {
  display: flex;
  gap: 8px;
}

.custom-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 13px;
  transition: all 0.2s;
}

.custom-input:focus {
  outline: none;
  border-color: var(--primary);
}

.add-btn {
  padding: 10px 16px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.add-btn:active {
  background: var(--primary-hover);
  transform: scale(0.98);
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
