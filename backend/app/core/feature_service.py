"""Feature Service

WP-11-04A: Feature Gate 服務層
提供 feature flag 的查詢與驗證功能
"""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.features import FeatureKeys
from app.modules.tenants.models import CompanyEntitlement

logger = logging.getLogger(__name__)


class FeatureDisabledError(Exception):
    """Feature 未啟用錯誤"""
    def __init__(self, feature_key: str, company_id: str, message: Optional[str] = None):
        self.feature_key = feature_key
        self.company_id = company_id
        self.message = message or f"Feature '{feature_key}' is not enabled for company '{company_id}'"
        super().__init__(self.message)


class FeatureService:
    """Feature Gate 服務"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, bool] = {}
    
    def is_enabled(self, company_id: str, feature_key: str) -> bool:
        """檢查 feature 是否啟用"""
        FeatureKeys.validate(feature_key)
        
        cache_key = f"{company_id}:{feature_key}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        entitlement = self.db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == company_id,
            CompanyEntitlement.feature_key == feature_key
        ).first()
        
        enabled = entitlement.enabled if entitlement else False
        self._cache[cache_key] = enabled
        
        return enabled
    
    def require_enabled(self, company_id: str, feature_key: str) -> None:
        """要求 feature 必須啟用"""
        if not self.is_enabled(company_id, feature_key):
            raise FeatureDisabledError(feature_key, company_id)
    
    def get_all_features(self, company_id: str) -> Dict[str, bool]:
        """取得公司的所有 feature flags"""
        entitlements = self.db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == company_id
        ).all()
        
        result = {}
        for feature_key in FeatureKeys.all_keys():
            result[feature_key] = False
        
        for ent in entitlements:
            if ent.feature_key in result:
                result[ent.feature_key] = ent.enabled
        
        return result
    
    def clear_cache(self, company_id: Optional[str] = None, feature_key: Optional[str] = None) -> None:
        """清除快取"""
        if company_id and feature_key:
            cache_key = f"{company_id}:{feature_key}"
            if cache_key in self._cache:
                del self._cache[cache_key]
        elif company_id:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{company_id}:")]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()


def get_feature_service(db: Session) -> FeatureService:
    """取得 FeatureService 實例（FastAPI Dependency）"""
    return FeatureService(db)
