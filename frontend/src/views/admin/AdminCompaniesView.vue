<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">公司管理</h1>
          <p class="admin-description"><router-link to="/admin" class="back-link">← 平台管理</router-link></p>
        </div>
      </div>
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
                <tr v-for="co in companies" :key="co.id" class="company-row" :class="{selected: selectedCompany?.id === co.id}" @click="selectCompany(co)" style="cursor:pointer">
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
          <div v-if="isSuperAdmin && createSuccess" class="alert alert-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>公司 <strong>{{ createSuccess }}</strong> 建立成功！</span>
          </div>
          <div v-if="isSuperAdmin && createError" class="alert alert-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>{{ createError }}</span>
          </div>
          <form v-if="isSuperAdmin" @submit.prevent="handleCreate" class="create-form" novalidate>
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
              <div id="f-tz" class="form-input tz-fixed">Asia/Taipei（固定）</div>
            </div>
            <button type="submit" class="btn-submit" :disabled="createLoading">
              <span v-if="createLoading" class="btn-spinner"></span>
              <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
              {{ createLoading ? '建立中…' : '建立公司' }}
            </button>
          </form>
          <div v-else class="state-box">
            <span>權限說明：只有 super_admin 可建立新公司。</span>
          </div>
        </section>

        <!-- S1-11A: Company Detail / Edit Panel -->
        <section class="panel panel-detail">
          <div class="panel-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              公司詳情 / 編輯
            </h2>
          </div>
          <div v-if="!selectedCompany" class="detail-empty">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" /></svg>
            <p>點擊左側列表選取公司以查看詳情</p>
          </div>
          <div v-else class="detail-body">
            <div class="detail-meta">
              <div class="detail-meta-item"><span class="detail-meta-label">ID</span><span class="detail-meta-val mono">{{ selectedCompany.id }}</span></div>
              <div class="detail-meta-item"><span class="detail-meta-label">建立時間</span><span class="detail-meta-val">{{ formatDate(selectedCompany.created_at) }}</span></div>
              <div class="detail-meta-item"><span class="detail-meta-label">狀態</span><span :class="selectedCompany.is_active ? 'badge-active' : 'badge-inactive'">{{ selectedCompany.is_active ? '啟用' : '停用' }}</span></div>
            </div>

            <div v-if="detailSuccess" class="alert alert-success" style="margin:0 0 12px">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>{{ detailSuccess }}</span>
            </div>
            <div v-if="detailError" class="alert alert-error" style="margin:0 0 12px">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>{{ detailError }}</span>
            </div>

            <form @submit.prevent="handleUpdate" class="detail-form" novalidate>
              <div class="form-group">
                <label class="form-label" for="d-name">公司名稱</label>
                <input id="d-name" v-model.trim="editForm.name" type="text" class="form-input" maxlength="255" />
              </div>
              <div class="form-group">
                <label class="form-label" for="d-tz">時區</label>
                <select id="d-tz" v-model="editForm.timezone" class="form-input">
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
              <div class="detail-actions">
                <button type="submit" class="btn-submit" :disabled="detailLoading">
                  <span v-if="detailLoading" class="btn-spinner"></span>
                  <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  {{ detailLoading ? '儲存中…' : '儲存變更' }}
                </button>
                <button type="button" class="btn-toggle" :disabled="detailLoading" @click="handleToggleActive">
                  {{ selectedCompany.is_active ? '停用公司' : '啟用公司' }}
                </button>
              </div>
            </form>
          </div>
        </section>

        <!-- Members Panel -->
        <section v-if="selectedCompany" class="members-section">
          <div class="panel-header members-section-header">
            <h2 class="panel-title">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              成員管理 — {{ selectedCompany.name }}
            </h2>
            <button class="btn-refresh" :disabled="membersLoading" @click="loadMembers" title="重新整理">
              <svg :class="{ spinning: membersLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>

          <div class="members-body">
            <div v-if="membersLoading" class="state-box"><div class="spinner"></div><span>載入中…</span></div>
            <div v-else-if="membersError" class="state-box state-error">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>{{ membersError }}</span>
            </div>
            <div v-else-if="members.length === 0" class="state-box state-empty">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
              <span>尚無成員，使用下方表單新增</span>
            </div>
            <div v-else class="members-table-wrapper">
              <table class="members-table">
                <thead><tr><th>登入帳號</th><th>顯示名稱</th><th>角色</th><th>狀態</th><th>加入時間</th><th>操作</th></tr></thead>
                <tbody>
                  <tr v-for="m in members" :key="m.membership_id">
                    <td class="cell-id">{{ m.login_username }}</td>
                    <td>{{ m.display_name }}</td>
                    <td><span class="role-badge">{{ m.role_id }}</span></td>
                    <td>
                      <span :class="m.membership_is_active ? 'badge-active' : 'badge-inactive'">
                        {{ m.membership_is_active ? '啟用' : '停用' }}
                      </span>
                    </td>
                    <td class="cell-date">{{ formatDate(m.membership_created_at) }}</td>
                    <td>
                      <button
                        class="btn-mem-toggle"
                        :disabled="memberActionLoading === m.membership_id"
                        @click="handleToggleMembership(m)"
                      >
                        {{ m.membership_is_active ? '停用' : '啟用' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p class="total-count">共 {{ members.length }} 位成員</p>
            </div>

            <!-- Add member form -->
            <div class="add-member-section">
              <div class="add-member-header" @click="showAddMember = !showAddMember" style="cursor:pointer">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
                <span>新增成員</span>
                <svg class="chevron" :class="{open: showAddMember}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
              </div>
              <div v-if="showAddMember" class="add-member-body">
                <div v-if="addMemberSuccess" class="alert alert-success" style="margin:0 0 12px">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>{{ addMemberSuccess }}</span>
                </div>
                <div v-if="addMemberError" class="alert alert-error" style="margin:0 0 12px">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>{{ addMemberError }}</span>
                </div>
                <form @submit.prevent="handleAddMember" class="add-member-form" novalidate>
                  <div class="am-grid">
                    <div class="form-group">
                      <label class="form-label" for="am-dispname">顯示名稱 <span class="label-hint">必填</span></label>
                      <input id="am-dispname" v-model.trim="addForm.display_name" type="text" class="form-input" maxlength="100" />
                    </div>
                    <div class="form-group">
                      <label class="form-label" for="am-username">登入帳號 <span class="label-hint">必填</span></label>
                      <input id="am-username" v-model.trim="addForm.login_username" type="text" class="form-input" maxlength="100" autocomplete="off" />
                    </div>
                    <div class="form-group">
                      <label class="form-label" for="am-password">初始密碼 <span class="label-hint">最少 6 字</span></label>
                      <input id="am-password" v-model="addForm.password" type="password" class="form-input" maxlength="255" autocomplete="new-password" />
                    </div>
                    <div class="form-group">
                      <label class="form-label" for="am-email">Email <span class="label-hint">選填</span></label>
                      <input id="am-email" v-model.trim="addForm.email" type="email" class="form-input" maxlength="255" />
                    </div>
                    <div class="form-group">
                      <label class="form-label" for="am-role">角色</label>
                      <select id="am-role" v-model="addForm.role_id" class="form-input">
                        <option value="employee">employee（員工）</option>
                        <option value="company_admin">company_admin（公司管理員）</option>
                      </select>
                    </div>
                  </div>
                  <button type="submit" class="btn-submit" style="margin-top:4px" :disabled="addMemberLoading">
                    <span v-if="addMemberLoading" class="btn-spinner"></span>
                    <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
                    {{ addMemberLoading ? '新增中…' : '新增成員' }}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { useAuthStore } from '@/stores/auth'
import { adminApi } from '@/api/admin'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.isSuperAdmin)

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
      timezone: 'Asia/Taipei'
    })
    createSuccess.value = created.name
    form.id = ''
    form.name = ''
    form.timezone = 'Asia/Taipei'
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

