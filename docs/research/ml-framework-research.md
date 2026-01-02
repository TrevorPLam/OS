# ML Framework Research: scikit-learn vs TensorFlow

**Status:** Research Complete  
**Date:** January 2, 2026  
**Related Features:** 
- AI-Powered Lead Scoring (AI-LEAD-1 through AI-LEAD-5)
- CRM Intelligence Enhancements (CRM-INT-2: Dynamic Client Health Score)
- Advanced AI Features (AI-1 through AI-4)
- Scheduling Intelligence (SCHED-INT-1 through SCHED-INT-4)

**Priority:** HIGH

## Executive Summary

This document evaluates ML framework options for implementing machine learning features across the platform, including lead scoring, client health scoring, predictive analytics, and scheduling optimization.

## Use Cases Requiring ML

### High Priority
1. **Lead Scoring** (AI-LEAD-1 through AI-LEAD-5)
   - Predict lead quality based on historical conversion data
   - Score range: 0-100
   - Features: contact attributes, behavioral data, demographic data
   - Model type: Classification (will they convert?) or Regression (score prediction)

2. **Client Health Score** (CRM-INT-2)
   - Predict client churn risk
   - Multi-factor scoring: engagement, payments, communication, project delivery
   - Real-time updates needed
   - Alert thresholds for at-risk clients

3. **Win Probability Prediction** (AI-3)
   - Predict likelihood of deal closure
   - Features: deal stage, value, age, contact engagement
   - Model type: Binary classification (win/loss) or Regression (probability)

4. **Churn Prediction** (AI-4)
   - Predict client churn within next 90 days
   - Features: payment history, engagement metrics, support tickets
   - Model type: Binary classification

### Medium Priority
5. **Predictive Send-Time Optimization** (AI-1)
   - Predict best email send times per contact
   - Features: historical open/click times, timezone, industry
   - Model type: Time series / Recommendation

6. **No-Show Prediction** (SCHED-INT-1)
   - Predict meeting no-show probability
   - Features: historical behavior, meeting type, notice time
   - Model type: Binary classification

## Framework Comparison

### Option 1: scikit-learn (Recommended for MVP)

**Website:** https://scikit-learn.org/  
**License:** BSD 3-Clause (permissive open source)  
**Latest Version:** 1.4.x  
**Language:** Python

#### Pros
- ✅ **Perfect for tabular data** - Most of our use cases involve structured data
- ✅ **Shallow learning excellence** - Best-in-class for traditional ML (Random Forest, Gradient Boosting, SVM)
- ✅ **Fast training times** - Models train in seconds/minutes, not hours
- ✅ **Low resource requirements** - Runs on CPU, no GPU needed
- ✅ **Easy deployment** - Models serialize to pickle/joblib files (~1-10 MB)
- ✅ **Excellent documentation** - Clear examples, great API design
- ✅ **Mature and stable** - 15+ years of development
- ✅ **Large ecosystem** - pandas, numpy integration seamless
- ✅ **Explainability built-in** - Feature importance, SHAP integration
- ✅ **Fast inference** - Predictions in milliseconds
- ✅ **Low learning curve** - Team can become productive quickly

#### Cons
- ⚠️ **No deep learning support** - Can't build neural networks (not needed for our use cases)
- ⚠️ **No GPU acceleration** - Not an issue for our data sizes (<1M rows)
- ⚠️ **Limited time series support** - Would need additional libraries for complex time series

#### Best For
- Lead scoring
- Client health scoring
- Churn prediction
- Win probability
- No-show prediction
- Any tabular data classification/regression

#### Example Code

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, classification_report
import joblib

