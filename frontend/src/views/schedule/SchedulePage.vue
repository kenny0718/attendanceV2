<template>
  <div class="page-root">
    <Navbar />

    <div class="page-container">
      <!-- Page Header -->
      <div class="page-header">
        <h1 class="page-title">Schedule Management</h1>
        <p class="page-sub">班別模板與指派管理</p>
      </div>

      <!-- Feature Gate Error -->
      <div v-if="featureDisabled" class="state-box error">
        Schedule feature 尚未啟用，請聯絡管理員。
      </div>

      <template v-else>
        <!-- Section A: Shift Templates -->
        <div class="section-card">
          <div class="section-header">
            <h2 class="section-title">Shift Templates（班別模板）</h2>
            <div class="header-actions">
              <span class="section-badge">{{ templates.length }} 筆</span>
              <button class="btn-add" @click="toggleCreateForm" :disabled="tplLoading">
                {{ showCreateForm ? "收起" : "+ 新增模板" }}
              </button>
            </div>
          </div>

          <!-- Inline Create Form -->
          <div v-if="showCreateForm" class="create-form-panel">
            <h3 class="form-title">建立新班別模板</h3>
            <div v-if="createError" class="form-msg form-msg--error">⚠ {{ createError }}</div>
            <div v-if="createSuccess" class="form-msg form-msg--success">✓ 班別模板建立成功</div>
            <div class="form-grid">
              <div class="form-field">
                <label class="field-label">Code <span class="required">*</span></label>
                <input v-model="form.code" class="field-input" type="text" placeholder="e.g. DAY_SHIFT" maxlength="32" />
              </div>
              <div class="form-field">
                <label class="field-label">名稱 <span class="required">*</span></label>
                <input v-model="form.name" class="field-input" type="text" placeholder="e.g. 日班" maxlength="64" />
              </div>
              <div class="form-field">
                <label class="field-label">上班時間 <span class="required">*</span></label>
                <input v-model="form.start_time" class="field-input" type="time" />
              </div>
              <div class="form-field">
                <label class="field-label">下班時間 <span class="required">*</span></label>
                <input v-model="form.end_time" class="field-input" type="time" />
              </div>
              <div class="form-field">
                <label class="field-label">休息時間（分鐘）</label>
                <input v-model.number="form.break_minutes" class="field-input" type="number" min="0" placeholder="0" />
              </div>
              <div class="form-field form-field--check">
                <label class="field-label-check">
                  <input v-model="form.is_overnight" type="checkbox" />
                  過夜班
                </label>
              </div>
              <div class="form-field form-field--check">
                <label class="field-label-check">
                  <input v-model="form.is_active" type="checkbox" />
                  啟用
                </label>
              </div>
            </div>
            <div class="form-actions">
              <button class="btn-submit" @click="submitCreate" :disabled="createLoading">
                <span v-if="createLoading">提交中...</span>
                <span v-else>建立</span>
              </button>
              <button class="btn-cancel" @click="cancelCreate" :disabled="createLoading">取消</button>
            </div>
          </div>

          <div class="section-body">
            <div v-if="editError" class="form-msg form-msg--error">⚠ {{ editError }}</div>
            <div v-if="editSuccess" class="form-msg form-msg--success">✓ 班別模板更新成功</div>
            <div v-if="tplLoading" class="state-box">
              <div class="spinner"></div>
              <span>載入中...</span>
            </div>
            <div v-else-if="tplError" class="state-box error">⚠ {{ tplError }}</div>
            <div v-else-if="templates.length === 0" class="state-box empty">目前無班別模板資料</div>
            <div v-else class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>名稱</th>
                    <th>上班時間</th>
                    <th>下班時間</th>
                    <th>休息(分)</th>
                    <th>過夜</th>
                    <th>狀態</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in templates" :key="t.id">
                    <td><code class="code-chip">{{ t.code }}</code></td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <input v-model="editForm.name" class="field-input field-input--inline" type="text" maxlength="64" />
                      </template>
                      <template v-else>{{ t.name }}</template>
                    </td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <input v-model="editForm.start_time" class="field-input field-input--inline" type="time" />
                      </template>
                      <template v-else>{{ t.start_time }}</template>
                    </td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <input v-model="editForm.end_time" class="field-input field-input--inline" type="time" />
                      </template>
                      <template v-else>{{ t.end_time }}</template>
                    </td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <input v-model.number="editForm.break_minutes" class="field-input field-input--inline" type="number" min="0" />
                      </template>
                      <template v-else>{{ t.break_minutes }}</template>
                    </td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <label class="inline-check">
                          <input v-model="editForm.is_overnight" type="checkbox" />
                          過夜
                        </label>
                      </template>
                      <template v-else>{{ t.is_overnight ? "是" : "否" }}</template>
                    </td>
                    <td>
                      <span :class="t.is_active ? 'badge-active' : 'badge-inactive'">
                        {{ t.is_active ? "啟用" : "停用" }}
                      </span>
                    </td>
                    <td>
                      <template v-if="editingTemplateId === t.id">
                        <button class="btn-action btn-save" :disabled="editLoading" @click="submitEditTemplate(t)">
                          {{ editLoading ? "儲存中..." : "儲存" }}
                        </button>
                        <button class="btn-action btn-inline-cancel" :disabled="editLoading" @click="cancelEditTemplate">取消</button>
                      </template>
                      <template v-else>
                        <button
                          class="btn-action btn-edit"
                          :disabled="editLoading || (editingTemplateId && editingTemplateId !== t.id)"
                          @click="startEditTemplate(t)"
                        >
                          編輯
                        </button>
                        <button
                          v-if="t.is_active"
                          class="btn-action btn-deactivate"
                          :disabled="tplActionId === t.id || !!editingTemplateId"
                          @click="toggleTemplateActive(t)"
                        >
                          {{ tplActionId === t.id ? "處理中..." : "停用" }}
                        </button>
                        <button
                          v-else
                          class="btn-action btn-activate"
                          :disabled="tplActionId === t.id || !!editingTemplateId"
                          @click="toggleTemplateActive(t)"
                        >
                          {{ tplActionId === t.id ? "處理中..." : "啟用" }}
                        </button>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Section B: Shift Assignments -->
        <div class="section-card">
          <div class="section-header">
            <h2 class="section-title">Shift Assignments（班別指派）</h2>
            <div class="header-actions">
              <span class="section-badge">{{ assignments.length }} 筆</span>
              <button class="btn-add" @click="toggleCreateAsgForm" :disabled="asgLoading || tplLoading">
                {{ showCreateAsgForm ? "收起" : "+ 新增指派" }}
              </button>
            </div>
          </div>

          <!-- Inline Create Assignment Form -->
          <div v-if="showCreateAsgForm" class="create-form-panel">
            <h3 class="form-title">建立新班別指派</h3>
            <div v-if="createAsgError" class="form-msg form-msg--error">⚠ {{ createAsgError }}</div>
            <div v-if="createAsgSuccess" class="form-msg form-msg--success">✓ 班別指派建立成功</div>
            <div v-if="templates.length === 0" class="form-msg form-msg--error">請先載入班別模板再新增指派</div>
            <div v-else class="form-grid">
              <div class="form-field">
                <label class="field-label">員工 ID <span class="required">*</span></label>
                <input v-model="asgForm.user_id" class="field-input" type="text" placeholder="輸入 User UUID" />
              </div>
              <div class="form-field">
                <label class="field-label">班別模板 <span class="required">*</span></label>
                <select v-model="asgForm.shift_template_id" class="field-input">
                  <option value="" disabled>請選擇模板</option>
                  <option v-for="t in templates" :key="t.id" :value="t.id">
                    {{ t.code }} — {{ t.name }}
                  </option>
                </select>
              </div>
              <div class="form-field">
                <label class="field-label">工作日期 <span class="required">*</span></label>
                <input v-model="asgForm.work_date" class="field-input" type="date" />
              </div>
              <div class="form-field">
                <label class="field-label">狀態</label>
                <select v-model="asgForm.status" class="field-input">
                  <option value="scheduled">scheduled</option>
                  <option value="confirmed">confirmed</option>
                </select>
              </div>
              <div class="form-field" style="grid-column: span 2">
                <label class="field-label">備註</label>
                <input v-model="asgForm.notes" class="field-input" type="text" placeholder="可留空" />
              </div>
            </div>
            <div class="form-actions">
              <button class="btn-submit" @click="submitCreateAsg" :disabled="createAsgLoading || templates.length === 0">
                <span v-if="createAsgLoading">提交中...</span>
                <span v-else>建立</span>
              </button>
              <button class="btn-cancel" @click="cancelCreateAsg" :disabled="createAsgLoading">取消</button>
            </div>
          </div>
          <div class="section-body">
            <div v-if="asgLoading" class="state-box">
              <div class="spinner"></div>
              <span>載入中...</span>
            </div>
            <div v-else-if="asgError" class="state-box error">⚠ {{ asgError }}</div>
            <div v-else-if="assignments.length === 0" class="state-box empty">目前無班別指派資料</div>
            <div v-else class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>工作日期</th>
                    <th>員工 ID</th>
                    <th>班別 ID</th>
                    <th>狀態</th>
                    <th>備註</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in assignments" :key="a.id">
                    <td>{{ a.work_date }}</td>
                    <td><code class="uuid-chip">{{ a.user_id.slice(0, 8) }}...</code></td>
                    <td><code class="uuid-chip">{{ a.shift_template_id.slice(0, 8) }}...</code></td>
                    <td><span :class="statusClass(a.status)">{{ a.status }}</span></td>
                    <td>{{ a.notes || "—" }}</td>
                    <td>
                      <button
                        v-if="a.status !== 'cancelled'"
                        class="btn-action btn-cancel-asg"
                        :disabled="asgActionId === a.id"
                        @click="cancelAssignment(a)"
                      >
                        {{ asgActionId === a.id ? "處理中..." : "取消" }}
                      </button>
                      <span v-else class="text-cancelled">已取消</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { scheduleApi } from '@/api/schedule'

