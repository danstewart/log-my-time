def verify_turnstile(turnstile_response: str) -> bool:
    import requests
    from flask import current_app as app

    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        json={
            "secret": app.config["CF_TURNSTILE_SECRET_KEY"],
            "response": turnstile_response,
        },
    )

    return response.status_code == 200 and response.json()["success"]
