from openpyxl import load_workbook
from datetime import datetime
from pathlib import Path
import pandas as pd


def save_data(filename, region, final_df):
    """
    Creates a DataFrame from passed list and saves an excel file based on rules

    :param filename: Name to save excel file as
    :param region: Name of the region
    :param final_df: Final Data Frame from format_data()
    """

    save_filename = filename + '.xlsx'
    check_path = Path(save_filename)

    # Checking if file already exists
    if check_path.exists():
        print(f'\nFilename {filename}.xlsx already exists, adding new sheet')
        book = load_workbook(save_filename)
        writer = pd.ExcelWriter(save_filename, engine='openpyxl')
        writer.book = book

        # If file already exists, add data into a new Excel Sheet
        final_df.to_excel(writer, sheet_name=region + f' ({datetime.today().strftime("%b-%d")})', index=0)
        writer.save()
        writer.close()
    else:
        print(f'\nFilename {filename}.xlsx doesnt exist, creating new file')

        # If file doesnt exist, put data into a new Excel file
        final_df.to_excel(save_filename, sheet_name=region + f' ({datetime.today().strftime("%b-%d")})', index=0)
