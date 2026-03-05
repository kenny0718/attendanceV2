# 考勤打卡系統 UI/UX 設計報告
## 基於舊系統經驗與配色整合的完整設計方案

---

**專案名稱**: 考勤打卡系統 (Attendance System)  
**技術棧**: Vue 3 + Vite + Tailwind CSS 4 + Pinia  
**設計風格**: 專業沉穩、藍色+沙色雙色調  
**參考系統**: `/opt/oldsystem/attendancev1`  
**報告日期**: 2026-03-05

---

## 📋 目錄

1. [設計理念](#設計理念)
2. [配色系統](#配色系統)
3. [組件設計](#組件設計)
4. [響應式設計](#響應式設計)
5. [交互設計](#交互設計)
6. [動畫效果](#動畫效果)
7. [無障礙設計](#無障礙設計)
8. [設計檢查清單](#設計檢查清單)

---

## 🎨 設計理念

### 核心價值

```
專業性 > 美觀性
穩定性 > 創新性
易用性 > 功能性
```

### 設計目標

1. **沉穩專業** - 適合企業環境的正式感
2. **清晰明確** - 打卡操作一目了然
3. **溫暖親和** - 沙色調增加溫度感
4. **高效便捷** - 減少操作步驟

### 與序號系統的差異

| 特性 | 序號系統 (PSMS) | 考勤系統 (Attendance) |
|------|----------------|---------------------|
| **色調** | 亮藍色 (#2563EB) | 商務藍 (#4A6FA5) |
| **風格** | 現代、科技感 | 沉穩、企業感 |
| **輔助色** | 灰色系 | 沙色系 (#F2E8DF) |
| **適用場景** | 動態操作、產品管理 | 正式操作、人事管理 |
| **視覺感受** | 清新、活潑 | 穩重、溫暖 |

---

## 🎨 配色系統

### 主色調 - 深藍色系

```css
/* 主要藍色 - 用於主要按鈕、導航欄 */
--primary-blue: #4A6FA5;
--primary-blue-hover: #3D5A8A;
--primary-blue-light: #7BA3D1;
--primary-blue-lighter: #DDEAF3;
--primary-blue-lightest: #EBF4F9;

/* 深海藍 - 用於標題、重點強調 */
--heading-blue: #1C3B6B;
```

**使用場景**:
- 主要按鈕：上班打卡、確認操作
- 導航欄背景
- 重要標題
- 連結文字

### 輔助色調 - 沙色/米色系

```css
/* 沙色系 - 用於次要按鈕、輔助區域 */
--secondary-sand: #F2E8DF;
--secondary-sand-hover: #E8D9CA;
--secondary-border: #DDCBB5;
--accent-beige: #BFBF99;
```

**使用場景**:
- 次要按鈕：外出打卡、功能按鈕
- 下拉選單背景
- 輔助資訊區塊
- 裝飾性邊框

### 中性色系

```css
/* 背景色 */
--bg-main: #F4F7F9;        /* 頁面主背景 */
--bg-card: #FFFFFF;        /* 卡片背景 */
--bg-hover: #F8FBFE;       /* Hover 背景 */

/* 文字色 */
--text-primary: #2D3A52;   /* 主要文字 */
--text-secondary: #5A6C7D; /* 次要文字 */
--text-hint: #A0B4C7;      /* 提示文字 */
--text-disabled: #C5D0DC;  /* 禁用文字 */
```

### 功能色彩

```css
/* 狀態色 */
--success: #2E7D32;        /* 成功 */
--success-bg: #E8F5E9;     /* 成功背景 */
--error: #C62828;          /* 錯誤 */
--error-bg: #FFEBEE;       /* 錯誤背景 */
--warning: #F57C00;        /* 警告 */
--warning-bg: #FFF3E0;     /* 警告背景 */
--info: #1976D2;           /* 資訊 */
--info-bg: #E3F2FD;        /* 資訊背景 */
```

### 配色速查表

| 用途 | 色碼 | Tailwind | 使用場景 |
|------|------|----------|----------|
| 主要按鈕 | #4A6FA5 | bg-[#4A6FA5] | 上班/下班打卡 |
| 主要 Hover | #3D5A8A | bg-[#3D5A8A] | 按鈕懸停 |
| 次要按鈕 | #F2E8DF | bg-[#F2E8DF] | 外出/返回打卡 |
| 次要 Hover | #E8D9CA | bg-[#E8D9CA] | 次要懸停 |
| 標題文字 | #1C3B6B | text-[#1C3B6B] | 頁面標題 |
| 主要文字 | #2D3A52 | text-[#2D3A52] | 正文內容 |
| 次要文字 | #5A6C7D | text-[#5A6C7D] | 說明文字 |
| 頁面背景 | #F4F7F9 | bg-[#F4F7F9] | 整體背景 |
| 卡片背景 | #FFFFFF | bg-white | 內容卡片 |

---

## 🧩 組件設計

### 1. 按鈕組件

#### 主要按鈕 (Primary Button)

```vue
<template>
  <button 
    class="px-8 py-6 bg-[#4A6FA5] hover:bg-[#3D5A8A] 
           text-white rounded-2xl text-xl font-bold
           transition-all shadow-lg hover:shadow-xl
           disabled:bg-[#DDEAF3] disabled:text-[#A0B4C7] 
           disabled:cursor-not-allowed disabled:shadow-none"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
```

#### 次要按鈕 (Secondary Button)

```vue
<template>
  <button 
    class="px-6 py-4 bg-[#F2E8DF] hover:bg-[#E8D9CA] 
           text-[#2D3A52] rounded-xl font-semibold
           transition-all"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
```

### 2. 卡片組件

```vue
<template>
  <div class="bg-white rounded-2xl p-8 shadow-md border border-[#F0F4F8]">
    <h2 v-if="title" class="text-2xl font-bold text-[#1C3B6B] mb-6 
                            pb-4 border-b-2 border-[#F4F7F9]">
      {{ title }}
    </h2>
    <div class="text-[#2D3A52]">
      <slot />
    </div>
  </div>
</template>
```

### 3. 狀態卡片

```vue
<template>
  <div class="p-5 bg-[#F4F7F9] hover:bg-[#EBF4F9] 
              rounded-xl text-center transition-all">
    <div class="text-sm text-[#5A6C7D] mb-2 font-medium">
      {{ label }}
    </div>
    <div class="text-2xl font-bold" 
         :class="value ? 'text-[#4A6FA5]' : 'text-[#A0B4C7]'">
      {{ value || '-' }}
    </div>
  </div>
</template>
```

### 4. 導航欄

```vue
<template>
  <nav class="bg-[#4A6FA5] text-white p-4 shadow-lg">
    <div class="container mx-auto flex justify-between items-center">
      <h1 class="text-xl font-bold">考勤系統</h1>
      
      <div class="flex flex-col items-end">
        <span class="font-semibold">{{ user.name }}</span>
        <span class="text-sm opacity-90">{{ user.company }}</span>
      </div>
      
      <div class="flex gap-3">
        <button class="px-4 py-2 bg-white/20 hover:bg-white/30 
                       rounded-lg transition">
          個人資料
        </button>
        <button class="px-4 py-2 bg-white/20 hover:bg-white/30 
                       rounded-lg transition">
          登出
        </button>
      </div>
    </div>
  </nav>
</template>
```

### 5. 表單輸入

```vue
<template>
  <div class="mb-5">
    <label class="block text-sm font-medium text-[#2D3A52] mb-2">
      {{ label }}
    </label>
    <input 
      v-model="modelValue"
      :type="type"
      :placeholder="placeholder"
      class="w-full px-4 py-3 border border-[#DDCBB5] rounded-xl
             focus:outline-none focus:ring-2 focus:ring-[#4A6FA5] 
             focus:border-transparent transition"
    />
  </div>
</template>
```

### 6. 下拉選單

```vue
<template>
  <select 
    v-model="modelValue"
    class="w-full px-4 py-3 bg-[#F2E8DF] border border-[#DDCBB5] 
           rounded-xl text-[#2D3A52] cursor-pointer
           hover:bg-[#E8D9CA] focus:outline-none 
           focus:ring-2 focus:ring-[#4A6FA5] transition"
  >
    <option value="">{{ placeholder }}</option>
    <option v-for="option in options" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</template>
```

### 7. 彈窗 (Modal)

```vue
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" 
           class="fixed inset-0 z-50 flex items-center justify-center">
        <!-- 背景遮罩 -->
        <div class="absolute inset-0 bg-black/50" 
             @click="$emit('update:modelValue', false)">
        </div>
        
        <!-- 彈窗內容 -->
        <div class="relative bg-white rounded-2xl p-8 max-w-md w-full 
                    shadow-2xl z-10">
          <h3 class="text-2xl font-bold text-[#1C3B6B] mb-4">
            {{ title }}
          </h3>
          <div class="text-[#2D3A52]">
            <slot />
          </div>
          <button 
            @click="$emit('update:modelValue', false)"
            class="mt-6 w-full px-6 py-3 bg-[#4A6FA5] hover:bg-[#3D5A8A] 
                   text-white rounded-xl font-semibold transition"
          >
            確定
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
```

---

## 📱 響應式設計

### 斷點定義

```css
/* 手機版 */
@media (max-width: 640px) {
  /* 單列佈局 */
  .grid-cols-4 { grid-template-columns: repeat(2, 1fr); }
  .grid-cols-2 { grid-template-columns: 1fr; }
  
  /* 全寬按鈕 */
  .punch-btn { width: 100%; }
  
  /* 減小內距 */
  .container { padding: 16px; }
}

/* 平板版 */
@media (min-width: 641px) and (max-width: 1024px) {
  /* 雙列佈局 */
  .grid-cols-4 { grid-template-columns: repeat(2, 1fr); }
  
  /* 適中按鈕 */
  .punch-btn { padding: 24px 20px; }
}

/* 桌面版 */
@media (min-width: 1025px) {
  /* 多列佈局 */
  .grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
  
  /* 標準按鈕 */
  .punch-btn { padding: 32px 24px; }
}
```

### 響應式組件範例

```vue
<template>
  <!-- 狀態卡片 - 響應式 -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <StatusCard label="上班時間" :value="status.punch_in" />
    <StatusCard label="下班時間" :value="status.punch_out" />
    <StatusCard label="外出時間" :value="status.break_out" />
    <StatusCard label="返回時間" :value="status.break_in" />
  </div>

  <!-- 打卡按鈕 - 響應式 -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
    <button class="punch-btn">上班打卡</button>
    <button class="punch-btn">下班打卡</button>
  </div>
</template>
```

---

## 🎭 交互設計

### 按鈕狀態

```css
/* 正常狀態 */
.btn {
  background: #4A6FA5;
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(74, 111, 165, 0.2);
}

/* Hover 狀態 */
.btn:hover {
  background: #3D5A8A;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(74, 111, 165, 0.3);
}

/* Active 狀態 */
.btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(74, 111, 165, 0.2);
}

/* 禁用狀態 */
.btn:disabled {
  background: #DDEAF3;
  color: #A0B4C7;
  cursor: not-allowed;
  box-shadow: none;
}
```

### 表單驗證提示

```vue
<template>
  <div class="form-group">
    <input 
      v-model="value"
      :class="{ 'border-red-500': error }"
      class="w-full px-4 py-3 border rounded-xl"
    />
    <p v-if="error" class="mt-2 text-sm text-red-600">
      {{ error }}
    </p>
  </div>
</template>
```

### 載入狀態

```vue
<template>
  <button :disabled="loading" class="btn-primary">
    <span v-if="loading" class="flex items-center justify-center">
      <svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" 
                stroke="currentColor" stroke-width="4" fill="none"/>
        <path class="opacity-75" fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      處理中...
    </span>
    <span v-else>確定</span>
  </button>
</template>
```

---

## ✨ 動畫效果

### 打卡成功動畫

```css
@keyframes punch-success {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.punch-success {
  animation: punch-success 0.5s ease-out;
}
```

### 淡入淡出

```css
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
```

### 滑入滑出

```css
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  transform: translateY(-20px);
  opacity: 0;
}

.slide-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
```

---

## ♿ 無障礙設計

### ARIA 標籤

```vue
<template>
  <button 
    aria-label="上班打卡"
    :aria-disabled="disabled"
    role="button"
  >
    上班打卡
  </button>
</template>
```

### 鍵盤導航

```vue
<script setup>
const handleKeydown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    handlePunch();
  }
};
</script>

<template>
  <div 
    tabindex="0"
    @keydown="handleKeydown"
    role="button"
  >
    打卡
  </div>
</template>
```

### 對比度要求

```
文字對比度：
- 正常文字：至少 4.5:1
- 大文字：至少 3:1
- 圖示：至少 3:1

我們的配色對比度：
- #2D3A52 on #FFFFFF: 11.2:1 ✓
- #4A6FA5 on #FFFFFF: 4.8:1 ✓
- #FFFFFF on #4A6FA5: 4.8:1 ✓
```

---

## ✅ 設計檢查清單

### 配色檢查

- [ ] 主色調使用 #4A6FA5（商務藍）
- [ ] 輔助色使用 #F2E8DF（沙色）
- [ ] 標題使用 #1C3B6B（深海藍）
- [ ] 背景使用 #F4F7F9（藍灰）
- [ ] 功能色保持一致（成功/錯誤/警告）

### 組件檢查

- [ ] 按鈕圓角 12-16px
- [ ] 卡片陰影 0 2px 8px
- [ ] 過渡時間 0.2s
- [ ] 字體使用系統字體
- [ ] 間距使用 8px 倍數

### 響應式檢查

- [ ] 手機版測試 (< 640px)
- [ ] 平板版測試 (641-1024px)
- [ ] 桌面版測試 (> 1024px)
- [ ] 觸控友善（按鈕至少 44px）

### 無障礙檢查

- [ ] ARIA 標籤完整
- [ ] 鍵盤可導航
- [ ] 對比度符合標準
- [ ] 焦點狀態清晰

---

## 📝 總結

### 設計特點

1. **專業沉穩** - 商務藍 + 沙色雙色調
2. **溫暖親和** - 沙色增加溫度感
3. **清晰明確** - 層次分明、易於理解
4. **系統區分** - 與序號系統形成對比

### 實作要點

1. 使用 Tailwind CSS 自定義配色
2. 組件化設計，提高可重用性
3. 響應式佈局，適配各種設備
4. 注重無障礙性，提升用戶體驗

### 下一步

1. 參考 [頁面設計文檔](./UI_UX設計報告_頁面設計.md) 實作具體頁面
2. 參考 [技術規範文檔](./UI_UX設計報告_技術規範.md) 配置開發環境
3. 參考 [開發指南](./參考舊系統_開發指南.md) 避免常見問題

---

**報告生成時間**: 2026-03-05  
**設計者**: Claude (Opus 4)  
**版本**: v1.0
