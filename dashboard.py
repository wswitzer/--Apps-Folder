# dashboard.py
import streamlit as st
import json
import pandas as pd

# --- Data Loading ---
# Assume the JSON data is saved in 'analysis_data.json' in the same directory
try:
    with open('data/cross_document_analysis_data.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    st.error("Error: cross_document_analysis_data.json.json not found. Please ensure the JSON data is saved in this file.")
    st.stop() # Stop execution if file not found
except json.JSONDecodeError:
    st.error("Error: Could not decode cross_document_analysis_data.json.json. Please ensure it's valid JSON.")
    st.stop() # Stop execution if JSON is invalid

# Extract main sections for easier access
doc_structure = data.get('document_structure', {})
term_analysis = data.get('terminology_analysis', {})
compliance = data.get('best_practices_compliance', {})
redundancy = data.get('redundancy_and_gaps', {})
recommendations = data.get('recommendations', [])
summary = data.get('summary', "No summary provided.")

# List of document names for selection
doc_names = list(doc_structure.keys())

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Overview",
    "Document Explorer",
    "Terminology Hub",
    "Compliance Dashboard",
    "Redundancy & Gaps",
    "Recommendations"
])

st.sidebar.markdown("---") # Separator
st.sidebar.info("This dashboard visualizes the analysis of your documentation.")

# --- Page Content ---

if page == "Overview":
    st.title("Documentation Analysis Overview")
    st.markdown("### Summary")
    st.write(summary)

    st.markdown("### Key Statistics")
    num_docs = len(doc_names)
    num_terms = len(term_analysis.get('terms', {}))
    num_inconsistencies = len(term_analysis.get('inconsistencies', []))
    num_recommendations = len(recommendations)
    num_compliance_areas = len(compliance)

    col1, col2, col3 = st.columns(3)
    col1.metric("Documents Analyzed", num_docs)
    col2.metric("Unique Terms Tracked", num_terms)
    col3.metric("Terminology Inconsistencies", num_inconsistencies)
    col1.metric("Compliance Areas Checked", num_compliance_areas)
    col2.metric("Recommendations Made", num_recommendations)

elif page == "Document Explorer":
    st.title("Document Explorer")
    selected_doc = st.selectbox("Select a Document", doc_names)

    if selected_doc and selected_doc in doc_structure:
        st.markdown(f"### Details for: `{selected_doc}`")
        doc_data = doc_structure[selected_doc]

        # Display Structure
        st.subheader("Structure")
        cols = st.columns(2)
        cols[0].metric("H1 Headings", doc_data.get('headings', {}).get('H1', 0))
        cols[0].metric("H2 Headings", doc_data.get('headings', {}).get('H2', 0))
        cols[1].metric("Sections", len(doc_data.get('section_lengths', [])))
        avg_len = sum(doc_data.get('section_lengths', [0])) / len(doc_data.get('section_lengths', [1]))
        cols[1].metric("Avg Section Length (Tokens)", f"{avg_len:.0f}")

        flags = {
            "Lists Present": doc_data.get('lists', False),
            "Tables Present": doc_data.get('tables', False),
            "FAQs Present": doc_data.get('faqs', False),
            "Metadata Present": doc_data.get('metadata', False)
        }
        st.write("**Features:**")
        st.json(flags) # Simple way to show boolean flags


        # Display Compliance Status
        st.subheader("Compliance Status")
        compliance_issues = []
        for practice, details in compliance.items():
            is_compliant = False
            reason = "Not explicitly listed as non-compliant"
            # Check if doc is in compliant list
            if selected_doc in details.get('compliant', []):
                is_compliant = True
            # Check if doc is in non-compliant list
            for item in details.get('non_compliant', []):
                if isinstance(item, dict) and item.get('file') == selected_doc:
                    is_compliant = False
                    reason = item.get('reason', 'No specific reason provided.')
                    break
            # Store issue if not compliant
            if not is_compliant:
                compliance_issues.append({"Practice": practice.replace('_', ' ').title(), "Reason": reason})

        if compliance_issues:
            st.warning("This document has compliance issues:")
            df_compliance = pd.DataFrame(compliance_issues)
            st.dataframe(df_compliance, use_container_width=True)
        else:
            st.success("This document appears compliant with all checked best practices.")

        # Display Terms Found (Optional - can be slow if many terms)
        st.subheader("Relevant Terms")
        found_terms = []
        for term, details in term_analysis.get('terms', {}).items():
            if selected_doc in details.get('documents', []):
                found_terms.append(term)
        if found_terms:
            st.write(", ".join(found_terms))
        else:
            st.write("No specific tracked terms were listed for this document.")


