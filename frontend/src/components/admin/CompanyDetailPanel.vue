<template>
  <PageCard>
    <AdminSectionHeader
      title="公司詳情 / 編輯"
      icon-path="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
    />

    <div
      v-if="!company"
      class="detail-empty"
    >
      <svg
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        stroke-width="2"
      ><path
        stroke-linecap="round"
        stroke-linejoin="round"
        d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5"
      /></svg>
      <p>請先從上方公司列表選擇一間公司</p>
    </div>

    <div
      v-else
      class="detail-body"
    >
      <div class="detail-meta">
        <div class="detail-meta-item">
          <span class="detail-meta-label">ID</span><span class="detail-meta-val mono">{{ company.id }}</span>
        </div>
        <div class="detail-meta-item">
          <span class="detail-meta-label">統一編號</span><span class="detail-meta-val mono">{{ company.tax_id || '—' }}</span>
        </div>
        <div class="detail-meta-item">
          <span class="detail-meta-label">建立時間</span><span class="detail-meta-val">{{ formatDate(company.created_at) }}</span>
        </div>
        <div class="detail-meta-item">
          <span class="detail-meta-label">狀態</span><span :class="company.is_active ? 'badge-active' : 'badge-inactive'">{{ company.is_active ? '啟用' : '停用' }}</span>
        </div>
      </div>

      <div
        v-if="success"
        class="alert alert-success"
      >
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="2"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        /></svg>
        <span>{{ success }}</span>
      </div>
      <div
        v-if="error"
        class="alert alert-error"
      >
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="2"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        /></svg>
        <span>{{ error }}</span>
      </div>

      <form
        class="detail-form"
        novalidate
        @submit.prevent="$emit('submit')"
      >
        <div class="form-grid form-grid-double">
          <div class="form-group">
            <label
              class="form-label"
              for="d-name"
            >公司名稱</label>
            <input
              id="d-name"
              :value="form.name"
              type="text"
              class="form-input"
              maxlength="255"
              @input="$emit('update:form', { ...form, name: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="d-display-name"
            >顯示名稱</label>
            <input
              id="d-display-name"
              :value="form.display_name"
              type="text"
              class="form-input"
              maxlength="255"
              placeholder="前台顯示名稱"
              @input="$emit('update:form', { ...form, display_name: $event.target.value })"
            >
          </div>
        </div>

        <div class="form-grid form-grid-double">
          <div class="form-group">
            <label
              class="form-label"
              for="d-tax-id"
            >統一編號</label>
            <input
              id="d-tax-id"
              :value="form.tax_id"
              type="text"
              inputmode="numeric"
              class="form-input"
              maxlength="8"
              placeholder="8 碼統編，可留空"
              @input="$emit('update:form', { ...form, tax_id: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="d-owner-name"
            >負責人</label>
            <input
              id="d-owner-name"
              :value="form.owner_name"
              type="text"
              class="form-input"
              maxlength="255"
              placeholder="公司負責人"
              @input="$emit('update:form', { ...form, owner_name: $event.target.value })"
            >
          </div>
        </div>

        <div class="form-group">
          <label
            class="form-label"
            for="d-registered-address"
          >登記地址</label>
          <input
            id="d-registered-address"
            :value="form.registered_address"
            type="text"
            class="form-input"
            maxlength="500"
            placeholder="公司工商登記地址"
            @input="$emit('update:form', { ...form, registered_address: $event.target.value })"
          >
        </div>
        <div class="form-group">
          <label
            class="form-label"
            for="d-contact-address"
          >聯絡地址</label>
          <input
            id="d-contact-address"
            :value="form.contact_address"
            type="text"
            class="form-input"
            maxlength="500"
            placeholder="對外聯絡或收件地址"
            @input="$emit('update:form', { ...form, contact_address: $event.target.value })"
          >
        </div>

        <div class="form-grid form-grid-triple">
          <div class="form-group">
            <label
              class="form-label"
              for="d-contact-phone"
            >聯絡電話</label>
            <input
              id="d-contact-phone"
              :value="form.contact_phone"
              type="text"
              class="form-input"
              maxlength="50"
              placeholder="02-12345678"
              @input="$emit('update:form', { ...form, contact_phone: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="d-contact-email"
            >聯絡 Email</label>
            <input
              id="d-contact-email"
              :value="form.contact_email"
              type="email"
              class="form-input"
              maxlength="255"
              placeholder="service@example.com"
              @input="$emit('update:form', { ...form, contact_email: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="d-tz"
            >時區</label>
            <select
              id="d-tz"
              :value="form.timezone"
              class="form-input"
              @change="$emit('update:form', { ...form, timezone: $event.target.value })"
            >
              <option value="UTC">
                UTC
              </option>
              <option value="Asia/Taipei">
                Asia/Taipei（台北）
              </option>
              <option value="Asia/Tokyo">
                Asia/Tokyo（東京）
              </option>
              <option value="Asia/Shanghai">
                Asia/Shanghai（上海）
              </option>
              <option value="Asia/Singapore">
                Asia/Singapore（新加坡）
              </option>
              <option value="America/New_York">
                America/New_York（紐約）
              </option>
              <option value="America/Los_Angeles">
                America/Los_Angeles（洛杉磯）
              </option>
              <option value="Europe/London">
                Europe/London（倫敦）
              </option>
              <option value="Europe/Paris">
                Europe/Paris（巴黎）
              </option>
            </select>
          </div>
        </div>

        <div class="detail-actions">
          <button
            type="button"
            class="btn-toggle"
            :disabled="loading"
            @click="$emit('toggle-active')"
          >
            {{ company.is_active ? '停用公司' : '啟用公司' }}
          </button>
          <button
            type="submit"
            class="btn-submit"
            :disabled="loading"
          >
            <span
              v-if="loading"
              class="btn-spinner"
            />
            <svg
              v-else
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              stroke-width="2"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M5 13l4 4L19 7"
            /></svg>
            <span class="btn-label">{{ loading ? '儲存中…' : '儲存變更' }}</span>
          </button>
        </div>
      </form>
    </div>
  </PageCard>
