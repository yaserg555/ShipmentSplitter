#!/usr/bin/env python3
"""
PDF Splitter by SKU

This script reads a CSV file containing shipment data and splits a provided PDF file
into multiple PDFs, grouped by SKU level. The script does not read or analyze the PDF
content itself but splits strictly by pages, assuming each page corresponds to one box.
All business logic and sorting rely solely on the CSV data.
"""

import os
import sys
import pandas as pd
import fitz  # PyMuPDF
from pathlib import Path
import logging
import argparse
import csv  # Add csv module for quoting constants

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_header_row(df):
    """
    Dynamically locate the header row containing required columns.
    
    Args:
        df: DataFrame with the raw CSV content
        
    Returns:
        int: Index of the header row
    """
    required_columns = ['SKU', 'ASIN', 'Total boxes', 'Box ID']
    
    # Iterate through rows to find a row that contains all required columns
    for i, row in df.iterrows():
        # Convert row values to strings and check if all required columns are present
        row_values = [str(val).strip() for val in row.values if not pd.isna(val)]
        if all(col in row_values for col in required_columns):
            logger.info(f"Found header row at index {i}")
            return i
    
    raise ValueError("Could not find header row with required columns")

def extract_shipment_id(df, header_row_idx):
    """
    Extract the shipment ID from the CSV file.
    
    Args:
        df: DataFrame with the raw CSV content
        header_row_idx: Index of the header row
        
    Returns:
        str: Shipment ID
    """
    # Look for shipment ID in rows before the header
    for i in range(header_row_idx):
        row = df.iloc[i]
        row_values = [str(val).strip() for val in row.values if not pd.isna(val)]
        
        # Look for values that might contain "Shipment ID" or similar
        for val in row_values:
            if "shipment" in val.lower() and ":" in val:
                shipment_id = val.split(":", 1)[1].strip()
                logger.info(f"Found Shipment ID: {shipment_id}")
                return shipment_id
    
    # If not found in specific format, try to extract from the first box ID
    try:
        # Get the first box ID after the header row
        first_box = df.iloc[header_row_idx + 1].iloc[-1]
        if isinstance(first_box, str) and len(first_box) >= 12:
            # Extract the first part of the box ID (usually the shipment ID)
            shipment_id = first_box.split("0000")[0]
            logger.info(f"Extracted Shipment ID from Box ID: {shipment_id}")
            return shipment_id
    except (IndexError, AttributeError):
        pass
    
    # Default fallback
    logger.warning("Could not extract Shipment ID, using default")
    return "UNKNOWN"

