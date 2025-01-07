from rest_framework import generics, permissions, filters
from rest_framework.exceptions import PermissionDenied
from reviews.models import Review
from .serializers import ReviewSerializer
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend


class ReviewListAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business_user_id', 'reviewer_id']
    ordering_fields = ['updated_at', 'rating']
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.

        If the request is a POST, it requires IsAuthenticated permission.
        Otherwise, it returns the default permissions.
        """
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Checks if the user has a customer profile before creating a review.

        This method is called when a new review is being created. It ensures that
        only users with a 'customer' profile type are allowed to create reviews.
        If the user does not have a customer profile, a PermissionDenied exception
        is raised. If the user has the appropriate profile, the review is saved
        with the current user set as the reviewer.

        :param serializer: The serializer instance containing the data to be saved.
        :raises PermissionDenied: If the user does not have a customer profile.
        """

        if not self.request.user.profile.type == 'customer':
            raise PermissionDenied(
                "Nur Benutzer mit einem Kundenprofil können Bewertungen erstellen.")
        serializer.save(reviewer=self.request.user)


class ReviewDetailsAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.

        If the request is a GET, it requires AllowAny permission.
        Otherwise, it requires IsAuthenticated permission.
        """
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        """
        Checks if the user has permission to update a review.

        This method is called when a review is being updated. It ensures that
        only the reviewer of the review or a staff user can update the review.
        If the user does not have the appropriate permission, a PermissionDenied
        exception is raised. If the user has the appropriate permission, the
        review is saved with the updated data.

        :param serializer: The serializer instance containing the data to be saved.
        :raises PermissionDenied: If the user does not have the appropriate permission.
        """
        if serializer.instance.reviewer != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied(
                "Nur der Ersteller oder ein Admin kann eine Bewertung bearbeiten.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Checks if the user has permission to delete a review.

        This method is called when a review is being deleted. It ensures that
        only the reviewer of the review or a staff user can delete the review.
        If the user does not have the appropriate permission, a PermissionDenied
        exception is raised. If the user has the appropriate permission, the
        review is deleted.

        :param instance: The review instance to be deleted.
        :raises PermissionDenied: If the user does not have the appropriate permission.
        """
        if instance.reviewer != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied(
                "Nur der Ersteller oder ein Admin kann eine Bewertung löschen.")
        instance.delete()

    def update(self, request, *args, **kwargs):
        """
        Updates a review.

        This method is called when a PUT or PATCH request is sent to the
        endpoint. It checks if the user has permission to update the review.
        If the user has the appropriate permission, the review is updated
        with the given data and the updated review is returned.

        :param request: The request object.
        :param args: Additional arguments.
        :param kwargs: Additional keyword arguments.
        :returns: A response object containing the updated review.
        :raises PermissionDenied: If the user does not have the appropriate permission.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
