from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
from mock_data import generate_mock_data

app = FastAPI(title="Hệ Thống Quản Lý Đào Tạo API")

# --- In-memory Database ---
subjects_db, students_db, grades_db = generate_mock_data()

# --- Models ---
class Subject(BaseModel):
    id: str; name: str; credits: int = Field(..., gt=0)
    w_qt: float; w_gk: float; w_ck: float

class Student(BaseModel):
    mssv: str
    name: str
    class_name: str
    major: str

class GradeInput(BaseModel):
    mssv: str
    subject_id: str
    qt: float = Field(-1.0, ge=-1, le=10)
    gk: float = Field(-1.0, ge=-1, le=10)
    ck: float = Field(-1.0, ge=-1, le=10)

# --- Helper Functions ---
def calculate_gpa(mssv: str) -> float:
    student_grades = [g for g in grades_db if g["mssv"] == mssv]
    total_score = 0
    total_credits = 0
    
    for g in student_grades:
        if g.get("total") is not None:  # Chỉ tính khi đã có điểm tổng kết
            sub = next((s for s in subjects_db if s["id"] == g["subject_id"]), None)
            if sub:
                total_score += g["total"] * sub["credits"]
                total_credits += sub["credits"]
                
    return round(total_score / total_credits, 2) if total_credits > 0 else 0.0

# --- API Môn Học (Subjects) ---
@app.get("/api/subjects", response_model=List[Subject])
def get_subjects(q: Optional[str] = None):
    if not q: return subjects_db
    result = []
    for s in subjects_db:
        if q.lower() in s["name"].lower() or q in str(s["credits"]):
            result.append(s)
    return result

@app.post("/api/subjects")
def add_subject(sub: Subject):
    if sub.w_qt + sub.w_gk + sub.w_ck != 100:
        raise HTTPException(400, "Tổng phần trăm các cột điểm phải bằng 100%")
    if any(s["id"] == sub.id for s in subjects_db):
        raise HTTPException(400, "Mã môn học đã tồn tại")
    subjects_db.append(sub.dict())
    return {"message": "Thêm môn học thành công"}

@app.put("/api/subjects/{old_id}")
def update_subject(old_id: str, sub: Subject):
    for i, s in enumerate(subjects_db):
        if s["id"] == old_id:
            # Nếu đổi mã môn, kiểm tra trùng lặp
            if old_id != sub.id and any(x["id"] == sub.id for x in subjects_db):
                raise HTTPException(400, "Mã môn học mới đã tồn tại")
            subjects_db[i] = sub.dict()
            
            # Cập nhật mã môn trong bảng điểm (cascade update)
            if old_id != sub.id:
                for g in grades_db:
                    if g["subject_id"] == old_id:
                        g["subject_id"] = sub.id
            return {"message": "Cập nhật môn học thành công"}
    raise HTTPException(404, "Không tìm thấy môn học")

@app.delete("/api/subjects/{sub_id}")
def delete_subject(sub_id: str):
    global subjects_db, grades_db
    subjects_db = [s for s in subjects_db if s["id"] != sub_id]
    grades_db = [g for g in grades_db if g["subject_id"] != sub_id] # Xóa môn kéo theo xóa điểm môn đó
    return {"message": "Xóa môn học thành công"}

# --- API Sinh Viên (Students) ---
@app.get("/api/students")
def get_students(q: Optional[str] = None):
    result = []
    for st in students_db:
        if q and q.lower() not in st["mssv"].lower() and q.lower() not in st["name"].lower():
            continue
        st_data = st.copy()
        st_data["gpa"] = calculate_gpa(st["mssv"])
        result.append(st_data)
    return result

@app.post("/api/students")
def add_student(st: Student):
    if any(s["mssv"] == st.mssv for s in students_db):
        raise HTTPException(400, "MSSV đã tồn tại")
    students_db.append(st.dict())
    return {"message": "Thêm sinh viên thành công"}

@app.put("/api/students/{old_mssv}")
def update_student(old_mssv: str, st: Student):
    for i, s in enumerate(students_db):
        if s["mssv"] == old_mssv:
            # Nếu đổi MSSV, kiểm tra trùng lặp
            if old_mssv != st.mssv and any(x["mssv"] == st.mssv for x in students_db):
                raise HTTPException(400, "MSSV mới đã tồn tại hệ thống")
            
            students_db[i] = st.dict()
            
            # Cập nhật MSSV trong bảng điểm (cascade update)
            if old_mssv != st.mssv:
                for g in grades_db:
                    if g["mssv"] == old_mssv:
                        g["mssv"] = st.mssv
                        
            return {"message": "Cập nhật sinh viên thành công"}
    raise HTTPException(404, "Không tìm thấy sinh viên")

@app.delete("/api/students/{mssv}")
def delete_student(mssv: str):
    global students_db, grades_db
    students_db = [s for s in students_db if s["mssv"] != mssv]
    grades_db = [g for g in grades_db if g["mssv"] != mssv] # Cascade delete grades
    return {"message": "Xóa sinh viên thành công"}

