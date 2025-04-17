import re
import os

def sanitize_filename(filename):
    """Removes or replaces characters invalid for filenames."""
    # Remove characters that are explicitly invalid in Windows and often problematic elsewhere
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename) 
    # Replace sequences of whitespace with a single underscore
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove leading/trailing underscores/whitespace that might have resulted
    sanitized = sanitized.strip('_ ') 
    # Optional: Limit length if needed (e.g., 200 characters)
    # max_len = 200
    # if len(sanitized) > max_len:
    #     # Find the last underscore before max_len to avoid cutting mid-word/sku
    #     cutoff = sanitized.rfind('_', 0, max_len)
    #     if cutoff != -1:
    #         sanitized = sanitized[:cutoff]
    #     else: # If no underscore, just truncate
    #         sanitized = sanitized[:max_len]
            
    return sanitized

# Example usage (can be removed later)
if __name__ == '__main__':
    test_names = [
        "SKU*123 / ABC? <1> : X",
        "  leading and trailing spaces  ",
        "multiple   spaces",
        "very/long/path/like/name/with/invalid:chars*?.pdf"
    ]
    for name in test_names:
        print(f"Original: '{name}' -> Sanitized: '{sanitize_filename(name)}'")
