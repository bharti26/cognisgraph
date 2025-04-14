import streamlit as st

def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown("""
    <style>
        /* General styling */
        .stApp {
            font-family: 'Inter', sans-serif;
        }
        
        /* Answer section styling */
        .answer-section {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .answer-section h3 {
            color: #1f77b4;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        /* Explanation section styling */
        .explanation-section {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .explanation-section h3 {
            color: #1f77b4;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        
        /* Metric styling */
        .metric-container {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        
        /* Graph styling */
        .graph-container {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        /* Document viewer styling */
        .document-viewer {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        /* Highlight styling */
        .highlight {
            background-color: #ffd54f;
            padding: 0 2px;
            border-radius: 2px;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #1f77b4;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: 500;
            transition: background-color 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #145c8e;
        }
        
        /* Input styling */
        .stTextInput>div>div>input {
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            padding: 10px;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #1f77b4;
        }
        
        /* Metric value styling */
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #1f77b4;
        }
        
        /* Metric label styling */
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        /* Progress bar styling */
        .stProgress>div>div>div>div {
            background-color: #1f77b4;
        }
        
        /* Tooltip styling */
        .tooltip {
            position: relative;
            display: inline-block;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
    """, unsafe_allow_html=True) 