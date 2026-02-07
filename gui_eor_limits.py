import streamlit as st
import pandas as pd
import plot_eor_limits
import eor_limits

@st.cache_data
def load_datasets():
    fnames = eor_limits.get_available_datasets()
    list_datasets = []
    for fname in fnames:
        draw = eor_limits.load_dataset(fname)
        dlowest = eor_limits.load_dataset_lowest_limits(fname)
        list_datasets.append({
            'fname': f"{draw.author}{draw.year}" if 'HERA' not in draw.author else f'HERA{draw.year}',
            'telescope': draw.telescope,
            'year': draw.year,
            'doi': draw.doi,
            'dataset_raw': draw,
            'dataset_lowest': dlowest,
            'checkbox': None
        })
    df_datasets = pd.DataFrame(list_datasets)
    return df_datasets

def main():
    
    # Page configuration
    st.set_page_config(page_title="21-cm Power Spectrum Limits Plotter", 
                       page_icon="📡",
                       layout='wide')
    
    # Title and description
    st.markdown(f"<div style='text-align: right; font-size: 12px;'>Last updated: 30 January, 2026</div>", unsafe_allow_html=True)
    st.title("📡 21-cm Power Spectrum Limits Plotter")
    st.markdown(
    """
    _An interactive tool to visualize published 21-cm power spectrum limits from interferometric experiments_ 
    """)
    #
    st.info(
    """
    - **How to use**: Select datasets from the sidebar, collapsible on the top left corner of the page, and customize from various plotting options!
    - **Pro tips**: Hover over the data points to see more information. Click on legend items to toggle visibility. Double-click to isolate.
    - **Note**: Limits are grouped by redshift. Datasets containing multiple fields or polarizations at the same redshift are treated as separate entries.
    """
    )
    
    # Sidebar for dataset selection
    with st.sidebar:
        
        # Load existing datasets
        if 'df_datasets' not in st.session_state:
            df_datasets = load_datasets()
        
        # Upload own dataset
        uploaded_datasets = st.file_uploader("**:blue[Upload your own dataset]**", type=['yaml'], 
                                             help="""
                                             Uploaded datasets are stored in-memory on the server for processing during your session. 
                                             They are not saved anywhere permanently, and not accessible to any other app users. 
                                             Only the main author (Jiten Dhandha) has access to the server logs, 
                                             which do not display the contents of uploaded files.
                                             """,
                                             accept_multiple_files=True)
        for uploaded_dataset in uploaded_datasets:
            upload_data = uploaded_dataset.getvalue().decode('utf-8')
            try:
                user_dataset = eor_limits.load_dataset(upload_data, if_yaml_str=True)
                user_dataset_lowest = eor_limits.load_dataset_lowest_limits(upload_data, if_yaml_str=True)
                st.success(f"Successfully loaded dataset: {user_dataset.author}{user_dataset.year}")
                df_datasets = pd.concat([
                    df_datasets,
                    pd.DataFrame([{
                        'fname': f"{user_dataset.author}{user_dataset.year}" if 'HERA' not in user_dataset.author else f'HERA{user_dataset.year}',
                        'telescope': user_dataset.telescope,
                        'year': user_dataset.year,
                        'doi': user_dataset.doi,
                        'dataset_raw': user_dataset,
                        'dataset_lowest': user_dataset_lowest,
                        'checkbox': None
                    }])
                ])
            except Exception as e:
                st.error(f"Failed to load dataset: {e}")
                
        # Sort datasets by telescope and year
        df_datasets = df_datasets.sort_values(by=['telescope', 'year']).reset_index(drop=True)

        # Dataset selection checkboxes
        with st.container(horizontal=True, gap="xsmall"):
            st.markdown("**:blue[Select/Deselect all]**")
            select_all = st.checkbox("", value=False, key="select_all")
        select_all_telescope = {}
        for idx, row in df_datasets.iterrows():
            if idx == 1 or df_datasets.iloc[idx]['telescope'] != df_datasets.iloc[idx-1]['telescope']:
                with st.container(horizontal=True, gap="xsmall"):
                    telescope_name = df_datasets.iloc[idx]['telescope']
                    st.markdown(f"***:blue[{telescope_name}]***")
                    select_all_telescope[telescope_name] = st.checkbox(f"", value=False, key=f"select_all_{telescope_name}")
            with st.container(horizontal=True, gap="xsmall"):
                df_datasets.at[idx, 'checkbox'] = st.checkbox(row['fname'], 
                                                value=select_all or select_all_telescope[row['telescope']])
                if row['doi']: # Add DOI link if available
                    st.markdown(f"<a href='https://doi.org/{row['doi']}' target='_blank' style='text-decoration: none;'>🔗</a>", 
                                unsafe_allow_html=True)
    
    # Two columns: left for options, right for plot
    columns = st.columns([1,3])
    bottom_left_cell = columns[0].container(border=True, height="stretch", vertical_alignment="center")
    cont_plot = columns[1].container(border=True, height="stretch", vertical_alignment="center")
    
    # Options area
    with bottom_left_cell:
        plot_type = st.radio(
            "Plot type:", 
            options=['line', 'scatter'],
            format_func=lambda x: 'Line plot' if x=='line' else 'Scatter plot',
        )
        x_axis = st.radio(
            "$x$ axis:", 
            options=['k', 'z'],
            format_func=lambda x: 'Wavenumber $k$' if x=='k' else 'Redshift $z$',
        )
        x_axis_errors = st.toggle("Show $x$ axis error bars", value=False)
        x_axis_log = st.toggle("Logarithmic $x$ axis", value=(x_axis=='k'))
        lowest_only = st.toggle("Show only lowest limits per $z$-bin", value=False)
        z_range = st.slider("$z$ range", min_value=5.0, max_value=30.0, value=(5.0,30.0), step=0.1)
        log_k_range = st.slider("$\log(k)$ range", min_value=-3.0, max_value=2.0, value=(-3.0,2.0), step=0.1)
        year_range = st.slider("Year range", min_value=2010, max_value=2030, value=(2010,2030), step=1)
        
    # Custom plot kwargs (needed first for plot_kwargs_dict to be defined)
    with st.expander("Customize plot appearance"):
        st.markdown("Provide a Python dictionary to customize the appearance of each dataset. \
                    The keys should be the dataset identifiers (e.g. `'HERA2025'`), and the values should be dictionaries containing Plotly marker/line properties. \
                    e.g. `{'HERA2025': {'marker': {'symbol': 'star', 'size': 4}, 'line': {'shape': 'hvh'}, 'color': 'green'}}`")
        plot_kwargs_code = st.text_area("plot_kwargs_dict:", "{}")
        try:
            plot_kwargs_dict = eval(plot_kwargs_code, {"__builtins__": {}})
        except Exception as e:
            st.warning(f"Invalid plot_kwargs_dict: {e}")
            plot_kwargs_dict = {}
    
    # Plot area
    with cont_plot:
        fig = plot_eor_limits.plot(
            [row['dataset_lowest' if lowest_only else 'dataset_raw'] for idx, row in df_datasets.iterrows() if row['checkbox']],
            plot_type=plot_type,
            x_axis=x_axis,
            x_axis_log=x_axis_log,
            x_axis_errors=x_axis_errors,
            z_range=z_range,
            k_range=(10**log_k_range[0], 10**log_k_range[1]),
            year_range=year_range,
            plot_kwargs_dict=plot_kwargs_dict
        )
        st.plotly_chart(fig, width="stretch", height="stretch")

    # Show raw data
    with st.expander("Show raw data of selected datasets"):
        for idx, row in df_datasets.iterrows():
            if row['checkbox']:
                st.markdown(f"**{row['fname']}**")
                st.dataframe(row['dataset_lowest' if lowest_only else 'dataset_raw'].data)
            
        
if __name__ == "__main__":
    main()
