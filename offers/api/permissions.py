from rest_framework.permissions import BasePermission

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user has permission to access the object.

        This method checks whether the requesting user is either the owner of 
        the object or has staff privileges. If the user is the owner or a staff
        member, they are granted permission to access the object.

        :param request: The HTTP request object.
        :param view: The view being accessed.
        :param obj: The object being accessed.
        :return: A boolean indicating whether the user has permission.
        """

        return request.user == obj.user or request.user.is_staff