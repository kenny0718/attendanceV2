<template>
  <div class="admin-page">
    <Navbar />
    <div class="container">
      <div class="admin-header">
        <div class="admin-header-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 class="admin-title">使用者 / 成員查看</h1>
          <p class="admin-description"><router-link to="/admin" class="back-link">← 平台管理</router-link></p>
        </div>
      </div>

      <!-- Company Selector -->
      <div class="panel selector-panel">
        <div class="panel-header">
          <h2 class="panel-title">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5" />
            </svg>
            選擇公司
          </h2>
          <button class="btn-refresh" :disabled="companiesLoading" @click="loadCompanies" title="重新整理公司列表">
            <svg :class="{ spinning: companiesLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <div class="selector-body">
          <div v-if="companiesLoading" class="state-box">
            <div class="spinner"></div><span>載入公司列表中…</span>
          </div>
          <div v-else-if="companiesError" class="state-box state-error">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div><p class="state-title">載入失敗</p><p class="state-msg">{{ companiesError }}</p></div>
          </div>
          <div v-else class="selector-row">
            <select v-model="selectedCompanyId" class="company-select" @change="onCompanyChange">
              <option value="">— 請選擇公司 —</option>
              <option v-for="co in companies" :key="co.id" :value="co.id">
                {{ co.name }} ({{ co.id }})
              </option>
            </select>
            <span v-if="companies.length > 0" class="company-count">共 {{ companies.length }} 間公司</span>
          </div>
        </div>
      </div>

      <!-- Add Member Panel (WP-S1-10D) -->
      <div class="panel add-member-panel" v-if="selectedCompanyId">
        <div class="panel-header">
          <h2 class="panel-title">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            新增成員
          </h2>
        </div>
        <div class="add-member-body">
          <div v-if="addMemberSuccess" class="add-msg add-msg-success">
            ✓ 成員「{{ addMemberSuccessName }}」已成功建立！
            <button class="add-msg-close" @click="addMemberSuccess = false">✕</button>
          </div>
          <div v-if="addMemberError" class="add-msg add-msg-error">
            {{ addMemberError }}
            <button class="add-msg-close" @click="addMemberError = null">✕</button>
          </div>
          <form class="add-member-form" @submit.prevent="handleAddMember">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">顯示名稱 <span class="required">*</span></label>
                <input v-model="newMember.display_name" class="form-input" type="text" placeholder="例：張小明" maxlength="100" required />
              </div>
              <div class="form-group">
                <label class="form-label">Email</label>
                <input v-model="newMember.email" class="form-input" type="email" placeholder="example@company.com" maxlength="255" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">登入帳號 <span class="required">*</span></label>
                <input v-model="newMember.login_username" class="form-input" type="text" placeholder="例：zhang.xiaoming" maxlength="100" required />
              </div>
              <div class="form-group">
                <label class="form-label">初始密碼 <span class="required">*</span></label>
                <input v-model="newMember.password" class="form-input" type="password" placeholder="至少 6 個字元" minlength="6" maxlength="255" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">角色 <span class="required">*</span></label>
                <select v-model="newMember.role_id" class="form-input">
                  <option value="employee">employee</option>
                  <option value="hr_manager">hr_manager</option>
                  <option value="company_admin">company_admin</option>
                </select>
              </div>
              <div class="form-group form-group-action">
                <button type="submit" class="btn-add-member" :disabled="addMemberLoading">
                  <span v-if="addMemberLoading" class="btn-spinner-sm"></span>
                  <span v-else>建立成員</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      <!-- Members Panel -->
      <div class="panel members-panel" v-if="selectedCompanyId">
        <div class="panel-header">
          <h2 class="panel-title">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            {{ selectedCompanyId }} 的成員
          </h2>
          <button class="btn-refresh" :disabled="membersLoading" @click="loadMembers" title="重新整理">
            <svg :class="{ spinning: membersLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        <!-- Filter bar (S1-10F) -->
        <div v-if="!membersLoading && !membersError && members.length > 0" class="filter-bar">
          <div class="filter-search">
            <svg class="filter-search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="searchQuery"
              class="filter-input"
              type="text"
              placeholder="搜尋名稱 / 帳號 / Email…"
            />
          </div>
          <select v-model="filterStatus" class="filter-select">
            <option value="all">全部狀態</option>
            <option value="active">有效成員</option>
            <option value="inactive">停用成員</option>
          </select>
          <select v-model="filterRole" class="filter-select">
            <option value="all">全部角色</option>
            <option v-for="r in uniqueRoles" :key="r" :value="r">{{ r }}</option>
          </select>
          <button v-if="isFiltered" class="filter-clear" @click="clearFilters" title="清除篩選">✕ 清除</button>
        </div>

        <!-- loading -->
        <div v-if="membersLoading" class="state-box">
          <div class="spinner"></div><span>載入成員中…</span>
        </div>

        <!-- error -->
        <div v-else-if="membersError" class="state-box state-error">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div><p class="state-title">載入失敗</p><p class="state-msg">{{ membersError }}</p></div>
        </div>

        <!-- empty -->
        <div v-else-if="members.length === 0" class="state-box">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <div><p class="state-title">尚無成員</p><p class="state-msg">此公司目前沒有任何成員。</p></div>
        </div>

        <!-- success: table -->
        <div v-else class="table-wrapper">
          <!-- toggle error banner -->
          <div v-if="toggleError" class="toggle-error-bar">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>{{ toggleError }}</span>
            <button class="toggle-error-close" @click="toggleError = null">✕</button>
          </div>

          <!-- no-result after filter -->
          <div v-if="filteredMembers.length === 0" class="state-box">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <div>
              <p class="state-title">沒有符合的成員</p>
              <p class="state-msg">請調整搜尋條件或<button class="link-btn" @click="clearFilters">清除篩選</button></p>
            </div>
          </div>

          <table v-else class="members-table">
            <thead>
              <tr>
                <th>成員</th>
                <th>角色</th>
                <th>成員狀態</th>
                <th>帳號狀態</th>
                <th>加入時間</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in filteredMembers" :key="m.membership_id">
                <td class="cell-member">
                  <span class="cell-name">{{ m.display_name }}</span>
                  <span class="cell-sub">{{ m.login_username }}</span>
                  <span v-if="m.email" class="cell-sub cell-email">{{ m.email }}</span>
                </td>
                <td><span class="role-badge" :class="'role-' + m.role_id">{{ m.role_id }}</span></td>
                <td>
                  <span :class="m.membership_is_active ? 'badge-active' : 'badge-inactive'">
                    {{ m.membership_is_active ? '有效' : '停用' }}
                  </span>
                </td>
                <td>
                  <span :class="m.user_is_active ? 'badge-active' : 'badge-inactive'">
                    {{ m.user_is_active ? '啟用' : '停用' }}
                  </span>
                </td>
                <td class="cell-date">{{ formatDate(m.membership_created_at) }}</td>
                <td class="cell-action">
                  <button class="btn-edit" @click="openEdit(m)" title="編輯成員">編輯</button>
                  <button class="btn-pwd" @click="openPwd(m)" title="重設密碼">密碼</button>
                  <button
                    v-if="m.membership_is_active"
                    class="btn-toggle btn-deactivate"
                    :disabled="togglingId === m.membership_id"
                    @click="handleToggle(m, false)"
                  >
                    <span v-if="togglingId === m.membership_id" class="btn-spinner-sm"></span>
                    <span v-else>停用</span>
                  </button>
                  <button
                    v-else
                    class="btn-toggle btn-activate"
                    :disabled="togglingId === m.membership_id"
                    @click="handleToggle(m, true)"
                  >
                    <span v-if="togglingId === m.membership_id" class="btn-spinner-sm"></span>
                    <span v-else>啟用</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <p class="total-count">
            <span v-if="isFiltered">篩選結果：{{ filteredMembers.length }} / {{ members.length }} 名成員</span>
            <span v-else>共 {{ members.length }} 名成員</span>
          </p>
        </div>
      </div>

      <!-- Initial state: no company selected -->
      <div v-else class="state-box state-initial">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
        </svg>
        <div><p class="state-title">請先選擇公司</p><p class="state-msg">從上方下拉選單選擇要查看的公司。</p></div>
      </div>

    </div>
  </div>

  <!-- WP-TECHDEBT-VUE-01: Edit Member Modal (extracted component) -->
  <MemberEditModal
    :open="editModalOpen"
    :member="editModalMember"
    :companyId="selectedCompanyId"
    @close="editModalOpen = false"
    @saved="onMemberSaved"
  />

  <!-- WP-TECHDEBT-VUE-01: Reset Password Modal (extracted component) -->
  <MemberPasswordModal
    :open="pwdModalOpen"
    :member="pwdModalMember"
    :companyId="selectedCompanyId"
    @close="pwdModalOpen = false"
  />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { adminApi } from '@/api/admin'
