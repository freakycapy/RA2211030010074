from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

USERS_API = "http://20.244.56.144/test/users"
USER_POSTS_API = "http://20.244.56.144/test/users/{userid}/posts"
POST_COMMENTS_API = "http://20.244.56.144/test/posts/{postid}/comments"

API_TIMEOUT = 0.5

def get_users():
    """Fetches the list of users from the test server."""
    try:
        response = requests.get(USERS_API, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json().get("users", {})
    except (requests.RequestException, ValueError):
        return {}

def get_posts_for_user(userid):
    """Fetches posts for a given user."""
    try:
        url = USER_POSTS_API.format(userid=userid)
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json().get("posts", [])
    except (requests.RequestException, ValueError):
        return []

def get_comments_count_for_post(postid):
    """Fetches the comments for a given post and returns the count."""
    try:
        url = POST_COMMENTS_API.format(postid=postid)
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        comments = response.json().get("comments", [])
        return len(comments)
    except (requests.RequestException, ValueError):
        return 0

@app.route('/users', methods=['GET'])
def top_users():
    """
    Returns the top five users with the highest number of posts.
    Aggregates posts for every user then sorts by count descending.
    """
    users = get_users() 
    user_post_counts = []

    for userid, username in users.items():
        posts = get_posts_for_user(userid)
        count = len(posts)
        user_post_counts.append({
            "userid": userid,
            "username": username,
            "post_count": count
        })

    top_five = sorted(user_post_counts, key=lambda u: u["post_count"], reverse=True)[:5]

    return jsonify(top_five)

@app.route('/posts', methods=['GET'])
def posts_insights():
    """
    Returns posts based on the query parameter 'type':
    - type=latest: Returns the five latest posts from all users.
    - type=popular: Returns the post(s) with the maximum number of comments.
    """
    post_type = request.args.get("type")
    if post_type not in ["latest", "popular"]:
        return jsonify({"error": "Invalid query parameter. Accepted values: latest, popular"}), 400

    users = get_users()
    all_posts = []

    for userid in users.keys():
        posts = get_posts_for_user(userid)
        all_posts.extend(posts)

    if not all_posts:
        return jsonify({"message": "No posts available"}), 200

    if post_type == "latest":
        sorted_posts = sorted(all_posts, key=lambda post: post.get("id", 0), reverse=True)
        latest_posts = sorted_posts[:5]
        return jsonify({"latest_posts": latest_posts})

    elif post_type == "popular":
        posts_with_comment_count = []
        for post in all_posts:
            postid = post.get("id")
            if postid is None:
                continue
            count = get_comments_count_for_post(postid)
            post_copy = post.copy()
            post_copy["comment_count"] = count
            posts_with_comment_count.append(post_copy)

        if not posts_with_comment_count:
            return jsonify({"message": "No posts available"}), 200

        max_count = max(p["comment_count"] for p in posts_with_comment_count)
        popular_posts = [p for p in posts_with_comment_count if p["comment_count"] == max_count]

        return jsonify({"popular_posts": popular_posts})

if __name__ == '__main__':
    app.run(port=9876)
