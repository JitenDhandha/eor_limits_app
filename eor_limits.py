import attr
import numpy as np
import yaml
import os

##################################################################
#####                  Validator functions                   #####
##################################################################

def check_is_empty(arr):
    return (arr is [] or arr is None or arr is np.array([], dtype=object) or arr is np.array(None, dtype=object))

def check_is_allowed(arr, allowed_types):
    return check_is_empty(arr) or all(isinstance(x, allowed_types) for x in arr)

def convert_to_empty(arr):
    return np.array([], dtype=object) if check_is_empty(arr) else np.array(arr, dtype=object)

def convert_to_empty_and_eval(arr):
    
    # Convert to empty array if needed
    arr = convert_to_empty(arr)
    
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
    
    z: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    z_lower: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    z_upper: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    z_tags: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty)
    k: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    k_lower: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    k_upper: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    delta_squared: np.ndarray = attr.field(default=np.array([], dtype=object), converter=convert_to_empty_and_eval)
    
    def __attrs_post_init__(self):
        # Check dimensionality
        for attr_name in ['z', 'z_lower', 'z_upper']:
            arr = getattr(self, attr_name)
            if not check_is_allowed(arr, (int, float)):
                raise ValueError(f"{attr_name} must be a 1D array of numbers.")
        for attr_name in ['k', 'k_lower', 'k_upper', 'delta_squared']:
            arr = getattr(self, attr_name)
            if not check_is_allowed(arr, (list, np.ndarray)):
                raise ValueError(f"{attr_name} must be a 2D array of numbers.")
        if not check_is_allowed(self.z_tags, str):
            raise ValueError("z_tags must be a 1D array of strings.")
        # Check sizes
        if (not self.z_lower.size == 0 and not self.z_lower.shape == self.z.shape) or \
            (not self.z_upper.size == 0 and not self.z_upper.shape == self.z.shape):
            raise ValueError("z_lower and z_upper must be the same shape as z.")
        if (not self.k_lower.size == 0 and not self.k_lower.shape == self.k.shape) or \
            (not self.k_upper.size == 0 and not self.k_upper.shape == self.k.shape) or \
            (not self.delta_squared.shape == self.k.shape):
            raise ValueError("k, k_lower, k_upper, and delta_squared must be the same shape.")
        if (not self.z_tags.size == 0 and not self.z_tags.shape == self.z.shape):
            raise ValueError("z_tags must be the same shape as z.")
            
##################################################################
#####                    Metadata class                      #####
##################################################################

@attr.define
class MetaData:
    telescope: str = attr.field(validator=attr.validators.instance_of(str), default='')
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
    
    # Retrieve dataset
    dataset = get_dataset(filepath)
    
    # Prepare lists to hold lowest limits
    z_L, k_L, dsq_L, k_lower_L, k_upper_L, z_lower_L, z_upper_L, z_tags_L = [], [], [], [], [], [], [], []
    
    # Loop over unique z values
    z_arr = dataset.data.z
    unique_z = np.unique(z_arr)
    for z_val in unique_z:
        # Find indices corresponding to this z value
        indices = np.where(z_arr == z_val)[0]
        min_val = np.inf
        min_idx = None
        # Loop over these indices to find the minimum delta_squared
        for iz in indices:
            ik = np.nanargmin(dataset.data.delta_squared[iz])
            min_dsq = np.nanmin(dataset.data.delta_squared[iz])
            if min_dsq < min_val:
                min_val = min_dsq
                min_idx = (iz, ik)
        iz, ik = min_idx
        # Append this minimum to the new dataset
        z_L.append(z_val)
        k_L.append([dataset.data.k[iz][ik]])
        dsq_L.append([dataset.data.delta_squared[iz][ik]])
        if dataset.data.k_lower.size > 0:
            k_lower_L.append([dataset.data.k_lower[iz][ik]])
        if dataset.data.k_upper.size > 0:
            k_upper_L.append([dataset.data.k_upper[iz][ik]])
        if dataset.data.z_lower.size > 0:
            z_lower_L.append(dataset.data.z_lower[iz])
        if dataset.data.z_upper.size > 0:
            z_upper_L.append(dataset.data.z_upper[iz])
        if dataset.data.z_tags.size > 0:
            z_tags_L.append(dataset.data.z_tags[iz])

    
    # Create new DataSet with lowest limits
    return DataSet(
        metadata=dataset.metadata,
        notes=dataset.notes,
        data=Data(
            z=np.array(z_L, dtype=object),
            z_lower=np.array(z_lower_L, dtype=object) if z_lower_L else np.array([], dtype=object),
            z_upper=np.array(z_upper_L, dtype=object) if z_upper_L else np.array([], dtype=object),
            z_tags=np.array(z_tags_L, dtype=object) if z_tags_L else np.array([], dtype=object),
            k=np.array(k_L, dtype=object),
            k_lower=np.array(k_lower_L, dtype=object) if k_lower_L else np.array([], dtype=object),
            k_upper=np.array(k_upper_L, dtype=object) if k_upper_L else np.array([], dtype=object),
            delta_squared=np.array(dsq_L, dtype=object),
        )
    )