// Shift Templates state
const templates  = ref([])
const tplLoading = ref(false)
const tplError   = ref(null)

// Shift Assignments state
const assignments = ref([])
const asgLoading  = ref(false)
const asgError    = ref(null)

// Feature gate
const featureDisabled = ref(false)

// Create Template state
const showCreateForm = ref(false)
const createLoading  = ref(false)
const createError    = ref(null)
const createSuccess  = ref(false)

const emptyForm = () => ({
  code:          '',
  name:          '',
  start_time:    '',
  end_time:      '',
  break_minutes: 0,
  is_overnight:  false,
  is_active:     true,
})

const form = ref(emptyForm())

// Helpers
function isFeatureDisabled(err) {
  return err?.status === 403 || err?.data?.code === 'FEATURE_DISABLED'
}

function statusClass(status) {
  if (status === 'scheduled') return 'badge-scheduled'
  if (status === 'confirmed') return 'badge-confirmed'
  if (status === 'cancelled') return 'badge-cancelled'
  return ''
}

// Create form controls
function toggleCreateForm() {
  showCreateForm.value = !showCreateForm.value
  if (!showCreateForm.value) resetCreate()
}

function cancelCreate() {
  showCreateForm.value = false
  resetCreate()
}

function resetCreate() {
  form.value          = emptyForm()
  createError.value   = null
  createSuccess.value = false
}

