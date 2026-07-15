import requests

BASE_URL = "http://127.0.0.1:8000/api/chat"

client_id = "local-test"

print("=== Chat Test ===")
print("exit 입력 시 종료\n")

while True:
    message = input("You > ").strip()

    if message.lower() == "exit":
        break

    payload = {
        "message": message,
        "client_id": client_id,
    }

    try:
        response = requests.post(
            BASE_URL,
            json=payload,
            timeout=60,
        )

        print(f"\nHTTP {response.status_code}")

        if response.ok:
            data = response.json()
            print(f"Bot > {data['answer']}\n")
        else:
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}\n")