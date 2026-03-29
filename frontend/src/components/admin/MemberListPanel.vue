<template>
  <div class="panel members-panel">
    <div class="panel-header">
      <h2 class="panel-title">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        {{ companyId }} 的成員
      </h2>
      <button class="btn-refresh" :disabled="loading" @click="$emit('reload')" title="重新整理">
        <svg :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- Filter bar -->
    <div v-if="!loading && !error && members.length > 0" class="filter-bar">
      <div class="filter-search">
        <svg class="filter-search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="searchQuery" class="filter-input" type="text" placeholder="搜尋名稱 / 帳號 / Email…" />
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
    <div v-if="loading" class="state-box">
      <div class="spinner"></div><span>載入成員中…</span>
    </div>

    <!-- error -->
    <div v-else-if="error" class="state-box state-error">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div><p class="state-title">載入失敗</p><p class="state-msg">{{ error }}</p></div>
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
        <button class="toggle-error-close" @click="$emit('update:toggleError', null)">✕</button>
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
              <button class="btn-edit" @click="$emit('edit', m)" title="編輯成員">編輯</button>
              <button class="btn-pwd" @click="$emit('password', m)" title="重設密碼">密碼</button>
              <button
                v-if="m.membership_is_active"
                class="btn-toggle btn-deactivate"
                :disabled="togglingId === m.membership_id"
                @click="$emit('toggle', m, false)"
              >
                <span v-if="togglingId === m.membership_id" class="btn-spinner-sm"></span>
                <span v-else>停用</span>
              </button>
              <button
                v-else
                class="btn-toggle btn-activate"
                :disabled="togglingId === m.membership_id"
                @click="$emit('toggle', m, true)"
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
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  members:     { type: Array,   required: true },
  loading:     { type: Boolean, required: true },
  error:       { type: String,  default: null },
  companyId:   { type: String,  required: true },
  togglingId:  { type: [String, Number], default: null },
  toggleError: { type: String,  default: null },
})

defineEmits(['edit', 'password', 'toggle', 'reload', 'update:toggleError'])

// Local filter state
const searchQuery  = ref('')
const filterStatus = ref('all')
const filterRole   = ref('all')

const uniqueRoles = computed(() => {
  const roles = new Set(props.members.map(m => m.role_id))
  return [...roles].sort()
})

const filteredMembers = computed(() => {
  let list = props.members
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(m =>
      (m.display_name   || '').toLowerCase().includes(q) ||
      (m.login_username || '').toLowerCase().includes(q) ||
      (m.email          || '').toLowerCase().includes(q)
    )
  }
  if (filterStatus.value === 'active')   list = list.filter(m =>  m.membership_is_active)
  if (filterStatus.value === 'inactive') list = list.filter(m => !m.membership_is_active)
  if (filterRole.value !== 'all')        list = list.filter(m =>  m.role_id === filterRole.value)
  return list
})

const isFiltered = computed(() =>
  searchQuery.value.trim() !== '' || filterStatus.value !== 'all' || filterRole.value !== 'all'
)

function clearFilters() {
  searchQuery.value  = ''
  filterStatus.value = 'all'
  filterRole.value   = 'all'
}

