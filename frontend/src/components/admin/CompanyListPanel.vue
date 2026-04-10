<template>
  <PageCard>
    <AdminSectionHeader
      title="公司列表"
      align="between"
      iconPath="M4 6h16M4 10h16M4 14h16M4 18h16"
    >
      <template #actions>
        <router-link to="/admin/onboarding" class="btn-link">前往新公司開通</router-link>
        <button class="btn-refresh" :disabled="loading" title="重新整理" @click="$emit('reload')">
          <svg :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </template>
    </AdminSectionHeader>

    <div v-if="loading" class="state-loading"><div class="spinner"></div><span>載入中…</span></div>
    <AdminStateBox
      v-else-if="error"
      variant="error"
      title="載入失敗"
      :message="error"
      iconPath="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
    <AdminStateBox
      v-else-if="companies.length === 0"
      variant="empty"
      title="尚無公司"
      message="目前尚未建立任何公司。"
      iconPath="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
    >
      <router-link to="/admin/onboarding" class="btn-link inline-link">前往新公司開通</router-link>
    </AdminStateBox>
    <div v-else class="list-stack">
      <button
        v-for="company in companies"
        :key="company.id"
        type="button"
        class="company-item"
        :class="{ selected: selectedCompanyId === company.id }"
        @click="$emit('select', company)"
      >
        <div class="company-head">
          <div class="company-title-block">
            <p class="company-name">{{ company.name }}</p>
            <div class="company-meta-inline">
              <span class="company-id">ID: {{ company.id }}</span>
              <span class="meta-dot">•</span>
              <span class="company-created-at">建立時間：{{ formatDate(company.created_at) }}</span>
            </div>
          </div>
          <span :class="company.is_active ? 'badge-active' : 'badge-inactive'">{{ company.is_active ? '啟用' : '停用' }}</span>
        </div>
      </button>
      <p class="total-count">共 {{ companies.length }} 間公司</p>
    </div>
  </PageCard>
</template>

<script setup>
import PageCard from '@/components/PageCard.vue'
import AdminSectionHeader from '@/components/admin/AdminSectionHeader.vue'
import AdminStateBox from '@/components/admin/AdminStateBox.vue'

defineEmits(['reload', 'select'])

defineProps({
  companies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  selectedCompanyId: { type: String, default: '' },
  formatDate: { type: Function, required: true },
})
</script>

<style scoped>
.state-loading {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}

.spinner {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 3px solid rgba(148, 163, 184, 0.28);
  border-top-color: #0ea5e9;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 14px;
  background: #0ea5e9;
  color: #ffffff;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 700;
}

.inline-link {
  margin-top: 12px;
}

.btn-refresh {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #64748b;
  cursor: pointer;
}

.btn-refresh svg {
  width: 18px;
  height: 18px;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 0.8s linear infinite;
}

.list-stack {
  display: grid;
  gap: 14px;
}

.company-item {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: #ffffff;
  border-radius: 20px;
  padding: 18px 22px;
  display: block;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.company-item:hover {
  border-color: rgba(14, 165, 233, 0.35);
  box-shadow: 0 14px 28px rgba(14, 165, 233, 0.08);
  transform: translateY(-1px);
}

.company-item.selected {
  border-color: rgba(14, 165, 233, 0.45);
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.96), rgba(255, 255, 255, 0.98));
  box-shadow: 0 18px 32px rgba(14, 165, 233, 0.12);
}

.company-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.company-title-block {
  min-width: 0;
  display: grid;
  gap: 8px;
}

.company-name {
  margin: 0;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 800;
  color: #0f172a;
}

.company-meta-inline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #64748b;
}

.company-id,
.company-created-at {
  font-size: 14px;
  line-height: 1.45;
}

.company-id {
  font-family: monospace;
}

.meta-dot {
  color: #cbd5e1;
  font-size: 12px;
}

.total-count {
  margin: 4px 0 0;
  font-size: 14px;
  line-height: 1.45;
  color: #64748b;
  text-align: right;
}

.badge-active,
.badge-inactive {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 76px;
  min-height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-active { background: #dcfce7; color: #15803d; }
.badge-inactive { background: #f1f5f9; color: #64748b; }

@media (max-width: 720px) {
  .company-head {
    flex-direction: column;
    align-items: stretch;
  }

  .company-meta-inline {
    gap: 6px;
  }

  .meta-dot {
    display: none;
  }

  .btn-link {
    width: 100%;
  }
}
</style>
