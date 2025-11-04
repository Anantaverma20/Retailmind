"""Multilingual speech generator for OMI responses."""
from typing import Dict, Any, Optional


# Translation dictionaries for common phrases
TRANSLATIONS = {
    "en": {
        "error_generic": "I'm sorry, something went wrong while processing your request.",
        "error_parse": "I'm sorry, I couldn't understand your request. Please try again.",
        "error_unknown_intent": "I'm sorry, I don't know how to handle that type of request.",
        "error_not_found": "I couldn't find that product.",
        "error_reorder": "I couldn't create that reorder.",
        "error_sales": "I couldn't retrieve sales data.",
        "error_supplier": "I couldn't find supplier information.",
        "error_delivery": "I couldn't find delivery information.",
        "no_products": "No products found matching your criteria.",
        "low_stock_warning": "This product is running low and needs restocking.",
        "stock_prefix": "There are",
        "stock_suffix": "in stock.",
        "stock_color_prefix": "in",
        "stock_size_prefix": "size",
        "stock_multiple": "Found {count} matching products with a total quantity of {total}.",
        "reorder_success": "Created reorder {reorder_id} for {quantity} {product_name}. Status: {status}",
        "sales_prefix": "In the last {days} days,",
        "sales_sold": "you sold {quantity} items",
        "sales_revenue": "with total revenue of ${revenue:.2f}",
        "supplier_info": "The supplier is {name} with a lead time of {days} days.",
        "delivery_status": "Order status is {status}.",
        "delivery_eta": "Expected delivery date is {eta}.",
        "request_success": "Request processed successfully.",
    },
    "es": {
        "error_generic": "Lo siento, algo salió mal al procesar tu solicitud.",
        "error_parse": "Lo siento, no pude entender tu solicitud. Por favor, inténtalo de nuevo.",
        "error_unknown_intent": "Lo siento, no sé cómo manejar ese tipo de solicitud.",
        "error_not_found": "No pude encontrar ese producto.",
        "error_reorder": "No pude crear esa reorden.",
        "error_sales": "No pude recuperar los datos de ventas.",
        "error_supplier": "No pude encontrar información del proveedor.",
        "error_delivery": "No pude encontrar información de entrega.",
        "no_products": "No se encontraron productos que coincidan con tus criterios.",
        "low_stock_warning": "Este producto se está agotando y necesita reabastecimiento.",
        "stock_prefix": "Hay",
        "stock_suffix": "en stock.",
        "stock_color_prefix": "en",
        "stock_size_prefix": "talla",
        "stock_multiple": "Se encontraron {count} productos que coinciden con una cantidad total de {total}.",
        "reorder_success": "Reorden {reorder_id} creada para {quantity} {product_name}. Estado: {status}",
        "sales_prefix": "En los últimos {days} días,",
        "sales_sold": "vendiste {quantity} artículos",
        "sales_revenue": "con un ingreso total de ${revenue:.2f}",
        "supplier_info": "El proveedor es {name} con un tiempo de entrega de {days} días.",
        "delivery_status": "El estado del pedido es {status}.",
        "delivery_eta": "La fecha de entrega esperada es {eta}.",
        "request_success": "Solicitud procesada exitosamente.",
    },
}


def get_translation(language: str, key: str, **kwargs) -> str:
    """Get translated text for a given key."""
    lang = language.lower() if language else "en"
    if lang not in TRANSLATIONS:
        lang = "en"
    
    template = TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))
    
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def generate_speech(intent: str, result: Dict[str, Any], language: str = "en") -> str:
    """
    Generate human-like speech text from intent and result.
    
    Args:
        intent: The intent name
        result: The result dictionary from the handler
        language: Language code (en, es)
        
    Returns:
        Speech text in the requested language
    """
    lang = language.lower() if language else "en"
    
    if intent == "get_stock":
        if "error" in result:
            return get_translation(lang, "error_not_found")
        
        items = result.get("items", [])
        if not items:
            return get_translation(lang, "no_products")
        
        if len(items) == 1:
            item = items[0]
            name = item.get("name", "item")
            quantity = item.get("quantity", 0)
            low_stock = item.get("low_stock", False)
            
            # Build speech
            speech_parts = [
                get_translation(lang, "stock_prefix"),
                str(quantity),
                name + ("s" if lang == "en" else ""),  # Simple pluralization
            ]
            
            if item.get("color"):
                speech_parts.append(get_translation(lang, "stock_color_prefix"))
                speech_parts.append(item["color"])
            
            if item.get("size"):
                speech_parts.append(get_translation(lang, "stock_size_prefix"))
                speech_parts.append(item["size"])
            
            speech_parts.append(get_translation(lang, "stock_suffix"))
            speech = " ".join(speech_parts)
            
            if low_stock:
                speech += " " + get_translation(lang, "low_stock_warning")
            
            return speech
        
        total = sum(i.get("quantity", 0) for i in items)
        return get_translation(lang, "stock_multiple", count=len(items), total=total)
    
    elif intent == "create_reorder":
        if "error" in result:
            error_msg = result.get("error_message", "")
            if error_msg:
                # Try to translate common error messages
                if "not found" in error_msg.lower():
                    return get_translation(lang, "error_not_found")
                return f"{get_translation(lang, 'error_reorder')}: {error_msg}"
            return get_translation(lang, "error_reorder")
        
        reorder_id = result.get("reorder_id", "order")
        quantity = result.get("quantity", 0)
        product_name = result.get("product_name", "items" if lang == "en" else "artículos")
        status = result.get("status", "pending")
        
        return get_translation(
            lang, "reorder_success",
            reorder_id=reorder_id,
            quantity=quantity,
            product_name=product_name,
            status=status
        )
    
    elif intent == "get_sales_summary":
        if "error" in result:
            return get_translation(lang, "error_sales")
        
        total_qty = result.get("total_quantity", 0)
        total_revenue = result.get("total_revenue", 0)
        window_days = result.get("window_days", 7)
        
        parts = [
            get_translation(lang, "sales_prefix", days=window_days),
            get_translation(lang, "sales_sold", quantity=total_qty),
            get_translation(lang, "sales_revenue", revenue=total_revenue),
        ]
        
        return " ".join(parts)
    
    elif intent == "get_supplier_info":
        if "error" in result:
            return get_translation(lang, "error_supplier")
        
        supplier_name = result.get("supplier_name", "supplier" if lang == "en" else "proveedor")
        lead_time = result.get("lead_time_days", 0)
        
        return get_translation(
            lang, "supplier_info",
            name=supplier_name,
            days=lead_time
        )
    
    elif intent == "get_delivery_status":
        if "error" in result:
            return get_translation(lang, "error_delivery")
        
        status = result.get("status", "unknown")
        eta = result.get("eta")
        
        speech = get_translation(lang, "delivery_status", status=status)
        if eta:
            speech += " " + get_translation(lang, "delivery_eta", eta=eta)
        
        return speech
    
    return get_translation(lang, "request_success")

