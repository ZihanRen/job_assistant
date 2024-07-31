import os
import shutil

def remove_all_except_specific_files(directory, file_extensions):
    for root, dirs, files in os.walk(directory, topdown=False):
        for file_name in files:
            if not any(file_name.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file_name)
                os.remove(file_path)
                print(f"Removed file: {file_path}")

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)
            print(f"Removed folder: {dir_path}")

# Set the current directory
current_directory = os.getcwd()

# Define the file extensions to keep
extensions_to_keep = ['.py', '.pickle']

# Remove all folders and files except the specified file extensions
remove_all_except_specific_files(current_directory, extensions_to_keep)
