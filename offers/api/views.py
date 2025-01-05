from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from offers.api.permissions import IsOwnerOrAdmin
from offers.models import Offer, OfferDetail
from offers.api.serializers import SingleDetailOfOfferSerializer, SingleFullOfferDetailSerializer, OfferDetailSerializer
from offers.api.serializers import OfferSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Min
from rest_framework.pagination import PageNumberPagination
from offers.api.ordering import OrderingHelperOffers

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
        queryset = OrderingHelperOffers.apply_ordering(queryset, ordering=odering)
        return queryset
    
    def perform_create(self, serializer, format = None):
        user = self.request.user
        profile = getattr(user, 'profile', None)

        if not profile or profile.type != 'business':
            raise BusinessProfileRequired()
        serializer.save(user=user)


class OfferDetailsAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.prefetch_related('details')
    serializer_class = SingleFullOfferDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def update(self, request, format=None, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      if 'image' in request.FILES:
          instance.image = request.FILES['image'] 
      serializer.save()

      updated_data = {
          'id': instance.id,
          'title': serializer.validated_data.get('title', instance.title),
          'description': serializer.validated_data.get('description', instance.description),
          'details': OfferDetailSerializer(instance.details.all(), many=True).data,
          'image': instance.image.url if instance.image else None 
      }

      return Response(updated_data, status=status.HTTP_200_OK)
    




class OfferDetailDetailsAPIView(RetrieveUpdateDestroyAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = SingleDetailOfOfferSerializer
    permission_classes = [AllowAny]