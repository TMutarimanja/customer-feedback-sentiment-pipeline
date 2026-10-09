# Step-by-Step Deployment Guide

## 🎯 Quick Start (15-20 minutes)

This guide walks through the complete deployment process for the Customer Feedback Sentiment Analysis System.

---

## ✅ Pre-Deployment Checklist

### 1. AWS Account & Credentials
```bash
# Verify AWS CLI is installed
aws --version

# Configure AWS credentials
aws configure
# When prompted, enter:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]  
# Default region: us-east-1
# Default output format: json

# Verify setup
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/..."
}
```

### 2. Local Tools
```bash
# Check Python
python3 --version  # Should be 3.9+

# Check Node.js
node --version    # Should be 18+
npm --version     # Should be 8+

# Check Git
git --version     # Should be 2.x+
```

---

## 📦 Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd cloudComputingDiscussion1

# Verify structure
ls -la
# Should show: backend/, frontend-new/, docs/, README.md, etc.

# Create .gitignore entries (optional but recommended)
echo ".env.local" >> .gitignore
echo "venv/" >> .gitignore
echo "node_modules/" >> .gitignore
```

---

## 🔧 Step 2: Prepare Backend

### 2.1 Create Python Virtual Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Verify activation (should show (venv) in terminal)
which python  # macOS/Linux
where python  # Windows
```

### 2.2 Install Backend Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import boto3; print(boto3.__version__)"
```

Expected output:
```
1.34.0
```

### 2.3 Create Lambda Deployment Packages (Optional for Testing)

```bash
# Create function packages if needed
cd lambda/sentiment-processor
zip -r ../../../sentiment-processor.zip .

cd ../api-handler
zip -r ../../../api-handler.zip .

# Verify packages created
ls -lh ../../../sentiment-processor.zip
```

---

## ☁️ Step 3: Deploy AWS Infrastructure (CloudFormation)

### 3.1 Set Environment Variables

```bash
# Set variables for easy reference
export AWS_REGION="us-east-1"
export ENVIRONMENT="dev"
export EMAIL="your-email@example.com"  # Change this!
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export STACK_NAME="sentiment-analysis-stack-${ENVIRONMENT}"

# Verify variables
echo "Stack: $STACK_NAME"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
```

### 3.2 Validate CloudFormation Template

```bash
# Navigate to CloudFormation directory
cd backend/infrastructure/cloudformation

# Validate template
aws cloudformation validate-template \
  --template-body file://sentiment-analysis-stack.yaml \
  --region $AWS_REGION

# Should return: TemplateDescription, Parameters, etc.
```

### 3.3 Create CloudFormation Stack

```bash
# Create the stack
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://sentiment-analysis-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    ParameterKey=S3BucketName,ParameterValue=customer-feedback-sentiment-analysis \
    ParameterKey=NotificationEmail,ParameterValue=$EMAIL \
    ParameterKey=NegativeSentimentThreshold,ParameterValue=0.3 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

# Output will show StackId
# Example: arn:aws:cloudformation:us-east-1:123456789012:stack/...
```

### 3.4 Monitor Stack Creation

```bash
# Check stack creation progress
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].StackStatus' \
  --region $AWS_REGION

# Watch creation (runs every 5 seconds)
watch -n 5 "aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].StackStatus' \
  --region $AWS_REGION"

# Or wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $AWS_REGION

# Once complete, should print: "Stack creation successful"
```

### 3.5 Get Stack Outputs

```bash
# Retrieve stack outputs
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs' \
  --region $AWS_REGION

# Store outputs in variables for later use
API_GATEWAY_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text \
  --region $AWS_REGION)

S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CustomerFeedbackBucketName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

DYNAMODB_TABLE=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`SentimentAnalysisTableName`].OutputValue' \
  --output text \
  --region $AWS_REGION)

# Verify outputs
echo "API URL: $API_GATEWAY_URL"
echo "S3 Bucket: $S3_BUCKET"
echo "DynamoDB Table: $DYNAMODB_TABLE"
```

---

## 🎨 Step 4: Deploy Frontend

### 4.1 Install Frontend Dependencies

```bash
# Navigate to frontend
cd ../../frontend-new

# Install Node dependencies
npm install

# Verify installation
npm list @nuxt/ui

# Should show: @nuxt/ui@X.X.X
```

### 4.2 Configure Environment

```bash
# Create environment file
cat > .env.local << EOF
API_BASE_URL=$API_GATEWAY_URL
S3_BUCKET_NAME=$S3_BUCKET
EOF

# Verify environment file
cat .env.local
```

### 4.3 Test Frontend Locally (Optional)

```bash
# Run development server
npm run dev