// ── S1-11A: Company Detail / Edit ──────────────────────────────────
const selectedCompany = ref(null)
const editForm = reactive({ name: '', timezone: 'UTC' })
const detailLoading = ref(false)
const detailError = ref(null)
const detailSuccess = ref(null)

function selectCompany(co) {
  selectedCompany.value = co
  editForm.name = co.name
  editForm.timezone = co.timezone
  detailError.value = null
  detailSuccess.value = null
  // reset members panel
  members.value = []
  showAddMember.value = false
  addMemberSuccess.value = null
  addMemberError.value = null
  loadMembers()
}

async function handleUpdate() {
  if (!selectedCompany.value) return
  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    const updated = await adminApi.updateCompany(selectedCompany.value.id, {
      name: editForm.name,
      timezone: editForm.timezone
    })
    selectedCompany.value = updated
    detailSuccess.value = '變更已儲存'
    await loadCompanies()
  } catch (err) {
    detailError.value = err.message || '更新失敗，請稍後再試'
  } finally {
    detailLoading.value = false
  }
}

async function handleToggleActive() {
  if (!selectedCompany.value) return
  const target = !selectedCompany.value.is_active
  const label = target ? '啟用' : '停用'
  if (!confirm(`確認要${label}公司「${selectedCompany.value.name}」？`)) return
  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    const updated = await adminApi.updateCompany(selectedCompany.value.id, { is_active: target })
    selectedCompany.value = updated
    detailSuccess.value = `公司已${label}`
    await loadCompanies()
  } catch (err) {
    detailError.value = err.message || `${label}失敗，請稍後再試`
  } finally {
    detailLoading.value = false
  }
}

function formatDate(val) {
  if (!val) return '—'
  const d = new Date(val)
  return d.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei', hour12: false })
}

// ── Members Management ──────────────────────────────────────────────
const members = ref([])
const membersLoading = ref(false)
const membersError = ref(null)
const memberActionLoading = ref(null)

const showAddMember = ref(false)
const addForm = reactive({ display_name: '', login_username: '', password: '', email: '', role_id: 'employee' })
const addMemberLoading = ref(false)
const addMemberSuccess = ref(null)
const addMemberError = ref(null)

