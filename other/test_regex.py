import re
import os

def extract_product_name(filename: str) -> str:
    """Test the product name extraction"""
    # Remove file extension if present
    name_without_ext = os.path.splitext(filename)[0]
    
    # Pattern: everything before _[single_digit]_[exactly_6_letters] at the end
    match = re.match(r'^(.+)_\d_[a-zA-Z]{6}$', name_without_ext)
    
    if match:
        product_name = match.group(1)
        # Replace underscores with spaces
        product_name = product_name.replace('_', ' ')
        return product_name.strip()
    else:
        # Fallback: try to remove the last two underscore sections if they exist
        parts = name_without_ext.split('_')
        if len(parts) >= 3:
            # Check if last part is 6 letters and second-to-last is a single digit
            if len(parts[-1]) == 6 and parts[-1].isalpha() and len(parts[-2]) == 1 and parts[-2].isdigit():
                product_name = '_'.join(parts[:-2])
                return product_name.replace('_', ' ').strip()
        
        # Final fallback: just replace underscores
        return name_without_ext.replace('_', ' ').strip()

# Test cases from your CSV
test_filenames = [
    "AC_Milan_04-05_1_xnfgfd.png",
    "AC_Milan_04-05_4_xupek6.png", 
    "Valencia_1980-81_5_crxple.png",
    "Valencia_1980-81_5_rvfyp9.png",
    "Santos_2012_Visita_4_bzsbbn.png",
    "Santos_2012_Local_8_pshcth.png",
    "Real_Madrid_Local_2003-04_7_ehzzya.png",
    "Manchester_United_2023-24_Visita_7_a50f2w.png",
    "México_Mundial_2010_Visita_Chicharito_uwlch0.png",
    # Adding the failing examples
    "Colo-Colo_2006_6_cwa7mo.png",
    "Colo-Colo_2006_5_flz7rf.png",
    "Colo-Colo_2006_4_u9hwid.png",
    "Colo-Colo_2006_3_w48dt2.png"
]

print("🧪 Testing Product Name Extraction")
print("=" * 50)

for filename in test_filenames:
    result = extract_product_name(filename)
    print(f"Input:  {filename}")
    print(f"Output: {result}")
    print(f"Match:  {bool(re.match(r'^(.+)_\d+_[a-zA-Z]{6}$', os.path.splitext(filename)[0]))}")
    print("-" * 30) 