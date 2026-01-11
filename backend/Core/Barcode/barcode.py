import requests
import re


def make_api_call(barcode: str):
    """Fetch product data from OpenFoodFacts API"""
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None


def extract_nutrients(product_data):
    """
    Extract tracked nutrients from OpenFoodFacts product data.
    Returns values per serving when available, otherwise per 100g.
    """
    if not product_data or product_data.get('status') != 1:
        return None

    product = product_data.get('product', {})
    nutriments = product.get('nutriments', {})

    if not nutriments:
        return None

    # Get serving info
    serving_qty = product.get('serving_quantity')
    serving_size = product.get('serving_size', '')

    # Parse serving quantity if it's a string
    if isinstance(serving_qty, str):
        match = re.search(r'(\d+\.?\d*)', serving_qty)
        serving_qty = float(match.group(1)) if match else None

    # Nutrient extraction rules
    # Format: nutrient_name: ([list of possible API keys], target_unit, conversion_factor)
    nutrient_rules = {
        'protein': {
            'keys': ['proteins_100g', 'protein_100g', 'proteins', 'protein'],
            'unit': 'g',
            'conversions': {}
        },
        'fiber': {
            'keys': ['fiber_100g', 'fibers_100g', 'fiber', 'fibers'],
            'unit': 'g',
            'conversions': {}
        },
        'iron': {
            'keys': ['iron_100g', 'iron'],
            'unit': 'g',
            'conversions': {
                'mg': 0.001,
                'mcg': 0.000001,
                'µg': 0.000001
            }
        },
        'vitamin_d': {
            'keys': ['vitamin-d_100g', 'vitamin_d_100g', 'vitamin-d', 'vitamin_d'],
            'unit': 'mcg',
            'conversions': {
                'µg': 1.0,
                'mg': 1000.0,
                'g': 1000000.0
            }
        },
        'omega_3': {
            'keys': ['omega-3-fat_100g', 'omega-3_100g', 'alpha-linolenic-acid_100g', 'omega_3_100g'],
            'unit': 'g',
            'conversions': {}
        },
        'omega_3_epa': {
            'keys': ['eicosapentaenoic-acid_100g', 'epa_100g', 'epa'],
            'unit': 'g',
            'conversions': {}
        },
        'omega_3_dha': {
            'keys': ['docosahexaenoic-acid_100g', 'dha_100g', 'dha'],
            'unit': 'g',
            'conversions': {}
        }
    }

    results = {}

    for nutrient_name, rules in nutrient_rules.items():
        value = None
        source_key = None

        # Find the first available key
        for key in rules['keys']:
            if key in nutriments and nutriments[key] is not None:
                value = float(nutriments[key])
                source_key = key
                break

        # If no value found, default to 0
        if value is None:
            results[nutrient_name] = {
                'per_100g': 0.0,
                'per_serving': 0.0 if serving_qty else None,
                'unit': rules['unit']
            }
            continue

        # Get the unit from API (if available)
        unit_key = source_key.replace('_100g', '_unit').replace('s_', '_')
        api_unit = nutriments.get(unit_key, '').lower()

        # Apply unit conversion if needed
        if api_unit in rules['conversions']:
            value = value * rules['conversions'][api_unit]

        # Calculate per serving if serving quantity is available
        per_serving = None
        if serving_qty:
            per_serving = round((value / 100) * serving_qty, 4)

        results[nutrient_name] = {
            'per_100g': round(value, 4),
            'per_serving': per_serving,
            'unit': rules['unit']
        }

    # Build final result
    output = {
        'product_name': product.get('product_name', 'Unknown'),
        'brand': product.get('brands', ''),
        'barcode': product.get('code', ''),
        'serving_size': serving_size,
        'serving_quantity_g': serving_qty,
        'nutrients': results
    }

    return output


def get_nutrients(barcode: str, per_serving: bool = True):
    """
    Main function to get nutrients from a barcode.

    Args:
        barcode: Product barcode
        per_serving: If True, return per-serving values (when available),
                     otherwise return per 100g values

    Returns:
        Dict with nutrient information or None if not found
    """
    data = make_api_call(barcode)
    nutrients_data = extract_nutrients(data)

    if not nutrients_data:
        return None

    # Simplify output based on preference
    if per_serving and nutrients_data['serving_quantity_g']:
        # Return per-serving values
        simple_nutrients = {}
        for name, data in nutrients_data['nutrients'].items():
            if data['per_serving'] is not None:
                simple_nutrients[name] = {
                    'value': data['per_serving'],
                    'unit': data['unit']
                }

        return {
            'product_name': nutrients_data['product_name'],
            'brand': nutrients_data['brand'],
            'serving_size': nutrients_data['serving_size'],
            'nutrients': simple_nutrients
        } if simple_nutrients else None
    else:
        # Return per 100g values
        simple_nutrients = {}
        for name, data in nutrients_data['nutrients'].items():
            simple_nutrients[name] = {
                'value': data['per_100g'],
                'unit': data['unit']
            }

        return {
            'product_name': nutrients_data['product_name'],
            'brand': nutrients_data['brand'],
            'per': '100g',
            'nutrients': simple_nutrients
        } if simple_nutrients else None


# Example usage
if __name__ == "__main__":
    barcode = "8901491981699"

    # Get per-serving nutrients
    print("Per Serving:")
    result = get_nutrients(barcode, per_serving=True)
    if result:
        print(f"Product: {result['product_name']}")
        print(f"Brand: {result['brand']}")
        print(f"Serving: {result.get('serving_size', 'N/A')}")
        print("\nNutrients:")
        for nutrient, data in result['nutrients'].items():
            print(f"  {nutrient}: {data['value']} {data['unit']}")

    print("\n" + "=" * 50 + "\n")

    # Get per 100g nutrients
    print("Per 100g:")
    result_100g = get_nutrients(barcode, per_serving=False)
    if result_100g:
        print(f"Product: {result_100g['product_name']}")
        print("\nNutrients:")
        for nutrient, data in result_100g['nutrients'].items():
            print(f"  {nutrient}: {data['value']} {data['unit']}")