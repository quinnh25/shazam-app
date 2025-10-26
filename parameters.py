import json


parameters_json = "./parameters.json"

# todo: if windowed constellation mapping is a total wash,
#       add paramset in read_parameters and set_parameters
#       for grid searching scipy.signal.find_peaks parameters.
#
#       (the idea is that you can simply insert 
#        read_parameters(...) anywhere in the codebase)

def set_parameters(
        cm_window_size=10,
        candidates_per_band=6,
        bands=[(0,10),(10,20),(20,40),(40,80),(80,160),(160,512)],
        fanout_t=100,
        fanout_f=1500
        ):
    """
    Used by `grid_search.py` to search for optimal parameters
    """
    parameters = {
        "constellation_mapping": {
            "cm_window_size": cm_window_size,
            "candidates_per_band": candidates_per_band,
            "bands": [list(interval) for interval in bands],
        },
        "hashing": {
            "fanout_t": fanout_t,
            "fanout_f": fanout_f
        }
    }
    with open(parameters_json, "w", encoding="utf-8") as f:
        json.dump(parameters, f, indent=2)
    return parameters
    

def read_parameters(paramset: str = "all_parameters"):
    """
    ```
    # const_map.py
    window_size, candidates_per_band, bands = read_parameters("constellation_mapping")

    # hasher.py
    fanout_t, fanout_f = read_parameters("hashing")

    # all
    returns dict containing all parameters

    ```
    """
    try:
        with open(parameters_json, "r", encoding="utf-8") as f:
            params = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        params = set_parameters()

    if paramset == "constellation_mapping":
        cm = params.get("constellation_mapping", {})
        cm_window_size = cm.get("cm_window_size")
        candidates_per_band = cm.get("candidates_per_band")
        bands = [tuple(b) for b in cm.get("bands", [])]
        return cm_window_size, candidates_per_band, bands

    if paramset == "hashing":
        h = params.get("hashing", {})
        return h.get("fanout_t"), h.get("fanout_f")

    if paramset == "all_parameters":
        return params

    return params


if __name__ == "__main__":
    set_parameters()