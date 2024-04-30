
## API Endpoints

### Tweets

- **GET `/api/tweets/`**: Retrieve all tweets with associated user details, likes, and comments.
- **POST `/api/tweets/`**: Create a new tweet.
- **PUT `/api/tweets/<int:tweet_id>/`**: Update an existing tweet.

### Comments

- **GET `/api/comments/`**: Retrieve all comments.
- **POST `/api/comments/`**: Add a new comment.
- **PUT `/api/comments/<int:comment_id>/`**: Update an existing comment.

### Users

- **GET `/api/users/`**: Retrieve all users.
- **POST `/api/users/`**: Create a new user.
- **PUT `/api/users/<int:user_id>/`**: Update an existing user.

### Followers

- **GET `/api/followers/`**: Retrieve all follower relationships.
- **POST `/api/followers/`**: Add a new follower relationship.
- **PUT `/api/followers/<int:follower_id>/<int:following_id>/`**: Update an existing follower relationship.

### Likes

- **GET `/api/likes/`**: Retrieve all likes.
- **POST `/api/likes/`**: Add a new like.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
