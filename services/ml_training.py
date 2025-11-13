"""Machine learning model training service."""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Callable, Optional
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
import joblib
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def train_resume_scoring_model(
    resumes: List[Dict],
    hyperparameters: Dict = None,
    on_progress: Optional[Callable[[int, str], None]] = None
) -> Dict:
    """
    Train a resume scoring model using the provided training data.

    This model learns to predict resume quality scores based on features
    extracted from parsed resume data.

    Args:
        resumes: List of training resume documents
        hyperparameters: Optional custom hyperparameters
        on_progress: Callback function for progress updates

    Returns:
        Dictionary with training metrics
    """
    try:
        logger.info(f"Starting model training with {len(resumes)} resumes")

        if on_progress:
            on_progress(5, "Extracting features from resumes")

        # Extract features from resumes
        features, labels = _extract_features_and_labels(resumes)

        if len(features) == 0:
            raise ValueError("No valid features extracted from resumes")

        if on_progress:
            on_progress(20, "Preparing training data")

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(features)
        y = np.array(labels)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            df, y, test_size=0.2, random_state=42
        )

        if on_progress:
            on_progress(30, "Scaling features")

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        if on_progress:
            on_progress(40, "Training model")

        # Get hyperparameters
        hp = hyperparameters or {}
        n_estimators = hp.get('n_estimators', 100)
        max_depth = hp.get('max_depth', 10)
        learning_rate = hp.get('learning_rate', 0.1)

        # Train gradient boosting regressor
        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42
        )

        model.fit(X_train_scaled, y_train)

        if on_progress:
            on_progress(70, "Evaluating model")

        # Evaluate model
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)

        # Calculate metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        test_mse = mean_squared_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)

        # Calculate accuracy within threshold (0.1 difference)
        train_accuracy = np.mean(np.abs(y_train - y_pred_train) < 0.1)
        test_accuracy = np.mean(np.abs(y_test - y_pred_test) < 0.1)

        if on_progress:
            on_progress(85, "Saving model")

        # Save model and scaler
        model_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
        models_dir = os.path.join(model_dir, 'models')
        os.makedirs(models_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        model_path = os.path.join(models_dir, f'resume_scorer_{timestamp}.pkl')
        scaler_path = os.path.join(models_dir, f'scaler_{timestamp}.pkl')

        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        # Save as latest
        latest_model_path = os.path.join(models_dir, 'resume_scorer_latest.pkl')
        latest_scaler_path = os.path.join(models_dir, 'scaler_latest.pkl')

        joblib.dump(model, latest_model_path)
        joblib.dump(scaler, latest_scaler_path)

        if on_progress:
            on_progress(100, "Training completed")

        logger.info(f"Model training completed. Test R²: {test_r2:.4f}, Test Accuracy: {test_accuracy:.4f}")

        return {
            'trainingSamples': len(X_train),
            'testSamples': len(X_test),
            'trainMse': float(train_mse),
            'testMse': float(test_mse),
            'trainR2': float(train_r2),
            'testR2': float(test_r2),
            'trainAccuracy': float(train_accuracy),
            'testAccuracy': float(test_accuracy),
            'modelPath': model_path,
            'scalerPath': scaler_path,
            'featureCount': len(df.columns),
            'hyperparameters': {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate
            }
        }

    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        raise


def _extract_features_and_labels(resumes: List[Dict]) -> tuple:
    """
    Extract features and labels from resume documents.

    Args:
        resumes: List of resume documents

    Returns:
        Tuple of (features list, labels list)
    """
    features = []
    labels = []

    for resume in resumes:
        try:
            parsed = resume.get('parsedData', {})
            quality_score = resume.get('qualityScore', 0)

            # Extract features
            feature_dict = {
                # Contact features
                'has_contact': 1 if parsed.get('contact') else 0,
                'has_email': 1 if parsed.get('contact', {}).get('email') else 0,
                'has_phone': 1 if parsed.get('contact', {}).get('phone') else 0,

                # Experience features
                'experience_count': len(parsed.get('experience', [])),
                'total_years_experience': _calculate_total_years(parsed.get('experience', [])),

                # Education features
                'education_count': len(parsed.get('education', [])),
                'has_degree': 1 if any(_has_degree(edu) for edu in parsed.get('education', [])) else 0,

                # Skills features
                'skills_count': len(parsed.get('skills', [])),

                # Text features
                'text_length': len(parsed.get('raw_text', '')),
                'word_count': len(parsed.get('raw_text', '').split()),

                # Structure features
                'has_summary': 1 if parsed.get('summary') else 0,
                'has_certifications': 1 if parsed.get('certifications') else 0,
                'section_count': _count_sections(parsed)
            }

            features.append(feature_dict)
            labels.append(quality_score)

        except Exception as e:
            logger.warning(f"Error extracting features from resume: {str(e)}")
            continue

    return features, labels


def _calculate_total_years(experience_list: List[Dict]) -> float:
    """Calculate total years of experience."""
    total_months = 0
    for exp in experience_list:
        # Simplified - in production, parse actual dates
        total_months += 12  # Assume 1 year per position
    return total_months / 12.0


def _has_degree(education: Dict) -> bool:
    """Check if education entry represents a degree."""
    degree_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'associate', 'b.s', 'm.s', 'b.a', 'm.a']
    degree_text = str(education.get('degree', '')).lower()
    return any(keyword in degree_text for keyword in degree_keywords)


