from app.schemas import StudentInput
from app.services.model_service import model_service


def test_model_predicts_one_student():
    model_service.load()
    student = StudentInput(student_id="TEST001", student_name="Test Student", G1=14, G2=15, G3=15, studytime=3)
    prediction = model_service.predict_one(student)
    assert prediction.student_id == "TEST001"
    assert prediction.profile_id in {0, 1, 2, 3, 4}
    assert 0 <= prediction.confidence <= 1

def test_feature_count_matches_model():
    model_service.load()
    expected = model_service.rf_model.n_features_in_
    assert expected == len(model_service.model_features), (
        f"El modelo espera {expected} features pero selected_features.json "
        f"tiene {len(model_service.model_features)}"
    )