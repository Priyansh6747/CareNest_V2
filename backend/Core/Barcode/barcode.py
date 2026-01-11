import requests

def make_api_call(HRI: str):
    # Build the API endpoint using the product code / barcode
    url = f"https://world.openfoodfacts.org/api/v2/product/{HRI}.json"
    
    # Send GET request to OpenFoodFacts API
    response = requests.get(url)
    
    # If API fails (network issues, invalid URL, etc.), return None
    if response.status_code != 200:
        return None
    
    # Raise exception for 4xx / 5xx, if any
    response.raise_for_status()
    
    # Return full JSON data
    return response.json()

# def extract_tracked_nutrients(product_data):
#     """
#     Extract tracked nutrients from product data.
    
#     Args:
#         product_data: The result from read_barcode() function
    
#     Returns:
#         dict: Dictionary containing the tracked nutrients with their values and units
#               Returns None if no product data or no nutriments found
#     """
#     if not product_data:
#         return None
    
#     # Get the product dictionary
#     product = product_data.get('product', {})
#     if not product:
#         return None
    
#     # Get nutriments section
#     nutriments = product.get('nutriments', {})
#     if not nutriments:
#         return None
    
#     # Tracked nutrients with their keys in the API response
#     # We need to check for different possible key formats
#     tracked_nutrients = {
#         'protein': {
#             'keys': ['protein', 'protein_100g', 'protein_value', 'protein_serving'],
#             'unit': 'g'
#         },
#         'fiber': {
#             'keys': ['fiber', 'fiber_100g', 'fiber_value', 'fiber_serving'],
#             'unit': 'g'
#         },
#         'iron': {
#             'keys': ['iron', 'iron_100g', 'iron_value', 'iron_serving', 
#                     'iron_100g', 'iron_prepared_100g'],
#             'unit': 'g'  # Note: Sometimes iron might be in mg, check unit separately
#         },
#         'vitamin_d': {
#             'keys': ['vitamin-d', 'vitamin_d', 'vitamin-d_100g', 'vitamin_d_100g',
#                     'vitamin-d_value', 'vitamin_d_value'],
#             'unit': 'mcg'
#         },
#         'omega_3': {
#             'keys': ['omega-3', 'omega_3', 'omega-3_100g', 'omega_3_100g',
#                     'alpha-linolenic-acid_100g', 'alpha_linolenic_acid_100g'],
#             'unit': 'g'
#         },
#         'omega_3_epa': {
#             'keys': ['epa', 'epa_100g', 'eicosapentaenoic-acid_100g'],
#             'unit': 'g'
#         },
#         'omega_3_dha': {
#             'keys': ['dha', 'dha_100g', 'docosahexaenoic-acid_100g'],
#             'unit': 'g'
#         }
#     }
    
#     result = {}
    
#     for nutrient_name, nutrient_info in tracked_nutrients.items():
#         value = None
        
#         # Try each possible key
#         for key in nutrient_info['keys']:
#             if key in nutriments:
#                 value = nutriments[key]
#                 break
        
#         # If we found a value, add it to results
#         if value is not None:
#             # For iron, check if it's in mg and convert to g if needed
#             if nutrient_name == 'iron':
#                 # Check unit
#                 iron_unit = nutriments.get('iron_unit', 'g')
#                 if iron_unit == 'mg':
#                     value = value / 1000  # Convert mg to g
            
#             result[nutrient_name] = {
#                 'value': value,
#                 'unit': nutrient_info['unit']
#             }
    
#     return result if result else None

