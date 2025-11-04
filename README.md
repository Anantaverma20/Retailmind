# OMI Voice Inventory Assistant

A voice-powered inventory management system for small and medium clothing stores. Built with FastAPI, Supabase, and OpenAI for natural language understanding.

## Features

- **Voice-powered inventory queries**: "How many red hoodies are left?"
- **Voice reorders**: "Restock 25 black jeans"
- **Sales summaries**: Get revenue and quantity sold over time periods
- **Supplier information**: Query supplier details for products
- **Delivery tracking**: Check status of pending reorders
- **Intent parsing**: OpenAI-powered NLU with rules-based fallback
- **Security**: Token-based authentication, rate limiting
- **Data integration**: Ready for Shopify, QuickBooks, Airtable (optional)

## Architecture

- **Backend**: FastAPI with async handlers
- **Database**: Supabase (PostgreSQL) with structured tables
- **NLU**: OpenAI GPT-4o-mini (default) with rules-based fallback
- **Device**: OMI.me device integration via webhook

## Setup

### Prerequisites

- Python 3.9+
- Supabase project with configured tables
- OpenAI API key
- OMI device (optional for testing)

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd omi-inventory-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OMI_WEBHOOK_TOKEN=your_webhook_token
OPENAI_API_KEY=your_openai_api_key
INTENT_PROVIDER=openai
```

### Supabase Setup

1. Create the following tables in Supabase:

**products**
```sql
create table products (
  id uuid primary key default gen_random_uuid(),
  sku text unique not null,
  name text not null,
  color text,
  size text,
  quantity int not null default 0,
  reorder_threshold int not null default 10,
  supplier_id uuid references suppliers(id),
  updated_at timestamptz default now()
);

create index idx_products_ncs on products(name, color, size);
```

**sales**
```sql
create table sales (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id),
  quantity int not null,
  sale_price numeric not null,
  sale_date date not null default current_date,
  channel text
);

create index idx_sales_date on sales(sale_date);
```

**suppliers**
```sql
create table suppliers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text,
  phone text,
  lead_time_days int not null default 7
);
```

**reorders**
```sql
create table reorders (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id),
  quantity int not null,
  status text not null default 'pending',
  purchase_order_id text,
  created_at timestamptz default now(),
  eta date
);

create index idx_suppliers_po on reorders(purchase_order_id);
```

**voice_logs (optional)**
```sql
create table voice_logs (
  id uuid primary key default gen_random_uuid(),
  transcript text,
  intent text,
  entities jsonb,
  result jsonb,
  created_at timestamptz default now()
);
```

2. Import CSV data (10k rows each) via Supabase UI

3. Run validation script:
```bash
python scripts/validate_data.py
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### OMI Webhook (Main Entry Point)
```bash
curl -X POST http://localhost:8000/omi/event \
  -H "Content-Type: application/json" \
  -H "X-OMI-Token: your_webhook_token" \
  -d '{
    "transcript": "How many red hoodies are left?",
    "entities": {},
    "language": "en"
  }'
```

**Spanish Example:**
```bash
curl -X POST http://localhost:8000/omi/event \
  -H "Content-Type: application/json" \
  -H "X-OMI-Token: your_webhook_token" \
  -d '{
    "transcript": "¿Cuántas sudaderas rojas quedan?",
    "entities": {},
    "language": "es"
  }'
```

### Query Stock (Direct)
```bash
curl -X POST http://localhost:8000/query_stock \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hoodie",
    "color": "red"
  }'
```

### Create Reorder (Direct)
```bash
curl -X POST http://localhost:8000/create_reorder \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "HOODIE-RED-L",
    "quantity": 25
  }'
```

### Get Sales Summary (Direct)
```bash
curl -X POST http://localhost:8000/get_sales_summary \
  -H "Content-Type: application/json" \
  -d '{
    "window_days": 7
  }'
```

### Get Supplier Info (Direct)
```bash
curl -X POST http://localhost:8000/get_supplier_info \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "HOODIE-RED-L"
  }'
```

### Get Delivery Status (Direct)
```bash
curl -X POST http://localhost:8000/get_delivery_status \
  -H "Content-Type: application/json" \
  -d '{
    "reorder_id": "reorder-uuid"
  }'
```

## Testing

Run unit tests:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Response Format

All OMI webhook responses follow this schema:

