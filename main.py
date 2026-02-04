import requests
import json
import os


USERNAME = os.getenv("LMS_USERNAME")
PASSWORD = os.getenv("LMS_PASSWORD")
CLIENT_ID = "2Mp4P7aMBAPPBRSQCjZj1NlXeAO"

NTFY_TOPIC = "lms-test-alert"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

SEEN_FILE = "seen_items.json"

SUBJECT_IDS = [
    "2qkYeO6fJinvl4bBeWU1OH9AFDf",
    "2qkYU8NjqIl1D8QakYVgIEJGEWu",
    "2qkYVDmdGo6BlKoDmP3rAkXsqoX",
    "2qkYctxmI1KaMJRvs6Ne6K96u6z",
    "2qkYlLPDGQ2npjN5gz75dVv4sF6",
    "2qkYjtGmgU9oY3IYPZvA19T05qo",
    "2qkYXHshDqmpyYHFbYVbCrMJlwz",
    "2qkYbNYulvHwNAXyxZYSDoOMiLD",
    "2qkYg2SNF99fyIKQe6FHBobZd5w",
    "2qkYhRzhmtnBU5Ci8nLIWVa4cJx",
    "2qkYifq4upSAioJRLVqrLmyzjCu",
    "37y8SzaYi3tUtUEhnIj3sbqpLLx",
    "37y8V3azre3AeSDSQuIdo4uGkgo",
    "37y8WoSePg5vO0Gh8sDXtovd58d",
    "37y8n1VQ942cUAdZWhlcAI7lh0L",
    "37y8olRZnjUN3szXzsuJH81EVJz",
    "37yN9V6EstKy9MBZoG7US4zr1QD",
    "37yNXrvoY5oC6R8CHIwdp9yEcCw",
    "37yNZXsAwBT8SySZ7iWiUcBfRGq",
    "37yOmjORGQAkhhs1qL30EqXYE52",
    "37yPKkb4w6VDj5HNOjxo6XeXXSv",
    "37yPIoqVjsibeEFKyiMHd2rW4x6",
    "37ySo49AgNHsM2TSeFsFNKex8Ys"
]

ACADEMIC_YEAR_ID = "2ycpIJ1qn1MIgmRjtnqLQSQwRaa"
AFFILIATION_ID = "28bTVsrHG2srx1S73PrT9TJTCk0"
STANDARD_ID = "2i396B1MdY3gOsjXIv0B8lJKv9r"
DIVISION_ID = "2UCD3VlHbJzoDCXGFF1eXgDnPGJ"
USER_ID = "2UnIOW2MU3QtyqXiOfgdyhiyfSE"



def send_ntfy(title, message):
    headers = {"Title": title, "Priority": "5"}
    requests.post(NTFY_URL, data=message.encode("utf-8"), headers=headers)


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {"tests": [], "quizzes": []}


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


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
    headers = {"Content-Type": "application/json", "Service-Header": "LoginService"}
    r = requests.post(url, json=payload, headers=headers)
    token = r.headers.get("Authorization")
    if not token:
        raise Exception("Token not found")
    print("Token OK")
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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = requests.post(url, json=payload, headers=headers).json()
    return data.get("result", {}).get("testData", [])


def fetch_quizzes(token):
    url = "https://era.mkcl.org/NewLMSFramework2021/r/mql"

    all_quizzes = []
    skip = 0
    limit = 20

    while True:
        payload = {
            "fetchQuizListForStudent": {
                "clientId": CLIENT_ID,
                "subjectIdList": SUBJECT_IDS,
                "standardId": STANDARD_ID,
                "divisionId": DIVISION_ID,
                "academicYearId": ACADEMIC_YEAR_ID,
                "affiliationAuthorityId": AFFILIATION_ID,
                "studentId": USER_ID,
                "filter": "",
                "skip": skip,
                "limit": limit
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Service-Header": "fetchQuizListForStudent"
        }

        r = requests.post(url, json=payload, headers=headers)
        data = r.json()

        quiz_list = (
            data.get("fetchQuizListForStudent", {})
                .get("result", {})
                .get("getQuizList", [])
        )

        if not quiz_list:
            break 

        all_quizzes.extend(quiz_list)
        skip += limit

    return all_quizzes


def main():
    token = login_and_get_token()
    seen = load_seen()

    for subject_id in SUBJECT_IDS:
        tests = fetch_tests(token, subject_id)
        for t in tests:
            test = t.get("test", t)
            tid = test.get("testId")
            name = test.get("testName")
            subject = t.get("subjects", {}).get("subjectName", "Unknown")

            if tid and tid not in seen["tests"]:
                seen["tests"].append(tid)
                msg = f"📝 New Test\n\n{name}\nSubject: {subject}"
                print(msg)
                send_ntfy("New Test", msg)

    quizzes = fetch_quizzes(token)
    for q in quizzes:
        qid = q.get("quizId")
        name = q.get("quizName")
        date = q.get("quizDate")
        time = q.get("quizTime")
        subject = q.get("subject", {}).get("subjectName", "Unknown")

        if qid and qid not in seen["quizzes"]:
            seen["quizzes"].append(qid)
            msg = f"🧠 New Quiz\n\n{name}\nSubject: {subject}\nDate: {date}\nTime: {time}"
            print(msg)
            send_ntfy("New Quiz", msg)

    save_seen(seen)
    print("Check complete")


if __name__ == "__main__":
    main()
