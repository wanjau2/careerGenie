# CareerGenie App Issues - Complete Analysis

## 🐛 **Critical Issues Reported**

1. ❌ Resume upload returns 404
2. ❌ No jobs returned for user
3. ❌ App crashes when updating filters in history page
4. ❌ Filters don't apply on home page
5. ❌ App crashes when updating profile
6. ❌ Logout doesn't work
7. ❌ Delete account doesn't work

---

## 🔍 **Backend Investigation Results**

### **Status: All Endpoints Exist and Are Functional**

✅ Backend running on http://localhost:8000
✅ Database connected with 1,778 active jobs
✅ User exists: wanjaueugene@gmail.com
✅ All endpoints properly defined

---

## 📋 **Endpoint Verification**

### 1. **Resume Upload** ✅ EXISTS
- **Endpoint**: `POST /api/onboarding/parse-resume`
- **File**: `routes/onboarding.py:159`
- **Requires**: JWT token + multipart form with field name "resume"
- **Supports**: PDF, DOCX, DOC

**Likely Flutter Issue**:
- App might be calling wrong URL (e.g., `/api/profile/parse-resume`)
- Check Flutter code for actual endpoint being called

---

### 2. **Get Jobs** ✅ EXISTS
- **Endpoint**: `GET /api/jobs?page=1&pageSize=10`
- **File**: `routes/jobs.py:23`
- **Requires**: JWT token
- **Features**: Filters, pagination, user preferences

**Possible Issues**:
- Token expired or invalid
- User has no saved preferences
- Filters too restrictive

---

### 3. **History Filters** ✅ EXISTS
- **Endpoint**: `GET /api/jobs/applications?status=applied&keywords=...`
- **File**: `routes/jobs.py:533`
- **Supports**: status, keywords, city, state, jobTypes, industries, dateFrom, dateTo, sortBy

**Crash Cause**: Likely one of these:
- Date parsing error (lines 598, 607)
- Missing job data (line 613-615)
- ObjectId conversion issue (line 613)

**Fix Needed**: Add better error handling

---

### 4. **Home Page Filters** ✅ EXISTS
- **Endpoint**: `GET /api/jobs` with query params
- **File**: `routes/jobs.py:23`
- **Filters**: keywords, city, remote, salary, jobTypes, industries, experienceLevels

**Issue**: Filters defined but might not be applied correctly
- Check Flutter: filters being sent as query params?
- Check backend logs: what filters are received?

---

### 5. **Update Profile** ✅ EXISTS
- **Endpoint**: `PUT /api/user/profile`
- **File**: `routes/users.py:39`
- **Fields**: firstName, lastName, phone, location, skills, experience, expectedSalary

**Crash Cause**: Likely validation error
- Invalid data format
- Missing required fields
- Unexpected data structure

---

### 6. **Logout** ✅ EXISTS
- **Endpoint**: `POST /api/auth/logout`
- **File**: `routes/auth.py:100`
- **Returns**: Success message

**Issue**: Endpoint works, but client-side token not being cleared
- Flutter needs to clear local storage
- Remove tokens from secure storage
- Navigate to login screen

---

### 7. **Delete Account** ✅ EXISTS
- **Endpoint**: `DELETE /api/user/account`
- **File**: `routes/users.py` (deactivate_account function)
- **Action**: Sets `isActive: false`

**Note**: Account is deactivated, not deleted (soft delete)

---

## 🔧 **Required Fixes**

### **Backend Fixes** (High Priority)

#### 1. Add Error Logging to History Endpoint

**File**: `routes/jobs.py:533` (get_applications function)

**Problem**: Errors being swallowed in try-except blocks

**Fix**: Add detailed logging

```python
except Exception as e:
    logger.error(f"Error in get_applications: {str(e)}", exc_info=True)
    return jsonify(format_error_response(f"Server error: {str(e)}", 500))
```

#### 2. Add Safety Checks for Date Parsing

**File**: `routes/jobs.py:594-610`

**Fix**:
```python
if date_from:
    try:
        from datetime import datetime
        app_date = app.get('appliedAt')
        if not app_date:
            continue  # Skip if no date
        if isinstance(app_date, str):
            app_date = datetime.fromisoformat(app_date.replace('Z', '+00:00'))
        if app_date < datetime.fromisoformat(date_from.replace('Z', '+00:00')):
            continue
    except Exception as e:
        logger.warning(f"Date parsing error: {e}")
        pass  # Skip this filter if parsing fails
```

#### 3. Add Job Existence Check

**File**: `routes/jobs.py:613`

**Current**:
```python
job = jobs_collection.find_one({'_id': app['jobId']})
if not job:
    continue
```