elif page == "Terminology Hub":
    st.title("Terminology Hub")

    st.subheader("Glossary")
    glossary = term_analysis.get('glossary', {})
    if glossary:
        df_glossary = pd.DataFrame(glossary.items(), columns=['Term', 'Definition'])
        st.dataframe(df_glossary, use_container_width=True)
    else:
        st.write("No glossary provided.")

    st.subheader("Synonym Map")
    synonyms = term_analysis.get('synonym_map', {})
    if synonyms:
         # Convert dict to list of dicts for DataFrame
        syn_list = [{'Term': k, 'Synonyms': ', '.join(v)} for k, v in synonyms.items()]
        df_synonyms = pd.DataFrame(syn_list)
        st.dataframe(df_synonyms, use_container_width=True)
    else:
        st.write("No synonym map provided.")

    st.subheader("Term Frequency")
    terms_data = term_analysis.get('terms', {})
    if terms_data:
        freq_data = [{'Term': term, 'Frequency': details.get('frequency', 0)} for term, details in terms_data.items()]
        df_freq = pd.DataFrame(freq_data).sort_values(by='Frequency', ascending=False)
        st.dataframe(df_freq, use_container_width=True)
        # Optional: Add a bar chart
        # st.bar_chart(df_freq.set_index('Term'))
    else:
        st.write("No term frequency data provided.")

    st.subheader("Inconsistencies")
    inconsistencies = term_analysis.get('inconsistencies', [])
    if inconsistencies:
        st.warning("The following terminology inconsistencies were noted:")
        df_incons = pd.DataFrame(inconsistencies)
        st.dataframe(df_incons, use_container_width=True)
    else:
        st.success("No terminology inconsistencies listed.")


elif page == "Compliance Dashboard":
    st.title("Best Practices Compliance Dashboard")

    if not compliance:
        st.warning("No compliance data available.")
    else:
        for practice, details in compliance.items():
            practice_name = practice.replace('_', ' ').title()
            with st.expander(f"**{practice_name}**"):
                st.markdown("**Compliant Documents:**")
                compliant_docs = details.get('compliant', [])
                if compliant_docs:
                    st.write(f"`{len(compliant_docs)}` document(s):")
                    # Make list scrollable if long
                    st.markdown(f"<div style='height:100px;overflow-y:scroll;border:1px solid lightgray;padding:5px;'>{'<br>'.join(compliant_docs)}</div>", unsafe_allow_html=True)
                else:
                    st.info("No documents explicitly listed as compliant.")

                st.markdown("**Non-Compliant Documents:**")
                non_compliant_info = details.get('non_compliant', [])
                if non_compliant_info:
                    st.write(f"`{len(non_compliant_info)}` document(s):")
                    # Process non-compliant which might be list of dicts
                    non_compliant_data = []
                    for item in non_compliant_info:
                        if isinstance(item, dict):
                             non_compliant_data.append({'Document': item.get('file'), 'Reason': item.get('reason')})
                        else: # Handle if it's just a list of filenames (though schema suggests dict)
                             non_compliant_data.append({'Document': item, 'Reason': 'N/A'})

                    df_noncompliant = pd.DataFrame(non_compliant_data)
                    st.dataframe(df_noncompliant, use_container_width=True)
                else:
                    st.info("No documents explicitly listed as non-compliant.")


elif page == "Redundancy & Gaps":
    st.title("Redundancy Analysis and Information Gaps")

    st.subheader("Overlapping Topics")
    overlaps = redundancy.get('overlaps', [])
    if overlaps:
        df_overlaps = pd.DataFrame(overlaps)
        df_overlaps['documents'] = df_overlaps['documents'].apply(lambda x: ', '.join(x)) # Make list readable
        st.dataframe(df_overlaps, use_container_width=True)
    else:
        st.info("No specific topic overlaps were identified.")

    st.subheader("Examples of Redundant Content")
    redundant_content = redundancy.get('redundant_content', [])
    if redundant_content:
        st.warning("The following potential redundancies were noted:")
        for item in redundant_content:
            st.markdown(f"- {item}")
    else:
        st.info("No specific examples of redundant content were provided.")

    st.subheader("Identified Information Gaps")
    missing_info = redundancy.get('missing_information', [])
    if missing_info:
        st.warning("The following general information gaps were identified:")
        for item in missing_info:
            st.markdown(f"- {item}")
    else:
        st.info("No specific information gaps were listed.")


elif page == "Recommendations":
    st.title("Recommendations for Improvement")

    if recommendations:
        st.markdown("Based on the analysis, the following actions are recommended:")
        for i, rec in enumerate(recommendations):
            st.markdown(f"{i+1}. {rec}")
    else:
        st.info("No specific recommendations were provided in the data.")