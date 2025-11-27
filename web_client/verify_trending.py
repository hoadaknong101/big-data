import unittest
from app import create_app
from models import db, User, Movie
from werkzeug.security import generate_password_hash

class TrendingApiTestCase(unittest.TestCase):
    def setUp(self):
        # Use in-memory SQLite for testing
        test_config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'TESTING': True,
            'WTF_CSRF_ENABLED': False
        }
        self.app = create_app(test_config)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create 50 test movies
        for i in range(50):
            movie = Movie(
                id=i+1,
                title=f'Movie {i+1}',
                genres='Action',
                poster_url='http://example.com/poster.jpg',
                overview='Test Overview',
                release_date='2023',
                rating_avg=4.5
            )
            db.session.add(movie)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_trending_api(self):
        # Access trending API
        response = self.client.get('/api/trending')
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        # Verify we get 30 results
        self.assertEqual(len(data['results']), 30)
        
        # Verify structure
        first_movie = data['results'][0]
        self.assertIn('id', first_movie)
        self.assertIn('title', first_movie)
        self.assertIn('poster_url', first_movie)

if __name__ == '__main__':
    unittest.main()
