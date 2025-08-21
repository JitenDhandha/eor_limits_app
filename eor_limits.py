
import attr
from attr import validators
import numpy as np
import yaml
import ast

def to_eval_and_float_array(value):
    
    # Eval an item. Allows for "21**2" type expressions
    def eval_item(item):
        # Only allow safe evaluation of math expressions
        if item=='nan':
            return np.nan
        elif isinstance(item, str):
            item = eval(str(item), {"__builtins__": None}, {})
            return float(item)
        elif isinstance(item, (int, float)):
            return float(item)

    # Process the list recursively (handles nested lists)
    def process_list(lst):
        if isinstance(lst, list):
            return [process_list(x) for x in lst]
        else:
            return eval_item(lst)
    processed = process_list(value)
    
    return np.array(processed, dtype=object)

@attr.define
class Data:
    
    z: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    z_lower: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    z_upper: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    k: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    k_lower: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    k_upper: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )
    delta_squared: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=float),
        converter=to_eval_and_float_array,
    )

    """
    def __attrs_post_init__(self):
        # If z has more than one element, delta_squared and k must be 2D
        if self.z.size > 1:
            if (self.k.ndim != 2) or (self.k_lower.ndim != 2) or (self.k_upper.ndim != 2) or (self.delta_squared.ndim != 2):
                raise ValueError("k, k_lower, k_upper, delta_squared must be 2D if z has more than one element!")
        # If z has only one element, delta_squared and k must be 1D
        elif self.z.size == 1:
            if (self.k.ndim != 1) or (self.k_lower.ndim != 1) or (self.k_upper.ndim != 1) or (self.delta_squared.ndim != 1):
                raise ValueError("k, k_lower, k_upper, delta_squared must be 1D if z has only one element!")
        elif self.z.size == 0:
            pass  # Allow empty arrays
        # Check that z_lower and z_upper have the same shape as z
        if (self.z_lower.size > 0 and self.z_lower.shape != self.z.shape) or (self.z_upper.size > 0 and self.z_upper.shape != self.z.shape):
            raise ValueError("z_lower and z_upper must have the same shape as z.")
        # Check that k_lower and k_upper have the same shape as k
        if (self.k_lower.size > 0 and self.k_lower.shape != self.k.shape) or (self.k_upper.size > 0 and self.k_upper.shape != self.k.shape):
            raise ValueError("k_lower and k_upper must have the same shape as k.")
    """

@attr.define
class MetaData:
    telescope: str = attr.field(validator=validators.instance_of(str), default='')
    telescope_suffix: str = attr.field(validator=validators.instance_of(str), default='')
    author: str = attr.field(validator=validators.instance_of(str), default='')
    year: int = attr.field(validator=validators.instance_of(int), default=0)
    doi: str = attr.field(validator=validators.instance_of(str), default='')

"""
@attr.define
class PlotParameters:
    linestyle: str = attr.field(validator=validators.instance_of(str), default='-')
    linewidth: int = attr.field(validator=validators.instance_of(int), default=1)
    marker: str = attr.field(validator=validators.instance_of(str), default='o')
    color: str = attr.field(validator=validators.instance_of(str), default='black')
    plot_mode: str = attr.field(validator=validators.instance_of(str), default='scatter')
"""

@attr.define
class DataSet:
    metadata: MetaData = attr.field(validator=validators.instance_of(MetaData))
    notes: str = attr.field(validator=validators.instance_of(list))
    data: Data = attr.field(validator=validators.instance_of(Data))
    #plot_parameters: PlotParameters = attr.field(validator=validators.instance_of(PlotParameters))

def load_dataset(file_path: str) -> DataSet:
    
    file_path = 'data/' + file_path
    file_path = file_path + '.yaml' if not file_path.endswith('.yaml') else file_path
    with open(file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    return DataSet(
        metadata=MetaData(**yaml_data.get('metadata', {})),
        notes=yaml_data.get('notes', []),
        data=Data(**yaml_data.get('data', {})),
        #plot_parameters=PlotParameters(**yaml_data.get('plot_parameters', {}))
    )