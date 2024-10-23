from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import socket


version= os.getenv('B_NUM')

if version is None:
    version='0.0.0'

host = socket.gethostname()

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Set up paths to align with the Bash script structure
alias = "topix"  # Set this to match the alias used in the Bash script
HOME_DIR = os.path.expanduser("~")
FILES_PATH = os.path.join(HOME_DIR, "script_files", alias)
DATA_DIR = os.path.join(FILES_PATH, "data")

# Ensure the directories exist
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Data directory: {DATA_DIR}")

# Route to search for topics
@app.route('/search', methods=['GET', 'POST'])
def search_topic():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        found_topics = []

        # Search by keyword in all JSON files
        for folder in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, folder)) and folder.isdigit():
                json_file = os.path.join(DATA_DIR, folder, f"{folder}.json")
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        for topic in data:
                            if search_term.lower() in topic["topic"].lower():
                                # Get the number of files in the 'files' folder
                                files_dir = os.path.join(DATA_DIR, folder, "files")
                                file_count = len(os.listdir(files_dir)) if os.path.exists(files_dir) else 0
                                
                                found_topics.append({
                                    'id': topic["topic_id"],  # Extract the topic ID
                                    'name': topic["topic"],    # Extract the topic name
                                    'folder': folder,          # Folder reference
                                    'file_count': file_count,  # Count the files
                                    'editor': topic["editor"]  # Extract the editor (author)
                                })

        if not found_topics:
            flash("No topics found with that term.", "danger")
        
        return render_template('search_results.html', topics=found_topics, search_term=search_term)

    return render_template('search.html')

@app.route('/files/<topic_id>/<filename>')
def download_file(topic_id, filename):
    folder_path = os.path.join(DATA_DIR, topic_id, "files")  # Path to the files folder
    return send_from_directory(folder_path, filename, as_attachment=True)

@app.route('/topic/<folder>/<id>/files', methods=['GET', 'POST'])
def manage_files(folder, id):
    topic_dir = os.path.join(DATA_DIR, folder)
    
    if not os.path.exists(topic_dir):
        flash(f"Topic directory for ID {id} not found.", "danger")
        return redirect(url_for('list_topics'))

    files_dir = os.path.join(topic_dir, 'files')
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    # Fetch the list of files
    files = []
    for filename in os.listdir(files_dir):
        filepath = os.path.join(files_dir, filename)
        file_size = os.path.getsize(filepath) / 1024  # File size in KB
        files.append({'name': filename, 'size': round(file_size, 2)})

    # If it's a POST request, we assume the user is uploading files
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        for uploaded_file in uploaded_files:
            if uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                uploaded_file.save(os.path.join(files_dir, filename))

        flash("Files uploaded successfully!", "success")
        return redirect(url_for('manage_files', folder=folder, id=id))

    # Load topic metadata (if needed)
    json_file = os.path.join(topic_dir, f'{id}.json')
    with open(json_file, 'r') as f:
        topic = json.load(f)[0]

    return render_template('files.html', files=files, topic=topic, folder=folder)

# Load a topic's metadata and markdown content
def load_topic(topic_id):
    topic_dir = os.path.join(DATA_DIR, topic_id)
    json_file = os.path.join(topic_dir, f"{topic_id}.json")
    md_file = os.path.join(topic_dir, f"{topic_id}.md")

    # Load JSON metadata
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            topic_data = json.load(f)

    # Load markdown content from the .md file
    if os.path.exists(md_file):
        with open(md_file, 'r') as f:
            topic_content = f.read()  # Read the markdown content

    return topic_data, topic_content

    topic_dir = os.path.join(DATA_DIR, topic_id)
    json_file = os.path.join(topic_dir, f"{topic_id}.json")
    md_file = os.path.join(topic_dir, f"{topic_id}.md")

    topic_data, topic_content = None, None
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            topic_data = json.load(f)

    if os.path.exists(md_file):
        with open(md_file, 'r') as f:
            topic_content = f.read()

    return topic_data, topic_content

# Save a topic's metadata and markdown content
def save_topic(topic_id, topic_data, topic_content):
    topic_dir = os.path.join(DATA_DIR, topic_id)
    os.makedirs(topic_dir, exist_ok=True)

    json_file = os.path.join(topic_dir, f"{topic_id}.json")
    md_file = os.path.join(topic_dir, f"{topic_id}.md")

    with open(json_file, 'w') as f:
        json.dump(topic_data, f, indent=4)

    with open(md_file, 'w') as f:
        f.write(topic_content)

# Helper function to generate the next topic ID
def generate_topic_id():
    existing_ids = sorted([int(d) for d in os.listdir(DATA_DIR) if d.isdigit()])

    next_topic_id = 1  # Start checking from ID 1

    for topic_id in existing_ids:
        if topic_id == next_topic_id:
            next_topic_id += 1  # Move to the next ID if current one exists
        else:
            break  # We found a gap, so break the loop and return this ID

    return str(next_topic_id)

# Route for home page
@app.route('/')
def home():
    return render_template('index.html', version = version, host = host)

