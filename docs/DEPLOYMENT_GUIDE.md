# Customer Feedback Sentiment Analysis - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Node.js 18+ and npm installed
- Git installed

### Install Required Tools
```bash
# Install AWS CLI (if not already installed)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installations
aws --version
node --version
npm --version
```

## 📋 Deployment Options

### Option 1: CloudFormation (Recommended)

#### 1. Deploy Backend Infrastructure
```bash
# Navigate to the project directory
cd /path/to/cloudComputingDiscussion1

# Deploy the CloudFormation stack
aws cloudformation create-stack \
  --stack-name sentiment-analysis-stack-prod \
  --template-body file://aws-cloudformation-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
               ParameterKey=S3BucketName,ParameterValue=customer-feedback-sentiment-analysis \
               ParameterKey=NotificationEmail,ParameterValue=your-email@example.com \
               ParameterKey=NegativeSentimentThreshold,ParameterValue=0.3 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name sentiment-analysis-stack-prod \
  --region us-east-1
```

#### 2. Get Stack Outputs
```bash
# Get API Gateway URL
aws cloudformation describe-stacks \
  --stack-name sentiment-analysis-stack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text

# Get S3 Bucket Name
aws cloudformation describe-stacks \
  --stack-name sentiment-analysis-stack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`CustomerFeedbackBucketName`].OutputValue' \
  --output text
```

#### 3. Deploy Frontend (Nuxt 4)
```bash
# Navigate to frontend directory
cd frontend-new

# Install dependencies
npm install

# Update configuration with your API URL
# Edit nuxt.config.ts and update the apiBaseUrl

# Build the application
npm run build

# Deploy to S3 and CloudFront
aws s3 sync .output/public/ s3://sentiment-analysis-frontend-123456789012 --delete
aws cloudfront create-invalidation --distribution-id E1R08LGUOQPA1E --paths "/*"
```

### Option 2: AWS SAM

#### 1. Install SAM CLI
```bash
pip install aws-sam-cli
sam --version
```

#### 2. Deploy with SAM
```bash
# Navigate to SAM directory
cd backend/infrastructure/sam

# Build the application
sam build

# Deploy to development
sam deploy --config-env dev

# Deploy to production
sam deploy --config-env prod
```

### Option 3: Manual Deployment

#### 1. Create S3 Bucket
```bash
# Create bucket with unique name
BUCKET_NAME="customer-feedback-sentiment-analysis-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME

# Enable versioning and encryption
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

#### 2. Create DynamoDB Tables
```bash
# Create sentiment results table
aws dynamodb create-table \
  --table-name sentiment-analysis-results-prod \
  --attribute-definitions \
    AttributeName=id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=TimestampIndex,KeySchema='[{AttributeName=timestamp,KeyType=HASH}]',Projection='{ProjectionType=ALL}' \
  --billing-mode PAY_PER_REQUEST

# Create alerts table
aws dynamodb create-table \
  --table-name sentiment-alerts-prod \
  --attribute-definitions \
    AttributeName=id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

#### 3. Deploy Lambda Functions
```bash
# Create deployment packages
cd backend/lambda/sentiment-processor
zip -r sentiment-processor.zip .
aws lambda create-function \
  --function-name sentiment-processor-prod \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR-ACCOUNT:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://sentiment-processor.zip \
  --timeout 300 \
  --memory-size 512

# Repeat for other Lambda functions...
```

## 🔧 Configuration

### Frontend Configuration (Nuxt 4)
```typescript
// frontend-new/nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBaseUrl: 'https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod',
      s3BucketName: 'YOUR-S3-BUCKET-NAME'
    }
  }
})
```

### Environment Variables
```bash
# Backend Lambda environment variables
export ENVIRONMENT=prod
export S3_BUCKET_NAME=your-bucket-name
export DYNAMODB_TABLE_NAME=sentiment-analysis-results-prod
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR-ACCOUNT:sentiment-notifications
export NOTIFICATION_EMAIL=your-email@example.com
```

## 🧪 Testing the Deployment

### 1. Test API Endpoints
```bash
# Get API URL from CloudFormation outputs
API_URL="https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod"

# Test summary endpoint
curl "$API_URL/sentiment/summary"

# Test results endpoint
curl "$API_URL/sentiment/results"

# Test single feedback submission
curl -X POST "$API_URL/sentiment/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test feedback message",
    "rating": 5,
    "metadata": {
      "customer_name": "Test User",
      "source": "web"
    }
  }'
```

### 2. Upload Test Files
```bash
# Create sample CSV file
cat > test-feedback.csv << EOF
feedback,rating,source
"The app is amazing and easy to use!",5,mobile
"I love the new features, great job!",5,web
"The customer service was terrible and unhelpful.",1,support
"This is the worst banking app I've ever used.",1,mobile
EOF

# Upload to S3 (this triggers Lambda processing)
aws s3 cp test-feedback.csv s3://YOUR-BUCKET-NAME/
```

### 3. Monitor Processing
```bash
# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# Get recent log events
aws logs get-log-events \
  --log-group-name /aws/lambda/sentiment-processor-prod \
  --log-stream-name $(aws logs describe-log-streams \
    --log-group-name /aws/lambda/sentiment-processor-prod \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text)
```

## 📊 Monitoring & Troubleshooting

### CloudWatch Logs
- `/aws/lambda/sentiment-processor-prod`
- `/aws/lambda/sentiment-api-handler-prod`
- `/aws/lambda/sentiment-alert-handler-prod`

