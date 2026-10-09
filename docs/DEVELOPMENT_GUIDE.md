# Customer Feedback Sentiment Analysis - Development Guide

## 🛠️ Development Environment Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- AWS CLI configured
- Git installed
- IDE (VS Code recommended)

### Local Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd cloudComputingDiscussion1

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend-new
npm install
npm run dev
```

## 🏗️ Architecture Overview

### System Components
1. **Frontend**: Nuxt 4 + @nuxt/ui + Chart.js
2. **API Gateway**: REST API endpoints
3. **Lambda Functions**: Serverless compute
4. **DynamoDB**: NoSQL database
5. **S3**: File storage
6. **SNS**: Notifications
7. **CloudWatch**: Monitoring

### Data Flow
```
Frontend → API Gateway → Lambda → DynamoDB
    ↓
S3 Upload → Lambda Trigger → Sentiment Analysis → SNS Notification
```

## 🔧 Backend Development

### Lambda Functions

#### 1. Sentiment Processor (`sentiment-processor`)
**Purpose**: Processes uploaded files and performs sentiment analysis

**Key Features**:
- File parsing (CSV, JSON, TXT)
- Rule-based sentiment analysis
- DynamoDB storage
- SNS notifications

**Code Structure**:
```python
def lambda_handler(event, context):
    """
    Main handler for S3 file processing
    """
    # Parse S3 event
    # Download and parse file
    # Analyze sentiment
    # Store results
    # Send notifications
```

**Sentiment Analysis Algorithm**:
```python
def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis (free alternative to AWS Comprehend)"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate']
    
    # Count positive and negative words
    positive_count = sum(1 for word in positive_words if word in text.lower())
    negative_count = sum(1 for word in negative_words if word in text.lower())
    
    # Determine sentiment and confidence
    if positive_count > negative_count:
        sentiment = 'POSITIVE'
        confidence = min(0.95, 0.5 + (positive_count - negative_count) * 0.1)
    elif negative_count > positive_count:
        sentiment = 'NEGATIVE'
        confidence = min(0.95, 0.5 + (negative_count - positive_count) * 0.1)
    else:
        sentiment = 'NEUTRAL'
        confidence = 0.5
    
    return {
        'sentiment': sentiment,
        'confidence': confidence
    }
```

#### 2. API Handler (`sentiment-api-handler`)
**Purpose**: Handles API requests and data retrieval

**Endpoints**:
- `GET /sentiment/results` - Retrieve analysis results
- `GET /sentiment/summary` - Get summary statistics
- `GET /sentiment/files` - List processed files
- `GET /sentiment/results/{id}` - Get specific result
- `POST /sentiment/feedback` - Submit single feedback

**Code Structure**:
```python
def lambda_handler(event, context):
    """
    Main handler for API Gateway requests
    """
    http_method = event['httpMethod']
    path = event['path']
    
    if http_method == 'GET':
        if path == '/sentiment/results':
            return get_results(event)
        elif path == '/sentiment/summary':
            return get_summary(event)
    elif http_method == 'POST':
        if path == '/sentiment/feedback':
            return submit_feedback(event)
```

#### 3. Alert Handler (`sentiment-alert-handler`)
**Purpose**: Manages alerts and notifications

**Features**:
- Negative sentiment alerts
- Email notifications via SNS
- Alert storage in DynamoDB

### Database Schema

#### DynamoDB Tables

**sentiment-analysis-results**:
```json
{
  "id": "UUID",
  "feedback_text": "string",
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL|MIXED",
  "confidence": "number",
  "timestamp": "ISO string",
  "source": "string",
  "metadata": {
    "customer_name": "string",
    "customer_email": "string",
    "rating": "number"
  }
}
```

**sentiment-alerts**:
```json
{
  "id": "string",
  "alert_type": "negative_sentiment",
  "message": "string",
  "details": "object",
  "timestamp": "ISO string",
  "status": "active|resolved"
}
```

## 🎨 Frontend Development

### Technology Stack
- **Framework**: Nuxt 4
- **UI Library**: @nuxt/ui
- **Styling**: Tailwind CSS
- **Charts**: Chart.js
- **State Management**: Pinia
- **Icons**: Heroicons

### Project Structure
```
frontend-new/
├── app/
│   ├── pages/
│   │   ├── index.vue          # Home page
│   │   └── results.vue        # Results page
│   ├── components/
│   │   └── SentimentChart.vue # Chart component
│   ├── stores/
│   │   └── sentiment.js       # Pinia store
│   └── app.vue               # Root component
├── assets/
│   └── css/
│       └── main.css          # Global styles
├── nuxt.config.ts            # Nuxt configuration
└── package.json              # Dependencies
```

### Key Components

#### 1. Home Page (`app/pages/index.vue`)
**Features**:
- File upload interface
- Individual feedback submission
- Rating input (1-5)
- Customer information fields

**Code Structure**:
```vue
<template>
  <div class="container mx-auto px-4 py-8 space-y-8">
    <!-- File Upload Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Upload Feedback Files</h2>
      </template>
      <!-- Upload interface -->
    </UCard>

    <!-- Individual Feedback Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Submit Individual Feedback</h2>
      </template>
      <!-- Feedback form -->
    </UCard>
  </div>