```json
{
  "ok": true,
  "intent": "get_stock",
  "entities": {
    "name": "hoodie",
    "color": "red"
  },
  "result": {
    "items": [
      {
        "product_id": "uuid",
        "sku": "HOODIE-RED-L",
        "name": "hoodie",
        "color": "red",
        "size": "large",
        "quantity": 15,
        "low_stock": false,
        "reorder_threshold": 10
      }
    ]
  },
  "speech": "There are 15 hoodies in red size large in stock."
}
```

## Intent Types

- `get_stock`: Query stock levels
- `create_reorder`: Create purchase order/reorder
- `get_sales_summary`: Get sales statistics
- `get_supplier_info`: Get supplier details
- `get_delivery_status`: Check delivery status

## Enhanced Features

### Multilingual Support (EN/ES)

The system supports English and Spanish responses. Set the `language` field in OMI webhook requests:

```json
{
  "transcript": "¿Cuántas sudaderas rojas quedan?",
  "language": "es"
}
```

Or set `DEFAULT_LANGUAGE=es` in `.env` to use Spanish by default.

All speech responses are automatically translated based on the `language` field. Supported languages:
- `en` - English (default)
- `es` - Spanish

### Voice Logging

Every voice interaction is automatically logged to the `voice_logs` table in Supabase (if the table exists). Logs include:
- Transcript
- Detected intent
- Extracted entities
- Result data
- Timestamp

This enables the live voice logs panel in the frontend dashboard.

### Enhanced Error Handling

The system provides context-aware error messages in both English and Spanish:
- Database connection errors
- Product not found errors
- Invalid input validation
- Connection timeout recovery

All errors are logged with full stack traces for debugging while providing user-friendly messages.

## Configuration

### Intent Provider

Set `INTENT_PROVIDER` in `.env`:
- `openai`: Uses OpenAI GPT-4o-mini (default)
- `rules`: Uses keyword-based rules (fallback, works offline)

### Rate Limiting

Default: 60 requests per minute per IP address. Configured in `app.py`.

### Request Size Limits

Webhook endpoint: 256 KB max request body size.

## OMI Device Integration

1. Register webhook URL in OMI dashboard:
   - URL: `https://your-domain.com/omi/event`
   - Token: Set `OMI_WEBHOOK_TOKEN` in `.env`

2. Device sends POST requests with:
   - `transcript`: Voice transcript text
   - `entities`: Tentative entities from device (optional)

3. Backend responds with:
   - `speech`: Text to speak on device
   - `intent`, `entities`, `result`: Structured response

## Optional Integrations

### Shopify

Set `ENABLE_SHOPIFY=true` and configure:
```
SHOPIFY_API_KEY=
SHOPIFY_PASSWORD=
SHOPIFY_STORE=
```

### QuickBooks Online

Set `ENABLE_QBO=true` and configure:
```
QUICKBOOKS_CLIENT_ID=
QUICKBOOKS_CLIENT_SECRET=
```

### Airtable

Set `ENABLE_AIRTABLE=true` and configure:
```
AIRTABLE_API_KEY=
```

## Project Structure

```
.
├── app.py                 # FastAPI entry point
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings and env vars
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py     # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── supabase_client.py  # Supabase singleton
│       ├── intent_router.py    # Intent routing
│       ├── nlu_openai.py       # OpenAI parser
│       ├── nlu_rules.py        # Rules parser
│       └── handlers.py         # Business logic
├── frontend/              # Next.js dashboard
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── lib/               # API client & utilities
│   └── package.json
├── scripts/
│   └── validate_data.py    # Data validation
├── tests/
│   └── test_intents.py     # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## Frontend Dashboard

A Next.js dashboard is available in the `frontend/` directory. See `frontend/README.md` for setup and deployment instructions.

**Features:**
- Inventory table with search and filters
- Low stock alerts
- Sales summary with 7/30 day views
- Reorders and PO status tracking
- Live voice logs panel

**Deployment:** Ready for Vercel deployment. See `frontend/README.md` for details.

## Development

### Code Style

- Follow PEP 8
- Type hints for all functions
- Docstrings for all modules and functions

### Logging

Structured JSON logging using `structlog`. Logs include:
- Request IDs
- Intent parsing results
- Handler execution
- Errors with stack traces

## Troubleshooting

### Supabase Connection Issues

- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check Supabase project status
- Verify table names match exactly (case-sensitive)

### OpenAI Parsing Failures

- Check `OPENAI_API_KEY` is valid
- Verify API quota/billing
- System falls back to rules parser automatically

### Rate Limiting

- Check slowapi middleware is configured
- Verify IP detection works behind proxies