def process_csv(csv_path):
    """
    Process the CSV file to extract shipment data using the csv module directly.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        tuple: (shipment_id, groups) where groups is a list of dictionaries with SKU grouping info
    """
    logger.info(f"Processing CSV file: {csv_path}")
    
    # Extract shipment ID and find header row
    shipment_id = "UNKNOWN"
    header_row_index = -1
    header_columns = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            if "Shipment ID" in line and shipment_id == "UNKNOWN":
                # Extract shipment ID from the line
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    shipment_id = parts[1].strip().strip('"')
                    logger.info(f"Found Shipment ID: {shipment_id}")
            
            if "SKU" in line and "ASIN" in line and "Box ID" in line:
                header_row_index = i
                # Extract header column names
                reader = csv.reader([line])
                header_columns = next(reader)
                logger.info(f"Found header row at line {i}")
                break
    
    if shipment_id == "UNKNOWN":
        logger.warning("Could not extract Shipment ID, using default")
    
    if header_row_index == -1:
        raise ValueError("Could not find header row with required columns")
    
    # Process the CSV data
    sku_index = header_columns.index("SKU")
    asin_index = header_columns.index("ASIN")
    box_id_index = header_columns.index("Box ID")
    
    # Read all data rows
    data_rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i > header_row_index and len(row) > box_id_index:
                # Add row number (relative to header row)
                row_num = i - header_row_index
                data_rows.append((row_num, row))
    
    # Process box IDs (they may be comma-separated)
    expanded_rows = []
    for row_num, row in data_rows:
        sku = row[sku_index]
        asin = row[asin_index]
        box_ids_str = row[box_id_index]
        
        # Split box IDs (they may be comma-separated)
        box_ids = box_ids_str.split(',')
        
        for box_id in box_ids:
            box_id = box_id.strip()
            if box_id:  # Skip empty box IDs
                expanded_rows.append({
                    "RowNum": row_num,
                    "SKU": sku,
                    "ASIN": asin,
                    "Box ID": box_id
                })
    
    # Sort by Box ID
    expanded_rows.sort(key=lambda x: x["Box ID"])
    
    # Group by SKU
    sku_groups = {}
    for row in expanded_rows:
        sku = row["SKU"]
        if sku not in sku_groups:
            sku_groups[sku] = {
                "RowNum": row["RowNum"],
                "SKU": sku,
                "ASIN": row["ASIN"],
                "Boxes": []
            }
        sku_groups[sku]["Boxes"].append(row["Box ID"])
    
    # Create page ranges
    groups = []
    current_page = 1
    
    for sku, group_data in sku_groups.items():
        total_boxes = len(group_data["Boxes"])
        start_page = current_page
        end_page = current_page + total_boxes - 1
        
        groups.append({
            "RowNum": group_data["RowNum"],
            "SKU": sku,
            "ASIN": group_data["ASIN"],
            "TotalBoxes": total_boxes,
            "PageRange": (start_page, end_page)
        })
        
        current_page = end_page + 1
    
    logger.info(f"Found {len(groups)} SKU groups")
    for group in groups:
        logger.info(f"Group: {group['SKU']}, ASIN: {group['ASIN']}, Boxes: {group['TotalBoxes']}, Pages: {group['PageRange']}")
    
    return shipment_id, groups

def split_pdf(pdf_path, shipment_id, groups, output_dir=None):
    """
    Split the PDF file based on SKU groupings.
    
    Args:
        pdf_path: Path to the PDF file
        shipment_id: Shipment ID for naming
        groups: List of dictionaries with SKU grouping info
        output_dir: Directory to save the split PDFs (default: shipment_[shipment_id])
    """
    logger.info(f"Processing PDF file: {pdf_path}")
    
    # Create output directory if not specified
    if output_dir is None:
        output_dir = f"shipment_{shipment_id}"
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Open the PDF file
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Error opening PDF file: {e}")
        raise
    
    # Validate that the PDF has the expected number of pages
    total_boxes = sum(group["TotalBoxes"] for group in groups)
    if len(doc) != total_boxes:
        error_msg = f"PDF page count ({len(doc)}) does not match total boxes in CSV ({total_boxes})"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"PDF has {len(doc)} pages, matching {total_boxes} boxes in CSV")
    
    # Split the PDF by SKU groups
    for group in groups:
        sku = group["SKU"]
        asin = group["ASIN"]
        total_boxes = group["TotalBoxes"]
        start_page, end_page = group["PageRange"]
        
        row_num = group["RowNum"]
        output_filename = f"{row_num}_{shipment_id}_{sku}_{asin}_{total_boxes}boxes.pdf"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"Creating PDF for SKU {sku}: {output_path}")
        
        # Create a new PDF for this SKU
        sku_doc = fitz.open()
        
        # Add pages from the original PDF (adjusting for 0-based indexing)
        for page_num in range(start_page - 1, end_page):
            sku_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Save the new PDF
        try:
            sku_doc.save(output_path)
            logger.info(f"Saved {output_path} with {total_boxes} pages")
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise
        finally:
            sku_doc.close()
    
    # Close the original PDF
    doc.close()
    
    logger.info("PDF splitting completed successfully")
    return output_dir

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Split PDF by SKU based on CSV data')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('pdf_file', help='Path to the PDF file')
    parser.add_argument('--output-dir', help='Output directory (default: shipment_[shipment_id])')
    
    args = parser.parse_args()
    
    try:
        # Process the CSV file
        shipment_id, groups = process_csv(args.csv_file)
        
        # Split the PDF file
        output_dir = split_pdf(args.pdf_file, shipment_id, groups, args.output_dir)
        
        logger.info(f"Process completed successfully. Output saved to {output_dir}")
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