async function submitCreate() {
  createError.value   = null
  createSuccess.value = false
  createLoading.value = true
  try {
    await scheduleApi.createTemplate(form.value)
    createSuccess.value = true
    form.value = emptyForm()
    await fetchTemplates()
    setTimeout(() => {
      createSuccess.value  = false
      showCreateForm.value = false
    }, 1500)
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      createError.value = err?.message || '建立失敗，請再試一次'
    }
  } finally {
    createLoading.value = false
  }
}

// Template edit
const editingTemplateId = ref(null)
const editLoading = ref(false)
const editError = ref(null)
const editSuccess = ref(false)
const editForm = ref({
  name: '',
  start_time: '',
  end_time: '',
  break_minutes: 0,
  is_overnight: false,
})

function normalizeTimeInput(value) {
  if (!value) return ''
  return String(value).slice(0, 5)
}

function toApiTime(value) {
  if (!value) return value
  return value.length === 5 ? `${value}:00` : value
}

function startEditTemplate(t) {
  editError.value = null
  editSuccess.value = false
  editingTemplateId.value = t.id
  editForm.value = {
    name: t.name || '',
    start_time: normalizeTimeInput(t.start_time),
    end_time: normalizeTimeInput(t.end_time),
    break_minutes: Number(t.break_minutes ?? 0),
    is_overnight: !!t.is_overnight,
  }
}

function cancelEditTemplate() {
  editingTemplateId.value = null
  editError.value = null
  editForm.value = {
    name: '',
    start_time: '',
    end_time: '',
    break_minutes: 0,
    is_overnight: false,
  }
}

async function submitEditTemplate(t) {
  editError.value = null
  editSuccess.value = false
  editLoading.value = true
  try {
    await scheduleApi.updateTemplate(t.id, {
      name: editForm.value.name,
      start_time: toApiTime(editForm.value.start_time),
      end_time: toApiTime(editForm.value.end_time),
      break_minutes: Number(editForm.value.break_minutes ?? 0),
      is_overnight: !!editForm.value.is_overnight,
    })
    await fetchTemplates()
    editingTemplateId.value = null
    editSuccess.value = true
    setTimeout(() => {
      editSuccess.value = false
    }, 1500)
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      editError.value = err?.message || '更新失敗，請再試一次'
    }
  } finally {
    editLoading.value = false
  }
}

