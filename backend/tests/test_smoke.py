from app.schemas import StudentInput
from app.services.model_service import model_service


def test_model_predicts_one_student():
    model_service.load()
    student = StudentInput(student_id="TEST001", G1=14, G2=15, G3=15, studytime=3)
    prediction = model_service.predict_one(student)
    assert prediction.student_id == "TEST001"
    assert prediction.profile_id in {0, 1, 2, 3, 4}
    assert 0 <= prediction.confidence <= 1
