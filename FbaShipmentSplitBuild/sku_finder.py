import re # Import regular expression module

def find_sku_on_page(page, status_callback):
    """
    (Version 6 - Extracted)
    Finds the SKU based on the structure:
    1. Line containing "SKU" header ("single sku", "単一のsku").
    2. SKU value on the next 1 or 2 lines.
    3. Quantity line (Menge/Qty/数量 + number) immediately after the SKU value line(s).
    Returns the SKU string or None if not found.
    """
    # Ensure page object is valid
    if not page:
        if status_callback: status_callback("    Error: Invalid page object received in find_sku_on_page.\n")
        return None

    try:
        # Get text, preserving line breaks reasonably well
        text = page.get_text("text")
        # Split into lines and remove leading/trailing whitespace from each
        lines = [line.strip() for line in text.splitlines() if line.strip()]
    except Exception as e:
        if status_callback: status_callback(f"    Error getting text from page {page.number + 1 if page else 'N/A'}: {e}\n")
        return None

    if not lines:
        if status_callback: status_callback(f"    Warn: No text lines found on page {page.number + 1}.\n")
        return None

    # --- Define Patterns ---
    sku_header_patterns = ["single sku", "単一のsku"]
    # Looks for Menge/Qty/数量, followed by whitespace, then one or more digits. Allows other text after. Case-insensitive.
    quantity_line_pattern = re.compile(r'(?:Menge|Qty|数量)\s+\d+', re.IGNORECASE) # Removed '$' anchor
    # Validates if a string looks like a plausible SKU (alphanumeric, underscore, hyphen, dot, plus)
    valid_sku_chars_regex = re.compile(r'^[A-Z0-9_.+-]+$', re.IGNORECASE) # Added '+'

    # --- Find SKU based on Structure ---
    sku_header_line_index = -1

    # 1. Find the SKU header line
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for pattern in sku_header_patterns:
            if pattern in line_lower:
                sku_header_line_index = i
                # if status_callback: status_callback(f"Debug: Found SKU header '{pattern}' on line {i+1}") # Debug
                break # Stop checking patterns for this line
        if sku_header_line_index != -1:
            break # Stop checking lines

    if sku_header_line_index == -1:
        # if status_callback: status_callback(f"Debug: No SKU header line found on page {page.number + 1}") # Debug
        return None # Header not found, cannot proceed with this logic

    # 2. Check lines following the header
    line_after_header = lines[sku_header_line_index + 1] if sku_header_line_index + 1 < len(lines) else None
    line_two_after_header = lines[sku_header_line_index + 2] if sku_header_line_index + 2 < len(lines) else None
    line_three_after_header = lines[sku_header_line_index + 3] if sku_header_line_index + 3 < len(lines) else None

    potential_sku = None

    # Scenario 1: Quantity line is 2 lines after header (SKU is 1 line)
    if line_two_after_header and quantity_line_pattern.search(line_two_after_header):
        # if status_callback: status_callback(f"Debug: Scenario 1 detected. Qty line: '{line_two_after_header}'") # Debug
        if line_after_header:
            potential_sku = line_after_header
            # if status_callback: status_callback(f"Debug: Potential 1-line SKU: '{potential_sku}'") # Debug

    # Scenario 2: Quantity line is 3 lines after header (SKU is 2 lines)
    elif line_three_after_header and quantity_line_pattern.search(line_three_after_header):
        # if status_callback: status_callback(f"Debug: Scenario 2 detected. Qty line: '{line_three_after_header}'") # Debug
        if line_after_header and line_two_after_header:
            # Combine the two lines presumed to be the SKU
            potential_sku = line_after_header + line_two_after_header
            # if status_callback: status_callback(f"Debug: Potential 2-line SKU: '{potential_sku}'") # Debug

    # 3. Validate the potential SKU
    if potential_sku:
        # Basic validation: check if it contains valid characters
        if valid_sku_chars_regex.match(potential_sku):
            # if status_callback: status_callback(f"Debug: Valid SKU found: '{potential_sku}'") # Debug
            return potential_sku
        else:
            # if status_callback: status_callback(f"Debug: Potential SKU '{potential_sku}' failed validation.") # Debug
            return None # Failed validation
    else:
        # if status_callback: status_callback(f"Debug: No SKU found matching scenarios on page {page.number + 1}") # Debug
        return None # Did not fit either scenario
