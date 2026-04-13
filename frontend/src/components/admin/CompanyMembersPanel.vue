<template>
  <PageCard v-if="company">
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
      message="目前尚無成員，可展開下方「新增公司成員」表單建立第一位成員。"
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

    <div class="add-member-section">
      <button
        type="button"
        class="add-member-header"
        @click="$emit('toggle-add-form')"
      >
        <div class="add-member-title-wrap">
          <div class="add-member-title">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              stroke-width="2"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
            /></svg>
            <span>新增公司成員</span>
          </div>
          <p class="add-member-subtitle">
            建立登入帳號、設定顯示名稱與角色。
          </p>
        </div>
        <svg
          class="chevron"
          :class="{ open: showAddMember }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="2"
        ><path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M19 9l-7 7-7-7"
        /></svg>
      </button>

      <div
        v-if="showAddMember"
        class="add-member-body"
      >
        <div
          v-if="addSuccess"
          class="alert alert-success"
        >
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            stroke-width="2"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          /></svg>
          <span>{{ addSuccess }}</span>
        </div>
        <div
          v-if="addError"
          class="alert alert-error"
        >
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            stroke-width="2"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          /></svg>
          <span>{{ addError }}</span>
        </div>

        <form
          class="add-member-form"
          novalidate
          @submit.prevent="$emit('submit-add-member')"
        >
          <div class="am-grid">
            <div class="form-group">
              <label
                class="form-label"
                for="am-dispname"
              >顯示名稱 <span class="label-hint">必填</span></label>
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
              >登入帳號 <span class="label-hint">必填</span></label>
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
              >初始密碼 <span class="label-hint">最少 6 字</span></label>
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
              >電子郵件 <span class="label-hint">選填</span></label>
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
          <button
            type="submit"
            class="btn-submit"
            :disabled="addLoading"
          >
            <span
              v-if="addLoading"
              class="btn-spinner"
            />
            <svg
              v-else
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              stroke-width="2"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 4v16m8-8H4"
            /></svg>
            {{ addLoading ? '新增中…' : '新增成員' }}
          </button>
        </form>
      </div>
    </div>
  </PageCard>
</template>

<script setup>
import PageCard from '@/components/PageCard.vue'
import AdminSectionHeader from '@/components/admin/AdminSectionHeader.vue'
import AdminStateBox from '@/components/admin/AdminStateBox.vue'

defineEmits(['reload', 'toggle-member', 'toggle-add-form', 'submit-add-member', 'update:form'])

defineProps({
  company: { type: Object, default: null },
  members: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  actionLoadingId: { type: [String, Number, null], default: null },
  showAddMember: { type: Boolean, default: false },
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
.add-member-section { margin-top: 18px; padding-top: 18px; border-top: 1px solid rgba(226, 232, 240, 0.9); }
.add-member-header {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}
.add-member-title-wrap { display: grid; gap: 4px; text-align: left; }
.add-member-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
  font-size: 18px;
  line-height: 1.35;
  font-weight: 800;
}
.add-member-subtitle { margin: 0; font-size: 14px; line-height: 1.5; color: #64748b; }
.add-member-title svg, .chevron { width: 18px; height: 18px; color: #0ea5e9; }
.chevron { transition: transform 0.2s ease; margin-top: 2px; }
.chevron.open { transform: rotate(180deg); }
.add-member-body { margin-top: 14px; display: grid; gap: 12px; }
.alert { display: flex; align-items: flex-start; gap: 10px; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; }
.alert svg { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.alert-error { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.add-member-form { display: grid; gap: 14px; }
.am-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-group { display: grid; gap: 6px; }
.form-label { font-size: 14px; font-weight: 700; color: #334155; }
.label-hint { color: #64748b; font-weight: 500; }
.form-input { min-height: 46px; padding: 0 14px; border: 1px solid rgba(148, 163, 184, 0.32); border-radius: 16px; font-size: 15px; color: #0f172a; background: rgba(255, 255, 255, 0.92); outline: none; }
.form-input:focus { border-color: #93c5fd; box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.25); }
.btn-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 148px;
  min-height: 46px;
  padding: 0 20px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  background: #0ea5e9;
  color: #ffffff;
}
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-spinner { width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) { .am-grid { grid-template-columns: 1fr; } }
@media (max-width: 720px) {
  .btn-submit { width: 100%; }
  .members-table { min-width: 640px; }
  .add-member-header { align-items: stretch; }
}
</style>
