import os
import streamlit as st
import plot_eor_limits
import eor_limits

def load_datasets():
    yaml_files = [os.path.basename(f) for f in os.listdir('data') if f.endswith('.yaml')]
    datasets = {}
    for fname in yaml_files:
        try:
            dataset = eor_limits.get_dataset(fname)
            telescope = getattr(dataset.metadata, 'telescope', None)
            if telescope not in datasets:
                datasets[telescope] = []
            datasets[telescope].append((fname, dataset))
        except Exception as e:
            st.warning(f"Failed to load {fname}: {e}")
    return datasets

def main():
    
    st.title("EoR 21-cm Power Spectrum Limits Plotter")
    st.text("Interactive tool to visualize EoR 21-cm power spectrum limits from various datasets.")
    datasets = load_datasets()
    selected = {}
    
    # Container for the plot first
    cont_plot = st.container()

    # Sidebar controls for dataset selection
    with st.sidebar:
        st.markdown("**Select Datasets**")
        all_keys = []
        dataset_info = []
        for telescope, dslist in datasets.items():
            sorted_dslist = sorted(dslist, key=lambda tup: getattr(tup[1].metadata, 'year', 0) or 0)
            for fname, dataset in sorted_dslist:
                key = f"{telescope}_{fname}"
                all_keys.append(key)
                dataset_info.append((telescope, fname, dataset, key))
        select_all = st.checkbox("Select/Deselect All", value=False, key="select_all")
        for telescope in datasets.keys():
            st.markdown(f"*{telescope}*")
            dslist = [info for info in dataset_info if info[0] == telescope]
            for _, fname, dataset, key in dslist:
                checked = st.checkbox(fname, key=key, value=select_all)
                if checked:
                    selected[key] = (dataset, fname)
    
    # Columns for plot controls
    with st.container():
        cols = st.columns(2, vertical_alignment='top')
        with cols[0]:
            plot_type = st.selectbox("Plot type", ["line", "scatter"], key="plot_type")
            x_axis = st.selectbox("X axis", ["k", "z"], key="x_axis")
            # Align this last one to match the other column
            x_axis_errors = st.checkbox("Show X axis errors", value=True, key="x_axis_errors")
        with cols[1]:
            z_range = st.slider("z range", min_value=5.0, max_value=50.0, value=(5.0,50.0), step=0.1, key="z_range")
            k_range = st.slider("k range", min_value=0.001, max_value=100.0, value=(0.001,100.0), step=0.001, key="k_range")
            year_range = st.slider("year range", min_value=2000, max_value=2050, value=(2000,2050), step=1, key="year_range")

    plot_kwargs_code = st.text_area("plot_kwargs_list (Python list of dicts, one per selected dataset)", "None", key="plot_kwargs_list")
    try:
        plot_kwargs_list = eval(plot_kwargs_code, {"__builtins__": {}})
        if plot_kwargs_list is None:
            pass
        elif not isinstance(plot_kwargs_list, list):
            raise ValueError("Not a list")
        else:
            if len(plot_kwargs_list) != len(selected):
                st.warning(f"Number of plot_kwargs dicts ({len(plot_kwargs_list)}) does not match number of selected datasets ({len(selected)}).")
    except Exception as e:
        st.warning(f"Invalid plot_kwargs_list: {e}")

    with cont_plot:
        datasets_to_plot = [dataset for dataset, fname in selected.values()]
        fig = plot_eor_limits.plot(
            datasets_to_plot,
            plot_type=plot_type,
            x_axis=x_axis,
            x_axis_errors=x_axis_errors,
            z_range=z_range,
            k_range=k_range,
            year_range=year_range,
            plot_kwargs_list=plot_kwargs_list
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
