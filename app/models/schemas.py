"""Pydantic schemas for request/response models."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# Request Schemas
class OMIEventRequest(BaseModel):
    """Request from OMI device webhook."""
    transcript: str = Field(..., description="Voice transcript text")
    entities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tentative entities from device")
    session_id: Optional[str] = Field(None, description="Session identifier")
    language: Optional[str] = Field("en", description="Language code (en, es) - defaults to en")


class QueryStockRequest(BaseModel):
    """Request to query stock levels."""
    sku: Optional[str] = None
    name: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None


class CreateReorderRequest(BaseModel):
    """Request to create a reorder."""
    product_id: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = Field(..., gt=0, description="Quantity to reorder")


class SalesSummaryRequest(BaseModel):
    """Request for sales summary."""
    window_days: int = Field(7, ge=1, le=365, description="Number of days to look back")


class SupplierInfoRequest(BaseModel):
    """Request for supplier information."""
    product_id: Optional[str] = None
    sku: Optional[str] = None


class DeliveryStatusRequest(BaseModel):
    """Request for delivery status."""
    reorder_id: Optional[str] = None
    purchase_order_id: Optional[str] = None


# Response Schemas
class OMIResponse(BaseModel):
    """Standard response schema for OMI device."""
    ok: bool
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    speech: str


class StockInfo(BaseModel):
    """Stock information result."""
    product_id: str
    sku: str
    name: str
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int
    low_stock: bool
    reorder_threshold: int


class ReorderResult(BaseModel):
    """Reorder creation result."""
    reorder_id: str
    product_id: str
    quantity: int
    status: str
    purchase_order_id: Optional[str] = None


class SalesSummaryResult(BaseModel):
    """Sales summary result."""
    total_quantity: int
    total_revenue: float
    window_days: int
    transaction_count: int


class SupplierInfoResult(BaseModel):
    """Supplier information result."""
    supplier_id: str
    supplier_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_time_days: int


class DeliveryStatusResult(BaseModel):
    """Delivery status result."""
    reorder_id: str
    status: str
    purchase_order_id: Optional[str] = None
    eta: Optional[str] = None
    quantity: int

