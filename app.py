import streamlit as st
import pdfplumber
import re
import pandas as pd
import io
import hashlib

# Function to calculate hash of a string
def calculate_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# Function to classify the document type
def classify_document(text):
    if "train" in text.lower() or "voyage" in text.lower():
        return "Train Booking"
    elif "flight" in text.lower() or "boarding pass" in text.lower():
        return "Plane Ticket"
    elif "hotel" in text.lower():
        return "Hotel Booking"
    elif "metro" in text.lower() or "bus" in text.lower():
        return "Public Transport Ticket"
    else:
        return "Unknown"

# Function to extract totals from PDF
def extract_totals_from_pdf(pdf_file):
    total_sum = 0
    page_totals = []  # List to store amounts from each page
    missing_pages = []  # List to store pages where no amount was found
    image_pages = []  # List to store pages with images or no text
    page_data = []  # List to store data for CSV
    seen_hashes = set()  # To detect duplicate pages
    
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                # If no text is found, consider it as an image page
                image_pages.append(page_num)
                page_data.append([page_num, "", "À vérifier", "Page contains an image or non-text content", "No", "Unknown"])
                continue  # Skip processing this page
            
            # Check for duplicates
            page_hash = calculate_hash(text)
            if page_hash in seen_hashes:
                page_data.append([page_num, "", "À vérifier", "Duplicate page", "Yes", classify_document(text)])
                continue
            seen_hashes.add(page_hash)
            
            # Search for any of the labels followed by a number
            match = re.search(r'(Montant total \(TTC\)|Prix|Montant TTC|Prix TTC|Montant du voyage|Total)[\s:]*([0-9,]+(?:\.[0-9]{1,2})?)', text)
            if match:
                # Extract the matched amount and convert it to float
                amount_str = match.group(2).replace(',', '.')  # Replace comma with dot for float conversion
                amount = float(amount_str)
                total_sum += amount
                page_data.append([page_num, f"€{amount:,.2f}", "OK", "", "No", classify_document(text)])
                page_totals.append((page_num, amount))  # Append page number and amount
            else:
                missing_pages.append(page_num)  # Append page number where no match is found
                page_data.append([page_num, "", "À vérifier", "No amount found", "No", classify_document(text)])
    
    return total_sum, page_totals, missing_pages, image_pages, page_data

# Streamlit app
st.title("Invoice Total Summation App")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file containing invoices", type=["pdf"])

# Process the file if uploaded
if uploaded_file is not None:
    st.info("Processing your file...")
    try:
        total, page_totals, missing_pages, image_pages, page_data = extract_totals_from_pdf(uploaded_file)
        
        # Display the totals for each page
        st.write("Amounts extracted from each page:")
        for page_num, amount in page_totals:
            st.write(f"Page {page_num}: €{amount:,.2f}")  # Use Euro symbol for each page amount
        
        # Display the total sum in euros
        st.success(f"The total sum of all invoices in this document is: €{total:,.2f}")
        
        # Display pages where no amount was found
        if missing_pages:
            st.warning("No amount was found on the following pages:")
            for page_num in missing_pages:
                st.write(f"Page {page_num}")
        
        # Display pages with images or no text
        if image_pages:
            st.warning("The following pages contain images or non-text content and could not be processed:")
            for page_num in image_pages:
                st.write(f"Page {page_num}")
        
        # If no pages are missing or have images, show success message
        if not missing_pages and not image_pages:
            st.info("All pages contained a valid amount.")
        
        # Create a DataFrame from the page_data for CSV export
        df = pd.DataFrame(page_data, columns=["Page", "Amount", "OK?", "Raison de refus", "Duplicate?", "Document Type"])
        
        # Display the data in a table format
        st.dataframe(df)
        
        # Convert the DataFrame to a CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        # Provide a download button
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="invoice_totals.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
