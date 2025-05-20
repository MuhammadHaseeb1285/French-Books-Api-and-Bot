import json
import time
from deep_translator import GoogleTranslator
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")
# =================================================================================
# CONFIGURATION
# =================================================================================
input_file = r"D:\Hassan Ali\Paid Projects\Scrapping\scraped_files\Sahih Muslim.json"
output_file = r"D:\Hassan Ali\Paid Projects\Scrapping\scraped_files\Sahih_Muslim_french.json"

FIELDS_TO_TRANSLATE = {
    "indextag",
    "english_name",
    "about_title",
    "about_content",
    "english_book_name",
    "chapter_title_english",
    "english_text",
    "narrator",
}

# =================================================================================
# TRANSLATION FUNCTIONS
# =================================================================================
def translate_text(text, max_retries=3):
    """Translate text with progress tracking and error handling"""
    if not isinstance(text, str) or not text.strip():
        print(" Skipping non-text value:", type(text))
        return text

    # Print original text (truncated for readability)
    max_show = 70  # Characters to show in console
    print("\n" + "="*50)
    print(" Translating:")
    print(f"ORIGINAL ({len(text)} chars): {text[:max_show]}...")

    for attempt in range(max_retries):
        try:
            translated = GoogleTranslator(source='en', target='fr').translate(text)
            print(f" SUCCESS (Attempt {attempt+1})")
            print(f"TRANSLATED ({len(translated)} chars): {translated[:max_show]}...")
            return translated
            
        except Exception as e:
            print(f" Attempt {attempt+1} failed: {str(e)}")
            time.sleep(2)  # Add delay between attempts
            
    print(" All translation attempts failed")
    return text  # Fallback to original

def process_structure(obj, depth=0):
    """Recursively process JSON structure with visual indentation"""
    indent = "  " * depth
    
    if isinstance(obj, dict):
        print(f"{indent} Processing dictionary ({len(obj)} keys)")
        for key in list(obj.keys()):  # Use list() to avoid modification issues
            print(f"{indent}   Key: {key}")
            if key in FIELDS_TO_TRANSLATE:
                # Translate matching fields
                original = obj[key]
                obj[key] = translate_text(original)
            else:
                # Recurse into non-translatable fields
                process_structure(obj[key], depth+1)
                
    elif isinstance(obj, list):
        print(f"{indent} Processing list ({len(obj)} items)")
        for i, item in enumerate(obj):
            print(f"{indent}   Item {i+1}/{len(obj)}")
            process_structure(item, depth+1)

# =================================================================================
# MAIN EXECUTION
# =================================================================================
def main():
    print(" Starting translation process")
    
    # Load data
    print(f"\n Loading file: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Process data
    print("\n Beginning translation...")
    process_structure(data)
    
    # Save results
    print(f"\n Saving translated file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n Translation complete!")

if _name_ == "_main_":
    main()
