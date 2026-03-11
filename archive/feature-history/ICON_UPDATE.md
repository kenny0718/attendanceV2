# 外出/返回圖標更新

**日期**: 2026-03-10  
**修改**: 調整外出和返回打卡的圖標方向

---

## 修改內容

### 外出打卡圖標
- **修改前**: 向右平行箭頭 →
- **修改後**: 向右離開箭頭 ↗

```html
<!-- 外出打卡 -->
<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H3" />
</svg>
```

### 返回打卡圖標
- **修改前**: 向左平行箭頭 ←
- **修改後**: 向左進入箭頭 ↙

```html
<!-- 返回打卡 -->
<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M7 8l-4 4m0 0l4 4m-4-4h18" />
</svg>
```

---

## 視覺效果

**外出**: 箭頭從門框向外離開 📤  
**返回**: 箭頭從外面進入門框 📥

---

## 修改文件
- `frontend/src/views/Home.vue` (line 206, 223)

## 編譯狀態
✅ 成功 (2.67s)

---

**修改時間**: 2026-03-10