**Better**:
```python
try:
    job_id = app['jobId'] if isinstance(app['jobId'], ObjectId) else ObjectId(app['jobId'])
    job = jobs_collection.find_one({'_id': job_id})
    if not job:
        logger.warning(f"Job {job_id} not found for application")
        continue
except Exception as e:
    logger.error(f"Error fetching job: {e}")
    continue
```

---

### **Flutter Fixes** (Critical)

#### 1. Resume Upload URL

**Check**:
```dart
// Make sure you're using:
final url = '$baseUrl/api/onboarding/parse-resume';

// NOT:
// /api/profile/parse-resume
// /api/resume/parse
// /api/resume/upload
```

#### 2. Logout Implementation

**Fix**:
```dart
Future<void> logout() async {
  try {
    // Call backend
    await http.post(
      Uri.parse('$baseUrl/api/auth/logout'),
      headers: {'Authorization': 'Bearer $token'}
    );
  } catch (e) {
    // Continue even if backend call fails
  } finally {
    // CRITICAL: Clear local tokens
    await _storage.delete(key: 'accessToken');
    await _storage.delete(key: 'refreshToken');
    await _storage.deleteAll();

    // Navigate to login
    Navigator.of(context).pushReplacementNamed('/login');
  }
}
```

#### 3. Filter Application (Home & History)

**Check**:
```dart
// Ensure filters are sent as query parameters
final queryParams = {
  'page': page.toString(),
  'pageSize': pageSize.toString(),
  if (keywords != null) 'keywords': keywords,
  if (city != null) 'city': city,
  if (remote != null) 'remote': remote.toString(),
  // ... other filters
};

final uri = Uri.parse('$baseUrl/api/jobs').replace(
  queryParameters: queryParams
);
```

#### 4. Error Handling

**Add** to all API calls:
```dart
try {
  final response = await http.get(url, headers: headers);

  if (response.statusCode == 401) {
    // Token expired - logout
    await logout();
    return;
  }

  if (response.statusCode != 200) {
    final error = json.decode(response.body);
    throw Exception(error['error'] ?? 'Unknown error');
  }

  // Process response
} catch (e) {
  print('API Error: $e');
  // Show error to user
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text('Error: $e'))
  );
}
```

---

## 🧪 **Testing Checklist**

### Backend Tests:

```bash
# Test resume endpoint
curl -X OPTIONS http://localhost:8000/api/onboarding/parse-resume

# Test jobs endpoint (requires token)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/jobs?page=1&pageSize=10

# Test logout
curl -X POST -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/auth/logout

# Test delete account
curl -X DELETE -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/user/account

# Test applications with filters
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/jobs/applications?status=applied&page=1"
```

### Flutter Tests:

1. **Resume Upload**: Upload a PDF and check network logs for actual URL
2. **Get Jobs**: Check if token is being sent in headers
3. **Filters**: Check network tab - are query params correct?
4. **Logout**: Verify local storage is cleared
5. **Delete Account**: Check if API call succeeds

---

## 📊 **Debug Mode**

### Enable Backend Logging:

Add to `app.py`:
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitor Requests:

```bash
tail -f /tmp/backend_fresh.log | grep -E "POST|GET|PUT|DELETE|ERROR"
```

---

## 🎯 **Priority Fixes**

### **Immediate** (Do First):
1. ✅ Check Flutter resume upload URL
2. ✅ Add error logging to history endpoint
3. ✅ Fix logout to clear local storage

### **High** (Do Soon):
4. ✅ Add date parsing safety checks
5. ✅ Improve error messages in all endpoints
6. ✅ Test filter application with actual data

### **Medium**:
7. ✅ Add request/response logging
8. ✅ Validate all data formats
9. ✅ Add unit tests for critical endpoints

---

## 💡 **Root Cause Analysis**

### Why Everything Seems Broken:

1. **Silent Failures**: Errors caught but not logged
2. **Poor Error Messages**: Generic "Server error" messages
3. **No Client-Side Validation**: Invalid data sent to backend
4. **Token Issues**: Expired tokens not handled properly
5. **Data Type Mismatches**: ObjectId vs string, datetime vs string

### The Fix Strategy:

1. **Add Comprehensive Logging** everywhere
2. **Better Error Messages** with specific details
3. **Input Validation** on both client and server
4. **Proper Error Handling** in Flutter (401, 404, 500)
5. **Data Type Consistency** across the stack

---

## 🆘 **Quick Debug Commands**

```bash
# Watch backend logs in real-time
tail -f /tmp/backend_fresh.log

# Check if endpoints exist
curl http://localhost:8000/api/jobs
# Should return 401 (needs auth) - means endpoint exists!

# Test with Flutter: Add to every API call
print('REQUEST: $method $url');
print('HEADERS: $headers');
print('RESPONSE: ${response.statusCode} - ${response.body}');
```

---

**All endpoints exist. The issues are in error handling, data validation, and Flutter-backend communication.**
