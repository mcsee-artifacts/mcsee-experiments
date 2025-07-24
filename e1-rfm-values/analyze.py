import argparse
import os
import json
import re

def parse_json_files(directory_path):
    """
    Parses JSON files in the given directory, extracts specific 'arfm' data,
    and prints a summary for each file with formatted values and filename,
    sorted by custom criteria. Also prints summary statistics at the end.

    Args:
        directory_path (str): The path to the directory containing JSON files.
    """
    # Check if the provided directory path exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return

    print(f"Parsing JSON files in: {directory_path}\n")

    json_files = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            json_files.append(filename)

    # Define the custom sorting order for initial letters
    letter_order = {'M': 0, 'H': 1, 'S': 2, 'U': 3}

    def custom_sort_key(filename):
        """
        Custom key for sorting filenames.
        Prioritizes M, H, S, U, then sorts by numeric part.
        """
        base_name = os.path.splitext(filename)[0] # Get filename without extension
        
        first_char = base_name[0].upper() if base_name else ''
        
        # Assign priority based on the defined letter_order, default to a high number for others
        priority = letter_order.get(first_char, 999)

        # Extract numeric part from the filename (e.g., "file10" -> 10)
        # Use regex to find digits at the end or after the first character
        match = re.search(r'(\d+)$', base_name)
        numeric_part = int(match.group(1)) if match else 0 # Default to 0 if no number found

        return (priority, numeric_part, base_name) # Include base_name for stable sort of non-numeric parts

    # Sort the list of JSON files using the custom key
    json_files.sort(key=custom_sort_key)

    # Initialize counters for statistics
    files_with_non_rfu_values = 0
    files_with_rfm_req_one = 0
    total_parsed_files = 0

    # Iterate through the sorted files
    for filename in json_files:
        filepath = os.path.join(directory_path, filename)
        
        # Flags for current file's statistics
        current_file_has_non_rfu = False
        current_file_has_rfm_req_one = False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            total_parsed_files += 1

            # Check if the 'arfm' key exists in the JSON data
            if "arfm" in data:
                arfm_data = data["arfm"]
                all_sdram_summary_parts = [] # List to hold formatted strings for sdram_0 and sdram_1

                # Define the structure to iterate through
                sdram_keys = ["sdram_0", "sdram_1"]
                sub_keys = ["A", "B", "C"]
                
                # Iterate through sdram_0 and sdram_1
                for sdram_k in sdram_keys:
                    current_sdram_block_parts = [] # List to hold formatted strings for A, B, C within current sdram
                    if sdram_k in arfm_data:
                        sdram_block = arfm_data[sdram_k]
                        # Iterate through A, B, C
                        for i, sub_k in enumerate(sub_keys):
                            if sub_k in sdram_block:
                                sub_block = sdram_block[sub_k]
                                
                                # Get values, defaulting to "N/A" if missing
                                # Format rfm_req, raaimt, and raammt to be right-aligned with 3 characters
                                rfm_req_val = str(sub_block.get("rfm_req", "N/A")).rjust(3)
                                raaimt_val = str(sub_block.get("raaimt", "N/A")).rjust(3)
                                raammt_val = str(sub_block.get("raammt", "N/A")).rjust(3)
                                
                                # Check for statistics
                                if raaimt_val.strip().upper() != "RFU" and raammt_val.strip().upper() != "RFU" and raammt_val.strip() != "0" and raaimt_val.strip() != "0": 
                                    current_file_has_non_rfu = True
                                if rfm_req_val.strip() == "1":
                                    current_file_has_rfm_req_one = True

                                # Join these three values with commas
                                current_sdram_block_parts.append(f"{rfm_req_val}, {raaimt_val}, {raammt_val}")
                            else:
                                # If sub-block (A, B, or C) is missing, append N/A for all its values
                                current_sdram_block_parts.append(f"{'N/A'.rjust(3)}, {'N/A'.rjust(3)}, {'N/A'.rjust(3)}")

                            # Add 3 spaces after A and B blocks, but not after C (the last one)
                            if i < len(sub_keys) - 1:
                                current_sdram_block_parts.append("   ") # Three spaces

                    else:
                        # If sdram_0 or sdram_1 block is missing, append N/A for all its sub-blocks
                        for i, sub_k in enumerate(sub_keys):
                            current_sdram_block_parts.append(f"{'N/A'.rjust(3)}, {'N/A'.rjust(3)}, {'N/A'.rjust(3)}")
                            if i < len(sub_keys) - 1:
                                current_sdram_block_parts.append("   ")
                    
                    # Join the parts for the current sdram block (e.g., sdram_0)
                    all_sdram_summary_parts.append("".join(current_sdram_block_parts))

                # Format the filename to a fixed width (e.g., 12 characters, left-aligned)
                formatted_filename = f"{filename:<12}" # Adjust 12 as needed for your longest filename

                # Print the summary line for the current file, joining sdram_0 and sdram_1 blocks with three spaces
                print(f"{formatted_filename} {'   '.join(all_sdram_summary_parts)}")
            else:
                print(f"Warning: File '{filename}' does not contain an 'arfm' object.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from file '{filename}'. Skipping.")
        except Exception as e:
            print(f"An unexpected error occurred while processing '{filename}': {e}")
        
        # Update global counters based on current file's flags
        if current_file_has_non_rfu:
            files_with_non_rfu_values += 1
        if current_file_has_rfm_req_one:
            files_with_rfm_req_one += 1

    print("\n--- Summary Statistics ---")
    print(f"Total files parsed: {total_parsed_files}")
    print(f"Files with valid RFM values: {files_with_non_rfu_values}")
    print(f"Files with RFM Required bit set: {files_with_rfm_req_one}")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Parse JSON files in a directory and summarize 'arfm' data with formatted values and filename."
    )
    parser.add_argument(
        "directory", 
        type=str, 
        help="The path to the directory containing JSON files."
    )
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    # Call the main parsing function
    parse_json_files(args.directory)
