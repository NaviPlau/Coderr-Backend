from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from offers.api.permissions import IsOwnerOrAdmin
from offers.models import Offer, OfferDetail
from offers.api.serializers import SingleDetailOfOfferSerializer, SingleFullOfferDetailSerializer, OfferDetailSerializer
from offers.api.serializers import OfferSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import  SearchFilter
from django.db.models import Min
from rest_framework.pagination import PageNumberPagination
from offers.api.ordering import OrderingHelperOffers
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied



class BusinessProfileRequired(APIException):
    status_code = 403
    default_detail = {"details": ["Nur Unternehmen können Angebote erstellen."]}
    default_code = "business_profile_required"


class OfferPagination(PageNumberPagination):
    page_size = 6 
    page_size_query_param = 'page_size'

class OfferListAPIView(ListCreateAPIView):
    queryset = Offer.objects.annotate(min_price=Min('details__price'))
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = OfferPagination
    filterset_fields = ['user']
    search_fields = ['title', 'description']

    def get_queryset(self):
        """
        Returns a filtered queryset of offers based on query parameters.

        The queryset is filtered as follows:

        - `creator_id`: filter by the user who created the offer
        - `min_price`: filter by the minimum price of the offer
        - `max_delivery_time`: filter by the maximum delivery time of the offer
        - `ordering`: filter by the ordering of the offer (default is 'updated_at')

        :return: a filtered queryset of offers
        """
        queryset = Offer.objects.annotate(min_price=Min('details__price'))
        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id:
            queryset = queryset.filter(user_id=creator_id)
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(min_price__gte=min_price)
        max_delivery_time = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time:
            queryset = queryset.filter(details__delivery_time_in_days__lte=max_delivery_time)
        odering = self.request.query_params.get('ordering', None)
        if odering is None:
            odering = 'updated_at'
        queryset = OrderingHelperOffers.apply_ordering(queryset, ordering=odering)
        return queryset
    

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.

        If the request is a POST, it requires IsOwnerOrAdmin permission.
        Otherwise, it returns the default permissions.

        :return: a list of permissions required by this view
        """
        if self.request.method == 'POST':
            return [IsOwnerOrAdmin()] 
        return super().get_permissions()
    
    def perform_create(self, serializer, format = None):
        """
        Checks if the user has a business profile before creating an offer.

        This method is called when a new offer is being created. It ensures that
        only users with a 'business' profile type are allowed to create offers.
        If the user does not have a business profile, a
        `BusinessProfileRequired` exception is raised. If the user has the
        appropriate profile, the offer is saved with the current user set as the
        creator.

        :param serializer: The serializer instance containing the data to be saved.
        :raises BusinessProfileRequired: If the user does not have a business profile.
        """
    
        user = self.request.user
        profile = getattr(user, 'profile', None)

        if not profile or profile.type != 'business':
            raise BusinessProfileRequired()
        serializer.save(user=user)


class OfferDetailsAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.prefetch_related('details')
    serializer_class = SingleFullOfferDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.

        If the request is a PATCH, it requires IsOwnerOrAdmin permission.
        Otherwise, it returns the default permissions.

        :return: a list of permissions required by this view
        """

        if self.request.method == 'PATCH':
            return [IsOwnerOrAdmin()] 
        return super().get_permissions()

    def update(self, request, format=None, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      serializer.save()
      instance.updated_at = now()
      instance.refresh_from_db()

      updated_data = {
          'id': instance.id,
          'title': serializer.validated_data.get('title', instance.title),
          'description': serializer.validated_data.get('description', instance.description),
          'details': OfferDetailSerializer(instance.details.all(), many=True).data,
          'image': instance.image.url if instance.image else None 
      }

      return Response(updated_data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk, *args, **kwargs):
        offer = get_object_or_404(Offer, id=pk)
        if not (request.user == offer.user or request.user.is_staff):
            raise PermissionDenied({"details": ["Nur der Besitzer oder ein Admin kann das Angebot löschen."], })
        if not (request.user.profile.type == 'business' or request.user.is_staff):
            raise PermissionDenied({"details" : ["Nur ein Unternehmen kann ein Angebot löschen."], })
        offer.delete()
        return Response({}, status=status.HTTP_200_OK)
    




class OfferDetailDetailsAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk, format=None):
        """
        API View to get the details of an offer by its primary key (pk).
        """
        offer = get_object_or_404(OfferDetail, id=pk)
        serializer = SingleDetailOfOfferSerializer(offer)
        return Response(serializer.data, status=status.HTTP_200_OK)