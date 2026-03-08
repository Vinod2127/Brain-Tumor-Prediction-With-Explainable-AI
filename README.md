# 🧠 Brain Tumor Detection System with Grad-CAM XAI

A web-based application for detecting brain tumors from MRI images using **EfficientNetB3** deep learning model with **Explainable AI (Grad-CAM)** visualization.

## 🌟 Features

- ✅ **Brain Tumor Detection**: Classifies MRI images into 4 categories:
  - Glioma Tumor
  - Meningioma Tumor
  - No Tumor
  - Pituitary Tumor

- 🔍 **Explainable AI (XAI)**: Grad-CAM visualization showing which regions the model focused on during prediction

- 📊 **Confidence Scores**: Displays prediction confidence for all tumor classes

- 🎨 **Modern UI**: Clean, responsive web interface with real-time predictions

- ⚡ **Fast Processing**: GPU-optimized inference with TensorFlow

- 📈 **Batch Processing**: API endpoint for analyzing multiple images

- 📥 **Report Generation**: Download analysis results as JSON

## 📋 System Requirements

- **Python**: 3.9 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended)

## 🚀 Installation

### 1. Clone/Navigate to Project Directory

```bash
cd brain_tumor_detection
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you have GPU support and want to use it:
```bash
pip install tensorflow[and-cuda]==2.14.0
```

### 4. Verify Model Files

Ensure the following files are in the project root directory:
- `efficientnetb3_best.keras` (preferred)
- `efficientnetb3_final.keras` (fallback)

If not, copy them from your model training location:
```bash
# From capsstone root directory
copy efficientnetb3_best.keras brain_tumor_detection/
copy efficientnetb3_final.keras brain_tumor_detection/
```

## 🏃 Running the Application

### 1. Navigate to Project Directory

```bash
cd brain_tumor_detection
```

### 2. Activate Virtual Environment

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Start Flask Server

```bash
python app.py
```

You should see:
```
============================================================
Brain Tumor Detection with Grad-CAM XAI
============================================================

✓ Model loaded successfully. Input shape: (None, 300, 300, 3)
✓ Class names loaded: ['glioma_tumor', 'meningioma_tumor', 'no_tumor', 'pituitary_tumor']

✓ Starting Flask server...
  Server: http://localhost:5000
  API Docs: http://localhost:5000/api/health
============================================================
```

### 4. Open Web Interface

Open your browser and go to:
```
http://localhost:5000
```

## 📖 API Documentation

### Health Check
```
GET /api/health
```
Returns server status and model load status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-13T10:30:00"
}
```

### Get Available Classes
```
GET /api/classes
```
Returns list of tumor classifications.

**Response:**
```json
{
  "classes": ["glioma_tumor", "meningioma_tumor", "no_tumor", "pituitary_tumor"],
  "count": 4
}
```

### Single Image Prediction
```
POST /api/predict
Content-Type: multipart/form-data

file: <image file>
```

**Response:**
```json
{
  "status": "success",
  "predicted_class": "glioma_tumor",
  "confidence": 95.42,
  "confidence_scores": {
    "glioma_tumor": 95.42,
    "meningioma_tumor": 3.21,
    "no_tumor": 1.12,
    "pituitary_tumor": 0.25
  },
  "gradcam": "data:image/png;base64,...",
  "all_predictions": {...},
  "input_shape": [512, 512, 3],
  "timestamp": "2024-01-13T10:30:00",
  "uploaded_file": "uploads/20240113_103000_brain_mri.jpg"
}
```

### Batch Prediction
```
POST /api/batch-predict
Content-Type: multipart/form-data

files: <image file 1>
files: <image file 2>
...
```

**Response:**
```json
{
  "status": "success",
  "total_files": 3,
  "successful": 3,
  "results": [
    {
      "filename": "image1.jpg",
      "status": "success",
      "predicted_class": "glioma_tumor",
      "confidence": 95.42
    },
    {...}
  ]
}
```

## 🎯 Usage Guide

### 1. Upload MRI Image

Click on the upload area or drag-and-drop an MRI image in **JPG**, **PNG**, **BMP**, or **GIF** format.

### 2. Analyze Image

Click the **"Analyze Image"** button to run prediction.

### 3. View Results

