import fitz  # PyMuPDF
import os
import re
import glob # Import glob
from collections import defaultdict
from utils import sanitize_filename # Use absolute import

def _find_sku_on_page(page, status_callback, sku_keyword=None):
    """
    Finds the SKU on a single page using primary and fallback methods.
    Returns the SKU string or None if not found.
    """
    text = page.get_text("text")
    lines = text.splitlines()
    sku = None
    method_used = "None"

    # Prepare regex pattern
    default_keywords = ["数量", "Qty", "Menge"]
    if sku_keyword and sku_keyword.strip():
        keyword_pattern = re.escape(sku_keyword.strip())
    else:
        keyword_pattern = "|".join(default_keywords)
    
    primary_sku_regex = re.compile(r'^([A-Z0-9_.-]+)\s+(?:' + keyword_pattern + r')', re.MULTILINE | re.IGNORECASE)

    # 1. Try Primary Regex
    primary_match = primary_sku_regex.search(text)
    if primary_match:
        sku = primary_match.group(1).strip()
        method_used = "Primary Regex"
    else:
        # 2. Try Fallback 1: Line after "Single SKU"
        try:
            single_sku_line_index = -1
            for i, line in enumerate(lines):
                if "single sku" in line.lower():
                    single_sku_line_index = i
                    break
            
            if single_sku_line_index != -1 and single_sku_line_index + 1 < len(lines):
                potential_sku = lines[single_sku_line_index + 1].strip()
                # Basic validation
                if potential_sku and re.match(r'^[A-Z0-9_.-]+$', potential_sku, re.IGNORECASE): 
                    sku = potential_sku
                    method_used = "Fallback 1 (After 'Single SKU')"
        except Exception as e:
            # Log error but don't stop processing
            status_callback(f"    Warn: Error during Fallback 1 on page {page.number + 1}: {e}\n")

        # 3. Try Fallback 2: 4th line (if Fallback 1 failed)
        if sku is None: 
            if len(lines) >= 4:
                potential_sku = lines[3].strip() 
                # Basic validation
                if potential_sku and re.match(r'^[A-Z0-9_.-]+$', potential_sku, re.IGNORECASE):
                    sku = potential_sku
                    method_used = "Fallback 2 (4th Line)"

    # if sku:
    #     status_callback(f"    Debug: Page {page.number + 1}: Found SKU '{sku}' (Method: {method_used})\n")
    # else:
    #      status_callback(f"    Debug: Page {page.number + 1}: No SKU found.\n")
         
    return sku

def _create_grouped_output_pdfs(doc, sku_pages, shipping_id, output_dir, status_callback):
    """
    Creates the grouped output PDFs based on the extracted SKUs and page numbers.
    Returns the total number of pages written to split PDFs.
    """
    sku_counter = 0
    total_split_pages = 0
    status_callback(f"  Creating {len(sku_pages)} split PDF(s)...\n")
    for sku, page_numbers in sku_pages.items():
        if not page_numbers: continue
        sku_counter += 1
        number = sku_counter
        box_count = len(page_numbers)
        total_split_pages += box_count

        # Construct filename
        filename_parts = [str(number), sku, shipping_id, str(box_count)]
        output_filename_base = "_".join(part for part in filename_parts if part) # Avoid empty parts
        sanitized_filename_base = sanitize_filename(output_filename_base)
        output_pdf_path = os.path.join(output_dir, f"{sanitized_filename_base}.pdf")

        status_callback(f"    Creating: {sanitized_filename_base}.pdf ({box_count} pages)\n")

        new_doc = None
        try:
            new_doc = fitz.open() # Create a new PDF for this SKU group
            # Insert pages one by one from the original document
            for page_num in sorted(page_numbers): # Ensure pages are added in order
                 new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            new_doc.save(output_pdf_path)
        except Exception as e:
            status_callback(f"    Error saving PDF {output_pdf_path}: {e}\n")
            # Optionally, re-raise or handle more specifically if needed
        finally:
            if new_doc:
                new_doc.close() 
    return total_split_pages

