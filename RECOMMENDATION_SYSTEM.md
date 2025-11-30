# 🎯 Recommendation System Integration

## Tổng quan

Hệ thống recommendation đã được tích hợp hoàn chỉnh giữa **Web Client** và **API Gateway** sử dụng **Milvus vector search**.

## 🔄 Flow hoạt động

```
User Login → Web Client → API Gateway → Milvus → PostgreSQL → Response
```

### Chi tiết từng bước:

1. **User đăng nhập vào Web Client**
   - User có `dataset_user_id` (mapping với user trong dataset gốc)

2. **Frontend gọi `/api/recommendations`**
   ```javascript
   fetch('/api/recommendations')
   ```

3. **Web Client gọi API Gateway**
   ```python
   GET http://api-gateway:5000/recommendations/{dataset_user_id}
   ```

4. **API Gateway xử lý:**
   - Lấy user embedding từ Milvus collection `user_embeddings`
   - Search top 20 movies gần nhất trong `movie_embeddings` (L2 distance)
   - Lấy thông tin chi tiết từ PostgreSQL
   - Trả về danh sách movies

5. **Web Client hiển thị:**
   - Section "Top Picks for You" trên dashboard
   - Personalized recommendations dựa trên viewing history

## 📊 Data Flow

### API Gateway → Milvus

```python
# 1. Lấy user embedding
user_vector = user_collection.query(
    expr=f"user_id == {user_id}",
    output_fields=["embedding"]
)

# 2. Search similar movies
search_results = movie_collection.search(
    data=[user_vector],
    anns_field="embedding",
    limit=20,
    output_fields=["movie_id"]
)
```

### API Gateway → PostgreSQL

```sql
SELECT id, title, genres, poster_url 
FROM movies 
WHERE id IN (1, 2, 3, ...)
```

### Web Client Response Format

```json
{
  "results": [
    {
      "id": 1,
      "title": "Toy Story (1995)",
      "genres": "Animation|Children's|Comedy",
      "poster_url": "https://...",
      "overview": "...",
      "release_date": "1995-11-22",
      "rating_avg": 4.5
    }
  ]
}
```

## 🛡️ Fallback Strategy

Hệ thống có 3 levels fallback để đảm bảo luôn có kết quả:

### Level 1: User không có dataset_user_id
```python
if not current_user.dataset_user_id:
    # Trả về random movies
    movies = Movie.query.order_by(db.func.random()).limit(10).all()
```

### Level 2: API Gateway error
```python
if response.status_code != 200:
    # Fallback to random
    movies = Movie.query.order_by(db.func.random()).limit(10).all()
```

### Level 3: API Gateway unavailable
```python
except requests.exceptions.RequestException:
    # Fallback to random
    movies = Movie.query.order_by(db.func.random()).limit(10).all()
```

## 🔧 Configuration

### Environment Variables

**Web Client** (`web_client/.env`):
```env
API_GATEWAY_URL=http://localhost:5000
```

**API Gateway** (`api_gateway/.env`):
```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
POSTGRES_HOST=localhost
POSTGRES_DB=movielens
```

## 📈 Performance

- **Vector Search**: ~10-50ms (Milvus)
- **Database Query**: ~5-20ms (PostgreSQL)
- **Total Response Time**: ~50-100ms
- **Timeout**: 5 seconds (với fallback)

## 🧪 Testing

### 1. Test API Gateway trực tiếp:
```bash
curl http://localhost:5000/recommendations/1
```

### 2. Test từ Web Client:
```bash
# Login với user có dataset_user_id
# Mở dashboard → Check "Top Picks for You"
```

### 3. Check logs:
```bash
# Web Client logs
docker compose logs web-client | grep recommendations

# API Gateway logs
docker compose logs api-gateway | grep recommendations
```

## 🎯 Expected Output

### Console logs (Web Client):
```
✅ Lấy được 20 recommendations từ API Gateway
```

### Console logs (API Gateway):
```
✅ User 1 found in Milvus
✅ Found 20 similar movies
✅ Retrieved movie details from PostgreSQL
```

## 🐛 Troubleshooting

### Issue: "User không có dataset_user_id"
**Solution**: 
- User mới cần được assign `dataset_user_id`
- Hoặc sẽ nhận random recommendations

### Issue: "API Gateway unavailable"
**Solution**:
- Check API Gateway container: `docker compose ps api-gateway`
- Check logs: `docker compose logs api-gateway`
- Verify network: `docker network inspect app-network`

### Issue: "Milvus collection not initialized"
**Solution**:
- Chạy model training để tạo embeddings
- Check Milvus collections: `curl http://localhost:9091/api/v1/collections`

## 🚀 Next Steps

1. **Improve recommendations**:
   - Tăng số lượng embeddings
   - Fine-tune model parameters
   - Add collaborative filtering

2. **Add caching**:
   - Cache recommendations trong Redis
   - TTL: 1 hour

3. **A/B Testing**:
   - So sánh vector search vs collaborative filtering
   - Track click-through rate

---

**Status: ✅ Fully Integrated**
