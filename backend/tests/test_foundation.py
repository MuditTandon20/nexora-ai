from app.routes import today


def make_class(admin):
    result = admin.post('/api/classes', json={'name': 'Class 5 A', 'grade': 5, 'teacher_ids': [2], 'student_ids': [3, 4]})
    assert result.status_code == 201, result.text
    return result.json()['id']


def test_admin_teacher_student_vertical_slice(context):
    login, _ = context
    admin, teacher, student, peer = [login(n) for n in ['admin', 'teacher', 'student', 'peer']]
    cid = make_class(admin)
    payload = {'day': str(today()), 'absent_ids': [4], 'confirmed': True}
    saved = teacher.post(f'/api/classes/{cid}/attendance', json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()['present'] == 1
    assert student.get('/api/dashboard').json()['attendance_status'] == 'present'
    assert peer.get('/api/dashboard').json()['attendance_status'] == 'absent'
    own = student.get(f'/api/classes/{cid}/attendance', params={'day': str(today())}).json()
    assert own['records'] == [{'student_id': 3, 'status': 'present'}]
    assert student.get(f'/api/classes/{cid}/roster').status_code == 403
    assert teacher.post(f'/api/classes/{cid}/attendance', json=payload).status_code == 409
    current = teacher.get(f'/api/classes/{cid}/attendance', params={'day': str(today())}).json()
    payload.update(expected_version=current['version'], correction_reason='Student arrived late', absent_ids=[])
    assert teacher.post(f'/api/classes/{cid}/attendance', json=payload).status_code == 200
    assert peer.get('/api/dashboard').json()['attendance_status'] == 'present'
    assert admin.get('/api/audit').json()[0]['action'] == 'attendance_corrected'


def test_tenant_roles_csrf_logout(context):
    login, _ = context
    admin, teacher, student, outsider = [login(n) for n in ['admin', 'teacher', 'student', 'outsider']]
    cid = make_class(admin)
    assert outsider.get(f'/api/classes/{cid}/roster').status_code == 404
    assert student.get('/api/users').status_code == 403
    assert teacher.post('/api/classes', json={'name': 'Forbidden', 'grade': 2}).status_code == 403
    assert admin.post('/api/classes', json={'name': 'Wrong school', 'grade': 2, 'teacher_ids': [5]}).status_code == 404
    token = admin.headers.pop('x-csrf-token')
    assert admin.post('/api/auth/logout').status_code == 403
    admin.headers['x-csrf-token'] = token
    cookies = dict(admin.cookies)
    assert admin.post('/api/auth/logout').status_code == 200
    admin.cookies.update(cookies)
    assert admin.get('/api/auth/me').status_code == 401
