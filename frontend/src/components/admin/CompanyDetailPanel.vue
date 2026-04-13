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
        v-if="memberSummary"
        class="summary-panel"
      >
        <div class="summary-card">
          <span class="summary-label">管理角色總數</span>
          <strong class="summary-value">{{ memberSummary.admin_count }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">啟用中的管理角色</span>
          <strong class="summary-value">{{ memberSummary.active_admin_count }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">company_admin</span>
          <strong class="summary-value">{{ memberSummary.has_company_admin ? '有' : '無' }}</strong>
        </div>
        <div class="summary-card">
          <span class="summary-label">hr_manager</span>
          <strong class="summary-value">{{ memberSummary.has_hr_manager ? '有' : '無' }}</strong>
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

      <div class="logo-panel">
        <div class="logo-preview-wrap">
          <div
            v-if="company.logo_url"
            class="logo-preview-box"
          >
            <img
              :src="company.logo_url"
              alt="Company logo"
              class="logo-preview"
            >
          </div>
          <div
            v-else
            class="logo-empty"
          >
            尚未設定 Logo
          </div>
        </div>
        <div class="logo-meta">
          <p class="logo-label">
            目前 Logo URL
          </p>
          <p class="logo-url mono">
            {{ company.logo_url || '—' }}
          </p>
          <p class="logo-hint">
            僅支援 PNG / JPG / JPEG，檔案上限 2MB。Logo 需以上傳方式設定，不能手動輸入 URL。
          </p>
          <div class="logo-actions">
            <input
              ref="logoInput"
              type="file"
              accept="image/png,image/jpeg"
              class="visually-hidden"
              @change="onFileChange"
            >
            <button
              type="button"
              class="btn-logo"
              :disabled="loading"
              @click="triggerLogoUpload"
            >
              上傳 Logo
            </button>
            <button
              type="button"
              class="btn-logo btn-logo-secondary"
              :disabled="loading || !company.logo_url"
              @click="$emit('remove-logo')"
            >
              移除 Logo
            </button>
          </div>
        </div>
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
            {{ loading ? '儲存中…' : '儲存變更' }}
          </button>
        </div>
      </form>
    </div>
  </PageCard>
</template>

<script setup>
import { ref } from 'vue'
import PageCard from '@/components/PageCard.vue'
import AdminSectionHeader from '@/components/admin/AdminSectionHeader.vue'

const logoInput = ref(null)

const emit = defineEmits(['submit', 'toggle-active', 'update:form', 'upload-logo', 'remove-logo'])

const props = defineProps({
  company: { type: Object, default: null },
  memberSummary: { type: Object, default: null },
  form: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  success: { type: String, default: '' },
  formatDate: { type: Function, required: true },
})

function triggerLogoUpload() {
  if (props.loading) return
  logoInput.value?.click()
}

function onFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  emit('upload-logo', file)
  event.target.value = ''
}
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
.summary-panel { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.summary-card { padding: 14px; border-radius: 16px; background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.16); }
.summary-label { display: block; font-size: 13px; font-weight: 700; color: #0369a1; margin-bottom: 8px; }
.summary-value { font-size: 24px; color: #0f172a; }
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
.btn-toggle,
.btn-logo { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-width: 144px; min-height: 46px; padding: 0 20px; border: none; border-radius: 16px; font-size: 15px; font-weight: 700; white-space: nowrap; cursor: pointer; }
.btn-submit { background: #0ea5e9; color: #ffffff; }
.btn-toggle { background: #e2e8f0; color: #334155; }
.btn-logo { background: #0f172a; color: #ffffff; }
.btn-logo-secondary { background: #e2e8f0; color: #334155; }
.btn-submit:disabled,
.btn-toggle:disabled,
.btn-logo:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner { width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; }
.alert { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; }
.alert svg { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.badge-active,
.badge-inactive { display: inline-flex; align-items: center; justify-content: center; min-width: 72px; min-height: 32px; padding: 0 12px; border-radius: 999px; font-size: 14px; font-weight: 700; }
.badge-active { background: #dcfce7; color: #15803d; }
.badge-inactive { background: #f1f5f9; color: #64748b; }
.logo-panel { display: grid; grid-template-columns: 180px minmax(0, 1fr); gap: 16px; padding: 16px; border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 18px; background: rgba(248, 250, 252, 0.7); }
.logo-preview-wrap { display: flex; align-items: center; justify-content: center; }
.logo-preview-box, .logo-empty { width: 180px; height: 120px; border-radius: 16px; border: 1px dashed rgba(148, 163, 184, 0.6); background: white; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.logo-preview { max-width: 140px; max-height: 80px; object-fit: contain; }
.logo-empty { color: #94a3b8; font-size: 13px; }
.logo-meta { display: grid; gap: 10px; align-content: start; }
.logo-label { margin: 0; font-size: 13px; font-weight: 800; color: #334155; }
.logo-url { margin: 0; font-size: 13px; color: #0f172a; word-break: break-all; }
.logo-hint { margin: 0; font-size: 12px; color: #64748b; line-height: 1.6; }
.logo-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.visually-hidden { display: none; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) { .detail-meta, .summary-panel, .form-grid-triple { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) { .detail-meta, .summary-panel, .form-grid-double, .form-grid-triple, .logo-panel { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .detail-actions { flex-direction: column; align-items: stretch; } .btn-submit, .btn-toggle, .btn-logo { width: 100%; } }
</style>