</template>

<script setup>
import PageCard from '@/components/PageCard.vue'
import AdminSectionHeader from '@/components/admin/AdminSectionHeader.vue'

defineEmits(['submit', 'toggle-active', 'update:form'])

const props = defineProps({
  company: { type: Object, default: null },
  memberSummary: { type: Object, default: null },
  form: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  success: { type: String, default: '' },
  formatDate: { type: Function, required: true },
})
</script>

<style scoped>
.detail-empty {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #94a3b8;
  text-align: center;
  font-size: 14px;
}

.detail-empty svg { width: 34px; height: 34px; }
.detail-body { display: grid; gap: 16px; }
.detail-meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.detail-meta-item { padding: 14px; border-radius: 16px; background: rgba(248, 250, 252, 0.92); border: 1px solid rgba(226, 232, 240, 0.9); }
.detail-meta-label { display: block; font-size: 13px; font-weight: 700; color: #64748b; margin-bottom: 6px; }
.detail-meta-val { font-size: 15px; line-height: 1.45; color: #0f172a; }
.mono { font-family: monospace; }
.detail-form { display: grid; gap: 14px; }
.form-grid { display: grid; gap: 14px; }
.form-grid-double { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.form-grid-triple { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.form-group { display: grid; gap: 6px; }
.form-label { font-size: 14px; font-weight: 700; color: #334155; }
.form-input { min-height: 46px; padding: 0 14px; border: 1px solid rgba(148, 163, 184, 0.32); border-radius: 16px; font-size: 15px; color: #0f172a; background: rgba(255, 255, 255, 0.92); outline: none; }
.form-input:focus { border-color: #93c5fd; box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.25); }
.detail-actions { display: flex; justify-content: flex-end; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 6px; }
.btn-submit,
.btn-toggle {
  width: 190px;
  min-width: 190px;
  min-height: 48px;
  padding: 0 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-submit {
  border: none;
  background: #4A6FA5;
  color: #ffffff;
}
.btn-submit svg,
.btn-toggle svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}
.btn-label {
  white-space: nowrap;
}
.btn-toggle {
  border: 1px solid #4A6FA5;
  background: #ffffff;
  color: #4A6FA5;
}
.btn-submit:disabled,
.btn-toggle:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner { width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; flex-shrink: 0; }
.alert { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; }
.alert svg { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.badge-active,
.badge-inactive { display: inline-flex; align-items: center; justify-content: center; min-width: 72px; min-height: 32px; padding: 0 12px; border-radius: 999px; font-size: 14px; font-weight: 700; }
.badge-active { background: #dcfce7; color: #15803d; }
.badge-inactive { background: #f1f5f9; color: #64748b; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) { .detail-meta, .form-grid-triple { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) { }
@media (max-width: 720px) { .detail-actions { flex-direction: column; align-items: stretch; } }
</style>
