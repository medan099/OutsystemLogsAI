import json
import base64
from pymongo import MongoClient
from bson import ObjectId
import gridfs
import os

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['outsystems_forum_db']
fs = gridfs.GridFS(db)

# Fetch forum posts
posts = list(db.outsystems_forum.find({}))
processed_data = []
total_posts = len(posts)

if total_posts == 0:
    print("⚠️ No posts found in the database. Check your MongoDB connection and query.")

# Process posts
for index, post in enumerate(posts, start=1):
    title = post.get("title", "No Title")
    url = post.get("url", "No URL")
    description = post.get("description", {}).get("text", "")
    image_ids = post.get("description", {}).get("images", [])
    solutions = post.get("solutions", [])

    print(f"🔍 [{index}/{total_posts}] Processing post: {title}")
    print(f"📸 Images: {len(image_ids)} | 💡 Solutions: {len(solutions)}")

    # Embed images as Base64
    image_data = []
    for image_id in image_ids:
        try:
            image = fs.get(ObjectId(image_id))
            base64_image = base64.b64encode(image.read()).decode("utf-8")
            image_data.append(base64_image)
        except Exception as e:
            print(f"⚠️ Error retrieving image {image_id}: {e}")

    # Process solutions
    processed_solutions = []
    for solution in solutions:
        solution_text = solution.get("text", "")
        solution_images = solution.get("images", [])

        solution_image_data = []
        for sol_img_id in solution_images:
            try:
                sol_image = fs.get(ObjectId(sol_img_id))
                base64_sol_image = base64.b64encode(sol_image.read()).decode("utf-8")
                solution_image_data.append(base64_sol_image)
            except Exception as e:
                print(f"⚠️ Error retrieving solution image {sol_img_id}: {e}")

        processed_solutions.append({
            "text": solution_text,
            "images": solution_image_data
        })

    # Append processed post data
    processed_data.append({
        "title": title,
        "url": url,
        "description": description,
        "images": image_data,
        "solutions": processed_solutions
    })

    # Save progress every 100 posts
    if index % 100 == 0:
        temp_file = "processed_forum_data_temp.json"
        with open(temp_file, "w", encoding="utf-8") as temp_f:
            json.dump(processed_data, temp_f, ensure_ascii=False, indent=4)
        print(f"💾 Saved progress: {index}/{total_posts} posts processed.")

# Final save to JSON
output_file = "processed_forum_data.json"
if processed_data:
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())  # Force OS to write immediately
        print(f"✅ Final processed data saved to {output_file} ({len(processed_data)} posts).")
    except Exception as e:
        print(f"❌ Error writing to JSON: {e}")
else:
    print("❌ No data was processed. JSON file not created.")