def extract_tracked_nutrients(product_data):
    """
    Extract tracked nutrients from product data with proper unit handling.
    
    Args:
        product_data: The result from read_barcode() function
    
    Returns:
        dict: Dictionary containing the tracked nutrients with their values and units
    """
    if not product_data:
        return None
    
    product = product_data.get('product', {})
    if not product:
        return None
    
    nutriments = product.get('nutriments', {})
    if not nutriments:
        return None
    
    # Define the nutrients we want to track with their expected units
    tracked_nutrients = {
        'protein': {
            'keys': ['protein_100g', 'protein_value', 'protein', 'proteins_100g'],
            'target_unit': 'g',
            'api_unit_key': 'protein_unit'
        },
        'fiber': {
            'keys': ['fiber_100g', 'fiber_value', 'fiber', 'fibers_100g'],
            'target_unit': 'g',
            'api_unit_key': 'fiber_unit'
        },
        'iron': {
            'keys': ['iron_100g', 'iron_value', 'iron'],
            'target_unit': 'g',  # We want grams output
            'api_unit_key': 'iron_unit',
            'conversions': {
                'mg': lambda x: x / 1000,  # mg to g
                'mcg': lambda x: x / 1000000,  # mcg to g
                'µg': lambda x: x / 1000000  # µg to g
            }
        },
        'vitamin_d': {
            'keys': ['vitamin-d_100g', 'vitamin_d_100g', 'vitamin-d_value', 'vitamin_d_value'],
            'target_unit': 'mcg',
            'api_unit_key': 'vitamin-d_unit',
            'conversions': {
                'µg': lambda x: x,  # µg is the same as mcg
                'mg': lambda x: x * 1000  # mg to mcg
            }
        },
        'omega_3': {
            'keys': ['omega-3-fat_100g', 'omega-3_100g', 'omega_3_100g', 'alpha-linolenic-acid_100g'],
            'target_unit': 'g',
            'api_unit_key': 'omega-3-fat_unit'
        },
        'omega_3_epa': {
            'keys': ['epa_100g', 'eicosapentaenoic-acid_100g'],
            'target_unit': 'g',
            'api_unit_key': 'epa_unit'
        },
        'omega_3_dha': {
            'keys': ['dha_100g', 'docosahexaenoic-acid_100g'],
            'target_unit': 'g',
            'api_unit_key': 'dha_unit'
        }
    }
    
    result = {}
    
    for nutrient_name, nutrient_info in tracked_nutrients.items():
        value = None
        found_key = None
        
        # Try each possible key
        for key in nutrient_info['keys']:
            if key in nutriments:
                value = nutriments[key]
                found_key = key
                break
        
        if value is not None:
            # Get the unit from the API
            api_unit = nutriments.get(nutrient_info['api_unit_key'], '')
            
            # Apply unit conversion if needed
            if 'conversions' in nutrient_info and api_unit in nutrient_info['conversions']:
                value = nutrient_info['conversions'][api_unit](value)
            
            result[nutrient_name] = {
                'value': round(float(value), 4),  # Round to 4 decimal places
                'unit': nutrient_info['target_unit'],
                'source_unit': api_unit if api_unit else 'unknown',
                'source_key': found_key
            }
    
    return result if result else None