def _count_sections(parsed_data: Dict) -> int:
    """Count number of resume sections."""
    section_keys = ['contact', 'summary', 'experience', 'education', 'skills', 'certifications', 'projects', 'awards']
    return sum(1 for key in section_keys if parsed_data.get(key))


def load_latest_model():
    """
    Load the latest trained resume scoring model.

    Returns:
        Tuple of (model, scaler) or (None, None) if not found
    """
    try:
        model_dir = os.getenv('TRAINING_DATA_DIR', 'training_data')
        models_dir = os.path.join(model_dir, 'models')

        model_path = os.path.join(models_dir, 'resume_scorer_latest.pkl')
        scaler_path = os.path.join(models_dir, 'scaler_latest.pkl')

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            logger.info("Loaded latest resume scoring model")
            return model, scaler
        else:
            logger.warning("No trained model found")
            return None, None

    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None, None


def predict_resume_quality(parsed_resume: Dict) -> float:
    """
    Predict quality score for a resume using the trained model.

    Args:
        parsed_resume: Parsed resume data

    Returns:
        Predicted quality score (0-1)
    """
    try:
        model, scaler = load_latest_model()

        if model is None or scaler is None:
            # Fallback to rule-based scoring
            logger.warning("No trained model available, using fallback scoring")
            return _fallback_quality_score(parsed_resume)

        # Extract features
        features, _ = _extract_features_and_labels([{'parsedData': parsed_resume, 'qualityScore': 0}])

        if len(features) == 0:
            return _fallback_quality_score(parsed_resume)

        # Convert to DataFrame
        df = pd.DataFrame(features)

        # Scale features
        X_scaled = scaler.transform(df)

        # Predict
        prediction = model.predict(X_scaled)[0]

        # Clip to 0-1 range
        return float(np.clip(prediction, 0, 1))

    except Exception as e:
        logger.error(f"Error predicting quality: {str(e)}")
        return _fallback_quality_score(parsed_resume)


def _fallback_quality_score(parsed_data: Dict) -> float:
    """
    Fallback rule-based quality scoring when ML model is not available.

    Args:
        parsed_data: Parsed resume data

    Returns:
        Quality score between 0 and 1
    """
    score = 0.0
    max_score = 10.0

    # Contact information (1 point)
    if parsed_data.get('contact'):
        score += 1.0

    # Experience (3 points)
    experience = parsed_data.get('experience', [])
    if len(experience) > 0:
        score += 1.0
    if len(experience) >= 2:
        score += 1.0
    if len(experience) >= 3:
        score += 1.0

    # Education (2 points)
    education = parsed_data.get('education', [])
    if len(education) > 0:
        score += 1.5
    if len(education) >= 2:
        score += 0.5

    # Skills (2 points)
    skills = parsed_data.get('skills', [])
    if len(skills) >= 3:
        score += 1.0
    if len(skills) >= 6:
        score += 1.0

    # Length/completeness (2 points)
    text_length = len(parsed_data.get('raw_text', ''))
    if text_length > 200:
        score += 1.0
    if text_length > 500:
        score += 1.0

    return round(score / max_score, 2)
