import os


def replace_tabs_with_spaces_in_file(file_path):
    # Read the contents of the file
    with open(file_path, "r") as file:
        content = file.read()

    # Replace all tabs with spaces
    content = content.replace("\t", " ")

    # Write the modified content back to the file
    with open(file_path, "w") as file:
        file.write(content)


def replace_tabs_in_folder(folder_path):
    # Iterate through all files in the specified folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Ensure it's a file (not a directory)
        if os.path.isfile(file_path):
            replace_tabs_with_spaces_in_file(file_path)
            print(f"Processed file: {file_path}")


if __name__ == "__main__":
    # Specify the folder containing the files
    folder_path = "./jobshoplab/data/jssp_instances/solutions"

    # Call the function to replace tabs with spaces in all files in the folder
    replace_tabs_in_folder(folder_path)
