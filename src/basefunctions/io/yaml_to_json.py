"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : yaml_to_json_converter

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Converter to recursively transform YAML files to JSON format

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import json
import yaml
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


class YamlToJsonConverter:
    """
    Converter class for transforming YAML files to JSON format recursively.
    """

    def __init__(self, target_directory: str):
        """
        Initialize the converter with target directory.

        Parameters
        ----------
        target_directory : str
            Directory path to process recursively.

        Raises
        ------
        ValueError
            If target directory does not exist.
        """
        if not basefunctions.check_if_dir_exists(target_directory):
            raise ValueError(f"Target directory '{target_directory}' does not exist")
        self.target_directory = basefunctions.norm_path(target_directory)
        self.logger = basefunctions.get_logger(__name__)

    def convert_directory(self) -> dict:
        """
        Convert all YAML files in target directory recursively.

        Returns
        -------
        dict
            Statistics about the conversion process with keys:
            - processed: number of successfully converted files
            - failed: number of failed conversions
            - errors: list of error messages
        """
        stats = {"processed": 0, "failed": 0, "errors": []}

        yaml_files = basefunctions.create_file_list(
            pattern_list=["*.yaml", "*.yml"],
            dir_name=self.target_directory,
            recursive=True,
            add_hidden_files=False,
        )

        self.logger.info(f"Found {len(yaml_files)} YAML files to convert")

        for yaml_file in yaml_files:
            try:
                self._convert_single_file(yaml_file)
                stats["processed"] += 1
                self.logger.info(f"Successfully converted: {yaml_file}")
            except Exception as e:
                stats["failed"] += 1
                error_msg = f"Failed to convert {yaml_file}: {str(e)}"
                stats["errors"].append(error_msg)
                self.logger.error(error_msg)

        return stats

    def _convert_single_file(self, yaml_file_path: str) -> None:
        """
        Convert a single YAML file to JSON and remove original.

        Parameters
        ----------
        yaml_file_path : str
            Path to the YAML file to convert.

        Raises
        ------
        Exception
            If file reading, conversion, or writing fails.
        """
        # Read YAML content
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            yaml_content = yaml.safe_load(file)

        # Generate JSON file path
        json_file_path = basefunctions.get_path_without_extension(yaml_file_path) + ".json"

        # Write JSON content
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(yaml_content, file, indent=2, ensure_ascii=False)

        # Remove original YAML file
        basefunctions.remove_file(yaml_file_path)


def convert_yaml_to_json(directory_path: str) -> dict:
    """
    Convenience function to convert YAML files to JSON in a directory.

    Parameters
    ----------
    directory_path : str
        Path to directory containing YAML files.

    Returns
    -------
    dict
        Conversion statistics.
    """
    converter = YamlToJsonConverter(directory_path)
    return converter.convert_directory()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python yaml_to_json_converter.py <directory_path>")
        sys.exit(1)

    target_dir = sys.argv[1]
    result = convert_yaml_to_json(target_dir)

    print(f"Conversion completed:")
    print(f"  Processed: {result['processed']} files")
    print(f"  Failed: {result['failed']} files")

    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