// Reset filters when company changes
watch(() => props.companyId, () => {
  clearFilters()
})

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
.members-panel {
  --primary: #4A6FA5;
  --heading: #1C3B6B;
  --text-primary: #2D3A52;
  --text-secondary: #5A6C7D;
  --bg-card: #FFFFFF;
  --border: #E5E7EB;
  --error: #dc2626;
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  overflow: hidden;
  margin-bottom: 24px;
}
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); }
.panel-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--heading); margin: 0; }
.panel-title svg { width: 18px; height: 18px; color: var(--primary); }
.btn-refresh { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); border-radius: 8px; background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
.btn-refresh:hover:not(:disabled) { background: #F0F4F8; color: var(--primary); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-refresh svg { width: 16px; height: 16px; }
.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.state-box { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 48px 24px; color: var(--text-secondary); font-size: 14px; }
.state-box svg { width: 36px; height: 36px; flex-shrink: 0; opacity: 0.4; }
.state-error { color: var(--error); }
.state-error svg { opacity: 1; }
.state-title { font-weight: 600; margin: 0 0 4px; font-size: 15px; }
.state-msg { margin: 0; font-size: 13px; opacity: 0.8; }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
.table-wrapper { overflow-x: auto; }
.members-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.members-table th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; background: #F8FAFC; border-bottom: 1px solid var(--border); white-space: nowrap; }
.members-table td { padding: 12px 16px; border-bottom: 1px solid #F1F5F9; color: var(--text-primary); vertical-align: middle; }
.members-table tbody tr:hover td { background: #F8FAFC; }
.members-table tbody tr:last-child td { border-bottom: none; }
.total-count { padding: 10px 16px; font-size: 12px; color: var(--text-secondary); text-align: right; margin: 0; border-top: 1px solid var(--border); }
.cell-member { display: flex; flex-direction: column; gap: 2px; }
.cell-name { font-weight: 600; color: var(--text-primary); font-size: 13px; }
.cell-sub { font-size: 11px; color: var(--text-secondary); font-family: monospace; }
.cell-email { font-family: inherit; }
.cell-date { font-size: 12px; white-space: nowrap; color: var(--text-secondary); }
.cell-action { white-space: nowrap; display: flex; align-items: center; gap: 8px; }
.badge-active { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #dcfce7; color: #15803d; }
.badge-inactive { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; background: #f1f5f9; color: #64748b; }
.role-badge { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.role-admin { background: #dbeafe; color: #1d4ed8; }
.role-company_admin { background: #dbeafe; color: #1d4ed8; }
.role-hr_manager { background: #ede9fe; color: #6d28d9; }
.role-employee { background: #f1f5f9; color: #475569; }
.btn-edit { padding: 6px 12px; font-size: 13px; font-weight: 600; line-height: 1.2; min-width: 52px; border: 1px solid var(--primary); border-radius: 6px; background: transparent; color: var(--primary); cursor: pointer; transition: all 0.15s; }
.btn-edit:hover { background: var(--primary); color: #fff; }
.btn-pwd { padding: 6px 12px; font-size: 13px; font-weight: 600; line-height: 1.2; min-width: 52px; border: 1px solid #f97316; border-radius: 6px; background: transparent; color: #f97316; cursor: pointer; transition: all 0.15s; }
.btn-pwd:hover { background: #f97316; color: #fff; }
.btn-toggle { display: inline-flex; align-items: center; justify-content: center; min-width: 52px; padding: 6px 12px; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; line-height: 1.2; cursor: pointer; transition: opacity 0.15s, transform 0.1s; }
.btn-toggle:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-toggle:active:not(:disabled) { transform: scale(0.96); }
.btn-deactivate { background: #fef2f2; color: #dc2626; }
.btn-deactivate:hover:not(:disabled) { background: #fee2e2; }
.btn-activate { background: #f0fdf4; color: #16a34a; }
.btn-activate:hover:not(:disabled) { background: #dcfce7; }
.btn-spinner-sm { display: inline-block; width: 12px; height: 12px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; }
.toggle-error-bar { display: flex; align-items: center; gap: 10px; padding: 10px 16px; background: #fef2f2; border-bottom: 1px solid #fecaca; color: #dc2626; font-size: 13px; }
.toggle-error-bar svg { width: 16px; height: 16px; flex-shrink: 0; }
.toggle-error-bar span { flex: 1; }
.toggle-error-close { background: none; border: none; color: #dc2626; cursor: pointer; font-size: 14px; padding: 0 4px; }
.filter-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 14px 24px; border-bottom: 1px solid var(--border); background: #FAFBFC; }
.filter-search { position: relative; flex: 1; min-width: 200px; }
.filter-search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 15px; height: 15px; color: var(--text-secondary); pointer-events: none; }
.filter-input { width: 100%; padding: 7px 10px 7px 32px; border: 1px solid #D1D5DB; border-radius: 8px; font-size: 13px; color: var(--text-primary); background: #fff; outline: none; transition: border-color 0.2s, box-shadow 0.2s; box-sizing: border-box; }
.filter-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.filter-select { padding: 7px 10px; border: 1px solid #D1D5DB; border-radius: 8px; font-size: 13px; color: var(--text-primary); background: #fff; outline: none; cursor: pointer; transition: border-color 0.2s; }
.filter-select:focus { border-color: var(--primary); }
.filter-clear { padding: 6px 12px; border: 1px solid #fecaca; border-radius: 8px; background: #fef2f2; color: #dc2626; font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: background 0.15s; }
.filter-clear:hover { background: #fee2e2; }
.link-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 13px; padding: 0; text-decoration: underline; }
</style>