def extract_tracked_nutrients_per_serving(product_data):
    """
    Extract tracked nutrients per serving from product data.
    More accurate version that handles unit conversions properly.
    
    Args:
        product_data: The result from read_barcode() function
    
    Returns:
        dict: Dictionary containing the tracked nutrients per serving
    """
    if not product_data:
        return None
    
    product = product_data.get('product', {})
    if not product:
        return None
    
    nutriments = product.get('nutriments', {})
    if not nutriments:
        return None
    
    # First get the per 100g values with proper unit handling
    per_100g_nutrients = {}
    
    nutrient_configs = {
        'protein': {
            'keys': ['protein_100g', 'protein_value', 'protein'],
            'unit_key': 'protein_unit'
        },
        'fiber': {
            'keys': ['fiber_100g', 'fiber_value', 'fiber'],
            'unit_key': 'fiber_unit'
        },
        'iron': {
            'keys': ['iron_100g', 'iron_value', 'iron'],
            'unit_key': 'iron_unit',
            'conversions': {
                'mg': lambda x: x / 1000,
                'mcg': lambda x: x / 1000000,
                'µg': lambda x: x / 1000000
            }
        },
        'vitamin_d': {
            'keys': ['vitamin-d_100g', 'vitamin_d_100g', 'vitamin-d_value'],
            'unit_key': 'vitamin-d_unit'
        },
        'omega_3': {
            'keys': ['omega-3-fat_100g', 'omega-3_100g', 'alpha-linolenic-acid_100g'],
            'unit_key': 'omega-3-fat_unit'
        },
        'omega_3_epa': {
            'keys': ['epa_100g', 'eicosapentaenoic-acid_100g'],
            'unit_key': 'epa_unit'
        },
        'omega_3_dha': {
            'keys': ['dha_100g', 'docosahexaenoic-acid_100g'],
            'unit_key': 'dha_unit'
        }
    }
    
    # First, extract all per 100g values
    for nutrient_name, config in nutrient_configs.items():
        value = None
        
        for key in config['keys']:
            if key in nutriments:
                value = nutriments[key]
                break
        
        if value is not None:
            # Get unit and apply conversions
            unit = nutriments.get(config['unit_key'], '')
            if 'conversions' in config and unit in config['conversions']:
                value = config['conversions'][unit](value)
                per_100g_nutrients[nutrient_name] = {
                    'value_per_100g': value,
                    'unit': 'g' if nutrient_name != 'vitamin_d' else 'mcg'
                }
            else:
                per_100g_nutrients[nutrient_name] = {
                    'value_per_100g': value,
                    'unit': unit if unit else 'g'
                }
    
    # Now calculate per serving
    result = {}
    serving_quantity = product.get('serving_quantity')
    serving_size = product.get('serving_size', '')
    
    if serving_quantity and per_100g_nutrients:
        # Try to parse serving quantity if it's a string
        if isinstance(serving_quantity, str):
            try:
                # Extract numeric part from string like "56 g"
                import re
                match = re.search(r'(\d+\.?\d*)', serving_quantity)
                if match:
                    serving_quantity = float(match.group(1))
            except:
                serving_quantity = None
        
        if serving_quantity:
            for nutrient_name, nutrient_data in per_100g_nutrients.items():
                # Calculate per serving: (value_per_100g / 100) * serving_quantity
                value_per_serving = (nutrient_data['value_per_100g'] / 100) * serving_quantity
                
                # Format based on magnitude
                if abs(value_per_serving) < 0.001:
                    formatted_value = round(value_per_serving, 6)
                elif abs(value_per_serving) < 0.01:
                    formatted_value = round(value_per_serving, 4)
                else:
                    formatted_value = round(value_per_serving, 2)
                
                result[nutrient_name] = {
                    'value': formatted_value,
                    'unit': nutrient_data['unit'],
                    'serving_quantity': serving_quantity,
                    'serving_size': serving_size
                }
    
    return result if result else None

