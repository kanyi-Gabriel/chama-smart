import os
import joblib
import numpy as np
from django.conf import settings
from .feature_engineering import extract_member_features


# Path where trained model will be saved
MODEL_PATH = os.path.join(settings.BASE_DIR, 'analytics', 'credit_model.pkl')


def rules_based_score(features):
    """
    Phase 1: Rules-based scoring.
    Works immediately with zero training data.
    Score range: 0 - 100

    Each factor contributes points:
    - On-time contribution rate: up to 40 points
    - Completion rate: up to 20 points
    - Loan repayment rate: up to 20 points
    - Penalty frequency: up to -20 points (penalty)
    - Months active (loyalty): up to 10 points
    - Defaulted loans: up to -30 points (heavy penalty)
    """
    score = 50.0  # Neutral starting point

    # Reward consistent on-time payments (max +40)
    score += features['on_time_rate'] * 40

    # Reward completing contributions (max +20)
    score += features['completed_rate'] * 20

    # Reward loan repayment history (max +20)
    score += features['loan_repayment_rate'] * 20

    # Reward loyalty — being active longer (max +10)
    loyalty_bonus = min(features['months_active'] / 12, 1.0) * 10
    score += loyalty_bonus

    # Penalize late payment frequency
    score -= features['penalty_frequency'] * 10

    # Heavy penalty for defaults
    score -= features['defaulted_loans'] * 30

    # Keep score within 0-100
    score = max(0.0, min(100.0, score))

    return round(score, 2)


def ml_based_score(features):
    """
    Phase 2: Trained ML model scoring.
    Used when enough training data exists (50+ members with history).
    Falls back to rules-based if model file doesn't exist.
    """
    if not os.path.exists(MODEL_PATH):
        return rules_based_score(features)

    try:
        model = joblib.load(MODEL_PATH)
        feature_vector = np.array([[
            features['on_time_rate'],
            features['late_rate'],
            features['completed_rate'],
            features['avg_penalty_amount'],
            features['penalty_frequency'],
            features['months_active'],
            features['loan_repayment_rate'],
            features['active_loans'],
            features['defaulted_loans'],
        ]])
        score = model.predict(feature_vector)[0]
        return round(float(max(0.0, min(100.0, score))), 2)
    except Exception:
        # Model failed — fall back to rules
        return rules_based_score(features)


def get_credit_score(user, chama=None):
    """
    Main entry point for scoring a member.
    Returns score and recommendation.
    """
    features = extract_member_features(user, chama)
    score = ml_based_score(features)

    # Recommendation thresholds
    if score >= 70:
        recommendation = 'approve'
        risk_level = 'low'
    elif score >= 50:
        recommendation = 'review'
        risk_level = 'medium'
    else:
        recommendation = 'reject'
        risk_level = 'high'

    return {
        'score': score,
        'recommendation': recommendation,
        'risk_level': risk_level,
        'features': features
    }


def update_member_credit_score(user, chama):
    """
    Called automatically after every contribution or loan repayment.
    Updates the membership credit_score field.
    """
    from chamas.models import Membership
    try:
        membership = Membership.objects.get(user=user, chama=chama)
        result = get_credit_score(user, chama)
        membership.credit_score = result['score']
        membership.save()
        return result
    except Membership.DoesNotExist:
        return None


def train_model():
    """
    Phase 2: Train the ML model on historical data.
    Run this manually once you have 50+ members with contribution history:
    python3 manage.py shell
    from analytics.ml_scorer import train_model
    train_model()
    """
    from chamas.models import Membership
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error

    print("Collecting training data...")
    memberships = Membership.objects.filter(
        is_active=True
    ).select_related('user', 'chama')

    X, y = [], []
    for membership in memberships:
        features = extract_member_features(membership.user, membership.chama)
        if features['total_contributions'] >= 3:
            X.append([
                features['on_time_rate'],
                features['late_rate'],
                features['completed_rate'],
                features['avg_penalty_amount'],
                features['penalty_frequency'],
                features['months_active'],
                features['loan_repayment_rate'],
                features['active_loans'],
                features['defaulted_loans'],
            ])
            # Use rules-based score as training target initially
            y.append(rules_based_score(features))

    if len(X) < 10:
        print(f"Not enough data yet ({len(X)} samples). Need at least 10.")
        return False

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training on {len(X_train)} samples...")
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"Model MAE: {mae:.2f} points")

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    return True