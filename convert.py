
# convert.py
# REQUIRES
install_requires=[
    'pandas']

# IMPORTS
try: 
	import pandas as pd
except ModuleNotFoundError:
	print("Module not found: pandas is not installed.")
	print("You can install pandas through your python package manager (e.g. pip3 install pandas)")
	exit

from datetime import datetime

# ARGUMENT INPUT AND HELP
import argparse
import sys
import os
MAX_LENGTH_OF_DX_CODE = 10 #Uset this value to make sure insurance providers are not caught up in DX codes

def create_arg_parser():
    """Creates and returns the ArgumentParser object."""

    parser = argparse.ArgumentParser(description='Convert csv files from one format to another')
    parser.add_argument('inputFilePath',
                    help='Path to the input file.')
    parser.add_argument('outputFilePath',
                    help='Path to the output file.')
    parser.add_argument('-v', action= 'store_true', default= False,
					 help = 'Verbose flag for printing each patient and their procesures to console window.')
    return parser

def get_dx(dxs, i):
	try:
		output = dxs[i-1].split('-')[0].replace(' ','')
		output = output if len(output) < MAX_LENGTH_OF_DX_CODE  else None
		return output
	except IndexError:
		#print("dxs only has {} items and you asked for {}, skipping this item.".format(len(dxs),i))
		return None

# Assign NPI Number by staff member
def get_npi(staff_member):
	
	npi_directory = {
					"Steve Rogers" : 12345678,
					"Tony Stark": 8765321
					}
	return npi_directory.get(staff_member, "not available")


