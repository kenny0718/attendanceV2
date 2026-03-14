<template>
  <span :class="['status-badge', badgeClass]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: ''
  }
})

const STATUS_MAP = {
  open:              { label: '進行中',   cls: 'badge-open' },
  closed:            { label: '已完成',   cls: 'badge-closed' },
  pending:           { label: '審核中',   cls: 'badge-pending' },
  approved:          { label: '已核准',   cls: 'badge-approved' },
  rejected:          { label: '已拒絕',   cls: 'badge-rejected' },
  missing_punch_out: { label: '缺下班卡', cls: 'badge-missing' }
}

const badgeInfo = computed(() => STATUS_MAP[props.status] || { label: '—', cls: 'badge-unknown' })
const label     = computed(() => badgeInfo.value.label)
const badgeClass = computed(() => badgeInfo.value.cls)
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.badge-open     { background: var(--info-bg);    color: var(--info); }
.badge-closed   { background: var(--success-bg); color: var(--success); }
.badge-pending  { background: var(--warning-bg); color: var(--warning); }
.badge-approved { background: #E8F5E9;           color: #1B5E20; }
.badge-rejected { background: var(--error-bg);   color: var(--error); }
.badge-missing  { background: #FFF3E0;           color: #E65100; }
.badge-unknown  { background: var(--border-light); color: var(--text-secondary); }
</style>
