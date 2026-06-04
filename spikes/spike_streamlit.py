import streamlit as st

st.set_page_config(layout="wide")

st.title("mein erster Streamlit-test < Angular/react")
name = st.selectbox(
    "wähle einen Ticker", 
    ["AAPL", "MSFT", "SAP.DE"])
st.write("Du hast gewählt:", name)

st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])

with col1:

    name2 = st.selectbox(

        "Wähle einen Ticker",

        ["AAPL", "MSFT", "SAP.DE"]

    )

with col2:
    st.write(name2)
# starten mit streamlit run spike_streamlit.py