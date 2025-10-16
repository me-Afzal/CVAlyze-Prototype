import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import pdfplumber
from docx import Document
import re
from typing import Dict, List, Optional
import time
import json

# Import your existing functions
from regex import (
    extract_name, extract_email, extract_phone, extract_location,
    extract_skills, extract_education, extract_links, extract_projects,
    extract_certifications, extract_achievements
)

from preprocess import extract_text, clean_text, get_lat_lon

# Configure page
st.set_page_config(
    page_title="CV Analysis Dashboard",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 30px;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stSelectbox > div > div > select {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'selected_locations' not in st.session_state:
    st.session_state.selected_locations = []

def process_uploaded_files(uploaded_files, progress_bar=None, status_text=None) -> pd.DataFrame:
    """Process uploaded CV files (from Streamlit uploader) and return a DataFrame"""
    all_cv_data = []

    for i, uploaded_file in enumerate(uploaded_files):
        if status_text:
            status_text.text(f"Processing {uploaded_file.name}...")

        try:
            # Extract and clean text directly from memory
            text = extract_text(uploaded_file)
            cleaned_text = clean_text(text)

            # Extract all details
            links_data = extract_links(cleaned_text)

            data = {
                "Filename": uploaded_file.name,
                "Name": extract_name(cleaned_text),
                "Email": extract_email(cleaned_text),
                "Phone": extract_phone(cleaned_text),
                "Location": extract_location(cleaned_text),
                "Skills": extract_skills(cleaned_text),
                "Education": extract_education(cleaned_text),
                "LinkedIn": links_data.get("linkedin"),
                "GitHub": links_data.get("github"),
                "Websites": links_data.get("websites"),
                "Projects": extract_projects(cleaned_text),
                "Certifications": extract_certifications(cleaned_text),
                "Achievements": extract_achievements(cleaned_text),
            }

            all_cv_data.append(data)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

        # Update progress bar
        if progress_bar:
            progress_bar.progress((i + 1) / len(uploaded_files))

    # Create DataFrame
    df = pd.DataFrame(all_cv_data)

    # Add coordinates
    if status_text:
        status_text.text("Adding geographical coordinates...")

    if not df.empty and 'Location' in df.columns:
        coordinates = df['Location'].apply(lambda x: pd.Series(get_lat_lon(x) if x else (None, None)))
        df[['Latitude', 'Longitude']] = coordinates

    return df

def create_enhanced_world_map(df, selected_locations=None):
    """Create enhanced interactive world map with candidate bubbles (from second app)"""
    if df.empty:
        return None
    
    # Filter dataframe for valid coordinates
    map_df = df.dropna(subset=['Latitude', 'Longitude']).copy()
    
    if map_df.empty:
        st.warning("No location data available for mapping.")
        return None
    
    # Group by location and count candidates
    location_counts = map_df.groupby(['Location', 'Latitude', 'Longitude']).size().reset_index(name='Count')
    
    # Filter if specific locations are selected
    if selected_locations:
        location_counts = location_counts[location_counts['Location'].isin(selected_locations)]
    
    # Create the map
    fig = go.Figure()
    
    # Add bubble markers
    fig.add_trace(go.Scattergeo(
        lon=location_counts['Longitude'],
        lat=location_counts['Latitude'],
        text=location_counts['Location'],
        mode='markers+text',
        marker=dict(
            size=location_counts['Count'] * 10 + 20,  # Scale bubble size
            color=location_counts['Count'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Candidate Count"),
            line=dict(width=1, color='white'),
            sizemode='diameter'
        ),
        textposition="top center",
        customdata=location_counts['Count'],
        hovertemplate='<b>%{text}</b><br>' +
                      'Candidates: %{customdata}<br>' +
                      '<extra></extra>',
        textfont=dict(size=12, color='darkblue')
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Global Distribution of Candidates',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular',
            bgcolor='rgba(0,0,0,0)',
            showland=True,
            landcolor='lightgray',
            showocean=True,
            oceancolor='lightblue'
        ),
        height=600,
        margin=dict(r=0, t=50, l=0, b=0)
    )
    
    return fig, location_counts

def create_location_bar_chart(df, selected_locations=None):
    """Create bar chart showing candidate count by location"""
    if df.empty:
        return None
    
    # Filter data if locations are selected
    if selected_locations:
        filtered_df = df[df['Location'].isin(selected_locations)]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return None
    
    # Get location counts
    location_counts = filtered_df['Location'].value_counts().head(10)
    
    # Create horizontal bar chart
    fig_bar = px.bar(
        x=location_counts.values,
        y=location_counts.index,
        orientation='h',
        title="Top 10 Locations by Candidate Count",
        labels={'x': 'Number of Candidates', 'y': 'Location'},
        color=location_counts.values,
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(height=400, showlegend=False)
    return fig_bar

def display_candidate_info_modal(candidate_data):
    """Display detailed candidate information in a modal-like format"""
    st.markdown("---")
    st.subheader(f"📋 {candidate_data.get('Name', 'Unknown Candidate')}")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Contact & Basic Info", "Skills & Education", "Projects & Experience", "Links & Files"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Contact Information**")
            st.write(f"📧 **Email:** {candidate_data.get('Email', 'Not provided')}")
            st.write(f"📱 **Phone:** {candidate_data.get('Phone', 'Not provided')}")
            st.write(f"📍 **Location:** {candidate_data.get('Location', 'Not provided')}")
        
        with col2:
            st.write("**File Information**")
            st.write(f"📄 **Filename:** {candidate_data.get('Filename', 'Not provided')}")
    
    with tab2:
        st.write("**Skills**")
        skills = candidate_data.get('Skills', 'Not provided')
        if skills and skills != 'Not provided':
            st.write(skills)
        else:
            st.info("No skills information available")
        
        st.write("**Education**")
        education = candidate_data.get('Education', 'Not provided')
        if education and education != 'Not provided':
            st.write(education)
        else:
            st.info("No education information available")
    
    with tab3:
        st.write("**Projects**")
        projects = candidate_data.get('Projects', 'Not provided')
        if projects and projects != 'Not provided':
            st.write(projects)
        else:
            st.info("No projects information available")
        
        st.write("**Certifications**")
        certifications = candidate_data.get('Certifications', 'Not provided')
        if certifications and certifications != 'Not provided':
            st.write(certifications)
        else:
            st.info("No certifications information available")
        
        st.write("**Achievements**")
        achievements = candidate_data.get('Achievements', 'Not provided')
        if achievements and achievements != 'Not provided':
            st.write(achievements)
        else:
            st.info("No achievements information available")
    
    with tab4:
        st.write("**Professional Links**")
        st.write(f"💼 **LinkedIn:** {candidate_data.get('LinkedIn', 'Not provided')}")
        st.write(f"💻 **GitHub:** {candidate_data.get('GitHub', 'Not provided')}")
        st.write(f"🌐 **Website:** {candidate_data.get('Websites', 'Not provided')}")

def display_candidates_table(df: pd.DataFrame, show_details=True):
    """Display candidates in a table with expandable details"""
    if df.empty:
        st.info("No candidates to display.")
        return
    
    st.write(f"**Total Candidates: {len(df)}**")
    
    # Create a summary table first
    summary_columns = ['Name', 'Email', 'Phone', 'Location']
    available_columns = [col for col in summary_columns if col in df.columns]
    
    if available_columns:
        summary_df = df[available_columns].copy()
        summary_df.index = range(1, len(summary_df) + 1)
        
        st.dataframe(summary_df, width='stretch')
        
        if show_details:
            st.write("**Click on a candidate below to view detailed information:**")
            
            # Create expandable sections for each candidate
            for idx, (_, candidate) in enumerate(df.iterrows()):
                candidate_name = candidate.get('Name', f'Candidate {idx + 1}')
                candidate_location = candidate.get('Location', 'Unknown Location')
                
                with st.expander(f"{idx + 1}. {candidate_name} - {candidate_location}"):
                    display_candidate_info_modal(candidate)

def main():
    st.title("📄 CV Analysis Dashboard")
    
    # Create main tabs
    tab1, tab2 = st.tabs(["📤 Upload CVs", "📊 Analysis & Visualization"])
    
    with tab1:
        st.header("Upload and Process CV Files")
        
        st.subheader("Upload Multiple CV Files")
        st.info("Select multiple PDF, DOCX, or TXT files by holding Ctrl/Cmd while clicking")
        
        uploaded_files = st.file_uploader(
            "Choose CV files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="You can upload multiple CV files at once"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files selected")
            
            # Show file preview
            with st.expander("📋 Preview Selected Files", expanded=False):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. **{file.name}** ({file.size / 1024:.1f} KB)")
            
            # Process button
            if st.button("🔄 Process Uploaded Files", type="primary"):
                st.info(f"Processing {len(uploaded_files)} uploaded CV files...")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process uploaded files
                with st.spinner("Processing uploaded CVs..."):
                    df = process_uploaded_files(uploaded_files, progress_bar, status_text)
                    st.session_state.df = df
                    st.session_state.processing_complete = True
                
                status_text.text("✅ Processing complete!")
                progress_bar.empty()
                time.sleep(1)
                status_text.empty()
                
                st.success(f"Successfully processed {len(df)} CVs!")
                st.info("🔄 Go to the 'Analysis & Visualization' tab to explore your data.")
        
        # Display processing results
        if st.session_state.df is not None and not st.session_state.df.empty:
            st.markdown("---")
            st.header("📊 Processing Summary")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total CVs", len(st.session_state.df))
            
            with col2:
                valid_emails = st.session_state.df['Email'].notna().sum()
                st.metric("Valid Emails", valid_emails)
            
            with col3:
                valid_phones = st.session_state.df['Phone'].notna().sum()
                st.metric("Valid Phones", valid_phones)
            
            with col4:
                valid_locations = st.session_state.df['Location'].notna().sum()
                st.metric("Valid Locations", valid_locations)
            
            # Clear data option
            if st.button("🗑️ Clear All Data", help="Clear all processed data and start over"):
                st.session_state.df = None
                st.session_state.processing_complete = False
                st.session_state.selected_locations = []
                st.rerun()
    
    with tab2:
        st.header("Data Analysis & Geographical Visualization")
        
        if st.session_state.df is None or st.session_state.df.empty:
            st.warning("⚠️ No data available. Please upload and process CVs first in the 'Upload CVs' tab.")
            return
        
        df = st.session_state.df
        
        # Check for location data
        location_data = df.dropna(subset=['Latitude', 'Longitude'])
        
        if location_data.empty:
            st.error("❌ No geographical data available. Make sure your CVs contain location information.")
            # Still show table without map
            st.subheader("📋 All Candidates")
            display_candidates_table(df)
            return
        
        # Enhanced location filter (from second app)
        st.subheader("🔍 Location Filter")
        all_locations = sorted(location_data['Location'].dropna().unique())
        
        selected_locations = st.multiselect(
            "Select locations to filter candidates:",
            options=all_locations,
            default=[],
            help="Select one or more locations to filter candidates. Leave empty to show all."
        )
        
        # Update session state
        st.session_state.selected_locations = selected_locations
        
        # Create layout for map and charts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🗺️ Global Distribution Map")
            # Create and display enhanced world map
            map_result = create_enhanced_world_map(df, selected_locations)
            if map_result:
                fig_world, location_counts = map_result
                st.plotly_chart(fig_world, use_container_width=True)
                st.info("💡 **Tip:** Bubble size represents the number of candidates in each location. "
                       "Use the dropdown above to filter by location.")
        
        with col2:
            st.subheader("📊 Location Statistics")
            
            # Show bar chart instead of text statistics
            fig_bar = create_location_bar_chart(df, selected_locations)
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Summary metrics
            if selected_locations:
                filtered_df = df[df['Location'].isin(selected_locations)]
                st.metric("Filtered Candidates", len(filtered_df))
                st.metric("Selected Locations", len(selected_locations))
            else:
                st.metric("Total Candidates", len(df))
                st.metric("Unique Locations", df['Location'].nunique())
            
            # Export options
            filtered_df = df[df['Location'].isin(selected_locations)] if selected_locations else df
            if not filtered_df.empty:
                st.markdown("---")
                st.subheader("📥 Export Data")
                
                export_df = filtered_df[['Name', 'Email', 'Phone', 'Location', 'Skills', 'Education']].copy()
                csv_data = export_df.to_csv(index=False)
                
                filename = "filtered_candidates.csv" if selected_locations else "all_candidates.csv"
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
        
        # Candidates table section
        st.markdown("---")
        if selected_locations:
            filtered_df = df[df['Location'].isin(selected_locations)]
            st.subheader(f"📋 Candidates in Selected Locations ({len(filtered_df)} found)")
            
            if not filtered_df.empty:
                display_candidates_table(filtered_df, show_details=True)
            else:
                st.info("No candidates found in selected locations.")
        else:
            st.subheader("📋 All Candidates")
            display_candidates_table(df, show_details=True)

if __name__ == "__main__":
    main()