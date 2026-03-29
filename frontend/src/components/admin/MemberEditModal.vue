<template>
  <div v-if="open" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">編輯成員資料</h3>
        <button class="modal-close" @click="$emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">顯示名稱</label>
          <input v-model="localDisplayName" class="form-input" type="text" maxlength="100" />
        </div>
        <div class="form-group">
          <label class="form-label">Email（選填）</label>
          <input v-model="localEmail" class="form-input" type="email" maxlength="255" placeholder="留空表示不更改" />
        </div>
        <div class="form-group">
          <label class="form-label">角色</label>
          <select v-model="localRoleId" class="form-input">
            <option value="employee">employee</option>
            <option value="hr_manager">hr_manager</option>
            <option value="company_admin">company_admin</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">登入帳號</label>
          <input v-model="localLoginUsername" class="form-input" type="text" maxlength="100" placeholder="不修改請留原帳號" />
          <p class="form-hint">修改後，該成員下次登入需使用新的登入帳號</p>
        </div>
        <div v-if="error" class="modal-error">{{ error }}</div>
        <div v-if="success" class="modal-success">已儲存</div>
      </div>
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')" :disabled="loading">取消</button>
        <button class="btn-save" @click="saveEdit" :disabled="loading || !localDisplayName">
          <span v-if="loading" class="btn-spinner-sm"></span>
          <span v-else>儲存</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * MemberEditModal.vue — S1-13A1/A2 Admin Edit Member (WP-TECHDEBT-VUE-01)
 *
 * Props:
 *   open       Boolean  — controls visibility
 *   member     Object   — { membership_id, display_name, email, role_id, login_username }
 *   companyId  String   — current company scope
 *
 * Emits:
 *   close              — parent should set open=false
 *   saved(updatedMember) — parent does local list update
 */
import { ref, watch } from 'vue'
import { adminApi } from '@/api/admin'

const props = defineProps({
  open: { type: Boolean, required: true },
  member: { type: Object, default: null },
  companyId: { type: String, required: true },
})

const emit = defineEmits(['close', 'saved'])

const localDisplayName = ref('')
const localEmail = ref('')
const localRoleId = ref('employee')
const localLoginUsername = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(false)

// Re-initialise local state whenever the modal is opened with a new member
watch(() => props.open, (val) => {
  if (val && props.member) {
    localDisplayName.value = props.member.display_name || ''
    localEmail.value = props.member.email || ''
    localRoleId.value = props.member.role_id || 'employee'
    localLoginUsername.value = props.member.login_username || ''
    loading.value = false
    error.value = null
    success.value = false
  }
})

async function saveEdit() {
  if (!localDisplayName.value.trim()) return
  loading.value = true
  error.value = null
  success.value = false
  try {
    const payload = {
      display_name: localDisplayName.value.trim(),
      role_id: localRoleId.value,
      email: localEmail.value.trim() || null,
    }
    // S1-13A2: only include login_username if provided
    const newUsername = localLoginUsername.value.trim()
    if (newUsername) payload.login_username = newUsername

    const result = await adminApi.updateMember(
      props.companyId,
      props.member.membership_id,
      payload
    )
    success.value = true
    // Emit saved so parent can do local list update without full reload
    emit('saved', {
      membership_id: props.member.membership_id,
      display_name: result.display_name,
      email: result.email,
      role_id: result.role_id,
      login_username: result.login_username,
    })
    setTimeout(() => { emit('close') }, 800)
  } catch (err) {
    const code = err?.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      error.value = '此帳號名稱在該公司已被使用，請換一個'
    } else {
      error.value = err.message || '儲存失敗，請稍後再試'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Modal shared styles */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 440px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18); overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px 14px; border-bottom: 1px solid #E5E7EB;
}
.modal-title { font-size: 16px; font-weight: 700; color: #1C3B6B; margin: 0; }
.modal-close {
  background: none; border: none; font-size: 16px;
  color: #5A6C7D; cursor: pointer; line-height: 1;
}
.modal-close:hover { color: #dc2626; }
.modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 24px; border-top: 1px solid #E5E7EB;
}
.modal-error { color: #dc2626; font-size: 13px; }
.modal-success { color: #15803d; font-size: 13px; font-weight: 600; }
.btn-cancel {
  padding: 8px 20px; border: 1px solid #E5E7EB; border-radius: 8px;
  background: #fff; color: #5A6C7D; font-size: 14px; cursor: pointer;
}
.btn-cancel:hover:not(:disabled) { background: #F0F4F8; }
.btn-save {
  padding: 8px 20px; border: none; border-radius: 8px;
  background: #4A6FA5; color: #fff; font-size: 14px;
  font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
}
.btn-save:hover:not(:disabled) { opacity: 0.88; }
.btn-save:disabled, .btn-cancel:disabled { opacity: 0.55; cursor: not-allowed; }
/* Form */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 12px; font-weight: 600; color: #5A6C7D; }
.form-input {
  padding: 9px 12px; border: 1px solid #D1D5DB; border-radius: 8px;
  font-size: 14px; color: #2D3A52; background: #fff; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.form-input:focus { border-color: #4A6FA5; box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.btn-spinner-sm {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid currentColor; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
/* Edit modal specific */
.form-hint { font-size: 11px; color: #5A6C7D; margin: 3px 0 0; opacity: 0.85; }
</style>
