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

      <!-- WP-TECHDEBT-VUE-02: Add Member Panel (extracted to MemberCreatePanel.vue) -->
      <MemberCreatePanel
        v-if="selectedCompanyId"
        :companyId="selectedCompanyId"
        @created="onMemberCreated"
      />

      <!-- Members Panel (extracted to MemberListPanel.vue) -->
      <MemberListPanel
        v-if="selectedCompanyId"
        :members="members"
        :loading="membersLoading"
        :error="membersError"
        :companyId="selectedCompanyId"
        :togglingId="togglingId"
        :toggleError="toggleError"
        @edit="openEdit"
        @password="openPwd"
        @toggle="handleToggle"
        @reload="loadMembers"
        @update:toggleError="toggleError = $event"
      />

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
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { adminApi } from '@/api/admin'
import MemberEditModal from '@/components/admin/MemberEditModal.vue'
import MemberCreatePanel from '@/components/admin/MemberCreatePanel.vue'
import MemberPasswordModal from '@/components/admin/MemberPasswordModal.vue'
import MemberListPanel from '@/components/admin/MemberListPanel.vue'

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
  toggleError.value = null
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

// ── WP-TECHDEBT-VUE-02: Add Member (extracted to MemberCreatePanel.vue) ──
async function onMemberCreated() {
  await loadMembers()
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


/* WP-TECHDEBT-VUE-02: add-member CSS migrated to MemberCreatePanel.vue */



</style>