// Template activate / deactivate
const tplActionId = ref(null)

async function toggleTemplateActive(t) {
  if (!window.confirm(t.is_active ? `確定要停用「${t.name}」嗎？` : `確定要啟用「${t.name}」嗎？`)) return
  tplActionId.value = t.id
  try {
    if (t.is_active) {
      await scheduleApi.deactivateTemplate(t.id)
    } else {
      await scheduleApi.activateTemplate(t.id)
    }
    await fetchTemplates()
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      tplError.value = err?.message || '操作失敗，請再試一次'
    }
  } finally {
    tplActionId.value = null
  }
}

// Assignment cancel
const asgActionId = ref(null)

async function cancelAssignment(a) {
  if (!window.confirm(`確定要取消此指派（${a.work_date}）嗎？`)) return
  asgActionId.value = a.id
  try {
    await scheduleApi.cancelAssignment(a.id)
    await fetchAssignments()
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      asgError.value = err?.message || '取消失敗，請再試一次'
    }
  } finally {
    asgActionId.value = null
  }
}

// Fetch
async function fetchTemplates() {
  tplLoading.value = true
  tplError.value   = null
  try {
    const data = await scheduleApi.listTemplates()
    templates.value = Array.isArray(data) ? data : []
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      tplError.value = err?.message || '載入班別模板失敗'
    }
  } finally {
    tplLoading.value = false
  }
}

async function fetchAssignments() {
  asgLoading.value = true
  asgError.value   = null
  try {
    const data = await scheduleApi.listAssignments()
    assignments.value = Array.isArray(data) ? data : []
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      asgError.value = err?.message || '載入班別指派失敗'
    }
  } finally {
    asgLoading.value = false
  }
}

// Create Assignment state
const showCreateAsgForm = ref(false)
const createAsgLoading  = ref(false)
const createAsgError    = ref(null)
const createAsgSuccess  = ref(false)

const emptyAsgForm = () => ({
  user_id:           '',
  shift_template_id: '',
  work_date:         '',
  status:            'scheduled',
  notes:             '',
})

const asgForm = ref(emptyAsgForm())

// Assignment create controls
function toggleCreateAsgForm() {
  showCreateAsgForm.value = !showCreateAsgForm.value
  if (!showCreateAsgForm.value) resetCreateAsg()
}

function cancelCreateAsg() {
  showCreateAsgForm.value = false
  resetCreateAsg()
}

function resetCreateAsg() {
  asgForm.value          = emptyAsgForm()
  createAsgError.value   = null
  createAsgSuccess.value = false
}

async function submitCreateAsg() {
  createAsgError.value   = null
  createAsgSuccess.value = false
  createAsgLoading.value = true
  try {
    await scheduleApi.createAssignment(asgForm.value)
    createAsgSuccess.value = true
    asgForm.value = emptyAsgForm()
    await fetchAssignments()
    setTimeout(() => {
      createAsgSuccess.value  = false
      showCreateAsgForm.value = false
    }, 1500)
  } catch (err) {
    if (isFeatureDisabled(err)) {
      featureDisabled.value = true
    } else {
      createAsgError.value = err?.message || '建立失敗，請再試一次'
    }
  } finally {
    createAsgLoading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
  fetchAssignments()
})
</script>

<style scoped>
.page-root { min-height: 100vh; background: var(--bg-main); }

.page-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 1.5rem; font-weight: 700; color: var(--heading); }
.page-sub { font-size: 0.85rem; color: var(--text-secondary); }

.section-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-main);
}

.section-title { font-size: 0.95rem; font-weight: 600; color: var(--heading); margin: 0; }

.header-actions { display: flex; align-items: center; gap: 10px; }

.section-badge {
  font-size: 0.75rem; font-weight: 600;
  color: var(--text-secondary);
  background: var(--border-light);
  border-radius: 4px; padding: 2px 8px;
}

