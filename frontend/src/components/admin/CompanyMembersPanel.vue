<template>
  <section
    v-if="company"
    class="members-section"
  >
    <AdminSectionHeader
      :title="`成員管理 — ${company.name}`"
      align="between"
      icon-path="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
    >
      <template #actions>
        <button
          class="btn-refresh"
          :disabled="loading"
          title="重新整理"
          @click="$emit('reload')"
        >
          <svg
            :class="{ spinning: loading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            stroke-width="2"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          /></svg>
        </button>
      </template>
    </AdminSectionHeader>

    <div
      v-if="loading"
      class="state-loading"
    >
      <div class="spinner" /><span>載入中…</span>
    </div>
    <AdminStateBox
      v-else-if="error"
      variant="error"
      :message="error"
      icon-path="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
    <AdminStateBox
      v-else-if="members.length === 0"
      variant="empty"
      message="目前尚無成員，可直接使用下方表單建立第一位成員。"
      icon-path="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
    />
    <div
      v-else
      class="members-table-wrapper"
    >
      <table class="members-table">
        <thead>
          <tr>
            <th>登入帳號</th>
            <th>顯示名稱</th>
            <th>角色</th>
            <th>加入時間</th>
            <th>狀態</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in members"
            :key="member.membership_id"
          >
            <td class="member-login">
              {{ member.login_username }}
            </td>
            <td class="member-name">
              {{ member.display_name || '—' }}
            </td>
            <td><span class="role-badge">{{ formatRole(member.role_id) }}</span></td>
            <td class="member-date">
              {{ formatDate(member.membership_created_at) }}
            </td>
            <td>
              <button
                class="btn-status-toggle"
                :class="member.membership_is_active ? 'is-active' : 'is-inactive'"
                :disabled="actionLoadingId === member.membership_id"
                @click="$emit('toggle-member', member)"
              >
                {{ member.membership_is_active ? '啟用中｜點擊停用' : '停用中｜點擊啟用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="total-count">
        共 {{ members.length }} 位成員
      </p>
    </div>

    <section class="add-member-section">
      <div class="section-header">
        <h2 class="section-title">
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

      <div
        v-if="addSuccess"
        class="alert alert-success"
      >
        {{ addSuccess }}
      </div>
      <div
        v-if="addError"
        class="alert alert-error"
      >
        {{ addError }}
      </div>

      <form
        class="create-form"
        novalidate
        @submit.prevent="$emit('submit-add-member')"
      >
        <div class="form-grid">
          <div class="form-group">
            <label
              class="form-label"
              for="am-dispname"
            >顯示名稱</label>
            <input
              id="am-dispname"
              :value="form.display_name"
              type="text"
              class="form-input"
              maxlength="100"
              @input="$emit('update:form', { ...form, display_name: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="am-username"
            >登入帳號</label>
            <input
              id="am-username"
              :value="form.login_username"
              type="text"
              class="form-input"
              maxlength="100"
              autocomplete="off"
              @input="$emit('update:form', { ...form, login_username: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="am-password"
            >初始密碼</label>
            <input
              id="am-password"
              :value="form.password"
              type="password"
              class="form-input"
              maxlength="255"
              autocomplete="new-password"
              @input="$emit('update:form', { ...form, password: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="am-email"
            >電子郵件（選填）</label>
            <input
              id="am-email"
              :value="form.email"
              type="email"
              class="form-input"
              maxlength="255"
              @input="$emit('update:form', { ...form, email: $event.target.value })"
            >
          </div>
          <div class="form-group">
            <label
              class="form-label"
              for="am-role"
            >角色</label>
            <select
              id="am-role"
              :value="form.role_id"
              class="form-input"
              @change="$emit('update:form', { ...form, role_id: $event.target.value })"
            >
              <option value="employee">
                員工
              </option>
              <option value="company_admin">
                公司管理員
              </option>
            </select>
          </div>
        </div>

        <div class="actions-row">
          <button
            type="submit"
            class="btn-submit"
            :disabled="addLoading"
          >
            <span
              v-if="addLoading"
              class="btn-spinner-sm"
            />
            <span v-else>新增成員</span>
          </button>
        </div>
      </form>
    </section>
  </section>
</template>

<script setup>
import AdminSectionHeader from '@/components/admin/AdminSectionHeader.vue'
import AdminStateBox from '@/components/admin/AdminStateBox.vue'

defineEmits(['reload', 'toggle-member', 'submit-add-member', 'update:form'])

defineProps({
  company: { type: Object, default: null },
  members: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  actionLoadingId: { type: [String, Number, null], default: null },
  addLoading: { type: Boolean, default: false },
  addSuccess: { type: String, default: '' },
  addError: { type: String, default: '' },
  form: { type: Object, required: true },
  formatDate: { type: Function, required: true },
})

function formatRole(roleId) {
  if (roleId === 'company_admin') return '公司管理員'
  if (roleId === 'employee') return '員工'
  return roleId || '—'
}
</script>

<style scoped>
.members-section {
  display: grid;
  gap: 18px;
}
.state-loading {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}
.spinner {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 3px solid rgba(148, 163, 184, 0.28);
  border-top-color: #0ea5e9;
  animation: spin 0.7s linear infinite;
}
.btn-refresh {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #64748b;
  cursor: pointer;
}
.btn-refresh svg { width: 18px; height: 18px; }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.spinning { animation: spin 0.8s linear infinite; }
.members-table-wrapper { overflow-x: auto; }
.members-table {
  width: 100%;
  min-width: 700px;
  border-collapse: separate;
  border-spacing: 0;
}
.members-table th {
  padding: 16px 18px;
  text-align: left;
  font-size: 14px;
  line-height: 1.4;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: #475569;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(248, 250, 252, 0.92);
  white-space: nowrap;
}
.members-table td {
  padding: 18px;
  font-size: 14px;
  line-height: 1.5;
  font-weight: 500;
  color: #0f172a;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  vertical-align: middle;
}
.members-table tbody tr:last-child td { border-bottom: none; }
.members-table tbody tr:hover { background: rgba(248, 250, 252, 0.92); }
.member-login { font-family: monospace; font-size: 14px; font-weight: 600; color: #0f172a; }
.member-name { font-size: 15px; font-weight: 700; color: #0f172a; }
.member-date { font-size: 14px; font-weight: 500; color: #334155; white-space: nowrap; }
.total-count { margin: 16px 0 0; font-size: 14px; line-height: 1.5; color: #64748b; text-align: right; }
.role-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 14px;
  line-height: 1;
  font-weight: 700;
  white-space: nowrap;
  background: #dbeafe;
  color: #1d4ed8;
}
.btn-status-toggle {
  min-width: 148px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid transparent;
  font-size: 13px;
  line-height: 1;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-status-toggle.is-active {
  background: #e0f2fe;
  border-color: #bae6fd;
  color: #0369a1;
}
.btn-status-toggle.is-inactive {
  background: #fee2e2;
  border-color: #fecaca;
  color: #b91c1c;
}
.btn-status-toggle:disabled { opacity: 0.45; cursor: not-allowed; }
.add-member-section {
  display: grid;
  gap: 16px;
  margin-top: 8px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1C3B6B;
  margin: 0;
}
.section-title svg { width: 18px; height: 18px; color: #4A6FA5; }
.alert { padding: 12px 14px; border-radius: 10px; font-size: 13px; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.create-form { display: grid; gap: 16px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-group { display: grid; gap: 6px; }
.form-label { font-size: 12px; font-weight: 600; color: #5A6C7D; }
.form-input {
  padding: 10px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  font-size: 14px;
  color: #2D3A52;
  background: #fff;
  outline: none;
}
.form-input:focus { border-color: #4A6FA5; box-shadow: 0 0 0 3px rgba(74,111,165,0.12); }
.actions-row { display: flex; justify-content: flex-end; }
.btn-submit {
  min-width: 132px;
  min-height: 40px;
  padding: 0 16px;
  border: none;
  border-radius: 10px;
  background: #4A6FA5;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner-sm {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) { .form-grid { grid-template-columns: 1fr; } }
@media (max-width: 720px) {
  .btn-submit { width: 100%; }
  .members-table { min-width: 640px; }
  .actions-row { justify-content: stretch; }
}
</style>
