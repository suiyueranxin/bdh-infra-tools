import string
import random
def password_generate(password_length=30):
    """
    1. has > 30 chars
    2. has lower, upper and digits (unchanged)
    3. has at least three special chars, of which two are definitely of '?!#'
    """
    if password_length <= 0:
        raise Exception("incorrect password length!")
    special_chars = "?%!_+.#@*"
    necessary_chars = '?!#'
    possible_chars = special_chars + string.ascii_letters + string.digits
    random_password = "".join(random.sample(string.ascii_uppercase, 3)) \
    + "".join(random.sample(string.ascii_lowercase, 3)) \
    + "".join(random.sample(string.digits, 3)) \
    + "".join(random.sample(possible_chars, 21)) \
    + random.choice(necessary_chars) \
    + random.choice(necessary_chars) \
    + random.choice(special_chars)
    return random_password

if __name__ == "__main__":
    print(password_generate())
