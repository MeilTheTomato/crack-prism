import enum
import json
import os
import psutil
import subprocess
import sys


ACCOUNT_FILE_PATH = f"{os.getenv("APPDATA")}/PrismLauncher/accounts.json"
PRISM_LAUNCHER_EXE_PATH = f"{os.getenv("LOCALAPPDATA")}/Programs/PrismLauncher/prismlauncher.exe"
PRISM_LAUNCHER_PROCESS_NAME = "prismlauncher.exe"
SUPPORTED_FORMAT_VERSIONS = [3]


class AccountType(enum.IntEnum):
    Msa = 1
    Offline = 2
    Unknown = 3

class ErrorType(enum.IntEnum):
    IncompatibleFormatVersion = 1
    NoAccountFile = 2
    NoMsaAccount = 3
    def __str__(self):
        match self:
            case ErrorType.IncompatibleFormatVersion:
                return "The account file is not in a supported format."
            case ErrorType.NoAccountFile:
                return "The account file was not found. Is Prism Launcher installed?"
            case ErrorType.NoMsaAccount:
                return "No Microsoft Account was found. It doesn't matter whether you own Minecraft or not, please connect any Microsoft account to Prism Launcher."


def askBoolean(prompt: str) -> bool:
    userInput = ""

    while (userInput.lower() != "y") and (userInput.lower() != "n"):
        userInput = input(f"{prompt} (y/n): ")

    return (userInput.lower() == "y")

def checkFormatVersionCompatibility(data) -> bool:
    try:
        SUPPORTED_FORMAT_VERSIONS.index(data["formatVersion"])
    except:
        return False

    return True

def clearAndWriteToFile(file, data): # (w+ mode doesn't work with the json module for whatever reason)
    file.seek(0)
    json.dump(data, file)
    file.truncate()

def enableEntitlement(account):
    entitlement = account["entitlement"]

    entitlement["canPlayMinecraft"] = True
    entitlement["ownsMinecraft"] = True

def getAccountType(account) -> AccountType:
    match account["type"]:
        case "MSA":
            return AccountType.Msa
        case "Offline":
            return AccountType.Offline
        case _:
            return AccountType.Unknown

def openAccountFile(filePath):
    file = None

    try:
        file = open(filePath, mode = "r+", encoding = "utf-8")
    except:
        print(str(ErrorType.NoAccountFile))
        sys.exit(ErrorType.NoAccountFile)

    return file

def openPrismLauncher():
    isOpen = (PRISM_LAUNCHER_PROCESS_NAME in (process.name() for process in psutil.process_iter()))

    if isOpen:
        input = askBoolean("Prism Launcher needs to relaunch to apply changes, you can relaunch it later if needed. Relaunch now?")

        if input:
            subprocess.run(f"taskkill /im {PRISM_LAUNCHER_PROCESS_NAME}")
            os.startfile(PRISM_LAUNCHER_EXE_PATH)
    else:
        os.startfile(PRISM_LAUNCHER_EXE_PATH)


ACCOUNT_FILE = openAccountFile(ACCOUNT_FILE_PATH)
ACCOUNT_DATA = json.load(ACCOUNT_FILE)


msaAccountFound = False

if not checkFormatVersionCompatibility(ACCOUNT_DATA):
    print(str(ErrorType.IncompatibleFormatVersion))
    sys.exit(ErrorType.IncompatibleFormatVersion)
for account in ACCOUNT_DATA["accounts"]:
    if getAccountType(account) == AccountType.Msa:
        msaAccountFound = True
        enableEntitlement(account)
if not msaAccountFound:
    print(str(ErrorType.NoMsaAccount))
    sys.exit(ErrorType.NoMsaAccount)
clearAndWriteToFile(ACCOUNT_FILE, ACCOUNT_DATA)
openPrismLauncher()