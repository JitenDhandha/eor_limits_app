import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rcParams['text.usetex'] = True
import eor_limits

# Main plotting function for EoR limits
def plot(dataset, 
        ax = None,
        plot_type = 'line', 
        x_axis = 'k', 
        x_axis_errors = True,
        z_range = None,
        k_range = None,
        plot_kwargs = {}):
    
    data = dataset.data
    meta = dataset.metadata

    if ax is None:
        fig, ax = plt.subplots()
    
    # Default kwargs
    if plot_type == 'line':
        plot_kwargs.setdefault('linewidth', 2)
    elif plot_type == 'scatter':
        plot_kwargs.setdefault('fmt', 'v')
        plot_kwargs.setdefault('ms', 7)
    label = plot_kwargs.pop('label', None)
    
    # y-axis is always delta_squared
    y_arr = data.delta_squared
    
    # Just a flag to ensure label is only added once
    label_added = False
    
    for iz in range(len(data.z)):
        
        y = np.array(y_arr[iz], dtype=float)
        
        # Apply z range filter
        if z_range is not None and (data.z[iz] < z_range[0] or data.z[iz] > z_range[1]):
            continue
        
        # Plotting based on the specified plot type
        if x_axis == 'k':
            x = np.array(data.k[iz], dtype=float)
            x_lower = data.k_lower[iz] if data.k_lower.size > 0 else None
            x_upper = data.k_upper[iz] if data.k_lower.size > 0 else None
        elif x_axis == 'z':
            x = data.z[iz] * np.ones_like(y)
            x_lower = data.z_lower[iz] if data.z_lower.size > 0 else None
            x_upper = data.z_upper[iz] if data.z_upper.size > 0 else None
        else:
            raise ValueError("Invalid x_axis. Use 'k' or 'z'.")
        
        # Apply k range filter
        if k_range is not None:
            k_mask = (data.k[iz] >= k_range[0]) & (data.k[iz] <= k_range[1])
            if not np.any(k_mask):
                continue
            y = np.where(k_mask, y, np.nan)
            x = np.where(k_mask, x, np.nan)
            if x_lower is not None:
                x_lower = np.where(k_mask, x_lower, np.nan)
            if x_upper is not None:
                x_upper = np.where(k_mask, x_upper, np.nan)
            
        if x_axis_errors and (x_lower is not None or x_upper is not None):
            xerr = [x - x_lower, x_upper - x]
        else:
            xerr = None
        if label is None:
            label = fr'$z={data.z[iz]}$'
        else:
            if label_added:
                label = ''
            else:
                label_added = True
            
        # Plotting the data
        if plot_type == 'line':
            ax.plot(x, y, label=label, **plot_kwargs)
        elif plot_type == 'scatter':
            ax.errorbar(x, y, xerr=xerr, label=label, **plot_kwargs)
        else:
            raise ValueError("Invalid plot_type. Use 'line' or 'scatter'.")

    # Set axis labels, scale, and title
    ax.set_xlabel('$k$ [$h$ Mpc$^{-1}$]' if x_axis == 'k' else '$z$')
    ax.set_ylabel(r'$\Delta^2$ [mK$^2$]')
    ax.set_yscale('log')
    ax.legend()
    
    return ax.get_figure(), ax
