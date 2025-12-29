from .models import Notification
from accounts.models import HouseholdMembership


def get_user_notification_type(user):
    """
    Get the preferred notification type for a user based on their preferences.
    
    Args:
        user: User instance
    
    Returns:
        String representing notification type ('push', 'sms', 'email')
    """
    try:
        prefs = user.notification_preferences
        if prefs.enable_push:
            return 'push'
        elif prefs.enable_email:
            return 'email'
        elif prefs.enable_sms:
            return 'sms'
        return 'push'  # Default fallback
    except Exception:
        return 'push'  # Default if preferences don't exist


def should_notify_user(user, event_type):
    """
    Check if a user should be notified for a specific event type.
    
    Args:
        user: User instance
        event_type: String representing the event ('expense_created', 'refund_requested', etc.)
    
    Returns:
        Boolean indicating whether to send notification
    """
    try:
        prefs = user.notification_preferences
        event_map = {
            'expense_created': prefs.notify_on_expense_created,
            'refund_requested': prefs.notify_on_refund_requested,
            'refund_approved': prefs.notify_on_refund_approved,
            'refund_rejected': prefs.notify_on_refund_rejected,
            'budget_exceeded': prefs.notify_on_budget_exceeded,
        }
        return event_map.get(event_type, True)  # Default to True if event not mapped
    except Exception:
        return True  # Default to sending notification if preferences don't exist


def create_notification(user, message, notification_type='push', event_type=None):
    """
    Create a notification for a specific user.
    
    Args:
        user: User instance to receive the notification
        message: Notification message text
        notification_type: Type of notification ('push', 'sms', 'email')
        event_type: Optional event type for preference checking
    
    Returns:
        Notification instance or None if user preferences block it
    """
    # Check if user wants this type of notification
    if event_type and not should_notify_user(user, event_type):
        return None
    
    # Get user's preferred notification type
    preferred_type = get_user_notification_type(user)
    
    return Notification.objects.create(
        user=user,
        message=message,
        type=preferred_type
    )


def notify_household_members(household, message, exclude_user=None, roles=None, notification_type='push', event_type=None):
    """
    Send notifications to all members of a household.
    
    Args:
        household: Household instance
        message: Notification message text
        exclude_user: Optional user to exclude from notifications (e.g., the user who triggered the action)
        roles: Optional list of roles to notify (e.g., ['homeowner', 'helper']). If None, notifies all.
        notification_type: Type of notification ('push', 'sms', 'email')
        event_type: Optional event type for preference checking
    
    Returns:
        List of created Notification instances
    """
    memberships = HouseholdMembership.objects.filter(household=household)
    
    if roles:
        memberships = memberships.filter(role__in=roles)
    
    if exclude_user:
        memberships = memberships.exclude(user=exclude_user)
    
    notifications = []
    for membership in memberships:
        notification = create_notification(
            user=membership.user,
            message=message,
            notification_type=notification_type,
            event_type=event_type
        )
        if notification:  # Only add if notification was created (not blocked by preferences)
            notifications.append(notification)
    
    return notifications


def notify_expense_created(expense):
    """
    Notify relevant household members when an expense is created.
    Notifies homeowners and helpers (excluding the creator).
    """
    message = (
        f"New expense: {expense.recorded_by.username} recorded "
        f"{expense.household.currency} {expense.amount} "
        f"for {expense.category.name if expense.category else 'Uncategorized'} "
        f"on {expense.date.strftime('%Y-%m-%d')}"
    )
    
    return notify_household_members(
        household=expense.household,
        message=message,
        exclude_user=expense.recorded_by,
        roles=['homeowner', 'helper'],
        event_type='expense_created'
    )


def notify_refund_requested(refund_request):
    """
    Notify homeowners when a refund is requested.
    """
    message = (
        f"Refund request: {refund_request.requested_by.username} requested "
        f"{refund_request.expense.household.currency} {refund_request.amount} "
        f"refund. Reason: {refund_request.reason[:50]}..."
    )
    
    return notify_household_members(
        household=refund_request.expense.household,
        message=message,
        exclude_user=refund_request.requested_by,
        roles=['homeowner'],
        event_type='refund_requested'
    )


def notify_refund_status_changed(refund_request, status):
    """
    Notify the requester when their refund status changes.
    """
    status_messages = {
        'approved': f"Your refund request for {refund_request.expense.household.currency} {refund_request.amount} has been approved.",
        'rejected': f"Your refund request for {refund_request.expense.household.currency} {refund_request.amount} has been rejected.",
        'need_info': f"Additional information needed for your refund request of {refund_request.expense.household.currency} {refund_request.amount}.",
        'paid': f"Your refund of {refund_request.expense.household.currency} {refund_request.amount} has been paid. Transaction ID: {refund_request.mpesa_transaction_id}",
    }
    
    message = status_messages.get(status, f"Your refund status changed to: {status}")
    
    if refund_request.comment:
        message += f" Comment: {refund_request.comment}"
    
    event_type = f'refund_{status}'  # e.g., 'refund_approved', 'refund_rejected'
    
    return create_notification(
        user=refund_request.requested_by,
        message=message,
        notification_type='push',
        event_type=event_type
    )
