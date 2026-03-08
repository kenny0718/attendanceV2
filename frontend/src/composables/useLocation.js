/**
 * useLocation Composable
 * 
 * Shared location foundation for attendance system
 * 提供統一的 location 服務介面
 * 
 * @module composables/useLocation
 * @version 1.0.0
 * @since WP-11-12
 */

import { ref, computed } from 'vue'

/**
 * Location 錯誤碼
 */
export const LocationErrorCode = {
  NOT_SUPPORTED: 'NOT_SUPPORTED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
}

/**
 * useLocation Composable
 * 
 * 提供統一的 location 服務，包含：
 * - 裝置類型判斷
 * - GPS 定位獲取
 * - 權限狀態追蹤
 * - Loading 狀態管理
 * - 統一錯誤處理
 * 
 * @param {Object} options - 定位選項
 * @param {boolean} options.enableHighAccuracy - 是否使用高精度（預設 true）
 * @param {number} options.timeout - 超時時間（預設 10000ms）
 * @param {number} options.maximumAge - 快取時間（預設 0ms）
 * @returns {Object} Location state and methods
 * 
 * @example
 * ```javascript
 * import { useLocation } from '@/composables/useLocation'
 * 
 * const {
 *   location,
 *   error,
 *   isLoading,
 *   deviceType,
 *   isGPSRequired,
 *   getCurrentLocation,
 *   getLocationIfRequired
 * } = useLocation()
 * 
 * // 獲取定位（如果需要）
 * const gps = await getLocationIfRequired()
 * ```
 */
export function useLocation(options = {}) {
  // ==================== State ====================
  
  /**
   * 當前位置資料
   * @type {Ref<LocationData | null>}
   */
  const location = ref(null)
  
  /**
   * 錯誤資訊
   * @type {Ref<LocationError | null>}
   */
  const error = ref(null)
  
  /**
   * Loading 狀態
   * @type {Ref<boolean>}
   */
  const isLoading = ref(false)
  
  /**
   * 裝置類型
   * @type {Ref<'mobile' | 'pc'>}
   */
  const deviceType = ref('pc')
  
  // ==================== Options ====================
  
  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
    ...options
  }
  
  // ==================== Computed ====================
  
  /**
   * 是否需要 GPS（Mobile 需要，PC 不需要）
   * @type {ComputedRef<boolean>}
   */
  const isGPSRequired = computed(() => deviceType.value === 'mobile')
  
  // ==================== Methods ====================
  
  /**
   * 偵測裝置類型
   * @returns {'mobile' | 'pc'}
   */
  function detectDeviceType() {
    const userAgent = navigator.userAgent || ''
    const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
    deviceType.value = isMobile ? 'mobile' : 'pc'
    return deviceType.value
  }
  
  /**
   * 獲取當前位置
   * 
   * @returns {Promise<LocationData>} 位置資料
   * @throws {LocationError} 定位失敗時拋出錯誤
   * 
   * @example
   * ```javascript
   * try {
   *   const location = await getCurrentLocation()
   *   console.log(location.latitude, location.longitude)
   * } catch (err) {
   *   console.error(err.message)
   * }
   * ```
   */
  async function getCurrentLocation() {
    isLoading.value = true
    error.value = null
    
    try {
      // 檢查瀏覽器支援
      if (!navigator.geolocation) {
        throw createLocationError(
          '此裝置不支援定位功能',
          LocationErrorCode.NOT_SUPPORTED
        )
      }
      
      // 獲取定位
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          defaultOptions
        )
      })
      
      // 建立標準化的位置資料
      const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        captured_at: new Date().toISOString(),
        provider: 'gps'
      }
      
      location.value = locationData
      return locationData
      
    } catch (err) {
      const locationError = mapGeolocationError(err)
      error.value = locationError
      throw locationError
      
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 條件式獲取定位（根據裝置類型）
   * 
   * Mobile: 獲取 GPS
   * PC: 返回 null
   * 
   * @returns {Promise<LocationData | null>} 位置資料或 null
   * 
   * @example
   * ```javascript
   * const gps = await getLocationIfRequired()
   * 
   * const payload = { notes: '外出洽公' }
   * if (gps) {
   *   payload.gps = gps
   * }
   * ```
   */
  async function getLocationIfRequired() {
    if (isGPSRequired.value) {
      return await getCurrentLocation()
    }
    return null
  }
  
  /**
   * 清除錯誤
   */
  function clearError() {
    error.value = null
  }
  
  /**
   * 重置所有狀態
   */
  function reset() {
    location.value = null
    error.value = null
    isLoading.value = false
  }
  
  // ==================== Helper Functions ====================
  
  /**
   * 建立 LocationError 物件
   * @private
   */
  function createLocationError(message, code, originalError = null) {
    return {
      code,
      message,
      originalError
    }
  }
  
  /**
   * 將瀏覽器 GeolocationPositionError 轉換為 LocationError
   * @private
   */
  function mapGeolocationError(err) {
    let message = '無法獲取定位'
    let code = LocationErrorCode.UNKNOWN
    
    if (err.code) {
      switch (err.code) {
        case 1: // PERMISSION_DENIED
          message = '請開啟定位權限後再外出打點'
          code = LocationErrorCode.PERMISSION_DENIED
          break
        case 2: // POSITION_UNAVAILABLE
          message = '定位資訊無法取得'
          code = LocationErrorCode.POSITION_UNAVAILABLE
          break
        case 3: // TIMEOUT
          message = '定位請求逾時'
          code = LocationErrorCode.TIMEOUT
          break
      }
    }
    
    return createLocationError(message, code, err)
  }
  
  // ==================== Initialize ====================
  
  // 初始化時偵測裝置類型
  detectDeviceType()
  
  // ==================== Return ====================
  
  return {
    // State
    location,
    error,
    isLoading,
    deviceType,
    
    // Computed
    isGPSRequired,
    
    // Methods
    getCurrentLocation,
    getLocationIfRequired,
    clearError,
    reset
  }
}

/**
 * @typedef {Object} LocationData
 * @property {number} latitude - 緯度
 * @property {number} longitude - 經度
 * @property {number} accuracy - 精度（公尺）
 * @property {string} captured_at - 捕獲時間（ISO 8601）
 * @property {'gps'} provider - 定位提供者
 */

/**
 * @typedef {Object} LocationError
 * @property {string} code - 錯誤碼
 * @property {string} message - 錯誤訊息
 * @property {Error} [originalError] - 原始錯誤物件
 */
