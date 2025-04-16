#!/usr/bin/env python3
"""
Batch processing script for PDF Splitter.

This script processes all CSV and PDF files in a specified directory,
matching them by shipment ID and splitting the PDFs accordingly.
"""

import os
import sys
import re
from pdf_splitter import process_csv, split_pdf

def main():
    """Process all shipment files in the specified directory."""
    if len(sys.argv) < 2:
        print("Usage: python process_all.py <directory_path>")
        return 1
    
    directory = sys.argv[1]
    print(f"Processing files in directory: {directory}")
    
    # Get all CSV and PDF files
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    
    print(f"Found {len(csv_files)} CSV files and {len(pdf_files)} PDF files")
    
    # Process each CSV file
    for csv_file in csv_files:
        # Extract shipment ID from CSV filename
        match = re.search(r'(FBA\w+)', csv_file)
        if not match:
            print(f"Could not extract shipment ID from {csv_file}, skipping")
            continue
        
        shipment_id = match.group(1)
        print(f"\nProcessing shipment: {shipment_id}")
        
        # Find matching PDF file
        matching_pdfs = [pdf for pdf in pdf_files if shipment_id in pdf]
        if not matching_pdfs:
            print(f"No matching PDF found for {csv_file}, skipping")
            continue
        
        # Use the first matching PDF
        pdf_file = matching_pdfs[0]
        print(f"Using PDF file: {pdf_file}")
        
        # Full paths
        csv_path = os.path.join(directory, csv_file)
        pdf_path = os.path.join(directory, pdf_file)
        
        try:
            # Process the CSV file
            shipment_id, groups = process_csv(csv_path)
            
            # Create output directory as a subfolder where the files are located
            output_dir = os.path.join(directory, f"shipment_{shipment_id}")
            
            # Split the PDF file
            output_dir = split_pdf(pdf_path, shipment_id, groups, output_dir)
            
            print(f"Successfully processed {csv_file} with {pdf_file}")
            print(f"Output saved to {output_dir}")
        except Exception as e:
            print(f"Error processing {csv_file} with {pdf_file}: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
