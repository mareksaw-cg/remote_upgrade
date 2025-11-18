import csv

def csv_to_bin_second_column(input_csv, output_bin):
    with open(input_csv, 'r') as csv_file, open(output_bin, 'wb') as bin_file:
        reader = csv.reader(csv_file, delimiter=';')  # Adjust delimiter if needed
        for row in reader:
            if len(row) >= 2:  # Ensure there are at least two columns
                try:
                    val = int(row[1])  # Take the second column
                    if 0 <= val <= 255:  # Ensure it fits in one byte
                        bin_file.write(val.to_bytes(1, byteorder='big'))
                    else:
                        print(f"Value {val} out of range (0-255), skipped.")
                except ValueError:
                    # Skip invalid rows or headers
                    continue
    print(f"Binary file '{output_bin}' created successfully.")

# Example usage:
csv_to_bin_second_column('data.csv', 'data8192.bin')
