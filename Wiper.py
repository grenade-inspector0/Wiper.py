import os
import time
import threading
import subprocess

def clear():
    os.system("clear")

def is_root():
    try:
        subprocess.run(["sudo", "-n", "true"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def keep_sudo_alive():
    while True:
        subprocess.run(["sudo", "-n", "true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 
        time.sleep(30)

def get_answer(question, accepted_answers=None, display_drives=False):
    while True:
        clear()
        if display_drives: # Display the drives if enabled
            os.system("lsblk")
        answer = input(f"{question}\n\n> ").lower()
        if accepted_answers != None and isinstance(accepted_answers, list):
            if answer not in accepted_answers:
                continue
        break
    return answer

def format_drive(block_device, filesystem_type="ext4"):
    os.system(f"sudo umount {block_device}* 2>/dev/null")
    match filesystem_type:
        case "ext4":
            command = f"mkfs.{filesystem_type} -F {block_device}"
        case "exfat":
            command = f"mkfs.{filesystem_type} {block_device}"
        case "ntfs":
            command = f"mkfs.{filesystem_type} -f {block_device}"
    os.system(command)

def wipe_drive(block_device, wiping_type="random"):
    os.system(f"sudo umount {block_device}* 2>/dev/null")
    wiping_method = "/dev/zero" if wiping_type == "zero" else "/dev/urandom"
    try:
        os.system(f"dd if={wiping_method} of={block_device} status=progress bs=1M") # Fill the selected drive with the selected "wiping_type"
    except:
        return
    return

clear()

# Make sure the script has root privileges 
if not is_root():
    print("This script must be ran using sudo.")
    time.sleep(3)
    clear()
    exit()

# This is needed to keep the sudo status in order to run the commands
thread = threading.Thread(target=keep_sudo_alive, daemon=True)
thread.start()

block_device = None
passes = 0
zeroing = False
formatting = {"enabled": True, "format_type": None}



# Have the user select the drive that they wish to wipe; DONE
block_device = f"/dev/{get_answer("\nWhich drive do you want to wipe? (Enter sda, sdb, etc.)", display_drives=True)}"

# Ask the user how many passes they want to do?; DONE
answer = get_answer("""Options:
1. 3 Passes (Safe; Long Amount of Time)
2. 5 Passes (Very Safe; Very Long Among of Time)
3. 7 Passes (Unnecessary unless you're doing something shady; In some cases it will take days to finish)

IMPORTANT - Each \"Pass\" is one full wipe of the drive using randomly generated data. (Bigger Size = Longer Time per Pass)
How many passes do you want to do?""", ["1", "2", "3"])

match answer:
    case "1":
        passes = 3
    case "2":
        passes = 5
    case _:
        passes = 7



# Ask the user if they wish to do a final wipe of zeroing the drive; DONE
answer = get_answer("Would you like to do a final wipe using zeroing? (Y/N)\nA final round of zeroing is recommended, but not necessary.", ["yes", "no", "y", "n"])
if answer in ["yes", "y"]:
    zeroing = True



# Ask the user if they want to format the drive after the final wipe, and what filesystem type it should be 
answer = get_answer("Would you like to format your drive after all passes have been done? (Y/N)", ["yes", "no", "y", "n"])
if answer in ["yes", "y"]:
    answer = get_answer("""Options:
1. ext4 Filesystem (Linux)
2. exfat Filesystem (Linux, Windows) 
3. ntfs Filesystem (Windows)
4. Cancel Formatting

When formatting the drive, which filesystem do you want to format it to?""", ["1", "2", "3", "4"])


match answer: 
    case "1":
        formatting["format_type"] = "ext4"
    case "2":
        formatting["format_type"] = "exfat"
    case "3":
        formatting["format_type"] = "ntfs"
    case _: # This uses the wildcard so that formatting can be disabled if the user denies the first question about formatting or if they wish to cancel the formatting
        formatting["enabled"] = False



for x in range(1, passes+1): # Wipe the drive for the user's choosen amount of passes.
    print(f"Starting Pass {x}...")

    # Wipe the drive using randomly generated data from /dev/urandom
    wipe_drive(block_device)

    print(f"Successfully finished Pass {x}!\n")



# Do a Final Pass of Zeroes if enabled by the user
if zeroing:
    wipe_drive(block_device, "zero")



# Format the drive after the final pass
if formatting["enabled"]:
    format_drive(block_device, formatting["format_type"])