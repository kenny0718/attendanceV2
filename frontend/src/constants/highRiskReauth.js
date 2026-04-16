export const HIGH_RISK_REAUTH_ACTIONS = [
  {
    key: 'attendance.bulk_approve',
    area: 'attendance-review',
    reason: '大量核准或退回打卡資料會直接影響薪資與出勤結算。'
  },
  {
    key: 'leave.final_approval',
    area: 'leave-review',
    reason: '請假最終核准會改變員工班表、出勤與薪資計算結果。'
  },
  {
    key: 'member.role_change',
    area: 'member-admin',
    reason: '變更角色或權限會影響後台可操作範圍。'
  },
  {
    key: 'tenant.settings_change',
    area: 'tenant-admin',
    reason: '公司設定、稅號、制度參數變更屬於高敏感操作。'
  },
  {
    key: 'system.export_restore',
    area: 'backup-audit',
    reason: '資料匯出、還原、稽核清除均屬高風險不可逆行為。'
  }
]
