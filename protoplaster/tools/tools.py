from colorama import Fore, Style


def assert_user_input(user_message,
                      assertion_message="User input failed",
                      possible_answers=["y", "n"],
                      correct_answer=0):
    answer = input(
        f"{user_message} [{'/'.join([ans.upper() if i == correct_answer else ans for i, ans in enumerate(possible_answers)])}] "
    )
    if answer != "":
        assert answer.lower() == possible_answers[correct_answer].lower()


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