### Common Issues & Solutions

#### 1. Stack Creation Fails
```bash
# Check stack events for errors
aws cloudformation describe-stack-events \
  --stack-name sentiment-analysis-stack-prod

# Verify IAM permissions
aws sts get-caller-identity
```

#### 2. Lambda Function Errors
```bash
# Check function logs
aws logs get-log-events \
  --log-group-name /aws/lambda/sentiment-processor-prod \
  --start-time $(date -d '1 hour ago' +%s)000

# Update function configuration
aws lambda update-function-configuration \
  --function-name sentiment-processor-prod \
  --timeout 300 \
  --memory-size 1024
```

#### 3. API Gateway Issues
```bash
# Test API Gateway directly
aws apigateway get-rest-api --rest-api-id YOUR-API-ID

# Check CORS configuration
aws apigateway get-method \
  --rest-api-id YOUR-API-ID \
  --resource-id YOUR-RESOURCE-ID \
  --http-method OPTIONS
```

#### 4. S3 Access Issues
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket YOUR-BUCKET-NAME

# Update bucket policy if needed
aws s3api put-bucket-policy \
  --bucket YOUR-BUCKET-NAME \
  --policy file://bucket-policy.json
```

### Debugging Commands
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name sentiment-analysis-stack-prod

# List all resources in stack
aws cloudformation list-stack-resources --stack-name sentiment-analysis-stack-prod

# Test Lambda function directly
aws lambda invoke \
  --function-name sentiment-processor-prod \
  --payload file://test-payload.json \
  response.json

# Check DynamoDB table
aws dynamodb describe-table --table-name sentiment-analysis-results-prod

# Monitor costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## 🔐 Security Configuration

### 1. SNS Email Subscription
```bash
# Check SNS topic
aws sns list-topics

# Subscribe to email notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT:sentiment-notifications-prod \
  --protocol email \
  --notification-endpoint your-email@example.com

# Confirm subscription (check your email and click link)
```

### 2. IAM Roles and Policies
```bash
# Check Lambda execution role
aws iam get-role --role-name LambdaExecutionRole

# Update role policies if needed
aws iam attach-role-policy \
  --role-name LambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### 3. VPC Configuration (Optional)
```bash
# Create VPC endpoints for private communication
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway
```

## 💰 Cost Monitoring

### AWS Free Tier Limits
- **Lambda**: 1M requests, 400,000 GB-seconds
- **S3**: 5GB storage, 20,000 GET requests
- **DynamoDB**: 25GB storage, 25 read/write capacity units
- **API Gateway**: 1M API calls per month
- **CloudFront**: 1TB data transfer out, 10M requests

### Cost Monitoring Commands
```bash
# Set up billing alerts
aws cloudwatch put-metric-alarm \
  --alarm-name "MonthlyCostAlert" \
  --alarm-description "Alert when monthly cost exceeds $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold

# Check current usage
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## 🚀 Production Considerations

### 1. Environment-Specific Configurations

#### Development
- **Stack Name**: `sentiment-analysis-stack-dev`
- **Log Retention**: 7 days
- **Monitoring**: Basic CloudWatch metrics
- **Cost**: Free tier only

#### Production
- **Stack Name**: `sentiment-analysis-stack-prod`
- **Log Retention**: 30 days
- **Monitoring**: Full monitoring with alerts
- **Backup**: Cross-region replication
- **Security**: Enhanced policies

### 2. Scaling Considerations
```bash
# Monitor DynamoDB capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=sentiment-analysis-results-prod \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Monitor Lambda performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=sentiment-processor-prod \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### 3. Backup and Recovery
```bash
# Enable DynamoDB point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name sentiment-analysis-results-prod \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Create S3 bucket versioning
aws s3api put-bucket-versioning \
  --bucket YOUR-BUCKET-NAME \
  --versioning-configuration Status=Enabled
```

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] **API Gateway** responds to all endpoints
- [ ] **S3 bucket** accepts file uploads
- [ ] **Lambda functions** process files correctly
- [ ] **DynamoDB** stores results properly
- [ ] **SNS notifications** work (check email)
- [ ] **Frontend** connects to API successfully
- [ ] **CloudWatch logs** show no errors
- [ ] **Cost monitoring** is set up
- [ ] **Security policies** are properly configured

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All API endpoints return expected responses
- ✅ File uploads trigger sentiment analysis
- ✅ Results are stored in DynamoDB
- ✅ Email notifications are received
- ✅ Frontend displays data correctly
- ✅ System stays within free tier limits
- ✅ No errors in CloudWatch logs

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name sentiment-analysis-stack-prod \
  --template-body file://aws-cloudformation-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Update frontend
cd frontend-new
npm run build
aws s3 sync .output/public/ s3://sentiment-analysis-frontend-123456789012 --delete
aws cloudfront create-invalidation --distribution-id E1R08LGUOQPA1E --paths "/*"
```

### Regular Maintenance Tasks
- Monitor CloudWatch logs for errors
- Check AWS costs monthly
- Update dependencies quarterly
- Review security policies annually
- Test backup and recovery procedures

## 📞 Support and Resources

### AWS Documentation
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [S3 User Guide](https://docs.aws.amazon.com/s3/)

### Troubleshooting Resources
- AWS Support Center
- AWS Forums
- Stack Overflow
- GitHub Issues (for this project)

---

**Remember**: Always test deployments in a development environment before promoting to production. Monitor costs closely and stay within free tier limits whenever possible.
