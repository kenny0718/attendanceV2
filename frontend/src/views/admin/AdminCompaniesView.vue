<template>
  <div class="stack-layout">
    <CompanyListPanel
      v-if="showCompanyList"
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
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { adminApi } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import CompanyListPanel from '@/components/admin/CompanyListPanel.vue'
import CompanyDetailPanel from '@/components/admin/CompanyDetailPanel.vue'

const authStore = useAuthStore()
const isTenantScopedAdmin = computed(() => ['company_admin', 'hr_manager'].includes(authStore.userRole))
const tenantCompanyId = computed(() => authStore.companyId || '')
const showCompanyList = computed(() => !isTenantScopedAdmin.value)

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
    const company = data?.company ?? data
    if (!company?.id) {
      throw new Error('公司詳情資料格式不正確')
    }
    selectedCompany.value = company
    selectedCompanySummary.value = data?.member_summary ?? null
    updateEditForm(company)
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
  loadCompanyDetail(company.id)
}

onMounted(async () => {
  if (isTenantScopedAdmin.value) {
    await loadCompanyDetail(tenantCompanyId.value)
    return
  }

  await loadCompanies()
})

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
    if (!isTenantScopedAdmin.value) {
      await loadCompanies()
    }
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
    await adminApi.updateCompany(selectedCompany.value.id, { is_active: target })
    await loadCompanyDetail(selectedCompany.value.id)
    detailSuccess.value = `公司已${label}`
    if (!isTenantScopedAdmin.value) {
      await loadCompanies()
    }
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
</script>

<style scoped>
.stack-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
}
</style>
