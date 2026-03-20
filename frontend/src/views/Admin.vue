<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">

      <!-- 頁面標題 -->
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">平台管理</h1>
          <p class="admin-description">管理系統租戶與公司帳戶（super_admin 專用）</p>
        </div>
      </div>

      <!-- 區塊一：公司列表 + 快速建立 -->
      <div class="main-layout">
        <section class="panel panel-list">
          <div class="panel-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
              公司列表
            </h2>
            <button class="btn-refresh" :disabled="listLoading" @click="loadCompanies" title="重新整理">
              <svg :class="{ spinning: listLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
          <div v-if="listLoading" class="state-box"><div class="spinner"></div><span>載入中…</span></div>
          <div v-else-if="listError" class="state-box state-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <div><p class="state-title">載入失敗</p><p class="state-msg">{{ listError }}</p></div>
          </div>
          <div v-else-if="companies.length === 0" class="state-box state-empty">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
            <div><p class="state-title">尚無公司</p><p class="state-msg">使用下方 Onboarding 建立第一間公司。</p></div>
          </div>
          <div v-else class="table-wrapper">
            <table class="company-table">
              <thead><tr><th>ID</th><th>名稱</th><th>狀態</th><th>時區</th><th>建立時間</th></tr></thead>
              <tbody>
                <tr v-for="co in companies" :key="co.id">
                  <td class="cell-id">{{ co.id }}</td>
                  <td class="cell-name">{{ co.name }}</td>
                  <td><span :class="co.is_active ? 'badge-active' : 'badge-inactive'">{{ co.is_active ? '啟用' : '停用' }}</span></td>
                  <td class="cell-tz">{{ co.timezone }}</td>
                  <td class="cell-date">{{ formatDate(co.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            <p class="total-count">共 {{ companies.length }} 間公司</p>
          </div>
        </section>

        <section class="panel panel-form">
          <div class="panel-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
              建立新公司
            </h2>
          </div>
          <div v-if="createSuccess" class="alert alert-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>公司 <strong>{{ createSuccess }}</strong> 建立成功！</span>
          </div>
          <div v-if="createError" class="alert alert-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>{{ createError }}</span>
          </div>
          <form @submit.prevent="handleCreate" class="create-form" novalidate>
            <div class="form-group">
              <label class="form-label" for="f-id">公司 ID <span class="label-hint">最多 50 字</span></label>
              <input id="f-id" v-model.trim="form.id" type="text" class="form-input" :class="{'input-error':fieldErrors.id}" placeholder="e.g. company-b" maxlength="50" autocomplete="off" />
              <p v-if="fieldErrors.id" class="field-error">{{ fieldErrors.id }}</p>
            </div>
            <div class="form-group">
              <label class="form-label" for="f-name">公司名稱 <span class="label-hint">最多 255 字</span></label>
              <input id="f-name" v-model.trim="form.name" type="text" class="form-input" :class="{'input-error':fieldErrors.name}" placeholder="e.g. Example Corp Ltd" maxlength="255" />
              <p v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</p>
            </div>
            <div class="form-group">
              <label class="form-label" for="f-tz">時區</label>
              <select id="f-tz" v-model="form.timezone" class="form-input">
                <option value="UTC">UTC</option>
                <option value="Asia/Taipei">Asia/Taipei（台北）</option>
                <option value="Asia/Tokyo">Asia/Tokyo（東京）</option>
                <option value="Asia/Shanghai">Asia/Shanghai（上海）</option>
                <option value="Asia/Singapore">Asia/Singapore（新加坡）</option>
                <option value="America/New_York">America/New_York（紐約）</option>
                <option value="America/Los_Angeles">America/Los_Angeles（洛杉磯）</option>
                <option value="Europe/London">Europe/London（倫敦）</option>
                <option value="Europe/Paris">Europe/Paris（巴黎）</option>
              </select>
            </div>
            <button type="submit" class="btn-submit" :disabled="createLoading">
              <span v-if="createLoading" class="btn-spinner"></span>
              <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
              {{ createLoading ? '建立中…' : '建立公司' }}
            </button>
          </form>
        </section>
      </div>

      <!-- 區塊二：Onboarding（WP-S1-09D）-->
      <div class="onboarding-section">
        <div class="onboarding-header">
          <div class="onboarding-header-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <div>
            <h2 class="onboarding-title">快速 Onboarding</h2>
            <p class="onboarding-desc">一次建立公司 + 初始管理者帳號 + Membership（原子操作）</p>
          </div>
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
                <p class="ob-result-sub">{{ obSuccess.user.email || '（無 email）' }}</p>\n              </div>\n              <div class="ob-result-group">\n                <p class="ob-result-label">登入帳號</p>\n                <p class="ob-result-val">{{ obSuccess.membership.login_username }}</p>\n                <p class="ob-result-sub">角色: {{ obSuccess.membership.role_id }}</p>\n              </div>\n            </div>\n            <button class="btn-ob-again" @click="resetOnboarding">再建立一個</button>
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
                      <option value="Asia/Tokyo">Asia/Tokyo（東京）</option>
                      <option value="Asia/Shanghai">Asia/Shanghai（上海）</option>
                      <option value="Asia/Singapore">Asia/Singapore（新加坡）</option>
                      <option value="America/New_York">America/New_York（紐約）</option>
                      <option value="America/Los_Angeles">America/Los_Angeles（洛杉磯）</option>
                      <option value="Europe/London">Europe/London（倫敦）</option>
                      <option value="Europe/Paris">Europe/Paris（巴黎）</option>
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
                      <option value="admin">admin（公司管理員）</option>
                    </select>
                  </div>
                </div>
              </div>
              <button type="submit" class="btn-submit btn-ob-submit" :disabled="obLoading">
                <span v-if="obLoading" class="btn-spinner"></span>
                <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
                {{ obLoading ? '建立中…' : '執行 Onboarding' }}
              </button>
            </form>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { adminApi } from '@/api/admin'

// ── 公司列表 ──────────────────────────────────────────────────────────
const companies = ref([])
const listLoading = ref(false)
const listError = ref(null)

async function loadCompanies() {
  listLoading.value = true
  listError.value = null
  try {
    const data = await adminApi.listCompanies()
    companies.value = data.companies || []
  } catch (err) {
    listError.value = err.message || '無法載入公司列表，請稍後再試'
  } finally {
    listLoading.value = false
  }
}

onMounted(loadCompanies)

// ── 快速建立公司（WP-S1-09B）─────────────────────────────────────────
const form = reactive({ id: '', name: '', timezone: 'UTC' })
const fieldErrors = reactive({ id: '', name: '' })
const createLoading = ref(false)
const createError = ref(null)
const createSuccess = ref(null)

function resetAlerts() {
  createError.value = null
  createSuccess.value = null
  fieldErrors.id = ''
  fieldErrors.name = ''
}

function validateForm() {
  let valid = true
  if (!form.id) { fieldErrors.id = '公司 ID 為必填'; valid = false }
  if (!form.name) { fieldErrors.name = '公司名稱為必填'; valid = false }
  return valid
}

async function handleCreate() {
  resetAlerts()
  if (!validateForm()) return
  createLoading.value = true
  try {
    const created = await adminApi.createCompany({
      id: form.id,
      name: form.name,
      timezone: form.timezone || 'UTC'
    })
    createSuccess.value = created.name
    form.id = ''
    form.name = ''
    form.timezone = 'UTC'
    await loadCompanies()
  } catch (err) {
    const detail = err.data?.detail
    if (err.status === 409 || detail?.code === 'DUPLICATE_COMPANY') {
      fieldErrors.id = `公司 ID「${form.id}」已存在，請使用其他 ID`
    } else if (err.status === 422) {
      const errors = detail
      if (Array.isArray(errors)) {
        errors.forEach(e => {
          const loc = e.loc?.[e.loc.length - 1]
          if (loc === 'id') fieldErrors.id = e.msg
          else if (loc === 'name') fieldErrors.name = e.msg
        })
        createError.value = '輸入資料有誤，請確認後重試'
      } else {
        createError.value = '輸入資料驗證失敗，請確認後重試'
      }
    } else if (err.status === 403) {
      createError.value = '權限不足：只有 super_admin 可建立公司'
    } else {
      createError.value = err.message || '建立失敗，請稍後再試'
    }
  } finally {
    createLoading.value = false
  }
}

// ── Onboarding（WP-S1-09D）───────────────────────────────────────────
const obForm = reactive({
  company: { id: '', name: '', timezone: 'UTC' },
  initial_user: { display_name: '', login_username: '', email: '', password: '', role_id: 'admin' }
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
    await loadCompanies()
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
      obError.value = '權限不足：只有 super_admin 可執行 Onboarding'
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
  obForm.initial_user.role_id = 'admin'
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
.btn-ob-submit { margin-top: 8px; align-self: flex-start; padding: 12px 28px; font-size: 15px; }
.btn-ob-submit svg { width: 18px; height: 18px; }
</style>