import MemberEditModal from '@/components/admin/MemberEditModal.vue'
import MemberPasswordModal from '@/components/admin/MemberPasswordModal.vue'

// ── Companies ─────────────────────────────────────────────────────────
const companies = ref([])
const companiesLoading = ref(false)
const companiesError = ref(null)

async function loadCompanies() {
  companiesLoading.value = true
  companiesError.value = null
  try {
    const data = await adminApi.listCompanies()
    companies.value = data.companies || []
  } catch (err) {
    companiesError.value = err.message || '無法載入公司列表，請稍後再試'
  } finally {
    companiesLoading.value = false
  }
}

onMounted(loadCompanies)

// ── Members ───────────────────────────────────────────────────────────
const selectedCompanyId = ref('')
const members = ref([])
const membersLoading = ref(false)
const membersError = ref(null)

async function loadMembers() {
  if (!selectedCompanyId.value) return
  membersLoading.value = true
  membersError.value = null
  try {
    const data = await adminApi.listCompanyMembers(selectedCompanyId.value)
    members.value = data.members || []
  } catch (err) {
    membersError.value = err.message || '無法載入成員列表，請稍後再試'
  } finally {
    membersLoading.value = false
  }
}

function onCompanyChange() {
  members.value = []
  membersError.value = null
  searchQuery.value = ''
  filterStatus.value = 'all'
  filterRole.value = 'all'
  loadMembers()
}

