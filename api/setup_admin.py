import getpass

from auth import (
    ensure_database,
    create_admin
)


def main():

    ensure_database()

    print()
    print(
        "================================"
    )
    print(
        " KULZZY ADMINISTRATOR SETUP"
    )
    print(
        "================================"
    )
    print()

    username = input(
        "Administrator username: "
    ).strip()

    if not username:

        print(
            "Username cannot be empty."
        )

        return

    password = getpass.getpass(
        "Administrator password: "
    )

    confirmation = getpass.getpass(
        "Confirm password: "
    )

    if password != confirmation:

        print(
            "Passwords do not match."
        )

        return

    if len(password) < 12:

        print(
            "Password must contain at least 12 characters."
        )

        return

    try:

        create_admin(
            username,
            password,
            "owner"
        )

        print()
        print(
            "Administrator created successfully."
        )
        print()

    except Exception as error:

        print()
        print(
            "Could not create administrator:"
        )
        print(error)


if __name__ == "__main__":

    main()
