from flask import Flask, request, jsonify, render_template, after_this_request
from dotenv import load_dotenv
import os
import openai
import uuid
from datetime import datetime
from flask_cors import CORS
import traceback

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'***' + api_key[-4:] if api_key else 'None'}")
openai.api_key = api_key


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
    return str(uuid.uuid4())

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
    try:
        # Get anonymous user ID
        user_id = get_user_fingerprint()
        feature = 'document'
        
        print("Received document request")
        print("Content-Type:", request.headers.get('Content-Type'))
        
        # Check if user has remaining free requests
        if not track_usage(user_id, feature):
            return jsonify({
                "status": "error", 
                "message": "You've reached the daily limit for free documentation requests. Upgrade to premium for unlimited access.",
                "usage": get_usage_stats(user_id, feature)
            }), 429
        
        # Parse data based on content type
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        print("Parsed data:", data)
        
        code = data.get('code')
        language = data.get('language')

        if not code or not language:
            return jsonify({"status": "error", "message": "Missing 'code' or 'language'."}), 400

        # OpenAI integration for documentation
        prompt = f"Generate {language} documentation for the following code:\n\n{code}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates code documentation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        documentation = response.choices[0].message["content"]
        
        api_response = jsonify({
            "status": "success", 
            "documentation": documentation,
            "usage": get_usage_stats(user_id, feature)
        })
        
        # Set cookie if needed
        if 'user_id' not in request.cookies:
            api_response.set_cookie('user_id', user_id, max_age=60*60*24*30)
            
        return api_response
    except Exception as e:
        print("ERROR IN DOCUMENT ENDPOINT:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# ---------------------------
# 2. Explain Code
# ---------------------------
@app.route('/explain', methods=['POST'])
def explain_code():
    try:
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
        
        # Parse data based on content type
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        code = data.get('code')
        language = data.get('language')

        if not code or not language:
            return jsonify({"status": "error", "message": "Missing 'code' or 'language'."}), 400

        # OpenAI integration for explanation
        prompt = f"Explain what this {language} code does in simple, beginner-friendly terms:\n\n{code}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You explain code clearly and simply."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        explanation = response.choices[0].message["content"]
        
        api_response = jsonify({
            "status": "success", 
            "explanation": explanation,
            "usage": get_usage_stats(user_id, feature)
        })
        
        # Set cookie if needed
        if 'user_id' not in request.cookies:
            api_response.set_cookie('user_id', user_id, max_age=60*60*24*30)
            
        return api_response
    except Exception as e:
        print("ERROR IN EXPLAIN ENDPOINT:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# ---------------------------
# 3. Translate Code (Premium Feature)
# ---------------------------
@app.route('/translate', methods=['POST'])
def translate_code():
    try:
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
        
        # For now, return premium feature message
        return jsonify({
            "status": "error", 
            "message": "Code translation is a premium feature. Please upgrade to access this functionality.",
            "upgrade_url": "/pricing"
        }), 403
    except Exception as e:
        print("ERROR IN TRANSLATE ENDPOINT:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# ---------------------------
# 4. Generate README
# ---------------------------
@app.route('/readme', methods=['POST'])
def generate_readme():
    try:
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
        
        # Parse data based on content type
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        description = data.get('description')

        if not description:
            return jsonify({"status": "error", "message": "Missing 'description'."}), 400

        # OpenAI integration for README generation
        prompt = f"Generate a README.md file for a project described as:\n\n{description}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You write clear and professional README files."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        readme = response.choices[0].message["content"]
        
        api_response = jsonify({
            "status": "success", 
            "readme_content": readme,
            "usage": get_usage_stats(user_id, feature)
        })
        
        # Set cookie if needed
        if 'user_id' not in request.cookies:
            api_response.set_cookie('user_id', user_id, max_age=60*60*24*30)
            
        return api_response
    except Exception as e:
        print("ERROR IN README ENDPOINT:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# ---------------------------
# 5. Debug Code (Premium Feature)
# ---------------------------
@app.route('/debug', methods=['POST'])
def debug_code():
    try:
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
        
        # For now, return premium feature message
        return jsonify({
            "status": "error", 
            "message": "Code debugging is a premium feature. Please upgrade to access this functionality.",
            "upgrade_url": "/pricing"
        }), 403
    except Exception as e:
        print("ERROR IN DEBUG ENDPOINT:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# Add a usage reset endpoint for testing
@app.route('/reset_usage', methods=['GET'])
def reset_usage():
    global daily_usage
    daily_usage = {}
    return jsonify({"status": "success", "message": "Usage reset successful"})

# Simple test endpoint to verify the server is running
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "success", "message": "Server is running correctly"})

# ---------------------------
# Run the Flask App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
