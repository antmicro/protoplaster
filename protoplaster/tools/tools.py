def assert_user_input(user_message,
                      assertion_message="User input failed",
                      possible_answers=["y", "n"],
                      correct_answer=0):
    answer = input(
        f"{user_message} [{'/'.join([ans.upper() if i == correct_answer else ans for i, ans in enumerate(possible_answers)])}] "
    )
    if answer != "":
        assert answer.lower() == possible_answers[correct_answer].lower()