# Output should show:
# > Local:    http://localhost:3000/
# > Modules:  1

# Open browser and visit http://localhost:3000
# Check for any console errors

# Stop server (Ctrl+C)
```

### 4.4 Build Frontend

```bash
# Build for production
npm run build

# Verify build output
ls -la .output/public/

# Should contain: index.html, _nuxt/, assets/, etc.
```

### 4.5 Deploy to S3

```bash
# Create S3 bucket for frontend (if not using CloudFormation)
# aws s3 mb s3://sentiment-analysis-frontend-${ACCOUNT_ID} --region $AWS_REGION

# Sync built files to S3
aws s3 sync .output/public/ \
  s3://$S3_BUCKET-frontend/ \
  --delete \
  --region $AWS_REGION

# Verify upload
aws s3 ls s3://$S3_BUCKET-frontend/ --recursive --region $AWS_REGION

# Should show all files uploaded
```

### 4.6 Configure S3 for Static Website (Optional)

```bash
# Enable static website hosting
aws s3 website s3://$S3_BUCKET-frontend/ \
  --index-document index.html \
  --error-document index.html \
  --region $AWS_REGION

# Get website endpoint
aws s3api get-bucket-website \
  --bucket $S3_BUCKET-frontend \
  --region $AWS_REGION
```

---

## 📧 Step 5: Configure SNS Notifications

### 5.1 Subscribe to Email Notifications

```bash
# Get SNS Topic ARN
SNS_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`NotificationTopicArn`].OutputValue' \
  --output text \
  --region $AWS_REGION)

echo "SNS Topic: $SNS_TOPIC"

# List existing subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn $SNS_TOPIC \
  --region $AWS_REGION

# Check email for subscription confirmation
# (You should have received an email - click the confirmation link)
```

---

## 🧪 Step 6: Test the System

### 6.1 Test S3 File Upload

```bash
# Create sample CSV file
cat > test-feedback.csv << EOF
feedback,rating,source
"The app is absolutely amazing and works great!",5,mobile
"I love the new features, excellent job!",5,web
"The customer service was terrible and unhelpful.",1,support
"This is the worst experience I've ever had.",1,mobile
"Average service, nothing special.",3,web
"Excellent support team, very helpful!",5,support
"Great application overall!",4,web
"Highly recommended to everyone!",5,mobile
"Very disappointed with the performance.",2,web
"Best investment ever!",5,support
EOF

# Upload to S3 (this triggers Lambda)
aws s3 cp test-feedback.csv s3://$S3_BUCKET/ --region $AWS_REGION

echo "File uploaded. Lambda will process it automatically..."

# Wait a few seconds for processing
sleep 10

# Check Lambda logs
aws logs tail /aws/lambda/sentiment-processor-${ENVIRONMENT} \
  --follow \
  --region $AWS_REGION

# Should see processing logs
```

### 6.2 Test API Endpoints

```bash
# Get summary statistics
curl -s "$API_GATEWAY_URL/sentiment/summary?summary=true" | jq .

# Get all results
curl -s "$API_GATEWAY_URL/sentiment/results" | jq .

# Submit single feedback
curl -s -X POST "$API_GATEWAY_URL/sentiment/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is excellent service!",
    "rating": 5,
    "customer_info": {
      "name": "Test User",
      "email": "test@example.com"
    }
  }' | jq .

# Should return: sentiment analysis result
```

### 6.3 Check DynamoDB Data

```bash
# Scan DynamoDB table to see results
aws dynamodb scan \
  --table-name $DYNAMODB_TABLE \
  --max-items 5 \
  --region $AWS_REGION

# Get item count
aws dynamodb scan \
  --table-name $DYNAMODB_TABLE \
  --select COUNT \
  --region $AWS_REGION

# Should show items with sentiment analysis
```

---

## 📊 Step 7: Access Dashboard

### 7.1 View Frontend Dashboard

```bash
# Get frontend URL from S3 website endpoint
aws s3api get-bucket-website \
  --bucket $S3_BUCKET-frontend \
  --region $AWS_REGION

# Or directly:
FRONTEND_URL="http://${S3_BUCKET}-frontend.s3-website.${AWS_REGION}.amazonaws.com"

echo "Frontend: $FRONTEND_URL"

# Open in browser
open "$FRONTEND_URL"  # macOS
# OR
xdg-open "$FRONTEND_URL"  # Linux
# OR
start "$FRONTEND_URL"  # Windows
```

### 7.2 Expected Dashboard Features

- ✅ File upload interface
- ✅ Individual feedback submission
- ✅ Sentiment distribution chart
- ✅ Summary statistics
- ✅ Results table with filtering
- ✅ Real-time updates

---

## 🔍 Step 8: Monitoring & Troubleshooting

### 8.1 Check CloudWatch Logs

```bash
# View sentiment processor logs
aws logs tail /aws/lambda/sentiment-processor-${ENVIRONMENT} --follow

