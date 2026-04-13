<template>
  <div class="stack-layout">
    <div v-if="isSuperAdmin" class="panel onboarding-section">
      <div class="panel-header">
        <div>
          <h2 class="onboarding-title">公司資料與初始管理者</h2>
          <p class="onboarding-desc">建立新租戶的唯一入口，含統一編號檢核、初始管理員帳號與 Membership。</p>
        </div>
      </div>
      <div class="onboarding-body">
        <div v-if="obSuccess" class="ob-result-card">
          <div class="ob-result-header">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>Onboarding 完成！</span>
          </div>
          <div class="ob-result-grid">
            <div class="ob-result-group">
              <p class="ob-result-label">公司</p>
              <p class="ob-result-val">{{ obSuccess.company.name }}</p>
              <p class="ob-result-sub">ID: {{ obSuccess.company.id }}</p>
              <p v-if="obSuccess.company.tax_id" class="ob-result-sub">統編: {{ obSuccess.company.tax_id }}</p>
            </div>
            <div class="ob-result-group">
              <p class="ob-result-label">使用者</p>
              <p class="ob-result-val">{{ obSuccess.user.display_name }}</p>
              <p class="ob-result-sub">{{ obSuccess.user.email || '（無 email）' }}</p>
            </div>
            <div class="ob-result-group">
              <p class="ob-result-label">登入帳號</p>
              <p class="ob-result-val">{{ obSuccess.membership.login_username }}</p>
              <p class="ob-result-sub">角色: {{ obSuccess.membership.role_id }}</p>
            </div>
          </div>
          <button class="btn-ob-again" @click="resetOnboarding">再建立一個</button>
        </div>

        <div v-else class="ob-form-wrap">
          <div v-if="obError" class="alert alert-error ob-alert">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>{{ obError }}</span>
          </div>
          <form @submit.prevent="handleOnboard" class="ob-form" novalidate>
            <div class="ob-cols">
              <div class="ob-col">
                <p class="ob-col-title">公司資料</p>
                <div class="form-group">
                  <label class="form-label" for="ob-co-id">公司 ID <span class="label-hint">必填，最多 50 字</span></label>
                  <input id="ob-co-id" v-model.trim="obForm.company.id" type="text" class="form-input" :class="{'input-error':obErr.company_id}" placeholder="e.g. acme-corp" maxlength="50" autocomplete="off" />
                  <p v-if="obErr.company_id" class="field-error">{{ obErr.company_id }}</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-co-name">公司名稱 <span class="label-hint">必填</span></label>
                  <input id="ob-co-name" v-model.trim="obForm.company.name" type="text" class="form-input" :class="{'input-error':obErr.company_name}" placeholder="e.g. Acme Corp Ltd" maxlength="255" />
                  <p v-if="obErr.company_name" class="field-error">{{ obErr.company_name }}</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-co-tax-id">統一編號 <span class="label-hint">選填，8 碼且需通過檢查碼</span></label>
                  <input id="ob-co-tax-id" v-model.trim="obForm.company.tax_id" type="text" inputmode="numeric" class="form-input" :class="{'input-error':obErr.tax_id}" placeholder="e.g. 24536806" maxlength="8" autocomplete="off" />
                  <p v-if="obErr.tax_id" class="field-error">{{ obErr.tax_id }}</p>
                  <p v-else class="field-hint">若有填寫，系統會做統編格式與檢查碼驗證。</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-co-tz">時區</label>
                  <select id="ob-co-tz" v-model="obForm.company.timezone" class="form-input">
                    <option value="UTC">UTC</option>
                    <option value="Asia/Taipei">Asia/Taipei（台北）</option>
                  </select>
                </div>
              </div>
              <div class="ob-col">
                <p class="ob-col-title">初始管理者</p>
                <div class="form-group">
                  <label class="form-label" for="ob-u-name">顯示名稱 <span class="label-hint">必填</span></label>
                  <input id="ob-u-name" v-model.trim="obForm.initial_user.display_name" type="text" class="form-input" :class="{'input-error':obErr.display_name}" placeholder="e.g. Alice Wang" maxlength="100" />
                  <p v-if="obErr.display_name" class="field-error">{{ obErr.display_name }}</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-u-login">登入帳號 <span class="label-hint">必填，公司內唯一</span></label>
                  <input id="ob-u-login" v-model.trim="obForm.initial_user.login_username" type="text" class="form-input" :class="{'input-error':obErr.login_username}" placeholder="e.g. alice" maxlength="100" autocomplete="off" />
                  <p v-if="obErr.login_username" class="field-error">{{ obErr.login_username }}</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-u-email">Email <span class="label-hint">選填</span></label>
                  <input id="ob-u-email" v-model.trim="obForm.initial_user.email" type="email" class="form-input" placeholder="alice@example.com" maxlength="255" />
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-u-pwd">密碼 <span class="label-hint">必填，至少 6 字</span></label>
                  <input id="ob-u-pwd" v-model="obForm.initial_user.password" type="password" class="form-input" :class="{'input-error':obErr.password}" placeholder="••••••••" maxlength="255" autocomplete="new-password" />
                  <p v-if="obErr.password" class="field-error">{{ obErr.password }}</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ob-u-role">角色</label>
                  <select id="ob-u-role" v-model="obForm.initial_user.role_id" class="form-input">
                    <option value="company_admin">company_admin（公司管理員）</option>
                  </select>
                </div>
              </div>
            </div>
            <button type="submit" class="btn-submit btn-ob-submit" :disabled="obLoading">
              <span v-if="obLoading" class="btn-spinner"></span>
              <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
              {{ obLoading ? '建立中…' : '開通公司' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <div v-else class="panel panel-state">
      <div class="state-box state-error">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <p class="state-title">權限不足</p>
          <p class="state-msg">此頁僅開放 super_admin。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { adminApi } from '@/api/admin'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.isSuperAdmin)
const TAX_ID_WEIGHTS = [1, 2, 1, 2, 1, 2, 4, 1]

const obForm = reactive({
  company: { id: '', name: '', tax_id: '', timezone: 'UTC' },
  initial_user: { display_name: '', login_username: '', email: '', password: '', role_id: 'company_admin' }
})
const obErr = reactive({
  company_id: '', company_name: '', tax_id: '',
  display_name: '', login_username: '', password: ''
})
const obLoading = ref(false)
const obError = ref(null)
const obSuccess = ref(null)

function resetObAlerts() {
  obError.value = null
  Object.keys(obErr).forEach(k => { obErr[k] = '' })
}

function isValidTaxId(value) {
  if (!/^\d{8}$/.test(value)) return false
  const digits = value.split('').map(Number)
  const checksum = digits.reduce((sum, digit, index) => {
    const product = digit * TAX_ID_WEIGHTS[index]
    return sum + Math.floor(product / 10) + (product % 10)
  }, 0)
  if (checksum % 10 === 0) return true
  return digits[6] === 7 && (checksum + 1) % 10 === 0
}

function validateObForm() {
  let valid = true
  if (!obForm.company.id) { obErr.company_id = '公司 ID 為必填'; valid = false }
  if (!obForm.company.name) { obErr.company_name = '公司名稱為必填'; valid = false }
  if (obForm.company.tax_id) {
    if (!/^\d{8}$/.test(obForm.company.tax_id)) {
      obErr.tax_id = '統一編號需為 8 位數字'
      valid = false
    } else if (!isValidTaxId(obForm.company.tax_id)) {
      obErr.tax_id = '統一編號檢查碼不正確'
      valid = false
    }
  }
  if (!obForm.initial_user.display_name) { obErr.display_name = '顯示名稱為必填'; valid = false }
  if (!obForm.initial_user.login_username) { obErr.login_username = '登入帳號為必填'; valid = false }
  if (!obForm.initial_user.password || obForm.initial_user.password.length < 6) {
    obErr.password = '密碼為必填且至少 6 個字元'
    valid = false
  }
  return valid
}

async function handleOnboard() {
  resetObAlerts()
  if (!validateObForm()) return
  obLoading.value = true
  try {
    const result = await adminApi.onboardCompany({
      company: {
        id: obForm.company.id,
        name: obForm.company.name,
        tax_id: obForm.company.tax_id || null,
        timezone: obForm.company.timezone || 'UTC'
      },
      initial_user: {
        display_name: obForm.initial_user.display_name,
        login_username: obForm.initial_user.login_username,
        email: obForm.initial_user.email || null,
        password: obForm.initial_user.password,
        role_id: obForm.initial_user.role_id
      }
    })
    obSuccess.value = result
  } catch (err) {
    const detail = err.data?.detail
    const code = detail?.code
    if (err.status === 409 && code === 'DUPLICATE_COMPANY') {
      obErr.company_id = `公司 ID「${obForm.company.id}」已存在`
    } else if (err.status === 409 && code === 'DUPLICATE_TAX_ID') {
      obErr.tax_id = `統一編號「${obForm.company.tax_id}」已存在`
    } else if (err.status === 409 && code === 'DUPLICATE_LOGIN_USERNAME') {
      obErr.login_username = `登入帳號「${obForm.initial_user.login_username}」在此公司已存在`
    } else if (err.status === 409) {
      obError.value = '資料重複衝突：' + (detail?.message || '請確認後重試')
    } else if (err.status === 422) {
      const errors = Array.isArray(detail) ? detail : []
      if (errors.length) {
        errors.forEach(e => {
          const loc = e.loc?.[e.loc.length - 1]
          if (loc === 'id') obErr.company_id = e.msg
          else if (loc === 'name') obErr.company_name = e.msg
          else if (loc === 'tax_id') obErr.tax_id = e.msg
          else if (loc === 'display_name') obErr.display_name = e.msg
          else if (loc === 'login_username') obErr.login_username = e.msg
          else if (loc === 'password') obErr.password = e.msg
        })
        obError.value = '輸入資料有誤，請確認後重試'
      } else if (detail?.code === 'INVALID_ROLE') {
        obError.value = `無效角色：${detail.message}`
      } else {
        obError.value = '輸入資料驗證失敗，請確認後重試'
      }
    } else if (err.status === 401) {
      obError.value = '登入已過期，請重新登入'
    } else if (err.status === 403) {
      obError.value = '權限不足：只有 super_admin 可執行 開通新公司'
    } else {
      obError.value = err.message || 'Onboarding 失敗，請稍後再試'
    }
  } finally {
    obLoading.value = false
  }
}

function resetOnboarding() {
  obSuccess.value = null
  resetObAlerts()
  obForm.company.id = ''
  obForm.company.name = ''
  obForm.company.tax_id = ''
  obForm.company.timezone = 'UTC'
  obForm.initial_user.display_name = ''
  obForm.initial_user.login_username = ''
  obForm.initial_user.email = ''
  obForm.initial_user.password = ''
  obForm.initial_user.role_id = 'company_admin'
}
</script>

<style scoped>
.stack-layout {
  display: grid;
  gap: 18px;
}

.panel {
  background: rgba(255, 255, 255, 0.84);
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.panel-state {
  min-height: 180px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.onboarding-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--heading);
  margin: 0 0 4px;
}

.onboarding-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
  margin: 0;
}

