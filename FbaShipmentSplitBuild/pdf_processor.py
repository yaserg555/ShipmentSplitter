import fitz  # PyMuPDF
import os
import re
import glob
from collections import defaultdict
from utils import sanitize_filename # Use absolute import
import traceback # Import traceback for detailed error logging
from sku_finder import find_sku_on_page # Import the extracted function


# Removed the old _find_sku_on_page function definition


def _create_grouped_output_pdfs(doc, sku_output_pages, shipping_id, output_dir, status_callback):
    """
    Creates the grouped output PDFs based on the final calculated page lists for each SKU.
    Returns the total number of pages written to split PDFs.
    """
    sku_counter = 0
    total_split_pages = 0
    status_callback(f"  Creating {len(sku_output_pages)} split PDF(s)...\n")
    
    for sku, page_list in sku_output_pages.items():
        if not page_list: 
            status_callback(f"    Skipping SKU '{sku}' due to empty page list.\n")
            continue
            
        sku_counter += 1
        number = sku_counter
        # Use the length of the final page list for the count in the filename
        box_count = len(page_list) 
        total_split_pages += box_count

        # Construct filename
        filename_parts = [str(number), sku, shipping_id, str(box_count)]
        output_filename_base = "_".join(part for part in filename_parts if part) 
        sanitized_filename_base = sanitize_filename(output_filename_base)
        output_pdf_path = os.path.join(output_dir, f"{sanitized_filename_base}.pdf")

        status_callback(f"    Creating: {sanitized_filename_base}.pdf ({box_count} pages: {min(page_list)+1} to {max(page_list)+1})\n")

        new_doc = None
        try:
            new_doc = fitz.open() 
            # Insert pages one by one from the calculated page list
            for page_num in sorted(page_list): # Ensure pages are added in order
                 # Check if page_num is valid for the original document
                 if 0 <= page_num < len(doc):
                     new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                 else:
                     status_callback(f"    Warn: Invalid page number {page_num+1} requested for insertion into {sanitized_filename_base}.pdf. Skipping.\n")
            
            if len(new_doc) > 0: # Only save if pages were actually inserted
                new_doc.save(output_pdf_path)
            else:
                status_callback(f"    Warn: No valid pages inserted for {sanitized_filename_base}.pdf. File not saved.\n")
                total_split_pages -= box_count # Adjust count as file wasn't saved

        except Exception as e:
            status_callback(f"    Error creating/saving PDF {output_pdf_path}: {e}\n")
            total_split_pages -= box_count # Adjust count as file wasn't saved properly
            status_callback(traceback.format_exc() + "\n") # Log detailed error
        finally:
            if new_doc:
                new_doc.close() 
                
    return total_split_pages