// ── Toggle membership active ──────────────────────────────────────────
const togglingId = ref(null)
const toggleError = ref(null)

async function handleToggle(member, newState) {
  const action = newState ? '啟用' : '停用'
  const confirmed = confirm(`確定要${action}「${member.display_name}（${member.login_username}）」的成員資格嗎？`)
  if (!confirmed) return

  togglingId.value = member.membership_id
  toggleError.value = null
  try {
    await adminApi.toggleMembershipActive(selectedCompanyId.value, member.membership_id, newState)
    // Local update to avoid full reload
    const idx = members.value.findIndex(m => m.membership_id === member.membership_id)
    if (idx !== -1) members.value[idx].membership_is_active = newState
  } catch (err) {
    toggleError.value = err.message || `${action}失敗，請稍後再試`
  } finally {
    togglingId.value = null
  }
}

// ── Add Member (WP-S1-10D) ───────────────────────────────────────────
const newMember = ref({ display_name: '', email: '', login_username: '', password: '', role_id: 'employee' })
const addMemberLoading = ref(false)
const addMemberError = ref(null)
const addMemberSuccess = ref(false)

async function handleAddMember() {
  addMemberLoading.value = true
  addMemberError.value = null
  addMemberSuccess.value = false
  try {
    await adminApi.createCompanyMember(selectedCompanyId.value, {
      display_name: newMember.value.display_name,
      email: newMember.value.email || null,
      login_username: newMember.value.login_username,
      password: newMember.value.password,
      role_id: newMember.value.role_id,
    })
    addMemberSuccessName.value = newMember.value.display_name
    addMemberSuccess.value = true
    newMember.value = { display_name: '', email: '', login_username: '', password: '', role_id: 'employee' }
    // Reset filters so new member is visible
    searchQuery.value = ''
    filterStatus.value = 'all'
    filterRole.value = 'all' 
    await loadMembers()
  } catch (err) {
    const code = err?.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      addMemberError.value = '此公司已有相同的登入帳號，請更換。'
    } else if (code === 'INVALID_ROLE') {
      addMemberError.value = '角色不存在，請選擇有效角色。'
    } else {
      addMemberError.value = err?.data?.detail?.message || err.message || '建立失敗，請稍後再試'
    }
  } finally {
    addMemberLoading.value = false
  }
}

// ── S1-10F: Client-side search / filter ──────────────────────────────
const searchQuery = ref('')
const filterStatus = ref('all') // 'all' | 'active' | 'inactive'
const filterRole = ref('all')   // 'all' | role_id string
const addMemberSuccessName = ref('')

const uniqueRoles = computed(() => {
  const roles = new Set(members.value.map(m => m.role_id))
  return [...roles].sort()
})

const filteredMembers = computed(() => {
  let list = members.value
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(m =>
      (m.display_name || '').toLowerCase().includes(q) ||
      (m.login_username || '').toLowerCase().includes(q) ||
      (m.email || '').toLowerCase().includes(q)
    )
  }
  if (filterStatus.value === 'active') list = list.filter(m => m.membership_is_active)
  if (filterStatus.value === 'inactive') list = list.filter(m => !m.membership_is_active)
  if (filterRole.value !== 'all') list = list.filter(m => m.role_id === filterRole.value)
  return list
})

