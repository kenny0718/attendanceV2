<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">
      <div class="admin-header">
        <div class="admin-header-icon" style="background:linear-gradient(135deg,#86efac,#16a34a)">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 21h18M9 8h6M9 12h6M9 16h6M4 21V7a1 1 0 011-1h3l2-2h4l2 2h3a1 1 0 011 1v14" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">新公司開通</h1>
          <p class="admin-description"><router-link to="/admin" class="back-link">← 平台管理</router-link></p>
        </div>
      </div>
      <!-- 區塊二：Onboarding（WP-S1-09D）-->
      <div v-if="isSuperAdmin" class="onboarding-section">
        <div class="onboarding-header">
                     <h2 class="onboarding-title">公司資料與初始管理者</h2>
                  </div>
        <div class="onboarding-body">

          <!-- 成功結果 -->
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

          <!-- Onboarding 表單 -->
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

      <div v-else class="state-box state-error">
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
import Navbar from '@/components/Navbar.vue'
import { useAuthStore } from '@/stores/auth'
import { adminApi } from '@/api/admin'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.isSuperAdmin)

// ── Onboarding（WP-S1-09D）───────────────────────────────────────────
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

// ── 工具函式 ──────────────────────────────────────────────────────────
function formatDate(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  if (isNaN(d)) return isoStr
  return d.toLocaleDateString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.admin-page {
  --primary: #4A6FA5; --primary-hover: #3D5A8A;
  --success: #16a34a; --success-bg: #f0fdf4; --success-border: #bbf7d0;
  --error: #dc2626; --error-bg: #fef2f2; --error-border: #fecaca;
  --heading: #1C3B6B; --text-primary: #2D3A52; --text-secondary: #5A6C7D;
  --bg-main: #F4F7F9; --bg-card: #FFFFFF; --border: #E5E7EB;
  --border-input: #D1D5DB; --border-focus: #4A6FA5;
  min-height: 100vh; background-color: var(--bg-main); padding-bottom: 48px;
}
.container { padding: 24px 16px; max-width: 1300px; margin: 0 auto; }
@media (min-width: 768px) { .container { padding: 32px; } }

/* ── Header ── */
.admin-header { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }
.admin-header-icon { width: 52px; height: 52px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg,#7BA3D1,var(--primary)); border-radius: 14px; color: white; }
.admin-header-icon svg { width: 28px; height: 28px; }
.admin-title { font-size: 26px; font-weight: 700; color: var(--heading); margin: 0 0 4px; }
.admin-description { font-size: 13px; color: var(--text-secondary); margin: 0; }

/* ── Section 1: main-layout ── */
.main-layout { display: grid; grid-template-columns: 1fr; gap: 24px; margin-bottom: 40px; }
@media (min-width: 1024px) { .main-layout { grid-template-columns: 1fr 380px; align-items: start; } }

/* ── Panel ── */
.panel { background: var(--bg-card); border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); }
.panel-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--heading); margin: 0; }
.panel-title svg { width: 18px; height: 18px; color: var(--primary); }

