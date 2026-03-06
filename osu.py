import httpx


def get_user_id_from_username(username: str) -> int:
    url = f"http://osu.ppy.sh/users/{username}"
    response = httpx.head(url)
    if "Location" not in response.headers:
        raise ValueError(
            f'Excpected a redirect to an user page when looking up "{url}", but'
            f" got {response}"
        )
    return int(response.headers["Location"].split("/")[-1])


def get_username_from_user_id(user_id: int) -> str:
    TITLE_START = "<title>"
    TITLE_END_PART = "\u202c · player info"
    buf = ""
    with httpx.stream("GET", f"http://osu.ppy.sh/users/{user_id}") as response:
        for chunk in response.iter_text():
            buf += chunk
            start = buf.find(TITLE_START)
            if start == -1:
                continue
            content = buf[start + len(TITLE_START) :]
            end = content.find(TITLE_END_PART)
            if end != -1:
                return content[:end]
    raise ValueError("Page does not seem to contain an username")


if __name__ == "__main__":
    import traceback

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