</template>
```

#### 2. Results Page (`app/pages/results.vue`)
**Features**:
- Sentiment distribution chart
- Summary statistics
- Filtering and search
- Pagination
- Export functionality

**Code Structure**:
```vue
<template>
  <div class="container mx-auto px-4 py-8 space-y-6">
    <!-- Filters -->
    <UCard>
      <!-- Filter controls -->
    </UCard>

    <!-- Summary + Chart -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <UCard>
        <SentimentChart :data="chartData" />
      </UCard>
      <UCard>
        <!-- Summary statistics -->
      </UCard>
    </div>

    <!-- Results -->
    <UCard>
      <!-- Results list with pagination -->
    </UCard>
  </div>
</template>
```

#### 3. Sentiment Chart (`app/components/SentimentChart.vue`)
**Features**:
- Bar chart visualization
- Responsive design
- Dark/light mode support

**Code Structure**:
```vue
<template>
  <div class="w-full h-64">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

const chartCanvas = ref(null)
let chart = null

onMounted(() => {
  createChart()
})

watch(() => props.data, () => {
  if (chart) {
    updateChart()
  }
})
</script>
```

### State Management (Pinia Store)

#### Sentiment Store (`app/stores/sentiment.js`)
```javascript
export const useSentimentStore = defineStore('sentiment', {
  state: () => ({
    results: [],
    summary: {},
    isLoading: false
  }),

  actions: {
    async fetchResults() {
      this.isLoading = true
      try {
        const response = await $fetch('/api/sentiment/results')
        this.results = response.results
      } finally {
        this.isLoading = false
      }
    },

    async submitTextFeedback(payload) {
      // Submit individual feedback
    },

    async uploadFile(file) {
      // Upload file for processing
    }
  }
})
```

## 🧪 Testing

### Backend Testing

#### 1. Lambda Function Testing
```bash
# Test sentiment processor
aws lambda invoke \
  --function-name sentiment-processor-dev \
  --payload file://test-payloads/processor-test.json \
  response.json

# Test API handler
aws lambda invoke \
  --function-name sentiment-api-handler-dev \
  --payload file://test-payloads/api-test.json \
  response.json

# Test alert handler
aws lambda invoke \
  --function-name sentiment-alert-handler-dev \
  --payload file://test-payloads/alert-test.json \
  response.json
```

#### 2. Automated Testing Script
```bash
#!/bin/bash
# test-lambda-functions.sh

echo "Testing Lambda Functions..."

# Test all functions
for func in sentiment-processor sentiment-api-handler sentiment-alert-handler; do
  echo "Testing $func..."
  aws lambda invoke \
    --function-name ${func}-dev \
    --payload file://test-payloads/${func}-test.json \
    test-results/${func}-response.json
  
  if [ $? -eq 0 ]; then
    echo "✅ $func test passed"
  else
    echo "❌ $func test failed"
  fi
done
```

#### 3. Test Payloads
**Processor Test** (`test-payloads/processor-test.json`):
```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "customer-feedback-sentiment-analysis-dev-123456789012"
        },
        "object": {
          "key": "test-feedback.csv"
        }
      }
    }
  ]
}
```

**API Test** (`test-payloads/api-test.json`):
```json
{
  "httpMethod": "GET",
  "path": "/sentiment/results",
  "queryStringParameters": null
}
```

### Frontend Testing

#### 1. Unit Testing
```bash
# Run frontend tests
cd frontend-new
npm run test
```

#### 2. E2E Testing
```bash
# Run end-to-end tests
npm run test:e2e
```

#### 3. Manual Testing Checklist
- [ ] File upload functionality
- [ ] Individual feedback submission
- [ ] Results display and filtering
- [ ] Chart rendering
- [ ] Export functionality
- [ ] Responsive design
- [ ] Dark/light mode toggle

## 🐛 Debugging

### Common Issues

#### 1. Lambda Function Errors
**Symptoms**: Function timeout or permission errors
**Solutions**:
```bash
# Check CloudWatch logs
aws logs get-log-events \
  --log-group-name /aws/lambda/sentiment-processor-dev \
  --start-time $(date -d '1 hour ago' +%s)000

# Update function configuration
aws lambda update-function-configuration \
  --function-name sentiment-processor-dev \
  --timeout 300 \
  --memory-size 1024
