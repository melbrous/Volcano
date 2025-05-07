"""
Michael Broussard
CS230-1
Volcano Dataset
Description: This Streamlit app allows users to explore volcanoes around the world
using interactive filters, maps, and charts. The app demonstrates Python features, data
analytics techniques, and visualization tools as required by the CS230 final project rubric.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt

# [PY3] Try/except block in function
@st.cache_data
def load_data():
    """Loads and cleans the volcano dataset."""
    try:
        df = pd.read_csv('volcanoes.csv', encoding='latin1', skiprows=1)
        df.columns = df.columns.str.strip().str.replace('\r', '').str.replace('\ufeff', '')

        # Data cleaning
        df['Elevation (m)'] = pd.to_numeric(df['Elevation (m)'], errors='coerce')
        df.dropna(subset=['Elevation (m)', 'Latitude', 'Longitude'], inplace=True)

        # Clean and standardize volcano types
        df['Primary Volcano Type'] = df['Primary Volcano Type'].str.replace(r'\(.*?\)', '', regex=True)
        df['Primary Volcano Type'] = df['Primary Volcano Type'].str.replace(r'\?', '', regex=True)
        df['Primary Volcano Type'] = df['Primary Volcano Type'].str.strip()

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# Sidebar controls
st.sidebar.title("\U0001F30B Volcano Explorer Controls")
countries = sorted(df['Country'].unique())
types = sorted(df['Primary Volcano Type'].unique())
selected_country = st.sidebar.selectbox("Select Country", countries)
selected_types = st.sidebar.multiselect("Select Volcano Type(s)", types, default=types)
elevation_range = st.sidebar.slider("Elevation Range (m)",
                                    int(df['Elevation (m)'].min()), int(df['Elevation (m)'].max()), (0, 5000))
name_search = st.sidebar.text_input("Search by Volcano Name")

# [PY1] Function with default parameter + [DA4] Filter 1 condition + [DA5] Filter 2+ conditions
def filter_data(country, types, elev_range, name=''):
    """Filters data based on user selections."""
    filtered = df[df['Country'] == country]  # [DA4]
    filtered = filtered[filtered['Primary Volcano Type'].isin(types)]
    filtered = filtered[(filtered['Elevation (m)'] >= elev_range[0]) & (filtered['Elevation (m)'] <= elev_range[1])]  # [DA5]
    if name:
        filtered = filtered[filtered['Volcano Name'].str.contains(name, case=False)]
    return filtered

# [PY1] Called twice
filtered_df = filter_data(selected_country, selected_types, elevation_range, name_search)
default_filtered_df = filter_data(selected_country, selected_types, elevation_range)

# [PY2] Function returns multiple values
def summary_stats(data):
    """Returns count, average elevation, max elevation."""
    count = len(data)
    avg_elev = data['Elevation (m)'].mean()
    max_elev = data['Elevation (m)'].max()
    return count, avg_elev, max_elev

count, avg_elev, max_elev = summary_stats(filtered_df)

# Main page formatting
st.title("\U0001F30B Interactive Volcano Explorer")
st.markdown("Explore volcanoes around the world with filters, maps, and charts.")

st.subheader(f"Summary for {selected_country}")
st.markdown(f"- **Number of Volcanoes:** {count}")
st.markdown(f"- **Average Elevation:** {avg_elev:.2f} m")
st.markdown(f"- **Highest Elevation:** {max_elev:.2f} m")

if not filtered_df.empty:
    # [DA2] Sort data
    top10 = filtered_df.nlargest(10, 'Elevation (m)')
    st.subheader("Top 10 Tallest Volcanoes")
    st.bar_chart(top10.set_index('Volcano Name')['Elevation (m)'])

    st.subheader("Volcano Type Distribution")
    type_counts = filtered_df['Primary Volcano Type'].value_counts()

    # Group small categories into "Other" (<5% threshold)
    threshold = 0.05 * type_counts.sum()
    major_types = type_counts[type_counts >= threshold]
    minor_types = type_counts[type_counts < threshold]

    if not minor_types.empty:
        major_types['Other'] = minor_types.sum()

    fig, ax = plt.subplots()
    ax.pie(major_types, labels=major_types.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    st.subheader("Volcano Map")

    # [PY4] List comprehension
    color_col = [[255, 0, 0] if 'Active' in str(status) or 'Historical' in str(status) else [0, 0, 255]
                 for status in filtered_df['Activity Evidence']]

    # [DA9] New column
    filtered_df['Color'] = color_col

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=filtered_df['Latitude'].mean(),
            longitude=filtered_df['Longitude'].mean(),
            zoom=3,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=filtered_df,
                get_position='[Longitude, Latitude]',
                get_color='Color',
                get_radius=10000,
                pickable=True,
            ),
        ],
    ))

st.subheader("Filtered Volcano Data")
# [DA7] Select/drop columns
st.dataframe(filtered_df[['Volcano Name', 'Country', 'Primary Volcano Type', 'Elevation (m)', 'Activity Evidence']])

st.download_button("Download Filtered Data", filtered_df.to_csv(index=False), "volcanoes_filtered.csv")
