<template>
  <!-- WP-TECHDEBT-VUE-02: MemberCreatePanel (extracted from AdminUsersView) -->
  <div class="panel add-member-panel">
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
          <div class="form-group">
            <label class="form-label">我的班表顯示</label>
            <label class="checkbox-row">
              <input v-model="newMember.uses_schedule" type="checkbox" />
              <span>此成員顯示「我的班表」</span>
            </label>
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
</template>

<script setup>
/**
 * MemberCreatePanel.vue — WP-S1-10D New Member Form (WP-TECHDEBT-VUE-02)
 *
 * Props:
 *   companyId  String  (required) — company scope for API call
 *
 * Emits:
 *   created(memberName)  — parent should clearFilters() + loadMembers()
 */
import { ref } from 'vue'
import { adminApi } from '@/api/admin'

const props = defineProps({
  companyId: { type: String, required: true },
})

const emit = defineEmits(['created'])

const newMember = ref({ display_name: '', email: '', login_username: '', password: '', role_id: 'employee', uses_schedule: false })
const addMemberLoading = ref(false)
const addMemberError = ref(null)
const addMemberSuccess = ref(false)
const addMemberSuccessName = ref('')

async function handleAddMember() {
  addMemberLoading.value = true
  addMemberError.value = null
  addMemberSuccess.value = false
  try {
    await adminApi.createCompanyMember(props.companyId, {
      display_name: newMember.value.display_name,
      email: newMember.value.email || null,
      login_username: newMember.value.login_username,
      password: newMember.value.password,
      role_id: newMember.value.role_id,
      uses_schedule: newMember.value.uses_schedule,
    })
    addMemberSuccessName.value = newMember.value.display_name
    addMemberSuccess.value = true
    newMember.value = { display_name: '', email: '', login_username: '', password: '', role_id: 'employee', uses_schedule: false }
    // Notify parent to reset filters and reload members list
    emit('created', addMemberSuccessName.value)
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
</script>

<style scoped>
/* Panel wrapper styles */
.panel {
  background: #fff; border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; margin-bottom: 24px;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 16px; border-bottom: 1px solid #E5E7EB;
}
.panel-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 600; color: #1C3B6B; margin: 0;
}
.panel-title svg { width: 18px; height: 18px; color: #4A6FA5; }

/* Add member body */
.add-member-body { padding: 20px 24px; }
.add-member-form { display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.form-group { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.form-group-action { flex: 0 0 auto; justify-content: flex-end; }
.form-label { font-size: 12px; font-weight: 600; color: #5A6C7D; }
.required { color: #dc2626; }
.form-input {
  padding: 9px 12px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 14px; color: #2D3A52; background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus { border-color: #4A6FA5; box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.btn-add-member {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 9px 20px; background: #4A6FA5; color: #fff;
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
.btn-spinner-sm {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid currentColor; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