```

#### 2. API Gateway CORS Issues
**Symptoms**: Frontend can't access API
**Solutions**:
```bash
# Check CORS configuration
aws apigateway get-method \
  --rest-api-id YOUR-API-ID \
  --resource-id YOUR-RESOURCE-ID \
  --http-method OPTIONS
```

#### 3. DynamoDB Access Issues
**Symptoms**: Permission denied errors
**Solutions**:
```bash
# Check IAM role permissions
aws iam get-role --role-name LambdaExecutionRole

# Update role policies
aws iam attach-role-policy \
  --role-name LambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

#### 4. Frontend Build Issues
**Symptoms**: Build failures or runtime errors
**Solutions**:
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check

# Verify Nuxt configuration
npm run dev
```

### Debugging Tools

#### 1. CloudWatch Logs
```bash
# Stream logs in real-time
aws logs tail /aws/lambda/sentiment-processor-dev --follow
```

#### 2. AWS X-Ray (Optional)
```bash
# Enable X-Ray tracing
aws lambda update-function-configuration \
  --function-name sentiment-processor-dev \
  --tracing-config Mode=Active
```

#### 3. Browser DevTools
- Network tab for API calls
- Console for JavaScript errors
- Vue DevTools for component state

## 📊 Performance Optimization

### Backend Optimization

#### 1. Lambda Function Optimization
```python
# Use connection pooling for DynamoDB
import boto3
from botocore.config import Config

# Configure DynamoDB client
dynamodb = boto3.resource('dynamodb', config=Config(
    retries={'max_attempts': 3},
    max_pool_connections=50
))

# Use batch operations for multiple items
def batch_write_items(items):
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
```

#### 2. Memory and Timeout Optimization
```bash
# Optimize function settings
aws lambda update-function-configuration \
  --function-name sentiment-processor-dev \
  --memory-size 1024 \
  --timeout 300
```

### Frontend Optimization

#### 1. Bundle Size Optimization
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  build: {
    analyze: true, // Analyze bundle size
    extractCSS: true // Extract CSS for better caching
  },
  
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'nuxt'],
            charts: ['chart.js']
          }
        }
      }
    }
  }
})
```

#### 2. Image and Asset Optimization
```typescript
// Use Nuxt Image for optimized images
<NuxtImg 
  src="/images/chart-icon.png" 
  alt="Chart" 
  width="64" 
  height="64"
  loading="lazy"
/>
```

## 🔒 Security Best Practices

### Backend Security

#### 1. IAM Least Privilege
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/sentiment-analysis-results-*"
    }
  ]
}
```

#### 2. Input Validation
```python
import json
from jsonschema import validate, ValidationError

def validate_feedback_data(data):
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1, "maxLength": 1000},
            "rating": {"type": "integer", "minimum": 1, "maximum": 5}
        },
        "required": ["text"]
    }
    
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError:
        return False
```

### Frontend Security

#### 1. Input Sanitization
```javascript
// Sanitize user input
function sanitizeInput(input) {
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .trim()
}
```

#### 2. Environment Variables
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'https://api.example.com'
    },
    // Server-only variables
    secretKey: process.env.SECRET_KEY
  }
})
```

## 📈 Monitoring and Logging

### CloudWatch Monitoring

#### 1. Custom Metrics
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='SentimentAnalysis',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

#### 2. Alarms and Notifications
```bash
# Create CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "HighErrorRate" \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### Application Logging

#### 1. Structured Logging
```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(event_type, data):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data
    }
    logger.info(json.dumps(log_entry))
```

#### 2. Error Tracking
```python
def handle_error(error, context):
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.utcnow().isoformat()
    }
    logger.error(json.dumps(error_data))
```

## 🚀 Deployment

### Development Deployment
```bash
# Deploy to development
sam deploy --config-env dev

# Deploy frontend
cd frontend-new
npm run build
aws s3 sync .output/public/ s3://dev-frontend-bucket --delete
```

### Production Deployment
```bash
# Deploy to production
sam deploy --config-env prod

# Deploy frontend with cache invalidation
cd frontend-new
npm run build
aws s3 sync .output/public/ s3://prod-frontend-bucket --delete
aws cloudfront create-invalidation --distribution-id PROD_DISTRIBUTION_ID --paths "/*"
```

## 📚 Resources and Documentation

### AWS Documentation
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [S3 User Guide](https://docs.aws.amazon.com/s3/)

### Nuxt Documentation
- [Nuxt 4 Documentation](https://nuxt.com/docs)
- [Nuxt UI Documentation](https://ui.nuxt.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)

### Chart.js Documentation
- [Chart.js Documentation](https://www.chartjs.org/docs/)

---

This development guide provides comprehensive information for developing, testing, debugging, and maintaining the Customer Feedback Sentiment Analysis system. Keep this guide updated as the system evolves.