def extract_product_info(json1):
    # Extract the 'product' block from API response
    product = json1.get('product', {})

    # Create a simplified product dictionary with selected fields
    simplified_product = {
        '_id': product.get('_id'),
        '_keywords': product.get('_keywords', []),
        'added_countries_tags': product.get('added_countries_tags', []),
        'allergens': product.get('allergens', ''),
        'allergens_from_ingredients': product.get('allergens_from_ingredients', ''),
        'brands': product.get('brands'),
        'brands_tags': product.get('brands_tags', []),
        'categories_properties': product.get('categories_properties', {}),
        'categories_properties_tags': product.get('categories_properties_tags', []),
        'checkers_tags': product.get('checkers_tags', []),
        'code': product.get('code'),
        'codes_tags': product.get('codes_tags', []),
        'complete': product.get('complete'),
        'completeness': product.get('completeness'),
        'correctors_tags': product.get('correctors_tags', []),
        'countries': product.get('countries'),
        'countries_hierarchy': product.get('countries_hierarchy', []),
        'countries_tags': product.get('countries_tags', []),
        'created_t': product.get('created_t'),
        'food_groups_tags': product.get('food_groups_tags', []),
        'id': product.get('id'),
        'image_front_small_url': product.get('image_front_small_url'),
        'image_front_thumb_url': product.get('image_front_thumb_url'),
        'image_front_url': product.get('image_front_url'),
        'image_small_url': product.get('image_small_url'),
        'image_thumb_url': product.get('image_thumb_url'),
        'image_url': product.get('image_url'),
        'images': product.get('images', {}),
        'informers_tags': product.get('informers_tags', []),
        'interface_version_created': product.get('interface_version_created'),
        'interface_version_modified': product.get('interface_version_modified'),
        'lang': product.get('lang'),
        'languages': product.get('languages', {}),
        'languages_codes': product.get('languages_codes', {}),
        'languages_hierarchy': product.get('languages_hierarchy', []),
        'languages_tags': product.get('languages_tags', []),
        'last_edit_dates_tags': product.get('last_edit_dates_tags', []),
        'last_editor': product.get('last_editor'),
        'last_image_dates_tags': product.get('last_image_dates_tags', []),
        'nova_group_debug': product.get('nova_group_debug'),
        'nova_group_error': product.get('nova_group_error'),
        'nova_groups_tags': product.get('nova_groups_tags', []),
        'nutrient_levels': product.get('nutrient_levels', {}),
        'nutrient_levels_tags': product.get('nutrient_levels_tags', []),
        'nutriments': product.get('nutriments', {}),
        'nutriscore': product.get('nutriscore', {}),
        'nutriscore_2021_tags': product.get('nutriscore_2021_tags', []),
        'nutriscore_2023_tags': product.get('nutriscore_2023_tags', []),
        'nutriscore_grade': product.get('nutriscore_grade'),
        'nutriscore_tags': product.get('nutriscore_tags', []),
        'nutriscore_version': product.get('nutriscore_version'),
        'nutrition_data': product.get('nutrition_data'),
        'nutrition_data_per': product.get('nutrition_data_per'),
        'nutrition_data_prepared_per': product.get('nutrition_data_prepared_per'),
        'nutrition_grade_fr': product.get('nutrition_grade_fr'),
        'nutrition_grades': product.get('nutrition_grades'),
        'nutrition_grades_tags': product.get('nutrition_grades_tags', []),
        'nutrition_score_beverage': product.get('nutrition_score_beverage'),
        'nutrition_score_debug': product.get('nutrition_score_debug'),
        'nutrition_score_warning_no_fiber': product.get('nutrition_score_warning_no_fiber'),
        'nutrition_score_warning_no_fruits_vegetables_nuts': product.get(
            'nutrition_score_warning_no_fruits_vegetables_nuts'),
        'packaging_materials_tags': product.get('packaging_materials_tags', []),
        'packaging_recycling_tags': product.get('packaging_recycling_tags', []),
        'packaging_shapes_tags': product.get('packaging_shapes_tags', []),
        'packagings': product.get('packagings', []),
        'packagings_materials': product.get('packagings_materials', {}),
        'photographers_tags': product.get('photographers_tags', []),
        'pnns_groups_1': product.get('pnns_groups_1'),
        'pnns_groups_1_tags': product.get('pnns_groups_1_tags', []),
        'pnns_groups_2': product.get('pnns_groups_2'),
        'pnns_groups_2_tags': product.get('pnns_groups_2_tags', []),
        'product_name': product.get('product_name'),
        'product_name_en': product.get('product_name_en'),
        'product_type': product.get('product_type'),
        'removed_countries_tags': product.get('removed_countries_tags', []),
        'rev': product.get('rev'),
        'scans_n': product.get('scans_n'),
        'schema_version': product.get('schema_version'),
        'selected_images': product.get('selected_images', {}),
    }

    # Extra fields: only add if present to avoid clutter
    if 'serving_quantity' in product:
        simplified_product['serving_quantity'] = product['serving_quantity']
    if 'serving_size' in product:
        simplified_product['serving_size'] = product['serving_size']

    # Remove all entries where value is None to keep output clean
    simplified_product = {k: v for k, v in simplified_product.items() if v is not None}

    # Final response structure expected by your app
    result = {
        'code': json1.get('code'),
        'product': simplified_product,
        'status': json1.get('status'),
        'status_verbose': json1.get('status_verbose')
    }

    return result


