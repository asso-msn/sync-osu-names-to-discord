import traceback

from config import config

if __name__ == "__main__":
    tests = ("peppy", "Tina_otoge", "should not exist")
    for test in tests:
        try:
            user_id = get_user_id_from_username(test)
            print(f"{user_id=}")
            username = get_username_from_user_id(user_id)
            print(f"{username=}")
        except Exception as e:

            traceback.print_exc()
    try:
        get_username_from_user_id(99999999999)
    except Exception as e:
        traceback.print_exc()
