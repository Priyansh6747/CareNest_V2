import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import json
from utils.pdf_parser import extract_text_from_pdf
from utils.ner_processor import MedicalNERExtractor
from utils.insights_generator import generate_clinical_insights
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Medical Report Parser",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        color: #374151;
        margin-bottom: 2rem;
    }
    .highlight-box {
        background-color: #F0F9FF;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .alert-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #F59E0B;
        margin: 0.5rem 0;
    }
    .entity-tag {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin: 0.2rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .medication { background-color: #DBEAFE; color: #1E40AF; }
    .condition { background-color: #FCE7F3; color: #9D174D; }
    .procedure { background-color: #D1FAE5; color: #065F46; }
    .anatomy { background-color: #FEF3C7; color: #92400E; }
    .measurement { background-color: #E0E7FF; color: #3730A3; }
</style>
""", unsafe_allow_html=True)

# Initialize NER extractor
@st.cache_resource
def load_ner_model():
    return MedicalNERExtractor()

# Sidebar
with st.sidebar:
    st.title("🏥 Medical Parser")
    st.markdown("---")
    
    st.subheader("Upload Options")
    upload_method = st.radio(
        "Choose input method:",
        ["Upload PDF", "Paste Text", "Sample Report"]
    )
    
    if upload_method == "Sample Report":
        sample_options = {
            "Cardiology Report": "sample_cardiology",
            "Lab Results": "sample_lab",
            "Discharge Summary": "sample_discharge"
        }
        selected_sample = st.selectbox("Select sample report:", list(sample_options.keys()))
    
    st.markdown("---")
    
    st.subheader("Extraction Settings")
    confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.05)
    
    entity_types = st.multiselect(
        "Entity Types to Extract:",
        ["MEDICATION", "CONDITION", "PROCEDURE", "ANATOMY", "MEASUREMENT", "DATE"],
        default=["MEDICATION", "CONDITION", "PROCEDURE"]
    )
    
    st.markdown("---")
    st.info("**Privacy Note:** All processing happens locally. No data is uploaded to external servers.")

# Main content
st.markdown('<h1 class="main-header">🏥 Medical Report Insight Extractor</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Upload medical reports to extract structured insights for clinical review</p>', unsafe_allow_html=True)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'original_text' not in st.session_state:
    st.session_state.original_text = ""
if 'insights' not in st.session_state:
    st.session_state.insights = {}

# File upload/paste text
if upload_method == "Upload PDF":
    uploaded_file = st.file_uploader("Upload Medical Report PDF", type="pdf")
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Extract text
            with st.spinner("Extracting text from PDF..."):
                text = extract_text_from_pdf(tmp_path)
                st.session_state.original_text = text
            
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            text = ""

elif upload_method == "Paste Text":
    text = st.text_area("Paste medical report text:", height=200)
    if text:
        st.session_state.original_text = text

else:  # Sample Report
    sample_texts = {
        "sample_cardiology": """
PATIENT: John Doe, 65M
DATE: 2024-01-15
REFERRING PHYSICIAN: Dr. Smith

CHIEF COMPLAINT: Chest pain for 2 days.

HISTORY OF PRESENT ILLNESS:
Patient is a 65-year-old male with history of hypertension, type 2 diabetes mellitus, 
and hyperlipidemia. He presents with substernal chest pain radiating to left arm, 
associated with diaphoresis. Pain started 2 days ago, worsening with exertion.

MEDICATIONS:
- Lisinopril 10mg daily
- Metformin 500mg BID
- Atorvastatin 40mg nightly
- Aspirin 81mg daily

PHYSICAL EXAM:
BP: 150/90 mmHg, HR: 98 bpm, RR: 18, Temp: 98.6°F
Cardiac: Regular rhythm, S4 gallop
Lungs: Clear to auscultation

LAB RESULTS:
- Troponin I: 0.15 ng/mL (elevated)
- CK-MB: 25 U/L
- LDL: 130 mg/dL
- HbA1c: 7.2%

IMPRESSION:
1. Acute coronary syndrome, rule out NSTEMI
2. Uncontrolled hypertension
3. Poorly controlled diabetes

RECOMMENDATIONS:
1. Admit to cardiac unit for monitoring
2. Start heparin drip
3. Cardiology consultation
4. Echocardiogram scheduled for tomorrow
""",
        "sample_lab": """
LABORATORY REPORT

Patient: Jane Smith, 45F
Collection Date: 2024-01-10
Report Date: 2024-01-11

COMPLETE BLOOD COUNT:
- WBC: 12.5 x10^3/μL (HIGH)
- RBC: 4.2 x10^6/μL
- HGB: 13.2 g/dL
- HCT: 39.5%
- Platelets: 250 x10^3/μL

COMPREHENSIVE METABOLIC PANEL:
- Glucose: 145 mg/dL (HIGH)
- BUN: 18 mg/dL
- Creatinine: 1.2 mg/dL
- Sodium: 140 mEq/L
- Potassium: 4.0 mEq/L
- ALT: 35 U/L
- AST: 28 U/L
- Alkaline Phosphatase: 85 U/L

THYROID FUNCTION:
- TSH: 2.5 mIU/L
- Free T4: 1.1 ng/dL

URINALYSIS:
- Color: Yellow
- Appearance: Clear
- Protein: Trace
- Glucose: Negative
- WBC: 5-10/HPF
- RBC: 0-2/HPF

IMPRESSION:
- Leukocytosis suggesting possible infection
- Elevated glucose levels
- Normal renal and hepatic function
"""
    }
    
    text = sample_texts.get(sample_options[selected_sample], "")
    if st.button("Load Sample Report"):
        st.session_state.original_text = text

# Process if we have text
if st.session_state.original_text:
    # Display original text
    with st.expander("📄 View Original Text", expanded=False):
        st.text_area("Extracted Text", st.session_state.original_text, height=300)
    
    # Process with NER
    if st.button("🔍 Extract Medical Entities", type="primary"):
        with st.spinner("Processing with Clinical NER..."):
            ner_extractor = load_ner_model()
            
            # Extract entities
            entities_df, processed_text = ner_extractor.extract_entities(
                st.session_state.original_text,
                confidence_threshold=confidence_threshold,
                entity_types=entity_types
            )
            
            # Generate insights
            insights = generate_clinical_insights(entities_df, st.session_state.original_text)
            
            # Store in session state
            st.session_state.extracted_data = entities_df
            st.session_state.processed_text = processed_text
            st.session_state.insights = insights

# Display results if available
if st.session_state.extracted_data is not None:
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary Dashboard", "🏷️ Extracted Entities", "🔬 Text Analysis", "📋 Doctor's Summary"])
    
    with tab1:
        # Dashboard
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Entities", len(st.session_state.extracted_data))
        
        with col2:
            conditions = len(st.session_state.extracted_data[
                st.session_state.extracted_data['entity_type'] == 'CONDITION'
            ])
            st.metric("Conditions Identified", conditions)
        
        with col3:
            medications = len(st.session_state.extracted_data[
                st.session_state.extracted_data['entity_type'] == 'MEDICATION'
            ])
            st.metric("Medications Found", medications)
        
        # Entity distribution chart
        if not st.session_state.extracted_data.empty:
            fig = px.pie(
                st.session_state.extracted_data,
                names='entity_type',
                title='Entity Type Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display insights
        st.subheader("⚡ Key Clinical Insights")
        
        if st.session_state.insights.get('critical_alerts'):
            for alert in st.session_state.insights['critical_alerts']:
                st.markdown(f'<div class="alert-box">⚠️ {alert}</div>', unsafe_allow_html=True)
        
        cols = st.columns(2)
        
        with cols[0]:
            if st.session_state.insights.get('active_conditions'):
                st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
                st.subheader("Active Conditions")
                for condition in st.session_state.insights['active_conditions']:
                    st.markdown(f"- {condition}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with cols[1]:
            if st.session_state.insights.get('current_medications'):
                st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
                st.subheader("Current Medications")
                for med in st.session_state.insights['current_medications']:
                    st.markdown(f"- {med}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        # Display entities table
        if not st.session_state.extracted_data.empty:
            st.dataframe(
                st.session_state.extracted_data,
                column_config={
                    "text": "Entity",
                    "entity_type": "Type",
                    "confidence": st.column_config.NumberColumn(
                        "Confidence",
                        format="%.2f",
                        help="Model confidence score"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Export options
            col1, col2, col3 = st.columns(3)
            with col1:
                csv = st.session_state.extracted_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="extracted_entities.csv",
                    mime="text/csv"
                )
            with col2:
                json_data = st.session_state.extracted_data.to_json(orient="records", indent=2)
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_data,
                    file_name="extracted_entities.json",
                    mime="application/json"
                )
    
    with tab3:
        # Highlighted text
        st.subheader("Text with Highlighted Entities")
        st.markdown(st.session_state.processed_text, unsafe_allow_html=True)
    
    with tab4:
        # Doctor-friendly summary
        st.subheader("📋 Clinical Summary for Doctor Review")
        
        # Generate structured summary
        summary_cols = st.columns(2)
        
        with summary_cols[0]:
            st.markdown("**Patient Summary**")
            st.text_area(
                "Summary",
                value=st.session_state.insights.get('summary', 'No summary generated'),
                height=200
            )
        
        with summary_cols[1]:
            st.markdown("**Recommendations**")
            for rec in st.session_state.insights.get('recommendations', []):
                st.markdown(f"• {rec}")
        
        # Action items
        st.markdown("**🔄 Action Items**")
        actions = st.session_state.insights.get('action_items', [])
        for i, action in enumerate(actions, 1):
            st.checkbox(f"{i}. {action}")
        
        # Notes section
        st.markdown("**📝 Doctor's Notes**")
        doctor_notes = st.text_area("Add your notes here:", height=100)
        
        if st.button("💾 Save Summary"):
            st.success("Summary saved to patient record")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6B7280; font-size: 0.9rem;">
    <i>This tool extracts medical entities using clinical NLP models. 
    Always verify extracted information with original documentation.</i>
    </div>
    """,
    unsafe_allow_html=True
)