def read_barcode(barcode: str):
    # Call the API wrapper function to fetch product details
    data = make_api_call(barcode)

    # If no data OR product not found (status == 0), return None
    if data is None or data.get("status") == 0:
        return None

    # Extract and return simplified product information
    return extract_product_info(data)
# Example usage:
# barcode_info = read_barcode("737628064502")
# print(barcode_info)

def get_barcode_nutrients(barcode: str):
    """
    Complete function to scan barcode and return tracked nutrients.
    
    Args:
        barcode (str): The barcode to scan
    
    Returns:
        dict: Tracked nutrients or None if product not found
    """
    # Get product data
    product_data = read_barcode(barcode)
    
    if not product_data:
        return None
    
    # Extract nutrients
    nutrients = extract_tracked_nutrients(product_data)
    
    # Add product name for reference
    if nutrients:
        product_name = product_data.get('product', {}).get('product_name', 'Unknown Product')
        return {
            'product_name': product_name,
            'barcode': barcode,
            'nutrients': nutrients
        }
    
    return None

def get_tracked_nutrients_simple(barcode: str):
    """
    Simple function to get just the tracked nutrients per serving.
    
    Args:
        barcode (str): The barcode to scan
    
    Returns:
        dict: Simple dictionary with nutrient names and values per serving
    """
    product_data = read_barcode(barcode)
    
    if not product_data:
        return None
    
    # Try to get per-serving nutrients first
    nutrients = extract_tracked_nutrients_per_serving(product_data)
    
    # If no per-serving data, fall back to per 100g
    if not nutrients:
        nutrients_100g = extract_tracked_nutrients(product_data)
        if nutrients_100g:
            nutrients = {}
            for name, data in nutrients_100g.items():
                nutrients[name] = {
                    'value': data['value'],
                    'unit': data['unit'],
                    'note': 'per 100g (serving data not available)'
                }
    
    if not nutrients:
        return None
    
    # Create simplified output
    product = product_data.get('product', {})
    return {
        'product_name': product.get('product_name', 'Unknown Product'),
        'barcode': barcode,
        'nutrients': nutrients
    }

def get_comprehensive_nutrient_report(barcode: str):
    """
    Get a comprehensive nutrient report for a barcode.
    
    Args:
        barcode (str): The barcode to scan
    
    Returns:
        dict: Complete nutrient information including both per 100g and per serving
    """
    product_data = read_barcode(barcode)
    
    if not product_data:
        return None
    
    product = product_data.get('product', {})
    
    # Get all nutrients per 100g
    nutrients_100g = extract_tracked_nutrients(product_data)
    
    # Get nutrients per serving
    nutrients_serving = extract_tracked_nutrients_per_serving(product_data)
    
    # Prepare comprehensive report
    report = {
        'product_name': product.get('product_name', 'Unknown Product'),
        'product_name_en': product.get('product_name_en', ''),
        'barcode': barcode,
        'brands': product.get('brands', ''),
        'serving_info': {
            'serving_quantity': product.get('serving_quantity'),
            'serving_size': product.get('serving_size'),
            'nutrition_data_per': product.get('nutrition_data_per', '100g')
        }
    }
    
    if nutrients_100g:
        report['nutrients_per_100g'] = nutrients_100g
    
    if nutrients_serving:
        report['nutrients_per_serving'] = nutrients_serving
    
    # Calculate which nutrients are missing
    all_nutrients = ['protein', 'fiber', 'iron', 'vitamin_d', 'omega_3', 'omega_3_epa', 'omega_3_dha']
    found_nutrients = list(nutrients_100g.keys()) if nutrients_100g else []
    missing_nutrients = [n for n in all_nutrients if n not in found_nutrients]
    
    if missing_nutrients:
        report['missing_nutrients'] = missing_nutrients
    
    return report