if __name__ == "__main__":
	print("> Reading in given arguments...")

	arg_parser = create_arg_parser()
	parsed_args = arg_parser.parse_args(sys.argv[1:])
	isVerbose = parsed_args.v
	

	if os.path.exists(parsed_args.inputFilePath):
		print("  The input file does exists... proceeding.")
		# The file exists, continue
        
		input_data = pd.read_csv(parsed_args.inputFilePath)
		#  INPUT FORMAT
		#  Invoice_Date    Service_Date    Patient_guid    Patient Staff_Member    Invoice#    Cliam   Adjuster    Description Personal

		# Format date
		df = pd.DataFrame(input_data)
		output = pd.DataFrame()

		# Convert Dates
		date_columns = ['Service Date', 'Invoice Date', 'Birth Date', 'Date of Injury']
		print("> Converting dates...")
		for col in date_columns:
			try:
				df[col] = df[col].str.replace('[','')
				df[col] = df[col].str.replace(']','')
				df[col] = pd.to_datetime(df[col])
				#print("Column '{}'' done".format(col))
			except AttributeError:
				print("   The column '{}' does not contain text".format(col))

        # Split Decription
		
		print("> Working through details in each row (this make take a while if there are many rows)...")
		if not isVerbose: print("\tFYI- you can use the '-v' flag after the output file path to active verbose mode.")



		# Before going through every detail, go through eacch line to look for Co Pay or Eligible Amount values
		for index, row in df.iterrows():
			try:
				dos				= df['Service Date'].values[index]
				claim_ref		= df['Invoice #'].values[index]
				name			= df['Patient'].values[index].split(' ')
				try:
					first_name		= name[0]
					last_name		= name[1]
				except IndexError:
					last_name = ""
				staff_member	= df['Staff Member'].values[index]
				birth_date		= df['Birth Date'].values[index]
				claim			= df['Claim'].values[index]
				total			= df['Total'].values[index]
				balance			= df['Balance'].values[index]
				#paid			= total-balance
				procedures		= []
				procedureIndex	= []
				npi				= get_npi(staff_member)

				# Initial Values for Copay and Elligible Amount
				copay 			= None
				eligible_amount 	= None
				
				try:
					descriptionLines =  df['Description'].tolist()[index].split('\n')

					indexer = 0
					for line in descriptionLines:
						if 'x ' in line: 
							#print('{} is a procedure line'.format(line))
							procedures.append(line)
							procedureIndex.append(indexer)
						
						if 'Co Pay' in line: copay = line.split('$')[1] 
						if isVerbose: print("!!! Line ={}...containts copay = {}..{}".format(line, 'Co Pay' in line,True if copay else False))
						
						if 'Eligible amount' in line: eligible_amount = line.split('$')[1] 
						indexer += 1
					
					# Set Paid Amount
					_paid = 0 # default value
					
					# Check to see if copay or eligible amount items are in description
					if copay:
						# Then patient only pays copay
						_paid = copay
						if isVerbose: print("!!! COPAY = PAID = {}".format(_paid))
					elif eligible_amount:
						# No copay, paitent only pays eligible amount
						_paid = eligible_amount
					# Slicers for description
					prev = len(descriptionLines)
					curr = 0
					
					# Work from the bottom of the description when getting Dx numbers
					procedureIndex.reverse()
					procedureNumber = 0
					if isVerbose: print("> Procedures found for patient: [{}]. Amount paid = [{}], type: [{}]".format(
						first_name + ' '+last_name, _paid, 'Co Pay' if copay else 'Eligible amount' if eligible_amount else "None"))
					
					# Cycle through and get max amount first
					max_amount = 0
					for procedure in procedures:
						# The line contains counts and amounts
						# Amounts always in parenthesis with $ in front of value
						unit, temp_amount = procedure.split('(')
						temp_amount = float(temp_amount.replace(')','').replace('$',''))
						# Number of units always followed by 'x'
						unit = unit.split('x')[0]
						# Compare the amount of each procedure to find the max for all proceures in set
						max_amount = max(temp_amount, max_amount)
						if isVerbose: print('!!! The max amount is {}'.format(max_amount))
					isPaid = False
					for procedure in procedures:
						amount = float(procedure.split('(')[1].replace(')','').replace('$','')) 
						
						if amount == max_amount and not isPaid:
							isPaid = True
							paid = _paid
							if isVerbose: print('!!! The bill has been paid at {} ({}).'.format(_paid,amount))
							
						else: 
							if isVerbose: print('!!! Dont pay the bill..')
							paid = 0
						curr = procedureIndex[procedureNumber]
						code = procedure.split('x ')[1].split(' - ')[0]
						details = descriptionLines[curr:prev]
						dxs = details[1:]
						dx1 = get_dx(dxs, 1)
						dx2 = get_dx(dxs, 2)
						dx3 = get_dx(dxs, 3)
						dx4 = get_dx(dxs, 4)
						
						# Add a new line for each procedure
						if isVerbose: print("    Code = [{}], Amt =[{}], Dx1-4 = [{}]...adding to output".format(code, amount, [dx1,dx2,dx3,dx4]))
						prev = curr
						procedureNumber += 1
						# Create a DataFrame output which can be easily exported to csv
						output = output.append(pd.DataFrame({
							'DOS'			:[dos],
							'Claim Ref'		:[claim_ref],
							'First Name'	:[first_name],
							'Last Name'		:[last_name],
							'Staff Member'	:[staff_member],
							'Claim'			:[claim],
							'Birth Date'	:[birth_date],
							'Billing NPI'	:[npi],
							'Poc. Code'		:[code],
							'Units'			:[unit],
							'Dx1'			:[dx1],
							'Dx2'			:[dx2],
							'Dx3'			:[dx3],
							'Dx4'			:[dx4],
							'Amount Billed'	:[amount],
							'Amount Paid'	:[paid]

							}))
				except IndexError:
					print("Erorr setting values")
					next
			
			except AttributeError:
				print('> Error on row {}: Does not contain data in the expected format (may be empty)'.format(index))
				next

		output = output.reset_index()
		try:
			output.to_csv(path_or_buf = parsed_args.outputFilePath)
			print("SUCCESS! Output created at {}.".format(parsed_args.outputFilePath))
		except PermissionError:
			print("Error: Cannot write to file. The file may be open in another window.\n")
			print("\tPlease close the file and try again.")
		
	else:
		print('File does not exist')
