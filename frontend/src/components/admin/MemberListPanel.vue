<template>
  <section class="panel">
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
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        成員列表
      </h2>
      <button
        class="btn-refresh"
        :disabled="loading"
        title="重新整理成員列表"
        @click="$emit('reload')"
      >
        <svg
          :class="{ spinning: loading }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      </button>
    </div>

    <div
      v-if="loading"
      class="state-box"
    >
      <div class="spinner" /><span>載入成員中…</span>
    </div>
    <div
      v-else-if="error"
      class="state-box state-error"
    >
      <div>
        <p class="state-title">
          載入失敗
        </p><p class="state-msg">
          {{ error }}
        </p>
      </div>
    </div>
    <div
      v-else-if="members.length === 0"
      class="state-box"
    >
      <div>
        <p class="state-title">
          尚無成員
        </p><p class="state-msg">
          請先使用上方表單新增成員。
        </p>
      </div>
    </div>
    <div
      v-else
      class="table-wrap"
    >
      <div
        v-if="toggleError"
        class="inline-error"
      >
        {{ toggleError }}
      </div>
      <table class="members-table">
        <thead>
          <tr>
            <th>登入帳號</th>
            <th>顯示名稱</th>
            <th>角色</th>
            <th>班表</th>
            <th>狀態</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in members"
            :key="member.membership_id"
          >
            <td class="mono">
              {{ member.login_username }}
            </td>
            <td class="name">
              {{ member.display_name || '—' }}
            </td>
            <td>{{ member.role_id }}</td>
            <td>{{ member.uses_schedule ? '顯示' : '隱藏' }}</td>
            <td>
              <span :class="member.membership_is_active ? 'badge-active' : 'badge-inactive'">
                {{ member.membership_is_active ? '啟用' : '停用' }}
              </span>
            </td>
            <td>
              <div class="action-row">
                <button
                  class="btn-secondary"
                  @click="$emit('edit', member)"
                >
                  編輯
                </button>
                <button
                  class="btn-secondary"
                  @click="$emit('password', member)"
                >
                  重設密碼
                </button>
                <button
                  class="btn-toggle"
                  :disabled="togglingId === member.membership_id"
                  @click="$emit('toggle', member, !member.membership_is_active)"
                >
                  {{ member.membership_is_active ? '停用' : '啟用' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
defineEmits(['edit', 'password', 'toggle', 'reload', 'update:toggleError'])

defineProps({
  members: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  companyId: { type: String, default: '' },
  togglingId: { type: [String, Number, null], default: null },
  toggleError: { type: String, default: '' },
})
</script>

<style scoped>
.panel { background: #fff; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; margin-bottom: 24px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid #E5E7EB; }
.panel-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: #1C3B6B; margin: 0; }
.panel-title svg { width: 18px; height: 18px; color: #4A6FA5; }
.btn-refresh { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid #E5E7EB; border-radius: 8px; background: transparent; color: #5A6C7D; cursor: pointer; }
.btn-refresh svg { width: 16px; height: 16px; }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }
.spinning { animation: spin 0.8s linear infinite; }
.state-box { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 48px 24px; color: #5A6C7D; font-size: 14px; }
.state-error { color: #dc2626; }
.state-title { font-weight: 600; margin: 0 0 4px; font-size: 15px; }
.state-msg { margin: 0; font-size: 13px; opacity: 0.85; }
.spinner { width: 24px; height: 24px; border: 3px solid #E5E7EB; border-top-color: #4A6FA5; border-radius: 50%; animation: spin 0.8s linear infinite; }
.table-wrap { padding: 0 24px 24px; overflow-x: auto; }
.inline-error { margin: 16px 0; padding: 10px 12px; border-radius: 10px; background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; font-size: 13px; }
.members-table { width: 100%; min-width: 900px; border-collapse: collapse; }
.members-table th { text-align: left; padding: 14px 12px; font-size: 12px; color: #5A6C7D; border-bottom: 1px solid #E5E7EB; }
.members-table td { padding: 16px 12px; font-size: 14px; color: #2D3A52; border-bottom: 1px solid #F1F5F9; vertical-align: middle; }
.mono { font-family: monospace; }
.name { font-size: 15px; font-weight: 600; color: #0f172a; }
.badge-active, .badge-inactive { display: inline-flex; align-items: center; justify-content: center; min-width: 72px; min-height: 32px; padding: 0 12px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.badge-active { background: #dcfce7; color: #15803d; }
.badge-inactive { background: #fee2e2; color: #b91c1c; }
.action-row { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-secondary, .btn-toggle { min-height: 34px; padding: 0 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-secondary { border: 1px solid #CBD5E1; background: #fff; color: #334155; }
.btn-toggle { border: 1px solid #BFDBFE; background: #DBEAFE; color: #1D4ED8; }
.btn-toggle:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