def process_single_pdf_document(pdf_path, keyword, status_callback):
    """
    Processes a single PDF document. Detects mode (standard/interleaved) based on page 2.
    Finds SKUs on each page and creates split PDFs based on the detected mode.
    Returns tuple: (success_boolean, pages_split_count)
    """
    status_callback(f"Processing PDF: {os.path.basename(pdf_path)}\n")
    doc = None
    pages_with_sku_count = 0 # Count pages where an SKU was *found*
    skipped_page_numbers = []
    is_interleaved_mode = False # Default to standard mode

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
                return False, 0
        except Exception as e:
            status_callback(f"  Error opening PDF: {e}\n")
            return False, 0

        # --- Mode Detection ---
        if total_pages >= 2:
            try:
                page_one = doc.load_page(1) # Page index 1 is the second page
                # Use the imported function (keyword argument is no longer used by the new function)
                sku_on_page_two = find_sku_on_page(page_one, status_callback)
                if sku_on_page_two is None:
                    is_interleaved_mode = True
                    # Clarify mode and implication
                    status_callback("  Mode Detected: Interleaved (No SKU on page 2). Output PDFs will include pages following SKU pages.\n") 
                else:
                    status_callback("  Mode Detected: Standard (SKU found on page 2). Output PDFs will include only pages with SKUs.\n")
            except Exception as e:
                 status_callback(f"  Warn: Could not check page 2 for mode detection: {e}. Assuming Standard Mode.\n")
        else:
             status_callback("  Warn: PDF has only one page. Assuming Standard Mode.\n")


        output_folder_name = f"{shipping_id}_{total_pages}pages"
        output_dir = os.path.join(input_dir, output_folder_name)
        os.makedirs(output_dir, exist_ok=True)

        status_callback(f"  Shipping ID: {shipping_id}\n")
        status_callback(f"  Total Pages: {total_pages}\n")
        status_callback(f"  Output Dir: {output_folder_name}\n")

        # --- Process pages to find SKU locations ---
        sku_pages = defaultdict(list) # Stores SKU -> [list of page indices where found]
        status_callback(f"  Scanning {total_pages} pages...\n")
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            # Use the imported function (keyword argument is no longer used by the new function)
            sku = find_sku_on_page(page, status_callback)
            if sku:
                sku_pages[sku].append(page_num)
                pages_with_sku_count += 1
            else:
                skipped_page_numbers.append(page_num + 1) 

        status_callback(f"  Finished scanning. Found {len(sku_pages)} unique SKUs across {pages_with_sku_count} pages.\n")

        if not sku_pages:
            status_callback("  No SKUs found in this document. No split PDFs created.\n")
            return True, 0 # Not an error, just nothing to split

        # --- Determine Output Page Ranges based on Mode ---
        sku_output_pages = defaultdict(list) # Stores SKU -> [final list of page indices to include]
        for sku, found_on_pages in sku_pages.items():
            if not found_on_pages: continue # Should not happen, but safe check
            
            min_page = min(found_on_pages)
            max_page = max(found_on_pages)
            
            if is_interleaved_mode:
                # Include all pages from min_page to max_page + 1
                # Ensure upper bound doesn't exceed total pages
                end_page_exclusive = min(max_page + 2, total_pages) 
                page_range = list(range(min_page, end_page_exclusive))
                sku_output_pages[sku] = page_range
                # status_callback(f"    SKU '{sku}': Interleaved range {min_page+1}-{end_page_exclusive}.\n")
            else:
                # Standard mode: Only include pages where SKU was found
                sku_output_pages[sku] = sorted(found_on_pages)
                # status_callback(f"    SKU '{sku}': Standard pages {sorted([p+1 for p in found_on_pages])}.\n")

        # --- Create output PDFs ---
        total_split_pages = _create_grouped_output_pdfs(doc, sku_output_pages, shipping_id, output_dir, status_callback)
        status_callback(f"  Finished creating split PDFs for {base_filename}.\n")

        # --- Verification ---
        status_callback("  Verification:\n")
        status_callback(f"    Original Pages: {total_pages}\n")
        status_callback(f"    Pages where SKU found: {pages_with_sku_count}\n")
        status_callback(f"    Total Pages Written to Split PDFs: {total_split_pages}\n")
        
        # Verification logic might differ based on mode
        if is_interleaved_mode:
             # Clarify verification in interleaved mode
             status_callback("    Verification Info: Interleaved mode used; page ranges include pages following last SKU occurrence.\n") 
        elif pages_with_sku_count != total_split_pages:
             # Standard mode failure condition
             status_callback("    Verification FAILED (Standard Mode): Mismatch between pages where SKU found and pages written.\n")
             # In standard mode, this indicates a potential problem
             # return False, total_split_pages # Decide if this is a hard failure

        if skipped_page_numbers:
             status_callback(f"    Note: {len(skipped_page_numbers)} page(s) were skipped (no SKU found): {skipped_page_numbers}\n")
             if not is_interleaved_mode: # Only recommend manual check if NOT interleaved
                 status_callback(f"    It's recommended to check the original PDF for these pages.\n") 

        return True, total_split_pages 

    except Exception as e:
        status_callback(f"  An unexpected error occurred processing {base_filename}: {e}\n")
        status_callback(traceback.format_exc() + "\n")
        return False, 0 
    finally:
        if doc:
            doc.close()

def process_shipment(input_path, is_folder, keyword, status_callback):
    """
    Main processing function called by the GUI thread.
    Handles both single file and folder processing.
    Returns tuple: (success_count, fail_count, total_files, total_pages_split)
    """
    success_count = 0
    fail_count = 0
    total_files = 0
    total_pages_split_across_run = 0 

    if is_folder:
        try:
            pdf_files = glob.glob(os.path.join(input_path, '*.[pP][dD][fF]')) 
            pdf_files = list(set(pdf_files)) 
            total_files = len(pdf_files)
            status_callback(f"Found {total_files} PDF(s) in the folder.\n")
            if not pdf_files:
                 status_callback("No PDF files found in the selected folder.\n")
                 return 0, 0, 0, 0 
            
            for i, pdf_path in enumerate(pdf_files):
                status_callback(f"--- Processing file {i+1}/{total_files} --- \n")
                success, pages_split = process_single_pdf_document(pdf_path, keyword, status_callback)
                if success:
                    success_count += 1
                    total_pages_split_across_run += pages_split
                else:
                    fail_count += 1
        except Exception as e:
            status_callback(f"Error scanning folder {input_path}: {e}\n")
            fail_count = total_files 
            total_pages_split_across_run = 0 
    else: # Single file processing
        total_files = 1
        # The input_path is the file path here
        success, pages_split = process_single_pdf_document(input_path, keyword, status_callback) 
        if success:
            success_count += 1
            total_pages_split_across_run = pages_split
        else:
            fail_count += 1
            
    return success_count, fail_count, total_files, total_pages_split_across_run