/* ── Refresh btn ── */
.btn-refresh { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
.btn-refresh:hover:not(:disabled) { background: #F0F4F8; color: var(--primary); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 16px; height: 16px; transition: transform 0.4s; }
.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── State boxes ── */
.state-box { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 48px 24px; color: var(--text-secondary); font-size: 14px; }
.state-box svg { width: 32px; height: 32px; flex-shrink: 0; opacity: 0.5; }
.state-error { color: var(--error); } .state-error svg { opacity: 1; }
.state-title { font-weight: 600; margin: 0 0 4px; font-size: 15px; } .state-msg { margin: 0; font-size: 13px; opacity: 0.8; }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }

/* ── Table ── */
.table-wrapper { overflow-x: auto; }
.company-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.company-table th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; background: #F8FAFC; border-bottom: 1px solid var(--border); white-space: nowrap; }
.company-table td { padding: 12px 16px; border-bottom: 1px solid #F1F5F9; color: var(--text-primary); vertical-align: middle; }
.company-table tbody tr:hover td { background: #F8FAFC; }
.company-table tbody tr:last-child td { border-bottom: none; }
.cell-id { font-family: monospace; font-size: 12px; color: var(--text-secondary); }
.cell-name { font-weight: 500; } .cell-tz { font-size: 12px; color: var(--text-secondary); } .cell-date { font-size: 12px; white-space: nowrap; color: var(--text-secondary); }
.badge-active { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #dcfce7; color: #15803d; }
.badge-inactive { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #f1f5f9; color: #64748b; }
.total-count { padding: 10px 16px; font-size: 12px; color: var(--text-secondary); text-align: right; margin: 0; border-top: 1px solid var(--border); }

/* ── Create Form ── */
.create-form { padding: 20px 24px 24px; display: flex; flex-direction: column; gap: 18px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--text-primary); display: flex; align-items: baseline; gap: 6px; }
.label-hint { font-size: 11px; font-weight: 400; color: var(--text-secondary); }
.form-input { padding: 9px 12px; border: 1px solid var(--border-input); border-radius: 8px; font-size: 14px; color: var(--text-primary); background: #fff; outline: none; transition: border-color 0.2s, box-shadow 0.2s; width: 100%; box-sizing: border-box; }
.form-input:focus { border-color: var(--border-focus); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.input-error { border-color: var(--error) !important; }
.field-error { font-size: 12px; color: var(--error); margin: 0; }
.btn-submit { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 11px 20px; background: var(--primary); color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s, transform 0.1s; }
.btn-submit:hover:not(:disabled) { background: var(--primary-hover); }
.btn-submit:active:not(:disabled) { transform: scale(0.98); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-submit svg { width: 16px; height: 16px; }
.btn-spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }

/* ── Alerts ── */
.alert { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border-radius: 10px; font-size: 13px; margin: 16px 24px 0; }
.alert svg { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }
.alert-success { background: var(--success-bg); border: 1px solid var(--success-border); color: var(--success); }
.alert-error { background: var(--error-bg); border: 1px solid var(--error-border); color: var(--error); }

/* ── Section 2: Onboarding ── */
.onboarding-section { background: var(--bg-card); border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; }
.onboarding-header { display: flex; align-items: center; gap: 16px; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); }
.onboarding-header-icon { width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #86efac, #16a34a); border-radius: 12px; color: white; }
.onboarding-header-icon svg { width: 24px; height: 24px; }
.onboarding-title { font-size: 16px; font-weight: 600; color: var(--heading); margin: 0 0 4px; }
.onboarding-desc { font-size: 13px; color: var(--text-secondary); margin: 0; }
.onboarding-body { padding: 24px; }

/* ── Onboarding result card ── */
.ob-result-card { background: var(--success-bg); border: 1px solid var(--success-border); border-radius: 12px; padding: 20px 24px; }
.ob-result-header { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--success); margin-bottom: 16px; }
.ob-result-header svg { width: 22px; height: 22px; }
.ob-result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
.ob-result-group { background: white; border-radius: 10px; padding: 14px 16px; border: 1px solid var(--success-border); }
.ob-result-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 6px; }
.ob-result-val { font-size: 15px; font-weight: 600; color: var(--heading); margin: 0 0 4px; }
.ob-result-sub { font-size: 12px; color: var(--text-secondary); margin: 0; font-family: monospace; }
.btn-ob-again { padding: 8px 18px; background: var(--success); color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
.btn-ob-again:hover { opacity: 0.88; }

/* ── Onboarding form ── */
.ob-alert { margin: 0 0 16px; }
.ob-form { display: flex; flex-direction: column; gap: 20px; }
.ob-cols { display: grid; grid-template-columns: 1fr; gap: 24px; }
@media (min-width: 768px) { .ob-cols { grid-template-columns: 1fr 1fr; } }
.ob-col { display: flex; flex-direction: column; gap: 14px; }
.ob-col-title { font-size: 13px; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 4px; padding-bottom: 8px; border-bottom: 2px solid #EFF3F8; }
.btn-ob-submit { margin-top: 8px; align-self: flex-end; padding: 12px 28px; font-size: 15px; }
.btn-ob-submit svg { width: 18px; height: 18px; }
</style>