.onboarding-body {
  padding: 22px 24px 24px;
}

.ob-form-wrap,
.ob-form {
  display: grid;
  gap: 18px;
}

.ob-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.ob-col {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.98));
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.ob-col-title {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}

.form-group {
  display: grid;
  gap: 6px;
}

.form-label {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.label-hint,
.field-hint {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.form-input {
  min-height: 46px;
  padding: 0 14px;
  border: 1px solid rgba(148, 163, 184, 0.32);
  border-radius: 16px;
  font-size: 15px;
  color: #0f172a;
  background: rgba(255, 255, 255, 0.96);
  outline: none;
}

.form-input:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.25);
}

.input-error {
  border-color: #f87171;
  box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.12);
}

.field-error {
  margin: 0;
  font-size: 12px;
  color: #dc2626;
}

.ob-alert,
.alert {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.alert svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.btn-submit,
.btn-ob-again {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 0 20px;
  border: none;
  border-radius: 16px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

.btn-ob-submit {
  justify-self: start;
  min-width: 164px;
  background: #0ea5e9;
  color: #ffffff;
}

.btn-ob-again {
  background: #e2e8f0;
  color: #334155;
}

.btn-submit:disabled,
.btn-ob-again:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.ob-result-card {
  display: grid;
  gap: 18px;
}

.ob-result-header {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #15803d;
  font-size: 15px;
  font-weight: 800;
}

.ob-result-header svg {
  width: 20px;
  height: 20px;
}

.ob-result-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.ob-result-group {
  padding: 16px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.ob-result-label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.ob-result-val {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.ob-result-sub {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}

.state-box {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  text-align: left;
}

.state-box svg {
  width: 24px;
  height: 24px;
}

.state-error {
  color: #dc2626;
}

.state-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 800;
}

.state-msg {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 960px) {
  .ob-cols,
  .ob-result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
