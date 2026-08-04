"""
Brain Tumor Detection Flask Backend with Grad-CAM XAI
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Model
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO
import base64
import json
from datetime import datetime
from config import config, CLASS_DESCRIPTIONS
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
app.config.update(
    UPLOAD_FOLDER=config.UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH,
)

# Ensure upload folder exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# Global variables for model
model = None
class_names = None
last_conv_layer = config.LAST_CONV_LAYER

# ==================== UTILITY FUNCTIONS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def resize_with_padding(image, target_size=config.IMG_SIZE):
    """Resize image with padding to maintain aspect ratio"""
    h, w = image.shape[:2]
    target_h, target_w = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    return canvas

def preprocess_image(image):
    """Preprocess image: CLAHE enhancement"""
    gray = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    return enhanced.astype(np.float32)

def generate_gradcam(img_array, model, last_conv_layer_name):
    """Generate Grad-CAM heatmap for explainability"""
    grad_model = Model(
        inputs=model.input,
        outputs=[model.get_layer(last_conv_layer_name).output, model.output]
    )
    
    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(img_array)
        # Calculate loss for the predicted class
        # Use the maximum prediction across the batch
        loss = tf.reduce_max(preds)
    
    grads = tape.gradient(loss, conv_out)
    
    if grads is None:
        return np.zeros((300, 300))
    
    weights = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = tf.reduce_sum(conv_out[0] * weights, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    
    if tf.reduce_max(heatmap) > 0:
        heatmap /= tf.reduce_max(heatmap)
    
    return heatmap.numpy()

def heatmap_to_base64(heatmap, original_img):
    """Convert heatmap and overlay to base64 string"""
    hm_resized = cv2.resize(heatmap, (original_img.shape[1], original_img.shape[0]))
    jet_heatmap = (plt.cm.jet(hm_resized)[:, :, :3] * 255).astype(np.uint8)
    overlay = cv2.addWeighted(original_img, 0.6, jet_heatmap, 0.4, 0)
    
    # Convert to base64
    _, buffer = cv2.imencode('.png', cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

def generate_pdf_report(prediction_data, gradcam_base64, tumor_info):
    """Generate a comprehensive PDF report with prediction results and medical information"""
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    # Title
    story.append(Paragraph("Brain Tumor Detection Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Report Generated:</b> {timestamp}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # === PREDICTION SECTION ===
    story.append(Paragraph("1. PREDICTION RESULTS", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Prediction table
    pred_data = [
        ['Metric', 'Value'],
        ['Predicted Class', prediction_data['predicted_class'].replace('_', ' ').title()],
        ['Confidence Score', f"{prediction_data['confidence']}%"],
        ['Model', 'EfficientNetB3'],
        ['Explainability Method', 'Grad-CAM (Gradient-weighted Class Activation Mapping)']
    ]
    
    pred_table = Table(pred_data, colWidths=[2.5*inch, 3.5*inch])
    pred_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 0.2*inch))
    
    # All confidence scores
    story.append(Paragraph("<b>Detailed Confidence Scores:</b>", normal_style))
    scores_data = [['Class', 'Confidence']]
    for class_name, score in prediction_data['all_predictions'].items():
        scores_data.append([class_name.replace('_', ' ').title(), f"{score:.2f}%"])
    
    scores_table = Table(scores_data, colWidths=[3*inch, 3*inch])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 0.3*inch))
    
    # === GRAD-CAM VISUALIZATION ===
    story.append(Paragraph("2. GRAD-CAM VISUALIZATION", heading_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "The heatmap below shows which regions of the MRI image contributed most to the model's prediction. "
        "Warmer colors (red/yellow) indicate areas the model focused on.",
        normal_style
    ))
    story.append(Spacer(1, 0.15*inch))
    
    # Add Grad-CAM image
    try:
        # Convert base64 to image
        base64_data = gradcam_base64.replace('data:image/png;base64,', '')
        img_data = base64.b64decode(base64_data)
        img_buffer = BytesIO(img_data)
        img = Image(img_buffer, width=5*inch, height=4*inch)
        story.append(img)
    except:
        story.append(Paragraph("<i>Grad-CAM visualization could not be displayed</i>", normal_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # === TUMOR INFORMATION ===
    if tumor_info:
        story.append(PageBreak())
        story.append(Paragraph("3. TUMOR INFORMATION & HEALTH EFFECTS", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Tumor name and severity
        story.append(Paragraph(f"<b>Tumor Type:</b> {tumor_info.get('name', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Severity Level:</b> {tumor_info.get('severity', 'N/A')}", normal_style))
        story.append(Paragraph(f"<b>Urgency:</b> <font color=red>{tumor_info.get('urgency', 'N/A')}</font>", normal_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Description
        story.append(Paragraph("<b>Medical Description:</b>", normal_style))
        story.append(Paragraph(tumor_info.get('detailed_description', ''), normal_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Symptoms
        if tumor_info.get('symptoms'):
            story.append(Paragraph("<b>Common Symptoms:</b>", normal_style))
            for symptom in tumor_info.get('symptoms', []):
                story.append(Paragraph(f"• {symptom}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Causes
        if tumor_info.get('causes'):
            story.append(Paragraph("<b>Root Causes & Risk Factors:</b>", normal_style))
            for cause in tumor_info.get('causes', []):
                story.append(Paragraph(f"• {cause}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Health effects
        if tumor_info.get('effects_on_health'):
            story.append(Paragraph("<b>Effects on Human Health:</b>", normal_style))
            for effect in tumor_info.get('effects_on_health', []):
                story.append(Paragraph(f"• {effect}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Treatment options
        if tumor_info.get('treatment_options'):
            story.append(Paragraph("<b>Treatment Options:</b>", normal_style))
            for treatment in tumor_info.get('treatment_options', []):
                story.append(Paragraph(f"• {treatment}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Prognosis
        if tumor_info.get('prognosis'):
            story.append(Paragraph("<b>Prognosis:</b>", normal_style))
            story.append(Paragraph(tumor_info.get('prognosis', ''), normal_style))
            story.append(Spacer(1, 0.15*inch))
    
    # === INSTRUCTIONS & DISCLAIMER ===
    story.append(PageBreak())
    story.append(Paragraph("4. IMPORTANT INSTRUCTIONS & DISCLAIMER", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    instructions = [
        "<b>Medical Disclaimer:</b><br/>This AI-powered analysis is intended for informational purposes only and should NOT be used as a substitute for professional medical diagnosis or treatment. Always consult with a qualified healthcare professional before making any medical decisions.",
        "<br/><b>How to Use This Report:</b><br/>1. Review the prediction results and confidence scores<br/>2. Understand the model's focus areas using the Grad-CAM visualization<br/>3. Read the tumor information provided for medical context<br/>4. Discuss results with your healthcare provider<br/>5. Seek professional medical evaluation for confirmation",
        "<br/><b>Accuracy Notes:</b><br/>• The model was trained on EfficientNetB3 architecture<br/>• Accuracy depends on image quality and resolution<br/>• This tool should be used as a secondary screening aid<br/>• Professional radiologist review is essential for clinical decisions",
        "<br/><b>Important Reminders:</b><br/>• Early detection and treatment are crucial for tumor management<br/>• Seek immediate medical attention if experiencing severe symptoms<br/>• This report should be shared with healthcare professionals<br/>• Do not delay professional medical consultation based on this analysis"
    ]
    
    for instruction in instructions:
        story.append(Paragraph(instruction, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ==================== MODEL LOADING ====================

def load_model_and_classes():
    """Load the trained model and class names"""
    global model, class_names
    
    try:
        # Try loading the best model first
        model_path = config.MODEL_PATH
        if not os.path.exists(model_path):
            model_path = config.FALLBACK_MODEL_PATH
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found. Looking for {model_path}")
        
        print(f"Loading model from {model_path}...")
        model = tf.keras.models.load_model(model_path)
        print(f"✓ Model loaded successfully. Input shape: {model.input_shape}")
        
        # Use class names from config
        class_names = config.CLASS_NAMES
        print(f"✓ Class names loaded: {class_names}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading model: {str(e)}")
        return False

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get available tumor classes"""
    return jsonify({
        'classes': class_names,
        'count': len(class_names)
    })

