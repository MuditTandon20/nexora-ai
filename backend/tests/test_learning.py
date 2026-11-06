from app.routes import today
from test_foundation import make_class

CONTENT = 'Plants make their own food through photosynthesis. Chlorophyll captures energy from sunlight. Oxygen is released during photosynthesis.'


def test_material_and_homework_lifecycle(context):
    login, _ = context
    admin, teacher, student, peer, outsider = [login(n) for n in ['admin','teacher','student','peer','outsider']]
    cid = make_class(admin)
    data = {'class_id': cid, 'subject_id': 1, 'title': 'Plants and light', 'content': CONTENT}
    created = teacher.post('/api/materials', json=data)
    assert created.status_code == 201, created.text
    mid = created.json()['id']
    assert student.get('/api/materials').json() == []
    assert student.get(f'/api/materials/{mid}/download').status_code == 404
    assert outsider.post(f'/api/materials/{mid}/approve').status_code == 404
    assert teacher.post(f'/api/materials/{mid}/approve').status_code == 200
    assert student.get('/api/materials').json()[0]['content'] == CONTENT
    bad = teacher.post('/api/materials/upload', data={'class_id':cid,'subject_id':1,'title':'Invalid file'},
                       files={'file': ('evil.pdf', b'not a PDF', 'application/pdf')})
    assert bad.status_code == 422
    h = teacher.post('/api/homework', json={'class_id':cid,'subject_id':1,'title':'Explain plants',
                                          'instructions':'Explain how leaves make food.', 'due_date':str(today())})
    assert h.status_code == 201, h.text
    hid = h.json()['id']
    assert student.post(f'/api/homework/{hid}/submit',json={'answer':'Plants use sunlight to make their food.'}).status_code == 200
    assert peer.get('/api/homework').json()[0]['my_submission'] is None
    assert peer.get(f'/api/homework/{hid}/submissions').status_code == 403
    subs = teacher.get(f'/api/homework/{hid}/submissions').json()
    assert len(subs) == 1
    sid = subs[0]['id']
    assert outsider.post(f'/api/submissions/{sid}/review',json={'status':'complete','feedback':'Good work'}).status_code == 404
    assert teacher.post(f'/api/submissions/{sid}/review',json={'status':'needs_revision','feedback':'Name the inputs too.'}).status_code == 200
    assert student.get('/api/homework').json()[0]['my_submission']['feedback'] == 'Name the inputs too.'
    assert student.post(f'/api/homework/{hid}/submit',json={'answer':'Water, carbon dioxide and sunlight are needed.'}).status_code == 200
    assert teacher.post(f'/api/submissions/{sid}/review',json={'status':'complete','feedback':'Great revision.'}).status_code == 200
    assert student.post(f'/api/homework/{hid}/submit',json={'answer':'Another answer'}).status_code == 409
    assert any(n['title'] == 'Homework reviewed' for n in student.get('/api/notifications').json())


def test_unassigned_teacher_and_invalid_members(context):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    c = admin.post('/api/classes',json={'name':'Private class','grade':5,'student_ids':[3]}).json()['id']
    assert teacher.get(f'/api/classes/{c}/roster').status_code == 403
    assert admin.post('/api/classes',json={'name':'Bad members','grade':5,'student_ids':[2]}).status_code == 422
    assert admin.post('/api/classes',json={'name':'Duplicates','grade':5,'student_ids':[3,3]}).status_code == 422


def test_real_pdf_upload_approval_and_download(context, tmp_path, monkeypatch):
    import io
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    from app.config import settings
    monkeypatch.setattr(settings(), 'upload_dir', str(tmp_path))
    login, _ = context
    admin, teacher, student = login('admin'), login('teacher'), login('student')
    cid = make_class(admin)
    writer = PdfWriter()
    page = writer.add_blank_page(600, 800)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 700 Td (Plants make their own food through photosynthesis. Roots absorb water from soil.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    payload = output.getvalue()
    result = teacher.post('/api/materials/upload',data={'class_id':cid,'subject_id':1,'title':'Readable PDF lesson'},
                          files={'file':('../../escape.pdf',payload,'application/pdf')})
    assert result.status_code == 201, result.text
    mid = result.json()['id']
    assert student.get(f'/api/materials/{mid}/download').status_code == 404
    assert teacher.post(f'/api/materials/{mid}/approve').status_code == 200
    downloaded = student.get(f'/api/materials/{mid}/download')
    assert downloaded.status_code == 200
    assert downloaded.content == payload
    assert 'attachment' in downloaded.headers['content-disposition']
    assert all('escape' not in str(p) for p in tmp_path.rglob('*'))