# --- API Điểm (Grades) ---
def _matches_grade_filters(
    grade: dict,
    subject_name: str,
    sub_name: Optional[str],
    min_score: Optional[float],
    max_score: Optional[float],
) -> bool:
    if sub_name and sub_name.lower() not in subject_name.lower():
        return False
    if min_score is None and max_score is None:
        return True

    scores = [
        score
        for score in (grade["qt"], grade["gk"], grade["ck"], grade.get("total"))
        if score != -1 and score is not None
    ]
    lower_bound = min_score if min_score is not None else 0
    upper_bound = max_score if max_score is not None else 10
    
    # Chỉ trả về True nếu có ít nhất một điểm lọt vào khoảng
    return bool(scores) and any(lower_bound <= score <= upper_bound for score in scores)

@app.get("/api/grades/{mssv}")
def get_student_grades(
    mssv: str, 
    sub_name: Optional[str] = None, 
    min_score: Optional[float] = None, 
    max_score: Optional[float] = None
):
    result = []
    for g in grades_db:
        if g["mssv"] != mssv:
            continue
        
        sub = next((s for s in subjects_db if s["id"] == g["subject_id"]), None)
        # Bỏ qua nếu không tìm thấy môn, hoặc không thỏa mãn bộ lọc
        if sub is None or not _matches_grade_filters(g, sub["name"], sub_name, min_score, max_score):
            continue

        g_data = g.copy()
        g_data["subject_name"] = sub["name"]
        result.append(g_data)
    return result


@app.post("/api/grades")
def add_grade(g: GradeInput):
    sub = next((s for s in subjects_db if s["id"] == g.subject_id), None)
    if not sub:
        raise HTTPException(404, "Môn học không tồn tại")
    
    # KHI THÊM MỚI: Nếu môn đã có thì báo lỗi (chỉ cho phép qua nút Sửa)
    if any(existing["mssv"] == g.mssv and existing["subject_id"] == g.subject_id for existing in grades_db):
        raise HTTPException(400, "Môn học này đã được thêm vào danh sách điểm, vui lòng nhấn Sửa!")

    new_grade = g.dict()
    # Tính điểm
    if g.qt != -1 and g.gk != -1 and g.ck != -1:
        new_grade["total"] = round((g.qt * sub["w_qt"] + g.gk * sub["w_gk"] + g.ck * sub["w_ck"]) / 100, 2)
    else:
        new_grade["total"] = None
        
    grades_db.append(new_grade)
    return {"message": "Thêm điểm thành công"}

@app.put("/api/grades")
def update_grade(g: GradeInput):
    sub = next((s for s in subjects_db if s["id"] == g.subject_id), None)
    if not sub:
        raise HTTPException(404, "Môn học không tồn tại")
        
    for i, existing in enumerate(grades_db):
        if existing["mssv"] == g.mssv and existing["subject_id"] == g.subject_id:
            updated_grade = g.dict()
            if g.qt != -1 and g.gk != -1 and g.ck != -1:
                updated_grade["total"] = round((g.qt * sub["w_qt"] + g.gk * sub["w_gk"] + g.ck * sub["w_ck"]) / 100, 2)
            else:
                updated_grade["total"] = None
                
            grades_db[i] = updated_grade
            return {"message": "Cập nhật điểm thành công"}
            
    raise HTTPException(404, "Điểm môn này chưa tồn tại")

@app.delete("/api/grades/{mssv}/{sub_id}")
def delete_grade(mssv: str, sub_id: str):
    global grades_db
    grades_db = [g for g in grades_db if not (g["mssv"] == mssv and g["subject_id"] == sub_id)]
    return {"message": "Xóa điểm môn học thành công"}

# Phục vụ file tĩnh
app.mount("/", StaticFiles(directory="static", html=True), name="static")








































# Phia duoi la code cu, de tham khao khi can

# from fastapi import FastAPI, HTTPException
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel, Field
# from typing import List, Optional

# app = FastAPI(title="Quản Lý Sinh Viên")

# student_db= []

# class Student(BaseModel):
#     id: str
#     name: str
#     # Điểm tự động ép kiểu về float, bắt buộc >= 0 và <= 10
#     score: float = Field(..., ge=0, le=10, description="Điểm từ 0 đến 10")

# # API lay danh sach (va tim kiem)
# @app.get("/api/students", response_model=List[Student])
# def get_students(search: Optional[str] = None):
#     if search:
#         return [s for s in student_db if search.lower() in s["name"].lower()]
#     return student_db

# # API them sinh vien
# @app.post("/api/students")
# def add_student(student: Student):
#     # Kiem tra trung mssv
#     for s in student_db:
#         if s["id"] == student.id:
#             raise HTTPException(status_code=400, detail="Mã số sinh viên đã tồn tại")
        
#     student_db.append(student.dict())
#     return {"message": "Thêm sinh viên thành công"}

# # Phuc vu giao dien frontend tinh
# app.mount("/", StaticFiles(directory="static", html=True), name="static")