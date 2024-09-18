# SciSafeEval Probe

import json

def read_sci_safe_eval(file_path, combine=True):
    """
    Reads JSONL data from a file and returns the processed data based on the combine option.
    
    Args:
        file_path (str): The path to the JSONL file.
        combine (bool): If True, replaces '<content>' in 'instruction' with 'content' to form 'prompt'. 
                        If False, only 'content' is returned.
                        
    Returns:
        list: A list of dictionaries containing either the combined 'prompt' or just 'content'.
    """
    data = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                json_obj = json.loads(line.strip())
                
                if combine:
                    # Replace '<content>' in 'instruction' with 'content'
                    prompt = json_obj['instruction'].replace('<content>', json_obj['content'])
                    data.append({"id": json_obj['id'], "prompt": prompt})
                else:
                    # Only return 'content'
                    data.append({"id": json_obj['id'], "prompt": json_obj['content']})
        
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
        return None