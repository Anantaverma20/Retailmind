"""Data validation script for Supabase tables."""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    sys.exit(1)


def validate_table(supabase, table_name: str, key_columns: list = None):
    """Validate a table: count rows, check for nulls in key columns."""
    print(f"\n=== Validating {table_name} ===")
    
    try:
        # Get row count
        response = supabase.table(table_name).select("id", count="exact").limit(1).execute()
        row_count = response.count if hasattr(response, 'count') else len(response.data)
        print(f"Row count: {row_count}")
        
        if row_count == 0:
            print(f"WARNING: {table_name} is empty")
            return False
        
        # Check for nulls in key columns
        if key_columns:
            for col in key_columns:
                response = supabase.table(table_name).select("id").is_(col, "null").limit(10).execute()
                null_count = len(response.data)
                if null_count > 0:
                    print(f"WARNING: Found {null_count} rows with null in column '{col}'")
        
        # Sample a few rows
        sample = supabase.table(table_name).select("*").limit(3).execute()
        if sample.data:
            print(f"Sample row keys: {list(sample.data[0].keys())}")
        
        return True
    
    except Exception as e:
        print(f"ERROR validating {table_name}: {e}")
        return False


def validate_relationships(supabase):
    """Validate referential integrity (e.g., orphan product_id in sales)."""
    print("\n=== Validating Relationships ===")
    
    try:
        # Check for orphan product_id in sales
        sales_resp = supabase.table("sales").select("product_id").limit(1000).execute()
        if sales_resp.data:
            product_ids = {row["product_id"] for row in sales_resp.data if row.get("product_id")}
            
            if product_ids:
                # Check if all product_ids exist in products table
                products_resp = supabase.table("products").select("id").in_("id", list(product_ids)).execute()
                existing_ids = {row["id"] for row in products_resp.data}
                
                orphan_ids = product_ids - existing_ids
                if orphan_ids:
                    print(f"WARNING: Found {len(orphan_ids)} orphan product_ids in sales table")
                else:
                    print("✓ All product_ids in sales exist in products table")
        
        # Check for orphan supplier_id in products
        products_resp = supabase.table("products").select("supplier_id").not_.is_("supplier_id", "null").limit(1000).execute()
        if products_resp.data:
            supplier_ids = {row["supplier_id"] for row in products_resp.data if row.get("supplier_id")}
            
            if supplier_ids:
                suppliers_resp = supabase.table("suppliers").select("id").in_("id", list(supplier_ids)).execute()
                existing_ids = {row["id"] for row in suppliers_resp.data}
                
                orphan_ids = supplier_ids - existing_ids
                if orphan_ids:
                    print(f"WARNING: Found {len(orphan_ids)} orphan supplier_ids in products table")
                else:
                    print("✓ All supplier_ids in products exist in suppliers table")
        
        # Check for orphan product_id in reorders
        reorders_resp = supabase.table("reorders").select("product_id").limit(1000).execute()
        if reorders_resp.data:
            product_ids = {row["product_id"] for row in reorders_resp.data if row.get("product_id")}
            
            if product_ids:
                products_resp = supabase.table("products").select("id").in_("id", list(product_ids)).execute()
                existing_ids = {row["id"] for row in products_resp.data}
                
                orphan_ids = product_ids - existing_ids
                if orphan_ids:
                    print(f"WARNING: Found {len(orphan_ids)} orphan product_ids in reorders table")
                else:
                    print("✓ All product_ids in reorders exist in products table")
        
    except Exception as e:
        print(f"ERROR validating relationships: {e}")


def main():
    """Run data validation."""
    print("Starting data validation...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Validate each table
    tables_valid = True
    tables_valid &= validate_table(supabase, "products", key_columns=["name", "sku"])
    tables_valid &= validate_table(supabase, "sales", key_columns=["product_id", "sale_date"])
    tables_valid &= validate_table(supabase, "suppliers", key_columns=["name"])
    tables_valid &= validate_table(supabase, "reorders", key_columns=["product_id"])
    
    # Validate relationships
    validate_relationships(supabase)
    
    print("\n=== Validation Summary ===")
    if tables_valid:
        print("✓ All tables validated successfully")
    else:
        print("✗ Some tables have issues")
        sys.exit(1)


if __name__ == "__main__":
    main()

