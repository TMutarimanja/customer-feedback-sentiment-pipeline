# Customer Feedback Sentiment Analysis System - Implementation Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Implementation Steps](#implementation-steps)
5. [Code Configurations](#code-configurations)
6. [Deployment Guide](#deployment-guide)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### Project Goals
- Build a **serverless sentiment analysis system** using AWS services
- Process customer feedback files (CSV, JSON, TXT) automatically
- Provide real-time sentiment insights through an interactive dashboard
- Stay within **AWS Free Tier** limits ($0/month)
- Implement using **Infrastructure as Code** (CloudFormation)

### Key Technologies
- **Backend**: AWS Lambda (Python 3.12)
- **Frontend**: Nuxt 4 + Vue.js 3 + Chart.js
- **Database**: AWS DynamoDB
- **Storage**: AWS S3
- **Messaging**: AWS SNS
- **Monitoring**: AWS CloudWatch
- **API**: AWS API Gateway

### Cost Optimization
| Service | Limit | Usage |
|---------|-------|-------|
| Lambda | 1M requests/month | ✅ Within free tier |
| S3 | 5GB storage | ✅ Within free tier |
| DynamoDB | 25GB storage | ✅ Within free tier |
| API Gateway | 1M calls/month | ✅ Within free tier |
| CloudFront | 1TB transfer | ✅ Within free tier |

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Nuxt 4 + Vue.js 3 + Chart.js                          │   │
│  │  - File Upload Interface                                │   │
│  │  - Real-time Dashboard                                  │   │
│  │  - Sentiment Visualization                              │   │
│  │  - Responsive Design (Mobile/Desktop)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API & Integration Layer                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Gateway (REST)                                     │   │
│  │  - GET /sentiment/results                               │   │
│  │  - GET /sentiment/summary                               │   │
│  │  - POST /sentiment/feedback                             │   │
│  │  - POST /sentiment/bulk                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Processing Layer                            │
│  ┌────────────────────────┐  ┌────────────────────────────────┐ │
│  │  Sentiment Processor   │  │  API Handler Lambda            │ │
│  │  - File Parsing        │  │  - Query Processing           │ │
│  │  - Sentiment Analysis  │  │  - Result Formatting          │ │
│  │  - Data Storage        │  │  - Text Feedback Handling     │ │
│  │  - Alert Triggering    │  │  - File Upload Processing     │ │
│  └────────────────────────┘  └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                    │                          │
          ┌─────────┴─────────┐     ┌────────────────────────┐
          ▼                   ▼     ▼                         ▼
    ┌──────────┐      ┌────────────┐              ┌──────────────┐
    │   S3     │      │ DynamoDB   │              │     SNS      │
    │  Bucket  │      │  Tables    │              │  Alerts      │
    └──────────┘      └────────────┘              └──────────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  CloudWatch    │
                    │  Logs & Metrics│
                    └────────────────┘
```

### Data Flow

#### File Upload Flow:
```
User Upload
    ↓
S3 Bucket
    ↓
Lambda Trigger (SentimentProcessor)
    ↓
Parse File (CSV/JSON/TXT)
    ↓
Sentiment Analysis
    ↓
Store in DynamoDB
    ↓
Send SNS Notification
    ↓
Update Frontend Dashboard
```

#### API Query Flow:
```
Frontend Request
    ↓
API Gateway
    ↓
Lambda (ApiHandler)
    ↓
Query DynamoDB
    ↓
Format Response
    ↓
Return JSON
    ↓
Frontend Updates Chart/Table
```

---

## 📋 Prerequisites

### AWS Account
- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- IAM User with permissions for:
  - Lambda, DynamoDB, S3, API Gateway, SNS, CloudFormation

### Local Development Environment
```bash
# Required software
- Python 3.9+
- Node.js 18+
- npm or yarn
- Git
- AWS CLI v2
```

### Installation Commands
```bash
# macOS (using Homebrew)
brew install python node git awscli

# Linux (Ubuntu/Debian)
sudo apt install python3 python3-pip nodejs npm git awscli

# Verify installations
python3 --version
node --version
npm --version
aws --version
```

---

## 🚀 Implementation Steps

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd cloudComputingDiscussion1
```

### Step 2: Configure AWS CLI
```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 3: Set Up Backend Environment
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Deploy Infrastructure (CloudFormation)
```bash
# Navigate to CloudFormation directory
cd backend/infrastructure/cloudformation

# Validate CloudFormation template
aws cloudformation validate-template \
  --template-body file://sentiment-analysis-stack.yaml

# Create CloudFormation stack
aws cloudformation create-stack \
  --stack-name sentiment-analysis-stack-dev \
  --template-body file://sentiment-analysis-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=S3BucketName,ParameterValue=customer-feedback-sentiment-analysis \
    ParameterKey=NotificationEmail,ParameterValue=your-email@example.com \
    ParameterKey=NegativeSentimentThreshold,ParameterValue=0.3 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for stack creation (typically 2-5 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name sentiment-analysis-stack-dev \
  --region us-east-1

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name sentiment-analysis-stack-dev \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

### Step 5: Deploy Backend Lambda Functions
```bash
# The Lambda functions are deployed automatically via CloudFormation
# But you can update them if needed:

# Update Sentiment Processor function
aws lambda update-function-code \
  --function-name sentiment-processor-dev \
  --zip-file fileb://lambda/sentiment-processor/lambda_function.zip

# Update API Handler function
aws lambda update-function-code \
  --function-name sentiment-api-handler-dev \
  --zip-file fileb://lambda/api-handler/lambda_function.zip

# Create function packages (if needed)
cd ../../lambda/sentiment-processor
zip -r ../../../sentiment-processor.zip .
cd ../api-handler
zip -r ../../../api-handler.zip .
```

### Step 6: Set Up Frontend
```bash
# Navigate to frontend directory
cd frontend-new

# Install dependencies
npm install

# Create environment file
cat > .env.local << EOF
API_BASE_URL=https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev
S3_BUCKET_NAME=customer-feedback-sentiment-analysis-dev-123456789012
EOF

# Run development server
npm run dev

# Build for production
npm run build

# Deploy to S3
aws s3 sync .output/public/ s3://YOUR-FRONTEND-BUCKET --delete

# Invalidate CloudFront cache (if using CloudFront)
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"
```

### Step 7: Configure SNS Notifications
```bash
# Get SNS topic ARN from stack outputs
TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name sentiment-analysis-stack-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`NotificationTopicArn`].OutputValue' \
  --output text)

# Verify subscription
aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN

# Check your email for subscription confirmation
# (Click the link in the email)
```

---

## 💻 Code Configurations

### 1. Backend Requirements (`backend/requirements.txt`)
```
# AWS SDK
boto3==1.34.0
botocore==1.34.0

# Data processing
pandas==2.1.4
numpy==1.24.3

# File handling
openpyxl==3.1.2
python-magic==0.4.27

# Testing
pytest==7.4.3
pytest-cov==4.1.0
factory-boy==3.3.0
moto==4.2.14

# Development
black==23.11.0
flake8==6.1.0
mypy==1.7.1

# Utilities
python-dotenv==1.0.0
requests==2.31.0
pytz==2023.3
```

### 2. Frontend Configuration (`frontend-new/nuxt.config.ts`)
```typescript
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/content',
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/test-utils',
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt'
  ],

  runtimeConfig: {
    public: {
      // Update these with your actual API Gateway URL and S3 bucket
      apiBaseUrl: process.env.API_BASE_URL || 
        'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev',
      s3BucketName: process.env.S3_BUCKET_NAME || 
        'customer-feedback-sentiment-analysis-clean-dev-123456789012'
    }
  },

  vite: {
    plugins: [tailwindcss()]
  },
  css: ['~/assets/css/main.css'],

  ssr: false,  // Disable SSR for static site deployment
  nitro: {
    preset: 'static'  // Build as static site
  }
})
```

### 3. CloudFormation Template Structure (`backend/infrastructure/cloudformation/sentiment-analysis-stack.yaml`)
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
  
  S3BucketName:
    Type: String
    Default: customer-feedback-sentiment-analysis
  
  NotificationEmail:
    Type: String
    Default: your-email@example.com
  
  NegativeSentimentThreshold:
    Type: Number
    Default: 0.3
    MinValue: 0.0
    MaxValue: 1.0

Globals:
  Function:
    Timeout: 300
    Runtime: python3.12
    Environment:
      Variables:
        ENVIRONMENT: !Ref Environment
        DYNAMODB_TABLE: !Ref SentimentAnalysisTable
        S3_BUCKET: !Ref CustomerFeedbackBucket
        SNS_TOPIC_ARN: !Ref NotificationTopic

Resources:
  # S3 Bucket
  CustomerFeedbackBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${S3BucketName}-${Environment}-${AWS::AccountId}"
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  # DynamoDB Table
  SentimentAnalysisTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "sentiment-analysis-results-${Environment}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH

  # SNS Topic
  NotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub "sentiment-analysis-notifications-${Environment}"

  # Lambda Functions
  SentimentProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "sentiment-processor-${Environment}"
      CodeUri: ../../lambda/sentiment-processor/
      Handler: lambda_function.lambda_handler
      MemorySize: 512
      Policies:
        - S3ReadPolicy:
            BucketName: !Ref CustomerFeedbackBucket
        - DynamoDBCrudPolicy:
            TableName: !Ref SentimentAnalysisTable
        - SNSPublishMessagePolicy:
            TopicName: !GetAtt NotificationTopic.TopicName
```

### 4. Sentiment Analysis Algorithm (`backend/lambda/sentiment-processor/lambda_function.py`)

Key function for sentiment analysis:
```python
def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis (free alternative to AWS Comprehend)"""
    
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
        'love', 'like', 'best', 'perfect', 'outstanding', 'brilliant', 'superb',
        'delighted', 'pleased', 'satisfied', 'happy', 'impressed', 'recommend',
        'helpful', 'easy', 'fast', 'quick', 'reliable', 'professional', 'friendly'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike',
        'disappointed', 'frustrated', 'angry', 'annoyed', 'upset', 'poor',
        'slow', 'broken', 'crashed', 'failed', 'error', 'problem', 'issue',
        'difficult', 'hard', 'confusing', 'complicated', 'unreliable', 'unhelpful'
    ]
    
    text_lower = text.lower()
    
    # Count positive and negative words
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
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
        'confidence': confidence,
        'positive_count': positive_count,
        'negative_count': negative_count
    }
```

### 5. File Parsing Functions
```python
def parse_csv_content(file_content: str) -> List[Dict[str, Any]]:
    """Parse CSV content and extract feedback"""
    feedback_data = []
    csv_reader = csv.DictReader(io.StringIO(file_content))
    
    for row in csv_reader:
        # Look for common feedback column names
        text_column = None
        for col in ['feedback', 'text', 'comment', 'review', 'message']:
            if col in row:
                text_column = col
                break
        
        if text_column and row[text_column].strip():
            feedback_data.append({
                'text': row[text_column].strip(),
                'metadata': {k: v for k, v in row.items() if k != text_column}
            })
    
    return feedback_data

def parse_json_content(file_content: str) -> List[Dict[str, Any]]:
    """Parse JSON content and extract feedback"""
    data = json.loads(file_content)
    feedback_data = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for field in ['feedback', 'text', 'comment', 'review']:
                    if field in item and item[field].strip():
                        feedback_data.append({
                            'text': item[field].strip(),
                            'metadata': {k: v for k, v in item.items() if k != field}
                        })
                        break
    
    return feedback_data
```

### 6. API Endpoints (`backend/lambda/api-handler/lambda_function.py`)

**GET /sentiment/results** - Retrieve analysis results
```python
def get_sentiment_results(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """Get sentiment analysis results with optional filtering"""
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    # Build filter expression
    filter_expression = None
    
    # Filter by sentiment
    if 'sentiment' in query_parameters:
        filter_expression = "sentiment = :sentiment"
    
    # Filter by date range
    if 'start_date' in query_parameters:
        filter_expression = "timestamp >= :start_date"
    
    # Query DynamoDB
    response = table.scan(FilterExpression=filter_expression)
    
    # Format and return results
    return create_response(200, {
        'results': response['Items'],
        'count': len(response['Items'])
    })
```

**GET /sentiment/summary** - Get summary statistics
```python
def get_sentiment_summary(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """Get sentiment analysis summary statistics"""
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    response = table.scan()
    items = response['Items']
    
    # Calculate statistics
    sentiment_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
    
    for item in items:
        sentiment = item['sentiment']
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    return create_response(200, {
        'total_items': len(items),
        'sentiment_counts': sentiment_counts
    })
```

**POST /sentiment/feedback** - Submit single feedback
```python
def handle_text_feedback(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle single text feedback submission"""
    body = json.loads(event.get('body', '{}'))
    
    if 'text' not in body or not body['text'].strip():
        return create_response(400, {'error': 'Text is required'})
    
    text = body['text'].strip()
    
    # Validate text length
    if len(text) < 10:
        return create_response(400, {'error': 'Text too short'})
    
    # Analyze sentiment
    sentiment_result = analyze_sentiment_simple(text, body.get('rating'))
    
    # Store in DynamoDB
    store_text_feedback_result(text, sentiment_result)
    
    return create_response(200, {
        'message': 'Feedback submitted successfully',
        'sentiment': sentiment_result['sentiment']
    })
```

### 7. Vue.js Component Example (`frontend-new/app/pages/index.vue`)
```vue
<template>
  <div class="container mx-auto px-4 py-8 space-y-8">
    <!-- File Upload Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Upload Feedback Files</h2>
      </template>
      <div class="border-2 border-dashed border-gray-300 rounded-lg p-8">
        <UIcon name="i-heroicons-cloud-arrow-up" class="w-12 h-12 mx-auto mb-4" />
        <UButton @click="fileInput?.click()">Choose Files</UButton>
        <input 
          ref="fileInput" 
          type="file" 
          accept=".csv,.json,.txt" 
          @change="handleFileUpload" 
          class="hidden" 
        />
      </div>
    </UCard>

    <!-- Individual Feedback Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Submit Individual Feedback</h2>
      </template>
      <div class="space-y-4">
        <UFormField label="Feedback Text">
          <UTextarea 
            v-model="feedbackText" 
            placeholder="Enter feedback..." 
            rows="4" 
          />
        </UFormField>
        <UFormField label="Rating">
          <URange v-model="rating" :min="1" :max="5" />
        </UFormField>
        <UButton @click="submitFeedback" :loading="isLoading">
          Submit Feedback
        </UButton>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSentimentStore } from '~/stores/sentiment'

const sentimentStore = useSentimentStore()
const feedbackText = ref('')
const rating = ref(3)
const isLoading = ref(false)
const fileInput = ref(null)

const handleFileUpload = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return
  
  isLoading.value = true
  try {
    // Upload each file
    for (const file of files) {
      await sentimentStore.uploadFile(file)
    }
  } finally {
    isLoading.value = false
  }
}

const submitFeedback = async () => {
  if (!feedbackText.value.trim()) return
  
  isLoading.value = true
  try {
    await sentimentStore.submitTextFeedback({
      text: feedbackText.value,
      rating: rating.value
    })
    feedbackText.value = ''
    rating.value = 3
  } finally {
    isLoading.value = false
  }
}
</script>
```

### 8. State Management (Pinia Store) (`frontend-new/app/stores/sentiment.js`)
```javascript
import { defineStore } from 'pinia'

export const useSentimentStore = defineStore('sentiment', {
  state: () => ({
    results: [],
    summary: {},
    isLoading: false,
    error: null
  }),

  getters: {
    positiveCount: (state) => state.summary.sentiment_counts?.POSITIVE || 0,
    negativeCount: (state) => state.summary.sentiment_counts?.NEGATIVE || 0,
    neutralCount: (state) => state.summary.sentiment_counts?.NEUTRAL || 0,
    totalCount: (state) => state.summary.total_feedback_items || 0
  },

  actions: {
    async fetchResults() {
      this.isLoading = true
      try {
        const config = useRuntimeConfig()
        const response = await $fetch(`${config.public.apiBaseUrl}/sentiment/results`)
        this.results = response.results
      } catch (error) {
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    async fetchSummary() {
      this.isLoading = true
      try {
        const config = useRuntimeConfig()
        const response = await $fetch(
          `${config.public.apiBaseUrl}/sentiment/results?summary=true`
        )
        this.summary = response
      } catch (error) {
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    async submitTextFeedback(payload) {
      try {
        const config = useRuntimeConfig()
        await $fetch(`${config.public.apiBaseUrl}/sentiment/feedback`, {
          method: 'POST',
          body: payload
        })
        await this.fetchResults()
        await this.fetchSummary()
      } catch (error) {
        this.error = error.message
      }
    },

    async uploadFile(file) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const config = useRuntimeConfig()
        await $fetch(`${config.public.apiBaseUrl}/sentiment/bulk`, {
          method: 'POST',
          body: formData
        })
        await this.fetchResults()
        await this.fetchSummary()
      } catch (error) {
        this.error = error.message
      }
    }
  }
})
```

---

## 🚀 Deployment Guide

### Development Deployment
```bash
# 1. Deploy infrastructure
cd backend/infrastructure/cloudformation
aws cloudformation create-stack \
  --stack-name sentiment-analysis-stack-dev \
  --template-body file://sentiment-analysis-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Deploy frontend
cd ../../../frontend-new
npm run build
aws s3 sync .output/public/ s3://sentiment-analysis-frontend-dev --delete
```

### Production Deployment
```bash
# 1. Deploy to production stack
aws cloudformation create-stack \
  --stack-name sentiment-analysis-stack-prod \
  --template-body file://sentiment-analysis-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Build and deploy frontend
npm run build
aws s3 sync .output/public/ s3://sentiment-analysis-frontend-prod --delete

# 3. Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"
```

---

## 🧪 Testing

### Test File Upload
```bash
# Create sample CSV file
cat > test-feedback.csv << EOF
feedback,rating,source
"The app is amazing!",5,mobile
"Terrible experience",1,web
"Average service",3,support
EOF

# Upload to S3
aws s3 cp test-feedback.csv s3://YOUR-BUCKET-NAME/

# Check CloudWatch logs
aws logs tail /aws/lambda/sentiment-processor-dev --follow
```

### Test API Endpoints
```bash
# Get summary
curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/sentiment/summary

# Get results
curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/sentiment/results

# Submit feedback
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/sentiment/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is great feedback!",
    "rating": 5
  }'
```

### Unit Tests
```bash
# Run backend tests
cd backend
pytest tests/ -v

# Run frontend tests
cd ../frontend-new
npm run test
```

---

## 🐛 Troubleshooting

### Issue: Lambda Function Timeout
**Symptoms**: Function returns 504 or "Task timed out"
**Solutions**:
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name sentiment-processor-dev \
  --timeout 900

# Increase memory (improves CPU)
aws lambda update-function-configuration \
  --function-name sentiment-processor-dev \
  --memory-size 1024
```

### Issue: DynamoDB Access Denied
**Symptoms**: "User is not authorized to perform: dynamodb:PutItem"
**Solutions**:
```bash
# Check IAM role
aws iam get-role --role-name LambdaExecutionRole

# Update role policies
aws iam attach-role-policy \
  --role-name LambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### Issue: S3 Bucket Not Triggering Lambda
**Symptoms**: Files upload but Lambda doesn't execute
**Solutions**:
```bash
# Check bucket notification configuration
aws s3api get-bucket-notification-configuration \
  --bucket YOUR-BUCKET-NAME

# Add Lambda permission for S3
aws lambda add-permission \
  --function-name sentiment-processor-dev \
  --principal s3.amazonaws.com \
  --action lambda:InvokeFunction \
  --statement-id AllowS3Invoke \
  --source-arn arn:aws:s3:::YOUR-BUCKET-NAME
```

### Issue: CORS Errors from Frontend
**Symptoms**: "CORS policy: No 'Access-Control-Allow-Origin' header"
**Solutions**:
```bash
# Check API Gateway CORS
aws apigateway get-method \
  --rest-api-id YOUR-API-ID \
  --resource-id YOUR-RESOURCE-ID \
  --http-method OPTIONS

# Update CORS in CloudFormation template
Cors:
  AllowMethods: "'GET,POST,OPTIONS'"
  AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"
  AllowOrigin: "'*'"
```

### Issue: High Costs (Exceeding Free Tier)
**Symptoms**: Unexpected AWS charges
**Solutions**:
```bash
# Monitor usage
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Check DynamoDB usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=sentiment-analysis-results-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 86400 \
  --statistics Sum

# Optimize: Use provisioned capacity for predictable workloads
```

---

## 📊 Monitoring and Logging

### CloudWatch Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/sentiment-processor-dev --follow

# View API Gateway logs
aws logs tail /aws/apigateway/sentiment-api-dev --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/sentiment-processor-dev \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics
```bash
# Monitor Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=sentiment-processor-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# Monitor Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=sentiment-processor-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

---

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/)
- [Nuxt 4 Documentation](https://nuxt.com/docs)
- [Vue.js 3 Guide](https://vuejs.org/)
- [Chart.js Documentation](https://www.chartjs.org/)

---

## ✅ Success Checklist

- [ ] AWS CLI configured and credentials verified
- [ ] CloudFormation stack created successfully
- [ ] S3 bucket created and accessible
- [ ] DynamoDB tables created
- [ ] Lambda functions deployed
- [ ] API Gateway endpoints accessible
- [ ] SNS topic configured with email subscription
- [ ] Frontend environment variables configured
- [ ] Frontend deployed to S3/CloudFront
- [ ] Test file upload processed successfully
- [ ] Dashboard displays sentiment analysis
- [ ] All API endpoints responding correctly
- [ ] CloudWatch logs showing no errors
- [ ] System monitoring and alerts configured

---

**Project Status**: ✅ Production Ready  
**Last Updated**: January 2025  
**Version**: 1.0.0

