from rest_framework.permissions import BasePermission

class IsAdminOrSuperAdmin(BasePermission):
    """
    Allows access only to superusers or users with the 'ADMIN' role.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Check if the user is a superuser
        if request.user.is_superuser:
            return True
            
        # Check if the user has an ADMIN role from the Lookup table
        if request.user.role and request.user.role.name == 'ROLE' and request.user.role.value == 'ADMIN':
            return True
            
        return False

class IsBuyer(BasePermission):
    """
    Allows access only to users with the 'BUYER' role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == 'ROLE' and 
            request.user.role.value == 'BUYER'
        )

class IsRetailer(BasePermission):
    """
    Allows access only to users with the 'RETAILER' role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == 'ROLE' and 
            request.user.role.value == 'RETAILER'
        )

class IsWholesaler(BasePermission):
    """
    Allows access only to users with the 'WHOLESALER' role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == 'ROLE' and 
            request.user.role.value == 'WHOLESALER'
        )

class IsServiceProvider(BasePermission):
    """
    Allows access only to users with the 'SERVICE_PROVIDER' role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == 'ROLE' and 
            request.user.role.value == 'SERVICE_PROVIDER'
        )

class IsAdminOrSuperAdminOrServiceProvider(BasePermission):
    """
    Allows access only to superusers, or users with the 'ADMIN' or 'SERVICE_PROVIDER' role.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.is_superuser:
            return True
            
        if request.user.role and request.user.role.name == 'ROLE':
            return request.user.role.value in ['ADMIN', 'SERVICE_PROVIDER']
            
        return False

class IsAdminOrSuperAdminOrBuyer(BasePermission):
    """
    Allows access only to superusers, or users with the 'ADMIN' or 'BUYER' role.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.is_superuser:
            return True
            
        if request.user.role and request.user.role.name == 'ROLE':
            return request.user.role.value in ['ADMIN', 'BUYER']
            
        return False
