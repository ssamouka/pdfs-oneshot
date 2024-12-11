import streamlit as st
import pdfplumber
import re
import pandas as pd
import io
from datetime import datetime

# Function to classify the document type
def classify_document(text):
    text_lower = text.lower()
    
    # Taxi services
    if "g7" in text_lower or "uber" in text_lower or "bolt" in text_lower or "cabify" in text_lower:
        return "Taxi Receipt"
    
    # Train bookings
    elif ("train" in text_lower or "voyage" in text_lower or "billet" in text_lower or 
          "sncf" in text_lower or "tgv" in text_lower or "intercités" in text_lower):
        return "Train Booking"
    
    # Plane tickets
    elif ("flight" in text_lower or "boarding pass" in text_lower or "vol" in text_lower or 
          "carte d'embarquement" in text_lower or "avion" in text_lower):
        return "Plane Ticket"
    
    # Public transport (added Navigo and Trajets)
    elif ("metro" in text_lower or "métro" in text_lower or "bus" in text_lower or "ticket de transport" in text_lower or 
          "tram" in text_lower or "tramway" in text_lower or "navigo" in text_lower or "trajets" in text_lower):
        return "Public Transport Ticket"
    
    # Boat/Ferry
    elif ("boat" in text_lower or "ferry" in text_lower or "ferries" in text_lower or 
          "bateau" in text_lower or "navette" in text_lower):
        return "Boat/Ferry"
    
    # Parking
    elif ("paybyphone" in text_lower or "indigo" in text_lower or "parc" in text_lower or 
          "stationnement" in text_lower or "parking" in text_lower or "apark" in text_lower):
        return "Parking Receipt"
    
    # Péage (Toll)
    elif ("ulys" in text_lower or "vinci" in text_lower or "peage" in text_lower or 
          "toll" in text_lower or "péage" in text_lower or "autoroute" in text_lower):
        return "Péage Receipt"
    
    # Essence (Fuel)
    elif ("total" in text_lower or "e.leclerc" in text_lower or "carrefour" in text_lower or 
          "auchan" in text_lower or "essence" in text_lower or "fuel" in text_lower):
        return "Essence Receipt"
    
    # Unknown
    else:
        return "Unknown"

# Function to extract totals from PDF
def extract_totals_from_pdf(pdf_file):
    total_sum = 0
    page_totals = []  # List to store amounts from each page
    missing_pages = []  # List to store pages where no amount was found
    image_pages = []  # List to store pages with images or no text
    page_data = []  # List to store data for CSV

    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                # If no text is found, consider it as an image page
                image_pages.append(page_num)
                page_data.append([page_num, "", "À vérifier", "Page contains an image or non-text content", "Unknown", False])
                continue  # Skip processing this page

            # Classify the document type
            doc_type = classify_document(text)
            
            # Search for the total amount paid (in French and English)
            match = re.search(r'(Montant total \(TTC\)|Prix|Montant TTC|Prix TTC|Montant du voyage|Total|Total voyageur \(trajet \+ options\)|NET A PAYER TTC)[\s:]*([0-9,]+(?:\.[0-9]{1,2})?)', text)
            if match:
                # Extract the matched amount and convert it to float
                amount_str = match.group(2).replace(',', '.')  # Replace comma with dot for float conversion
                amount = float(amount_str)
                total_sum += amount
                page_data.append([page_num, f"€{amount:,.2f}", "OK", "", doc_type, False])
                page_totals.append((page_num, amount))  # Append page number and amount
            else:
                missing_pages.append(page_num)  # Append page number where no match is found
                page_data.append([page_num, "", "À vérifier", "No amount found", doc_type, False])
    
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
        
        # Create a DataFrame from the page_data with updated column names
        df = pd.DataFrame(page_data, columns=["Page", "Montant", "Montant OK?", "Justif à vérifier pourquoi?", "Type de dépense", "Doublons?"])
        
        # Identify duplicates based on Amount and Document Type
        duplicate_mask = df.duplicated(subset=["Montant", "Type de dépense"], keep=False)
        df["Doublons?"] = duplicate_mask

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
        
        # Highlight duplicates in the app
        if duplicate_mask.any():
            st.warning("The following rows are potential duplicates and need to be checked manually:")
            st.dataframe(df[df["Doublons?"]])
        
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
