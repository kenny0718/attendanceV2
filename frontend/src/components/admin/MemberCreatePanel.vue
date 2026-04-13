<template>
  <section class="panel panel-create">
    <div class="panel-header">
      <h2 class="panel-title">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
          />
        </svg>
        新增成員
      </h2>
    </div>

    <div class="panel-body">
      <div
        v-if="success"
        class="alert alert-success"
      >
        {{ success }}
      </div>
      <div
        v-if="error"
        class="alert alert-error"
      >
        {{ error }}
      </div>

      <form
        class="create-form"
        @submit.prevent="submitCreate"
      >
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">顯示名稱</label>
            <input
              v-model.trim="form.display_name"
              class="form-input"
              type="text"
              maxlength="100"
            >
          </div>
          <div class="form-group">
            <label class="form-label">登入帳號</label>
            <input
              v-model.trim="form.login_username"
              class="form-input"
              type="text"
              maxlength="100"
              autocomplete="off"
            >
          </div>
          <div class="form-group">
            <label class="form-label">初始密碼</label>
            <input
              v-model="form.password"
              class="form-input"
              type="password"
              maxlength="255"
              autocomplete="new-password"
            >
          </div>
          <div class="form-group">
            <label class="form-label">電子郵件（選填）</label>
            <input
              v-model.trim="form.email"
              class="form-input"
              type="email"
              maxlength="255"
            >
          </div>
          <div class="form-group">
            <label class="form-label">角色</label>
            <select
              v-model="form.role_id"
              class="form-input"
            >
              <option value="employee">
                員工
              </option>
              <option value="hr_manager">
                HR 管理員
              </option>
              <option value="company_admin">
                公司管理員
              </option>
            </select>
          </div>
          <div class="form-group form-group-checkbox">
            <label class="form-label">我的班表顯示</label>
            <label class="checkbox-row">
              <input
                v-model="form.uses_schedule"
                type="checkbox"
              >
              <span>此成員顯示「我的班表」</span>
            </label>
          </div>
        </div>

        <div class="actions-row">
          <button
            class="btn-submit"
            type="submit"
            :disabled="loading"
          >
            <span
              v-if="loading"
              class="btn-spinner-sm"
            />
            <span v-else>新增成員</span>
          </button>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { adminApi } from '@/api/admin'

const props = defineProps({
  companyId: { type: String, required: true },
})

const emit = defineEmits(['created'])

const loading = ref(false)
const error = ref(null)
const success = ref('')
const form = reactive({
  display_name: '',
  login_username: '',
  password: '',
  email: '',
  role_id: 'employee',
  uses_schedule: false,
})

function resetForm() {
  form.display_name = ''
  form.login_username = ''
  form.password = ''
  form.email = ''
  form.role_id = 'employee'
  form.uses_schedule = false
}

async function submitCreate() {
  error.value = null
  success.value = ''
  if (!form.display_name || !form.login_username || !form.password) {
    error.value = '顯示名稱、登入帳號、初始密碼為必填'
    return
  }
  loading.value = true
  try {
    const created = await adminApi.createCompanyMember(props.companyId, {
      display_name: form.display_name,
      login_username: form.login_username,
      password: form.password,
      email: form.email || undefined,
      role_id: form.role_id,
      uses_schedule: form.uses_schedule,
    })
    success.value = `成員「${created.display_name}」已新增`
    resetForm()
    emit('created', created)
  } catch (err) {
    const code = err?.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      error.value = `登入帳號「${form.login_username}」已存在於此公司`
    } else if (code === 'INVALID_ROLE') {
      error.value = '角色無效'
    } else {
      error.value = err.message || '新增失敗，請稍後再試'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.panel { background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; margin-bottom: 24px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #E5E7EB; }
.panel-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: #1C3B6B; margin: 0; }
.panel-title svg { width: 18px; height: 18px; color: #4A6FA5; }
.panel-body { padding: 20px 24px 24px; }
.alert { padding: 12px 14px; border-radius: 10px; font-size: 13px; margin-bottom: 14px; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.create-form { display: grid; gap: 16px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-group { display: grid; gap: 6px; }
.form-group-checkbox { align-content: start; }
.form-label { font-size: 12px; font-weight: 600; color: #5A6C7D; }
.form-input { padding: 10px 12px; border: 1px solid #D1D5DB; border-radius: 8px; font-size: 14px; color: #2D3A52; background: #fff; outline: none; }
.form-input:focus { border-color: #4A6FA5; box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.checkbox-row { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #2D3A52; }
.actions-row { display: flex; justify-content: flex-end; }
.btn-submit { min-width: 132px; min-height: 40px; padding: 0 16px; border: none; border-radius: 10px; background: #4A6FA5; color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner-sm { display: inline-block; width: 12px; height: 12px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 820px) { .form-grid { grid-template-columns: 1fr; } .actions-row { justify-content: stretch; } .btn-submit { width: 100%; } }
</style>
