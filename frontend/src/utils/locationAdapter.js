/**
 * Location Adapter (臨時過渡層)
 * 
 * 目的: 在 shared location module 完成前，提供統一的定位介面
 * 注意: 這是臨時方案，未來會被 useLocation composable 取代
 * 
 * @deprecated 將在 shared location module 完成後移除
 */

/**
 * 獲取裝置類型
 * @returns {'mobile' | 'pc'}
 */
export function detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
}

/**
 * GPS 錯誤類型
 */
export class LocationError extends Error {
  constructor(message, code, originalError = null) {
    super(message)
    this.name = 'LocationError'
    this.code = code
    this.originalError = originalError
  }
}

/**
 * GPS 錯誤碼
 */
export const LocationErrorCode = {
  NOT_SUPPORTED: 'NOT_SUPPORTED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
}

/**
 * 獲取 GPS 定位
 * @param {Object} options - 定位選項
 * @returns {Promise<Object>} GPS 資料
 * @throws {LocationError}
 */
export async function getGPSLocation(options = {}) {
  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
    ...options
  }

  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new LocationError(
        '此裝置不支援定位功能',
        LocationErrorCode.NOT_SUPPORTED
      ))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          captured_at: new Date().toISOString(),
          provider: 'gps'
        })
      },
      (error) => {
        const locationError = mapGeolocationError(error)
        reject(locationError)
      },
      defaultOptions
    )
  })
}

/**
 * 將瀏覽器 GeolocationPositionError 轉換為 LocationError
 * @private
 */
function mapGeolocationError(error) {
  let message = '無法獲取定位'
  let code = LocationErrorCode.UNKNOWN

  switch (error.code) {
    case error.PERMISSION_DENIED:
      message = '請開啟定位權限後再外出打點'
      code = LocationErrorCode.PERMISSION_DENIED
      break
    case error.POSITION_UNAVAILABLE:
      message = '定位資訊無法取得'
      code = LocationErrorCode.POSITION_UNAVAILABLE
      break
    case error.TIMEOUT:
      message = '定位請求逾時'
      code = LocationErrorCode.TIMEOUT
      break
  }

  return new LocationError(message, code, error)
}

/**
 * 檢查是否需要 GPS（根據裝置類型）
 * @returns {boolean}
 */
export function isGPSRequired() {
  return detectDeviceType() === 'mobile'
}

/**
 * 獲取定位（如果需要）
 * @returns {Promise<Object|null>} GPS 資料或 null
 */
export async function getLocationIfRequired() {
  if (isGPSRequired()) {
    return await getGPSLocation()
  }
  return null
}
