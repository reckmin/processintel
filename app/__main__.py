import os
from streamlit import config
from streamlit.web.bootstrap import run as streamlit_run


def parse_env_value(value: str):
    v = value.strip()

    if v.lower() in ("true", "false"):
        return v.lower() == "true"

    if v.isdigit():
        return int(v)
    return v


def env_to_config_key(env_key: str) -> str:
    key = env_key[10:].lower()
    parts = key.split("_")
    section = parts[0]
    option = parts[1:]

    option_camel_case = option[0] + "".join(w.capitalize() for w in option[1:])

    if option_camel_case == "enableCors":
        option_camel_case = "enableCORS"

    return f"{section}.{option_camel_case}"


def apply_streamlit_env(prefix="STREAMLIT_"):

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        config_key = env_to_config_key(env_key)
        value = parse_env_value(env_value)

        try:
            config.set_option(config_key, value)
        except Exception as e:
            print(e)


def main():
    apply_streamlit_env()

    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    streamlit_run(
        app_path,
        is_hello=False,
        args=[],
        flag_options={},
    )


if __name__ == "__main__":
    main()
