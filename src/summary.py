import os
from datetime import datetime, timezone

def message_log_normalize(message):
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    new_message = f"{current_date}: " \
    +  message.replace("--", "").replace("\n", "").replace(">", "").replace("<", "")

    return new_message

# Write new content to the file everyday
def writeline_message_to_file(message, path):
    # check file exist
    if os.path.exists(path):
        # Read the final content from the file
        with open(path, "r") as file:
            last_line = file.readlines()[-1].strip()

        # Get the last date that the content was written to the file
        last_date = str(datetime.strptime(last_line.split()[0], "%Y-%m-%d").date())

        # Get the current day
        today = str(datetime.now(timezone.utc).strftime('%Y-%m-%d'))

        # Checks if the current date is different from the last date that was written to the file
        if today != last_date:
            # Write new content to file
            with open(path, "a") as f:
                f.write(message + "\n")
    else:
        with open(path, "a") as f:
            f.write(message + "\n")

def read_file(path):
    lines = []

    with open(path, "r") as f:
        for line in f:
            lines.append(line.strip())
    return lines

def sumary(list_messages):
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    new_message  = f"\n------------------>>> Summary of the day: {current_date} <<<------------------\n" 

    for message in list_messages:
        new_message += f"{message}\n"
    print (new_message)

#----------------------------------------------------------
path = r"..\storage\example.txt"
