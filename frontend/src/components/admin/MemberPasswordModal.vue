<template>
  <div
    v-if="open"
    class="modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">
          重設密碼
        </h3>
        <button
          class="modal-close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>
      <div class="modal-body">
        <p class="pwd-member-name">
          為「{{ member?.display_name }}」重設登入密碼
        </p>
        <div class="form-group">
          <label class="form-label">新密碼</label>
          <input
            v-model="newPassword"
            class="form-input"
            type="password"
            maxlength="255"
            placeholder="至少6個字元"
          >
        </div>
        <div class="form-group">
          <label class="form-label">確認新密碼</label>
          <input
            v-model="confirmPassword"
            class="form-input"
            type="password"
            maxlength="255"
            placeholder="再輸入一次"
          >
        </div>
        <div
          v-if="error"
          class="modal-error"
        >
          {{ error }}
        </div>
        <div
          v-if="success"
          class="modal-success"
        >
          密碼已成功重設
        </div>
      </div>
      <div class="modal-footer">
        <button
          class="btn-cancel"
          :disabled="loading"
          @click="$emit('close')"
        >
          取消
        </button>
        <button
          class="btn-save"
          :disabled="loading"
          @click="savePwd"
        >
          <span
            v-if="loading"
            class="btn-spinner-sm"
          />
          <span v-else>確認重設</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * MemberPasswordModal.vue — S1-13A3 Admin Reset Member Password (WP-TECHDEBT-VUE-01)
 *
 * Props:
 *   open       Boolean  — controls visibility
 *   member     Object   — { membership_id, display_name }
 *   companyId  String   — current company scope
 *
 * Emits:
 *   close      — parent should set open=false
 */
import { ref, watch } from 'vue'
import { adminApi } from '@/api/admin'

const props = defineProps({
  open: { type: Boolean, required: true },
  member: { type: Object, default: null },
  companyId: { type: String, required: true },
})

const emit = defineEmits(['close'])

const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(false)

// Reset local state whenever the modal is opened
watch(() => props.open, (val) => {
  if (val) {
    newPassword.value = ''
    confirmPassword.value = ''
    loading.value = false
    error.value = null
    success.value = false
  }
})

async function savePwd() {
  const pwd = newPassword.value
  const confirm = confirmPassword.value
  // Client-side validation
  if (!pwd || pwd.length < 6) {
    error.value = '密碼至少6個字元'
    return
  }
  if (pwd !== confirm) {
    error.value = '兩次密碼輸入不一致'
    return
  }
  loading.value = true
  error.value = null
  success.value = false
  try {
    await adminApi.resetMemberPassword(
      props.companyId,
      props.member.membership_id,
      pwd
    )
    success.value = true
    setTimeout(() => { emit('close') }, 1000)
  } catch (err) {
    const code = err?.data?.detail?.code
    if (code === 'PASSWORD_TOO_SHORT') {
      error.value = '密碼至少6個字元'
    } else {
      error.value = err.message || '重設失敗，請稍後再試'
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
/* Password modal specific */
.pwd-member-name { font-size: 14px; font-weight: 600; color: #1C3B6B; margin: 0 0 4px; }
</style>
