from flask import Flask, Response, jsonify, request
import os
import json
import re
app = Flask(__name__)

# Path to the JSON data folder
DATA_DIR = "data"
hadith_data = {}

# Load all JSON files
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as file:
            book_name = filename.replace("-Translated.json", "").lower().replace(" ", "-")  # Normalize book names
            hadith_data[book_name] = json.load(file)
            print(f"Loaded Book: {book_name}")  # Debugging print

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Hadith API! Use /books to see available books."})

@app.route('/books', methods=['GET'])
def get_books_names():
    """Retrieve a list of all Hadith collections with English and Arabic names, along with links."""
    collection_names = []

    for collection, details in hadith_data.items():
        if isinstance(details, dict):  # Ensure it's a valid dictionary
            book_key = list(details.keys())[1]  # Extract actual book name key if nested
            book_data = details[book_key]  # Access correct data structure

            collection_names.append({
                "english_name": book_data.get("english_name", collection),
                "arabic_name": book_data.get("arabic_name", "لا يوجد اسم بالعربية"),  # Default if missing
                "link": book_data.get("link", "")
            })

    return custom_jsonify({"collections": collection_names})

def custom_jsonify(data):
    """Ensure Arabic text is properly displayed."""
    return Response(json.dumps(data, ensure_ascii=False, indent=4), content_type='application/json; charset=utf-8')


# ✅ 2. Get book metadata and details
@app.route('/books/<book_name>', methods=['GET'])
def get_book_info(book_name):
    book_name = book_name.lower().replace(" ", "-")
    available_books = {k.lower(): k for k in hadith_data.keys()}

    if book_name in available_books:
        book_data = hadith_data[available_books[book_name]]

        # Extract metadata correctly
        book_data_key = list(book_data.keys())[1]  # Extract the actual book name key
        book_data = book_data[book_data_key]  # Go inside this key

        # Extract `about_info` if available
        about_info = book_data.get("books_or_chapters", {}).get("about_info", {})

        book_info = {
            "book_name": available_books[book_name],
            "english_name": book_data.get("english_name", "No English Name Available"),
            "arabic_name": book_data.get("arabic_name", "لا يوجد اسم باللغة العربية"),
            "index_tag": book_data.get("indextag", "No Index Tag Available"),
            "link": book_data.get("link", "No Link Available"),
            "total_chapters": len(book_data.get("books_or_chapters", {}).get("books", [])),
            "about_info": {
                "title": about_info.get("about_title", "No About Title Available"),
                "content english": about_info.get("about_content_english", ""),
                "content arabic":about_info.get("about_content_arabic","")
            }
        }

        # ✅ Return response with proper encoding
        return Response(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8"
        )

    return jsonify({"error": "Book not found"}), 404


