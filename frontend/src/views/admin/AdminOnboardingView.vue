<template>
  <div class="stack-layout">
    <div v-if="isSuperAdmin" class="panel onboarding-section">
      <div class="panel-header">
        <div>
          <h2 class="onboarding-title">公司資料與初始管理者</h2>
          <p class="onboarding-desc">建立新租戶的唯一入口，含初始管理員帳號與 Membership。</p>
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

const obForm = reactive({
  company: { id: '', name: '', timezone: 'UTC' },
  initial_user: { display_name: '', login_username: '', email: '', password: '', role_id: 'company_admin' }
})
const obErr = reactive({
  company_id: '', company_name: '',
  display_name: '', login_username: '', password: ''
})
const obLoading = ref(false)
const obError = ref(null)
const obSuccess = ref(null)

function resetObAlerts() {
  obError.value = null
  Object.keys(obErr).forEach(k => { obErr[k] = '' })
}

function validateObForm() {
  let valid = true
  if (!obForm.company.id) { obErr.company_id = '公司 ID 為必填'; valid = false }
  if (!obForm.company.name) { obErr.company_name = '公司名稱為必填'; valid = false }
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
  color: var(--text-secondary);
  margin: 0;
}

.onboarding-body {
  padding: 24px;
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 24px;
  color: var(--text-secondary);
  font-size: 14px;
}

.state-box svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  opacity: 0.5;
}

.state-error {
  color: var(--error);
}

.state-error svg {
  opacity: 1;
}

.state-title {
  font-weight: 600;
  margin: 0 0 4px;
  font-size: 15px;
}

.state-msg {
  margin: 0;
  font-size: 13px;
  opacity: 0.8;
}

.alert {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
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
  color: var(--error);
}

.ob-alert {
  margin: 0 0 16px;
}

.ob-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ob-cols {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 768px) {
  .ob-cols {
    grid-template-columns: 1fr 1fr;
  }
}

.ob-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ob-col-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 4px;
  padding-bottom: 8px;
  border-bottom: 2px solid #eff3f8;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.label-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-secondary);
}

.form-input {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  background: #fff;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.12);
}

.input-error {
  border-color: var(--error) !important;
}

.field-error {
  font-size: 12px;
  color: var(--error);
  margin: 0;
}

.btn-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-submit svg {
  width: 16px;
  height: 16px;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ob-result-card {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 20px 24px;
}

.ob-result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #16a34a;
  margin-bottom: 16px;
}

.ob-result-header svg {
  width: 22px;
  height: 22px;
}

.ob-result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.ob-result-group {
  background: white;
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid #bbf7d0;
}

.ob-result-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 6px;
}

.ob-result-val {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px;
  word-break: break-word;
}

.ob-result-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

.btn-ob-again {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  background: #16a34a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-ob-again:hover {
  opacity: 0.9;
}
</style>
