<template>
  <div class="admin-page">
    <Navbar />

    <div class="container">
      <!-- 頁面標題 -->
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">平台管理</h1>
          <p class="admin-description">管理系統租戶與公司帳戶（super_admin 專用）</p>
        </div>
      </div>

      <!-- 主內容：左列表 + 右表單 -->
      <div class="main-layout">

        <!-- ── 左側：公司列表 ── -->
        <section class="panel panel-list">
          <div class="panel-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              公司列表
            </h2>
            <button class="btn-refresh" :disabled="listLoading" @click="loadCompanies" title="重新整理">
              <svg :class="{ spinning: listLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          <!-- Loading -->
          <div v-if="listLoading" class="state-box">
            <div class="spinner"></div>
            <span>載入中…</span>
          </div>

          <!-- Error -->
          <div v-else-if="listError" class="state-box state-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="state-title">載入失敗</p>
              <p class="state-msg">{{ listError }}</p>
            </div>
          </div>

          <!-- Empty -->
          <div v-else-if="companies.length === 0" class="state-box state-empty">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <div>
              <p class="state-title">尚無公司</p>
              <p class="state-msg">請使用右側表單建立第一間公司。</p>
            </div>
          </div>

          <!-- 公司表格 -->
          <div v-else class="table-wrapper">
            <table class="company-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>名稱</th>
                  <th>狀態</th>
                  <th>時區</th>
                  <th>建立時間</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="co in companies" :key="co.id">
                  <td class="cell-id">{{ co.id }}</td>
                  <td class="cell-name">{{ co.name }}</td>
                  <td>
                    <span :class="co.is_active ? 'badge-active' : 'badge-inactive'">
                      {{ co.is_active ? '啟用' : '停用' }}
                    </span>
                  </td>
                  <td class="cell-tz">{{ co.timezone }}</td>
                  <td class="cell-date">{{ formatDate(co.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            <p class="total-count">共 {{ companies.length }} 間公司</p>
          </div>
        </section>

        <!-- ── 右側：建立表單 ── -->
        <section class="panel panel-form">
          <div class="panel-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              建立新公司
            </h2>
          </div>

          <!-- 成功訊息 -->
          <div v-if="createSuccess" class="alert alert-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>公司 <strong>{{ createSuccess }}</strong> 建立成功！</span>
          </div>

          <!-- 錯誤訊息 -->
          <div v-if="createError" class="alert alert-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ createError }}</span>
          </div>

          <form @submit.prevent="handleCreate" class="create-form" novalidate>
            <!-- Company ID -->
            <div class="form-group">
              <label class="form-label" for="f-id">
                公司 ID
                <span class="label-hint">英文、數字、連字號，最多 50 字</span>
              </label>
              <input
                id="f-id"
                v-model.trim="form.id"
                type="text"
                class="form-input"
                :class="{ 'input-error': fieldErrors.id }"
                placeholder="e.g. company-b"
                maxlength="50"
                autocomplete="off"
              />
              <p v-if="fieldErrors.id" class="field-error">{{ fieldErrors.id }}</p>
            </div>

            <!-- Company Name -->
            <div class="form-group">
              <label class="form-label" for="f-name">
                公司名稱
                <span class="label-hint">最多 255 字</span>
              </label>
              <input
                id="f-name"
                v-model.trim="form.name"
                type="text"
                class="form-input"
                :class="{ 'input-error': fieldErrors.name }"
                placeholder="e.g. Example Corp Ltd"
                maxlength="255"
              />
              <p v-if="fieldErrors.name" class="field-error">{{ fieldErrors.name }}</p>
            </div>

            <!-- Timezone -->
            <div class="form-group">
              <label class="form-label" for="f-tz">
                時區
                <span class="label-hint">留空預設為 UTC</span>
              </label>
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

            <button
              type="submit"
              class="btn-submit"
              :disabled="createLoading"
            >
              <span v-if="createLoading" class="btn-spinner"></span>
              <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              {{ createLoading ? '建立中…' : '建立公司' }}
            </button>
          </form>
        </section>

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

// ── 建立表單 ──────────────────────────────────────────────────────────
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
/* ── CSS 變數 ────────────────────────────────────────── */
.admin-page {
  --primary: #4A6FA5;
  --primary-hover: #3D5A8A;
  --success: #16a34a;
  --success-bg: #f0fdf4;
  --success-border: #bbf7d0;
  --error: #dc2626;
  --error-bg: #fef2f2;
  --error-border: #fecaca;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --border: #E5E7EB;
  --border-input: #D1D5DB;
  --border-focus: #4A6FA5;
  min-height: 100vh;
  background-color: var(--bg-main);
  padding-bottom: 40px;
}

.container {
  padding: 24px 16px;
  max-width: 1300px;
  margin: 0 auto;
}

/* ── Header ──────────────────────────────────────────── */
.admin-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.admin-header-icon {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #7BA3D1, var(--primary));
  border-radius: 14px;
  color: white;
}

.admin-header-icon svg { width: 28px; height: 28px; }

.admin-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--heading);
  margin: 0 0 4px;
}

.admin-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

/* ── Main layout ─────────────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 1024px) {
  .main-layout { grid-template-columns: 1fr 380px; align-items: start; }
}

/* ── Panel ───────────────────────────────────────────── */
.panel {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--heading);
  margin: 0;
}

.panel-title svg { width: 18px; height: 