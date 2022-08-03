import os
import json
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import pandas as pd
import re
import time
load_dotenv()
CHROMEDRIVER_PATH = "./chromedriver.exe"


service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service)

output_df = pd.DataFrame(
    columns=[
        "keyword", 
        "id", 
        "title", 
        "company", 
        "location", 
        "post_date", 
        "work_type", 
        "applicant_count", 
        "description", 
        "data_analyst", 
        "bi_analyst", 
        "data_engineer", 
        "data_scientist", 
        "etl_developer",
        "business_information",
        "analyst"
        ]
)

def main():
    # get current time
    current_time = time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())
    output_file = "output_" + current_time + ".csv"
    output_df.to_csv(output_file, index=False)

    login()
    keywords = ['"Data Analyst"', '"BI Analyst"',
                '"Data Engineer"', '"Data Scientist"',
                '"ETL Developer"', '"Business Information"',
                '"Analyst"'
                ]
    for keyword in keywords:
        search_jobs(keyword, "Indonesia", output_file)

    # save output to output.csv
    output_df.to_csv(output_file, index=False)


def login():
    url = "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
    driver.get(url)

    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    sleep(5)

    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CLASS_NAME, "btn__primary--large").click()
    sleep(5)

jobs_id = set()
def search_jobs(keyword, location, output_file_name):
    # max linkedin is 1000 (40 pages)

    global output_df
    for page in range(0, 40):
        url = "https://www.linkedin.com/jobs/search/?keywords=" + \
            keyword + "&location=" + location + "&start=" + str(page*25)
        driver.get(url)
        if "No matching jobs found." in driver.page_source:
            break
        
        for _ in range(3):
            sleep(3)
            try:
                current_job = driver.find_element(
                    By.CLASS_NAME, "job-card-list__title")
                break
            except:
                continue

        while current_job is not None:

            # scrolldown until current_job is in view
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", current_job)
            current_job.click()
            sleep(2)

            current_url = driver.current_url
            id = re.findall(r'currentJobId=(\d+)', current_url)[0]

            if id in jobs_id:

                
                index = output_df.index[output_df['id'] == id].tolist()[0]
                # set keyword column to 1
                keyword_column = ""
                if keyword == '"Data Analyst"':
                    keyword_column = "data_analyst"
                elif keyword == '"BI Analyst"':
                    keyword_column = "bi_analyst"
                elif keyword == '"Data Engineer"':
                    keyword_column = "data_engineer"
                elif keyword == '"Data Scientist"':
                    keyword_column = "data_scientist"
                elif keyword == '"ETL Developer"':
                    keyword_column = "etl_developer"
                elif keyword == '"Business Information"':
                    keyword_column = "business_information"
                elif keyword == '"Analyst"':
                    keyword_column = "analyst"
                output_df.at[index, keyword_column] = 1  
                driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, current_job)
                try:
                    current_job = driver.find_element(
                    By.CLASS_NAME, "job-card-list__title")
                except:
                    current_job = None
                continue

            jobs_id.add(id)

            job_title = driver.find_element(
                By.CLASS_NAME, "jobs-unified-top-card__job-title").text
            primary_description = driver.find_element(
                By.CLASS_NAME, "jobs-unified-top-card__primary-description")
            first = primary_description.find_element(
                By.CLASS_NAME, "jobs-unified-top-card__subtitle-primary-grouping")
            second = primary_description.find_element(
                By.CLASS_NAME, "jobs-unified-top-card__subtitle-secondary-grouping")

            # get all elements in first
            first_elements = first.find_elements(By.TAG_NAME, "span")
            second_elements = second.find_elements(By.TAG_NAME, "span")

            company_name = first_elements[0].text
            company_location = first_elements[1].text
            if len(first_elements) > 2:
                work_type = first_elements[2].text
            else:
                work_type = ""

            post_date = second_elements[0].text
            if len(second_elements) > 1:
                applicant_count = second_elements[1].text
            else:
                applicant_count = "0"

            # get the job description
            jobs_article = driver.find_element(
                By.CLASS_NAME, "jobs-description__container")
            jobs_description = jobs_article.find_elements(
                By.TAG_NAME, "span")[-1].text

            row = {
                "keyword": [keyword],
                "id": [id],
                "title": [job_title],
                "company": [company_name],
                "location": [company_location],
                "post_date": [post_date],
                "work_type": [work_type],
                "applicant_count": [applicant_count],
                "description": [jobs_description],
                "data_analyst": [1 if keyword == '"Data Analyst"' else 0],
                "bi_analyst": [1 if keyword == '"BI Analyst"' else 0],
                "data_engineer": [1 if keyword == '"Data Engineer"' else 0],
                "data_scientist": [1 if keyword == '"Data Scientist"' else 0],
                "etl_developer": [1 if keyword == '"ETL Developer"' else 0],
                "business_information": [1 if keyword == '"Business Information"' else 0],
                "analyst": [1 if keyword == '"Analyst"' else 0]
            }

            # concat row to output_df
            output_df = pd.concat([output_df, pd.DataFrame(row)], ignore_index=True)
            # save
            output_df.to_csv(output_file_name, index=False)

            driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, current_job)

            # select next current job
            try:
                current_job = driver.find_element(
                    By.CLASS_NAME, "job-card-list__title")
            except:
                current_job = None



if __name__ == "__main__":
    main()
