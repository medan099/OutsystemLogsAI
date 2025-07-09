"""
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import gridfs

# 👉 1. Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["forum_data"]  # Database will be created automatically
fs = gridfs.GridFS(db)  # GridFS to store images
collection = db["outsystems_forum"]  # Collection for forum data

# 👉 2. Start Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run without GUI
driver = webdriver.Chrome(options=options)

# 👉 3. Open the OutSystems Community forum
driver.get("https://www.outsystems.com/forums/")
wait = WebDriverWait(driver, 10)

# 👉 4. Extract problem posts
forum_data = []
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.text-neutral-8")))
problems = driver.find_elements(By.CSS_SELECTOR, "a.text-neutral-8")

# Function to extract text and download images
def extract_text_and_images(element):
    text_with_images = []
    image_ids = []
    paragraphs = element.find_elements(By.TAG_NAME, "p")

    for idx, p in enumerate(paragraphs):
        img_elements = p.find_elements(By.TAG_NAME, "img")
        
        if img_elements:
            for img in img_elements:
                image_url = img.get_attribute("src")
                
                # Download and store image in GridFS
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    image_id = fs.put(image_response.content, filename=f"image_{idx}.jpg")
                    image_ids.append(str(image_id))
                
                # Replace in text
                text_with_images.append(f"[Image_{idx}]")  
        else:
            text_with_images.append(p.text.strip())

    return "\n\n".join(text_with_images), image_ids

# 👉 5. Loop through problem posts
for problem in problems[:5]:  # Scrape first 5 problems for testing
    problem_title = problem.text
    problem_url = problem.get_attribute("href")

    # Open problem in new tab
    driver.execute_script("window.open(arguments[0]);", problem_url)
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(2)

    # Extract problem description
    try:
        description_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.margin-top-m.fr-view")))
        formatted_text, image_ids = extract_text_and_images(description_element)

        problem_description = {
            "text": formatted_text,
            "images": image_ids
        }
    except:
        problem_description = {"text": "No description found", "images": []}

    # Extract solutions
    solutions = []
    try:
        solution_elements = driver.find_elements(By.CSS_SELECTOR, "div.image-zoom")
        for solution in solution_elements:
            formatted_solution_text, solution_image_ids = extract_text_and_images(solution)

            solutions.append({
                "text": formatted_solution_text,
                "images": solution_image_ids
            })
    except:
        solutions.append({"text": "No solutions found", "images": []})

    # Save to MongoDB
    document = {
        "title": problem_title,
        "url": problem_url,
        "description": problem_description,
        "solutions": solutions
    }
    
    collection.insert_one(document)

    # Close problem tab & return to forum page
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

# Close WebDriver
driver.quit()

print("✅ Scraping complete! Data & images stored in MongoDB.")



"""































"""
import time
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import gridfs

# Initialize WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["outsystems_forum_db"]
forum_collection = db["outsystems_forum"]
fs = gridfs.GridFS(db)

# Function to close the cookie banner
def close_cookie_banner():
    try:
        cookie_banner = wait.until(EC.presence_of_element_located((By.ID, "onetrust-policy-text")))
        accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_button.click()
        print("✅ Cookie banner closed.")
        time.sleep(2)  # Wait for banner to disappear
    except:
        print("ℹ️ No cookie banner found.")

# Function to extract text and images
def extract_text_and_images(element):
    text_with_images = []
    image_references = []

    paragraphs = element.find_elements(By.TAG_NAME, "p")

    for i, p in enumerate(paragraphs):
        img = p.find_elements(By.TAG_NAME, "img")
        if img:
            img_url = img[0].get_attribute("src")

            # Download and store the image in GridFS
            try:
                response = requests.get(img_url)
                if response.status_code == 200:
                    image_id = fs.put(BytesIO(response.content), filename=f"image_{i}.jpg")
                    text_with_images.append(f"[Image_{i}]")
                    image_references.append(str(image_id))  # Store ObjectId reference
            except Exception as e:
                print(f"❌ Error downloading image: {e}")
        else:
            text_with_images.append(p.text.strip())

    return "\n\n".join(text_with_images), image_references

# Start scraping from the first page
page_number = 1
driver.get("https://www.outsystems.com/forums/")
time.sleep(3)
close_cookie_banner()  # Handle banner on first page

while True:
    print(f"📄 Scraping page {page_number}...")

    # Extract problem titles and links
    problems = driver.find_elements(By.CSS_SELECTOR, "a.text-neutral-8")

    for problem in problems:
        problem_title = problem.text
        problem_url = problem.get_attribute("href")

        # Open problem page in a new tab
        driver.execute_script("window.open(arguments[0]);", problem_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        # Extract problem description
        try:
            description_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.margin-top-m.fr-view")))
            description_text, description_images = extract_text_and_images(description_element)
            problem_description = {"text": description_text, "images": description_images}
        except:
            problem_description = {"text": "No description found", "images": []}

        # Extract solutions
        solutions = []
        try:
            solution_elements = driver.find_elements(By.CSS_SELECTOR, "div.image-zoom")
            for j, solution in enumerate(solution_elements):
                solution_text, solution_images = extract_text_and_images(solution)
                solutions.append({"text": solution_text, "images": solution_images})
        except:
            solutions.append({"text": "No solutions found", "images": []})

        # Save data to MongoDB
        forum_collection.insert_one({
            "title": problem_title,
            "url": problem_url,
            "description": problem_description,
            "solutions": solutions
        })

        print(f"✅ Saved: {problem_title}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    # Try to find the "Next" button
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a.pagination-next")
        if next_button.is_displayed():
            next_button.click()
            page_number += 1
            time.sleep(3)
            close_cookie_banner()  # Close banner again if it reappears
        else:
            break  # No more pages
    except:
        break  # Stop if next button is not found

# Close WebDriver
driver.quit()

print("🎉 Scraping complete! All data saved to MongoDB.")
"""




