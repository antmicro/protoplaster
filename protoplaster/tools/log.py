from colorama import Fore, Style


def warning(text):
    return Fore.YELLOW + f"[WARNING] {text}" + Style.RESET_ALL


def pr_warn(text):
    print(warning(text))


def error(text):
    return Fore.RED + f"[ERROR] {text}" + Style.RESET_ALL


def pr_err(text):
    print(error(text))


def info(text):
    return f"[INFO] {text}"


def pr_info(text):
    print(info(text))