def process_single_pdf_document(pdf_path, keyword, status_callback):
    """
    Processes a single PDF document to find SKUs on each page and create split PDFs.
    Returns True on success, False on failure.
    """
    status_callback(f"Processing PDF: {os.path.basename(pdf_path)}\n")
    doc = None
    pages_processed_count = 0
    skipped_page_numbers = []

    try:
        # Determine output dir and basic info
        input_dir = os.path.dirname(pdf_path)
        base_filename = os.path.basename(pdf_path)
        shipping_id_base, _ = os.path.splitext(base_filename)

        if shipping_id_base.lower().startswith("package-"):
            shipping_id = shipping_id_base[len("package-"):]
        else:
            shipping_id = shipping_id_base

        # Open PDF safely
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            if total_pages == 0:
                status_callback("  Error: PDF has no pages.\n")
                return False
        except Exception as e:
            status_callback(f"  Error opening PDF: {e}\n")
            return False

        output_folder_name = f"{shipping_id}_{total_pages}pages"
        output_dir = os.path.join(input_dir, output_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        status_callback(f"  Shipping ID: {shipping_id}\n")
        status_callback(f"  Total Pages: {total_pages}\n")
        status_callback(f"  Output Dir: {output_folder_name}\n")

        # Process pages
        sku_pages = defaultdict(list)
        status_callback(f"  Scanning {total_pages} pages...\n")
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            sku = _find_sku_on_page(page, status_callback, keyword)
            if sku:
                sku_pages[sku].append(page_num)
                pages_processed_count += 1
            else:
                skipped_page_numbers.append(page_num + 1) # Store 1-based page number

        status_callback(f"  Finished scanning. Found {len(sku_pages)} unique SKUs across {pages_processed_count} pages.\n")

        if not sku_pages:
            status_callback("  No SKUs found in this document. No split PDFs created.\n")
            # Decide if this is an error or just a note
            # return False # Uncomment if this should be treated as an error

        # Create output PDFs
        total_split_pages = _create_grouped_output_pdfs(doc, sku_pages, shipping_id, output_dir, status_callback)
        status_callback(f"  Finished creating split PDFs for {base_filename}.\n")

        # Verification
        status_callback("  Verification:\n")
        status_callback(f"    Original Pages: {total_pages}\n")
        status_callback(f"    Pages Assigned to SKUs: {pages_processed_count}\n")
        status_callback(f"    Pages Written to Split PDFs: {total_split_pages}\n")
        
        if pages_processed_count == total_split_pages:
            status_callback("    Verification successful.\n")
            if skipped_page_numbers:
                 status_callback(f"    Note: {len(skipped_page_numbers)} page(s) were skipped (no SKU found): {skipped_page_numbers}\n")
                 status_callback(f"    It's recommended to check the original PDF for these pages.\n") # Manual check suggestion
        else:
            status_callback(f"    Verification FAILED: Mismatch between pages assigned ({pages_processed_count}) and written ({total_split_pages}).\n")
            return False

        return True

    except Exception as e:
        status_callback(f"  An unexpected error occurred processing {base_filename}: {e}\n")
        import traceback
        status_callback(traceback.format_exc() + "\n")
        return False
    finally:
        if doc:
            doc.close()
            # status_callback("  Document closed.\n")

# Placeholder for the function that the GUI thread will call
# This function will handle iterating if it's a folder
def process_shipment(input_path, is_folder, keyword, status_callback):
    """
    Main processing function called by the GUI thread.
    Handles both single file and folder processing.
    """
    success_count = 0
    fail_count = 0
    total_files = 0

    if is_folder:
        try:
            pdf_files = glob.glob(os.path.join(input_path, '*.[pP][dD][fF]')) 
            pdf_files = list(set(pdf_files)) 
            total_files = len(pdf_files)
            status_callback(f"Found {total_files} PDF(s) in the folder.\n")
            if not pdf_files:
                 status_callback("No PDF files found in the selected folder.\n")
                 return 0, 0, 0 # Return counts directly
            
            for i, pdf_path in enumerate(pdf_files):
                status_callback(f"--- Processing file {i+1}/{total_files} --- \n")
                if process_single_pdf_document(pdf_path, keyword, status_callback):
                    success_count += 1
                else:
                    fail_count += 1
        except Exception as e:
            status_callback(f"Error scanning folder {input_path}: {e}\n")
            fail_count = total_files # Assume all failed if folder scan fails
    else: # Single file
        total_files = 1
        if process_single_pdf_document(input_path, keyword, status_callback):
            success_count += 1
        else:
            fail_count += 1
            
    return success_count, fail_count, total_files