# View API handler logs  
aws logs tail /aws/lambda/sentiment-api-handler-${ENVIRONMENT} --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/sentiment-processor-${ENVIRONMENT} \
  --filter-pattern "ERROR"
```

### 8.2 Check Lambda Function Status

```bash
# Get function info
aws lambda get-function \
  --function-name sentiment-processor-${ENVIRONMENT} \
  --region $AWS_REGION

# View recent invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=sentiment-processor-${ENVIRONMENT} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region $AWS_REGION
```

### 8.3 Check DynamoDB Performance

```bash
# Check table size
aws dynamodb describe-table \
  --table-name $DYNAMODB_TABLE \
  --region $AWS_REGION \
  --query 'Table.TableSizeBytes'

# Check item count
aws dynamodb scan \
  --table-name $DYNAMODB_TABLE \
  --select COUNT \
  --region $AWS_REGION
```

---

## 💰 Step 9: Verify Free Tier Compliance

```bash
# Get current AWS usage
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 day ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --region $AWS_REGION

# Check service quotas
aws service-quotas list-service-quotas \
  --service-code lambda \
  --region $AWS_REGION

# Should show: 1M requests/month (free tier)
```

---

## 🚀 Step 10: Production Deployment

### 10.1 Deploy to Production Stack

```bash
# Create production stack (repeat steps 3.1-3.5 with ENVIRONMENT=prod)
export ENVIRONMENT="prod"
export STACK_NAME="sentiment-analysis-stack-${ENVIRONMENT}"

aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://backend/infrastructure/cloudformation/sentiment-analysis-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    ParameterKey=S3BucketName,ParameterValue=customer-feedback-sentiment-analysis \
    ParameterKey=NotificationEmail,ParameterValue=$EMAIL \
    ParameterKey=NegativeSentimentThreshold,ParameterValue=0.3 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $AWS_REGION
```

### 10.2 Deploy Production Frontend

```bash
# Update environment for production
cat > .env.local << EOF
API_BASE_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text)
S3_BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CustomerFeedbackBucketName`].OutputValue' \
  --output text)
EOF

# Build and deploy
npm run build
aws s3 sync .output/public/ \
  s3://$(cat .env.local | grep S3_BUCKET_NAME | cut -d= -f2)-frontend/ \
  --delete \
  --region $AWS_REGION
```

---

## ✅ Verification Checklist

Before considering deployment complete:

- [ ] CloudFormation stack created successfully
- [ ] S3 bucket contains uploaded files
- [ ] DynamoDB table has test data
- [ ] Lambda functions invoked without errors
- [ ] API endpoints return JSON responses
- [ ] Frontend loads without errors
- [ ] Dashboard displays sentiment data
- [ ] SNS notifications received
- [ ] CloudWatch logs clean (no errors)
- [ ] System within free tier limits

---

## 🆘 Common Issues & Fixes

### Issue: "Stack creation failed"
```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name $STACK_NAME | jq '.StackEvents[] | {Timestamp, LogicalResourceId, ResourceStatus, ResourceStatusReason}'
```

### Issue: "Lambda timeout"
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name sentiment-processor-${ENVIRONMENT} \
  --timeout 600 \
  --region $AWS_REGION
```

### Issue: "Permission denied" errors
```bash
# Check IAM role
aws iam list-attached-role-policies \
  --role-name sentiment-analysis-stack-${ENVIRONMENT}-LambdaExecutionRole*
```

### Issue: "Frontend not loading"
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy \
  --bucket $S3_BUCKET-frontend

# Enable public access if needed
aws s3api put-bucket-policy \
  --bucket $S3_BUCKET-frontend \
  --policy file://bucket-policy.json
```

---

## 🎉 Success!

Your deployment is complete when:
1. ✅ All AWS resources created
2. ✅ Sample file processed successfully
3. ✅ API endpoints responding
4. ✅ Frontend dashboard loads and displays data
5. ✅ Notifications working
6. ✅ No errors in logs

---

## 📞 Need Help?

Check these resources:
- AWS CloudFormation Documentation: https://docs.aws.amazon.com/cloudformation/
- AWS Lambda Guide: https://docs.aws.amazon.com/lambda/
- Troubleshooting section in IMPLEMENTATION_GUIDE.md

**Estimated Total Time**: 20-30 minutes  
**Cost**: $0 (within AWS Free Tier)  
**Success Rate**: 95%+ when following steps