.btn-add {
  font-size: 0.78rem; font-weight: 600;
  color: white; background: var(--primary, #3b5bdb);
  border: none; border-radius: 6px;
  padding: 5px 12px; cursor: pointer; transition: opacity 0.15s;
}
.btn-add:hover { opacity: 0.85; }
.btn-add:disabled { opacity: 0.5; cursor: not-allowed; }

/* Inline Create Form */
.create-form-panel {
  padding: 20px;
  border-bottom: 1px solid var(--border-light);
  background: #f8faff;
}

.form-title { font-size: 0.9rem; font-weight: 600; color: var(--heading); margin: 0 0 14px; }

.form-msg {
  padding: 8px 12px; border-radius: 6px;
  font-size: 0.82rem; margin-bottom: 12px;
}
.form-msg--error   { background: #fff5f5; color: #c62828; border: 1px solid #fcc; }
.form-msg--success { background: #f0fdf4; color: #2e7d32; border: 1px solid #c8e6c9; }

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-field--check { justify-content: flex-end; }

.field-label { font-size: 0.75rem; font-weight: 500; color: var(--text-secondary); }
.required { color: #c62828; }

.field-input {
  padding: 6px 10px;
  border: 1px solid var(--border-medium, #d0d7de);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s;
}
.field-input:focus { border-color: var(--primary, #3b5bdb); }
.field-input--inline { min-width: 110px; padding: 4px 8px; font-size: 0.8rem; }

.field-label-check {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.85rem; color: var(--text-primary); cursor: pointer;
}

.form-actions { display: flex; gap: 8px; }

.btn-submit {
  font-size: 0.82rem; font-weight: 600;
  color: white; background: var(--primary, #3b5bdb);
  border: none; border-radius: 6px;
  padding: 6px 18px; cursor: pointer; transition: opacity 0.15s;
}
.btn-submit:hover { opacity: 0.85; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-cancel {
  font-size: 0.82rem; font-weight: 600;
  color: var(--text-secondary); background: white;
  border: 1px solid var(--border-medium, #d0d7de);
  border-radius: 6px; padding: 6px 18px; cursor: pointer;
}
.btn-cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.section-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

.state-box {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; padding: 40px 20px;
  border: 1px solid var(--border-light); border-radius: 8px;
  color: var(--text-secondary); font-size: 0.875rem;
}
.state-box.error { color: #c0392b; border-color: #fcc; background: #fff5f5; }
.state-box.empty { color: var(--text-hint); }

.spinner {
  width: 18px; height: 18px;
  border: 3px solid var(--border-light);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.table-wrap { overflow-x: auto; border: 1px solid var(--border-light); border-radius: 8px; }

.data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }

.data-table th {
  background: var(--bg-main);
  color: var(--text-secondary); font-weight: 600; font-size: 0.75rem;
  text-transform: uppercase; letter-spacing: 0.04em;
  padding: 10px 14px; text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.data-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}

.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--bg-hover); }

.code-chip {
  font-family: monospace; font-size: 0.8rem;
  background: #f0f4ff; color: #3b5bdb;
  border-radius: 4px; padding: 1px 6px;
}

.uuid-chip {
  font-family: monospace; font-size: 0.78rem;
  background: var(--bg-main); color: var(--text-secondary);
  border-radius: 4px; padding: 1px 6px;
}

.badge-active    { color: #2e7d32; background: #e8f5e9; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; }
.badge-inactive  { color: #757575; background: #f5f5f5; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; }
.badge-scheduled { color: #1565c0; background: #e3f2fd; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; }
.badge-confirmed { color: #2e7d32; background: #e8f5e9; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; }
.badge-cancelled { color: #c62828; background: #ffebee; border-radius: 4px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; }

/* Action buttons in table */
.btn-action {
  font-size: 0.75rem; font-weight: 600;
  border: none; border-radius: 4px;
  padding: 3px 10px; cursor: pointer; transition: opacity 0.15s;
}
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-activate   { color: #2e7d32; background: #e8f5e9; }
.btn-activate:hover:not(:disabled)   { background: #c8e6c9; }
.btn-deactivate { color: #c62828; background: #fff3e0; }
.btn-deactivate:hover:not(:disabled) { background: #ffe0b2; }
.btn-edit { color: #1e40af; background: #e0e7ff; margin-right: 6px; }
.btn-edit:hover:not(:disabled) { background: #c7d2fe; }
.btn-save { color: #ffffff; background: #2563eb; margin-right: 6px; }
.btn-save:hover:not(:disabled) { background: #1d4ed8; }
.btn-inline-cancel { color: #4b5563; background: #f3f4f6; }
.btn-inline-cancel:hover:not(:disabled) { background: #e5e7eb; }
.inline-check { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; }

.btn-cancel-asg { color: #6d4c41; background: #fbe9e7; }
.btn-cancel-asg:hover:not(:disabled) { background: #ffccbc; }

.text-cancelled {
  font-size: 0.75rem;
  color: var(--text-hint, #aaa);
  font-style: italic;
}
</style>
