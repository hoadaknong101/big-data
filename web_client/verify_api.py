import unittest
from app import create_app, db
from models import User, Movie
from werkzeug.security import generate_password_hash

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(test_config={
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            user = User(username='testuser', email='test@example.com', password=generate_password_hash('password'), gender='M', age='25', occupation='1', zip='12345')
            db.session.add(user)
            
            # Create test movies
            movie1 = Movie(title='Test Movie 1', genres='Action', poster_url='http://example.com/1.jpg')
            db.session.add(movie1)
            db.session.commit()
            
            movie2 = Movie(title='Test Movie 2', genres='Comedy', poster_url='http://example.com/2.jpg')
            db.session.add(movie2)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_api_movies(self):
        response = self.client.get('/api/movies')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['movies']), 2)

    def test_api_movie_detail(self):
        response = self.client.get('/api/movie/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['title'], 'Test Movie 1')

    def test_api_search(self):
        response = self.client.get('/api/search?q=Movie 1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Test Movie 1')

    def test_api_recommendations(self):
        self.login('testuser', 'password')
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Should return random movies from our list of 2
        self.assertTrue(len(data['results']) > 0)

if __name__ == '__main__':
    unittest.main()