async function loadMembers() {
  if (!selectedCompany.value) return
  membersLoading.value = true
  membersError.value = null
  try {
    const data = await adminApi.listCompanyMembers(selectedCompany.value.id)
    members.value = data.members || []
  } catch (err) {
    membersError.value = err.message || '無法載入成員列表'
  } finally {
    membersLoading.value = false
  }
}

async function handleToggleMembership(m) {
  const target = !m.membership_is_active
  const label = target ? '啟用' : '停用'
  if (!confirm(`確認要${label}成員「${m.display_name}」的帳號？`)) return
  memberActionLoading.value = m.membership_id
  try {
    await adminApi.toggleMembershipActive(selectedCompany.value.id, m.membership_id, target)
    await loadMembers()
  } catch (err) {
    alert(err.message || `${label}失敗`)
  } finally {
    memberActionLoading.value = null
  }
}

async function handleAddMember() {
  addMemberSuccess.value = null
  addMemberError.value = null
  if (!addForm.display_name || !addForm.login_username || !addForm.password) {
    addMemberError.value = '顯示名稱、登入帳號、初始密碼為必填'
    return
  }
  addMemberLoading.value = true
  try {
    const created = await adminApi.createCompanyMember(selectedCompany.value.id, {
      display_name: addForm.display_name,
      login_username: addForm.login_username,
      password: addForm.password,
      email: addForm.email || undefined,
      role_id: addForm.role_id,
    })
    addMemberSuccess.value = `成員「${created.display_name}」已新增`
    addForm.display_name = ''
    addForm.login_username = ''
    addForm.password = ''
    addForm.email = ''
    addForm.role_id = 'employee'
    await loadMembers()
  } catch (err) {
    const code = err.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      addMemberError.value = `登入帳號「${addForm.login_username}」已存在於此公司`
    } else if (code === 'INVALID_ROLE') {
      addMemberError.value = '角色無效'
    } else {
      addMemberError.value = err.message || '新增失敗，請稍後再試'
    }
  } finally {
    addMemberLoading.value = false
  }
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

/* ── S1-11A: Company Detail Panel ── */
.main-layout { grid-template-columns: 1fr; }

.panel-detail { min-height: 200px; }

.detail-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 48px 24px; color: var(--text-secondary); font-size: 13px; text-align: center; }
.detail-empty svg { width: 32px; height: 32px; opacity: 0.35; }
.detail-empty p { margin: 0; }

.detail-body { padding: 20px 24px 24px; display: flex; flex-direction: column; gap: 16px; }

.detail-meta { display: flex; flex-direction: column; gap: 8px; background: #F8FAFC; border-radius: 10px; padding: 14px 16px; }
.detail-meta-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.detail-meta-label { font-weight: 600; color: var(--text-secondary); min-width: 72px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
.detail-meta-val { color: var(--text-primary); }
.mono { font-family: monospace; font-size: 12px; }

.detail-form { display: flex; flex-direction: column; gap: 14px; }

.detail-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }

.btn-toggle { padding: 10px 16px; background: transparent; border: 1.5px solid var(--border-input); border-radius: 10px; font-size: 13px; font-weight: 600; color: var(--text-primary); cursor: pointer; transition: all 0.2s; }
.btn-toggle:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); background: #F0F4F8; }
.btn-toggle:disabled { opacity: 0.5; cursor: not-allowed; }

/* selected row highlight */
.company-row.selected td { background: #EBF2FB !important; }

/* ── Members Panel ── */
.members-section { background: var(--bg-card); border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; margin-top: 24px; }
.members-section-header { background: linear-gradient(135deg, #EFF6FF, #DBEAFE); border-bottom: 1px solid #BFDBFE; }
.members-body { padding: 0; }

.members-table-wrapper { overflow-x: auto; }
.members-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.members-table th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; background: #F8FAFC; border-bottom: 1px solid var(--border); white-space: nowrap; }
.members-table td { padding: 11px 14px; border-bottom: 1px solid #F1F5F9; color: var(--text-primary); vertical-align: middle; }
.members-table tbody tr:hover td { background: #F8FAFC; }
.members-table tbody tr:last-child td { border-bottom: none; }

.role-badge { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }

.btn-mem-toggle { padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 6px; border: 1px solid var(--border-input); background: transparent; color: var(--text-primary); cursor: pointer; transition: all 0.15s; }
.btn-mem-toggle:hover:not(:disabled) { border-color: var(--primary); color: var(--primary); background: #F0F4F8; }
.btn-mem-toggle:disabled { opacity: 0.45; cursor: not-allowed; }

/* Add member section */
.add-member-section { border-top: 1px solid var(--border); }
.add-member-header { display: flex; align-items: center; gap: 8px; padding: 14px 20px; font-size: 13px; font-weight: 600; color: var(--primary); user-select: none; }
.add-member-header svg { width: 16px; height: 16px; }
.add-member-header .chevron { width: 14px; height: 14px; margin-left: auto; transition: transform 0.2s; }
.add-member-header .chevron.open { transform: rotate(180deg); }
.add-member-body { padding: 0 20px 20px; }
.add-member-form { display: flex; flex-direction: column; gap: 12px; }
.am-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 767px) { .am-grid { grid-template-columns: 1fr; } }
</style>