import time
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import gridfs

# Initialize WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["outsystems_forum_db"]
forum_collection = db["outsystems_forum"]
fs = gridfs.GridFS(db)

# Function to close the cookie banner
def close_cookie_banner():
    try:
        cookie_banner = wait.until(EC.presence_of_element_located((By.ID, "onetrust-policy-text")))
        accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_button.click()
        print("✅ Cookie banner closed.")
        time.sleep(2)  # Wait for banner to disappear
    except:
        print("ℹ️ No cookie banner found.")

# Function to extract text and images
def extract_text_and_images(element):
    text_with_images = []
    image_references = []

    paragraphs = element.find_elements(By.TAG_NAME, "p")

    for i, p in enumerate(paragraphs):
        img = p.find_elements(By.TAG_NAME, "img")
        if img:
            img_url = img[0].get_attribute("src")

            # Download and store the image in GridFS
            try:
                response = requests.get(img_url)
                if response.status_code == 200:
                    image_id = fs.put(BytesIO(response.content), filename=f"image_{i}.jpg")
                    text_with_images.append(f"[Image_{i}]")
                    image_references.append(str(image_id))  # Store ObjectId reference
            except Exception as e:
                print(f"❌ Error downloading image: {e}")
        else:
            text_with_images.append(p.text.strip())

    return "\n\n".join(text_with_images), image_references

# Start scraping from the first page
page_number = 1
driver.get("https://www.outsystems.com/forums/")
time.sleep(3)
close_cookie_banner()  # Handle banner on first page

while True:
    print(f"📄 Scraping page {page_number}...")

    # Extract problem titles and links
    problems = driver.find_elements(By.CSS_SELECTOR, "a.text-neutral-8")

    for problem in problems:
        problem_title = problem.text
        problem_url = problem.get_attribute("href")

        # Open problem page in a new tab
        driver.execute_script("window.open(arguments[0]);", problem_url)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        # Extract problem description
        try:
            description_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.margin-top-m.fr-view")))
            description_text, description_images = extract_text_and_images(description_element)
            problem_description = {"text": description_text, "images": description_images}
        except:
            problem_description = {"text": "No description found", "images": []}

        # Extract solutions
        solutions = []
        try:
            solution_elements = driver.find_elements(By.CSS_SELECTOR, "div.image-zoom")
            for j, solution in enumerate(solution_elements):
                solution_text, solution_images = extract_text_and_images(solution)
                solutions.append({"text": solution_text, "images": solution_images})
        except:
            solutions.append({"text": "No solutions found", "images": []})

        # Save data to MongoDB
        forum_collection.insert_one({
            "title": problem_title,
            "url": problem_url,
            "description": problem_description,
            "solutions": solutions
        })

        print(f"✅ Saved: {problem_title}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    # Try to find the "Next" button using the correct selector
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a.ListNavigation_Next")
        if next_button.is_displayed():
            next_button.click()
            page_number += 1
            time.sleep(3)
            close_cookie_banner()  # Close banner again if it reappears
        else:
            break  # No more pages
    except Exception as e:
        print(f"❌ Error finding next button: {e}")
        break  # Stop if next button is not found

# Close WebDriver
driver.quit()

print("🎉 Scraping complete! All data saved to MongoDB.")
















































































