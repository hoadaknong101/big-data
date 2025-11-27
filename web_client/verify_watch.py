import unittest
from app import create_app
from models import db, User, Movie
from werkzeug.security import generate_password_hash

class WatchPageTestCase(unittest.TestCase):
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

        # Create a test user
        self.user = User(
            email='test@example.com',
            username='testuser',
            password=generate_password_hash('password', method='pbkdf2:sha256'),
            gender='M', age=25, occupation=1, zip='12345', dataset_user_id=1
        )
        db.session.add(self.user)
        
        # Create a test movie
        self.movie = Movie(
            id=1,
            title='Test Movie',
            genres='Action',
            poster_url='http://example.com/poster.jpg',
            overview='Test Overview',
            release_date='2023',
            rating_avg=4.5
        )
        db.session.add(self.movie)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        return self.client.post('/login', data=dict(
            email='test@example.com',
            password='password'
        ), follow_redirects=True)

    def test_watch_page_access(self):
        # Login first
        self.login()
        
        # Access watch page
        response = self.client.get('/watch/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Movie', response.data)
        self.assertIn(b'Test Overview', response.data)
        self.assertIn(b'Back to Browse', response.data)
        self.assertIn(b'<video', response.data)

if __name__ == '__main__':
    unittest.main()
