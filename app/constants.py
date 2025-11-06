"""Application constants."""

# Database query limits
MAX_QUERY_RESULTS = 20
DEFAULT_REORDER_QUANTITY = 50
DEFAULT_SALES_WINDOW_DAYS = 7
MAX_SALES_WINDOW_DAYS = 365
REORDER_DUE_DAYS = 7
MAX_DELIVERY_ORDERS = 5

# Request limits
MAX_REQUEST_BODY_SIZE = 256 * 1024  # 256 KB
RATE_LIMIT_PER_MINUTE = 60

# Table names
TABLE_INVENTORY = "clothing_retail_inventory"
TABLE_TASKS = "employee_task_logs"
TABLE_SALES = "retail_sales_transactions"
TABLE_SUPPLIERS = "supplier_purchase_orders"
TABLE_VOICE_QUERIES = "voice_queries_inventory_assistant"
TABLE_VOICE_LOGS = "voice_logs"

# Task constants
TASK_TYPE_REORDER = "Reorder"
TASK_STATUS_PENDING = "Pending"
EMPLOYEE_SYSTEM = "System"

# Order statuses
ORDER_STATUS_PENDING = "Pending"
ORDER_STATUS_SHIPPED = "Shipped"
ORDER_STATUS_DELIVERED = "Delivered"

# Default values
DEFAULT_LANGUAGE = "en"
DEFAULT_PRODUCT_NAME = "Unknown"

