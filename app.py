import streamlit as st
import pdfplumber
import re

# Function to extract totals from PDF
def extract_totals_from_pdf(pdf_file):
    total_sum = 0
    page_totals = []  # List to store amounts from each page
    missing_pages = []  # List to store pages where no amount was found
    image_pages = []  # List to store pages with images or no text
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                # If no text is found, consider it as an image page
                image_pages.append(page_num)
                continue  # Skip processing this page

            # Search for any of the labels followed by a number
            match = re.search(r'(Montant total \(TTC\)|Prix|Montant TTC|Prix TTC|Montant de la transaction \(TTC\)|Montant du voyage|Total)[\s:]*([0-9,]+(?:\.[0-9]{1,2})?)', text)
            if match:
                # Extract the matched amount and convert it to float
                amount_str = match.group(2).replace(',', '.')  # Replace comma with dot for float conversion
                amount = float(amount_str)
                total_sum += amount
                page_totals.append((page_num, amount))  # Append page number and amount
            else:
                missing_pages.append(page_num)  # Append page number where no match is found
    
    return total_sum, page_totals, missing_pages, image_pages

# Streamlit app
st.title("Invoice Total Summation App")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file containing invoices", type=["pdf"])

# Process the file if uploaded
if uploaded_file is not None:
    st.info("Processing your file...")
    try:
        total, page_totals, missing_pages, image_pages = extract_totals_from_pdf(uploaded_file)
        
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
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
