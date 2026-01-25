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
        x_axis_log = False,
        x_axis_errors = True,
        z_range = None,
        k_range = None,
        year_range = None,
        plot_kwargs_dict = {}):
    """
    Plot multiple datasets on the same figure.
    datasets: list of dataset objects
    plot_kwargs_dict: dict of dicts, keys are dataset identifiers, values are Plotly marker/line dicts
    """
    if not isinstance(datasets, (list, tuple)):
        datasets = [datasets]
    if not isinstance(plot_kwargs_dict, dict):
        raise ValueError("plot_kwargs_dict must be a dict.")
    else:
        # Ensure all datasets have an entry
        for dataset in datasets:
            key = f'{dataset.author}{dataset.year}' if 'HERA' not in dataset.author else f'HERA{dataset.year}'
            if key not in plot_kwargs_dict:
                plot_kwargs_dict[key] = {}

    # Make square figure
    fig = go.Figure()
    base_colors = px.colors.qualitative.Plotly
    
    # Loop over datasets
    for idx, dataset in enumerate(datasets):
        
        #Retrieve data
        data = dataset.data
        y_arr = data.delta_squared
        
        # Plotting parameters 
        key = f'{dataset.author}{dataset.year}' if 'HERA' not in dataset.author else f'HERA{dataset.year}'
        kwargs = plot_kwargs_dict.get(key, {})
        base_color = kwargs.get('color', base_colors[idx % len(base_colors)]) # default color
        color_gradient = _gradient_colors(base_color, len(data.z))
        
        # Loop over redshifts
        for iz in range(len(data.z)):
            
            # Get data for this redshift
            y = y_arr[iz]
            z_vals = float(data.z[iz]) * np.ones_like(y)
            z_lower_vals = data.z_lower[iz] * np.ones_like(y) if data.z_lower.size > 0 else None
            z_upper_vals = data.z_upper[iz] * np.ones_like(y) if data.z_upper.size > 0 else None
            k_vals = data.k[iz]
            k_upper_vals = data.k_lower[iz] if data.k_lower.size > 0 else None
            k_lower_vals = data.k_upper[iz] if data.k_upper.size > 0 else None
            z_tag_val = f'({data.z_tags[iz]})' if data.z_tags.size > 0 else ""
            
            # Apply z range filter
            if z_range is not None and (z_vals[0] < z_range[0] or z_vals[0] > z_range[1]):
                continue
            # Apply year range filter
            if year_range is not None and (dataset.year is not None) and (dataset.year < year_range[0] or dataset.year > year_range[1]):
                continue
            # Apply k range filter
            if k_range is not None:
                k_mask = (k_vals >= k_range[0]) & (k_vals <= k_range[1])
                if not np.any(k_mask):
                    continue
                k_vals = np.where(k_mask, k_vals, np.nan)
                k_upper_vals = np.where(k_mask, k_upper_vals, np.nan) if k_upper_vals is not None else None
                k_lower_vals = np.where(k_mask, k_lower_vals, np.nan) if k_lower_vals is not None else None
                z_vals = np.where(k_mask, z_vals, np.nan)
                z_lower_vals = np.where(k_mask, z_lower_vals, np.nan) if z_lower_vals is not None else None
                z_upper_vals = np.where(k_mask, z_upper_vals, np.nan) if z_upper_vals is not None else None
                y = np.where(k_mask, y, np.nan)
            
            # Check what the x axis is
            if x_axis == 'k':
                x = k_vals
                x_lower = k_lower_vals
                x_upper = k_upper_vals
            elif x_axis == 'z':
                x = z_vals
                x_lower = z_lower_vals
                x_upper = z_upper_vals
            else:
                raise ValueError("Invalid x_axis. Use 'k' or 'z'.")
            
            # x axis errors
            if x_axis_errors and (x_lower is not None or x_upper is not None):
                error_x = dict(type='data',symmetric=False,array=x_upper-x, arrayminus=x-x_lower)
            else:
                error_x = None
                
            # Plotting label and style
            color = color_gradient[iz]
            marker_kwargs = kwargs.get('marker', dict(symbol='triangle-down',size=8,)) # default marker
            line_kwargs = kwargs.get('line', dict(shape='linear')) # default line
            marker_kwargs['color'] = color # color set separately
            line_kwargs['color'] = color # color set separately
            label = f'{dataset.author}{dataset.year}' if 'HERA' not in dataset.author else f'HERA{dataset.year}'
            label = f'{label}, z={z_vals[0]} {z_tag_val}'
            
            # Plot type
            if plot_type == 'line':
                mode = 'lines+markers'
            elif plot_type == 'scatter':
                mode = 'markers'
            else:
                raise ValueError("Invalid plot_type. Use 'line' or 'scatter'.")
            
            # Finally add the trace to the plot
            fig.add_trace(go.Scatter(x=x, y=y, mode=mode,
                        error_x=error_x,
                        name=label,
                        marker=marker_kwargs,
                        line=line_kwargs)
                        )
    
    fig.update_layout(
        xaxis = dict(
            type='log' if x_axis_log else 'linear', exponentformat='e',
            title='k [h/Mpc]' if x_axis == 'k' else 'Redshift z',
        ),
        yaxis = dict(
            type='log', exponentformat='e',
            title='Δ² [mK²]',
        ),
        legend=dict(
            font=dict(size=10),
        )
    )
    return fig