# ✅ 3. Get full book content (all chapters and hadiths)
@app.route('/book/<book_name>', methods=['GET'])
def get_book(book_name):
    book_name = book_name.lower().replace(" ", "-")
    available_books = {k.lower(): k for k in hadith_data.keys()}

    if book_name in available_books:
        book_data = hadith_data[available_books[book_name]]
        return Response(
            json.dumps(book_data, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8"
        )

    return jsonify({"error": "Book not found"}), 404

#import json
@app.route('/book/<book_name>/all-hadiths', methods=['GET'])
def get_all_hadiths_from_book(book_name):
    # 🔹 Improved Normalization
    # Replace both `-` and `'` with an empty string to match any variation
    formatted_book_name = (
        book_name.lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace("’", "")
        .replace("-", "")  # Remove hyphens to match variations like "dan" vs "d'an"
    )

    # 🔍 Fix: Ensure correct book lookup by matching normalized names
    available_books = {
        k.lower().replace(" ", "-").replace("'", "").replace("’", "").replace("-", ""): k
        for k in hadith_data.keys()
    }

    # 🛠 Debug: Print the available book names for troubleshooting
    print(f"DEBUG: Requested Book = {formatted_book_name}")
    print(f"DEBUG: Available Books = {list(available_books.keys())}")

    if formatted_book_name in available_books:
        book_data = hadith_data[available_books[formatted_book_name]]

        # Extract actual book data (since it's nested inside the book name key)
        book_data_keys = list(book_data.keys())
        if len(book_data_keys) > 1:
            actual_book_key = book_data_keys[1]  # Extract the correct book key dynamically
            book_data = book_data[actual_book_key]

        # ✅ Extract Hadiths: Handling multiple structures dynamically
        hadith_list = []
        if "books_or_chapters" in book_data:
            if "books" in book_data["books_or_chapters"]:  # Case: books exist
                books = book_data["books_or_chapters"]["books"]
                for book in books:
                    for chapter in book.get("chapters_and_hadiths", []):
                        for hadith in chapter.get("hadiths", []):
                            hadith_list.append(format_hadith(hadith, book, chapter))
            elif "chapters_and_hadiths" in book_data["books_or_chapters"]:  # Case: only chapters exist
                chapters = book_data["books_or_chapters"]["chapters_and_hadiths"]
                for chapter in chapters:
                    for hadith in chapter.get("hadiths", []):
                        hadith_list.append(format_hadith(hadith, None, chapter))

        # ✅ Return Hadith List
        return Response(
            json.dumps({"hadiths": hadith_list}, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8"
        )

    # 🔍 Debugging: Show available book names in error response
    return jsonify({
        "error": "Book not found",
        "requested_book": formatted_book_name,
        "available_books": list(available_books.keys())
    }), 404


# ✅ Helper function to format hadith
def format_hadith(hadith, book=None, chapter=None):
    return {
        "reference": hadith.get("reference", "No Reference"),
        "narrator": hadith.get("narrator", "No Narrator"),
        "english_text": hadith.get("english_text", "No English Text Available"),
        "arabic_text": hadith.get("arabic_text", "No Arabic Text Available"),
        "book_number": book.get("book_number", "No Book Number") if book else "N/A",
        "chapter_no": chapter.get("chapter_no", "No Chapter Number") if chapter else "N/A",
        "chapter_title_english": chapter.get("chapter_title_english", "No Chapter Title") if chapter else "N/A",
        "chapter_title_arabic": chapter.get("chapter_title_arabic", "No Chapter Title Arabic") if chapter else "N/A"
    }



@app.route('/books/<book_name>/sections', methods=['GET'])
def get_book_sections(book_name):
    book_name = book_name.lower().replace(" ", "-")
    available_books = {k.lower(): k for k in hadith_data.keys()}

    if book_name in available_books:
        book_data = hadith_data[available_books[book_name]]

        # ✅ Ensure book data structure is correct
        book_data_keys = list(book_data.keys())
        if len(book_data_keys) < 2:
            return jsonify({"error": "Invalid book structure"}), 404

        book_data_key = book_data_keys[1]  # Extracts the actual book name key
        book_data = book_data[book_data_key]  # Go inside this key

        # ✅ Extract all sections (books inside "books_or_chapters")
        sections = [
            {
                "book_number": book.get("book_number", ""),
                "english_book_name": book.get("english_book_name", ""),
                "arabic_book_name": book.get("arabic_book_name", ""),  # Arabic Support
                "book_range":book.get("book_range"," ")
            }
            for book in book_data.get("books_or_chapters", {}).get("books", [])
        ]

        # ✅ Ensure UTF-8 encoding is handled correctly for Arabic
        return Response(
            json.dumps({"sections": sections}, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8"
        )

    return jsonify({"error": "Book not found"}), 404
import unicodedata

def normalize_text(text):
    """Removes accents and normalizes text for matching."""
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).lower().replace(" ", "-")

@app.route('/books/<book_name>/hadiths/<section_name>', methods=['GET'])
def get_hadiths_from_section(book_name, section_name):
    book_name = book_name.lower().replace(" ", "-")
    section_name = normalize_text(section_name)  # Normalize input for better matching
    available_books = {k.lower(): k for k in hadith_data.keys()}

    if book_name in available_books:
        book_data = hadith_data[available_books[book_name]]

        # ✅ Extract actual book key from JSON
        book_data_keys = list(book_data.keys())
        if len(book_data_keys) < 2:
            return jsonify({"error": "Invalid book structure"}), 404

        book_data_key = book_data_keys[1]  # Extracts the actual book name key
        book_data = book_data[book_data_key]  # Access correct book key

        # ✅ Get all books (sections)
        books = book_data.get("books_or_chapters", {}).get("books", [])

        # 🔍 Debug: Print all available sections for troubleshooting
        print("DEBUG: Available Sections (Normalized):")
        available_section_names = {}
        for book in books:
            english_name = book.get("english_book_name", "").strip()
            arabic_name = book.get("arabic_book_name", "").strip()
            
            normalized_english = normalize_text(english_name)
            normalized_arabic = normalize_text(arabic_name)

            available_section_names[normalized_english] = book
            available_section_names[normalized_arabic] = book  # Allow Arabic matching too
            
            print(f"  - English (Normalized): {normalized_english} → {english_name}")
            print(f"  - Arabic (Normalized): {normalized_arabic} → {arabic_name}")
            print("-" * 50)

        # ✅ Check if section exists
        if section_name in available_section_names:
            selected_section = available_section_names[section_name]

            hadiths_list = []
            for chapter in selected_section.get("chapters_and_hadiths", []):
                chapter_info = {
                    "chapter_no": chapter.get("chapter_no", "No Chapter Number"),
                    "chapter_title_english": chapter.get("chapter_title_english", "No English Title"),
                    "chapter_title_arabic": chapter.get("chapter_title_arabic", "No Arabic Title"),
                    "chapter_intro": chapter.get("chapter_intro", "No Introduction")
                }

                chapter_hadiths = []
                for hadith in chapter.get("hadiths", []):
                    chapter_hadiths.append({
                        "reference": hadith.get("reference", "No Reference"),
                        "narrator": hadith.get("narrator", "No Narrator"),
                        "english_text": hadith.get("english_text", "No English Text Available"),
                        "arabic_text": hadith.get("arabic_text", "لا يوجد نص باللغة العربية"),
                        "references": hadith.get("references", [])
                    })

                hadiths_list.append({
                    "chapter_info": chapter_info,
                    "hadiths": chapter_hadiths
                })

            # ✅ Ensure UTF-8 encoding is handled correctly for Arabic
            return Response(
                json.dumps({"hadiths": hadiths_list}, ensure_ascii=False, indent=2),
                content_type="application/json; charset=utf-8"
            )

        return jsonify({"error": f"Section '{section_name}' not found in '{book_name}'"}), 404

    return jsonify({"error": "Book not found"}), 404

# ✅ 7. Search for a keyword within a specific book
@app.route('/search', methods=['GET'])
def search_hadith():
    keyword = request.args.get('q', '').lower()
    results = []

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    for book_name, book_data in hadith_data.items():
        for book in book_data.get("books_or_chapters", {}).get("books", []):
            for chapter in book.get("chapters_and_hadiths", []):
                for hadith in chapter.get("hadiths", []):
                    english_text = hadith.get("english_text", "").lower() if hadith.get("english_text") else ""
                    arabic_text = hadith.get("arabic_text", "").lower() if hadith.get("arabic_text") else ""

                    if keyword in english_text or keyword in arabic_text:
                        results.append({
                            "book_name": book_name,
                            "reference": hadith["reference"],
                            "text": hadith.get("english_text", "No English Text Available"),
                            "arabic_text": hadith.get("arabic_text", "No Arabic Text Available")
                        })

    return Response(
        json.dumps({"results": results}, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8"
    )

# ✅ 8. Global search across all books
@app.route('/global-search', methods=['GET'])
def global_search():
    keyword = request.args.get('q', '').lower()
    results = []

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    for book_name, book_data in hadith_data.items():
        for book in book_data.get("books_or_chapters", {}).get("books", []):
            for chapter in book.get("chapters_and_hadiths", []):
                for hadith in chapter.get("hadiths", []):
                    english_text = hadith.get("english_text", "").lower() if hadith.get("english_text") else ""
                    arabic_text = hadith.get("arabic_text", "").lower() if hadith.get("arabic_text") else ""

                    if keyword in english_text or keyword in arabic_text:
                        results.append({
                            "book_name": book_name,
                            "reference": hadith["reference"],
                            "text": hadith.get("english_text", "No English Text Available"),
                            "arabic_text": hadith.get("arabic_text", "No Arabic Text Available")
                        })

    return Response(
        json.dumps({"results": results}, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8"
    )

if __name__ == '__main__':
    app.run(debug=True)