# Alternatively, a more specific version that gets per serving values:
def extract_tracked_nutrients_per_serving(product_data):
    """
    Extract tracked nutrients per serving from product data.
    Tries to get per-serving values first, falls back to per 100g values.
    
    Args:
        product_data: The result from read_barcode() function
    
    Returns:
        dict: Dictionary containing the tracked nutrients per serving
    """
    if not product_data:
        return None
    
    product = product_data.get('product', {})
    if not product:
        return None
    
    nutriments = product.get('nutriments', {})
    if not nutriments:
        return None
    
    # Mapping of nutrient names to their per-serving and per-100g keys
    nutrient_mapping = {
        'protein': {'serving': 'protein_serving', '100g': 'protein_100g'},
        'fiber': {'serving': 'fiber_serving', '100g': 'fiber_100g'},
        'iron': {'serving': 'iron_serving', '100g': 'iron_100g'},
        'vitamin_d': {'serving': 'vitamin-d_serving', '100g': 'vitamin-d_100g'},
        'omega_3': {'serving': 'omega-3_serving', '100g': 'omega-3_100g'},
        'omega_3_epa': {'serving': 'epa_serving', '100g': 'epa_100g'},
        'omega_3_dha': {'serving': 'dha_serving', '100g': 'dha_100g'}
    }
    
    result = {}
    
    for nutrient_name, keys in nutrient_mapping.items():
        value = None
        unit = None
        
        # Try per-serving value first
        if keys['serving'] in nutriments:
            value = nutriments[keys['serving']]
            # Try to get the unit
            unit_key = keys['serving'].replace('_serving', '_unit')
            unit = nutriments.get(unit_key, 'g')  # Default to grams
        # Fall back to per 100g value
        elif keys['100g'] in nutriments:
            value = nutriments[keys['100g']]
            # Get serving quantity to calculate per serving
            serving_quantity = product.get('serving_quantity')
            if serving_quantity:
                value = value * (serving_quantity / 100)
            unit_key = keys['100g'].replace('_100g', '_unit')
            unit = nutriments.get(unit_key, 'g')
        
        if value is not None:
            # Convert iron from mg to g if needed
            if nutrient_name == 'iron' and unit == 'mg':
                value = value / 1000
                unit = 'g'
            
            result[nutrient_name] = {
                'value': round(value, 2),  # Round to 2 decimal places
                'unit': unit
            }
    
    return result if result else None

# Example usage:
if __name__ == "__main__":
    barcode = "737628064502"
    
    # Option 1: Get simple tracked nutrients
    simple_result = get_tracked_nutrients_simple(barcode)
    print("Simple Tracked Nutrients:")
    print(simple_result)
    
    print("\n" + "="*50 + "\n")
    
    # Option 2: Get comprehensive report
    comprehensive = get_comprehensive_nutrient_report(barcode)
    print("Comprehensive Report:")
    
    if comprehensive:
        print(f"Product: {comprehensive['product_name']}")
        print(f"Brand: {comprehensive.get('brands', 'N/A')}")
        print(f"Serving: {comprehensive['serving_info']['serving_quantity']} {comprehensive['serving_info']['serving_size']}")
        
        if 'nutrients_per_serving' in comprehensive:
            print("\nNutrients per serving:")
            for nutrient, data in comprehensive['nutrients_per_serving'].items():
                print(f"  {nutrient}: {data['value']} {data['unit']}")
        
        if 'nutrients_per_100g' in comprehensive:
            print("\nNutrients per 100g:")
            for nutrient, data in comprehensive['nutrients_per_100g'].items():
                print(f"  {nutrient}: {data['value']} {data['unit']}")
        
        if 'missing_nutrients' in comprehensive:
            print(f"\nMissing data for: {', '.join(comprehensive['missing_nutrients'])}")