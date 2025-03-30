import asyncio
import random
import pytz
from datetime import datetime, timedelta
from google.cloud import firestore

from linkedin_scrapper import scrape_linkedin_jobs, convert_posted_time_to_datetime, format_posted_time_local  # Reuse your defined scraper logic
import os
from google.cloud import firestore
import base64
import json
# Add this before initializing Firestore client
firebase_json_base64 = os.environ["FIREBASE_CREDENTIALS"]
firebase_json = base64.b64decode(firebase_json_base64).decode("utf-8")

with open("firebase_creds.json", "w") as f:
    f.write(firebase_json)

# Set the environment variable for Firestore client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase_creds.json"

firestore_client = firestore.Client()

# Define your target queries and role type filters
JOB_QUERIES = [[
    ("sde intern", "Internship"),
    ("software developer intern", "Internship"),
    ("machine learning intern", "Internship"),
    ("backend developer intern", "Internship"),
    ("full stack developer intern", "Internship"),
    ("frontend developer intern", "Internship"),
    ("data scientist intern", "Internship"),
    ("software engineer intern", "Internship"),
    ("software development engineer intern", "Internship")],[
    ("frontend developer", "Full-time"),
("software development engineer", "Full-time"),
    ("software developer", "Full-time"),
    ("software engineer", "Full-time"),
    ("frontend developer", "Full-time"),
    ("backend developer", "Full-time")]
]

# Define your collection
COLLECTION_NAME = "linkedin_jobs"

# Function to check if job already exists based on URL
async def job_exists(job_url):
    docs = firestore_client.collection(COLLECTION_NAME).where("url", "==", job_url).stream()
    return any(True for _ in docs)

# Save job to Firestore
async def save_job(job_data):
    firestore_client.collection(COLLECTION_NAME).add(job_data)
def save_job_to_firestore(job, firestore_client):
    job_type = job.get("job_type", "Unknown").replace(" ", "-")
    job_id = f"{job['title']}_{job['company']}_{job['location']}".replace(" ", "_").replace("/", "_")
    doc_ref = firestore_client.collection("jobs").document(job_type).collection("postings").document(job_id)
    if not doc_ref.get().exists:
        doc_ref.set(job)
        print(f"[+] Saved new job to Firestore: {job['title']} ({job_type})")
    else:
        print(f"[=] Skipped duplicate job: {job['title']} ({job_type})")
# Run scraper for a single query-role pair
async def run_single_scrape(query, role_type):
    print(f"[SCRAPE] Running for: {query} | {role_type}")
    jobs = await scrape_linkedin_jobs(query=query, location="United States", role_type_filter=role_type,limit=25)

    for job in jobs:
        if await job_exists(job["url"]):
            print(f"[SKIP] Duplicate job: {job['title']}")
            continue

        # Convert posting time to UTC and local time
        try:
            utc_time = convert_posted_time_to_datetime(job["posted"])
            job["posted"] = utc_time.isoformat()
            job["posted_local"] = format_posted_time_local(utc_time, timezone_str="America/New_York")
        except:
            job["posted_local"] = job["posted"]

        save_job_to_firestore(job, firestore_client)

        print(f"[SAVED] {job['title']} | {job['company']}")

# Random cron runner
async def run_cron_scraper():
    while True:
        queries = random.choice(JOB_QUERIES)
        print(queries)
        for query, role in queries:
            await run_single_scrape(query, role)

        next_sleep = random.choice([300, 600, 900, 1200, 1800,3600,1500,1000,])  # 5m, 10m, 15m, 20m, 30m
        print(f"[WAIT] Sleeping for {next_sleep // 60} minutes...")
        await asyncio.sleep(next_sleep)

if __name__ == "__main__":
    asyncio.run(run_cron_scraper())
