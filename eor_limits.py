import attr
from attr import validators
import numpy as np
import yaml
import ast


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
        if isinstance(lst, list):
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
        for attr_name in ['z', 'z_lower', 'z_upper']:
            arr = getattr(self, attr_name)
            if not check_is_1d_array(arr):
                raise ValueError(f"{attr_name} must be a 1D array of numbers.")
        for attr_name in ['k', 'k_lower', 'k_upper', 'delta_squared']:
            arr = getattr(self, attr_name)
            if not check_is_2d_array(arr):
                raise ValueError(f"{attr_name} must be a 2D array of numbers.")
            
##################################################################
#####                    Metadata class                      #####
##################################################################

@attr.define
class MetaData:
    telescope: str = attr.field(validator=validators.instance_of(str), default='')
    telescope_suffix: str = attr.field(validator=validators.instance_of(str), default='')
    author: str = attr.field(validator=validators.instance_of(str), default='')
    year: int = attr.field(validator=validators.instance_of(int), default=0)
    doi: str = attr.field(validator=validators.instance_of(str), default='')

##################################################################
#####                     Dataset class                      #####
##################################################################
@attr.define
class DataSet:
    metadata: MetaData = attr.field(validator=validators.instance_of(MetaData))
    notes: str = attr.field(validator=validators.instance_of(list))
    data: Data = attr.field(validator=validators.instance_of(Data))
    
    
##################################################################
#####                    Loader function                     #####
##################################################################

def load_dataset(file_path: str) -> DataSet:
    
    file_path = 'data/' + file_path
    file_path = file_path + '.yaml' if not file_path.endswith('.yaml') else file_path
    with open(file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    return DataSet(
        metadata=MetaData(**yaml_data.get('metadata', {})),
        notes=yaml_data.get('notes', []),
        data=Data(**yaml_data.get('data', {})),
    )