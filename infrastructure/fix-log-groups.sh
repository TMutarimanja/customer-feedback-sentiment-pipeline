#!/bin/bash

# Fix CloudWatch Log Groups Issue
# This script handles the existing log groups conflict

echo "🔧 Fixing CloudWatch Log Groups Issue..."

# Set environment
ENVIRONMENT="dev"
REGION="us-east-1"

echo "📋 Current log groups:"
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/sentiment" \
  --region $REGION \
  --query 'logGroups[].logGroupName' \
  --output table

echo ""
echo "🗑️  Deleting existing log groups to avoid conflicts..."

# Delete existing log groups
aws logs delete-log-group \
  --log-group-name "/aws/lambda/sentiment-processor-$ENVIRONMENT" \
  --region $REGION 2>/dev/null || echo "Log group /aws/lambda/sentiment-processor-$ENVIRONMENT not found or already deleted"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/sentiment-api-handler-$ENVIRONMENT" \
  --region $REGION 2>/dev/null || echo "Log group /aws/lambda/sentiment-api-handler-$ENVIRONMENT not found or already deleted"

aws logs delete-log-group \
  --log-group-name "/aws/lambda/sentiment-alert-handler-$ENVIRONMENT" \
  --region $REGION 2>/dev/null || echo "Log group /aws/lambda/sentiment-alert-handler-$ENVIRONMENT not found or already deleted"

echo ""
echo "✅ Log groups cleaned up. You can now redeploy the CloudFormation stack."
echo ""
echo "🚀 To redeploy:"
echo "aws cloudformation update-stack \\"
echo "  --stack-name sentiment-analysis-stack-dev \\"
echo "  --template-body file://aws-cloudformation-template.yaml \\"
echo "  --capabilities CAPABILITY_NAMED_IAM \\"
echo "  --region $REGION"
