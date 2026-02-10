import requests

url = "https://backend-s2sj.onrender.com/auth/token"
headers = {"Origin": "https://frontend-psi-one-79.vercel.app"}

try:
    r = requests.options(url, headers=headers, timeout=10)
    print("OPTIONS", r.status_code)
    for k, v in r.headers.items():
        if k.lower().startswith("access-control") or k.lower().startswith("vary"):
            print(f"{k}: {v}")
    print()
except Exception as e:
    print("OPTIONS error", e)

try:
    r2 = requests.post(
        url, data={"username": "nope", "password": "nope"}, headers=headers, timeout=10
    )
    print("POST", r2.status_code)
    for k, v in r2.headers.items():
        if k.lower().startswith("access-control") or k.lower().startswith("vary"):
            print(f"{k}: {v}")
    print("BODY:")
    print(r2.text[:400])
except Exception as e:
    print("POST error", e)

# Additional checks: root and debug endpoints
for path in ["/", "/debug/cors"]:
    try:
        url2 = "https://backend-s2sj.onrender.com" + path
        r3 = requests.get(url2, headers=headers, timeout=10)
        print("\nGET", path, r3.status_code)
        for k, v in r3.headers.items():
            if k.lower().startswith("access-control") or k.lower().startswith("vary"):
                print(f"{k}: {v}")
        print("BODY:", r3.text[:400])
    except Exception as e:
        print("GET", path, "error", e)
