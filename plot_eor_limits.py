import numpy as np
import matplotlib as mpl
import plotly.express as px
import plotly.graph_objects as go
import eor_limits

def _gradient_colors(base_color, n):
    rgb = np.array(mpl.colors.to_rgb(base_color))
    # Generate gradient factors (light=1 → base=0)
    factors = np.linspace(1.5, 0.5, n) # lighter to darker
    return [f'rgb({int(255*min(1, rgb[0]*f))}, {int(255*min(1, rgb[1]*f))}, {int(255*min(1, rgb[2]*f))})' for f in factors]

# Main plotting function for EoR limits using Plotly

def plot(datasets, 
        plot_type = 'line', 
        x_axis = 'k', 
        x_axis_errors = True,
        z_range = None,
        k_range = None,
        year_range = None,
        plot_kwargs_list = None):
    """
    Plot multiple datasets on the same figure.
    datasets: list of dataset objects
    plot_kwargs_list: list of dicts, one per dataset
    """
    if not isinstance(datasets, (list, tuple)):
        datasets = [datasets]
    if plot_kwargs_list is None:
        plot_kwargs_list = [{} for _ in datasets]
    if len(plot_kwargs_list) != len(datasets):
        raise ValueError("plot_kwargs_list must be a list of dicts, one per dataset.")

    fig = go.Figure()
    base_colors = px.colors.qualitative.Plotly
    for idx, dataset in enumerate(datasets):
        data = dataset.data
        meta = dataset.metadata
        y_arr = data.delta_squared
        kwargs = plot_kwargs_list[idx]
        base_color = kwargs.get('color', base_colors[idx % len(base_colors)])
        color_gradient = _gradient_colors(base_color, len(data.z))
        for iz in range(len(data.z)):
            z_val = float(data.z[iz])
            k_vals = np.array(data.k[iz], dtype=float)
            year_val = getattr(meta, 'year', None)
            # Apply z range filter
            if z_range is not None and (z_val < z_range[0] or z_val > z_range[1]):
                continue
            # Apply year range filter
            if year_range is not None and (year_val is not None) and (year_val < year_range[0] or year_val > year_range[1]):
                continue
            y = np.array(y_arr[iz], dtype=float)
            if x_axis == 'k':
                x = k_vals
                x_lower = data.k_lower[iz] if data.k_lower.size > 0 else None
                x_upper = data.k_upper[iz] if data.k_upper.size > 0 else None
            elif x_axis == 'z':
                x = z_val * np.ones_like(y)
                x_lower = data.z_lower[iz] if data.z_lower.size > 0 else None
                x_upper = data.z_upper[iz] if data.z_upper.size > 0 else None
            else:
                raise ValueError("Invalid x_axis. Use 'k' or 'z'.")
            # Apply k range filter
            if k_range is not None:
                k_mask = (k_vals >= k_range[0]) & (k_vals <= k_range[1])
                if not np.any(k_mask):
                    continue
                y = np.where(k_mask, y, np.nan)
                x = np.where(k_mask, x, np.nan)
                if x_lower is not None:
                    x_lower = np.where(k_mask, x_lower, np.nan)
                if x_upper is not None:
                    x_upper = np.where(k_mask, x_upper, np.nan)
            # Error bars
            if x_axis_errors and (x_lower is not None or x_upper is not None):
                xerr = [x - x_lower, x_upper - x]
            else:
                xerr = None
            # Plotting kwargs
            label = kwargs.pop('label', f'{meta.telescope} ({meta.author}, {meta.year}) z={z_val}')
            color = color_gradient[iz]
            error_x = dict(type='data',symmetric=False,array=xerr[1], arrayminus=xerr[0]) if xerr is not None else None
            marker_kwargs = kwargs.pop('marker', dict(color=color,symbol="triangle-down",size=7,))
            line_kwargs = kwargs.pop('line', dict(color=color))
            if plot_type == 'line':
                mode = 'lines+markers'
            elif plot_type == 'scatter':
                mode = 'markers'
            else:
                raise ValueError("Invalid plot_type. Use 'line' or 'scatter'.")
            fig.add_trace(go.Scatter(x=x, y=y, mode=mode,
                        error_x=error_x,
                        name=label,
                        marker=marker_kwargs,
                        line=line_kwargs,
                        **{k:v for k,v in kwargs.items()})
                        )
    fig.update_layout(
        xaxis_title='k [h/Mpc]' if x_axis == 'k' else 'Redshift z',
        yaxis_title='Δ² [mK²]',
        yaxis_type='log',
        title='EoR Limits',
        legend_title="z"
    )
    return fig
