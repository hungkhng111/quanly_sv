import random

def generate_mock_data():
    subjects_db = []
    students_db = []
    grades_db = []

    # 1. TẠO 15 MÔN HỌC IT (Trọng số mặc định: 20-30-50, Tín chỉ: 3-5)
    it_subjects = [
        ("IT01", "Nhập môn Lập trình"), ("IT02", "Kỹ thuật Lập trình"),
        ("IT03", "Cấu trúc dữ liệu & Giải thuật"), ("IT04", "Cơ sở dữ liệu"),
        ("IT05", "Lập trình hướng đối tượng"), ("IT06", "Mạng máy tính"),
        ("IT07", "Hệ điều hành"), ("IT08", "Trí tuệ nhân tạo"),
        ("IT09", "Công nghệ phần mềm"), ("IT10", "Tương tác người máy (HCI)"),
        ("IT11", "Lập trình Web"), ("IT12", "Lập trình di động"),
        ("IT13", "An toàn thông tin"), ("IT14", "Điện toán đám mây"),
        ("IT15", "Học máy (Machine Learning)")
    ]
    
    for sid, name in it_subjects:
        subjects_db.append({
            "id": sid, 
            "name": name, 
            "credits": random.randint(3, 5), # Random 3 đến 5 tín chỉ
            "w_qt": 20.0, "w_gk": 30.0, "w_ck": 50.0
        })

    # 2. TẠO 30 SINH VIÊN (Tên tiếng Việt đa dạng, mssv 4 chữ số 1001 -> 1030)
    ho_list = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng"]
    dem_list = ["Văn", "Thị", "Ngọc", "Hữu", "Đức", "Minh", "Thanh", "Hoài", "Gia", "Thành"]
    
    # 30 tên xếp đa dạng theo bảng chữ cái
    ten_list = [
        "An", "Bình", "Châu", "Cường", "Dương", "Đạt", "Đức", "Giang", "Hải", "Hưng",
        "Khang", "Kiên", "Linh", "Long", "Mai", "Nam", "Nghĩa", "Ngọc", "Oanh", "Phong",
        "Quân", "Quang", "Sang", "Thành", "Thảo", "Tuấn", "Uyên", "Vinh", "Vy", "Yến"
    ]

    for i in range(30):
        mssv = f"{1001 + i}" # Tạo MSSV từ 1001 đến 1030
        full_name = f"{random.choice(ho_list)} {random.choice(dem_list)} {ten_list[i]}"
        students_db.append({
            "mssv": mssv, 
            "name": full_name, 
            "class_name": "IT45A", 
            "major": "Công nghệ thông tin"
        })

    # 3. TẠO ĐIỂM NGẪU NHIÊN CHO TỪNG SINH VIÊN (Học 5-15 môn)
    for st in students_db:
        # Chọn ngẫu nhiên từ 5 đến 15 môn học cho sinh viên này
        num_subjects = random.randint(5, 15)
        chosen_subjects = random.sample(subjects_db, num_subjects)
        
        for sub in chosen_subjects:
            # Random điểm từ 3.0 đến 10.0 (giả lập có cả điểm thấp và cao)
            qt = round(random.uniform(4.0, 10.0), 1)
            gk = round(random.uniform(3.0, 10.0), 1)
            ck = round(random.uniform(2.0, 10.0), 1)
            
            # Tính điểm tổng kết
            total = round((qt * sub["w_qt"] + gk * sub["w_gk"] + ck * sub["w_ck"]) / 100, 2)
            
            grades_db.append({
                "mssv": st["mssv"],
                "subject_id": sub["id"],
                "qt": qt, "gk": gk, "ck": ck,
                "total": total
            })

    return subjects_db, students_db, grades_db