const isFiltered = computed(() =>
  searchQuery.value.trim() !== '' || filterStatus.value !== 'all' || filterRole.value !== 'all'
)

function clearFilters() {
  searchQuery.value = ''
  filterStatus.value = 'all'
  filterRole.value = 'all'
}


// ── WP-TECHDEBT-VUE-01: Edit Member Modal (extracted to MemberEditModal.vue) ──
const editModalOpen = ref(false)
const editModalMember = ref(null)

function openEdit(member) {
  editModalMember.value = member
  editModalOpen.value = true
}

function onMemberSaved(updatedMember) {
  const idx = members.value.findIndex(m => m.membership_id === updatedMember.membership_id)
  if (idx !== -1) {
    members.value[idx].display_name = updatedMember.display_name
    members.value[idx].email = updatedMember.email
    members.value[idx].role_id = updatedMember.role_id
    members.value[idx].login_username = updatedMember.login_username
  }
}

// ── WP-TECHDEBT-VUE-01: Reset Password Modal (extracted to MemberPasswordModal.vue) ──
const pwdModalOpen = ref(false)
const pwdModalMember = ref(null)

function openPwd(member) {
  pwdModalMember.value = member
  pwdModalOpen.value = true
}

// ── Utils ─────────────────────────────────────────────────────────────
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
  --primary: #4A6FA5;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --bg-main: #F4F7F9;
  --bg-card: #FFFFFF;
  --border: #E5E7EB;
  --error: #dc2626;
  min-height: 100vh;
  background-color: var(--bg-main);
  padding-bottom: 48px;
}
.container { padding: 24px 16px; max-width: 1300px; margin: 0 auto; }
@media (min-width: 768px) { .container { padding: 32px; } }

/* Header */
.admin-header { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }
.admin-header-icon {
  width: 52px; height: 52px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #93c5fd, #3b82f6);
  border-radius: 14px; color: white;
}
.admin-header-icon svg { width: 28px; height: 28px; }
.admin-title { font-size: 26px; font-weight: 700; color: var(--heading); margin: 0 0 4px; }
.admin-description { font-size: 13px; color: var(--text-secondary); margin: 0; }
.back-link { color: var(--primary); text-decoration: none; }
.back-link:hover { text-decoration: underline; }

/* Panel */
.panel { background: var(--bg-card); border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; margin-bottom: 24px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); }
.panel-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--heading); margin: 0; }
.panel-title svg { width: 18px; height: 18px; color: var(--primary); }

