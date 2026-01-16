  ---
  name: read-intco-invoice
  description: Extract data from INTCO Medical invoices. Use when processing PDF invoices from INTCO.
  ---

  # Reading INTCO Invoices

## Usage

```
/read-intco-invoice [path]
```

- `path`: Path to a PDF file or glob pattern (e.g., `*.pdf`, `invoices/*.pdf`)
- If no path provided, process all `*.pdf` files in current directory

## Behavior

This skill extracts product line items from INTCO Medical proforma invoices and creates an Excel file with the following columns:

| Column | Description |
|--------|-------------|
| PO Number | Purchase Order number (e.g., INUSBG06.26) |
| PI Number | Proforma Invoice number (e.g., IN25026696) |
| Item Number | Product SKU/code (e.g., 534024) |
| Item Name | Full product description |
| Unit Price (USD) | Price per carton |
| Cases (CTN) | Number of cartons ordered |
| Pcs per CTN | Pieces per carton (from packaging info) |
| Total Pcs | Calculated: Cases × Pcs per CTN |
| Total Price (USD) | Calculated: Cases × Unit Price |

## Output

- **Location**: Same folder as the source PDF
- **Filename**: Based on PO number range extracted from the invoice (e.g., `INUSBG06.26-08.26.xlsx`)
- **Format**: One row per product line item per invoice (if a PDF contains 3 invoices with 4 products each = 12 rows)

## Instructions for Claude

When this skill is invoked:

1. **Find PDF files**: Use the provided path or glob pattern. If no argument, use `*.pdf` in current directory.

2. **Read each PDF**: Use the Read tool to view the PDF content.

3. **Extract data from each invoice page**:
   - PO Number (e.g., "PO Number: INUSBG06.26")
   - PI Number (e.g., "PI Number: IN25026696")
   - For each product row in the commodity table:
     - Item number (6-digit code at end of description, e.g., 534024)
     - Item name (full commodity description without the item number)
     - Unit price
     - Quantity (cases/CTN)
     - Pcs per carton (from "Packaging" field or product description, typically 200)

4. **Create Excel file** using Python with openpyxl:
   ```python
   from openpyxl import Workbook
   from openpyxl.styles import Font, Alignment

   wb = Workbook()
   ws = wb.active
   ws.title = "Invoice Data"

   headers = ["PO Number", "PI Number", "Item Number", "Item Name",
              "Unit Price (USD)", "Cases (CTN)", "Pcs per CTN", "Total Pcs", "Total Price (USD)"]
   # ... add data rows with calculated Total Pcs and Total Price
   ```

5. **Determine output filename**:
   - Extract all unique PO numbers from the data
   - Sort them and create a range (e.g., INUSBG06.26, INUSBG07.26, INUSBG08.26 → "INUSBG06.26-08.26")
   - If PO numbers have different prefixes, use full range (e.g., "INUSBG06.26-INUSBG08.26")
   - If only one PO, use just that number (e.g., "INUSBG06.26.xlsx")

6. **Save the file** in the same directory as the source PDF.

7. **Report results**: Show summary of extracted data (number of invoices, products, total value).

## Example

```
> /read-intco-invoice "invoices/*.pdf"

Processing 2 PDF files...

✓ IN25026696 IN25026697 IN25026698.pdf
  - 3 invoices, 12 product lines
  - Total: 9,228 cases, $261,152.40

✓ IN25030001.pdf
  - 1 invoice, 6 product lines
  - Total: 500 cases, $15,000.00

Created:
- invoices/INUSBG06.26-08.26.xlsx
- invoices/INUSBG10.26.xlsx
```