- **Predicted Class**: The detected tumor type with a color-coded badge
- **Confidence Score**: Percentage confidence of the prediction
- **Detailed Scores**: Confidence levels for all 4 tumor classes
- **Grad-CAM Visualization**: Heatmap showing which regions influenced the prediction

### 4. Download Report

Click **"Download Report"** to save analysis results as JSON file.

## 🧠 Understanding Grad-CAM

**Grad-CAM (Gradient-weighted Class Activation Map)** is an explainability technique that:

1. **Identifies Important Regions**: Shows which parts of the MRI image the model focused on
2. **Generates Heatmaps**: Warmer colors (red/yellow) indicate important areas
3. **Builds Trust**: Helps medical professionals understand the model's reasoning
4. **Improves Diagnosis**: Highlights tumor locations for further review

### Interpretation:
- 🔴 **Red/Yellow Areas**: Strong activation - high model attention
- 🟢 **Green/Blue Areas**: Weak activation - low model attention
- ⚪ **White Overlay**: Original MRI image for reference

## 📁 Project Structure

```
brain_tumor_detection/
├── app.py                          # Flask backend application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── efficientnetb3_best.keras       # Trained model (best weights)
├── efficientnetb3_final.keras      # Trained model (final weights)
├── uploads/                        # Uploaded images storage
├── static/
│   ├── css/
│   │   └── style.css              # Frontend styling
│   └── js/
│       └── script.js              # Frontend interactivity
└── templates/
    └── index.html                 # Web interface
```

## 🔧 Configuration

### Model Settings

Edit `app.py` to customize:

```python
IMG_SIZE = (300, 300)              # Input image size
ALLOWED_EXTENSIONS = {...}        # Accepted file types
MAX_FILE_SIZE = 16 * 1024 * 1024   # Max upload size
last_conv_layer = 'top_conv'       # Layer for Grad-CAM
```

### Flask Settings

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Change `debug=False` for production use.

## 🐛 Troubleshooting

### Issue: Model Not Loading
**Solution**: Ensure model files (.keras) are in the project root directory.

```bash
ls *.keras  # List .keras files
```

### Issue: GPU Not Detected
**Solution**: Install GPU-enabled TensorFlow with CUDA:

```bash
pip install tensorflow[and-cuda]==2.14.0
```

Verify GPU availability:
```python
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### Issue: Port Already in Use
**Solution**: Change port in `app.py`:

```python
app.run(port=5001)  # Use different port
```

### Issue: File Upload Too Slow
**Solution**: Reduce image resolution before uploading or increase `MAX_FILE_SIZE`.

## 📊 Model Information

- **Architecture**: EfficientNetB3
- **Pre-trained on**: ImageNet
- **Fine-tuning**: Brain Tumor MRI Dataset
- **Input Size**: 300×300×3 (RGB)
- **Output Classes**: 4 (Glioma, Meningioma, No Tumor, Pituitary)
- **Preprocessing**: CLAHE enhancement, padding-based resizing
- **Explainability**: Grad-CAM visualization

## ⚠️ Medical Disclaimer

**Important**: This application is for **educational and research purposes only**. It is not a medical device and should not be used for clinical diagnosis.

- ❌ Not FDA-approved
- ❌ Not intended for patient diagnosis
- ✅ Consult qualified medical professionals for actual diagnosis
- ✅ Use only under medical supervision

## 🤝 Contributing

To improve this project:

1. Report bugs or request features via GitHub issues
2. Improve model accuracy with additional training
3. Enhance UI/UX with additional features
4. Optimize performance for production deployment

## 📄 License

This project is provided for educational purposes.

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review error messages in the console
3. Verify all dependencies are installed correctly
4. Check API endpoints are responding

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] 3D visualization of brain tumors
- [ ] Integration with DICOM file format
- [ ] Cloud deployment (AWS, Google Cloud)
- [ ] Mobile app version
- [ ] Real-time streaming analysis
- [ ] Advanced statistics and reporting
- [ ] User authentication and history tracking

## 📚 References

- **EfficientNetB3**: https://arxiv.org/abs/1905.11946
- **Grad-CAM**: https://arxiv.org/abs/1610.02055
- **Brain Tumor Dataset**: https://www.kaggle.com/masoudnickparvar/brain-tumor-mri-dataset

---

**Created**: January 2024  
**Version**: 1.0.0  
**Status**: Ready for Production (with disclaimers)

🧠 **Making Medical AI More Explainable and Transparent** 🧠
