# csv_converter

## Description

This script was created for a user trying to convert data outputted from a tracking system into a billing system. The existing workflow was very manual and tedious. The script here is intended to run from the command line. The input file is converted into a pandas DataFrame where the values are then split and recombined as needed.

While this exact script will likely not be of much use, the format and template for dealing with csv columns and creating a new csv file should be reusable.

## Usage

The script is meant to be run from a terminal with the input file and output file passed as the first and second arguments, respectively. There is an optional verbose flag (-v) to print out each phase of the conversion.

```
python3 convert.py input_file.csv output_file.csv -v
```

