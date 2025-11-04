-- Create clothing_retail_inventory table
CREATE TABLE IF NOT EXISTS clothing_retail_inventory (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    color VARCHAR(50),
    size VARCHAR(10),
    cost_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    reorder_threshold INTEGER DEFAULT 0,
    supplier_id VARCHAR(20),
    last_restock_date DATE,
    location VARCHAR(255),
    barcode VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_product_id ON clothing_retail_inventory(product_id);
CREATE INDEX idx_category ON clothing_retail_inventory(category);
CREATE INDEX idx_stock_quantity ON clothing_retail_inventory(stock_quantity);
CREATE INDEX idx_supplier_id ON clothing_retail_inventory(supplier_id);

-- Create employee_task_logs table
CREATE TABLE IF NOT EXISTS employee_task_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(20) UNIQUE NOT NULL,
    employee_name VARCHAR(255),
    employee_role VARCHAR(100),
    task_type VARCHAR(100),
    assigned_date DATE,
    due_date DATE,
    completion_date DATE,
    status VARCHAR(50),
    related_product VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for employee tasks
CREATE INDEX idx_task_id ON employee_task_logs(task_id);
CREATE INDEX idx_employee_name ON employee_task_logs(employee_name);
CREATE INDEX idx_status ON employee_task_logs(status);
CREATE INDEX idx_related_product ON employee_task_logs(related_product);

-- Create retail_sales_transactions table
CREATE TABLE IF NOT EXISTS retail_sales_transactions (
    id SERIAL PRIMARY KEY,
    sale_id VARCHAR(20) UNIQUE NOT NULL,
    product_id VARCHAR(20),
    quantity_sold INTEGER,
    sale_date DATE,
    channel VARCHAR(50),
    revenue DECIMAL(10, 2),
    payment_method VARCHAR(50),
    customer_id VARCHAR(50),
    discount_applied BOOLEAN DEFAULT FALSE,
    city VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for sales transactions
CREATE INDEX idx_sale_id ON retail_sales_transactions(sale_id);
CREATE INDEX idx_sale_product_id ON retail_sales_transactions(product_id);
CREATE INDEX idx_sale_date ON retail_sales_transactions(sale_date);
CREATE INDEX idx_channel ON retail_sales_transactions(channel);

-- Create supplier_purchase_orders table
CREATE TABLE IF NOT EXISTS supplier_purchase_orders (
    id SERIAL PRIMARY KEY,
    supplier_id VARCHAR(20),
    supplier_name VARCHAR(255),
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    phone_number VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    product_categories_supplied TEXT,
    purchase_order_id VARCHAR(20) UNIQUE NOT NULL,
    order_date DATE,
    delivery_date DATE,
    status VARCHAR(50),
    total_cost DECIMAL(10, 2),
    payment_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for suppliers and orders
CREATE INDEX idx_supplier_id_po ON supplier_purchase_orders(supplier_id);
CREATE INDEX idx_purchase_order_id ON supplier_purchase_orders(purchase_order_id);
CREATE INDEX idx_po_status ON supplier_purchase_orders(status);
CREATE INDEX idx_delivery_date ON supplier_purchase_orders(delivery_date);

-- Create voice_queries_inventory_assistant table
CREATE TABLE IF NOT EXISTS voice_queries_inventory_assistant (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(20) UNIQUE NOT NULL,
    query_text TEXT,
    intent VARCHAR(100),
    entities JSONB,
    response_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for voice queries
CREATE INDEX idx_query_id ON voice_queries_inventory_assistant(query_id);
CREATE INDEX idx_intent ON voice_queries_inventory_assistant(intent);
CREATE INDEX idx_entities ON voice_queries_inventory_assistant USING GIN (entities);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_inventory_updated_at
    BEFORE UPDATE ON clothing_retail_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_logs_updated_at
    BEFORE UPDATE ON employee_task_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_purchase_orders_updated_at
    BEFORE UPDATE ON supplier_purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

