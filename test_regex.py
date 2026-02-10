
import re

VERBOSE_INFERENCE = True

REGEX_PATTERNS = {
    "ukrainian_id_card": r"\b(\d{3}\s?\d{3}\s?\d{3}|\d{9})\b",
    "passport_book": r"\b([А-ЯA-Z]{2}\s?\d{6}|[А-ЯA-Z]{2}\d{6})\b",
    "international": r"\b(?=.*[0-9])([A-Z0-9]{8,15})\b",  # Updated regex
}

def _extract_passport_number(ocr_text: str):
    cleaned_text = re.sub(r"\s+", " ", ocr_text).upper()
    print(f"Cleaned Text: {cleaned_text}")

    # ID Card
    pattern = REGEX_PATTERNS.get("ukrainian_id_card")
    match = re.search(pattern, cleaned_text)
    if match:
        print("Match: ID Card")
        return match.group(0).replace(" ", "")

    # Passport Book
    pattern = REGEX_PATTERNS.get("passport_book")
    match = re.search(pattern, cleaned_text)
    if match:
        print("Match: Passport Book")
        return match.group(0).replace(" ", "")

    # International
    pattern = REGEX_PATTERNS.get("international")
    match = re.search(pattern, cleaned_text)
    if match:
        print(f"Match: International (Group 1: {match.group(1)})")
        return match.group(1)

    return None

# Test Cases
test_cases = [
    # User Example 1
    """Kingdom of Nordland
Type:
Code:
Passport No:
P
NO
N482019222
Surname
ANDERSEN
Authority
10 JAN 2019
POLICE BOARD""",
    
    # User Example 2
    """State of New Hanover
Type:
Code:
Passport No:
P
NH
A189919111
Surname:
MORGAN
Authority: :
BLACKWATER AGENCY""",

    # False Positive Checks
    "AUTHORITY",
    "REPUBLIC OF NOWHERE",
    "PASSPORT NO",
    "DATE OF BIRTH",
    "12345678" # 8 digits -> Should match international if ID card fails? 
               # ID card requires 9 digits. 
               # International requires 8-15 chars and at least one digit. 
               # So 8 digits is valid international passport number.
]

print("--- Testing Regex logic ---")
for i, text in enumerate(test_cases):
    print(f"\nCase {i+1}:")
    res = _extract_passport_number(text)
    print(f"Result: {res}")
