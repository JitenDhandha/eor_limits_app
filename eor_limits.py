import attr
import numpy as np
import yaml
import os

##################################################################
#####                  Validator functions                   #####
##################################################################

def check_is_1d_array(arr):
    if arr is np.array([], dtype=object):
        return True
    else:
        return all(isinstance(x, (int, float)) for x in arr)

def check_is_2d_array(arr):
    if arr is np.array([], dtype=object):
        return True
    else:
        return all(isinstance(row, (list, np.ndarray)) for row in arr)

def to_eval_and_obj_array(arr):
    
    # If arr is None, convert to empty array
    if arr is [] or arr is None or arr is np.array([], dtype=object) or arr is np.array(None, dtype=object):
        return np.array([], dtype=object)
    
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
        if isinstance(lst, (list, np.ndarray)):
            return [process_list(x) for x in lst]
        else:
            return eval_item(lst)
    processed = process_list(arr)
    
    return np.array(processed, dtype=object)


##################################################################
#####                      Data class                        #####
##################################################################

@attr.define
class Data:
    
    z: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    z_lower: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    z_upper: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    k: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    k_lower: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    k_upper: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    delta_squared: np.ndarray = attr.field(
        factory=lambda: np.array([], dtype=object),
        converter=to_eval_and_obj_array,
    )
    
    def __attrs_post_init__(self):
        # Check dimensionality
        for attr_name in ['z', 'z_lower', 'z_upper']:
            arr = getattr(self, attr_name)
            if not check_is_1d_array(arr):
                raise ValueError(f"{attr_name} must be a 1D array of numbers.")
        for attr_name in ['k', 'k_lower', 'k_upper', 'delta_squared']:
            arr = getattr(self, attr_name)
            if not check_is_2d_array(arr):
                raise ValueError(f"{attr_name} must be a 2D array of numbers.")
        # Check sizes
        if (not self.z_lower.size == 0 and not self.z_lower.shape == self.z.shape) or \
            (not self.z_upper.size == 0 and not self.z_upper.shape == self.z.shape):
            raise ValueError("z_lower and z_upper must be the same shape as z.")
        if (not self.k_lower.size == 0 and not self.k_lower.shape == self.k.shape) or \
            (not self.k_upper.size == 0 and not self.k_upper.shape == self.k.shape) or \
            (not self.delta_squared.shape == self.k.shape):
            raise ValueError("k, k_lower, k_upper, and delta_squared must be the same shape.")
            
##################################################################
#####                    Metadata class                      #####
##################################################################

@attr.define
class MetaData:
    telescope: str = attr.field(validator=attr.validators.instance_of(str), default='')
    telescope_suffix: str = attr.field(validator=attr.validators.instance_of(str), default='')
    author: str = attr.field(validator=attr.validators.instance_of(str), default='')
    year: int = attr.field(validator=attr.validators.instance_of(int), default=0)
    doi: str = attr.field(validator=attr.validators.instance_of(str), default='')

##################################################################
#####                     Dataset class                      #####
##################################################################

@attr.define
class DataSet:
    metadata: MetaData = attr.field(validator=attr.validators.instance_of(MetaData))
    notes: list = attr.field(validator=attr.validators.instance_of(list))
    data: Data = attr.field(validator=attr.validators.instance_of(Data))
    
##################################################################
#####                    Loader function                     #####
##################################################################

def get_all_dataset_names() -> list[str]:
    
    files = [f[:-5] for f in os.listdir('data') if f.endswith('.yaml')]
    return files

def get_dataset(file_path: str) -> DataSet:
    
    file_path = 'data/' + file_path
    file_path = file_path + '.yaml' if not file_path.endswith('.yaml') else file_path
    with open(file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    return DataSet(
        metadata=MetaData(**yaml_data.get('metadata', {})),
        notes=yaml_data.get('notes', []),
        data=Data(**yaml_data.get('data', {})),
    )
    
# WARNING: This might be over-estimating the lowest limit, if the lowest k-bin is erroneously low.
def get_dataset_lowest_limits(filepath: str) -> DataSet:
    
    dataset = get_dataset(filepath)
    dsq_L = []
    k_L = []
    k_lower_L = []
    k_upper_L = []
    for iz in range(len(dataset.data.z)):
        delta_squared_z = np.array(dataset.data.delta_squared[iz], dtype=float)
        min_index = np.nanargmin(delta_squared_z)
        # Remove all but the minimum value in this z slice
        dsq_L.append([delta_squared_z[min_index]])
        k_L.append([dataset.data.k[iz][min_index]])
        if dataset.data.k_lower.size > 0:
            k_lower_L.append([dataset.data.k_lower[iz][min_index]])
        else:
            pass
        if dataset.data.k_upper.size > 0:
            k_upper_L.append([dataset.data.k_upper[iz][min_index]])
        else:
            pass
    return  DataSet(
        metadata=dataset.metadata,
        notes=dataset.notes,
        data=Data(
            z=dataset.data.z,
            z_lower=dataset.data.z_lower,
            z_upper=dataset.data.z_upper,
            k=k_L,
            k_lower=k_lower_L,
            k_upper=k_upper_L,
            delta_squared=dsq_L,
        )
    )
        
    