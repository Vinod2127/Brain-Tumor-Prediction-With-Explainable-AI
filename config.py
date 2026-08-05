"""
Configuration Module for Brain Tumor Detection System
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# ==================== FLASK CONFIGURATION ====================
class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Flask settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
    
    # Model settings
    MODEL_PATH = os.getenv('MODEL_PATH', 'efficientnetb3_best.keras')
    FALLBACK_MODEL_PATH = 'efficientnetb3_final.keras'
    IMG_SIZE = (300, 300)
    LAST_CONV_LAYER = 'top_conv'
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
    
    # Class names for brain tumors
    CLASS_NAMES = ['glioma_tumor', 'meningioma_tumor', 'no_tumor', 'pituitary_tumor']
    
    # Explainability
    ENABLE_GRADCAM = os.getenv('GRADCAM_ENABLED', 'false').lower() in ('1', 'true', 'yes')

    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Disable file uploads in production if needed
    # UPLOAD_FOLDER = '/var/uploads'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB for testing

# Select configuration based on environment
ENV = os.getenv('FLASK_ENV', 'development')

if ENV == 'production':
    config = ProductionConfig()
elif ENV == 'testing':
    config = TestingConfig()
else:
    config = DevelopmentConfig()

# Ensure upload folder exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Tumor class descriptions with detailed medical information
CLASS_DESCRIPTIONS = {
    'glioma_tumor': {
        'name': 'Glioma Tumor',
        'severity': 'High',
        'color': '#ef4444',
        'short_description': 'A malignant brain cancer arising from glial cells',
        'detailed_description': '''
Glioma is the most common type of primary brain tumor, originating from glial cells 
(support cells in the brain). It is highly aggressive and invasive.

Types:
- Astrocytomas
- Oligodendrogliomas  
- Ependymomas
- Mixed gliomas
        ''',
        'symptoms': [
            'Headaches (often worse in the morning)',
            'Seizures',
            'Vision or hearing problems',
            'Balance and coordination difficulties',
            'Nausea and vomiting',
            'Cognitive changes or memory issues',
            'Motor weakness on one side of body'
        ],
        'causes': [
            'Genetic mutations in glial cells',
            'Possible radiation exposure',
            'Possible genetic syndromes'
        ],
        'effects_on_health': [
            'Cognitive decline and memory loss',
            'Motor control impairment',
            'Sensory loss (vision, hearing)',
            'Increased intracranial pressure',
            'Potential brain damage if untreated',
            'High mortality rate if malignant'
        ],
        'treatment_options': [
            'Surgery (tumor resection)',
            'Radiation therapy',
            'Chemotherapy',
            'Targeted therapy',
            'Combined multimodal treatment'
        ],
        'prognosis': 'Depends on grade (I-IV). Lower grades have better prognosis (5-10 years survival). Grade IV (Glioblastoma) has poor prognosis (12-15 months median survival).',
        'urgency': 'IMMEDIATE - Requires urgent consultation and treatment planning'
    },
    'meningioma_tumor': {
        'name': 'Meningioma Tumor',
        'severity': 'Medium',
        'color': '#f59e0b',
        'short_description': 'A tumor arising from the meninges (brain membrane)',
        'detailed_description': '''
Meningiomas are tumors arising from the dura mater and arachnoid membrane that 
surround and protect the brain and spinal cord. Most are benign but can be serious 
due to compression of brain tissue.

Characteristics:
- Typically slow-growing
- Usually benign (80-90%)
- Can compress brain tissue
- May affect cerebrospinal fluid circulation
        ''',
        'symptoms': [
            'Headaches',
            'Vision problems (double or blurred)',
            'Hearing loss (ringing in ears)',
            'Weakness in legs or arms',
            'Seizures',
            'Balance and coordination problems',
            'Personality or behavioral changes'
        ],
        'causes': [
            'Unknown primary cause',
            'Possible radiation exposure history',
            'Hormonal factors (more common in women)',
            'Genetic syndromes (neurofibromatosis type 2)'
        ],
        'effects_on_health': [
            'Brain compression and swelling',
            'Impaired cognitive function',
            'Motor and sensory deficits',
            'Hydrocephalus (fluid accumulation)',
            'Quality of life impacts',
            'Generally better outcomes than gliomas'
        ],
        'treatment_options': [
            'Surgical resection (primary treatment)',
            'Radiation therapy if surgery incomplete',
            'Observation (for slow-growing benign tumors)',
            'Chemotherapy (rare)',
            'Stereotactic radiosurgery'
        ],
        'prognosis': 'Generally favorable for benign meningiomas. 5-year survival rate: 85-90%. Malignant meningiomas have poorer outcomes.',
        'urgency': 'URGENT - Requires neurosurgical consultation and treatment planning'
    },
    'no_tumor': {
        'name': 'No Tumor',
        'severity': 'None',
        'color': '#10b981',
        'short_description': 'Normal brain MRI - No tumor detected',
        'detailed_description': '''
Good news! The MRI scan shows normal brain tissue with no evidence of tumors, 
abnormal growths, or mass lesions. The brain structure appears healthy.

Note: This is an AI assessment and should be confirmed by qualified radiologists 
and medical professionals.
        ''',
        'symptoms': [
            'No concerning symptoms detected'
        ],
        'causes': [
            'N/A - Normal findings'
        ],
        'effects_on_health': [
            'No adverse health effects from brain tumor',
            'Continue regular health monitoring',
            'Maintain healthy lifestyle habits',
            'Regular check-ups as recommended by physician'
        ],
        'treatment_options': [
            'No treatment required for tumor',
            'Continue preventive healthcare'
        ],
        'prognosis': 'Excellent - No tumor detected. Normal brain imaging is a positive sign.',
        'urgency': 'NONE - Continue routine health care'
    },
    'pituitary_tumor': {
        'name': 'Pituitary Tumor',
        'severity': 'Medium-High',
        'color': '#8b5cf6',
        'short_description': 'A tumor in the pituitary gland affecting hormone production',
        'detailed_description': '''
Pituitary tumors are growths in the pituitary gland, the master endocrine gland that 
controls hormone production throughout the body. Most are benign adenomas, but they 
can cause significant hormonal and neurological effects.

Types:
- Prolactinoma (most common)
- Growth hormone-secreting
- ACTH-secreting (Cushing's disease)
- TSH-secreting
- Non-functioning adenomas
        ''',
        'symptoms': [
            'Hormonal imbalances',
            'Headaches',
            'Vision problems (bitemporal hemianopia)',
            'Sexual dysfunction',
            'Infertility',
            'Galactorrhea (abnormal milk secretion)',
            'Mood and behavioral changes',
            'Fatigue and weakness'
        ],
        'causes': [
            'Genetic mutations (rare)',
            'Sporadic development (most common)',
            'Pituitary adenoma familial syndrome',
            'Multiple endocrine neoplasia (MEN)'
        ],
        'effects_on_health': [
            'Hormonal dysregulation (prolactin, growth hormone, cortisol, TSH)',
            'Metabolic disorders',
            'Reproductive dysfunction',
            'Visual complications from mass effect',
            'Increased intracranial pressure',
            'Possible pituitary apoplexy if ruptured'
        ],
        'treatment_options': [
            'Medical management (dopamine agonists, somatostatin analogs)',
            'Surgical resection (transsphenoidal surgery)',
            'Radiation therapy',
            'Combination of above approaches',
            'Hormone replacement therapy'
        ],
        'prognosis': 'Generally favorable. Most pituitary adenomas are benign. Cure rates: 70-90% with transsphenoidal surgery. Recurrence rates: 10-20%.',
        'urgency': 'URGENT - Requires endocrinologist and neurosurgeon consultation'
    }
}

