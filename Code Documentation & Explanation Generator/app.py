from flask import Flask, request, jsonify, render_template, after_this_request
from dotenv import load_dotenv
import os
import openai
import uuid
from datetime import datetime
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Free tier usage limits
FREE_TIER_LIMITS = {
    'document': 10,
    'explain': 10,
    'readme': 5,
    'translate': 0,  # Premium only
    'debug': 0       # Premium only
}

# In-memory storage for usage tracking (replace with database in production)
daily_usage = {}

# Function to get a unique identifier for anonymous users
def get_user_fingerprint():
    # Check for existing cookie
    if 'user_id' in request.cookies:
        return request.cookies['user_id']
    
    # Create new anonymous ID
    anonymous_id = str(uuid.uuid4())
    
    # Set in response
    @after_this_request
    def set_cookie(response):
        response.set_cookie('user_id', anonymous_id, max_age=60*60*24*30)
        return response
        
    return anonymous_id

# Function to track and check usage
def track_usage(user_id, feature):
    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{user_id}:{today}:{feature}"
    
    if key not in daily_usage:
        daily_usage[key] = 0
    
    daily_usage[key] += 1
    
    # Check if exceeded limit
    return daily_usage[key] <= FREE_TIER_LIMITS.get(feature, 0)

# Utility function to get current usage stats
def get_usage_stats(user_id, feature):
    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{user_id}:{today}:{feature}"
    used = daily_usage.get(key, 0)
    limit = FREE_TIER_LIMITS[feature]
    
    return {
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used)
    }

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------
# 1. Document Code
# ---------------------------
@app.route('/document', methods=['POST'])
def document_code():
    # Get anonymous user ID
    user_id = get_user_fingerprint()
    feature = 'document'
    
    # Check if user has remaining free requests
    if not track_usage(user_id, feature):
        return jsonify({
            "status": "error", 
            "message": "You've reached the daily limit for free documentation requests. Upgrade to premium for unlimited access.",
            "usage": get_usage_stats(user_id, feature)
        }), 429
    
    # Continue with your existing code
    data = request.get_json() if request.is_json else request.form
    code = data.get('code')
    language = data.get('language')

    if not code or not language:
        return jsonify({"status": "error", "message": "Missing 'code' or 'language'."}), 400

    prompt = f"Generate {language} documentation for the following code:\n\n{code}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates code documentation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        documentation = response.choices[0].message["content"]
        return jsonify({
            "status": "success", 
            "documentation": documentation,
            "usage": get_usage_stats(user_id, feature)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# 2. Explain Code
# ---------------------------
@app.route('/explain', methods=['POST'])
def explain_code():
    # Get anonymous user ID
    user_id = get_user_fingerprint()
    feature = 'explain'
    
    # Check if user has remaining free requests
    if not track_usage(user_id, feature):
        return jsonify({
            "status": "error", 
            "message": "You've reached the daily limit for free explanation requests. Upgrade to premium for unlimited access.",
            "usage": get_usage_stats(user_id, feature)
        }), 429
    
    # Continue with your existing code
    data = request.get_json() if request.is_json else request.form
    code = data.get('code')
    language = data.get('language')

    if not code or not language:
        return jsonify({"status": "error", "message": "Missing 'code' or 'language'."}), 400

    prompt = f"Explain what this {language} code does in simple, beginner-friendly terms:\n\n{code}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You explain code clearly and simply."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        explanation = response.choices[0].message["content"]
        return jsonify({
            "status": "success", 
            "explanation": explanation,
            "usage": get_usage_stats(user_id, feature)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# 3. Translate Code (Premium Feature)
# ---------------------------
@app.route('/translate', methods=['POST'])
def translate_code():
    # Get anonymous user ID
    user_id = get_user_fingerprint()
    feature = 'translate'
    
    # Since this is premium, always return upgrade message for free users
    if FREE_TIER_LIMITS[feature] == 0:
        return jsonify({
            "status": "error", 
            "message": "Code translation is a premium feature. Please upgrade to access this functionality.",
            "upgrade_url": "/pricing"
        }), 403
    
    # If we reached here, it would be premium user logic
    # (not implemented yet, will add authentication check later)
    
    # For now, continue with existing code
    data = request.get_json() if request.is_json else request.form
    code = data.get('code')
    source_language = data.get('source_language')
    target_language = data.get('target_language')

    if not code or not source_language or not target_language:
        return jsonify({"status": "error", "message": "Missing 'code', 'source_language', or 'target_language'."}), 400

    prompt = f"Translate this code from {source_language} to {target_language}:\n\n{code}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code translation expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        translation = response.choices[0].message["content"]
        return jsonify({"status": "success", "translated_code": translation, "note": "Review translations for accuracy."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# 4. Generate README
# ---------------------------
@app.route('/readme', methods=['POST'])
def generate_readme():
    # Get anonymous user ID
    user_id = get_user_fingerprint()
    feature = 'readme'
    
    # Check if user has remaining free requests
    if not track_usage(user_id, feature):
        return jsonify({
            "status": "error", 
            "message": "You've reached the daily limit for free README generation requests. Upgrade to premium for unlimited access.",
            "usage": get_usage_stats(user_id, feature)
        }), 429
    
    # Continue with your existing code
    data = request.get_json() if request.is_json else request.form
    description = data.get('description')

    if not description:
        return jsonify({"status": "error", "message": "Missing 'description'."}), 400

    prompt = f"Generate a README.md file for a project described as:\n\n{description}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You write clear and professional README files."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        readme = response.choices[0].message["content"]
        return jsonify({
            "status": "success", 
            "readme_content": readme,
            "usage": get_usage_stats(user_id, feature)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# 5. Debug Code (Premium Feature)
# ---------------------------
@app.route('/debug', methods=['POST'])
def debug_code():
    # Get anonymous user ID
    user_id = get_user_fingerprint()
    feature = 'debug'
    
    # Since this is premium, always return upgrade message for free users
    if FREE_TIER_LIMITS[feature] == 0:
        return jsonify({
            "status": "error", 
            "message": "Code debugging is a premium feature. Please upgrade to access this functionality.",
            "upgrade_url": "/pricing"
        }), 403
    
    # If we reached here, it would be premium user logic
    # (not implemented yet, will add authentication check later)
    
    # For now, continue with existing code
    data = request.get_json() if request.is_json else request.form
    code = data.get('code')
    language = data.get('language')
    error_message = data.get('error_message')

    if not code or not language or not error_message:
        return jsonify({"status": "error", "message": "Missing 'code', 'language', or 'error_message'."}), 400

    prompt = f"""The following {language} code is producing an error: "{error_message}". 
Please help debug it and explain why this is happening:\n\n{code}"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior developer who helps debug code and explain errors."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        explanation = response.choices[0].message["content"]
        return jsonify({"status": "success", "explanation": explanation})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------
# Run the Flask App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
