#!/usr/bin/env python3
"""
Example script demonstrating how to use the PDF Splitter.

This script provides a simple example of how to use the PDF Splitter
with sample data.
"""

import os
from pdf_splitter import process_csv, split_pdf

def main():
    """Run an example of the PDF Splitter."""
    # Sample file paths - replace with actual files for testing
    csv_path = "sample_shipment.csv"
    pdf_path = "sample_labels.pdf"
    
    # Process the CSV file
    shipment_id, groups = process_csv(csv_path)
    
    # Create a custom output directory
    output_dir = f"output_{shipment_id}"
    
    # Split the PDF file
    split_pdf(pdf_path, shipment_id, groups, output_dir)
    
    print(f"Example completed. Check the '{output_dir}' directory for the split PDFs.")

if __name__ == "__main__":
    main()
