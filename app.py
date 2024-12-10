import streamlit as st
import pdfplumber
import re

# Function to extract totals from PDF
def extract_totals_from_pdf(pdf_file):
    total_sum = 0
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Extract monetary values using regex
                amounts = re.findall(r'\d+\.\d{2}', text)  # Matches numbers like 123.45
                total_sum += sum(map(float, amounts))  # Convert and sum
    return total_sum

# Streamlit app
st.title("Invoice Total Summation App")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file containing invoices", type=["pdf"])

# Process the file if uploaded
if uploaded_file is not None:
    st.info("Processing your file...")
    try:
        total = extract_totals_from_pdf(uploaded_file)
        st.success(f"The total sum of all invoices in this document is: ${total:,.2f}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
