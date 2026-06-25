import tomllib
import streamlit as st
import pandas as pd
import plot_eor_limits
import eor_limits

# Load from .streamlit/config.toml
with open(".streamlit/config.toml", "rb") as f:
    config = tomllib.load(f)['theme']
    primaryColor = config.get("primaryColor")
    textColor = config.get("textColor")
    backgroundColor = config.get("backgroundColor")
    secondaryBackgroundColor = config.get("secondaryBackgroundColor")

def _apply_css():

    def _color_to_rgba(color, alpha):
        """Convert a hex color to an rgba string with the given alpha value."""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r}, {g}, {b}, {alpha})'

    st.markdown(
        f'''
        <style>
        .block-container {{
            padding-top: 2.5rem;
            padding-bottom: 1.5rem;
            max-width: 1480px;
        }}
        .app-section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0.1rem 0 0.65rem 0;
            color: {primaryColor};
        }}
        .app-telescope-heading {{
            font-size: 1.15rem;
            font-weight: 600;
            color: {primaryColor};
            opacity: 0.75;
        }}
        section[data-testid="stSidebar"] {{
            background:
                radial-gradient(circle at top left, {_color_to_rgba(primaryColor,0.15)}, transparent 60%),
                linear-gradient(180deg, {backgroundColor} 0%, {backgroundColor} 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )

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

    _apply_css()
    
    st.markdown(
        f'''
        <div style="padding: 0.15rem 0 0.5rem 0;">
            <div style="font-size: 3rem; font-weight: 800; line-height: 1.05; color:{primaryColor}">📡 21-cm Power Spectrum Limits Plotter</div>
            <div style="font-size: 0.95rem; opacity: 0.75; margin-top: 0.35rem"> by Jiten Dhandha, last updated 25 June 2026</div>
            <div style="margin-top: 0.75rem; margin-bottom: 1rem; line-height: 1.55;">
                An interactive tool to visualize published 21-cm power spectrum upper limits from interferometric experiments.
                Select datasets from the sidebar and customize the plot using the options below. Hover over the data points
                for more info, click on legend items to toggle visibility, and double-click to isolate a dataset.
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    # Sidebar for dataset selection
    with st.sidebar:
        
        # Load existing datasets
        if 'df_datasets' not in st.session_state:
            df_datasets = load_datasets()
        
        # Upload own dataset
        st.markdown('<div class="app-section-title">Upload your own data</div>', unsafe_allow_html=True)
        uploaded_datasets = st.file_uploader("For data protection, hover over info icon", type=['yaml'], 
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
        st.markdown('<div class="app-section-title">Select datasets</div>', unsafe_allow_html=True)
        with st.container(horizontal=True, gap="xsmall"):
            st.markdown("Select/Deselect all")
            select_all = st.checkbox("", value=False, key="select_all")
        select_all_telescope = {}
        for idx, row in df_datasets.iterrows():
            if idx == 1 or df_datasets.iloc[idx]['telescope'] != df_datasets.iloc[idx-1]['telescope']:
                with st.container(horizontal=True, gap="xsmall"):
                    telescope_name = df_datasets.iloc[idx]['telescope']
                    st.markdown(f'<div class="app-telescope-heading">{telescope_name}</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="app-section-title">Plotting options</div>', unsafe_allow_html=True)
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
        y_axis = st.radio(
            "$y$ axis:", 
            options=['delta_sq', 'power'],
            format_func=lambda x: 'Dimensionless $\Delta^2(k)$' if x=='delta_sq' else 'Power $P(k)$',
        )
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
        st.markdown('<div class="app-section-title">Main plot</div>', unsafe_allow_html=True)
        fig = plot_eor_limits.plot(
            [row['dataset_lowest' if lowest_only else 'dataset_raw'] for idx, row in df_datasets.iterrows() if row['checkbox']],
            plot_type=plot_type,
            x_axis=x_axis,
            x_axis_log=x_axis_log,
            x_axis_errors=x_axis_errors,
            y_axis=y_axis,
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
                st.markdown(f'<div class="app-telescope-heading">{row["fname"]}</div>', unsafe_allow_html=True)
                st.dataframe(row['dataset_lowest' if lowest_only else 'dataset_raw'].data)
            
        
if __name__ == "__main__":
    main()