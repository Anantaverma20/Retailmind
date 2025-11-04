"""
Script to upload all CSV data to Supabase tables.
Run this after creating your Supabase project and running the migration.
"""

import sys
import os
import csv
from typing import List, Dict
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_client import get_supabase_client


def read_csv_file(file_path: str) -> List[Dict]:
    """Read CSV file and return list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def clean_empty_strings(data: Dict) -> Dict:
    """Convert empty strings to None for database."""
    cleaned = {}
    for key, value in data.items():
        if value == '':
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


def upload_inventory_data(supabase, batch_size: int = 500):
    """Upload clothing_retail_inventory.csv data."""
    print("\n[INVENTORY] Uploading clothing_retail_inventory...")
    
    file_path = "data/clothing_retail_inventory.csv"
    data = read_csv_file(file_path)
    
    print(f"   Found {len(data)} records")
    
    # Upload in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cleaned_batch = []
        
        for row in batch:
            cleaned_row = clean_empty_strings({
                'product_id': row['product_id'],
                'name': row['name'],
                'category': row['category'],
                'sub_category': row['sub_category'],
                'color': row['color'],
                'size': row['size'],
                'cost_price': float(row['cost_price']) if row['cost_price'] else None,
                'selling_price': float(row['selling_price']) if row['selling_price'] else None,
                'stock_quantity': int(row['stock_quantity']) if row['stock_quantity'] else 0,
                'reorder_threshold': int(row['reorder_threshold']) if row['reorder_threshold'] else 0,
                'supplier_id': row['supplier_id'],
                'last_restock_date': row['last_restock_date'],
                'location': row['location'],
                'barcode': row['barcode']
            })
            cleaned_batch.append(cleaned_row)
        
        try:
            supabase.table("clothing_retail_inventory").insert(cleaned_batch).execute()
            print(f"   [OK] Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   [ERROR] Error in batch {i//batch_size + 1}: {e}")
            return False
    
    print(f"   [SUCCESS] Uploaded {len(data)} inventory records!")
    return True


def upload_employee_tasks(supabase, batch_size: int = 500):
    """Upload employee_task_logs.csv data."""
    print("\n[TASKS] Uploading employee_task_logs...")
    
    file_path = "data/employee_task_logs.csv"
    data = read_csv_file(file_path)
    
    print(f"   Found {len(data)} records")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cleaned_batch = []
        
        for row in batch:
            cleaned_row = clean_empty_strings({
                'task_id': row['task_id'],
                'employee_name': row['employee_name'],
                'employee_role': row['employee_role'],
                'task_type': row['task_type'],
                'assigned_date': row['assigned_date'],
                'due_date': row['due_date'],
                'completion_date': row['completion_date'],
                'status': row['status'],
                'related_product': row['related_product']
            })
            cleaned_batch.append(cleaned_row)
        
        try:
            supabase.table("employee_task_logs").insert(cleaned_batch).execute()
            print(f"   [OK] Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   [ERROR] Error in batch {i//batch_size + 1}: {e}")
            return False
    
    print(f"   [SUCCESS] Uploaded {len(data)} task records!")
    return True


def upload_sales_transactions(supabase, batch_size: int = 500):
    """Upload retail_sales_transactions.csv data."""
    print("\n[SALES] Uploading retail_sales_transactions...")
    
    file_path = "data/retail_sales_transactions.csv"
    data = read_csv_file(file_path)
    
    print(f"   Found {len(data)} records")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cleaned_batch = []
        
        for row in batch:
            cleaned_row = clean_empty_strings({
                'sale_id': row['sale_id'],
                'product_id': row['product_id'],
                'quantity_sold': int(row['quantity_sold']) if row['quantity_sold'] else 0,
                'sale_date': row['sale_date'],
                'channel': row['channel'],
                'revenue': float(row['revenue']) if row['revenue'] else None,
                'payment_method': row['payment_method'],
                'customer_id': row['customer_id'],
                'discount_applied': row['discount_applied'].lower() == 'true' if row['discount_applied'] else False,
                'city': row['city']
            })
            cleaned_batch.append(cleaned_row)
        
        try:
            supabase.table("retail_sales_transactions").insert(cleaned_batch).execute()
            print(f"   [OK] Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   [ERROR] Error in batch {i//batch_size + 1}: {e}")
            return False
    
    print(f"   [SUCCESS] Uploaded {len(data)} sales records!")
    return True


def upload_supplier_orders(supabase, batch_size: int = 500):
    """Upload supplier_purchase_orders.csv data."""
    print("\n[SUPPLIERS] Uploading supplier_purchase_orders...")
    
    file_path = "data/supplier_purchase_orders.csv"
    data = read_csv_file(file_path)
    
    print(f"   Found {len(data)} records")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cleaned_batch = []
        
        for row in batch:
            cleaned_row = clean_empty_strings({
                'supplier_id': row['supplier_id'],
                'supplier_name': row['supplier_name'],
                'contact_name': row['contact_name'],
                'contact_email': row['contact_email'],
                'phone_number': row['phone_number'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'product_categories_supplied': row['product_categories_supplied'],
                'purchase_order_id': row['purchase_order_id'],
                'order_date': row['order_date'],
                'delivery_date': row['delivery_date'],
                'status': row['status'],
                'total_cost': float(row['total_cost']) if row['total_cost'] else None,
                'payment_status': row['payment_status']
            })
            cleaned_batch.append(cleaned_row)
        
        try:
            supabase.table("supplier_purchase_orders").insert(cleaned_batch).execute()
            print(f"   [OK] Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   [ERROR] Error in batch {i//batch_size + 1}: {e}")
            return False
    
    print(f"   [SUCCESS] Uploaded {len(data)} supplier/order records!")
    return True


def upload_voice_queries(supabase, batch_size: int = 500):
    """Upload voice_queries_inventory_assistant.csv data."""
    print("\n[VOICE QUERIES] Uploading voice_queries_inventory_assistant...")
    
    file_path = "data/voice_queries_inventory_assistant.csv"
    data = read_csv_file(file_path)
    
    print(f"   Found {len(data)} records")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cleaned_batch = []
        
        for row in batch:
            # Parse entities JSON
            entities = None
            if row['entities']:
                try:
                    # Replace single quotes with double quotes for valid JSON
                    entities_str = row['entities'].replace("'", '"')
                    entities = json.loads(entities_str)
                except:
                    entities = {}
            
            cleaned_row = clean_empty_strings({
                'query_id': row['query_id'],
                'query_text': row['query_text'],
                'intent': row['intent'],
                'entities': entities,
                'response_text': row['response_text']
            })
            cleaned_batch.append(cleaned_row)
        
        try:
            supabase.table("voice_queries_inventory_assistant").insert(cleaned_batch).execute()
            print(f"   [OK] Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
        except Exception as e:
            print(f"   [ERROR] Error in batch {i//batch_size + 1}: {e}")
            return False
    
    print(f"   [SUCCESS] Uploaded {len(data)} voice query records!")
    return True


def main():
    """Main upload function."""
    print("=" * 70)
    print("UPLOADING CSV DATA TO SUPABASE")
    print("=" * 70)
    
    # Check if .env is configured
    print("\nChecking configuration...")
    try:
        supabase = get_supabase_client()
        print("   [OK] Supabase client configured")
    except Exception as e:
        print(f"   [ERROR] {e}")
        print("\nMake sure you have:")
        print("   1. Created a Supabase project")
        print("   2. Run the migration SQL (001_create_inventory_tables.sql)")
        print("   3. Updated your .env file with SUPABASE_URL and SUPABASE_KEY")
        sys.exit(1)
    
    print("\nWARNING: This will upload ~50,000 rows to your Supabase database.")
    print("   Make sure you've already run the migration to create the tables!")
    
    # Check for --yes flag to skip confirmation
    if '--yes' not in sys.argv:
        response = input("\n   Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("   [CANCELLED] Upload cancelled")
            sys.exit(0)
    
    print("\nStarting upload...")
    
    # Upload each dataset
    success = True
    success &= upload_inventory_data(supabase)
    success &= upload_employee_tasks(supabase)
    success &= upload_sales_transactions(supabase)
    success &= upload_supplier_orders(supabase)
    success &= upload_voice_queries(supabase)
    
    if success:
        print("\n" + "=" * 70)
        print("ALL DATA UPLOADED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("   1. Run: python scripts/test_supabase_connection.py")
        print("   2. Check your Supabase dashboard to see the data")
        print("   3. Start building your inventory assistant features!")
    else:
        print("\n" + "=" * 70)
        print("UPLOAD COMPLETED WITH ERRORS")
        print("=" * 70)
        print("\nCheck the error messages above and try again")


if __name__ == "__main__":
    main()