@app.route('/api/tumor-info/<tumor_type>', methods=['GET'])
def get_tumor_info(tumor_type):
    """Get detailed information about a specific tumor type"""
    if tumor_type not in CLASS_DESCRIPTIONS:
        return jsonify({'error': 'Tumor type not found'}), 404
    
    info = CLASS_DESCRIPTIONS[tumor_type]
    return jsonify(info), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Predict tumor class and generate Grad-CAM explanation
    
    Expected: multipart/form-data with 'file' key
    Returns: JSON with prediction, confidence, and Grad-CAM visualization
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(config.ALLOWED_EXTENSIONS)}'}), 400
        
        # Read image from file
        in_memory_file = file.stream.read()
        data = np.frombuffer(in_memory_file, np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Could not read image file'}), 400
        
        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        original_shape = img_rgb.shape
        
        # Preprocess
        img_resized = resize_with_padding(img_rgb, config.IMG_SIZE)
        processed = preprocess_image(img_resized)
        img_batch = np.expand_dims(processed, axis=0)
        
        # Make prediction
        predictions = model.predict(img_batch, verbose=0)
        
        # Handle different tensor formats (for Keras 3.x compatibility)
        if isinstance(predictions, (list, tuple)):
            predictions = predictions[0] if len(predictions) > 0 else predictions
        
        # Convert to numpy array if it's a tensor
        if hasattr(predictions, 'numpy'):
            predictions = predictions.numpy()
        
        # Ensure predictions is a 1D array
        predictions = np.array(predictions)
        if predictions.ndim > 1:
            predictions = predictions[0]
        
        predicted_idx = int(np.argmax(predictions))
        predicted_class = class_names[predicted_idx]
        confidence = float(predictions[predicted_idx]) * 100
        
        # Generate Grad-CAM
        heatmap = generate_gradcam(img_batch, model, last_conv_layer)
        gradcam_img = heatmap_to_base64(heatmap, img_resized)
        
        # Get confidence scores for all classes
        confidence_scores = {
            class_names[i]: float(predictions[i]) * 100
            for i in range(len(class_names))
        }
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename)
        cv2.imwrite(filepath, img)
        
        return jsonify({
            'status': 'success',
            'predicted_class': predicted_class,
            'confidence': round(confidence, 2),
            'confidence_scores': {k: round(v, 2) for k, v in confidence_scores.items()},
            'gradcam': gradcam_img,
            'all_predictions': confidence_scores,
            'input_shape': list(original_shape),
            'timestamp': datetime.now().isoformat(),
            'uploaded_file': filepath
        }), 200
    
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/api/generate-pdf-report', methods=['POST'])
def generate_pdf_report_endpoint():
    """
    Generate a comprehensive PDF report with prediction results and medical information
    
    Expected JSON: {
        'predicted_class': 'glioma_tumor',
        'confidence': 95.5,
        'all_predictions': {...},
        'gradcam': 'data:image/png;base64,...'
    }
    Returns: PDF file download
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        predicted_class = data.get('predicted_class')
        confidence = data.get('confidence')
        all_predictions = data.get('all_predictions', {})
        gradcam_base64 = data.get('gradcam', '')
        
        if not predicted_class:
            return jsonify({'error': 'Missing predicted class'}), 400
        
        # Get tumor information
        tumor_info = CLASS_DESCRIPTIONS.get(predicted_class)
        
        # Prepare prediction data for PDF
        prediction_data = {
            'predicted_class': predicted_class,
            'confidence': round(confidence, 2) if confidence else 0,
            'all_predictions': all_predictions
        }
        
        # Generate PDF
        pdf_buffer = generate_pdf_report(prediction_data, gradcam_base64, tumor_info)
        
        # Return as file download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'brain_tumor_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    except Exception as e:
        print(f"Error generating PDF report: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """
    Batch prediction for multiple files
    
    Expected: multipart/form-data with multiple 'files' keys
    Returns: JSON array with predictions for each file
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        results = []
        
        for file in files:
            if not allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'File type not allowed'
                })
                continue
            
            try:
                # Read and process image
                in_memory_file = file.stream.read()
                data = np.frombuffer(in_memory_file, np.uint8)
                img = cv2.imdecode(data, cv2.IMREAD_COLOR)
                
                if img is None:
                    results.append({
                        'filename': file.filename,
                        'status': 'error',
                        'message': 'Could not read image'
                    })
                    continue
                
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_resized = resize_with_padding(img_rgb, IMG_SIZE)
                processed = preprocess_image(img_resized)
                img_batch = np.expand_dims(processed, axis=0)
                
                # Predict
                predictions = model.predict(img_batch, verbose=0)
                predicted_idx = np.argmax(predictions[0])
                
                results.append({
                    'filename': file.filename,
                    'status': 'success',
                    'predicted_class': class_names[predicted_idx],
                    'confidence': round(float(predictions[0][predicted_idx]) * 100, 2)
                })
            
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'total_files': len(files),
            'successful': len([r for r in results if r['status'] == 'success']),
            'results': results
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Batch prediction failed: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================

# Load the model when the module is imported.
# This is required for deployments using Gunicorn / WSGI,
# because the __main__ block is not executed.
if not load_model_and_classes():
    print("\n✗ Failed to load model during import. Please check that the model files are present and accessible.")
    print("Expected: efficientnetb3_best.keras or efficientnetb3_final.keras")


if __name__ == '__main__':
    print("=" * 60)
    print("Brain Tumor Detection with Grad-CAM XAI")
    print("=" * 60)
    
    if model is not None:
        print("\n✓ Starting Flask server...")
        print("=" * 60 + "\n")

        # Render requires dynamic port
        port = int(os.environ.get("PORT", 5000))

        app.run(host="0.0.0.0", port=port)
    else:
        print("\n✗ Model failed to load. Please check model files.")
        print("Expected: efficientnetb3_best.keras or efficientnetb3_final.keras")