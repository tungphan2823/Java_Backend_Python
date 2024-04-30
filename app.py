from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime

app = Flask(__name__)

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="admin123",
            database="updated_twitter"
        )
        return conn
    except (Exception, psycopg2.OperationalError) as error:
        print(error)
        return None

# @app.route('/api/postgres/', methods=['GET'])
# def get_data():
#     try:
#         conn = connect_to_db()
#         if conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM tweets;")
#             results = cursor.fetchall()
#             cursor.close()
#             conn.close()
#             return jsonify(results)
#         else:
#             return f"Error connecting to the PostgreSQL database"
#     except (Exception, psycopg2.OperationalError) as error:
#         print(error)
#         return str(error)

#TWEETS
@app.route('/api/tweets/', methods=['GET'])
def get_tweets():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.tweet_id, t.content, t.timestamp, t.user_id,
                       u.username, u.email, u.password_hash, u.day_joined,
                       u.first_name, u.last_name, u.profile_picture_url
                FROM tweets t
                JOIN users u ON t.user_id = u.user_id;
            """)
            
            tweets = []
            for row in cursor.fetchall():
                (
                    tweet_id, content, timestamp, user_id,
                    username, email, password_hash, day_joined,
                    first_name, last_name, profile_picture_url
                ) = row
                
                user = {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'password': password_hash,  # Include password hash (for demonstration)
                    'dayJoined': day_joined.isoformat(),
                    'firstName': first_name,
                    'lastName': last_name,
                    'profilePicture': profile_picture_url
                }

                likes = fetch_likes(cursor, tweet_id)
                comments = fetch_comments(cursor, tweet_id)

                tweet = {
                    'tweetId': tweet_id,
                    'content': content,
                    'timestamp': timestamp.isoformat(),
                    'userId': user_id,
                    'user': user,
                    'likes': likes,
                    'comments': comments
                }

                tweets.append(tweet)

            cursor.close()
            conn.close()
            
            # Organize tweets, comments, and likes in the desired order
            organized_response = []
            for tweet in tweets:
                organized_tweet = {
                    'tweetId': tweet['tweetId'],
                    'content': tweet['content'],
                    'timestamp': tweet['timestamp'],
                    'userId': tweet['userId'],
                    'user': tweet['user']
                }
                if tweet['comments']:
                    organized_tweet['comments'] = tweet['comments']
                if tweet['likes']:
                    organized_tweet['likes'] = tweet['likes']
                organized_response.append(organized_tweet)

            return jsonify(organized_response)
        else:
            return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500
    except (Exception, psycopg2.Error) as error:
        print(error)
        return jsonify({'error': f'Failed to retrieve tweets: {str(error)}'}), 500

def fetch_likes(cursor, tweet_id):
    cursor.execute("""
        SELECT like_id, user_id, timestamp
        FROM likes
        WHERE tweet_id = %s;
    """, (tweet_id,))
    likes = [{'like_id': like[0], 'user_id': like[1], 'timestamp': like[2].isoformat()}
             for like in cursor.fetchall()]
    return likes

def fetch_comments(cursor, tweet_id):
    cursor.execute("""
        SELECT comment_id, user_id, comment, timestamp
        FROM comments
        WHERE tweet_id = %s;
    """, (tweet_id,))
    comments = [{'comment_id': comment[0], 'user_id': comment[1], 'comment': comment[2], 'timestamp': comment[3].isoformat()}
                for comment in cursor.fetchall()]
    return comments

@app.route('/api/tweets/', methods=['POST'])
def create_tweet():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract tweet data from the JSON object
        content = data.get('content')
        timestamp = datetime.utcnow()  # Use current timestamp
        user_id = data.get('userId')  # Assuming userId is provided in the request

        # Validate that all required fields are present
        if None in (content, user_id):
            return jsonify({'error': 'Incomplete tweet data provided'}), 400

        # Insert the new tweet into the database
        query = """
            INSERT INTO tweets (content, timestamp, user_id)
            VALUES (%s, %s, %s)
            RETURNING tweet_id;
        """
        cursor.execute(query, (content, timestamp, user_id))

        # Get the newly inserted tweet_id
        new_tweet_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'tweet_id': new_tweet_id, 'result': 'Tweet created successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to create tweet in the database: {str(error)}'}), 500


@app.route('/api/tweets/<int:tweet_id>/', methods=['PUT'])
def update_tweet(tweet_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract updated tweet content from the JSON object
        content = data.get('content')

        # Validate that content is provided
        if content is None:
            return jsonify({'error': 'No content provided for update'}), 400

        # Update the tweet in the database
        query = "UPDATE tweets SET content = %s WHERE tweet_id = %s;"
        cursor.execute(query, (content, tweet_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'tweet_id': tweet_id, 'result': 'Tweet updated successfully'}), 200

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to update tweet in the database: {str(error)}'}), 500

#POSTGRES
@app.route('/api/postgres/', methods=['GET'])
def get_data():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tweet_id, content, timestamp, user_id FROM tweets;")
            
            # Fetch all rows as a list of dictionaries (with column names)
            results = []
            for row in cursor.fetchall():
                result_dict = {
                    'tweet_id': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'user_id': row[3]
                }
                results.append(result_dict)

            cursor.close()
            conn.close()
            return jsonify(results)
        else:
            return f"Error connecting to the PostgreSQL database"
    except (Exception, psycopg2.OperationalError) as error:
        print(error)
        return str(error)

@app.route('/api/postgres/', methods=['POST'])
def insert_data():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract tweet data from the JSON object
        tweet_id = data.get('tweet_id')
        content = data.get('content')
        timestamp = data.get('timestamp')
        user_id = data.get('user_id')

        # Validate that all required fields are present
        if None in (tweet_id, content, timestamp, user_id):
            return jsonify({'error': 'Incomplete tweet data provided'}), 400

        # Insert the tweet data into the database
        query = "INSERT INTO tweets (tweet_id, content, timestamp, user_id) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (tweet_id, content, timestamp, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'result': 'Data inserted successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to insert data into the database: {str(error)}'}), 500


@app.route('/api/postgres/', methods=['DELETE'])
def delete_data():
    id = request.args.get('id')
    if not id:
        return 'Missing required argument: id'

    conn = connect_to_db()
    if not conn:
        return f"Error connecting to the PostgreSQL database"

    cursor = conn.cursor()
    query = "DELETE FROM your_table WHERE id = %s;"
    cursor.execute(query, (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'result': f'Data with id {id} deleted successfully'})

#COMMENTS
@app.route('/api/comments/', methods=['GET'])
def get_comments():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT comment_id, tweet_id, user_id, comment, timestamp FROM comments;")
            
            # Fetch all rows as a list of dictionaries (with column names)
            results = []
            for row in cursor.fetchall():
                result_dict = {
                    'comment_id': row[0],
                    'tweet_id': row[1],
                    'user_id': row[2],
                    'comment': row[3],
                    'timestamp': row[4]
                }
                results.append(result_dict)

            cursor.close()
            conn.close()
            return jsonify(results)
        else:
            return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500
    except (Exception, psycopg2.Error) as error:
        print(error)
        return jsonify({'error': f'Failed to retrieve comments: {str(error)}'}), 500

@app.route('/api/comments/', methods=['POST'])
def add_comment():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract comment data from the JSON object
        tweet_id = data.get('tweet_id')
        user_id = data.get('user_id')
        comment_text = data.get('comment')
        timestamp = data.get('timestamp')

        # Validate that all required fields are present
        if None in (tweet_id, user_id, comment_text, timestamp):
            return jsonify({'error': 'Incomplete comment data provided'}), 400

        # Insert the comment into the database
        query = "INSERT INTO comments (tweet_id, user_id, comment, timestamp) VALUES (%s, %s, %s, %s) RETURNING comment_id;"
        cursor.execute(query, (tweet_id, user_id, comment_text, timestamp))

        # Get the newly inserted comment_id
        new_comment_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'comment_id': new_comment_id, 'result': 'Comment added successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to add comment to the database: {str(error)}'}), 500

@app.route('/api/comments/<int:comment_id>/', methods=['PUT'])
def update_comment(comment_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract updated comment data from the JSON object
        comment_text = data.get('comment')
        timestamp = data.get('timestamp')

        # Validate that comment data is provided
        if comment_text is None:
            return jsonify({'error': 'No comment text provided for update'}), 400

        # Update the comment in the database
        query = "UPDATE comments SET comment = %s, timestamp = %s WHERE comment_id = %s;"
        cursor.execute(query, (comment_text, timestamp, comment_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'comment_id': comment_id, 'result': 'Comment updated successfully'}), 200

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to update comment in the database: {str(error)}'}), 500


#USERS
@app.route('/api/users/', methods=['GET'])
def get_users():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, email, password_hash, profile_picture_url, day_joined, first_name, last_name FROM users;")
            
            # Fetch all rows as a list of dictionaries (with column names)
            results = []
            for row in cursor.fetchall():
                result_dict = {
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'password_hash': row[3],
                    'profile_picture_url': row[4],
                    'day_joined': row[5].strftime('%Y-%m-%d'),  # Format date to string
                    'first_name': row[6],
                    'last_name': row[7]
                }
                results.append(result_dict)

            cursor.close()
            conn.close()
            return jsonify(results)
        else:
            return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500
    except (Exception, psycopg2.Error) as error:
        print(error)
        return jsonify({'error': f'Failed to retrieve users: {str(error)}'}), 500

@app.route('/api/users/', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract user data from the JSON object
        username = data.get('username')
        email = data.get('email')
        password_hash = data.get('password_hash')
        profile_picture_url = data.get('profile_picture_url')
        day_joined = datetime.now().strftime('%Y-%m-%d')  # Current date formatted as string
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        # Validate that all required fields are present
        if None in (username, email, password_hash, first_name, last_name):
            return jsonify({'error': 'Incomplete user data provided'}), 400

        # Insert the user into the database
        query = "INSERT INTO users (username, email, password_hash, profile_picture_url, day_joined, first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id;"
        cursor.execute(query, (username, email, password_hash, profile_picture_url, day_joined, first_name, last_name))

        # Get the newly inserted user_id
        new_user_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'user_id': new_user_id, 'result': 'User created successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to create user in the database: {str(error)}'}), 500

@app.route('/api/users/<int:user_id>/', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract updated user data from the JSON object
        username = data.get('username')
        email = data.get('email')
        password_hash = data.get('password_hash')
        profile_picture_url = data.get('profile_picture_url')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        # Validate that at least one field is provided for update
        if not any([username, email, password_hash, profile_picture_url, first_name, last_name]):
            return jsonify({'error': 'No fields provided for update'}), 400

        # Construct the UPDATE query based on provided fields
        query = "UPDATE users SET "
        update_values = []

        if username:
            update_values.append(f"username = '{username}'")
        if email:
            update_values.append(f"email = '{email}'")
        if password_hash:
            update_values.append(f"password_hash = '{password_hash}'")
        if profile_picture_url:
            update_values.append(f"profile_picture_url = '{profile_picture_url}'")
        if first_name:
            update_values.append(f"first_name = '{first_name}'")
        if last_name:
            update_values.append(f"last_name = '{last_name}'")

        query += ", ".join(update_values) + f" WHERE user_id = {user_id};"

        # Execute the UPDATE query
        cursor.execute(query)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'user_id': user_id, 'result': 'User updated successfully'}), 200

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to update user in the database: {str(error)}'}), 500


#FOLLOWERS
@app.route('/api/followers/', methods=['GET'])
def get_followers():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT follower_id, following_id FROM followers;")
            
            # Fetch all rows as a list of dictionaries (with column names)
            results = []
            for row in cursor.fetchall():
                result_dict = {
                    'follower_id': row[0],
                    'following_id': row[1]
                }
                results.append(result_dict)

            cursor.close()
            conn.close()
            return jsonify(results)
        else:
            return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500
    except (Exception, psycopg2.Error) as error:
        print(error)
        return jsonify({'error': f'Failed to retrieve followers: {str(error)}'}), 500


@app.route('/api/followers/', methods=['POST'])
def add_follower():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract follower data from the JSON object
        follower_id = data.get('follower_id')
        following_id = data.get('following_id')

        # Validate that all required fields are present
        if None in (follower_id, following_id):
            return jsonify({'error': 'Incomplete follower data provided'}), 400

        # Insert the follower relationship into the database
        query = "INSERT INTO followers (follower_id, following_id) VALUES (%s, %s);"
        cursor.execute(query, (follower_id, following_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'result': 'Follower relationship added successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to add follower relationship to the database: {str(error)}'}), 500

@app.route('/api/followers/<int:follower_id>/<int:following_id>/', methods=['PUT'])
def update_follower(follower_id, following_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract updated follower data from the JSON object
        new_follower_id = data.get('new_follower_id')
        new_following_id = data.get('new_following_id')

        # Validate that the new follower_id and following_id are provided
        if None in (new_follower_id, new_following_id):
            return jsonify({'error': 'Incomplete follower data provided'}), 400

        # Update the follower relationship in the database
        query = "UPDATE followers SET follower_id = %s, following_id = %s WHERE follower_id = %s AND following_id = %s;"
        cursor.execute(query, (new_follower_id, new_following_id, follower_id, following_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'result': 'Follower relationship updated successfully'}), 200

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to update follower relationship in the database: {str(error)}'}), 500


#LIKES
@app.route('/api/likes/', methods=['GET'])
def get_likes():
    try:
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT like_id, tweet_id, user_id, timestamp FROM likes;")
            
            # Fetch all rows as a list of dictionaries (with column names)
            results = []
            for row in cursor.fetchall():
                result_dict = {
                    'like_id': row[0],
                    'tweet_id': row[1],
                    'user_id': row[2],
                    'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp
                }
                results.append(result_dict)

            cursor.close()
            conn.close()
            return jsonify(results)
        else:
            return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500
    except (Exception, psycopg2.Error) as error:
        print(error)
        return jsonify({'error': f'Failed to retrieve likes: {str(error)}'}), 500

@app.route('/api/likes/', methods=['POST'])
def add_like():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided in the request'}), 400

    conn = connect_to_db()

    if not conn:
        return jsonify({'error': 'Error connecting to the PostgreSQL database'}), 500

    cursor = conn.cursor()

    try:
        # Extract like data from the JSON object
        tweet_id = data.get('tweet_id')
        user_id = data.get('user_id')
        timestamp = datetime.now()  # Current timestamp

        # Validate that all required fields are present
        if None in (tweet_id, user_id):
            return jsonify({'error': 'Incomplete like data provided'}), 400

        # Insert the like into the database
        query = "INSERT INTO likes (tweet_id, user_id, timestamp) VALUES (%s, %s, %s) RETURNING like_id;"
        cursor.execute(query, (tweet_id, user_id, timestamp))

        # Get the newly inserted like_id
        new_like_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'like_id': new_like_id, 'result': 'Like added successfully'}), 201

    except (Exception, psycopg2.Error) as error:
        conn.rollback()
        return jsonify({'error': f'Failed to add like to the database: {str(error)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
