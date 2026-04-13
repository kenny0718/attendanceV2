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
      :member-summary="selectedCompanySummary"
      :form="editForm"
      :loading="detailLoading"
      :error="detailError || ''"
      :success="detailSuccess || ''"
      :format-date="formatDate"
      @submit="handleUpdate"
      @toggle-active="handleToggleActive"
      @update:form="updateEditForm"
      @upload-logo="handleUploadLogo"
      @remove-logo="handleRemoveLogo"
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
const selectedCompanySummary = ref(null)
const editForm = reactive({
  name: '',
  tax_id: '',
  display_name: '',
  owner_name: '',
  registered_address: '',
  contact_address: '',
  contact_phone: '',
  contact_email: '',
  timezone: 'UTC',
})
const detailLoading = ref(false)
const detailError = ref(null)
const detailSuccess = ref(null)

function updateEditForm(next) {
  editForm.name = next.name ?? ''
  editForm.tax_id = next.tax_id ?? ''
  editForm.display_name = next.display_name ?? ''
  editForm.owner_name = next.owner_name ?? ''
  editForm.registered_address = next.registered_address ?? ''
  editForm.contact_address = next.contact_address ?? ''
  editForm.contact_phone = next.contact_phone ?? ''
  editForm.contact_email = next.contact_email ?? ''
  editForm.timezone = next.timezone ?? 'UTC'
}

async function loadCompanyDetail(companyId) {
  detailLoading.value = true
  detailError.value = null
  try {
    const data = await adminApi.getCompany(companyId)
    selectedCompany.value = data.company
    selectedCompanySummary.value = data.member_summary || null
    updateEditForm(data.company)
  } catch (err) {
    detailError.value = err.message || '無法載入公司詳情，請稍後再試'
  } finally {
    detailLoading.value = false
  }
}

function selectCompany(company) {
  selectedCompany.value = company
  selectedCompanySummary.value = null
  updateEditForm(company)
  detailError.value = null
  detailSuccess.value = null
  members.value = []
  showAddMember.value = false
  addMemberSuccess.value = null
  addMemberError.value = null
  loadCompanyDetail(company.id)
  loadMembers()
}

async function handleUpdate() {
  if (!selectedCompany.value) return
  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    await adminApi.updateCompany(selectedCompany.value.id, {
      name: editForm.name,
      tax_id: editForm.tax_id || null,
      display_name: editForm.display_name || null,
      owner_name: editForm.owner_name || null,
      registered_address: editForm.registered_address || null,
      contact_address: editForm.contact_address || null,
      contact_phone: editForm.contact_phone || null,
      contact_email: editForm.contact_email || null,
      timezone: editForm.timezone,
    })
    await loadCompanyDetail(selectedCompany.value.id)
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

async function handleUploadLogo(file) {
  if (!selectedCompany.value || !file) return

  const allowedTypes = ['image/png', 'image/jpeg']
  if (!allowedTypes.includes(file.type)) {
    detailError.value = 'Logo 僅支援 PNG / JPG / JPEG'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    detailError.value = 'Logo 檔案大小不可超過 2MB'
    return
  }

  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    const contentBase64 = await fileToBase64(file)
    await adminApi.uploadCompanyLogo(selectedCompany.value.id, {
      filename: file.name,
      content_type: file.type,
      content_base64: contentBase64,
    })
    await loadCompanyDetail(selectedCompany.value.id)
    detailSuccess.value = 'Logo 已上傳'
    await loadCompanies()
  } catch (err) {
    detailError.value = err.data?.detail?.message || err.message || 'Logo 上傳失敗'
  } finally {
    detailLoading.value = false
  }
}

async function handleRemoveLogo() {
  if (!selectedCompany.value) return
  if (!confirm(`確認要移除公司「${selectedCompany.value.name}」的 Logo？`)) return

  detailError.value = null
  detailSuccess.value = null
  detailLoading.value = true
  try {
    await adminApi.deleteCompanyLogo(selectedCompany.value.id)
    await loadCompanyDetail(selectedCompany.value.id)
    detailSuccess.value = 'Logo 已移除'
    await loadCompanies()
  } catch (err) {
    detailError.value = err.data?.detail?.message || err.message || 'Logo 移除失敗'
  } finally {
    detailLoading.value = false
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const base64 = result.includes(',') ? result.split(',')[1] : result
      resolve(base64)
    }
    reader.onerror = () => reject(new Error('檔案讀取失敗'))
    reader.readAsDataURL(file)
  })
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
    await adminApi.updateCompany(selectedCompany.value.id, { is_active: target })
    await loadCompanyDetail(selectedCompany.value.id)
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
    await loadCompanyDetail(selectedCompany.value.id)
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
    await loadCompanyDetail(selectedCompany.value.id)
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
