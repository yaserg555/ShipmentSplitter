# PDF Splitter by SKU

This Python script reads a CSV file containing shipment data and splits a provided PDF file into multiple PDFs, grouped by SKU level. The script does not read or analyze the PDF content itself but splits strictly by pages, assuming each page corresponds to one box. All business logic and sorting rely solely on the CSV data.

## Prerequisites

- Python 3.6 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Single Shipment Processing

```bash
python pdf_splitter.py sample_shipment.csv sample_labels.pdf [--output-dir OUTPUT_DIR]
```

#### Arguments:

- `csv_file`: Path to the CSV file containing shipment data
- `pdf_file`: Path to the PDF file to split
- `--output-dir`: (Optional) Output directory for the split PDFs. Default is `shipment_[ShipmentID]`

#### Example:

```bash
python pdf_splitter.py sample_shipment.csv sample_labels.pdf
```

### Batch Processing

For processing multiple shipments at once, use the batch processing script:

```bash
python process_all.py DIRECTORY_PATH
```

Or use the provided batch file (Windows):

```
process_all_shipments.bat "DIRECTORY_PATH"
```

#### Example:

```bash
python process_all.py "E:\Developing\ShipmentSplitter\test 2"
```

The batch processor will:
1. Find all CSV files in the specified directory
2. Extract the shipment ID from each CSV filename
3. Find matching PDF files with the same shipment ID
4. Process each CSV-PDF pair and create the split PDFs

## CSV Format Requirements

The script dynamically locates the header row containing these columns:
- SKU
- ASIN
- Total boxes
- Box ID

The script also extracts the Shipment ID from the CSV file.

## How It Works

1. **CSV Parsing and Preparation**:
   - Dynamically locates the header row
   - Extracts the Shipment ID
   - Sorts data by Box ID

2. **Grouping Logic (by SKU)**:
   - Groups rows by SKU
   - Records ASIN, total number of boxes, and page range for each SKU

3. **PDF Splitting Logic**:
   - Splits the PDF strictly by page numbers determined from CSV grouping
   - Does NOT read or analyze PDF content
   - Assumes PDF pages correspond exactly to the sorted Box IDs from CSV

4. **Output Structure**:
   - Creates an output directory named using the Shipment ID
   - Saves each PDF with naming convention: `[RowNum]_[ShipmentID]_[SKU]_[ASIN]_[TotalBoxes]boxes.pdf`

## Key Assumptions

- Box IDs in CSV are incrementally sorted within each SKU
- The PDF file has exactly the same number of pages as the total boxes listed in CSV
- The PDF pages correspond exactly (in ascending order) to the sorted Box IDs from CSV

## Error Handling

The script includes robust error handling for:
- Missing or malformed CSV files
- PDF page count mismatches
- Missing required columns
- File access issues

## Sample Output Structure

```
shipment_FBA111111111/
├── 1_FBA111111111_SKU1_B0111111_3boxes.pdf
├── 2_FBA111111111_SKU2_B0222222_15boxes.pdf
└── ...