# Lead Scoring Model
class LeadScoringModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
    
    def train(self, X, y):
        """Train on historical lead data"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred)
        print(f"AUC: {auc:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X, y, cv=5, scoring='roc_auc'
        )
        print(f"CV AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    def predict_score(self, X):
        """Predict lead score (0-100)"""
        probability = self.model.predict_proba(X)[:, 1]
        return (probability * 100).astype(int)
    
    def get_feature_importance(self):
        """Return feature importance for explainability"""
        return dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
    
    def save(self, path):
        """Save model to disk"""
        joblib.dump(self.model, path)
    
    @classmethod
    def load(cls, path):
        """Load model from disk"""
        instance = cls()
        instance.model = joblib.load(path)
        return instance
```

#### Recommended Algorithms by Use Case

| Use Case | Algorithm | Justification |
|----------|-----------|---------------|
| Lead Scoring | Random Forest or XGBoost | Handles non-linear relationships, feature importance built-in |
| Client Health | Gradient Boosting (XGBoost/LightGBM) | Highest accuracy for structured data |
| Churn Prediction | Logistic Regression or XGBoost | Interpretable (LR) or accurate (XGBoost) |
| Win Probability | XGBoost | Best for imbalanced datasets |
| No-Show Prediction | Random Forest | Robust to outliers, easy to explain |
| Send-Time Optimization | K-Means Clustering + Rules | Group users by behavior patterns |

### Option 2: TensorFlow/Keras

**Website:** https://www.tensorflow.org/  
**License:** Apache 2.0  
**Latest Version:** 2.15.x  
**Language:** Python

#### Pros
- ✅ **Deep learning support** - Can build complex neural networks
- ✅ **GPU acceleration** - Fast training for large datasets (>1M rows)
- ✅ **TensorFlow Serving** - Production-ready model serving
- ✅ **TensorBoard** - Advanced visualization and monitoring
- ✅ **Wide adoption** - Industry standard for deep learning

#### Cons
- ❌ **Overkill for tabular data** - scikit-learn often outperforms for structured data
- ❌ **Longer training times** - Neural networks take hours, not minutes
- ❌ **Complex deployment** - Requires TensorFlow runtime (~500MB+)
- ❌ **Higher resource usage** - GPU needed for efficient training
- ❌ **Steeper learning curve** - Harder for team to debug and maintain
- ❌ **Slower inference** - Milliseconds vs microseconds for simple predictions
- ❌ **Less interpretable** - Black box models, harder to explain predictions
- ❌ **Larger model files** - 50-500 MB vs 1-10 MB for scikit-learn

#### Best For
- Image recognition (not our primary use case)
- Natural language processing (could be useful for email content analysis)
- Time series forecasting with complex patterns
- When you have >1M training samples

#### When to Consider TensorFlow

Only if we need:
1. **Natural Language Processing** - Email content analysis, document classification
2. **Image Recognition** - Document type classification from scanned images
3. **Very large datasets** - >1M training samples where deep learning excels
4. **Complex time series** - Multiple seasonal patterns, long-term dependencies

### Option 3: PyTorch

**Website:** https://pytorch.org/  
**License:** BSD 3-Clause  
**Latest Version:** 2.1.x

#### Pros/Cons
- Similar to TensorFlow but with more Pythonic API
- Preferred by researchers, less production-ready than TensorFlow
- Same overkill concerns as TensorFlow for our use cases

**Verdict:** Not recommended unless we hire ML researchers

### Option 4: XGBoost / LightGBM (Complementary to scikit-learn)

**Recommendation:** ✅ **Use alongside scikit-learn**

These are gradient boosting libraries that work seamlessly with scikit-learn API:
- **XGBoost:** https://xgboost.readthedocs.io/
- **LightGBM:** https://lightgbm.readthedocs.io/

#### Why Include?
- Often achieve highest accuracy on structured data (Kaggle winners)
- Drop-in replacement for scikit-learn classifiers
- Still fast training (minutes, not hours)
- Still lightweight deployment
- Better performance on imbalanced datasets

```python
from xgboost import XGBClassifier

# Drop-in replacement for RandomForestClassifier
model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)
```

## Recommendation

### **Recommended Stack: scikit-learn + XGBoost/LightGBM** ✅

#### Justification

1. **Perfect fit for our data types** - 95% of our ML use cases involve tabular/structured data
2. **Fast iteration** - Train and test models in minutes, not hours
3. **Easy deployment** - Lightweight models, fast inference, no GPU needed
4. **Team productivity** - Lower learning curve, easier debugging
5. **Explainability** - Critical for business users to trust predictions
6. **Cost-effective** - No GPU infrastructure needed
7. **Battle-tested** - Used by thousands of companies for similar use cases

#### When to Revisit TensorFlow

Consider adding TensorFlow later if we need:
- **Email content analysis** - Sentiment analysis, intent classification (NLP)
- **Document image classification** - OCR + classification of scanned docs
- **Very large datasets** - Once we have >1M training samples per model
- **Complex time series** - If simple time series models don't perform well

But for MVP and first year of ML features, scikit-learn + XGBoost is ideal.

## Implementation Plan

### Phase 1: Infrastructure Setup (4-6 hours)
- Create ML module structure in Django
- Set up model storage (S3 or local filesystem)
- Create model versioning system
- Set up training pipeline (Celery task)
- Create inference API endpoint

### Phase 2: Lead Scoring MVP (12-16 hours)
- Define features (20-30 features from contact/activity data)
- Collect historical training data (conversions vs non-conversions)
- Train initial model (Random Forest)
- Evaluate performance (AUC, precision, recall)
- Deploy model
- Create admin UI for model monitoring

### Phase 3: Model Monitoring (4-6 hours)
- Track model performance over time
- Detect model drift (data distribution changes)
- Set up retraining schedule (weekly/monthly)
- Create alerts for performance degradation

### Phase 4: Additional Models (8-12 hours each)
- Client Health Score model
- Churn Prediction model
- Win Probability model
- No-Show Prediction model

### Total Estimated Effort: 28-40 hours for MVP + infrastructure

## Code Structure

```
src/modules/ml/
├── __init__.py
├── models.py                      # Django models (MLModel, MLPrediction)
├── training/
│   ├── __init__.py
│   ├── lead_scoring.py           # Lead scoring training pipeline
│   ├── client_health.py          # Client health training pipeline
│   └── base.py                   # Base training class
├── inference/
│   ├── __init__.py
│   ├── lead_scoring.py           # Lead scoring inference
│   └── base.py                   # Base inference class
├── features/
│   ├── __init__.py
│   ├── contact_features.py       # Extract features from contacts
│   ├── activity_features.py      # Extract features from activities
│   └── base.py                   # Base feature extractor
├── monitoring/
│   ├── __init__.py
│   ├── performance.py            # Track model performance
│   └── drift.py                  # Detect data/concept drift
└── api/
    ├── __init__.py
    ├── views.py                  # API endpoints
    └── serializers.py            # DRF serializers
```

## Dependencies

```python
# requirements.txt
scikit-learn==1.4.0
xgboost==2.0.3
lightgbm==4.1.0
pandas==2.1.4
numpy==1.26.2
joblib==1.3.2
shap==0.44.0  # For model explainability
```

## Model Deployment Strategy

### Development
- Train models locally or on CI/CD
- Store in Git LFS or S3
- Version with semantic versioning (v1.0.0)

### Production
- Load models on Django startup (cached in memory)
- Inference via API endpoint
- Batch predictions via Celery task
- Real-time predictions (<100ms response time)

### Model Updates
- Train new model version
- A/B test against current model (10% traffic)
- Promote to 100% if performance improves
- Keep last 3 versions for rollback

## Performance Benchmarks

### Expected Performance (scikit-learn)

| Operation | Time | Notes |
|-----------|------|-------|
| Model Training | 1-5 minutes | 10k-100k samples, 20-50 features |
| Single Prediction | <1ms | Random Forest, 100 trees |
| Batch Prediction (1000) | <100ms | Vectorized numpy operations |
| Model Load | <100ms | From disk to memory |
| Model Size | 1-10 MB | Compressed pickle/joblib |

### Expected Performance (TensorFlow)

| Operation | Time | Notes |
|-----------|------|-------|
| Model Training | 30min-2hr | Neural network with GPU |
| Single Prediction | 5-10ms | Includes TF runtime overhead |
| Batch Prediction (1000) | 100-500ms | GPU batching helps |
| Model Load | 500ms-2s | Load TF runtime + model |
| Model Size | 50-500 MB | Model + TF dependencies |

**Verdict:** scikit-learn is 10-100x faster for our use cases

## Explainability & Compliance

### Why Explainability Matters
- Build user trust in predictions
- Comply with GDPR "right to explanation"
- Debug model issues
- Identify bias in predictions

### Tools for Explainability
- **SHAP (SHapley Additive exPlanations)** - Best for explaining individual predictions
- **Feature Importance** - Built into Random Forest, XGBoost
- **Partial Dependence Plots** - Show feature effect on predictions

```python
import shap

# Explain a single prediction
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test[0:1])

# "This lead scored 85 because:
# - Email domain is @fortune500.com (+15 points)
# - Opened 5 emails in last 7 days (+12 points)
# - Job title is 'Director' (+8 points)"
```

## References

- scikit-learn Documentation: https://scikit-learn.org/stable/
- XGBoost Documentation: https://xgboost.readthedocs.io/
- LightGBM Documentation: https://lightgbm.readthedocs.io/
- SHAP Documentation: https://shap.readthedocs.io/
- ML Best Practices: https://developers.google.com/machine-learning/guides/rules-of-ml

## Next Steps

1. ✅ **Research Complete** - scikit-learn + XGBoost selected
2. [ ] Create ML module infrastructure (4-6 hours)
3. [ ] Build lead scoring MVP (12-16 hours)
4. [ ] Set up model monitoring (4-6 hours)
5. [ ] Update TODO.md to mark research task as complete

---

**Research Completed By:** Development Team  
**Approved By:** [Pending Review]  
**Implementation Target:** Q1 2026
