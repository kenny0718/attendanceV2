<template>
  <div class="stack-layout">
    <CompanyListPanel
      :companies="companies"
      :loading="listLoading"
      :error="listError || ''"
      :selected-company-id="selectedCompany?.id || ''"
      :format-date="formatDate"
      @reload="loadCompanies"
      @select="selectCompany"
    />

    <CompanyDetailPanel
      :company="selectedCompany"
      :form="editForm"
      :loading="detailLoading"
      :error="detailError || ''"
      :success="detailSuccess || ''"
      :format-date="formatDate"
      @submit="handleUpdate"
      @toggle-active="handleToggleActive"
      @update:form="updateEditForm"
    />

    <CompanyMembersPanel
      v-if="selectedCompany"
      :company="selectedCompany"
      :members="members"
      :loading="membersLoading"
      :error="membersError || ''"
      :action-loading-id="memberActionLoading"
      :show-add-member="showAddMember"
      :add-loading="addMemberLoading"
      :add-success="addMemberSuccess || ''"
      :add-error="addMemberError || ''"
      :form="addForm"
      :format-date="formatDate"
      @reload="loadMembers"
      @toggle-member="handleToggleMembership"
      @toggle-add-form="showAddMember = !showAddMember"
      @submit-add-member="handleAddMember"
      @update:form="updateAddForm"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { adminApi } from '@/api/admin'
import CompanyListPanel from '@/components/admin/CompanyListPanel.vue'
import CompanyDetailPanel from '@/components/admin/CompanyDetailPanel.vue'
import CompanyMembersPanel from '@/components/admin/CompanyMembersPanel.vue'

const companies = ref([])
const listLoading = ref(false)
const listError = ref(null)

async function loadCompanies() {
  listLoading.value = true
  listError.value = null
  try {
    const data = await adminApi.listCompanies()
    companies.value = data.companies || []
  } catch (err) {
    listError.value = err.message || '無法載入公司列表，請稍後再試'
  } finally {
    listLoading.value = false
  }
}

onMounted(loadCompanies)

const selectedCompany = ref(null)
const editForm = reactive({ name: '', tax_id: '', timezone: 'UTC' })
const detailLoading = ref(false)
const detailError = ref(null)
const detailSuccess = ref(null)

function updateEditForm(next) {
  editForm.name = next.name ?? ''
  editForm.tax_id = next.tax_id ?? ''
  editForm.timezone = next.timezone ?? 'UTC'
}

function selectCompany(company) {
  selectedCompany.value = company
  editForm.name = company.name
  editForm.tax_id = company.tax_id || ''
  editForm.timezone = company.timezone
  detailError.value = null
  detailSuccess.value = null
  members.value = []
  showAddMember.value = false
  addMemberSuccess.value = null
  addMemberError.value = null
  loadMembers()
}

async function handleUpdate() {
  if (!selectedCompany.value) return
  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    const updated = await adminApi.updateCompany(selectedCompany.value.id, {
      name: editForm.name,
      tax_id: editForm.tax_id || null,
      timezone: editForm.timezone,
    })
    selectedCompany.value = updated
    detailSuccess.value = '變更已儲存'
    await loadCompanies()
  } catch (err) {
    const code = err.data?.detail?.code
    if (code === 'DUPLICATE_TAX_ID') {
      detailError.value = `統一編號「${editForm.tax_id}」已存在`
    } else {
      detailError.value = err.message || '更新失敗，請稍後再試'
    }
  } finally {
    detailLoading.value = false
  }
}

async function handleToggleActive() {
  if (!selectedCompany.value) return
  const target = !selectedCompany.value.is_active
  const label = target ? '啟用' : '停用'
  if (!confirm(`確認要${label}公司「${selectedCompany.value.name}」？`)) return
  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    const updated = await adminApi.updateCompany(selectedCompany.value.id, { is_active: target })
    selectedCompany.value = updated
    detailSuccess.value = `公司已${label}`
    await loadCompanies()
  } catch (err) {
    detailError.value = err.message || `${label}失敗，請稍後再試`
  } finally {
    detailLoading.value = false
  }
}

function formatDate(val) {
  if (!val) return '—'
  const d = new Date(val)
  return d.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei', hour12: false })
}

const members = ref([])
const membersLoading = ref(false)
const membersError = ref(null)
const memberActionLoading = ref(null)

const showAddMember = ref(false)
const addForm = reactive({ display_name: '', login_username: '', password: '', email: '', role_id: 'employee' })
const addMemberLoading = ref(false)
const addMemberSuccess = ref(null)
const addMemberError = ref(null)

function updateAddForm(next) {
  addForm.display_name = next.display_name ?? ''
  addForm.login_username = next.login_username ?? ''
  addForm.password = next.password ?? ''
  addForm.email = next.email ?? ''
  addForm.role_id = next.role_id ?? 'employee'
}

async function loadMembers() {
  if (!selectedCompany.value) return
  membersLoading.value = true
  membersError.value = null
  try {
    const data = await adminApi.listCompanyMembers(selectedCompany.value.id)
    members.value = data.members || []
  } catch (err) {
    membersError.value = err.message || '無法載入成員列表'
  } finally {
    membersLoading.value = false
  }
}

async function handleToggleMembership(member) {
  const target = !member.membership_is_active
  const label = target ? '啟用' : '停用'
  if (!confirm(`確認要${label}成員「${member.display_name}」的帳號？`)) return
  memberActionLoading.value = member.membership_id
  try {
    await adminApi.toggleMembershipActive(selectedCompany.value.id, member.membership_id, target)
    await loadMembers()
  } catch (err) {
    alert(err.message || `${label}失敗`)
  } finally {
    memberActionLoading.value = null
  }
}

async function handleAddMember() {
  addMemberSuccess.value = null
  addMemberError.value = null
  if (!addForm.display_name || !addForm.login_username || !addForm.password) {
    addMemberError.value = '顯示名稱、登入帳號、初始密碼為必填'
    return
  }
  addMemberLoading.value = true
  try {
    const created = await adminApi.createCompanyMember(selectedCompany.value.id, {
      display_name: addForm.display_name,
      login_username: addForm.login_username,
      password: addForm.password,
      email: addForm.email || undefined,
      role_id: addForm.role_id,
    })
    addMemberSuccess.value = `成員「${created.display_name}」已新增`
    updateAddForm({ display_name: '', login_username: '', password: '', email: '', role_id: 'employee' })
    await loadMembers()
  } catch (err) {
    const code = err.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      addMemberError.value = `登入帳號「${addForm.login_username}」已存在於此公司`
    } else if (code === 'INVALID_ROLE') {
      addMemberError.value = '角色無效'
    } else {
      addMemberError.value = err.message || '新增失敗，請稍後再試'
    }
  } finally {
    addMemberLoading.value = false
  }
}
</script>

<style scoped>
.stack-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
}
</style>
