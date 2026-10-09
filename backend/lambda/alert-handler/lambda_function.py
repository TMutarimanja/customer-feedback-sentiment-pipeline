"""
Lambda function to handle alerts and notifications for the sentiment analysis system.
Processes negative sentiment alerts and sends notifications via SNS.
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', '')
DYNAMODB_ALERTS_TABLE = os.environ.get('DYNAMODB_ALERTS_TABLE', 'sentiment-alerts')

def lambda_handler(event, context):
    """
    Main Lambda handler function for alert processing.
    
    Args:
        event: Event containing alert information
        context: Lambda context object
        
    Returns:
        dict: Response with processing status
    """
    try:
        logger.info(f"Processing alert event: {json.dumps(event)}")
        
        # Handle different types of alerts
        alert_type = event.get('alert_type', 'negative_sentiment')
        
        if alert_type == 'negative_sentiment':
            return handle_negative_sentiment_alert(event)
        elif alert_type == 'system_alert':
            return handle_system_alert(event)
        elif alert_type == 'summary_report':
            return handle_summary_report(event)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unknown alert type',
                    'alert_type': alert_type
                })
            }
            
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process alert',
                'message': str(e)
            })
        }

def handle_negative_sentiment_alert(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle negative sentiment alert.
    
    Args:
        event: Event containing alert information
        
    Returns:
        dict: Response with processing status
    """
    try:
        # Extract alert information
        object_key = event.get('object_key', '')
        negative_count = event.get('negative_count', 0)
        total_count = event.get('total_count', 0)
        negative_percentage = event.get('negative_percentage', 0)
        
        # Store alert in DynamoDB
        alert_id = store_alert_record(
            alert_type='negative_sentiment',
            object_key=object_key,
            details={
                'negative_count': negative_count,
                'total_count': total_count,
                'negative_percentage': negative_percentage
            }
        )
        
        # Send SNS notification
        if SNS_TOPIC_ARN:
            send_sns_notification(
                subject=f"Negative Sentiment Alert - {object_key}",
                message=create_negative_sentiment_message(
                    object_key, negative_count, total_count, negative_percentage
                )
            )
        
        # Send email notification if SES is configured
        if SES_FROM_EMAIL:
            send_email_notification(
                subject=f"Negative Sentiment Alert - {object_key}",
                message=create_negative_sentiment_message(
                    object_key, negative_count, total_count, negative_percentage
                )
            )
        
        logger.info(f"Processed negative sentiment alert: {alert_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Negative sentiment alert processed successfully',
                'alert_id': alert_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling negative sentiment alert: {str(e)}")
        raise

def handle_system_alert(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle system alert (errors, performance issues, etc.).
    
    Args:
        event: Event containing alert information
        
    Returns:
        dict: Response with processing status
    """
    try:
        # Extract alert information
        alert_level = event.get('level', 'INFO')
        message = event.get('message', '')
        details = event.get('details', {})
        
        # Store alert in DynamoDB
        alert_id = store_alert_record(
            alert_type='system_alert',
            details={
                'level': alert_level,
                'message': message,
                'details': details
            }
        )
        
        # Send notification for high-priority alerts
        if alert_level in ['ERROR', 'CRITICAL']:
            if SNS_TOPIC_ARN:
                send_sns_notification(
                    subject=f"System Alert [{alert_level}] - Sentiment Analysis",
                    message=create_system_alert_message(alert_level, message, details)
                )
        
        logger.info(f"Processed system alert: {alert_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'System alert processed successfully',
                'alert_id': alert_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling system alert: {str(e)}")
        raise

def handle_summary_report(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle summary report generation and distribution.
    
    Args:
        event: Event containing report information
        
    Returns:
        dict: Response with processing status
    """
    try:
        # Extract report information
        report_period = event.get('period', 'daily')
        summary_data = event.get('summary_data', {})
        
        # Store report in DynamoDB
        report_id = store_alert_record(
            alert_type='summary_report',
            details={
                'period': report_period,
                'summary_data': summary_data
            }
        )
        
        # Send summary report
        if SNS_TOPIC_ARN:
            send_sns_notification(
                subject=f"Sentiment Analysis Summary Report - {report_period.title()}",
                message=create_summary_report_message(report_period, summary_data)
            )
        
        logger.info(f"Processed summary report: {report_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Summary report processed successfully',
                'report_id': report_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling summary report: {str(e)}")
        raise

def store_alert_record(alert_type: str, object_key: str = '', details: Dict[str, Any] = None) -> str:
    """
    Store alert record in DynamoDB.
    
    Args:
        alert_type: Type of alert
        object_key: S3 object key (if applicable)
        details: Alert details
        
    Returns:
        str: Alert ID
    """
    try:
        table = dynamodb.Table(DYNAMODB_ALERTS_TABLE)
        
        # Generate unique alert ID
        alert_id = f"{alert_type}_{datetime.now().isoformat()}"
        
        # Prepare item for DynamoDB
        item = {
            'id': alert_id,
            'alert_type': alert_type,
            'object_key': object_key,
            'details': details or {},
            'timestamp': datetime.now().isoformat(),
            'status': 'processed',
            'ttl': int((datetime.now().timestamp() + (90 * 24 * 60 * 60)))  # 90 days TTL
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Stored alert record: {alert_id}")
        return alert_id
        
    except Exception as e:
        logger.error(f"Error storing alert record: {str(e)}")
        raise

def send_sns_notification(subject: str, message: str):
    """
    Send SNS notification.
    
    Args:
        subject: Notification subject
        message: Notification message
    """
    try:
        if not SNS_TOPIC_ARN:
            logger.warning("SNS topic ARN not configured, skipping notification")
            return
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        
        logger.info(f"Sent SNS notification: {subject}")
        
    except Exception as e:
        logger.error(f"Error sending SNS notification: {str(e)}")
        # Don't raise exception for notification failures

def send_email_notification(subject: str, message: str):
    """
    Send email notification via SES.
    
    Args:
        subject: Email subject
        message: Email message
    """
    try:
        if not SES_FROM_EMAIL:
            logger.warning("SES from email not configured, skipping email notification")
            return
        
        # For demo purposes, we'll use a placeholder recipient
        # In production, this would be configured based on the alert type
        recipient_email = os.environ.get('SES_TO_EMAIL', 'admin@example.com')
        
        ses_client.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': message},
                    'Html': {'Data': f"<pre>{message}</pre>"}
                }
            }
        )
        
        logger.info(f"Sent email notification: {subject}")
        
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        # Don't raise exception for notification failures

def create_negative_sentiment_message(object_key: str, negative_count: int, 
                                    total_count: int, negative_percentage: float) -> str:
    """
    Create negative sentiment alert message.
    
    Args:
        object_key: S3 object key
        negative_count: Number of negative items
        total_count: Total number of items
        negative_percentage: Percentage of negative items
        
    Returns:
        str: Formatted message
    """
    return f"""
🚨 NEGATIVE SENTIMENT ALERT 🚨

File: {object_key}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
• Total feedback items: {total_count}
• Negative sentiment items: {negative_count}
• Negative sentiment percentage: {negative_percentage:.1f}%

Action Required:
Please review the customer feedback and take appropriate action to address the concerns raised.

This alert was generated automatically by the Sentiment Analysis System.
"""

def create_system_alert_message(level: str, message: str, details: Dict[str, Any]) -> str:
    """
    Create system alert message.
    
    Args:
        level: Alert level
        message: Alert message
        details: Alert details
        
    Returns:
        str: Formatted message
    """
    return f"""
🔧 SYSTEM ALERT [{level}] 🔧

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}

Details:
{json.dumps(details, indent=2)}

This alert was generated automatically by the Sentiment Analysis System.
"""

def create_summary_report_message(period: str, summary_data: Dict[str, Any]) -> str:
    """
    Create summary report message.
    
    Args:
        period: Report period
        summary_data: Summary data
        
    Returns:
        str: Formatted message
    """
    return f"""
📊 SENTIMENT ANALYSIS SUMMARY REPORT 📊

Period: {period.title()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
• Total feedback items: {summary_data.get('total_feedback_items', 0)}
• Positive sentiment: {summary_data.get('sentiment_percentages', {}).get('POSITIVE', 0):.1f}%
• Negative sentiment: {summary_data.get('sentiment_percentages', {}).get('NEGATIVE', 0):.1f}%
• Neutral sentiment: {summary_data.get('sentiment_percentages', {}).get('NEUTRAL', 0):.1f}%

This report was generated automatically by the Sentiment Analysis System.
"""