/* Refresh */
.btn-refresh { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
.btn-refresh:hover:not(:disabled) { background: #F0F4F8; color: var(--primary); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 16px; height: 16px; }
.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Selector */
.selector-body { padding: 20px 24px; }
.selector-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.company-select {
  flex: 1; min-width: 260px; max-width: 480px;
  padding: 10px 14px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 14px; color: var(--text-primary); background: #fff;
  outline: none; cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.company-select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.company-count { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }

/* State boxes */
.state-box { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 48px 24px; color: var(--text-secondary); font-size: 14px; }
.state-box svg { width: 36px; height: 36px; flex-shrink: 0; opacity: 0.4; }
.state-error { color: var(--error); }
.state-error svg { opacity: 1; }
.state-initial svg { opacity: 0.3; }
.state-title { font-weight: 600; margin: 0 0 4px; font-size: 15px; }
.state-msg { margin: 0; font-size: 13px; opacity: 0.8; }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }

/* Members table */
.table-wrapper { overflow-x: auto; }
.members-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.members-table th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; background: #F8FAFC; border-bottom: 1px solid var(--border); white-space: nowrap; }
.members-table td { padding: 12px 16px; border-bottom: 1px solid #F1F5F9; color: var(--text-primary); vertical-align: middle; }
.members-table tbody tr:hover td { background: #F8FAFC; }
.members-table tbody tr:last-child td { border-bottom: none; }
.cell-name { font-weight: 500; }
.cell-mono { font-family: monospace; font-size: 12px; }
.cell-email { font-size: 12px; color: var(--text-secondary); }
.cell-date { font-size: 12px; white-space: nowrap; color: var(--text-secondary); }
.total-count { padding: 10px 16px; font-size: 12px; color: var(--text-secondary); text-align: right; margin: 0; border-top: 1px solid var(--border); }

/* Badges */
.badge-active { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #dcfce7; color: #15803d; }
.badge-inactive { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #f1f5f9; color: #64748b; }

/* Role badges */
.role-badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.role-admin { background: #dbeafe; color: #1d4ed8; }
.role-company_admin { background: #dbeafe; color: #1d4ed8; }
.role-hr_manager { background: #ede9fe; color: #6d28d9; }
.role-employee { background: #f1f5f9; color: #475569; }

/* ── Toggle action column ── */
.cell-action { white-space: nowrap; }
.btn-toggle {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 52px; padding: 4px 12px;
  border: none; border-radius: 6px;
  font-size: 12px; font-weight: 600; cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}
.btn-toggle:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-toggle:active:not(:disabled) { transform: scale(0.96); }
.btn-deactivate { background: #fef2f2; color: #dc2626; }
.btn-deactivate:hover:not(:disabled) { background: #fee2e2; }
.btn-activate { background: #f0fdf4; color: #16a34a; }
.btn-activate:hover:not(:disabled) { background: #dcfce7; }
.btn-spinner-sm {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid currentColor; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}

/* ── Toggle error bar ── */
.toggle-error-bar {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; background: #fef2f2;
  border-bottom: 1px solid #fecaca; color: #dc2626; font-size: 13px;
}
.toggle-error-bar svg { width: 16px; height: 16px; flex-shrink: 0; }
.toggle-error-bar span { flex: 1; }
.toggle-error-close {
  background: none; border: none; color: #dc2626;
  cursor: pointer; font-size: 14px; padding: 0 4px;
}
/* ── Add Member Panel (WP-S1-10D) ── */
.add-member-body { padding: 20px 24px; }
.add-member-form { display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.form-group { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.form-group-action { flex: 0 0 auto; justify-content: flex-end; }
.form-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.required { color: var(--error); }
.form-input {
  padding: 9px 12px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 14px; color: var(--text-primary); background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.btn-add-member {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 9px 20px; background: var(--primary); color: #fff;
  border: none; border-radius: 8px; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s; white-space: nowrap; min-width: 90px;
  align-self: flex-end;
}
.btn-add-member:hover:not(:disabled) { opacity: 0.88; }
.btn-add-member:disabled { opacity: 0.55; cursor: not-allowed; }
.add-msg {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 8px;
}
.add-msg-success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.add-msg-error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.add-msg-close { background: none; border: none; cursor: pointer; color: inherit; font-size: 14px; padding: 0 4px; }


/* ── S1-10F: Filter bar ── */
.filter-bar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 14px 24px; border-bottom: 1px solid var(--border); background: #FAFBFC;
}
.filter-search {
  position: relative; flex: 1; min-width: 200px;
}
.filter-search-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  width: 15px; height: 15px; color: var(--text-secondary); pointer-events: none;
}
.filter-input {
  width: 100%; padding: 7px 10px 7px 32px;
  border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 13px; color: var(--text-primary); background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}
.filter-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.filter-select {
  padding: 7px 10px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 13px; color: var(--text-primary); background: #fff; outline: none;
  cursor: pointer; transition: border-color 0.2s;
}
.filter-select:focus { border-color: var(--primary); }
.filter-clear {
  padding: 6px 12px; border: 1px solid #fecaca; border-radius: 8px;
  background: #fef2f2; color: #dc2626; font-size: 12px; font-weight: 600;
  cursor: pointer; white-space: nowrap; transition: background 0.15s;
}
.filter-clear:hover { background: #fee2e2; }

/* ── S1-10F: cell-member stacked layout ── */
.cell-member { display: flex; flex-direction: column; gap: 2px; }
.cell-name { font-weight: 600; color: var(--text-primary); font-size: 13px; }
.cell-sub { font-size: 11px; color: var(--text-secondary); font-family: monospace; }
.cell-email { font-family: inherit; }

/* ── S1-10F: link-btn inline ── */
.link-btn {
  background: none; border: none; color: var(--primary);
  cursor: pointer; font-size: 13px; padding: 0; text-decoration: underline;
}

/* S1-13A1/S1-13A3: Action buttons (remain in parent table, modals extracted to components) */
.btn-edit {
  padding: 4px 12px; font-size: 12px; font-weight: 600;
  border: 1px solid var(--primary); border-radius: 6px;
  background: transparent; color: var(--primary); cursor: pointer;
  transition: all 0.15s; margin-right: 6px;
}
.btn-edit:hover { background: var(--primary); color: #fff; }
.btn-pwd {
  padding: 4px 10px; font-size: 12px; font-weight: 600;
  border: 1px solid #f97316; border-radius: 6px;
  background: transparent; color: #f97316; cursor: pointer;
  transition: all 0.15s; margin-left: 4px;
}
.btn-pwd:hover { background: #f97316; color: #fff; }
</style>