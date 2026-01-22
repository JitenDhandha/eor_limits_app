import os
import streamlit as st
import pandas as pd
import plot_eor_limits
import eor_limits

@st.cache_data
def load_datasets(lowest_only):
    fnames = eor_limits.get_all_dataset_names()
    if lowest_only:
        return [eor_limits.get_dataset(fname) for fname in fnames]
    else:
        return [eor_limits.get_dataset_lowest_limits(fname) for fname in fnames]

def main():
    
    st.title("21-cm Power Spectrum Limits Plotter")
    st.set_page_config(page_title="21-cm Power Spectrum Limits Plotter")
    st.text(
    """\
This is an interactive tool to visualize published 21-cm power spectrum limits from various experiments. \
You can select datasets from the sidebar (collapsible on the top left corner of the page), choose plotting \
options, and customize the appearance of the plots. \
The datasets are sourced from the 'eor_limits' Python package, which provides a standardized interface \
to access these limits.

Note that for each dataset, the limits are grouped by redshift. For datasets containing multiple fields or \
polarizations at the same redshift, they are treated as separate redshift entries.
    """
    )
    st.info(
    """\
Pro tips: You can click on a legend item to toggle its visibility. Double-clicking a legend item will isolate it. \
Furthermore, you can zoom into a specific region of the plot by clicking and dragging your mouse, or reset \
the view by double-clicking on the plot area. Hovering over data points will show detailed information about that point.
    """
    )
    
    # Container for the plot first
    cont_plot = st.container()

    # Columns for plot controls
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            plot_type = st.selectbox("Plot type", ["line", "scatter"], key="plot_type")
            x_axis = st.selectbox("X axis", ["k", "z"], key="x_axis")
            cols2 = st.columns(2)
            with cols2[0]:
                x_axis_errors = st.checkbox("Show x axis errors", value=True, key="x_axis_errors")
            with cols2[1]:
                x_axis_log = st.checkbox("Log x axis", value=False, key="x_axis_log")
            lowest_only = st.checkbox("Show only lowest limit per z", value=False, key="lowest_only")
        with cols[1]:
            z_range = st.slider("z range", min_value=5.0, max_value=30.0, value=(5.0,30.0), step=0.1, key="z_range")
            log_k_range = st.slider("log(k) range", min_value=-3.0, max_value=2.0, value=(-3.0,2.0), step=0.1, key="k_range")
            year_range = st.slider("year range", min_value=2010, max_value=2030, value=(2010,2030), step=1, key="year_range")

    # Load datasets
    dataset_raw = load_datasets(lowest_only=False)
    dataset_lowest = load_datasets(lowest_only=True)
    datasets = dataset_lowest if lowest_only else dataset_raw
    # Create a pandas DataFrame with 1) fname, 2) telescope, 3) year, 4) dataset, 5) checkbox object
    df_data = []
    for d in datasets:
        df_data.append({
            'fname': f'{d.metadata.author}{d.metadata.year}' if 'HERA' not in d.metadata.author else f'HERA{d.metadata.year}',
            'telescope': d.metadata.telescope,
            'year': d.metadata.year,
            'dataset': d,
            'checkbox': None  # Will be populated later with Streamlit checkbox objects
        })
    # Order by telescope then year
    df_datasets = pd.DataFrame(df_data).sort_values(by=['telescope', 'year'])
    # Display checkboxes in sidebar ordered by telescope and year
    with st.sidebar:
        select_all = st.checkbox("Select/Deselect all")
        for telescope in df_datasets['telescope'].unique():
            st.markdown(f"*{telescope}*")
            for idx, row in df_datasets[df_datasets['telescope'] == telescope].iterrows():
                df_datasets.at[idx, 'checkbox'] = st.checkbox(row['fname'], value=select_all)
            
    plot_kwargs_code = st.text_area("plot_kwargs_dict: Python dict of dicts, keys are dataset identifiers, values are Plotly marker/line dicts", "{}", 
                                    help="e.g. {'HERA2025': {'marker': {'symbol': 'star', 'size': 4}, 'line': {'shape': 'hvh'}, 'color': 'green'}}",
                                    key="plot_kwargs_dict")
    try:
        plot_kwargs_dict = eval(plot_kwargs_code, {"__builtins__": {}})
    except Exception as e:
        st.warning(f"Invalid plot_kwargs_dict: {e}")
        plot_kwargs_dict = {}

    with cont_plot:
        fig = plot_eor_limits.plot(
            [row['dataset'] for idx, row in df_datasets.iterrows() if row['checkbox']],
            plot_type=plot_type,
            x_axis=x_axis,
            x_axis_log=x_axis_log,
            x_axis_errors=x_axis_errors,
            z_range=z_range,
            k_range=(10**log_k_range[0], 10**log_k_range[1]),
            year_range=year_range,
            plot_kwargs_dict=plot_kwargs_dict
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