# Route to list all topics
@app.route('/list')
def list_topics():
    all_topics = []
    for folder in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder)
        if os.path.isdir(folder_path):
            json_file = os.path.join(folder_path, f"{folder}.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    topic = data[0]  # Assuming the first topic is the main one
                    files_dir = os.path.join(folder_path, "files")
                    file_count = len(os.listdir(files_dir)) if os.path.exists(files_dir) else 0
                    topic['file_count'] = file_count  # Add file count to the topic
                    topic['folder'] = folder  # Make sure this is added when building the topic dictionary
                    all_topics.append(topic)

    return render_template('list.html', topics=all_topics)

# Route to display a topic
@app.route('/topic/<folder>/<id>')
def show_topic(folder, id):
    topic_dir = os.path.join(DATA_DIR, folder)
    json_file = os.path.join(topic_dir, f"{id}.json")
    md_file = os.path.join(topic_dir, f"{id}.md")
    files_dir = os.path.join(topic_dir, "files")

    topic = None  # Initialize topic variable
    topic_content = "No content available"  # Default content if markdown file is missing

    # Load topic metadata from the .json file
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
                topic = data[0]  # Assuming the topic is the first entry in the JSON file
            except json.JSONDecodeError:
                flash("Error decoding JSON data for this topic.", "danger")
                return redirect(url_for('list_topics'))
    else:
        flash("Topic metadata not found.", "danger")
        return redirect(url_for('list_topics'))

    # Load markdown content from the .md file if it exists
    if os.path.exists(md_file):
        with open(md_file, 'r') as f:
            topic_content = f.read()

    # Check if the "files" directory exists
    if os.path.exists(files_dir):
        files = os.listdir(files_dir)
    else:
        files = []

    # Pass the topic data and markdown content to the template
    return render_template('topic.html', topic=topic, files=files, topic_content=topic_content, folder=folder)

# Route to edit a topic
@app.route('/topic/<folder>/<id>/edit', methods=['GET', 'POST'])
def edit_topic(folder, id):
    topic_dir = os.path.join(DATA_DIR, folder)
    json_file = os.path.join(topic_dir, f"{id}.json")
    md_file = os.path.join(topic_dir, f"{id}.md")

    # Load the topic metadata
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            topic = json.load(f)[0]
    else:
        flash("Topic not found.", "danger")
        return redirect(url_for('list_topics'))

    # Load markdown content
    if os.path.exists(md_file):
        with open(md_file, 'r') as f:
            topic_content = f.read()
    else:
        topic_content = ""

    if request.method == 'POST':
        # Get the updated topic name and author from the form
        updated_topic_name = request.form['topic']
        updated_author = request.form['author']
        
        # Update the topic name and author in the JSON metadata
        topic['topic'] = updated_topic_name
        topic['editor'] = updated_author

        # Get the updated content from the form
        updated_content = request.form['data']

        # Save the updated content to the markdown file
        with open(md_file, 'w') as f:
            f.write(updated_content)

        # Update the JSON metadata
        topic['edition_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save the updated JSON metadata
        with open(json_file, 'w') as f:
            json.dump([topic], f, indent=4)

        # git_push(id, f"Edited topic {id}")
        flash("Topic updated successfully.", "success")

        return redirect(url_for('show_topic', folder=folder, id=id))
    
    return render_template('edit.html', topic=topic, topic_content=topic_content, folder=folder)


# Route to create a new topic
@app.route('/create', methods=['GET', 'POST'])
def create_topic():
    if request.method == 'POST':
        new_topic = request.form.get('new_topic')
        new_author = request.form.get('new_author')
        new_content = request.form.get('new_data')

        topic_id = generate_topic_id()
        topic_dir = os.path.join(DATA_DIR, topic_id)
        os.makedirs(topic_dir, exist_ok=True)

        creation_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        new_entry = [{
            "topic_id": topic_id,
            "topic": new_topic,
            "creation_date": creation_date,
            "edition_date": creation_date,
            "editor": new_author,  # Save the new author here
            "data_file": os.path.join(topic_dir, f"{topic_id}.md"),
            "files": os.path.join(topic_dir, "files")
        }]

        save_topic(topic_id, new_entry, new_content)
        flash(f"New topic '{new_topic}' added successfully!", "success")
        return redirect(url_for('list_topics'))

    return render_template('create.html')


# Route to delete a topic
@app.route('/delete/<folder>/<id>', methods=['POST'])
def delete_topic(folder, id):
    topic_dir = os.path.join(DATA_DIR, folder)
    if os.path.exists(topic_dir):
        os.system(f'rm -r {topic_dir}')
        flash(f"Topic with ID {id} has been deleted.", "success")
    else:
        flash(f"Topic with ID {id} not found.", "danger")
    return redirect(url_for('list_topics'))

# Route to delete a file
@app.route('/delete_file/<folder>/<filename>', methods=['POST'])
def delete_file(folder, filename):
    file_path = os.path.join(DATA_DIR, folder, "files", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' has been deleted.", "success")
    else:
        flash(f"File '{filename}' not found.", "danger")
    return redirect(url_for('edit_topic', folder=folder, id=folder))

if __name__ == '__main__':
    app.run(debug=True)
