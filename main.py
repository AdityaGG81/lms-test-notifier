import requests
import json
import os
import ssl
import urllib3
from datetime import datetime

# ================= SSL LEGACY FIX =================
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CONFIG =================

USERNAME = os.getenv("LMS_USERNAME")
PASSWORD = os.getenv("LMS_PASSWORD")

CLIENT_ID = "2Mp4P7aMBAPPBRSQCjZj1NlXeAO"

NTFY_TOPIC = "lms-test-alert-12345"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

SEEN_FILE = "seen_tests.json"

SUBJECT_IDS = [
    "37yNXrvoY5oC6R8CHIwdp9yEcCw",
    "37y8n1VQ942cUAdZWhlcAI7lh0L",
    "37yN9V6EstKy9MBZoG7US4zr1QD",
    "37yOmjORGQAkhhs1qL30EqXYE52",
    "37y8SzaYi3tUtUEhnIj3sbqpLLx",
    "37ySo49AgNHsM2TSeFsFNKex8Ys"
]

ACADEMIC_YEAR_ID = "2ycpIJ1qn1MIgmRjtnqLQSQwRaa"
AFFILIATION_ID = "28bTVsrHG2srx1S73PrT9TJTCk0"
STANDARD_ID = "2i396B1MdY3gOsjXIv0B8lJKv9r"
DIVISION_ID = "2UCD3VlHbJzoDCXGFF1eXgDnPGJ"
USER_ID = "2UnIOW2MU3QtyqXiOfgdyhiyfSE"


def within_college_hours():
    now = datetime.now()
    return 8 <= now.hour < 15


def send_ntfy(title, message):
    headers = {"Title": title}
    requests.post(NTFY_URL, data=message.encode(), headers=headers, verify=False)


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def login_and_get_token():
    url = "https://era.mkcl.org/NewLMSFramework2021/o/mql"

    payload = {
        "LoginService": {
            "userName": USERNAME,
            "password": PASSWORD,
            "clientId": CLIENT_ID,
            "instituteCategory": "Institutes",
            "institutetypeId": "2"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Service-Header": "LoginService"
    }

    r = requests.post(url, json=payload, headers=headers, verify=False)
    token = r.headers.get("Authorization")

    if not token:
        raise Exception("Token not found")

    print("✅ Token OK")
    return token


def fetch_tests(token, subject_id):
    url = "https://era.mkcl.org/lms/assessmentServer/r/getTestsAndStudentTestSubmissions"

    payload = {
        "clientId": CLIENT_ID,
        "academicYearId": ACADEMIC_YEAR_ID,
        "affiliationAuthorityId": AFFILIATION_ID,
        "standardId": STANDARD_ID,
        "divisionId": DIVISION_ID,
        "subjectId": subject_id,
        "userId": USER_ID,
        "filter": "",
        "skip": 0,
        "limit": 10
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers, verify=False)
    data = r.json()

    if data.get("error"):
        return []

    return data.get("result", {}).get("testData", [])


def main():
    if not within_college_hours():
        print("Outside college hours")
        return

    token = login_and_get_token()
    seen = load_seen()
    new_found = False

    for subject_id in SUBJECT_IDS:
        tests = fetch_tests(token, subject_id)

        for t in tests:
            test_obj = t.get("test", {})
            test_id = test_obj.get("testId")
            if not test_id:
                continue

            name = test_obj.get("testName")
            start = test_obj.get("startTime") or test_obj.get("testStartDateTime")
            end = test_obj.get("endTime") or test_obj.get("testEndDateTime")
            subject = t.get("subjects", {}).get("subjectName", "Unknown")

            if test_id not in seen:
                seen.add(test_id)
                new_found = True
                msg = f"📝 New Test\n{name}\n{subject}\n{start} → {end}"
                print(msg)
                send_ntfy("New Test", msg)

    save_seen(seen)

    if not new_found:
        print("No new tests")


if __name__ == "__main__":
    main()
